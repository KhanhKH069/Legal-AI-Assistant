"""Screening API Router — SQLite backed"""

from typing import Any, Dict, List, Optional

import asyncio
from fastapi import (
    APIRouter,
    HTTPException,
    BackgroundTasks,
    Depends,
    WebSocket,
    WebSocketDisconnect,
)
from sqlmodel import select
from api.models import User
from api.auth import get_current_user
from src.db import get_session
from src.db_models import ScreeningResult, Applicant
import json

router = APIRouter(prefix="/screening", tags=["screening"])
from src.celery_app import run_screening_background_task
import redis.asyncio as redis_async
from src.core.config import config


# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.listener_task = None
        self.redis_client = None

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

        # Start Redis listener if not already running
        if self.listener_task is None:
            self.redis_client = redis_async.from_url(config.redis_url)
            self.listener_task = asyncio.create_task(self._listen_to_redis())

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass

    async def _listen_to_redis(self):
        pubsub = self.redis_client.pubsub()
        await pubsub.subscribe("screening_progress_global")
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    await self.broadcast(data)
        except asyncio.CancelledError:
            pass
        finally:
            await pubsub.unsubscribe("screening_progress_global")
            await pubsub.close()


manager = ConnectionManager()


@router.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We just keep connection open.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@router.post("/run")
def run_screening(
    background_tasks: BackgroundTasks,
    applicant_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    try:
        # Trigger Celery Task
        run_screening_background_task.delay(applicant_id)
        return {
            "status": "processing",
            "message": "CV screening task added to background Celery queue.",
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/results")
def list_results(
    position: Optional[str] = None,
    recommendation: Optional[str] = None,
    current_user: User = Depends(get_current_user),
) -> List[Dict]:
    session = get_session()
    query = select(ScreeningResult, Applicant).join(Applicant)

    if position:
        query = query.where(ScreeningResult.position == position)
    if recommendation:
        query = query.where(ScreeningResult.recommendation == recommendation)

    db_results = session.exec(query).all()

    results = []
    for res, app in db_results:
        d = res.model_dump()
        d["applicant_name"] = app.name
        results.append(d)

    return results


@router.get("/results/{result_id}")
def get_result(result_id: int, current_user: User = Depends(get_current_user)) -> Dict:
    session = get_session()
    res = session.get(ScreeningResult, result_id)
    if not res:
        raise HTTPException(status_code=404, detail="Screening result not found")

    app = session.get(Applicant, res.applicant_id)
    d = res.model_dump()
    if app:
        d["applicant_name"] = app.name

    return d


from fastapi.responses import StreamingResponse
import io
import csv


@router.get("/export")
def export_results_csv(current_user: User = Depends(get_current_user)):
    session = get_session()
    query = select(ScreeningResult, Applicant).join(Applicant)
    db_results = session.exec(query).all()

    output = io.StringIO()
    writer = csv.writer(output)

    # Header
    writer.writerow(
        [
            "ID",
            "Candidate Name",
            "Position",
            "Score (%)",
            "Recommendation",
            "Status",
            "Action",
            "Missing Skills",
        ]
    )

    for res, app in db_results:
        # Extract missing skills from breakdown if available
        missing_skills = []
        if res.breakdown and "required_skills" in res.breakdown:
            # We don't have exact missing skills in DB easily, but we can put placeholder
            missing_skills.append("See Breakdown")

        writer.writerow(
            [
                res.id,
                app.name,
                res.position,
                res.percentage,
                res.recommendation,
                res.status.strip(),
                res.action,
                ", ".join(missing_skills),
            ]
        )

    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=screening_results.csv"},
    )

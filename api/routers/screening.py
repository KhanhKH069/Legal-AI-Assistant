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


# --- WebSocket Connection Manager ---
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                pass


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


# ------------------------------------


def _run_screening_background(applicant_id: Optional[int] = None) -> None:
    """
    Run real CV screening using cv_screening.py and save to SQLite.
    Broadcasts progress via WebSocket.
    """
    try:
        from cv_screening import screen_all_applicants

        # We need the event loop to send broadcast messages from this synchronous thread
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        def progress_callback(msg: str, pct: float):
            payload = {"message": msg, "progress": pct}
            if loop:
                asyncio.run_coroutine_threadsafe(manager.broadcast(payload), loop)
            else:
                # Fallback if no loop (e.g. tests)
                asyncio.run(manager.broadcast(payload))

        # This will query SQLite DB, score CVs using RAG/EasyOCR/Gemini
        # and return a list of dicts.
        results = screen_all_applicants(progress_callback=progress_callback)

        if results:
            session = get_session()

            # Clear old results to prevent duplicates if screening all
            if applicant_id is None:
                old_results = session.exec(select(ScreeningResult)).all()
                for r in old_results:
                    session.delete(r)
            else:
                old_results = session.exec(
                    select(ScreeningResult).where(
                        ScreeningResult.applicant_id == applicant_id
                    )
                ).all()
                for r in old_results:
                    session.delete(r)

            session.commit()

            for r in results:
                app_id = r.get("id")
                if applicant_id is not None and app_id != applicant_id:
                    continue

                if not app_id:
                    continue

                db_result = ScreeningResult(
                    applicant_id=app_id,
                    position=r.get("position", ""),
                    total_score=r.get("total_score", 0),
                    max_score=r.get("max_score", 100),
                    percentage=r.get("percentage", 0),
                    recommendation=r.get("recommendation", ""),
                    status=r.get("status", ""),
                    action=r.get("action", ""),
                    breakdown=r.get("breakdown", {}),
                    interview_questions=r.get("interview_questions", []),
                    min_score=r.get("min_score", 60),
                )
                session.add(db_result)

                # Update applicant status based on recommendation
                app = session.get(Applicant, app_id)
                if app:
                    app.status = "SCREENED"
                    session.add(app)

            session.commit()
            print(
                f"Successfully screened {len(results)} applicants and saved to SQLite."
            )

            # Send completion signal
            def completion_signal():
                payload = {
                    "message": "Đã hoàn tất đánh giá toàn bộ CV!",
                    "progress": 100,
                    "done": True,
                }
                if loop:
                    asyncio.run_coroutine_threadsafe(manager.broadcast(payload), loop)
                else:
                    asyncio.run(manager.broadcast(payload))

            completion_signal()
        else:
            print("No applicants found or no results generated.")

            def empty_signal():
                payload = {
                    "message": "Không có ứng viên nào để đánh giá.",
                    "progress": 100,
                    "done": True,
                }
                if loop:
                    asyncio.run_coroutine_threadsafe(manager.broadcast(payload), loop)
                else:
                    asyncio.run(manager.broadcast(payload))

            empty_signal()
    except Exception as e:
        print(f"Error running background screening: {e}")
        # Send error signal
        try:
            loop = asyncio.get_running_loop()
            asyncio.run_coroutine_threadsafe(
                manager.broadcast(
                    {"message": f"Lỗi: {e}", "progress": 0, "error": True}
                ),
                loop,
            )
        except Exception:
            pass


@router.post("/run")
def run_screening(
    background_tasks: BackgroundTasks,
    applicant_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    background_tasks.add_task(_run_screening_background, applicant_id)
    return {
        "status": "processing",
        "message": "CV screening task added to background queue.",
    }


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

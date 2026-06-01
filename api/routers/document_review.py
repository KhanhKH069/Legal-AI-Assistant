import asyncio
import json
import os
import redis
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import fitz  # PyMuPDF
from typing import Dict, Any, List

from src.agents.contract_reviewer_agent import run_contract_review
from src.tasks.async_review import process_contract

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

router = APIRouter(prefix="/contract", tags=["Contract Review"])


@router.post("/review")
async def review_contract(files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    combined_text = ""

    for idx, file in enumerate(files):
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=400, detail=f"File {file.filename} is not a PDF."
            )

        temp_path = f"temp_{idx}_{file.filename}"
        try:
            content = await file.read()
            with open(temp_path, "wb") as f:
                f.write(content)

            # Extract text using PyMuPDF
            text = f"--- START OF DOCUMENT: {file.filename} ---\n"
            with fitz.open(temp_path) as doc:
                for page in doc:
                    text += page.get_text()
            text += f"\n--- END OF DOCUMENT: {file.filename} ---\n\n"

            combined_text += text

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    if not combined_text.strip():
        raise HTTPException(
            status_code=400, detail="Could not extract text from the provided PDFs."
        )

    # Pass all documents to the LangGraph agent for review and cross-reference
    result = run_contract_review(combined_text)

    return {"status": "success", "result": result}

@router.post("/async-review")
async def async_review_contract(files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")

    combined_text = ""

    for idx, file in enumerate(files):
        if not file.filename.endswith(".pdf"):
            raise HTTPException(
                status_code=400, detail=f"File {file.filename} is not a PDF."
            )

        temp_path = f"temp_{idx}_{file.filename}"
        try:
            content = await file.read()
            with open(temp_path, "wb") as f:
                f.write(content)

            # Extract text using PyMuPDF
            text = f"--- START OF DOCUMENT: {file.filename} ---\n"
            with fitz.open(temp_path) as doc:
                for page in doc:
                    text += page.get_text()
            text += f"\n--- END OF DOCUMENT: {file.filename} ---\n\n"

            combined_text += text

        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    if not combined_text.strip():
        raise HTTPException(
            status_code=400, detail="Could not extract text from the provided PDFs."
        )

    # Dispatch Celery Task
    task = process_contract.delay(combined_text)

    return {
        "status": "accepted",
        "job_id": task.id,
        "message": "Contract is being processed in the background."
    }

@router.get("/stream/{job_id}")
async def stream_review_status(job_id: str):
    async def event_generator():
        pubsub = redis_client.pubsub()
        pubsub.subscribe(f"job_status_{job_id}")
        
        # Initial ping to keep connection alive
        yield "data: {\"status\": \"connected\"}\n\n"

        while True:
            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                data = json.loads(message['data'])
                yield f"data: {json.dumps(data)}\n\n"
                if data.get("status") in ["success", "error"]:
                    break
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

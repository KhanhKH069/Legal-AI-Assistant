import asyncio
import json
import os
import redis
import tempfile
import time
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from typing import Dict, Any, List

from src.agents.contract_reviewer_agent import run_contract_review
from src.tasks.async_review import process_contract

redis_client = redis.from_url(os.getenv("REDIS_URL", "redis://localhost:6379/0"))

_reader = None
def get_easyocr_reader():
    global _reader
    if _reader is None:
        import easyocr
        _reader = easyocr.Reader(['vi', 'en'])
    return _reader

async def _extract_text_from_pdf(file: UploadFile) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        temp_path = tmp.name
        content = await file.read()
        tmp.write(content)

    try:
        text = f"--- START OF DOCUMENT: {file.filename} ---\n"
        has_text = False

        import pdfplumber
        with pdfplumber.open(temp_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    text += page_text + "\n"
                    has_text = True

        if not has_text:
            reader = get_easyocr_reader()
            import fitz
            with fitz.open(temp_path) as doc:
                for page in doc:
                    pix = page.get_pixmap()
                    img_bytes = pix.tobytes("png")
                    result = reader.readtext(img_bytes, detail=0)
                    text += " ".join(result) + "\n"

        text += f"\n--- END OF DOCUMENT: {file.filename} ---\n\n"
        return text
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

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

        extracted_text = await _extract_text_from_pdf(file)
        combined_text += extracted_text

    if not combined_text.strip():
        raise HTTPException(
            status_code=400, detail="Could not extract text from the provided PDFs."
        )

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

        extracted_text = await _extract_text_from_pdf(file)
        combined_text += extracted_text

    if not combined_text.strip():
        raise HTTPException(
            status_code=400, detail="Could not extract text from the provided PDFs."
        )

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

        yield "data: {\"status\": \"connected\"}\n\n"

        start_time = time.time()
        while True:
            if time.time() - start_time > 300:
                yield f"data: {json.dumps({'status': 'error', 'message': 'Timeout after 5 minutes'})}\n\n"
                break

            message = pubsub.get_message(ignore_subscribe_messages=True)
            if message:
                data = json.loads(message['data'])
                yield f"data: {json.dumps(data)}\n\n"
                if data.get("status") in ["success", "error"]:
                    break
            await asyncio.sleep(0.5)

    return StreamingResponse(event_generator(), media_type="text/event-stream")

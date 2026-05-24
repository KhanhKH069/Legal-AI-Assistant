from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import Dict, Any
import os
import uuid
from api.models import User
from api.auth import get_current_user

router = APIRouter(prefix="/policies", tags=["policies"])

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "policies")


@router.post("/upload")
async def upload_policy(
    file: UploadFile = File(...), current_user: User = Depends(get_current_user)
) -> Dict[str, Any]:
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    os.makedirs(DATA_DIR, exist_ok=True)

    file_id = str(uuid.uuid4())[:8]
    safe_filename = f"{file_id}_{file.filename}"
    file_path = os.path.join(DATA_DIR, safe_filename)

    # Save file
    try:
        content = await file.read()
        with open(file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Process PDF and insert to ChromaDB
    try:
        import PyPDF2

        text = ""
        with open(file_path, "rb") as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page in pdf_reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"

        if not text.strip():
            raise Exception("No text could be extracted from PDF")

        # Basic chunking (split by double newline or chunk by length)
        chunks = [c.strip() for c in text.split("\n\n") if len(c.strip()) > 50]
        if not chunks:
            # Fallback chunking by 500 chars
            chunks = [text[i : i + 500] for i in range(0, len(text), 500)]

        from src.services.vector_db import get_vector_db

        vdb = get_vector_db()

        docs = []
        metadatas = []
        ids = []

        for i, chunk in enumerate(chunks):
            docs.append(chunk)
            metadatas.append({"source_file": file.filename, "chunk_index": i})
            ids.append(f"{file_id}_{i}")

        vdb.add_documents("hr_policies", docs, metadatas, ids)

        # Also rebuild Hybrid BM25 index if available
        try:
            from src.services.hybrid_retriever import get_hybrid_retriever

            retriever = get_hybrid_retriever()
            retriever.build_bm25()
        except Exception as e:
            print(f"Warning: Could not rebuild BM25 index: {e}")

        return {
            "status": "success",
            "message": f"Policy '{file.filename}' processed successfully. {len(chunks)} chunks indexed.",
            "file_id": file_id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing policy file: {e}"
        )

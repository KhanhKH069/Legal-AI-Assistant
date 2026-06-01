import os
from fastapi import APIRouter, UploadFile, File, HTTPException
import fitz  # PyMuPDF
from typing import Dict, Any, List

from src.agents.contract_reviewer_agent import run_contract_review

router = APIRouter(prefix="/contract", tags=["Contract Review"])

@router.post("/review")
async def review_contract(files: List[UploadFile] = File(...)) -> Dict[str, Any]:
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")
        
    combined_text = ""
    
    for idx, file in enumerate(files):
        if not file.filename.endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"File {file.filename} is not a PDF.")
            
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
        raise HTTPException(status_code=400, detail="Could not extract text from the provided PDFs.")
    
    # Pass all documents to the LangGraph agent for review and cross-reference
    result = run_contract_review(combined_text)
    
    return {"status": "success", "result": result}

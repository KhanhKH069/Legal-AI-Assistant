from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile
import os

router = APIRouter(prefix="/files", tags=["files"])

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx", ".png", ".jpg", ".jpeg"}


@router.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...)) -> dict:
    """
    Upload CV file and store it on disk.
    Returns a server-side cv_path that backend uses for screening.
    Files are stored under data/cv_uploads/ for consistency with the screening pipeline.
    """
    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"File type not allowed. Allowed types are: {', '.join(ALLOWED_EXTENSIONS)}",
        )

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413, detail="File too large. Maximum size is 10MB."
        )

    # Use StorageService instead of hardcoded paths
    from src.core.storage import get_storage_service
    import io
    
    storage = get_storage_service()
    try:
        # Wrap content in BytesIO for the StorageService
        cv_path = storage.save_file(file.filename, io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Return the path/URL returned by StorageService
    return {
        "filename": file.filename,
        "cv_path": cv_path,
    }

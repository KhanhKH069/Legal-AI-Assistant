from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...)) -> dict:
    """
    Upload CV file and store it on disk.
    Returns a server-side cv_path that backend uses for screening.
    """
    upload_dir = Path("cv_uploads")
    upload_dir.mkdir(exist_ok=True)

    # Use original filename; could be improved to avoid collisions
    dest_path = upload_dir / file.filename

    try:
        content = await file.read()
        with open(dest_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    return {
        "filename": file.filename,
        "cv_path": str(dest_path),
    }


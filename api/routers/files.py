from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/files", tags=["files"])


@router.post("/upload-cv")
async def upload_cv(file: UploadFile = File(...)) -> dict:
    """
    Upload CV file and store it on disk.
    Returns a server-side cv_path that backend uses for screening.
    Files are stored under data/cv_uploads/ for consistency with the screening pipeline.
    """
    # Resolve absolute path to data/cv_uploads relative to this file
    base_dir = Path(__file__).resolve().parent.parent.parent
    upload_dir = base_dir / "data" / "cv_uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Use original filename; could be improved to avoid collisions
    dest_path = upload_dir / file.filename

    try:
        content = await file.read()
        with open(dest_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {e}")

    # Return relative path (relative to project root) so screening can locate it
    return {
        "filename": file.filename,
        "cv_path": str(
            Path("cv_uploads") / file.filename
        ),  # stored as cv_uploads/xxx.pdf for DB
    }

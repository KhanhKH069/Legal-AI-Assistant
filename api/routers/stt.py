import os
import tempfile
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from faster_whisper import WhisperModel

logger = logging.getLogger(__name__)

router = APIRouter()

# Initialize the model at module level so it loads only once.
# Using 'tiny' model and INT8 quantization for maximum speed on CPU/GPU.
try:
    model = WhisperModel("small", device="cuda", compute_type="float16")
except Exception as e:
    logger.error(f"Failed to load WhisperModel: {e}")
    model = None


@router.post("")
async def transcribe_audio(file: UploadFile = File(...)):
    if model is None:
        raise HTTPException(
            status_code=500, detail="STT model is not available on this server."
        )

    try:
        # Save the uploaded file temporarily
        suffix = os.path.splitext(file.filename)[1] if file.filename else ".webm"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_path = tmp_file.name

        # Transcribe using faster-whisper
        # Force language="vi" since this is a Vietnamese Legal AI
        segments, info = model.transcribe(tmp_path, language="vi", beam_size=5)
        text = " ".join([segment.text for segment in segments])

        # Cleanup
        os.remove(tmp_path)

        return {"text": text.strip()}

    except Exception as e:
        logger.error(f"Speech-to-text error: {e}")
        # Ensure cleanup if error occurs
        if "tmp_path" in locals() and os.path.exists(tmp_path):
            os.remove(tmp_path)
        raise HTTPException(
            status_code=500, detail=f"Failed to transcribe audio: {str(e)}"
        )

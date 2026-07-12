"""Transcription API routes."""
import logging

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from transcriber import transcribe_audio, get_model_info
from config import WHISPER_MODEL, WHISPER_DEVICE

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/transcription", tags=["transcription"])


class TranscribeRequest(BaseModel):
    """Audio samples to transcribe."""

    samples: list[float]
    language: str | None = None


class TranscribeResponse(BaseModel):
    """Transcription result."""

    text: str
    model: str
    device: str
    language: str | None = None


@router.post("/", response_model=TranscribeResponse)
async def transcribe(req: TranscribeRequest):
    """Transcribe audio samples to text.

    Accepts raw float32 audio at 16kHz mono. Returns transcribed text.
    """
    if not req.samples:
        raise HTTPException(status_code=400, detail="No audio samples provided")

    try:
        text = transcribe_audio(req.samples, language=req.language)
    except Exception as e:
        logger.exception("Transcription failed")
        raise HTTPException(status_code=500, detail=str(e))

    return TranscribeResponse(
        text=text,
        model=WHISPER_MODEL,
        device=WHISPER_DEVICE,
    )


@router.get("/info")
async def info():
    """Get model info (loaded status, device, etc.)."""
    return get_model_info()

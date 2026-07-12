"""Dictation control routes — manual start/stop via API."""
from fastapi import APIRouter
from pydantic import BaseModel

from orchestrator import orchestrator

router = APIRouter(prefix="/api/dictation", tags=["dictation"])


class DictationResponse(BaseModel):
    status: str
    is_dictating: bool
    text: str = ""


@router.post("/start", response_model=DictationResponse)
async def start():
    """Start recording."""
    if orchestrator.is_dictating:
        return DictationResponse(status="already_recording", is_dictating=True)
    await orchestrator.start_dictation()
    return DictationResponse(status="recording", is_dictating=True)


@router.post("/stop", response_model=DictationResponse)
async def stop():
    """Stop recording, transcribe, and paste."""
    if not orchestrator.is_dictating:
        return DictationResponse(status="not_recording", is_dictating=False)
    text = await orchestrator.stop_dictation()
    return DictationResponse(status="done", is_dictating=False, text=text)


@router.get("/status", response_model=DictationResponse)
async def status():
    """Get current dictation status."""
    return DictationResponse(
        status="recording" if orchestrator.is_dictating else "idle",
        is_dictating=orchestrator.is_dictating,
    )

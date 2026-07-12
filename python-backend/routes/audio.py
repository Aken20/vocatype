"""Audio device management routes."""
from fastapi import APIRouter

from audio_capture import recorder

router = APIRouter(prefix="/api/audio", tags=["audio"])


@router.get("/devices")
async def list_devices():
    """List available audio input devices."""
    return {"devices": recorder.list_devices()}

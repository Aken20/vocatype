"""Pill overlay routes — start/stop the floating indicator."""
from fastapi import APIRouter
from pydantic import BaseModel

from pill_overlay import toggle_pill, stop_pill, start_pill

router = APIRouter(prefix="/api/pill", tags=["pill"])


class PillResponse(BaseModel):
    status: str

@router.post("/toggle", response_model=PillResponse)
async def toggle():
    result = toggle_pill()
    return PillResponse(status=result)

@router.get("/status", response_model=PillResponse)
async def status():
    from pill_overlay import _pill
    running = _pill is not None and _pill.is_running
    return PillResponse(status="running" if running else "stopped")

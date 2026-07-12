"""Pill overlay routes — start/stop the floating indicator."""
from fastapi import APIRouter
from pydantic import BaseModel

from pill_overlay import toggle_pill, pill

router = APIRouter(prefix="/api/pill", tags=["pill"])


class PillResponse(BaseModel):
    status: str
    running: bool


@router.post("/toggle", response_model=PillResponse)
async def toggle():
    result = toggle_pill()
    return PillResponse(status=result, running=pill.is_running)


@router.get("/status", response_model=PillResponse)
async def status():
    return PillResponse(
        status="running" if pill.is_running else "stopped",
        running=pill.is_running,
    )

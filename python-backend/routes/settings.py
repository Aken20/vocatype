"""Settings routes — LLM cleanup toggle, model selection, etc."""
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/settings", tags=["settings"])

# In-memory settings (persist to SQLite later)
_settings = {
    "llm_cleanup_enabled": True,
}


class SettingsResponse(BaseModel):
    llm_cleanup_enabled: bool


@router.get("/", response_model=SettingsResponse)
async def get_settings():
    return SettingsResponse(**{k: v for k, v in _settings.items()})


@router.post("/llm-cleanup", response_model=SettingsResponse)
async def toggle_llm_cleanup(data: dict):
    enabled = data.get("enabled", True)
    _settings["llm_cleanup_enabled"] = bool(enabled)
    return SettingsResponse(llm_cleanup_enabled=_settings["llm_cleanup_enabled"])


def is_llm_cleanup_enabled() -> bool:
    return _settings.get("llm_cleanup_enabled", True)

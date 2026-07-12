"""WhisperType Backend — FastAPI server.

Press Ctrl+Shift+F12 to dictate. Audio flows through:
  WASAPI mic → faster-whisper (small) → optional LM Studio cleanup → clipboard paste
"""
import asyncio
import logging
import sys

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import HOST, PORT, WHISPER_MODEL

# Import orchestrator early — used by WebSocket handler
from orchestrator import orchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="WhisperType Backend",
    version="0.1.0",
    description="Local voice dictation engine — audio capture, transcription, text injection",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routes
from routes.transcription import router as transcription_router
from routes.audio import router as audio_router
from routes.dictation import router as dictation_router

app.include_router(transcription_router)
app.include_router(audio_router)
app.include_router(dictation_router)


@app.get("/api/health")
async def health():
    """Health check endpoint. Frontend polls this on startup."""
    from transcriber import get_model_info
    from text_cleaner import check_lm_studio_health

    lm_available = await check_lm_studio_health()

    return {
        "status": "ok",
        "version": "0.1.0",
        "model": get_model_info(),
        "lm_studio_available": lm_available,
    }


# ── WebSocket for real-time status ────────────────────────────────────

# Store connected clients
_ws_clients: list[WebSocket] = []


@app.websocket("/api/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket for real-time dictation status and control.

    Client → Server:
      {"action": "start"}   — start dictation
      {"action": "stop"}    — stop dictation
      {"action": "status"}  — get current status
      {"action": "ping"}    — keepalive

    Server → Client:
      {"type": "status", "isRecording": bool, "lastText": str, "state": str}
      {"type": "health", "lmStudioAvailable": bool}
      {"type": "pong"}
    """
    await ws.accept()
    _ws_clients.append(ws)
    orchestrator.set_ws_clients(_ws_clients)
    logger.info("WebSocket client connected (%d total)", len(_ws_clients))

    try:
        # Send initial health status
        from text_cleaner import check_lm_studio_health
        lm_available = await check_lm_studio_health()
        await ws.send_json({
            "type": "health",
            "lmStudioAvailable": lm_available,
        })

        while True:
            data = await ws.receive_json()
            action = data.get("action", "")

            if action == "start":
                await orchestrator.start_dictation()
            elif action == "stop":
                await orchestrator.stop_dictation()
            elif action == "status":
                await ws.send_json({
                    "type": "status",
                    "isRecording": orchestrator.is_dictating,
                    "state": "recording" if orchestrator.is_dictating else "idle",
                })
            elif action == "ping":
                await ws.send_json({"type": "pong"})
            elif action == "health":
                lm_available = await check_lm_studio_health()
                await ws.send_json({
                    "type": "health",
                    "lmStudioAvailable": lm_available,
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning("WebSocket error: %s", e)
    finally:
        if ws in _ws_clients:
            _ws_clients.remove(ws)
        orchestrator.set_ws_clients(_ws_clients)
        logger.info("WebSocket client disconnected (%d remaining)", len(_ws_clients))


# ── Startup / Shutdown ────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Initialize the backend on startup."""
    logger.info("=" * 50)
    logger.info("🎙️  WhisperType Backend v0.1.0")
    logger.info("   Model: %s | Device: CPU", WHISPER_MODEL)
    logger.info("   Server: http://%s:%d", HOST, PORT)
    logger.info("   Hotkey: Ctrl+Shift+F12")
    logger.info("=" * 50)

    # Give the orchestrator access to WebSocket clients
    from orchestrator import orchestrator

    orchestrator.set_ws_clients(_ws_clients)

    # Start global hotkey listener (Ctrl+Shift+F12 → toggle dictation)
    import os as _os
    _debug_log = _os.path.join(_os.path.dirname(__file__), "debug.log")
    with open(_debug_log, "w") as f:
        f.write("startup reached hotkey init\n")

    from hotkey_manager import HotkeyManager
    import urllib.request

    with open(_debug_log, "a") as f:
        f.write("imports done, creating HotkeyManager\n")

    hotkey_mgr = HotkeyManager()

    with open(_debug_log, "a") as f:
        f.write("HotkeyManager created, starting listener\n")

    API_BASE = f"http://{HOST}:{PORT}"

    def on_hotkey():
        """Called when Ctrl+Shift+F12 is pressed — uses REST API to avoid asyncio thread issues."""
        logger.info("🔥 HOTKEY PRESSED — Ctrl+Shift+F12 detected!")
        try:
            if orchestrator.is_dictating:
                logger.info("  → Stopping dictation...")
                urllib.request.urlopen(
                    urllib.request.Request(f"{API_BASE}/api/dictation/stop", method="POST")
                )
                logger.info("  → Stop request sent")
            else:
                logger.info("  → Starting dictation...")
                urllib.request.urlopen(
                    urllib.request.Request(f"{API_BASE}/api/dictation/start", method="POST")
                )
                logger.info("  → Start request sent")
        except Exception as e:
            logger.error("  → Hotkey HTTP request failed: %s", e)

    hotkey_mgr.start(on_hotkey)

    # Store for shutdown
    app.state.hotkey_manager = hotkey_mgr
    app.state.orchestrator = orchestrator

    # Pre-load the Whisper model in the background
    from transcriber import get_model

    async def load_model():
        try:
            get_model()
            logger.info("✅ Whisper model loaded and ready")
        except Exception as e:
            logger.warning("⚠️  Could not pre-load Whisper model: %s", e)
            logger.warning("   It will load on first transcription request")

    asyncio.create_task(load_model())


@app.on_event("shutdown")
async def shutdown():
    """Cleanup on shutdown."""
    from transcriber import unload_model

    unload_model()

    if hasattr(app.state, "hotkey_manager"):
        app.state.hotkey_manager.stop()

    logger.info("WhisperType backend shut down")


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")

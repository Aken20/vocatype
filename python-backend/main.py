"""WhisperType Backend — FastAPI server.

Press Ctrl+Shift+V to dictate. Audio flows through:
  WASAPI mic → faster-whisper (small) → optional LM Studio cleanup → clipboard paste
"""
import logging
import sys

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from config import HOST, PORT, WHISPER_MODEL

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

app.include_router(transcription_router)


@app.get("/api/health")
async def health():
    """Health check endpoint. Frontend polls this on startup."""
    from transcriber import get_model_info

    return {
        "status": "ok",
        "version": "0.1.0",
        "model": get_model_info(),
        "lm_studio_available": False,  # checked on startup via text_cleaner
    }


# ── WebSocket for real-time status ────────────────────────────────────

# Store connected clients
_ws_clients: list[WebSocket] = []


@app.websocket("/api/ws")
async def websocket_endpoint(ws: WebSocket):
    """WebSocket for real-time dictation status updates.

    Sends:
      {"type": "status", "isRecording": true/false, "lastText": "..."}
      {"type": "health", "lmStudioAvailable": true/false}
    """
    await ws.accept()
    _ws_clients.append(ws)
    logger.info("WebSocket client connected (%d total)", len(_ws_clients))

    try:
        while True:
            data = await ws.receive_json()
            action = data.get("action", "")

            if action == "ping":
                await ws.send_json({"type": "pong"})
            elif action == "health":
                await ws.send_json({
                    "type": "health",
                    "lmStudioAvailable": False,
                })

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.warning("WebSocket error: %s", e)
    finally:
        _ws_clients.remove(ws)
        logger.info("WebSocket client disconnected (%d remaining)", len(_ws_clients))


# ── Startup / Shutdown ────────────────────────────────────────────────

@app.on_event("startup")
async def startup():
    """Initialize the backend on startup."""
    logger.info("=" * 50)
    logger.info("🎙️  WhisperType Backend v0.1.0")
    logger.info("   Model: %s | Device: %s", WHISPER_MODEL, "CPU")
    logger.info("   Server: http://%s:%d", HOST, PORT)
    logger.info("   WebSocket: ws://%s:%d/api/ws", HOST, PORT)
    logger.info("=" * 50)

    # Pre-load the Whisper model in the background
    import asyncio
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
    logger.info("WhisperType backend shut down")


if __name__ == "__main__":
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")

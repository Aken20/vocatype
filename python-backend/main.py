"""WhisperType Backend — FastAPI server."""
import logging
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import HOST, PORT

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


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "version": "0.1.0",
        "whisper_model": None,  # populated when model loads
        "lm_studio_available": False,
    }


if __name__ == "__main__":
    logger.info("Starting WhisperType backend on %s:%d", HOST, PORT)
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")

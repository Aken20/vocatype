"""Configuration for WhisperType backend."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Server
HOST = os.getenv("WHISPERTYPE_HOST", "127.0.0.1")
PORT = int(os.getenv("WHISPERTYPE_PORT", "9877"))

# Whisper model
WHISPER_MODEL = os.getenv("WHISPERTYPE_WHISPER_MODEL", "small")
WHISPER_DEVICE = os.getenv("WHISPERTYPE_WHISPER_DEVICE", "cpu")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPERTYPE_WHISPER_COMPUTE", "int8")

# Models directory
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Database
DB_PATH = BASE_DIR / "whispertype.db"

# Hotkey
HOTKEY_MODIFIERS = os.getenv("WHISPERTYPE_HOTKEY_MODIFIERS", "win+shift")
HOTKEY_KEY = os.getenv("WHISPERTYPE_HOTKEY_KEY", "v")

# Audio
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1

# LM Studio
LM_STUDIO_URL = os.getenv("WHISPERTYPE_LM_STUDIO_URL", "http://localhost:1234/v1")

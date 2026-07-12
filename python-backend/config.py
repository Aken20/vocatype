"""Configuration for WhisperType backend."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Server
HOST = os.getenv("WHISPERTYPE_HOST", "127.0.0.1")
PORT = int(os.getenv("WHISPERTYPE_PORT", "9877"))

# Whisper model
WHISPER_MODEL = os.getenv("WHISPERTYPE_WHISPER_MODEL", "small")
WHISPER_DEVICE = os.getenv("WHISPERTYPE_WHISPER_DEVICE", "cuda")
WHISPER_COMPUTE_TYPE = os.getenv("WHISPERTYPE_WHISPER_COMPUTE", "float16")

# Models directory
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Register CUDA DLLs from nvidia pip packages (Windows)
# Must happen BEFORE any ctranslate2/faster_whisper import
import os as _os, sys as _sys
try:
    _nv = _os.path.join(_os.path.dirname(__file__), ".venv", "Lib", "site-packages", "nvidia")
    _cublas = _os.path.join(_nv, "cublas", "bin")
    _nvrtc  = _os.path.join(_nv, "cuda_nvrtc", "bin")
    if _os.path.isdir(_cublas):
        _os.add_dll_directory(_cublas)
        _os.environ["PATH"] = _cublas + _os.pathsep + _os.environ.get("PATH", "")
    if _os.path.isdir(_nvrtc):
        _os.add_dll_directory(_nvrtc)
        _os.environ["PATH"] = _nvrtc + _os.pathsep + _os.environ.get("PATH", "")
except Exception:
    pass

# Database
DB_PATH = BASE_DIR / "whispertype.db"

# Hotkey
HOTKEY_MODIFIERS = os.getenv("WHISPERTYPE_HOTKEY_MODIFIERS", "ctrl+shift")
HOTKEY_KEY = os.getenv("WHISPERTYPE_HOTKEY_KEY", "d")

# Audio
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1

# LM Studio
LM_STUDIO_URL = os.getenv("WHISPERTYPE_LM_STUDIO_URL", "http://localhost:1234/v1")

"""Configuration for VocaType backend."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# Server
HOST = os.getenv("VOCATYPE_HOST", "127.0.0.1")
PORT = int(os.getenv("VOCATYPE_PORT", "9877"))

# Whisper model
WHISPER_MODEL = os.getenv("VOCATYPE_WHISPER_MODEL", "small")

# Auto-detect CUDA; fall back to CPU if unavailable
def _detect_device():
    try:
        import ctranslate2
        if ctranslate2.get_cuda_device_count() > 0:
            return "cuda", "float16"
    except Exception:
        pass
    return "cpu", "int8"

_detected_device, _detected_compute = _detect_device()

WHISPER_DEVICE = os.getenv("VOCATYPE_WHISPER_DEVICE", _detected_device)
WHISPER_COMPUTE_TYPE = os.getenv("VOCATYPE_WHISPER_COMPUTE", _detected_compute)

# Models directory
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Register CUDA DLLs from nvidia pip packages (Windows)
# Must happen BEFORE any ctranslate2/faster_whisper import
try:
    _nv = os.path.join(BASE_DIR, ".venv", "Lib", "site-packages", "nvidia")
    _cublas = os.path.join(_nv, "cublas", "bin")
    _nvrtc  = os.path.join(_nv, "cuda_nvrtc", "bin")
    if os.path.isdir(_cublas):
        os.add_dll_directory(_cublas)
        os.environ["PATH"] = _cublas + os.pathsep + os.environ.get("PATH", "")
    if os.path.isdir(_nvrtc):
        os.add_dll_directory(_nvrtc)
        os.environ["PATH"] = _nvrtc + os.pathsep + os.environ.get("PATH", "")
except Exception:
    pass

# Database
DB_PATH = BASE_DIR / "vocatype.db"

# Hotkey
HOTKEY_MODIFIERS = os.getenv("VOCATYPE_HOTKEY_MODIFIERS", "ctrl+shift")
HOTKEY_KEY = os.getenv("VOCATYPE_HOTKEY_KEY", ".")

# Audio
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1

# LM Studio
LM_STUDIO_URL = os.getenv("VOCATYPE_LM_STUDIO_URL", "http://localhost:1234/v1")

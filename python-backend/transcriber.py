"""Whisper transcription engine using faster-whisper (CTranslate2).

faster-whisper is 3-4x faster than vanilla whisper.cpp on CPU because
CTranslate2 uses Intel MKL optimizations and int8 quantization.
"""
import logging
from pathlib import Path
from typing import Optional

from faster_whisper import WhisperModel

from config import WHISPER_MODEL, WHISPER_DEVICE, WHISPER_COMPUTE_TYPE, MODELS_DIR

logger = logging.getLogger(__name__)

# Singleton — loaded once, reused across requests
_model: Optional[WhisperModel] = None


def get_model() -> WhisperModel:
    """Get or initialize the Whisper model (lazy singleton).

    Downloads the model on first call from HuggingFace if not cached.
    Models are stored in the `models/` directory.

    Available sizes:
      tiny      ~75 MB  — fastest, least accurate
      base      ~140 MB — good for short phrases
      small     ~460 MB — best balance (default)
      medium    ~1.5 GB — very accurate, needs more RAM
      large-v3  ~3 GB   — best accuracy, needs GPU
    """
    global _model
    if _model is None:
        logger.info(
            "Loading Whisper model '%s' on %s (compute_type=%s)...",
            WHISPER_MODEL,
            WHISPER_DEVICE,
            WHISPER_COMPUTE_TYPE,
        )
        _model = WhisperModel(
            WHISPER_MODEL,
            device=WHISPER_DEVICE,
            compute_type=WHISPER_COMPUTE_TYPE,
            download_root=str(MODELS_DIR),
            local_files_only=False,
        )
        logger.info("Whisper model '%s' loaded successfully", WHISPER_MODEL)
    return _model


def transcribe_audio(
    audio_samples: list[float],
    language: Optional[str] = None,
) -> str:
    """Transcribe raw float32 audio samples at 16kHz to text.

    Args:
        audio_samples: List of float32 audio samples (16kHz, mono).
        language: Optional language code (e.g., 'en', 'ar').
                  Omit or pass None for auto-detection.

    Returns:
        Transcribed text string. Empty string if nothing detected.

    Raises:
        RuntimeError: If transcription fails.
    """
    if not audio_samples:
        return ""

    model = get_model()

    segments, info = model.transcribe(
        audio_samples,
        language=language or None,
        beam_size=5,
        vad_filter=True,  # Voice activity detection — skips silence
        vad_parameters=dict(
            min_silence_duration_ms=500,
        ),
    )

    # Log detected language
    logger.debug(
        "Transcription: language=%s (prob=%.2f), duration=%.1fs",
        info.language,
        info.language_probability,
        info.duration,
    )

    # Join all segments
    text = " ".join(segment.text.strip() for segment in segments)
    logger.info("Transcribed %d characters in %.1fs", len(text), info.duration)
    return text


def get_model_info() -> dict:
    """Get information about the currently loaded model."""
    return {
        "model": WHISPER_MODEL,
        "device": WHISPER_DEVICE,
        "compute_type": WHISPER_COMPUTE_TYPE,
        "loaded": _model is not None,
    }


def unload_model():
    """Release the model from memory. Next call to get_model() will reload."""
    global _model
    _model = None
    logger.info("Whisper model unloaded from memory")

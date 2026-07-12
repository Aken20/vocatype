"""Audio capture using sounddevice (WASAPI backend on Windows).

Captures mono float32 audio at 16kHz — the native format Whisper expects.
"""
import logging
import threading
from typing import Optional

import numpy as np
import sounddevice as sd

from config import AUDIO_SAMPLE_RATE, AUDIO_CHANNELS

logger = logging.getLogger(__name__)


class AudioRecorder:
    """Records audio from the default microphone using WASAPI.

    Usage:
        recorder = AudioRecorder()
        recorder.start()
        # ... user speaks ...
        samples = recorder.stop()
        # samples is a list[float] at 16kHz mono
    """

    def __init__(self):
        self._stream: Optional[sd.InputStream] = None
        self._buffer: list[np.ndarray] = []
        self._recording = False
        self._lock = threading.Lock()
        self._latest_level = 0.0  # For UI audio level meter

    @property
    def is_recording(self) -> bool:
        return self._recording

    @property
    def audio_level(self) -> float:
        """Current audio level (0.0 to 1.0) for UI visualization."""
        return self._latest_level

    def start(self, device_id: Optional[int] = None):
        """Start recording audio from the microphone.

        Args:
            device_id: Specific audio input device ID, or None for default.
        """
        if self._recording:
            logger.warning("Already recording, ignoring duplicate start")
            return

        self._buffer = []
        self._recording = True
        self._latest_level = 0.0

        def callback(indata: np.ndarray, frames: int, time_info, status):
            if status:
                logger.warning("Audio callback status: %s", status)
            with self._lock:
                self._buffer.append(indata.copy())
                # Compute RMS level for UI meter
                rms = np.sqrt(np.mean(indata ** 2))
                self._latest_level = min(float(rms) * 10, 1.0)  # Scale to 0-1

        try:
            self._stream = sd.InputStream(
                samplerate=AUDIO_SAMPLE_RATE,
                channels=AUDIO_CHANNELS,
                device=device_id,
                dtype=np.float32,
                callback=callback,
            )
            self._stream.start()
            logger.info(
                "Audio recording started (device=%s, sr=%dHz, channels=%d)",
                device_id or "default",
                AUDIO_SAMPLE_RATE,
                AUDIO_CHANNELS,
            )
        except Exception as e:
            self._recording = False
            logger.error("Failed to start audio stream: %s", e)
            raise

    def stop(self) -> list[float]:
        """Stop recording and return captured audio as a flat list of floats.

        Returns:
            List of float32 audio samples at 16kHz mono.
            Empty list if no audio was captured.
        """
        if not self._recording:
            return []

        self._recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            if not self._buffer:
                logger.warning("No audio data captured")
                return []

            audio = np.concatenate(self._buffer, axis=0)
            self._buffer = []

        duration = len(audio) / AUDIO_SAMPLE_RATE
        flat = audio.flatten().tolist()
        logger.info(
            "Recording stopped: %.1fs, %d samples, %d bytes",
            duration,
            len(flat),
            len(flat) * 4,
        )
        return flat

    @staticmethod
    def list_devices() -> list[dict]:
        """List available audio input devices.

        Returns:
            List of dicts with id, name, channels, sample_rate, is_default.
        """
        devices = []
        default_input = sd.default.device[0]

        for i, dev in enumerate(sd.query_devices()):
            if dev["max_input_channels"] > 0:
                devices.append(
                    {
                        "id": i,
                        "name": dev["name"],
                        "channels": dev["max_input_channels"],
                        "default_samplerate": int(dev["default_samplerate"]),
                        "is_default": i == default_input,
                    }
                )

        return devices


# Global recorder instance
recorder = AudioRecorder()

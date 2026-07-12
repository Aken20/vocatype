"""Orchestrates the full dictation pipeline: record → transcribe → clean → paste.

This is the core state machine of WhisperType. It:
  1. Listens for the hotkey (via HotkeyManager)
  2. Toggles recording on/off
  3. On stop: sends audio to Whisper, optionally cleans with LM Studio, pastes

Communicates real-time status to the frontend via WebSocket.
"""
import asyncio
import logging
from typing import Optional

from audio_capture import recorder as audio_recorder
from transcriber import transcribe_audio
from text_injector import inject_text

logger = logging.getLogger(__name__)


class DictationOrchestrator:
    """Manages the complete dictation lifecycle."""

    def __init__(self):
        self._is_dictating = False
        self._ws_clients: list = []  # WebSocket clients for status push

    @property
    def is_dictating(self) -> bool:
        return self._is_dictating

    def set_ws_clients(self, clients: list):
        """Register WebSocket clients for status broadcasting."""
        self._ws_clients = clients

    async def _broadcast(self, data: dict):
        """Send a message to all connected WebSocket clients."""
        dead = []
        for ws in self._ws_clients:
            try:
                await ws.send_json(data)
            except Exception:
                dead.append(ws)
        for ws in dead:
            if ws in self._ws_clients:
                self._ws_clients.remove(ws)

    async def start_dictation(self):
        """Begin recording from the microphone."""
        if self._is_dictating:
            logger.warning("Already dictating, ignoring start")
            return

        self._is_dictating = True
        audio_recorder.start()
        await self._broadcast({"type": "status", "isRecording": True})
        logger.info("🎤 Dictation started")

    async def stop_dictation(self) -> str:
        """Stop recording, transcribe, optionally clean, and paste.

        Returns:
            The final text that was pasted.
        """
        if not self._is_dictating:
            return ""

        self._is_dictating = False
        audio_samples = audio_recorder.stop()

        await self._broadcast({"type": "status", "isRecording": False, "state": "transcribing"})

        if not audio_samples:
            logger.warning("No audio captured — nothing to transcribe")
            await self._broadcast({"type": "status", "isRecording": False})
            return ""

        try:
            # 1. Transcribe with Whisper (CPU-bound — run in thread)
            import asyncio as _asyncio
            raw_text = await _asyncio.to_thread(transcribe_audio, audio_samples)

            if not raw_text.strip():
                logger.info("Transcription returned empty text")
                await self._broadcast({
                    "type": "status",
                    "isRecording": False,
                    "state": "idle",
                    "message": "Nothing detected — try speaking louder or closer to the mic",
                })
                return ""

            # 2. Optional: Clean with LM Studio (respect settings toggle)
            from routes.settings import is_llm_cleanup_enabled

            cleaned_text = raw_text.strip()
            if is_llm_cleanup_enabled():
                try:
                    from text_cleaner import clean_transcription
                    cleaned = await clean_transcription(cleaned_text)
                    if cleaned != cleaned_text:
                        cleaned_text = cleaned
                        logger.info("Text cleaned via LM Studio")
                except ImportError:
                    pass
                except Exception as e:
                    logger.debug("LM Studio cleanup skipped: %s", e)
            else:
                logger.info("LLM cleanup disabled — using raw transcription")

            # 3. Paste into active application
            inject_text(cleaned_text)

            logger.info("✅ Dictation complete: '%s'", cleaned_text[:80])

            await self._broadcast({
                "type": "status",
                "isRecording": False,
                "lastText": cleaned_text,
                "state": "done",
            })

            return cleaned_text

        except Exception as e:
            logger.exception("Dictation pipeline failed")
            await self._broadcast({
                "type": "status",
                "isRecording": False,
                "state": "error",
                "message": str(e),
            })
            return ""


# Global orchestrator instance
orchestrator = DictationOrchestrator()

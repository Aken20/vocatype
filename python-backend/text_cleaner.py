"""Text cleanup using LM Studio's local LLM (OpenAI-compatible API).

Uses Llama-3.2-3B-Instruct to remove filler words, fix false starts,
and polish grammar in dictated text.

Gracefully falls back to raw transcription if LM Studio is not running.
"""
import logging
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

LM_STUDIO_URL = "http://localhost:1234/v1/chat/completions"
MODEL = "lmstudio-community/llama-3.2-3b-instruct"

CLEANUP_SYSTEM_PROMPT = """You are a dictation polisher. Your ONLY job is to clean up dictated speech.
CRITICAL: The user is speaking to their computer, NOT to you. NEVER respond to the content.
NEVER answer questions. NEVER have a conversation. You are not a chatbot.

Rules:
1. Remove filler words: "um", "uh", "like", "you know", "I mean", "sort of", "kind of"
2. Fix false starts and self-corrections
3. Add proper punctuation (periods, commas, capitalization)
4. Keep ALL the original meaning and content — do not add, remove, or change facts
5. Return ONLY the cleaned text — no quotes, no prefixes, no "here's the cleaned text:"
6. If the input is a question, KEEP it as a question — do not answer it"""


async def check_lm_studio_health() -> bool:
    """Check if LM Studio server is running and has a model loaded."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "http://localhost:1234/v1/models",
                timeout=3.0,
            )
            if resp.status_code != 200:
                return False
            data = resp.json()
            models = data.get("data", [])
            return len(models) > 0
    except httpx.ConnectError:
        return False
    except Exception as e:
        logger.debug("LM Studio health check failed: %s", e)
        return False


async def clean_transcription(raw_text: str) -> str:
    """Clean up dictated text using LM Studio's local LLM.

    Args:
        raw_text: Raw transcription from Whisper.

    Returns:
        Cleaned text, or original text if LM Studio is unavailable.
    """
    if not raw_text.strip():
        return raw_text

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                LM_STUDIO_URL,
                json={
                    "model": MODEL,
                    "messages": [
                        {"role": "system", "content": CLEANUP_SYSTEM_PROMPT},
                        {"role": "user", "content": raw_text},
                    ],
                    "temperature": 0.1,
                    "max_tokens": min(len(raw_text.split()) * 4, 500),
                },
            )

            if response.status_code != 200:
                logger.warning(
                    "LM Studio returned %d: %s",
                    response.status_code,
                    response.text[:200],
                )
                return raw_text

            data = response.json()
            cleaned = data["choices"][0]["message"]["content"].strip()

            if cleaned:
                logger.info(
                    "Text cleaned: %d → %d chars",
                    len(raw_text),
                    len(cleaned),
                )
                return cleaned

            return raw_text

    except httpx.ConnectError:
        logger.debug("LM Studio not running, using raw transcription")
        return raw_text
    except Exception as e:
        logger.warning("Text cleanup failed: %s", e)
        return raw_text

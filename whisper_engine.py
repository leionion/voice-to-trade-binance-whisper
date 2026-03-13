"""
Whisper STT engine — local or API mode.
"""

from pathlib import Path
from typing import Optional

# Lazy load to avoid import cost when not used
_whisper_model = None


def transcribe_local(audio_path: str, model_name: str = "base.en") -> str:
    """Transcribe with local Whisper model."""
    import whisper
    global _whisper_model
    if _whisper_model is None or getattr(_whisper_model, "_name", "") != model_name:
        _whisper_model = whisper.load_model(model_name)
    result = _whisper_model.transcribe(audio_path, language="en", fp16=False)
    return (result.get("text") or "").strip()


def transcribe_local_bytes(wav_bytes: bytes, model_name: str = "base.en") -> str:
    """Transcribe from WAV bytes (writes to temp file)."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_bytes)
        path = f.name
    try:
        return transcribe_local(path, model_name)
    finally:
        Path(path).unlink(missing_ok=True)


def transcribe_api(audio_path: str, api_key: str) -> str:
    """Transcribe via OpenAI Whisper API."""
    from openai import OpenAI
    client = OpenAI(api_key=api_key)
    with open(audio_path, "rb") as f:
        response = client.audio.transcriptions.create(model="whisper-1", file=f)
    return (response.text or "").strip()


def transcribe_api_bytes(wav_bytes: bytes, api_key: str) -> str:
    """Transcribe from WAV bytes via API."""
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_bytes)
        path = f.name
    try:
        return transcribe_api(path, api_key)
    finally:
        Path(path).unlink(missing_ok=True)


def transcribe(
    wav_bytes: bytes,
    mode: str = "local",
    model_name: str = "base.en",
    api_key: str = "",
) -> str:
    """Unified transcribe: local or api."""
    if mode == "api" and api_key:
        return transcribe_api_bytes(wav_bytes, api_key)
    return transcribe_local_bytes(wav_bytes, model_name)

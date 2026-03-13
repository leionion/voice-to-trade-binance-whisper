"""
Audio capture — PyAudio stream, VAD trigger, WAV buffer.
Records from microphone until silence detected.
"""

import io
import struct
import wave
from typing import Optional

try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    pyaudio = None


def record_until_silence(
    sample_rate: int = 16000,
    silence_threshold: int = 500,
    silence_duration_ms: int = 800,
    chunk_size: int = 1024,
    max_duration_s: float = 30.0,
) -> tuple[Optional[bytes], float]:
    """
    Record from microphone until silence_duration_ms of silence.
    Returns (wav_bytes, duration_seconds).
    """
    if not PYAUDIO_AVAILABLE:
        raise RuntimeError(
            "PyAudio not installed. Run: pip install PyAudio. "
            "On Linux you may need: sudo apt install portaudio19-dev"
        )

    pa = pyaudio.PyAudio()
    stream = None
    frames = []
    silence_chunks = 0
    silence_chunks_needed = int((silence_duration_ms / 1000.0) * sample_rate / chunk_size)
    total_chunks_max = int(max_duration_s * sample_rate / chunk_size)
    duration_s = 0.0

    try:
        stream = pa.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=sample_rate,
            input=True,
            frames_per_buffer=chunk_size,
        )

        for i in range(total_chunks_max):
            data = stream.read(chunk_size, exception_on_overflow=False)
            frames.append(data)

            # RMS energy
            if len(data) >= 2:
                samples = struct.unpack(f"{len(data)//2}h", data)
                rms = (sum(s * s for s in samples) / len(samples)) ** 0.5
                if rms < silence_threshold:
                    silence_chunks += 1
                    if silence_chunks >= silence_chunks_needed and len(frames) > 10:
                        break
                else:
                    silence_chunks = 0

        duration_s = len(frames) * chunk_size / sample_rate
        wav_buf = io.BytesIO()
        with wave.open(wav_buf, "wb") as wav:
            wav.setnchannels(1)
            wav.setsampwidth(2)
            wav.setframerate(sample_rate)
            wav.writeframes(b"".join(frames))
        return wav_buf.getvalue(), duration_s

    finally:
        if stream:
            try:
                stream.stop_stream()
                stream.close()
            except Exception:
                pass
        pa.terminate()


def load_wav_bytes(wav_bytes: bytes) -> tuple[bytes, int]:
    """Validate WAV and return (bytes, sample_rate)."""
    with wave.open(io.BytesIO(wav_bytes), "rb") as wav:
        return wav_bytes, wav.getframerate()

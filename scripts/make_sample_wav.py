#!/usr/bin/env python3
"""Create a minimal WAV file for testing (e.g. for --file mode)."""
import wave
import struct
import sys

def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "sample.wav"
    duration_s = float(sys.argv[2]) if len(sys.argv) > 2 else 1.0
    sr = 16000
    n = int(sr * duration_s)
    with wave.open(path, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes(struct.pack(f"{n}h", *([0] * n)))
    print(f"Created {path} ({duration_s}s, {sr}Hz)")


if __name__ == "__main__":
    main()

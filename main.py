#!/usr/bin/env python3
"""
Voice-to-Trade Binance Whisper — main entry point.
Mic → Whisper → Intent Parser → Binance (paper or live).
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

import yaml

# Load .env if present (optional)
def _load_dotenv():
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip().strip("'\"").strip()
                if k and v:
                    os.environ.setdefault(k, v)

_load_dotenv()

from audio_capture import PYAUDIO_AVAILABLE, record_until_silence
from intent_parser import parse_intent
from whisper_engine import transcribe
from binance_executor import execute_order


def load_config(path: str = "config.yaml") -> dict:
    p = Path(path)
    if not p.is_absolute():
        p = Path(__file__).resolve().parent / path
    if not p.exists():
        return {}
    with open(p) as f:
        return yaml.safe_load(f) or {}


def _speak(text: str) -> None:
    """Optional TTS feedback (pyttsx3). Set ELEVENLABS_API_KEY for cloud TTS (optional)."""
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(
        description="Voice-to-Trade Binance Whisper — Say the trade. Watch it execute.",
    )
    parser.add_argument(
        "--mode",
        choices=["paper", "live"],
        default="paper",
        help="paper = validate, no real orders (default); live = real orders",
    )
    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Config file path",
    )
    parser.add_argument(
        "--file",
        help="Process WAV file instead of microphone (for testing)",
    )
    parser.add_argument(
        "--transcript",
        help="Use transcript directly instead of audio (for testing)",
    )
    args = parser.parse_args()

    config_path = Path(args.config) if Path(args.config).is_absolute() else Path(__file__).resolve().parent / args.config
    if not config_path.exists():
        example = Path(__file__).resolve().parent / "config.example.yaml"
        if example.exists():
            import shutil
            shutil.copy(example, config_path)
            print("Created config.yaml from config.example.yaml. Edit config.yaml with your settings.")
        else:
            print("ERROR: config.yaml not found. Copy config.example.yaml to config.yaml")
            sys.exit(1)
    config = load_config(str(config_path))
    if not config:
        print("ERROR: config.yaml is empty or invalid.")
        sys.exit(1)

    binance_cfg = dict(config.get("binance", {}))
    whisper_cfg = dict(config.get("whisper", {}))
    audio_cfg = config.get("audio", {})
    trading_cfg = config.get("trading", {})
    log_cfg = config.get("logging", {})

    # Env vars override config (for security: keep keys out of config files)
    if os.environ.get("OPENAI_API_KEY") and not whisper_cfg.get("api_key"):
        whisper_cfg["api_key"] = os.environ["OPENAI_API_KEY"]
    if os.environ.get("BINANCE_API_KEY") and not binance_cfg.get("api_key"):
        binance_cfg["api_key"] = os.environ["BINANCE_API_KEY"]
    if os.environ.get("BINANCE_API_SECRET") and not binance_cfg.get("api_secret"):
        binance_cfg["api_secret"] = os.environ["BINANCE_API_SECRET"]

    level = log_cfg.get("level", "INFO")
    logging.basicConfig(level=getattr(logging, level), format="%(message)s")
    logger = logging.getLogger(__name__)

    log_output = log_cfg.get("output", "logs/session.jsonl")
    log_path = Path(log_output)
    if not log_path.is_absolute():
        log_path = Path(__file__).resolve().parent / log_output
    log_path.parent.mkdir(parents=True, exist_ok=True)

    paper = args.mode == "paper"
    if not paper and (not binance_cfg.get("api_key") or not binance_cfg.get("api_secret")):
        logger.warning("Live mode requires API keys. Falling back to paper.")
        paper = True

    default_quote = trading_cfg.get("default_quote", "USDT")
    confirmation_audio = trading_cfg.get("confirmation_audio", True)
    executor_config = {
        **binance_cfg,
        "max_order_usdt": trading_cfg.get("max_order_usdt", 500),
    }

    # Validate --file before starting session
    if args.file:
        file_path = Path(args.file)
        if not file_path.is_absolute():
            file_path = Path(__file__).resolve().parent / args.file
        if not file_path.exists():
            print("ERROR: File not found:", args.file, file=sys.stderr)
            sys.exit(1)

    print("═" * 59)
    print(f"  VOICE-TO-TRADE  |  Session Start: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
    print("═" * 59)
    print()

    order_count = 0
    parse_errors = 0

    while True:
        try:
            if args.transcript:
                transcript = args.transcript
                wav_bytes = b""
                duration_s = 0
                ts = datetime.utcnow().strftime("%H:%M:%S UTC")
                logger.info(f"[{ts}] 📝  Transcript (direct): \"{transcript}\"")
                single_file = True
            elif args.file:
                file_path = Path(args.file)
                if not file_path.is_absolute():
                    file_path = Path(__file__).resolve().parent / args.file
                with open(file_path, "rb") as f:
                    wav_bytes = f.read()
                duration_s = len(wav_bytes) / 32000  # rough
                logger.info(f"Loaded {args.file} ({duration_s:.1f}s)")
                single_file = True
                transcript = None
            else:
                transcript = None
                if not PYAUDIO_AVAILABLE:
                    logger.error("PyAudio not available. Use --file to test with a WAV file.")
                    sys.exit(1)
                wav_bytes, duration_s = record_until_silence(
                    sample_rate=audio_cfg.get("sample_rate", 16000),
                    silence_threshold=audio_cfg.get("silence_threshold", 500),
                    silence_duration_ms=audio_cfg.get("silence_duration_ms", 800),
                )
                single_file = False

            if not args.transcript and len(wav_bytes) < 1000:
                logger.info("Audio too short, skipped")
                if single_file:
                    break
                continue

            if not args.transcript:
                ts = datetime.utcnow().strftime("%H:%M:%S UTC")
                logger.info(f"[{ts}] 🎙  Audio captured ({duration_s:.1f}s)")

                transcript = transcribe(
                wav_bytes,
                    mode=whisper_cfg.get("mode", "local"),
                    model_name=whisper_cfg.get("model", "base.en"),
                    api_key=whisper_cfg.get("api_key", ""),
                )
                logger.info(f"[{ts}] ✍  Whisper transcript: \"{transcript}\"")

            ts = datetime.utcnow().strftime("%H:%M:%S UTC")

            intent = parse_intent(transcript, default_quote)

            logger.info("[%s] 🔍  Parsed intent:", ts)
            logger.info("                    symbol  → %s", intent.symbol)
            logger.info("                    side    → %s", intent.side)
            logger.info("                    type    → %s", intent.order_type)
            logger.info("                    qty     → %s %s", intent.quantity, "USDT" if intent.quantity_in_usdt else intent.symbol.replace("USDT", ""))
            if intent.price:
                logger.info("                    price   → %s", f"{intent.price:,.2f}")

            if intent.parse_error:
                parse_errors += 1
                logger.warning(f"Parse error: {intent.parse_error}")
                log_entry = {
                    "ts": datetime.utcnow().isoformat() + "Z",
                    "transcript": transcript,
                    "intent": {"parse_error": intent.parse_error},
                    "result": {"success": False, "error": intent.parse_error},
                }
                with open(log_path, "a") as f:
                    f.write(json.dumps(log_entry) + "\n")
                if single_file:
                    break
                continue

            if confirmation_audio:
                _speak(f"{intent.side} {intent.quantity} {intent.symbol} {intent.order_type}")

            logger.info("[%s] ⚡  Sending order to Binance...", ts)

            result = execute_order(intent, executor_config, paper)

            log_entry = {
                "ts": datetime.utcnow().isoformat() + "Z",
                "transcript": transcript,
                "intent": {
                    "symbol": intent.symbol,
                    "side": intent.side,
                    "type": intent.order_type,
                    "qty": intent.quantity,
                    "price": intent.price,
                },
                "result": {
                    "success": result.success,
                    "order_id": result.order_id,
                    "status": result.status,
                    "avg_price": result.avg_price,
                    "executed_qty": result.executed_qty,
                    "latency_ms": result.latency_ms,
                    "error": result.error,
                },
            }
            with open(log_path, "a") as f:
                f.write(json.dumps(log_entry) + "\n")

            if result.success:
                order_count += 1
                status_emoji = "✅"
                if result.status == "FILLED":
                    logger.info(f"[{ts}] {status_emoji}  FILLED — orderId: {result.order_id}")
                    logger.info("                    avgPrice: %s USDT", f"{result.avg_price:,.2f}" if result.avg_price else "N/A")
                    logger.info("                    qty: %s", result.executed_qty)
                else:
                    logger.info(f"[{ts}] {status_emoji}  ACCEPTED — orderId: {result.order_id}")
                    logger.info("                    status: %s", result.status)
                if result.latency_ms:
                    logger.info("                    latency: %sms (mic → fill confirmation)", result.latency_ms)
            else:
                logger.error(f"[{ts}] ❌  Error: {result.error}")

            print()
            if single_file:
                break

        except KeyboardInterrupt:
            print()
            break
        except FileNotFoundError as e:
            logger.error("File not found: %s", e)
            sys.exit(1)
        except OSError as e:
            # No audio device, permission denied, etc. — unrecoverable in mic mode
            logger.error("Audio device error: %s", e)
            logger.info("Use --file or --transcript to test without a microphone.")
            sys.exit(1)
        except Exception as e:
            logger.exception("Error: %s", e)
            if args.file or args.transcript:
                sys.exit(1)
            # Mic mode: unrecoverable errors (e.g. device fail) exit above; other errors exit here
            sys.exit(1)

    print("═" * 59)
    print(f"  End of snippet  |  {order_count} orders  |  {parse_errors} parse errors")
    print("═" * 59)


if __name__ == "__main__":
    main()

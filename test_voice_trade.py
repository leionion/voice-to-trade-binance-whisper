#!/usr/bin/env python3
"""Test suite for voice-to-trade-binance-whisper (shipped features only)."""

import sys
from pathlib import Path

def test_intent_parser():
    from intent_parser import parse_intent

    cases = [
        ("buy point five btc at market", "BTCUSDT", "BUY", "MARKET", 0.5, None),
        ("limit sell 0.5 btc at 69500", "BTCUSDT", "SELL", "LIMIT", 0.5, 69500),
        ("buy half a bitcoin market", "BTCUSDT", "BUY", "MARKET", 0.5, None),
        ("short 200 USDT ETH limit 3200", "ETHUSDT", "SELL", "LIMIT", 200, 3200),
    ]
    for transcript, symbol, side, order_type, qty, price in cases:
        i = parse_intent(transcript, "USDT")
        assert i.symbol == symbol, f"symbol: {i.symbol}"
        assert i.side == side, f"side: {i.side}"
        assert i.order_type == order_type, f"type: {i.order_type}"
        assert i.quantity == qty, f"qty: {i.quantity}"
        assert i.price == price, f"price: {i.price}"
        assert i.parse_error is None
    print("OK: intent_parser")


def test_config():
    from main import load_config
    cfg = load_config("config.yaml")
    assert "whisper" in cfg
    assert "binance" in cfg
    assert "audio" in cfg
    print("OK: config")


def test_binance_executor_paper():
    from intent_parser import parse_intent
    from binance_executor import execute_order

    i = parse_intent("buy 0.001 btc at market", "USDT")
    r = execute_order(i, {"api_key": "", "api_secret": "", "max_order_usdt": 50000}, paper=True)
    assert r.success, r.error
    assert r.status in ("FILLED", "OPEN (GTC)")
    print("OK: binance_executor paper")


def test_main_transcript_mode():
    """Run main with --transcript to verify full pipeline."""
    import subprocess
    result = subprocess.run(
        [sys.executable, "main.py", "--mode", "paper", "--transcript", "buy 0.001 btc at market"],
        cwd=Path(__file__).parent,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert result.returncode == 0, f"exit {result.returncode}: {result.stderr}"
    out = result.stdout + result.stderr
    assert "FILLED" in out or "ACCEPTED" in out or "orderId" in out, f"Expected fill/accept in: {out[:500]}"
    print("OK: main --transcript")


def test_audit_log():
    """Verify audit log is written."""
    log_path = Path("logs/session.jsonl")
    if log_path.exists():
        lines = log_path.read_text().strip().split("\n")
        if lines:
            import json
            last = json.loads(lines[-1])
            assert "ts" in last
            assert "transcript" in last or "intent" in last
            print("OK: audit_log")
            return
    print("SKIP: audit_log (no logs yet)")


if __name__ == "__main__":
    errors = []
    for name, fn in [
        ("intent_parser", test_intent_parser),
        ("config", test_config),
        ("binance_executor", test_binance_executor_paper),
        ("main_transcript", test_main_transcript_mode),
        ("audit_log", test_audit_log),
    ]:
        try:
            fn()
        except Exception as e:
            errors.append(f"{name}: {e}")
            print(f"FAIL: {name} - {e}")

    if errors:
        sys.exit(1)
    print("\nAll tests passed.")

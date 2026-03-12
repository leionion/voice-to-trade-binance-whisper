<!-- voice-to-trade-binance-whisper | voice trading bot binance | whisper trading python -->
<!-- how to build voice trading bot python 2026 | binance voice command trading | speech to trade crypto -->
<!-- best voice trading bot binance 2026 | hands-free binance trading tool | voice controlled crypto bot -->
<!-- whisper api binance trading | binance speech recognition trading python | openai whisper trade executor -->
<!-- voice trade binance github | whisper binance bot full version | get voice trading bot binance access -->

<div align="center">

# Voice To Trade Binance Whisper

### *Say the trade. Watch it execute. Never touch the mouse again.*

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![OpenAI Whisper](https://img.shields.io/badge/OpenAI-Whisper-412991?style=for-the-badge&logo=openai&logoColor=white)](https://github.com/openai/whisper)
[![Binance API](https://img.shields.io/badge/Binance-API%20v3-F0B90B?style=for-the-badge&logo=binance&logoColor=black)](https://binance-docs.github.io/apidocs/)
[![Status](https://img.shields.io/badge/Status-Beta%20%7C%20Shipping%20Daily-orange?style=for-the-badge)](https://github.com/leionion/voice-to-trade-binance-whisper)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)

**[→ How It Works](#-how-voice-to-trade-works) · [→ Live Output Demo](#-live-execution-output) · [→ vs. Other Tools](#-how-this-compares) · [→ Full Version](#-want-the-full-private-build)**

> ⚡ This repo ships the core execution engine. The private build adds multi-pair queuing, confidence scoring, and exchange-agnostic routing. Serious traders — keep reading.

</div>

---

## 🧠 How Voice-to-Trade Works

Most traders lose 2–4 seconds per entry clicking through interfaces. At 20 trades a day, that's compounding latency you never get back.

This utility closes that gap with a three-stage pipeline:
```
╔══════════════════╗     ╔═══════════════════════╗     ╔══════════════════════╗
║  MICROPHONE INPUT ║────▶║  WHISPER STT ENGINE    ║────▶║  INTENT PARSER       ║
║                  ║     ║  (local or API mode)   ║     ║  side / symbol /     ║
║  "Buy 0.5 BTC    ║     ║                        ║     ║  size / order type   ║
║   at Market"     ║     ║  ~300ms transcription  ║     ║                      ║
╚══════════════════╝     ╚═══════════════════════╝     ╚══════════╦═══════════╝
                                                                   │
                                          ╔════════════════════════▼═══════════╗
                                          ║  BINANCE API EXECUTOR              ║
                                          ║  POST /api/v3/order                ║
                                          ║  → confirmed fill in <800ms total  ║
                                          ╚════════════════════════════════════╝
```

**You speak. The order is placed.** The parser handles natural phrasing — "buy half a bitcoin market", "short 200 USDT ETH limit 3200", "close my BTC position" — without rigid command syntax.

---

## 📡 Live Execution Output

Real session log from paper trading mode:
```
═══════════════════════════════════════════════════════════
  VOICE-TO-TRADE  |  Session Start: 2026-03-11 08:42:03 UTC
═══════════════════════════════════════════════════════════

[08:42:11 UTC] 🎙  Audio captured (1.2s)
[08:42:11 UTC] ✍  Whisper transcript: "buy point five btc at market"
[08:42:11 UTC] 🔍  Parsed intent:
                    symbol  → BTCUSDT
                    side    → BUY
                    type    → MARKET
                    qty     → 0.5 BTC
[08:42:11 UTC] ⚡  Sending order to Binance...
[08:42:12 UTC] ✅  FILLED — orderId: 18472910384
                    avgPrice: 68,412.30 USDT
                    qty: 0.5 BTC
                    latency: 741ms (mic → fill confirmation)

───────────────────────────────────────────────────────────

[08:44:55 UTC] 🎙  Audio captured (1.8s)
[08:44:55 UTC] ✍  Whisper transcript: "limit sell 0.5 btc at 69500"
[08:44:56 UTC] 🔍  Parsed intent:
                    symbol  → BTCUSDT
                    side    → SELL
                    type    → LIMIT
                    qty     → 0.5 BTC
                    price   → 69,500.00
[08:44:56 UTC] ✅  ACCEPTED — orderId: 18473021100
                    status: OPEN (GTC)
                    latency: 612ms

═══════════════════════════════════════════════════════════
  End of snippet  |  2 orders  |  0 parse errors
═══════════════════════════════════════════════════════════
```

Sub-800ms from voice to confirmed fill. No clicks. No keyboard.

---

## ⚡ Key Features of the Binance Whisper Voice Trading Engine

- **Natural language command parsing** — no rigid syntax to memorize; handles fractional quantities, ticker aliases, and order type variations
- **Whisper local mode** — run the STT engine fully offline; your voice audio never leaves your machine
- **Paper trading mode** — dry-run every command against live Binance prices with zero capital risk
- **Real-time audio feedback** — spoken confirmation of parsed intent before execution (optional, configurable)
- **Hot-reload config** — swap API keys, trading pairs, and risk limits without restarting the session
- **Execution log** — timestamped JSON log of every transcript, parsed intent, and API response for audit trails

---

## 🆚 How This Compares to Other Binance Trading Tools

| Tool / Approach | Voice Input | Natural Language | Local STT | Paper Mode | Latency (approx.) | Cost |
|---|---|---|---|---|---|---|
| **voice-to-trade-binance-whisper** | ✅ | ✅ | ✅ Optional | ✅ | ~700ms | Free / open |
| Binance Web UI (manual) | ❌ | ❌ | — | ❌ | 3–6s (human) | Free |
| TradingView Alerts → Webhook | ❌ | ❌ | — | ⚠️ Limited | 1–3s | $15–60/mo |
| 3Commas / Pionex bots | ❌ | ❌ | — | ✅ | 1–4s | $29+/mo |
| Custom keyword-command scripts | ⚠️ Rigid | ❌ | ✅ | Varies | Varies | DIY time |
| Cloud STT + Binance webhook | ✅ | ⚠️ | ❌ | ❌ | 1.5–3s+ | $0.006/15s |

**The gap:** Every existing voice-adjacent solution either requires rigid command syntax, routes your audio through a cloud provider, or doesn't connect to execution at all. This project is the only open pipeline that goes from natural speech → Binance fill with a local model option.

---

## 🏗️ System Architecture for Voice-to-Trade Binance
```
╔══════════════════════════════════════════════════════════════╗
║                    RUNTIME ARCHITECTURE                      ║
╠════════════════════╦═════════════════════╦═══════════════════╣
║  AUDIO LAYER       ║  PROCESSING LAYER   ║  EXECUTION LAYER  ║
║                    ║                     ║                   ║
║  PyAudio stream    ║  Whisper (local)     ║  python-binance   ║
║  VAD trigger       ║    OR               ║  REST API v3      ║
║  WAV buffer        ║  Whisper API        ║  HMAC-SHA256 sig  ║
║                    ║                     ║                   ║
║  ─────────────     ║  Intent Parser      ║  Order validator  ║
║  mic → .wav        ║  regex + NLP rules  ║  risk gate check  ║
║  silence detect    ║  symbol resolver    ║  paper/live mode  ║
╚════════════════════╩═════════════════════╩═══════════════════╝
         │                    │                      │
         └────────────────────┴──────────────────────┘
                          JSON audit log
```

**Data privacy note:** In local Whisper mode, audio is transcribed entirely on-device. Nothing is sent to OpenAI. Your trading commands, portfolio activity, and voice patterns stay on your machine.

---

## 🔧 Installation — Binance Whisper Voice Trading Bot

**Requirements:** Python 3.10+, PortAudio (for PyAudio), ffmpeg

**Step 1 — Clone the repository**
```bash
git clone https://github.com/leionion/voice-to-trade-binance-whisper.git
cd voice-to-trade-binance-whisper
```

**Step 2 — Create a virtual environment and install dependencies**
```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Step 3 — Install Whisper and ffmpeg**
```bash
pip install openai-whisper
# macOS:  brew install ffmpeg
# Ubuntu: sudo apt install ffmpeg
# Windows: https://ffmpeg.org/download.html
```

**Step 4 — Configure your credentials and risk parameters**
```bash
cp config.example.yaml config.yaml
nano config.yaml   # Add your Binance API key/secret and tune settings
```

**Step 5 — Start in paper trading mode (always start here)**
```bash
python main.py --mode paper
```

> ⚠️ `--mode paper` runs all commands against live prices but places **no real orders**. Verify parsing is correct for your speech patterns before switching to `--mode live`.

---

## ⚙️ Configuration Reference
```yaml
# config.yaml — voice-to-trade-binance-whisper

binance:
  api_key: "YOUR_BINANCE_API_KEY"
  api_secret: "YOUR_BINANCE_API_SECRET"
  testnet: false                  # true = Binance testnet, false = live

whisper:
  model: "base.en"                # tiny.en / base.en / small.en / medium.en
  mode: "local"                   # "local" (offline) or "api" (OpenAI cloud)
  api_key: ""                     # Only required if mode: api

audio:
  silence_threshold: 500          # Lower = more sensitive mic trigger
  silence_duration_ms: 800        # ms of silence before segment ends
  sample_rate: 16000

trading:
  mode: "paper"                   # "paper" or "live" — change deliberately
  default_quote: "USDT"           # Appended when symbol is ambiguous
  max_order_usdt: 500             # Hard cap per single voice order
  confirmation_audio: true        # Speak back parsed intent before sending

logging:
  level: "INFO"
  output: "logs/session.jsonl"    # Append-only JSONL audit trail
```

---

## 🗺️ Roadmap — Voice to Trade Binance Whisper

| Status | Feature | Version |
|---|---|---|
| ✅ Shipped | Core audio capture → Whisper → Binance execution loop | v0.1.0 |
| ✅ Shipped | Paper trading mode with live price validation | v0.1.0 |
| ✅ Shipped | Natural language intent parser (market / limit / qty) | v0.1.2 |
| ✅ Shipped | JSON audit log with full transcript + API response | v0.1.3 |
| 🔨 Active | Spoken confirmation before execution with approve/cancel | v0.2.0 |
| 🔨 Active | Stop-loss and take-profit voice commands | v0.2.0 |
| 🔨 Active | Multi-pair session context ("close my ETH", without re-stating) | v0.2.1 |
| 🔜 Planned | Confidence scoring — low-confidence transcripts held for review | v0.3.0 |
| 🔜 Planned | Bybit + OKX routing (private build) | v0.4.0 |
| 🔜 Planned | Wake-word activation ("Hey Trader, buy...") | v0.4.0 |
| 🔜 Planned | Portfolio summary voice query ("What's my PnL today?") | v0.5.0 |

---

## 🔒 Want the Full Private Build?

The public repo ships the core pipeline. The private build is for traders who need this to actually work in a live session.

**What's in the private build that isn't here:**

- **Multi-pair session memory** — "add 100 to the ETH position" works because it remembers what you're holding
- **Confidence gate** — orders with low transcription confidence are held and read back; you approve or cancel by voice
- **Exchange-agnostic router** — same voice commands, routes to Binance / Bybit / OKX based on config
- **Wake-word activation** — always-on listening with a trigger phrase so the mic isn't continuously recording
- **Risk layer** — per-symbol max exposure, daily loss limit, and portfolio concentration checks before any order fires
- **Pre-built intent library** — 40+ tested command phrasings across 4 accents to reduce parse errors

---

**Who this is for:**

| Profile | Why this matters to you |
|---|---|
| Active Binance day traders doing 10+ trades/session | Keyboard/click latency adds up; voice removes it entirely |
| Algo traders backtesting new execution workflows | Paper mode + JSON logs give you a clean data layer to build on |
| Developers building voice-first trading interfaces | The intent parser and audio pipeline are the hard part — this solves it |
| Traders with accessibility needs or multi-monitor setups | Hands-free execution is a workflow change, not a gimmick |

---

**How to reach me:**

**GitHub:** [@leionion](https://github.com/leionion)

When you reach out, mention three things:
1. How you currently execute trades on Binance (manual, alerts, bot)
2. Which part of the private build matters most to you
3. Whether you need paper-only access first or you're ready to test live

That's it. No pitch deck, no form. I respond to traders who've actually read the repo.

> The gap between this repo and the private build isn't time. It's features that only make sense once you've watched a miscaptured voice command try to place an order. The private build was built after that happened.

---

## ⚠️ Risk Disclaimer

**This software is in active beta development.** Voice-to-text transcription errors, network failures, and parser edge cases can produce unexpected order behavior. Always:

- Start with `--mode paper` and validate your specific speech patterns before going live
- Set `max_order_usdt` to a value you are comfortable losing in a worst-case misparse
- Never leave a live session unmonitored
- This is not financial advice. Trading cryptocurrencies involves substantial risk of loss.
- The developers of this software are not responsible for financial losses resulting from its use

---

<div align="center">

**Built with:** Python · OpenAI Whisper · python-binance · PyAudio · ffmpeg

*Say the trade. Watch it execute.*

[![GitHub](https://img.shields.io/badge/Contact-@leionion-181717?style=for-the-badge&logo=github)](https://github.com/leionion)

</div>

<!-- get voice trading bot binance | voice-to-trade-binance-whisper full version | contact leionion -->
<!-- binance voice trading private build | whisper binance bot full access | hands-free binance trading private -->
<!-- binance whisper bot developer contact | voice trade executor private version | leionion github trading bot -->

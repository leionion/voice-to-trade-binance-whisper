# Voice-to-Trade Binance Whisper — Execution Commands

## One-time setup
```bash
cd /root/voice-to-trade-binance-whisper
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install openai-whisper
sudo apt install portaudio19-dev ffmpeg    # Linux
pip install PyAudio
cp config.example.yaml config.yaml
```

## Test (no microphone, no API keys)
```bash
cd /root/voice-to-trade-binance-whisper
source venv/bin/activate
python main.py --mode paper --transcript "buy 0.001 btc at market"
```

## Run full test suite
```bash
python test_voice_trade.py
```

## Test with WAV file
```bash
python scripts/make_sample_wav.py sample.wav 0.5
python main.py --mode paper --file sample.wav
```

## Live microphone mode (requires PyAudio + PortAudio)
```bash
python main.py --mode paper
```
Press Ctrl+C to stop.

## Live trading (requires Binance API keys in .env or config.yaml)
```bash
python main.py --mode live
```

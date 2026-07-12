# 🎙️ WhisperType

> **Press a hotkey. Speak. Your words appear anywhere. 100% local.**

WhisperType is a fully-local Windows voice dictation app inspired by [Voquill](https://github.com/voquill/voquill). Press `Ctrl+Shift+F12`, speak naturally, and your words appear in any text field — cleaned up by a local AI.

## ✨ Features

- 🎤 **Voice-to-text anywhere** — dictate into any app, any text field
- 🤖 **AI text cleanup** — removes "um", "uh", fixes grammar (local LLM via LM Studio)
- 📋 **Personal dictionary** — custom terms so Whisper gets your names right
- 📜 **Transcription history** — browse and replay past dictations
- 🪟 **Floating overlay pill** — always-on-top indicator shows recording state
- 🔒 **100% local** — no cloud, no API keys, no internet needed
- ⚡ **Fast** — faster-whisper is 3-4x faster than vanilla whisper.cpp

## 🏗️ Architecture

```
Ctrl+Shift+F12 → WASAPI mic → faster-whisper (small) → Llama-3.2-3B → clipboard paste
                              ↑ Python sidecar          ↑ LM Studio
                              localhost:9877            localhost:1234

┌─ Tauri Shell (Rust) ─────────────────────────┐
│  ┌─ React Frontend (TypeScript) ──────────┐  │
│  │  Settings · History · Dictionary · Pill│  │
│  └────────────────────────────────────────┘  │
│  System tray · Auto-start · Window mgmt      │
└──────────────────────────────────────────────┘
         ↕
┌─ Python Sidecar (FastAPI) ───────────────────┐
│  Audio · Transcription · Hotkeys · Injection │
└──────────────────────────────────────────────┘
         ↕ (optional)
┌─ LM Studio (Local SLM) ──────────────────────┐
│  Llama-3.2-3B-Instruct · Text cleanup        │
└──────────────────────────────────────────────┘
```

## 📋 Prerequisites

- **Windows 10/11**
- **Python 3.11+** — for the transcription backend
- **Node.js 18+** — for the Tauri/React frontend
- **Rust toolchain** — for the Tauri shell
- **LM Studio** (optional) — for AI text cleanup

## 🚀 Quick Start

```bash
# 1. Clone
git clone https://github.com/Aken20/whispertype.git
cd whispertype

# 2. Python backend
cd python-backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py

# 3. Tauri frontend (new terminal)
cd tauri-app
npm install
npm run tauri dev
```

Press `Ctrl+Shift+F12` to start dictating!

## 🧠 AI Cleanup (Optional)

For grammar polishing and filler-word removal:

1. Install [LM Studio](https://lmstudio.ai/)
2. Download `Llama-3.2-3B-Instruct` (Q4_K_M)
3. Start the local server
4. WhisperType auto-detects and enables cleanup

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Desktop Shell | Tauri 2.x (Rust) |
| Frontend | React 18 + TypeScript + Zustand + Tailwind |
| Backend | Python 3.11 + FastAPI |
| Transcription | faster-whisper (CTranslate2) |
| Audio | sounddevice (WASAPI) |
| Text Cleanup | LM Studio (Llama-3.2-3B-Instruct) |
| Storage | SQLite (aiosqlite) |

## 📄 License

MIT — see [LICENSE](LICENSE)

## 🙏 Acknowledgments

Inspired by [Voquill](https://github.com/voquill/voquill), the open-source voice dictation app. WhisperType reimagines the same concept for a fully-local Windows experience using Python's faster ML ecosystem.

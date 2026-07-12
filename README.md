# 🎙️ VocaType

<div align="center">

**Press a hotkey. Speak. Your words appear anywhere. 100% local.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11+-green.svg)](https://python.org)
[![Tauri 2.x](https://img.shields.io/badge/Tauri-2.x-orange.svg)](https://tauri.app)
[![faster-whisper](https://img.shields.io/badge/Whisper-small%20%7C%20CUDA-purple.svg)](https://github.com/SYSTRAN/faster-whisper)

</div>

VocaType is a fully-local Windows voice dictation app inspired by [Voquill](https://github.com/voquill/voquill). Press `Ctrl+Shift+.`, speak naturally, and your words appear in any text field — optionally cleaned up by a local AI running in LM Studio.

> **No cloud. No API keys. No internet.** Everything runs on your machine.

## ✨ Features

| | |
|---|---|
| 🎤 **Dictate anywhere** | Speak into any text field — browser, VS Code, Notion, terminal |
| 🤖 **AI Polish** | Local LLM removes filler words, fixes grammar (toggle on/off) |
| 🪟 **Floating pill** | Always-on-top indicator — blue when idle, pulses when recording |
| ⚡ **GPU accelerated** | CUDA support via faster-whisper — near real-time transcription |
| 🔒 **100% local** | All processing on your machine. Zero data leaves your computer |
| ⌨️ **Global hotkey** | `Ctrl+Shift+.` from any app — no need to switch windows |

## 🏗️ Architecture

```
Ctrl+Shift+. → WASAPI mic → faster-whisper (small) → optional LM Studio → clipboard paste
         ↑ Tauri shell            ↑ Python sidecar              ↑ Llama-3.2-3B
         localhost:5174           localhost:9877               localhost:1234
```

| Layer | Stack |
|---|---|
| Desktop Shell | Tauri 2.x (Rust) |
| Frontend | React 18 + TypeScript + Zustand + Tailwind CSS |
| Backend | Python 3.11 + FastAPI + WebSocket |
| Transcription | faster-whisper (CTranslate2) — CPU or CUDA |
| Audio | sounddevice (WASAPI) — low-latency on Windows |
| Text Cleanup | LM Studio — Llama-3.2-3B-Instruct (optional) |
| Keyboard Hook | SetWindowsHookEx (low-level, no conflicts) |
| Overlay Pill | Native tkinter window — frameless, always-on-top |

## 🚀 Quick Start

### Prerequisites

- **Windows 10/11**
- **Python 3.11+** — [download](https://python.org)
- **Node.js 18+** — [download](https://nodejs.org)
- **Rust toolchain** — `winget install Rustlang.Rustup`
- **LM Studio** (optional) — for AI text polish

### Setup

```powershell
# Clone
git clone https://github.com/Aken20/vocatype.git
cd vocatype

# Python backend (Terminal 1)
cd python-backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python main.py

# Tauri frontend (Terminal 2)
cd tauri-app
npm install
npm run tauri dev
```

Press `Ctrl+Shift+.` and start dictating. The floating pill appears automatically.

### GPU Acceleration (CUDA)

VocaType auto-detects CUDA GPUs. If transcription is slow, install CUDA 12 toolkit:

```powershell
winget install --id NVIDIA.CUDA -v 12.6
```

Or use the bundled pip package (slower but no system install needed):
```powershell
pip install nvidia-cublas-cu12
```

### AI Polish (Optional)

1. Install [LM Studio](https://lmstudio.ai/)
2. Download `Llama-3.2-3B-Instruct` (Q4_K_M quantization, ~2GB)
3. Start the local server (default port 1234)
4. Toggle **✨ AI Polish** in the VocaType UI

The app works fine without LM Studio — just toggles off gracefully.

## 🎮 Usage

| Action | How |
|---|---|
| Start/stop dictation | `Ctrl+Shift+.` or click the **🎤** button |
| Toggle AI Polish | Switch in the main window |
| Move pill | Click and drag anywhere on the pill |
| Close pill | Click **×** or right-click the pill |
| Re-open pill | Restart the backend (pill auto-starts) |

## 🛠️ Development

```powershell
# Backend changes: just restart Python
Ctrl+C && python main.py

# Frontend changes: Tauri rebuilds automatically
npm run tauri dev  # watches Rust + Vite
```

### Project Structure

```
vocatype/
├── python-backend/         # FastAPI server + transcription engine
│   ├── main.py             # Entry point, routes, WebSocket
│   ├── transcriber.py      # faster-whisper wrapper (CPU/CUDA)
│   ├── audio_capture.py    # WASAPI mic capture
│   ├── hotkey_manager.py   # SetWindowsHookEx global hotkey
│   ├── text_injector.py    # Clipboard paste + SendInput
│   ├── text_cleaner.py     # LM Studio integration
│   ├── orchestrator.py     # Record → transcribe → clean → paste
│   ├── pill_overlay.py     # Native tkinter floating indicator
│   ├── config.py           # Environment-based configuration
│   └── routes/             # API route modules
├── tauri-app/              # Tauri + React frontend
│   ├── src/                # React components, store, hooks
│   ├── src-tauri/          # Rust shell (minimal — just hosts UI)
│   └── package.json
└── docs/                   # (coming soon)
```

## 📄 License

MIT — see [LICENSE](LICENSE). Do whatever you want with it.

## 🙏 Acknowledgments

Built on the shoulders of giants:

- [Voquill](https://github.com/voquill/voquill) — the original open-source voice dictation app that inspired this project
- [faster-whisper](https://github.com/SYSTRAN/faster-whisper) — CTranslate2-based Whisper inference
- [whisper.cpp](https://github.com/ggerganov/whisper.cpp) — the model format
- [Tauri](https://tauri.app) — lightweight desktop app framework
- [LM Studio](https://lmstudio.ai) — local LLM runner

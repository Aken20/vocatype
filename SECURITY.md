# Security Policy

## Supported Versions

VocaType is currently in developer preview. Security updates will be provided for the latest release only.

| Version | Supported |
|---|---|
| 0.1.x (preview) | ✅ |
| < 0.1.0 | ❌ |

## Reporting a Vulnerability

**Do not open a public issue.** Instead, report vulnerabilities privately:

- **Email**: Create a GitHub Security Advisory at https://github.com/Aken20/vocatype/security/advisories/new
- **Response time**: We aim to acknowledge within 48 hours and provide a fix within 7 days.

## Security Model

VocaType runs entirely on your machine. No data leaves your computer.

- **Audio**: Captured locally, never uploaded.
- **Transcription**: Processed by faster-whisper running locally.
- **AI Polish**: If enabled, text is sent to LM Studio on `localhost:1234` — never to external servers.
- **Clipboard**: Dictated text is pasted then immediately cleared from the clipboard.
- **Keystrokes**: The global hotkey hook only detects `Ctrl+Shift+.` — it does not log, store, or transmit any keystrokes.
- **Network**: The Python backend binds to `127.0.0.1` only. No external network access required (except first-run Whisper model download from HuggingFace).

## Dependencies

We monitor dependencies via Dependabot. If you discover a vulnerability in a dependency, please report it using the process above.

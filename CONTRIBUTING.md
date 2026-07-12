# Contributing to WhisperType

Thanks for considering contributing! Here's how to get started.

## Development Setup

See the [Quick Start](#) in the README for full setup instructions.

### Before submitting

- **Backend**: ensure `python main.py` starts without errors
- **Frontend**: ensure `npm run tauri dev` compiles and renders
- **Hotkey**: test `Ctrl+Shift+.` triggers dictation
- **Pill**: verify the floating overlay appears and reflects recording state

## Code Style

- **Python**: follow PEP 8. Keep functions small and focused.
- **TypeScript/React**: use functional components, Zustand for state, Tailwind for styling.
- **Rust**: minimal — the Tauri shell should stay thin. All business logic lives in Python.

## Commit Conventions

```
feat: add new feature
fix: bug fix
perf: performance improvement
chore: maintenance, cleanup
docs: documentation changes
refactor: code restructuring without behavior change
```

## Adding Features

1. Open an issue describing what you want to add
2. Discuss the approach before coding
3. Keep the architecture clean: Python owns business logic, Tauri is just the shell

## Questions?

Open an issue or start a discussion. We're friendly.

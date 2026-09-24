# My-AI-Agent

Sanctuary is a Windows AI agent you can talk to by text or voice. It answers using Gemini or a local Ollama model, and it can take actions on your PC: open apps and websites, take notes, rename episode files, send email and do quick calculations. Actions that can't be undone ask for your confirmation first.

## Features

- **Text and voice chat** through one command. Voice uses an offline wake word ("Hey Jarvis"), push-to-talk, offline speech-to-text (Whisper) and spoken replies.
- **Two model options:** Gemini (`gemini-2.5-flash`), or a local `hermes3:8b` through Ollama. Both use native tool calling.
- **Tools:** math, opening apps, websites and folders, notes, and renaming episodes.
- **Gmail:** list unread mail, search, read and summarize messages, create drafts (the default), and send (with confirmation).
- **Memory:** "remember that…" facts persist across runs, and the last conversation is resumed at startup (`--fresh` to skip).
- **Undo:** "what have you done?" and "undo that" for renames, notes and drafts. Every action is recorded in `logs/actions.jsonl`.
- **Streaming voice:** replies are spoken sentence by sentence while they are still being generated.
- **Safety:** sending email, closing apps, renaming files and undoing show the exact action and wait for y/N. Email content is treated as untrusted data.
- **Logs** in `logs/sanctuary.log`, including every approved or declined action.

## Requirements

- Windows (the app uses `os.startfile`, AppOpener and Windows speech)
- Python 3.12 and [uv](https://docs.astral.sh/uv/)
- For Gemini: a `GOOGLE_API_KEY`
- For the local model: [Ollama](https://ollama.com/) with `ollama pull hermes3:8b`
- For sending email: a Google OAuth `credentials.json` in the project folder

## Installation

```bash
git clone https://github.com/171801rohith/My-AI-Agent.git
cd My-AI-Agent
uv sync
```

Create a `.env` file in the project folder:

```
GOOGLE_API_KEY=your-key
```

## Usage

```bash
uv run sanctuary                     # text chat with Gemini
uv run sanctuary --mode voice        # voice chat: say "Hey Jarvis", hold SPACE to talk
uv run sanctuary --model ollama      # use the local Ollama model
uv run sanctuary --wake              # text chat, but wait for the wake word first
uv run sanctuary --fresh             # don't resume the previous conversation
```

To end a chat, type `exit` or `quit`, or say "exit chat". `python -m my_ai_agent` works as well.

On the first voice run, the wake word model (about 5 MB) and Whisper model (about 150 MB) download automatically. After that, voice runs fully offline. The first Gmail action opens a browser to sign in to Google once. Sign in again if the app asks after an update that needs new Gmail permissions.

Remembered facts and the recent conversation are stored in `data/`. Delete that folder to wipe the agent's memory.

## Configuration

Every setting has a default and can be overridden in `.env`:

| Variable | Default | Purpose |
|---|---|---|
| `GOOGLE_API_KEY` | none | Required for `--model gemini` |
| `GEMINI_MODEL` | `gemini-2.5-flash` | Gemini model |
| `OLLAMA_MODEL` | `hermes3:8b` | Local model (needs tool-calling support) |
| `WAKE_WORD` | `hey_jarvis` | Built-in openWakeWord model |
| `WAKE_THRESHOLD` | `0.5` | Raise it if the wake word triggers by mistake |
| `WHISPER_MODEL` | `base.en` | Use `small.en` for better accuracy at the cost of speed |
| `NOTES_DIR` | `<project>/notes` | Where the notes tool writes |

To add website shortcuts, edit `src/my_ai_agent/websites.py`.

## Project structure

```
src/my_ai_agent/
├── cli.py            # `sanctuary` command: picks mode, model and wake word
├── chat_session.py   # conversation loop shared by text and voice
├── settings.py       # all configuration, loaded from .env once
├── persona.py        # Sanctuary's system prompt
├── agents/           # Gemini and Ollama agents (common.py builds both)
├── tools/            # tools the agent can call, and the confirmation prompt
├── functions/        # file and browser helpers used by the tools
├── audio/            # wake word, speech-to-text, text-to-speech, playback
├── gmail_auth.py     # Google sign-in and token refresh
├── action_log.py     # record of actions taken, used by undo
├── memory_store.py   # remembered facts and recent conversation on disk
└── assets/           # intro and outro sounds
tests/                # offline pytest suite (run with: uv run pytest)
IMPROVEMENTS.md       # roadmap of fixes and planned features
```

## Development

```bash
uv run pytest
```

The tests run fully offline: models, Gmail, audio devices and the browser are all faked.

## License

This project currently does not specify a license.

## Author

- [171801rohith](https://github.com/171801rohith)

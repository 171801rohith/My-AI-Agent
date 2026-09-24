# Improvements Roadmap

This file lists the fixes and new features planned for My-AI-Agent. It is ordered by priority. Fix Part 1 before starting Part 2, because most new features depend on the refactor described there.

## Current state (verified by tests)

The test suite is in [`tests/`](tests/). It runs fully offline: Gemini, Gmail, the browser, AppOpener, `os.startfile`, audio and wake-word detection are all mocked.

```bash
uv sync            # installs pytest from the dev dependency group
uv run pytest -rx  # -rx lists the known bugs
```

Result before the fixes: **32 passed, 14 xfailed**. After fixes 1–11: **64 passed, 0 xfailed**.

### Progress

- [x] **P0 fixes 1–5.** Done, except the "restrict file tools to configured root folders" part of fix 1, which waits for the settings module (fix 15). Old recordings are still in git history; see fix 2.
- [x] **P1 fixes 6–11.** Done. Live runs against Gemini and Ollama are still to be checked by hand.
- [x] **P2 fixes 12–15.** Done:
  - `config/settings.py` loads configuration once.
  - Picovoice Leopard is replaced by offline faster-whisper, recording into memory (Leopard failed with the same activation error as Porcupine).
  - No busy-wait for the spacebar.
  - The Whisper model and audio mixer are each created once, on first use.
  - The wake word moved to openWakeWord ("Hey Jarvis").

  Deferred to feature 7 (streaming voice replies): moving `pyttsx3` off the event loop and removing the TTS file round trip. `pyttsx3`'s Windows speech engine is unreliable in worker threads, and nothing else runs concurrently yet.
- [x] **P3 fixes 16–19.** Done:
  - One `ChatSession` with `sanctuary --mode text|voice --model gemini|ollama`.
  - Personal values are in settings (`NOTES_DIR`) and `websites.py`.
  - The code is in the `src/my_ai_agent/` package with a `sanctuary` command.
  - Dependencies are cleaned up.
  - Logging goes to `logs/sanctuary.log`.

  **Note:** the fix tables below use the old file paths (`Tools/`, `Functions/`, `Agents/`, `service.py`). See the README for the new layout. 93 tests pass.
- [x] **Part 2 ★★★ features 1, 2, 7, 12 and 17.** Done: Gmail read/search/summarize, drafts by default, streaming spoken replies, long-term memory (facts and resumed conversation), and the action log with undo.
- [ ] **Remaining Part 2 features** (3–6, 8–11, 13–16, 18).
- **One-time action:** the next email sent will open a browser sign-in and create `token.json`. After that, `token.pickle` can be deleted.

- **Passed:** the core behavior works. This covers the math tools, opening known URLs and apps, creating notes, building and sending the Gmail message, reusing a cached Gmail token, detecting the exit phrase in voice chat, and a full agent turn (prompt, then ReAct answer) with an offline LLM.
- **xfailed:** each xfail is a known bug, and the test asserts the correct behavior. `xfail_strict = true` is set in `pyproject.toml`, so when a bug is fixed its test "unexpectedly passes" and the run fails. Remove the `@pytest.mark.xfail` marker in the same commit as the fix.
- **Not covered by tests:** microphone recording, wake-word detection, TTS playback and live Gemini or Gmail calls all need hardware or network access. Check them by hand with `uv run main_voice_chat.py` after changes to `Functions/`.

---

## Part 1: Fixes

### P0: Safety and security

| # | Issue | Fix | Test |
|---|-------|-----|------|
| 1 | The LLM can send email, bulk-rename files, close apps and `os.startfile` any path without asking. `open_directory` will run a `.bat`/`.exe` if given one. In voice mode, a misheard phrase can trigger any of these. | Mark side-effecting tools and wrap them in a confirmation step that shows the exact action and waits for y/n. Check `os.path.isdir` in `open_directory`, and restrict file tools to configured root folders. | `test_open_directory_refuses_files` |
| 2 | Voice recordings are committed to git. The `.gitignore` entry `.input_audios` has a typo, and `input_audios/audio_in.wav` appears in 8 commits. Generated output WAVs are also tracked. | Ignore `input_audios/`, `output_audios/audio_out.wav` and `output_audios/temp.wav`, and run `git rm --cached` on them. If the repo is public, remove them from history with `git filter-repo`. | — |
| 3 | Gmail credentials: `token.pickle` is loaded with `pickle`, which runs code if the file is tampered with. Expired or revoked credentials are never refreshed. The unused `gmail.readonly` scope is requested. Paths depend on the current working directory. The sender address is hardcoded. | Use `Credentials.from_authorized_user_file("token.json")`, refresh when `creds.expired and creds.refresh_token`, otherwise run the OAuth flow again, and save with `creds.to_json()`. Resolve paths from the project root. Move the sender address to settings. | `test_get_gmail_service_refreshes_expired_token` |
| 4 | `mail_body` is inserted into the email's HTML without escaping. | Use `html.escape(mail_body)` and convert newlines to `<br>`. | `test_send_mail_escapes_html` |
| 5 | `rename_to_episodes` numbers files in `os.listdir` order, renames sub-folders, and stops halfway if a target name already exists. | Take only files, sort them in natural order, and build the full plan first. Preview and confirm it, then rename in two phases (temporary names, then final names). Use `f"E{i:02d}"`. | `test_rename_to_episodes_uses_natural_order`, `…_skips_directories`, `…_handles_existing_target_names` |

### P1: Correctness

| # | Issue | Fix | Test |
|---|-------|-----|------|
| 6 | The ReAct header in `config/system_prompt.py` lost its format examples ("use the following format:" is followed by nothing). This causes intermittent parse failures. | Switch to `FunctionAgent`, since Gemini supports native tool calling, and put only the persona in `system_prompt`. Alternatively, restore the full default ReAct header. | `test_system_prompt_describes_react_format` |
| 7 | Each user message reaches the LLM twice. It is passed as `user_msg` and also as the last `chat_history` entry, and `ctx` memory is overwritten every turn, which loses tool steps. The history list also grows without limit. | Keep one source of truth: `agent.run(prompt, ctx=ctx)` with a token-limited memory. Delete `messages`/`chatMessages` from both entry points. | `test_user_message_sent_to_llm_once` |
| 8 | Tools report success when they fail. `close_app` says "opened". `open_url` wraps a failure message in "Successfully opened…". `text_to_speech` swallows errors and returns `None`. | Low-level functions should raise. One wrapper at the tool layer should turn exceptions into clear error messages for the LLM. | `test_close_app_message`, `test_open_url_tool_reports_unknown_site_as_failure`, `test_text_to_speech_raises_on_failure` |
| 9 | `agent_ollama.py` doesn't import (`Tools` doesn't exist). It also runs the agent twice and iterates an async stream synchronously. | Replace both agent files with one `build_agent(provider, tools, persona)` factory. | `test_ollama_agent_imports` |
| 10 | The exit phrase is missed when the transcript has punctuation ("Exit chat."). | Normalize the transcript (lowercase, strip punctuation) and match `\b(exit\|quit) chat\b`. | `test_termination_with_punctuation` |
| 11 | `substract` is defined but never registered as a tool. Division by zero is not handled. | Register it as `subtract`, and return a clear error on division by zero. | `test_subtract_is_exposed_to_agent` |

### P2: Reliability and performance

| # | Issue | Fix |
|---|-------|-----|
| 12 | Waiting for the spacebar is a busy loop that pins a CPU core. `pyttsx3.runAndWait()` and recording block the event loop. | Use `keyboard.wait("space")` or an event for the key press, and move blocking audio work into `asyncio.to_thread`. |
| 13 | A new Leopard model is created on every utterance and never deleted. The openWakeWord model is loaded per wake. The mixer, LLM, tools and agent are all built at import time. | Create each once in a startup `App` object and release them in `finally` on shutdown. |
| 14 | Audio goes through fixed WAV files: 44.1 kHz stereo is written to disk, read back, and resampled. TTS makes two file round trips. | Record at `leopard.sample_rate` in mono and call `leopard.process(pcm)` in memory. Use temporary files or buffers for TTS, and drop pydub's private `_spawn`. |
| 15 | Missing API keys or `credentials.json` produce cryptic errors partway through a run. `load_dotenv()` is called in four modules. | Add one `config/settings.py` (pydantic-settings) that loads `.env` once and validates required keys at startup. |

### P3: Maintainability

| # | Issue | Fix |
|---|-------|-----|
| 16 | `main_live_chat.py` and `main_voice_chat.py` are about 70% the same code. Text chat requires the spoken wake word and has no exit command. | Create one `ChatSession` with an `InputSource` (text or voice) and an `OutputSink` (console, or console plus TTS), and add a `--mode text\|voice` flag. |
| 17 | Hardcoded personal values (`R:/MOVIES/...`, GitHub URL, sender email). Paths are resolved from the working directory in some places and from `__file__` in others. | Move these values to settings, resolve all paths from the project root, and document that the app is Windows-only. |
| 18 | Packaging: capitalized package folders with no `__init__.py`, a `dotenv` dependency instead of `python-dotenv`, unused `edge-tts`, the full `llama-index` meta-package, a README that refers to a non-existent `requirements.txt`, and `*.json` ignored everywhere. | Move the code into `src/my_ai_agent/` and add a `[project.scripts]` entry point. Clean up dependencies, document `uv sync` in the README, and ignore `credentials.json` and `token.json` by name. |
| 19 | No logging (only `print`), and the stream collected in `generateResponse` is never used. | Use `logging`, and either use the stream (see feature 7) or remove it. |

Suggested order: fix 1–5, then 6 and 7 together (switching to `FunctionAgent` with one memory solves both), then 8. After that, fix 12–19 as one refactor: settings module, startup `App` object, and `ChatSession`.

---

## Part 2: New features

Priorities: ★★★ start here · ★★ next · ★ later.

### Quick wins (build on existing pieces)

1. ★★★ **Read and summarize Gmail.** Add `list_unread(n)`, `search_mail(query)` and `read_thread(id)` tools. Treat email content as untrusted data, never as instructions.
2. ★★★ **Draft email instead of send.** Add a `create_draft` tool and make it the default. Sending directly requires confirmation (see fix 1).
3. ★★ **Google Calendar and Tasks.** Add scopes to the existing OAuth flow. Tools cover today's agenda, adding events and reminders.
4. ★★ **Configurable site and app aliases.** Move `web_urls` into a YAML/JSON file, and add a `web_search(query)` fallback.
5. ★★ **Better notes.** Dated Markdown notes with titles, plus `append_note`, `list_notes` and `search_notes`, in a configurable notes folder.
6. ★ **Media folder tools.** Support `S01E01` naming, parse episode numbers from existing names, add a dry-run preview, and a "next unwatched episode" tool.

### Voice experience

7. ★★★ **Streaming voice replies.** Speak each sentence as soon as it is complete, using the `AgentStream` deltas. Add `edge-tts` as an optional higher-quality voice.
8. ★★ **Barge-in and follow-up.** Let the wake word or spacebar interrupt playback, and listen briefly for a follow-up after each reply.
9. ★ **Hands-free recording.** Detect end of speech with Picovoice Cobra or `webrtcvad`, then remove the `keyboard` dependency.

### Assistant capabilities

10. ★★ **Morning briefing.** Date, weather, calendar, unread-mail summary and notes in one command, optionally scheduled with Windows Task Scheduler.
11. ★★ **Web search and page summaries.** A search API tool (Tavily, Brave or SerpAPI) plus "summarize this URL". Treat page content as untrusted.
12. ★★★ **Persistent long-term memory.** Save conversation summaries and facts to remember in SQLite or a llama-index vector store, and reload them at startup.
13. ★ **Local file Q&A.** Index a chosen folder with `VectorStoreIndex` and expose a `query_documents` tool.
14. ★ **System utilities.** System info, volume and media keys, clipboard, screenshots, and timers or reminders with Windows toast notifications.

### Platform and quality

15. ★★ **Model fallback.** Fall back from Gemini to Ollama when offline or rate-limited. Depends on the agent factory from fix 9.
16. ★ **Switchable personas.** Keep "Sanctuary" as one option alongside a neutral persona. Keep persona text separate from tool-format instructions.
17. ★★★ **Action log and undo.** Write every side-effecting tool call to a JSONL audit log, and store rename plans so they can be undone.
18. ★ **Optional UI.** A tray app or web UI (Gradio or Textual) showing the conversation, pending confirmations and the action log.

**Start with:** features 2, 1, 7, 12 and 17. Features 2 and 17 also close safety gaps from Part 1.

Each new tool or feature should ship with offline tests in `tests/` that follow the existing pattern: mock external services, and use `tmp_path` for anything that touches the filesystem.

# Phase 3: Claude Cleanup + Settings — Research

**Researched:** 2026-03-28
**Domain:** Anthropic Claude API integration, OS keychain credential storage, persistent JSON settings, live i18n reload, ttkbootstrap modal dialogs, text chunking for long transcripts
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Both paths available: "Přepsat + Upravit" runs full pipeline (transcribe then cleanup automatically), and standalone "Upravit" button in action bar allows running cleanup on any completed ("hotovo") file.
- **D-02:** Long transcripts that exceed Claude's context window are chunked with overlap, sent separately, and merged. Simple progress for single-chunk files, granular chunk progress (e.g., "Chunk 2/5") for multi-chunk files.
- **D-03:** On Claude API failure: _prepis.txt is always saved. Error logged with reason. File marked as "chyba (Claude)" — raw transcript preserved. User can retry "Upravit" later. No auto-retry.
- **D-04:** Claude cleanup processes files one at a time (sequential), not in parallel. Avoids rate limiting.
- **D-05:** Pipeline mode: cleanup starts as each file finishes transcription (file 2 transcribes while file 1 cleans up), not waiting for all transcriptions to complete.
- **D-06:** When user has no API key and clicks "Přepsat + Upravit", button is blocked — tooltip says "Set up API key first" and highlights the banner. Only "Přepsat" is available without API key.
- **D-07:** `_upraveno.txt` contains: executive summary + cleaned/structured transcript + diff comparison vs original. "Original Transcript" section is skipped to save ~50% output tokens (user has _prepis.txt already).
- **D-08:** Re-running "Upravit" on a file that already has `_upraveno.txt` creates versioned files: `_upraveno_2.txt`, `_upraveno_3.txt`, etc.
- **D-09:** File collision handling for `_prepis.txt` uses same incrementing pattern: `_prepis.txt`, `_prepis_2.txt`, `_prepis_3.txt`.
- **D-10:** Non-blocking banner at top of window: "Set up Claude API key for text cleanup". Banner disappears for the session once dismissed, reappears next launch until key is set. If API key is already stored, banner never appears. Banner reappears only if a Claude API call fails due to missing/invalid key.
- **D-11:** API key stored in Windows Credential Manager / macOS Keychain via `keyring` library. Never in plaintext.
- **D-12:** On save, key is validated with a small test API call — immediate success/fail feedback in the settings dialog.
- **D-13:** Warning shown before saving API key: tooltip/info icon with Anthropic rate limiter setup guide.
- **D-14:** Gear icon in header bar opens a modal dialog window. Closable with Escape (closes without saving). Save/Cancel buttons.
- **D-15:** Two tabs: **General** (language, output folder, parallel workers) | **Claude** (API key, model selection, rate limiter guide).
- **D-16:** Always opens on General tab (does not remember last-open tab).
- **D-17:** All settings persist between sessions: output folder, language, worker count, API key (in keyring), prompt, context profiles, model selection.
- **D-18:** Storage: JSON config file in user's app data directory. API key stored separately in keyring.
- **D-19:** "Reset to defaults" opens a modal with checkboxes — user can tick which settings to reset. Resets everything except API key by default.
- **D-20:** When GPU detected, show info text: "GPU mode: 1 worker recommended (VRAM) — GPU is ~5x faster than CPU for single files". User can still override.
- **D-21:** Settings stores the default output folder. Action bar picker overrides for current session only.
- **D-22:** "Upravit prompt" link/button near action bar expands inline editor. Editable prompt text area + "Reset to default" button.
- **D-23:** Prompt edits persist to settings (same as editing in settings dialog).
- **D-24:** Default prompt: `transcript-processor-prompt.md` ships with the app. Czech and English versions — live language reload switches the default prompt language too.
- **D-25:** Per-session context field visible in main panel near "Přepsat + Upravit" button. Always visible.
- **D-26:** Named context profiles with dropdown selector: "New...", "Rename", "Delete" options.
- **D-27:** Context profiles persist between sessions (part of settings JSON).
- **D-28:** Dropdown in Claude settings tab with two options: Haiku (fast/cheap) and Sonnet (balanced/quality). No Opus.
- **D-29:** Before sending: show estimated cost in the inline prompt area (e.g., "~$0.03 estimated").
- **D-30:** After completion: show actual usage in the log (e.g., "Claude: 1,250 tokens, ~$0.02").
- **D-31:** Phase 3 implements live language reload — switching language reloads all UI strings without restart. Default prompt also switches to match the selected language.
- **D-32:** ~300 seconds timeout per API call. User notified in log when a call is taking long (e.g., after 60s: "Claude still processing...").
- **D-33:** Animated spinner/dots in the status column during VAD preprocessing (before Whisper progress kicks in).
- **D-34:** No background API key check at startup. Key validity only checked when Claude features are triggered.

### Claude's Discretion

- Chunking strategy details (overlap size, merge algorithm for long transcripts)
- Exact JSON config file location and schema
- Log message formatting for Claude progress
- Inline prompt editor layout details
- Cost estimation calculation method
- Spinner/dots animation implementation

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CLAUDE-01 | User can trigger "Přepsat + Upravit" for transcription + Claude API text cleanup | anthropic SDK `messages.create`, background threading pattern from Phase 2, pipeline mode (D-05) |
| CLAUDE-02 | Claude cleanup produces: grammar correction, paragraph structure, executive summary, and comparison with original | `transcript-processor-prompt.md` (already written, validated); system prompt + user message structure in SDK |
| CLAUDE-03 | Output is 2 files: original transcript (_prepis.txt) + edited version with summary & diff (_upraveno.txt) | File write pattern from Phase 2; versioned collision handling (D-07, D-08) |
| CLAUDE-04 | Original transcript is always preserved and never deleted or overwritten | Save `_prepis.txt` first before any Claude call; Claude call in separate try/except (D-03) |
| CLAUDE-05 | "Přepsat" button works independently — raw transcription without Claude API | Existing transcription path unchanged; new button routes to a different code path |
| CLAUDE-06 | App works fully without Claude API key (transcription-only mode) | `keyring.get_password()` returns `None` when no key → graceful degradation; button disabled state (D-06) |
| KEY-01 | App prompts for Anthropic API key on first use of Claude features | Banner (D-10); settings modal Claude tab with key entry (D-15) |
| KEY-02 | API key stored securely via Windows Credential Manager / macOS Keychain | `keyring.set_password("whisperai", "anthropic_api_key", key)` — maps to OS native storage |
| KEY-03 | User can skip API key setup and use transcription-only mode | "Přepsat" path unblocked; "Přepsat + Upravit" disabled with tooltip (D-06) |
| KEY-04 | When app is moved to new PC/user, prompts for fresh API key (no hardcoded keys) | `keyring.get_password()` returns `None` on new machine; banner shown |
| KEY-05 | User can update or remove API key from settings | Settings Claude tab: key entry + "Odstranit API klíč" button (D-15) |
| UI-04 | Settings panel for API key, output folder, parallel workers, language, GPU preference | Two-tab settings modal (D-14, D-15); `ttk.Notebook` with General + Claude tabs |
| UI-05 | Persistent settings between sessions (output folder, language, worker count) | JSON config file via `platformdirs.user_data_dir` (D-18); load on startup, save on settings close |

</phase_requirements>

---

## Summary

Phase 3 adds Claude API cleanup, OS-native API key storage, a persistent settings system, live language reload, and several UI enhancements (banner, prompt editor, context profiles, cost estimation, VAD spinner). The phase builds directly on the Phase 2 background-threading and queue-drain patterns.

**Anthropic SDK** (0.86.0) uses a straightforward `client.messages.create(model, max_tokens, system, messages, timeout)` call. The response includes `message.usage.input_tokens` and `message.usage.output_tokens` for actual cost reporting. Token counting before the API call uses `client.messages.count_tokens(model, system, messages)`, which returns an `input_tokens` count suitable for pre-send cost estimates. Both `AuthenticationError` and `APIStatusError` are importable from `anthropic` for error classification.

**Keyring** (25.7.0) provides a three-argument API: `keyring.set_password(service, username, password)` / `keyring.get_password(service, username)` / `keyring.delete_password(service, username)`. On Windows it delegates to Windows Credential Manager; on macOS to Keychain. Returns `None` (not an exception) when no credential exists — the app must treat `None` as "no key stored."

**Config persistence** uses a JSON file placed in the OS app-data directory via `platformdirs.user_data_dir("WhisperPrepisovac", "WhisperAI")`. This resolves to `%APPDATA%\WhisperAI\WhisperPrepisovac` on Windows and `~/Library/Application Support/WhisperPrepisovac` on macOS. `platformdirs` (4.9.4) is the current successor to the deprecated `appdirs` package and is already a transitive dependency of many tools.

**Live language reload** requires extending `i18n.py` so `set_language()` re-installs `_()` into builtins, then adding a `reload_ui_strings()` method on `MainWindow` that cascades to `TranscriptionPanel.reload_strings()`. The settings modal, if open, must also be refreshed or re-created. The current `_on_language_changed` handler shows a restart notice — Phase 3 replaces that with the live-reload path.

**Primary recommendation:** Wire the Claude cleanup module as a standalone `core/claude_cleaner.py` worker that mirrors the `transcriber.py` pattern (module-level state, function-call API, progress via queue messages). Keep UI purely in `TranscriptionPanel` / settings classes. Settings and keyring access live in a new `utils/settings.py` singleton.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| `anthropic` | 0.86.0 | Claude API client — `messages.create`, token counting, error types | Project-mandated; latest stable as of 2026-03-28 |
| `keyring` | 25.7.0 | OS-native secure credential storage | Project-mandated; delegates to Windows Credential Manager / macOS Keychain without custom crypto |
| `platformdirs` | 4.9.4 | Cross-platform user app-data directory resolution | Successor to deprecated `appdirs`; `user_data_dir()` handles Windows `%APPDATA%` and macOS `~/Library/Application Support/` correctly |
| `tkinter.ttk` / `ttkbootstrap` | stdlib / 1.20.2 | Settings modal (`ttk.Toplevel`), `ttk.Notebook`, `ttk.Spinbox` | Project-mandated; already in use |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| `tkinter.simpledialog` | stdlib | `askstring()` for new context profile name | Single-input quick dialogs; already in Python |
| `tkinter.messagebox` | stdlib | Confirmation for API key removal, context profile deletion | Two-choice confirmations |
| `threading` | stdlib | Background Claude API calls (mirrors Phase 2 dispatcher thread) | Any Claude API call; never block the Tkinter event loop |
| `queue` | stdlib | Progress messages from Claude worker thread to UI drain loop | Same two-queue pattern from Phase 2 |
| `json` | stdlib | Config file serialization | Settings persistence |
| `difflib` | stdlib | Generating diff between original and cleaned transcript | Built-in; no extra dependency; `difflib.unified_diff` produces human-readable output |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `platformdirs` | Manually construct `os.environ["APPDATA"]` | `platformdirs` handles edge cases (missing env var, macOS sandboxing, Linux XDG); manual construction is fragile |
| `difflib.unified_diff` | `deepdiff`, custom line diff | `difflib` is stdlib and produces readable Markdown-compatible diffs; sufficient for transcript comparison |
| Synchronous `client.messages.create` in a thread | `AsyncAnthropic` async client | Async client requires `asyncio` loop coordination with Tkinter's event loop — complex to integrate; synchronous client in a `threading.Thread` is the established Phase 2 pattern |

**Installation (new packages only):**
```bash
pip install anthropic==0.86.0 keyring==25.7.0 platformdirs==4.9.4
```

**Add to `requirements.in`:**
```
anthropic==0.86.0
keyring==25.7.0
platformdirs==4.9.4
```

**Version verification:** Confirmed against PyPI registry on 2026-03-28.
- `anthropic`: 0.86.0 (latest, released 2026-03-18)
- `keyring`: 25.7.0 (latest, released Nov 2025)
- `platformdirs`: 4.9.4 (latest)

---

## Architecture Patterns

### Recommended Project Structure (new files only)

```
src/whisperai/
├── core/
│   ├── transcriber.py         (existing)
│   └── claude_cleaner.py      (NEW) — Claude API worker, token counting, chunking
├── gui/
│   ├── main_window.py         (extend) — gear button, banner, live reload
│   ├── transcription_panel.py (extend) — new action bar rows, prompt editor, context profiles
│   └── settings_dialog.py     (NEW) — SettingsDialog class, two-tab modal
└── utils/
    ├── i18n.py                (extend) — set_language() re-installs _(), live reload support
    ├── resource_path.py       (existing)
    └── settings.py            (NEW) — SettingsStore singleton: load/save JSON + keyring bridge
```

### Pattern 1: SettingsStore Singleton

**What:** A single `SettingsStore` object loaded at app startup, providing typed getters/setters. Saves to JSON on explicit `save()` call only (not on every mutation — callers control flush timing).

**When to use:** Any code that reads or writes persistent settings. Pass the store instance into `MainWindow`, `TranscriptionPanel`, and `SettingsDialog` — do not create multiple instances.

```python
# src/whisperai/utils/settings.py
import json
from pathlib import Path
from typing import Any
import platformdirs

DEFAULTS = {
    "language": "cs",
    "output_folder": "",
    "worker_count": 1,
    "claude_model": "claude-haiku-4-5",
    "claude_prompt": "",          # empty = use bundled default file
    "context_profiles": {},       # name -> text
    "active_profile": "",
}

class SettingsStore:
    def __init__(self, app_name: str = "WhisperPrepisovac", app_author: str = "WhisperAI") -> None:
        data_dir = Path(platformdirs.user_data_dir(app_name, app_author))
        data_dir.mkdir(parents=True, exist_ok=True)
        self._path = data_dir / "settings.json"
        self._data: dict[str, Any] = dict(DEFAULTS)
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                loaded = json.loads(self._path.read_text(encoding="utf-8"))
                self._data.update({k: v for k, v in loaded.items() if k in DEFAULTS})
            except Exception:
                pass  # Corrupt file — use defaults silently

    def save(self) -> None:
        self._path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get(self, key: str) -> Any:
        return self._data.get(key, DEFAULTS.get(key))

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
```

### Pattern 2: Claude Cleaner Worker

**What:** A standalone `clean_transcript()` function in `core/claude_cleaner.py` that runs in a background `threading.Thread`. Reports progress via `queue.Queue` messages (same drain pattern as `transcriber.py`). Called by the dispatcher in `TranscriptionPanel`.

**When to use:** Every time "Přepsat + Upravit" or standalone "Upravit" triggers Claude processing.

```python
# src/whisperai/core/claude_cleaner.py
# Source: anthropic SDK README + platform.claude.com/docs/en/about-claude/models/overview
import anthropic
import time

CHUNK_CHARS = 80_000      # ~20k tokens — safely within 200k context window
OVERLAP_CHARS = 2_000     # overlap between chunks to preserve context continuity

def clean_transcript(
    text: str,
    system_prompt: str,
    context_text: str,
    model: str,
    api_key: str,
    progress_queue,          # queue.Queue
    task_id: str,
    timeout: float = 300.0,
) -> dict:
    """Run Claude cleanup on a transcript. Returns dict with 'result' or raises on failure."""
    client = anthropic.Anthropic(api_key=api_key)

    # Build user message: inject optional context
    user_content = text
    if context_text.strip():
        user_content = f"Context: {context_text.strip()}\n\n---\n\n{text}"

    chunks = _split_into_chunks(text)
    total_chunks = len(chunks)
    results = []
    total_input_tokens = 0
    total_output_tokens = 0

    for i, chunk in enumerate(chunks):
        chunk_msg = chunk
        if context_text.strip():
            chunk_msg = f"Context: {context_text.strip()}\n\n---\n\n{chunk}"

        if total_chunks > 1:
            progress_queue.put({"type": "claude_chunk", "task_id": task_id, "n": i + 1, "total": total_chunks})
        else:
            progress_queue.put({"type": "claude_processing", "task_id": task_id})

        # Long-call notification after 60s
        call_start = time.monotonic()

        def _long_call_warning():
            import threading
            def _warn():
                time.sleep(60)
                elapsed = int(time.monotonic() - call_start)
                progress_queue.put({"type": "claude_slow", "task_id": task_id, "elapsed": elapsed})
            t = threading.Thread(target=_warn, daemon=True)
            t.start()

        _long_call_warning()

        response = client.messages.create(
            model=model,
            max_tokens=64_000,
            system=system_prompt,
            messages=[{"role": "user", "content": chunk_msg}],
            timeout=timeout,
        )
        results.append(response.content[0].text)
        total_input_tokens += response.usage.input_tokens
        total_output_tokens += response.usage.output_tokens

    merged = _merge_chunks(results) if total_chunks > 1 else results[0]
    return {
        "result": merged,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
    }


def _split_into_chunks(text: str) -> list[str]:
    if len(text) <= CHUNK_CHARS:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + CHUNK_CHARS
        if end < len(text):
            # Find last paragraph break before end to avoid mid-sentence splits
            break_pos = text.rfind("\n\n", start, end)
            if break_pos > start:
                end = break_pos
        chunks.append(text[start:end])
        start = end - OVERLAP_CHARS  # Overlap for context continuity
    return chunks


def _merge_chunks(parts: list[str]) -> str:
    # Simple join with section marker — overlap means content may repeat slightly
    return "\n\n---\n\n".join(parts)


def count_tokens_estimate(text: str, system_prompt: str, model: str, api_key: str) -> int:
    """Return estimated input token count for cost preview. Returns 0 on any error."""
    try:
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.count_tokens(
            model=model,
            system=system_prompt,
            messages=[{"role": "user", "content": text}],
        )
        return response.input_tokens
    except Exception:
        return 0
```

### Pattern 3: API Key Validation Call

**What:** A minimal test call (`max_tokens=1`) to validate an API key before saving it. Runs in a background thread to avoid blocking the settings dialog UI.

```python
# Source: anthropic SDK error types
from anthropic import Anthropic, AuthenticationError, APIStatusError

def validate_api_key(api_key: str) -> tuple[bool, str]:
    """Returns (is_valid, error_message). is_valid=True means key accepted."""
    try:
        client = Anthropic(api_key=api_key)
        client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1,
            messages=[{"role": "user", "content": "ping"}],
        )
        return True, ""
    except AuthenticationError:
        return False, "Invalid API key — check the value"
    except APIStatusError as e:
        # Rate limit or quota errors still mean the key is structurally valid
        if e.status_code in (429, 529):
            return True, ""
        return False, f"API error {e.status_code}: {e.message}"
    except Exception as e:
        return False, str(e)
```

### Pattern 4: Keyring API Key Storage

**What:** Wrapping `keyring` in a thin helper in `utils/settings.py` to centralize the service/username constants.

```python
# Source: keyring 25.7.0 docs — keyring.readthedocs.io
import keyring

KEYRING_SERVICE = "WhisperPrepisovac"
KEYRING_USERNAME = "anthropic_api_key"

def get_api_key() -> str | None:
    """Returns stored API key or None if not set."""
    return keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)

def set_api_key(key: str) -> None:
    keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, key)

def delete_api_key() -> None:
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except keyring.errors.PasswordDeleteError:
        pass  # Already absent — not an error
```

### Pattern 5: Live Language Reload

**What:** `set_language()` already re-installs `_()` into builtins. Add a `reload_ui_strings()` method to `MainWindow` that replaces all widget text in-place. Delegate to `TranscriptionPanel.reload_strings()` and `SettingsDialog.reload_strings()` if open.

**When to use:** Called from `_on_language_changed` in `MainWindow` footer Combobox — replaces the current "show restart notice" implementation.

```python
# Extend MainWindow._on_language_changed:
def _on_language_changed(self, event):
    selected_index = self._lang_combo.current()
    codes = ["cs", "en"]
    new_lang = codes[selected_index]
    if new_lang != self.current_lang:
        from src.whisperai.utils.i18n import set_language
        set_language(new_lang)
        self.current_lang = new_lang
        self._settings.set("language", new_lang)
        self._settings.save()
        self.reload_ui_strings()

def reload_ui_strings(self) -> None:
    self.app_title_label.configure(text=_("app.title"))
    self._lang_label.configure(text=_("ui.language_label"))
    self.transcription_panel.reload_strings()
    if hasattr(self, "_settings_dialog") and self._settings_dialog:
        self._settings_dialog.reload_strings()
```

### Pattern 6: Settings Modal (ttk.Toplevel + grab_set)

**What:** A `SettingsDialog` class wrapping `ttk.Toplevel`. Called from gear button. `grab_set()` blocks main window interaction.

```python
# Source: tkinter documentation + ttkbootstrap built-ins
class SettingsDialog:
    def __init__(self, parent_root: ttk.Window, settings: SettingsStore) -> None:
        self.dialog = ttk.Toplevel(parent_root)
        self.dialog.title(_("settings.title"))
        self.dialog.grab_set()
        self.dialog.minsize(480, 360)
        self.dialog.bind("<Escape>", lambda e: self.dialog.destroy())
        self._settings = settings
        self._build()

    def _build(self) -> None:
        frame = ttk.Frame(self.dialog, padding=16)
        frame.pack(fill="both", expand=True)
        notebook = ttk.Notebook(frame)
        notebook.pack(fill="both", expand=True, pady=(0, 16))
        # Always open on General tab (D-16)
        self._build_general_tab(notebook)
        self._build_claude_tab(notebook)
        notebook.select(0)
        # Button row
        btn_row = ttk.Frame(frame)
        btn_row.pack(fill="x")
        ttk.Button(btn_row, text=_("settings.reset_defaults"), bootstyle="secondary",
                   command=self._on_reset).pack(side="left")
        ttk.Button(btn_row, text=_("settings.cancel"), bootstyle="secondary",
                   command=self.dialog.destroy).pack(side="right")
        ttk.Button(btn_row, text=_("settings.save"), bootstyle="success",
                   command=self._on_save).pack(side="right", padx=(0, 8))
```

### Pattern 7: Cost Estimation Formula

**What:** Pre-send estimate uses character-count approximation (no API call). Post-send shows actual token count from `response.usage`.

**Cost calculation (based on verified Anthropic pricing 2026-03-28):**
- Haiku 4.5: $1.00 / MTok input + $5.00 / MTok output
- Sonnet 4.6: $3.00 / MTok input + $15.00 / MTok output

```python
PRICING = {
    "claude-haiku-4-5": {"input": 1.0 / 1_000_000, "output": 5.0 / 1_000_000},
    "claude-sonnet-4-6": {"input": 3.0 / 1_000_000, "output": 15.0 / 1_000_000},
}

def estimate_cost_pre_send(char_count: int, model: str) -> float:
    """Rough pre-send estimate. ~4 chars per token as English approximation.
    Czech may be slightly more tokens per word — treat as upper-bound estimate."""
    estimated_input_tokens = char_count / 4
    estimated_output_tokens = estimated_input_tokens * 0.8  # cleaned output ~80% of input
    p = PRICING.get(model, PRICING["claude-haiku-4-5"])
    return estimated_input_tokens * p["input"] + estimated_output_tokens * p["output"]

def calculate_actual_cost(input_tokens: int, output_tokens: int, model: str) -> float:
    p = PRICING.get(model, PRICING["claude-haiku-4-5"])
    return input_tokens * p["input"] + output_tokens * p["output"]
```

### Pattern 8: VAD Spinner (animated dots)

**What:** During VAD preprocessing, cycle status cell text through `·`, `··`, `···` using `root.after(400, tick)`. Stop when `vad_done` message arrives.

```python
def _start_vad_spinner(self, iid: str) -> None:
    dots = ["·", "··", "···"]
    state = {"index": 0, "running": True}

    def tick():
        if not state["running"]:
            return
        d = dots[state["index"] % 3]
        state["index"] += 1
        current_values = list(self.tree.item(iid, "values"))
        current_values[3] = f"VAD {d}"
        self.tree.item(iid, values=current_values, tags=("processing",))
        self.root.after(400, tick)

    state["_stop"] = lambda: state.update({"running": False})
    self.root.after(400, tick)
    return state  # caller stores state and calls state["_stop"]() on vad_done
```

### Pattern 9: Diff Generation for _upraveno.txt

**What:** Use `difflib.unified_diff` to produce a text-based diff appended to the `_upraveno.txt` output. Kept short (≤100 lines) by limiting context lines.

```python
import difflib

def build_upraveno_content(original: str, cleaned_result: str) -> str:
    """Assemble the _upraveno.txt content per D-07: summary + cleaned + diff vs original."""
    diff_lines = list(difflib.unified_diff(
        original.splitlines(keepends=True),
        # Extract just the cleaned transcript section from cleaned_result
        cleaned_result.splitlines(keepends=True),
        fromfile="_prepis.txt (original)",
        tofile="_upraveno.txt (cleaned)",
        n=3,
    ))
    diff_text = "".join(diff_lines[:200])  # Cap at 200 lines to avoid huge diffs
    return f"{cleaned_result}\n\n---\n\n## Diff vs. originál\n\n```diff\n{diff_text}\n```"
```

### Anti-Patterns to Avoid

- **Calling `keyring` in `ProcessPoolExecutor` subprocess:** Keyring requires the main process (Windows Credential Manager COM calls are not subprocess-safe). Always access keyring in the main thread or a `threading.Thread`.
- **Blocking the Tkinter event loop with `client.messages.create`:** Claude calls can take 30-300s. Must run in a `threading.Thread`.
- **Creating `anthropic.Anthropic(api_key=...)` at module import time:** If no key is set, the client raises on construction in some versions. Construct `Anthropic(api_key=key)` lazily inside the worker function.
- **Using `grab_set()` without also binding Escape:** The dialog will be unclosable if the save operation has a bug. Always bind `<Escape>` to `destroy()`.
- **Updating Treeview cells from a non-main thread:** All Treeview mutations must go through the `_ui_queue` → `root.after` drain loop, same as Phase 2.
- **Over-chunking short transcripts:** Chunking adds overhead (multiple API calls, merge seams). Only chunk when `len(text) > CHUNK_CHARS`. The default 200k context window of both Haiku 4.5 and Sonnet 4.6 fits ~150,000 English words — chunking is only needed for very long recordings.
- **Storing the API key in `settings.json`:** All key storage must go through `keyring`. The JSON config must never contain the key field.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OS-native credential storage | Custom AES file encryption | `keyring` | Windows Credential Manager and macOS Keychain handle encryption, ACLs, and migration natively |
| Platform-specific app data dir | Manual `os.environ["APPDATA"]` | `platformdirs.user_data_dir()` | Edge cases: missing env vars, macOS sandboxing, roaming vs local, UWP paths |
| Transcript diff generation | Custom line-diff algorithm | `difflib.unified_diff` | Already handles edge cases (empty files, Unicode, line endings); stdlib = zero extra dep |
| API key validation | Heuristic regex check on key format | Small live `messages.create` call | Only the API can confirm a key is live and has quota |
| Cost estimation | Tokenizer library (`tiktoken`) | Character-count approximation | `tiktoken` adds 20 MB and a binary dependency; ~4 chars/token is accurate enough for a pre-send estimate display |

**Key insight:** The heavy lifting in this phase (API calls, OS credential storage, diff generation) is already solved by SDK/stdlib. All custom code should be thin orchestration glue.

---

## Common Pitfalls

### Pitfall 1: `keyring` Returns `None`, Not an Exception, for Missing Key

**What goes wrong:** Code calls `keyring.get_password(...)` and fails to handle `None`. Later code attempts to use `None` as an API key, causing a confusing `AuthenticationError` instead of the expected "no key set" path.
**Why it happens:** `keyring.get_password` returns `None` when the credential does not exist — it does not raise `PasswordNotFound`.
**How to avoid:** `api_key = get_api_key(); if api_key is None: <show banner/disable button>`
**Warning signs:** `AuthenticationError` appearing when the user has never entered a key.

### Pitfall 2: `keyring.delete_password` Raises `PasswordDeleteError` When Key Does Not Exist

**What goes wrong:** Calling `delete_api_key()` when no key is stored raises `keyring.errors.PasswordDeleteError`.
**Why it happens:** Unlike `get_password`, the delete function is not idempotent.
**How to avoid:** Wrap `keyring.delete_password` in a `try/except PasswordDeleteError: pass` block (see Pattern 4 above).

### Pitfall 3: Tkinter `ttk.Toplevel` Without `wait_window` Blocks Parent Incorrectly

**What goes wrong:** Settings dialog is created with `grab_set()` but the calling code continues executing synchronously. If the caller tries to read settings values before the dialog closes, it reads stale values.
**Why it happens:** `ttk.Toplevel` is non-blocking by default. `grab_set()` only blocks mouse/keyboard events, not Python execution.
**How to avoid:** The settings dialog is fire-and-forget — the gear button handler creates it and returns. Settings changes are written to `SettingsStore` when the user clicks Save. The main window reads from `SettingsStore` at action time, not at dialog-creation time.

### Pitfall 4: `anthropic.Anthropic` Client Not Thread-Safe for Concurrent Calls

**What goes wrong:** A shared `Anthropic` client instance is used from multiple threads simultaneously, producing unpredictable errors.
**Why it happens:** The httpx client underlying the SDK maintains connection state.
**How to avoid:** Claude cleanup is sequential (D-04). Each cleanup worker call creates its own `Anthropic(api_key=key)` instance. Do not create a single global `Anthropic` client.

### Pitfall 5: Live Language Reload Misses Dynamically Generated Strings

**What goes wrong:** After language switch, most UI labels update but some strings (e.g., status tags in the Treeview, tooltip text on buttons) remain in the old language.
**Why it happens:** Treeview cell values are stored as plain strings written once at insertion/update time. Tooltip text is set via `ToolTip(widget, text=_(...))` at construction time and not reactively bound.
**How to avoid:** `reload_strings()` must explicitly update: (a) all live Treeview row status cells that still show translatable status text (e.g., rows with "čeká" / "waiting" status), (b) `ToolTip` instances must be recreated or updated via `tooltip.text = _(...)`.

### Pitfall 6: `processs.Queue` Cannot Be Used From Tkinter's `root.after` Poll Loop

**What goes wrong:** Passing a `multiprocessing.Queue` directly to the Tkinter drain loop (`_drain_ui_queue`) causes pickling errors or deadlocks.
**Why it happens:** `multiprocessing.Queue` requires a separate drain thread (established in Phase 2). Claude cleanup runs in a `threading.Thread` (not a subprocess), so it uses a plain `queue.Queue` — no drain thread needed.
**How to avoid:** Claude worker uses `queue.Queue` directly. The existing `root.after(100, _drain_ui_queue)` loop already drains `_ui_queue: queue.Queue`. Route Claude progress messages through the same `_ui_queue`.

### Pitfall 7: `ttk.Notebook` Tab Index Is Not Stable After `reload_strings`

**What goes wrong:** After calling `reload_strings()` on the settings dialog, if tabs are destroyed and recreated, the active tab resets to 0 (General). This is actually correct per D-16 — the dialog always opens on General.
**Why it happens:** Notebook tabs are widgets; re-creating them resets the selection.
**How to avoid:** Do not destroy/recreate the Notebook on language reload if the dialog is open. Instead, update widget text in place (`widget.configure(text=_(...))`). For the tab header text, use `notebook.tab(index, text=_(...))`.

### Pitfall 8: Czech Characters in File Paths on Windows

**What goes wrong:** `platformdirs.user_data_dir` returns a path that may contain Czech characters (e.g., user name "Ján Novák"). Writing the JSON config file using default encoding fails on Windows.
**Why it happens:** Python's `open()` uses system locale encoding by default on Windows, which may not be UTF-8 in all configurations.
**How to avoid:** Always pass `encoding="utf-8"` when reading/writing config files (consistent with Phase 2 output files).

---

## Code Examples

Verified patterns from official/confirmed sources:

### Anthropic SDK — Basic Message Call with Usage

```python
# Source: github.com/anthropics/anthropic-sdk-python README
import anthropic

client = anthropic.Anthropic(api_key="sk-ant-...")
message = client.messages.create(
    model="claude-haiku-4-5",
    max_tokens=64_000,
    system="You are a helpful assistant.",
    messages=[{"role": "user", "content": "Hello"}],
    timeout=300.0,
)
text = message.content[0].text
input_tokens = message.usage.input_tokens
output_tokens = message.usage.output_tokens
```

### Anthropic SDK — Token Count Before Send

```python
# Source: platform.claude.com/docs/en/api/messages-count-tokens
response = client.messages.count_tokens(
    model="claude-haiku-4-5",
    system="You are a helpful assistant.",
    messages=[{"role": "user", "content": "Hello"}],
)
token_count = response.input_tokens
```

### Anthropic SDK — Error Handling

```python
# Source: anthropic SDK README error types
from anthropic import AuthenticationError, APIStatusError, APITimeoutError

try:
    response = client.messages.create(...)
except AuthenticationError:
    # Key invalid or expired
    ...
except APIStatusError as e:
    if e.status_code == 429:
        # Rate limited — key is valid, quota exceeded
        ...
    else:
        # Other API error
        ...
except APITimeoutError:
    # Exceeded timeout= parameter
    ...
```

### Keyring — Store and Retrieve API Key

```python
# Source: keyring 25.7.0 docs — keyring.readthedocs.io
import keyring
import keyring.errors

SERVICE = "WhisperPrepisovac"
USERNAME = "anthropic_api_key"

# Store
keyring.set_password(SERVICE, USERNAME, "sk-ant-...")

# Retrieve — returns None if not found (does not raise)
api_key = keyring.get_password(SERVICE, USERNAME)

# Delete — raises PasswordDeleteError if not found
try:
    keyring.delete_password(SERVICE, USERNAME)
except keyring.errors.PasswordDeleteError:
    pass
```

### platformdirs — Resolve Config Directory

```python
# Source: platformdirs.readthedocs.io
import platformdirs
from pathlib import Path

data_dir = Path(platformdirs.user_data_dir("WhisperPrepisovac", "WhisperAI"))
data_dir.mkdir(parents=True, exist_ok=True)
config_path = data_dir / "settings.json"
# Windows: C:\Users\<user>\AppData\Local\WhisperAI\WhisperPrepisovac\settings.json
# macOS:   ~/Library/Application Support/WhisperPrepisovac/settings.json
```

### Settings JSON — Recommended Schema

```json
{
  "language": "cs",
  "output_folder": "C:\\Users\\sosno\\Documents\\prepisy",
  "worker_count": 1,
  "claude_model": "claude-haiku-4-5",
  "claude_prompt": "",
  "context_profiles": {
    "Týmová porada": "Pravidelná týmová schůzka. Účastníci: Jan, Eva, Tomáš.",
    "Rozhovor - Novák": "Rozhovor pro projekt XY. Dotazovaný: Ing. Novák."
  },
  "active_profile": "Týmová porada"
}
```

Note: `api_key` is NEVER in this file — stored in OS keychain only.

### ttkbootstrap Notebook (Settings Modal)

```python
# Source: ttkbootstrap 1.20.2 docs — ttkbootstrap built-ins
import ttkbootstrap as ttk

dialog = ttk.Toplevel(parent)
dialog.grab_set()
dialog.minsize(480, 360)
dialog.bind("<Escape>", lambda e: dialog.destroy())

notebook = ttk.Notebook(dialog)
notebook.pack(fill="both", expand=True)

tab_general = ttk.Frame(notebook, padding=16)
tab_claude = ttk.Frame(notebook, padding=16)
notebook.add(tab_general, text=_("settings.tab_general"))
notebook.add(tab_claude, text=_("settings.tab_claude"))
notebook.select(0)  # Always open on General (D-16)
```

### Live Language Reload — In-Place Widget Text Update

```python
# Pattern: update widget text in-place without recreating widgets
def reload_strings(self) -> None:
    # Labels
    self.lbl_output.configure(text=_("ui.action.output_label"))
    self.btn_transcribe.configure(text=_("ui.action.transcribe"))
    # Treeview column headings
    self.tree.heading("filename", text=_("ui.queue.col_file"))
    self.tree.heading("status",   text=_("ui.queue.col_status"))
    # Update Treeview rows that still show translated status strings
    for iid in self.tree.get_children():
        tags = self.tree.item(iid, "tags")
        if "waiting" in tags:
            self.update_row_status(iid, _("ui.status.waiting"), "waiting")
    # Tooltips
    self._btn_upravit_tooltip.text = _("ui.tooltip.upravit_disabled")
```

---

## Model Selection — Verified Model IDs

**CRITICAL:** The CONTEXT.md specifies "Haiku (fast/cheap) and Sonnet (balanced/quality)" as dropdown options (D-28). Current verified model IDs as of 2026-03-28:

| Display Name in UI | API Model ID | Context | Pricing (input/output per MTok) |
|-------------------|--------------|---------|--------------------------------|
| Haiku (rychlý/levný) | `claude-haiku-4-5` | 200k | $1.00 / $5.00 |
| Sonnet (vyvážený) | `claude-sonnet-4-6` | 1M | $3.00 / $15.00 |

**Note:** The UI-SPEC shows "claude-haiku-4-5" and "claude-sonnet-4-5" in the dropdown. However, `claude-sonnet-4-5` is now a legacy model. The current Sonnet is `claude-sonnet-4-6`. The planner should use `claude-sonnet-4-6` as the Sonnet option. Both model IDs are stable aliases (no snapshot date required in the alias).

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `appdirs` library for app data dirs | `platformdirs` (successor) | ~2022 | `appdirs` is unmaintained; `platformdirs` is the replacement |
| Claude Haiku 3 for cheap tasks | Claude Haiku 4.5 | Oct 2025 | Haiku 3 deprecated, retiring April 19 2026 |
| Restart on language change (Phase 1 pattern) | Live reload via `reload_ui_strings()` | Phase 3 | Deferred from Phase 1, now implemented |
| `gettext.install()` once at startup | `gettext.install()` called again in `set_language()` on each language switch | Phase 3 | Re-calling `install()` replaces the builtins `_()` function — no gettext extension needed |

**Deprecated/outdated:**
- `claude-haiku-3-20240307` (and alias): Retiring April 19 2026 — do not use.
- `appdirs` package: Unmaintained, superseded by `platformdirs`.
- `claude-sonnet-4-5` as the primary Sonnet alias: Still functional but `claude-sonnet-4-6` is the current generation.

---

## Runtime State Inventory

Step 2.5: SKIPPED — This is a new feature addition phase, not a rename/refactor/migration phase. No existing runtime state needs to be migrated.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `anthropic` Python package | Claude API calls | Not installed | 0.86.0 on PyPI | None — must be installed before Phase 3 runs |
| `keyring` Python package | API key storage | Not installed | 25.7.0 on PyPI | None — required for KEY-02 |
| `platformdirs` Python package | Config file location | Not installed | 4.9.4 on PyPI | Could hardcode `%APPDATA%` but fragile — install instead |
| `tkinter` | All GUI | Installed | stdlib | N/A — stdlib |
| `ttkbootstrap` | All GUI | Installed (env) | 1.20.2 | N/A |
| Windows Credential Manager | KEY-02 on Windows | Available (OS) | Windows 11 confirmed | — |

**Missing dependencies with no fallback:**
- `anthropic 0.86.0` — must be added to `requirements.in` and installed before any Wave that touches Claude integration
- `keyring 25.7.0` — must be added to `requirements.in`
- `platformdirs 4.9.4` — must be added to `requirements.in`

**Wave 0 action:** `pip install anthropic==0.86.0 keyring==25.7.0 platformdirs==4.9.4` and update `requirements.in`.

---

## Open Questions

1. **Czech vs English prompt files**
   - What we know: CONTEXT.md D-24 says "Czech and English versions — live language reload switches the default prompt language too." The existing `transcript-processor-prompt.md` is in English.
   - What's unclear: Should the Czech version be a translation of the English prompt, or a separate prompt tailored to Czech? The file is already designed to auto-detect language and respond in the transcript's language.
   - Recommendation: Create `transcript-processor-prompt-cs.md` (Czech UI copy, identical instructions) and `transcript-processor-prompt-en.md` (current content renamed). The instruction "Respond in the same language as the transcript" remains in both — the language switch only changes the UI text of the prompt, not its behavior.

2. **`pywin32` requirement for `keyring` on Windows PyInstaller**
   - What we know: CLAUDE.md notes "On Windows, uses `pywin32` for Credential Manager access — ensure `pywin32` is installed or bundled." Phase 4 handles PyInstaller packaging, but `pywin32` must be present in the dev environment for Phase 3 testing.
   - What's unclear: Whether `pip install keyring` automatically pulls `pywin32` on Windows.
   - Recommendation: Explicitly add `pywin32` to `requirements.in` (Windows-only). Verify by running `keyring.get_password("test", "test")` during Wave 0 smoke test.

3. **Chunk merge quality for long transcripts**
   - What we know: D-02 says "chunked with overlap, sent separately, and merged." Overlap prevents mid-sentence cuts.
   - What's unclear: The prompt asks Claude to produce a structured summary+transcript. For chunked inputs, the summary in chunk N may not reflect chunk N+1. The merge will produce multiple summaries.
   - Recommendation: For multi-chunk files, send each chunk with the instruction "This is chunk N of M. Process only this chunk." Then produce a final synthesis pass from all chunk outputs. This requires one additional API call per multi-chunk file. Alternatively: only chunk the cleaned transcript section and keep a single summary pass over the full text (requires two API calls regardless of chunking). Decision is discretionary per CONTEXT.md — recommend the latter (two-pass approach) as it produces better summaries.

---

## Project Constraints (from CLAUDE.md)

All Phase 3 code must comply with these directives, identical to prior phases:

| Constraint | Applies To |
|------------|-----------|
| Python 3.12.x required (not 3.13, not 3.10.0) | All new modules |
| `anthropic==0.86.0` — official Anthropic Python SDK | Claude API calls |
| `keyring==25.7.0` — OS-native secure storage; never plaintext API keys | KEY-01 through KEY-05 |
| `ttkbootstrap 1.20.2` — use `ttk.` widgets with `bootstyle=` parameter | All new UI widgets |
| `pathlib.Path` throughout — no `os.path` | File path handling |
| All user-visible strings through `_()` — no hardcoded text | All new labels, messages, tooltips |
| `ProcessPoolExecutor` for CPU-bound parallelism; `threading.Thread` for I/O-bound or API calls | Claude worker is threading.Thread |
| `queue.Queue` + `root.after(100, drain)` pattern for thread→UI communication | Claude progress messages |
| API key never in plaintext files or config JSON | KEY-02 |
| PyInstaller `--onedir` packaging target — code must be frozen-context aware (`get_resource_path`) | Prompt template file access |
| No `wx`, `PyQt`, `PySide6` | — |
| GSD workflow entry points required before editing files | Development workflow |

---

## Sources

### Primary (HIGH confidence)
- [platform.claude.com/docs/en/about-claude/models/overview](https://platform.claude.com/docs/en/about-claude/models/overview) — verified model IDs, context windows, pricing 2026-03-28
- [platform.claude.com/docs/en/about-claude/pricing](https://platform.claude.com/docs/en/about-claude/pricing) — per-token pricing table verified 2026-03-28
- [github.com/anthropics/anthropic-sdk-python](https://github.com/anthropics/anthropic-sdk-python) — SDK usage patterns, error types, timeout parameter
- [keyring.readthedocs.io](https://keyring.readthedocs.io/) — keyring 25.7.0 API (set/get/delete_password, PasswordDeleteError)
- [platformdirs.readthedocs.io](https://platformdirs.readthedocs.io/) — user_data_dir() platform paths
- PyPI registry — `anthropic 0.86.0`, `keyring 25.7.0`, `platformdirs 4.9.4` version confirmation (verified via `pip index versions`)
- `locale/cs_CZ/LC_MESSAGES/messages.po` — existing i18n key inventory (direct file read)
- `src/whisperai/gui/transcription_panel.py` — Phase 2 two-queue pattern, action bar layout, Treeview tag system (direct file read)
- `transcript-processor-prompt.md` — validated default Claude prompt (direct file read)

### Secondary (MEDIUM confidence)
- [platform.claude.com/docs/en/api/messages-count-tokens](https://platform.claude.com/docs/en/api/messages-count-tokens) — token counting endpoint (redirect followed; content verified against SDK README)
- CONTEXT.md D-01 through D-34 — locked implementation decisions
- UI-SPEC.md — verified component inventory and copywriting contract

### Tertiary (LOW confidence)
- `pywin32` requirement for `keyring` on Windows — stated in CLAUDE.md; not independently verified via a live install test

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all library versions confirmed via PyPI registry on 2026-03-28
- Architecture patterns: HIGH — mirrors established Phase 2 patterns; SDK usage confirmed via official docs
- Model IDs and pricing: HIGH — fetched directly from platform.claude.com/docs 2026-03-28
- Pitfalls: HIGH — sourced from official API behavior docs and verified code patterns
- Chunking/merge strategy: MEDIUM — discretionary design choice; recommended approach is logical but not empirically tested

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (30 days; pricing and model IDs are stable; verify model aliases if planning beyond this date)

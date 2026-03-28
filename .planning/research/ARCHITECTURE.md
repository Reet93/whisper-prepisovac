# Architecture Research

**Domain:** Desktop audio transcription app (Python + Tkinter + Whisper + Claude API)
**Researched:** 2026-03-28
**Confidence:** HIGH

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        GUI Layer (Main Thread)                   │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────────────┐ │
│  │  File Panel  │  │  Log Panel   │  │  Settings / API Panel  │ │
│  │ (file list,  │  │ (live scroll │  │  (key prompt, output   │ │
│  │  status)     │  │  output)     │  │   folder, lang toggle) │ │
│  └──────┬───────┘  └──────┬───────┘  └────────────┬───────────┘ │
│         │                 │                        │             │
│  ┌──────▼─────────────────▼────────────────────────▼───────────┐ │
│  │             App Controller / Event Bus                       │ │
│  │  (button handlers, queue.Queue poll via root.after(100ms))   │ │
│  └──────────────────────────┬────────────────────────────────── ┘ │
└─────────────────────────────┼───────────────────────────────────┘
                              │ spawns / communicates via queue
┌─────────────────────────────▼───────────────────────────────────┐
│                     Worker Layer (Background Threads)            │
│  ┌──────────────────┐     ┌──────────────────────────────────┐  │
│  │  Transcription   │     │       Claude Cleanup Worker      │  │
│  │  Worker Pool     │     │  (one thread, sequential, async  │  │
│  │  (1-N threads,   │     │   HTTP via anthropic SDK)        │  │
│  │  one model each) │     └──────────────────────────────────┘  │
│  └──────────────────┘                                            │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                     Service / Utility Layer                      │
│  ┌─────────────┐  ┌────────────┐  ┌──────────┐  ┌───────────┐  │
│  │  Whisper    │  │  Claude    │  │  Config  │  │  Keyring  │  │
│  │  Service    │  │  Service   │  │  Service │  │  Service  │  │
│  │ (model load │  │ (API call, │  │ (settings│  │ (Win Cred │  │
│  │  + transcr.)│  │  prompt    │  │  persist)│  │  / Keychain│  │
│  │             │  │  building) │  │          │  │  wrapper) │  │
│  └─────────────┘  └────────────┘  └──────────┘  └───────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────▼───────────────────────────────────┐
│                        Storage Layer                             │
│  ┌──────────────────┐  ┌──────────────┐  ┌────────────────────┐ │
│  │  Input Audio     │  │  Output Text │  │  App Config        │ │
│  │  Files (user FS) │  │  Files       │  │  (platformdirs     │ │
│  │                  │  │  _prepis.txt │  │   user_config_dir) │ │
│  │                  │  │  _upraveno   │  │                    │ │
│  │                  │  │  .txt)       │  │                    │ │
│  └──────────────────┘  └──────────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| GUI Layer | Render widgets, capture user input, display status | Tkinter widgets, StringVar/BooleanVar for reactive state |
| App Controller | Wire GUI events to workers, poll result queue, dispatch UI updates | `root.after(100, poll_queue)` loop; central `queue.Queue` |
| Transcription Worker Pool | Run Whisper inference off the main thread; one worker per parallel slot | `threading.Thread` per job; each loads its own model instance |
| Claude Cleanup Worker | Call Anthropic API, build prompt, parse structured response | Single thread; `anthropic.Anthropic` client; sequential queue |
| Whisper Service | Load model from bundled path, call `model.transcribe()`, return segments | Pure function wrapper; detects GPU via `torch.cuda`/`torch.backends.mps` |
| Claude Service | Build cleanup prompt, send API call, parse response into (edited, summary, diff) | Stateless functions; API key from Keyring Service |
| Config Service | Read/write user preferences (language, output folder, parallelism) | `configparser` or `json`; path from `platformdirs.user_config_dir` |
| Keyring Service | Store and retrieve Claude API key in OS-native secure storage | `keyring` library; abstracts Win Credential Manager + macOS Keychain |
| File Manager | Validate input paths, build output filenames, write text files | Path utilities; never overwrites `_prepis.txt` |
| i18n Module | Translate all UI strings at runtime; switch language without restart | `gettext`; `.mo` files bundled; module-level `_()` alias |
| PyInstaller Bootstrap | Resolve bundled resource paths (`ffmpeg`, model, locale files) at runtime | `sys._MEIPASS` helper function; called at app startup |

## Recommended Project Structure

```
whisperai/
├── main.py                 # Entry point; creates Tk root, starts App
├── app.py                  # App Controller: wires GUI + workers + queue
├── gui/
│   ├── __init__.py
│   ├── main_window.py      # Top-level window layout
│   ├── file_panel.py       # File list, add/folder buttons, status column
│   ├── log_panel.py        # Scrollable live log output
│   └── settings_panel.py   # API key prompt, output folder, language toggle
├── workers/
│   ├── __init__.py
│   ├── transcription.py    # Worker thread: calls WhisperService, posts results
│   └── cleanup.py          # Worker thread: calls ClaudeService, posts results
├── services/
│   ├── __init__.py
│   ├── whisper_service.py  # Model load, GPU detection, transcribe()
│   ├── claude_service.py   # Prompt build, API call, response parse
│   ├── keyring_service.py  # get/set/delete API key via keyring
│   ├── config_service.py   # Read/write app settings via platformdirs
│   └── file_service.py     # Input validation, output path generation, write
├── i18n/
│   ├── __init__.py         # install gettext, expose _() globally
│   ├── locale/
│   │   ├── cs/LC_MESSAGES/app.mo
│   │   └── en/LC_MESSAGES/app.mo
│   └── strings.pot         # Source template for translators
├── resources/
│   ├── ffmpeg/             # Platform-specific ffmpeg binary (bundled)
│   └── model/              # Whisper medium model weights (bundled)
├── utils/
│   ├── __init__.py
│   ├── paths.py            # sys._MEIPASS resolver for PyInstaller
│   └── gpu.py              # CUDA / MPS / CPU detection
└── whisperai.spec          # PyInstaller spec (defines binaries, datas, hiddenimports)
```

### Structure Rationale

- **gui/:** Pure presentation. No business logic. Widgets read app-level state via callbacks passed in at construction. No direct imports from `services/`.
- **workers/:** Long-running tasks that must not block the Tk event loop. Each worker thread communicates exclusively through `queue.Queue` — never touches Tkinter widgets directly.
- **services/:** Stateless or lightly-stateful domain logic. Importable and testable without a running GUI. Workers call services; services do not know about workers or GUI.
- **i18n/:** Isolated so the `_()` translation function can be installed once at startup and imported anywhere without circular dependencies.
- **resources/:** Static assets that PyInstaller copies into the bundle. Accessed only through `utils/paths.py` to ensure correct resolution whether running from source or packaged.
- **utils/paths.py:** Single place that knows about `sys._MEIPASS`. All other modules call `get_resource_path("ffmpeg/ffmpeg")` instead of hardcoding paths.

## Architectural Patterns

### Pattern 1: Main-Thread-Only GUI Updates via Queue + after()

**What:** Worker threads never touch Tkinter widgets. They put result dicts onto a `queue.Queue`. The main thread polls the queue every 100ms via `root.after(100, poll_queue)` and applies all widget mutations.

**When to use:** Always. Tkinter's Tcl/Tk layer is not thread-safe. Touching widgets from a background thread causes silent corruption or crashes.

**Trade-offs:** 100ms polling adds negligible latency for this use case. Progress updates feel smooth. Error handling is centralised.

**Example:**
```python
# In worker thread
result_queue.put({"type": "progress", "file": path, "status": "processing"})

# In main thread, called by root.after(100, poll_queue)
def poll_queue(self):
    while not self.result_queue.empty():
        msg = self.result_queue.get_nowait()
        if msg["type"] == "progress":
            self.file_panel.set_status(msg["file"], msg["status"])
    self.root.after(100, self.poll_queue)
```

### Pattern 2: One Whisper Model Instance Per Worker Thread

**What:** Each parallel transcription worker loads its own copy of the Whisper model. Models are not shared across threads.

**When to use:** When running N parallel files. Whisper model inference uses forward hooks that are not thread-safe; sharing a model instance across threads causes race conditions.

**Trade-offs:** N parallel workers = N × ~1.5GB model RAM usage. For the configurable 1-N parallelism, default of 1-2 workers is sensible. CPU fallback limits practical parallelism.

**Example:**
```python
class TranscriptionWorker(threading.Thread):
    def run(self):
        model = whisper.load_model("medium", device=detect_device())
        while True:
            job = self.job_queue.get()
            if job is None:
                break
            result = model.transcribe(job.path, language="cs")
            self.result_queue.put({"type": "done", "job": job, "result": result})
```

### Pattern 3: Lazy API Key First-Use Prompt

**What:** The app boots without requiring a Claude API key. When the user clicks "Přepsat + Upravit", the app checks `keyring_service.get_key()`. If absent, it opens a settings dialog, validates the key with a test API call, then stores it via keyring. The core transcription path never touches keyring.

**When to use:** Always — matches the requirement that the app works without Claude API setup.

**Trade-offs:** Slightly more complex first-run flow, but prevents blocking users who only want raw transcription.

### Pattern 4: PyInstaller Resource Path Abstraction

**What:** A single `get_resource_path(relative)` utility resolves the correct base directory whether the app is running from source or from a PyInstaller bundle.

**When to use:** Anywhere a bundled asset (model weights, ffmpeg, locale .mo files) is referenced.

**Example:**
```python
import sys, os

def get_resource_path(relative_path: str) -> str:
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)
```

## Data Flow

### Transcription Flow (core path)

```
User adds files
    ↓
FilePanel → App Controller: [list of paths]
    ↓
App Controller creates Job objects, pushes to job_queue
    ↓
TranscriptionWorker.run() pulls job
    ↓
WhisperService.transcribe(path, device) → raw transcript text
    ↓
Worker puts {"type": "transcript_done", path, text} on result_queue
    ↓
Main thread poll_queue() receives message
    ↓
FileService.write_prepis(path, text) → _prepis.txt
    ↓
FilePanel updates row status to "hotovo"
    ↓
LogPanel appends timestamped entry
```

### Cleanup Flow (Claude path)

```
User clicks "Přepsat + Upravit" (or cleanup runs after transcription)
    ↓
App Controller checks keyring_service.get_key()
    │── key missing → open SettingsPanel key prompt → validate → store
    └── key present → continue
    ↓
ClaudeWorker receives (transcript_text, output_dir)
    ↓
ClaudeService.cleanup(text, api_key) → {edited, summary, diff}
    ↓
Worker puts {"type": "cleanup_done", path, edited, summary, diff} on result_queue
    ↓
FileService.write_upraveno(path, edited, summary, diff) → _upraveno.txt
    ↓
FilePanel updates row status; LogPanel logs completion
```

### Settings / State Flow

```
App startup
    ↓
ConfigService.load() → {output_dir, parallelism, language, ...}
    ↓
i18n.install(language) → gettext installs _() translation function
    ↓
GUI renders with translated strings
    ↓
User changes language toggle
    ↓
i18n.switch(language) → reload translations → GUI re-renders all labels
```

### Key Data Flows Summary

1. **File addition:** User FS path → FilePanel list → Job queue → Worker → result queue → File write + GUI update
2. **Progress reporting:** Worker puts incremental log messages on queue → LogPanel appends (never blocks worker)
3. **API key lifecycle:** First use prompt → keyring store → retrieved per Claude call → never written to disk in plaintext
4. **Bundled resource access:** Any service needing ffmpeg/model calls `get_resource_path()` → correct path in both dev and packaged modes

## Scaling Considerations

This is a local desktop app. "Scaling" means handling longer recordings and more files, not more users.

| Concern | At 1-2 files | At 10-20 files | At 50+ files |
|---------|--------------|----------------|--------------|
| Memory | Fine — 1 model (~1.5GB) | Fine if parallelism capped at 2 | RAM pressure if parallelism > 2; enforce max |
| UI responsiveness | Fine with threading | Fine with queue pattern | Fine; queue pattern scales linearly |
| Disk I/O | Negligible | Negligible | Negligible — text output is small |
| Claude API rate limits | Fine | May hit rate limits — queue requests sequentially | Add exponential backoff in ClaudeService |

### Scaling Priorities

1. **First bottleneck:** VRAM/RAM when running multiple workers with large model. Mitigation: cap parallelism in UI, warn user when selecting N > 2 on CPU.
2. **Second bottleneck:** Claude API rate limiting on large batches. Mitigation: sequential cleanup queue with retry/backoff (not parallel).

## Anti-Patterns

### Anti-Pattern 1: Touching Tkinter Widgets from Worker Threads

**What people do:** Call `label.config(text=...)` or `listbox.insert(...)` directly inside a worker thread.
**Why it's wrong:** Tkinter's Tcl/Tk runtime is single-threaded. Cross-thread widget access causes intermittent crashes, silent data corruption, or deadlocks — often only on macOS or Windows, not reproducible in dev.
**Do this instead:** Put a message dict on `result_queue`; let the main thread's `after()` loop apply all widget mutations.

### Anti-Pattern 2: Sharing a Single Whisper Model Across Threads

**What people do:** Load the model once at startup, then call `model.transcribe()` from multiple threads simultaneously.
**Why it's wrong:** Whisper's KV cache uses forward hooks attached to module objects. Concurrent calls corrupt the cache state, causing garbled output or crashes.
**Do this instead:** Each worker thread loads its own model instance. Accept the RAM cost or enforce parallelism = 1 when RAM is constrained.

### Anti-Pattern 3: Storing the API Key in a Config File

**What people do:** Write `api_key = sk-ant-...` to `config.json` or `settings.ini` in the app data directory.
**Why it's wrong:** Config files are readable by any process running as the user, get accidentally committed to git, and are exposed in crash reports. This is explicitly called out as out-of-spec.
**Do this instead:** Use the `keyring` library — one call routes to Windows Credential Manager or macOS Keychain, both of which encrypt at rest with OS-level protection.

### Anti-Pattern 4: Hardcoding Resource Paths

**What people do:** `open("resources/model/medium.pt")` or `os.path.join(__file__, "..", "ffmpeg")`.
**Why it's wrong:** PyInstaller extracts bundled files to a temp directory (`sys._MEIPASS`) at runtime. Relative paths from `__file__` break in the packaged build on both platforms.
**Do this instead:** All asset access goes through `get_resource_path(relative)` which handles both dev and packaged environments.

### Anti-Pattern 5: Running Transcription on the Main Thread

**What people do:** Call `model.transcribe(path)` directly in a button click handler.
**Why it's wrong:** A 30-minute audio file takes minutes to transcribe. The GUI freezes completely — window can't be moved, the OS marks it as "not responding", and there is no way to show progress.
**Do this instead:** Spawn a worker thread immediately on button click; the main thread stays in the Tk event loop.

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| Anthropic Claude API | `anthropic.Anthropic(api_key=...)` synchronous client in worker thread | Rate limit errors need retry with backoff; structured response via prompt engineering, not tool use |
| OpenAI Whisper (local) | `whisper.load_model()` + `model.transcribe()` — fully local, no network | Model bundled at `resources/model/`; load once per worker at thread start |
| ffmpeg | Subprocess call via `whisper` internals; ffmpeg binary bundled | Path must be on `PATH` or passed explicitly; use `get_resource_path` to locate binary |
| OS Keychain | `keyring.set_password` / `keyring.get_password` | `keyring` auto-selects backend; test at startup, fall back to in-memory if keyring unavailable |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| GUI ↔ Workers | `queue.Queue` (thread-safe) + `root.after()` poll | Workers never import from `gui/`; GUI never calls worker methods directly |
| Workers ↔ Services | Direct function calls (same thread) | Services are pure / stateless; safe to call from any thread |
| Services ↔ Storage | File I/O via `pathlib.Path`; keyring calls are synchronous | `FileService` enforces no-overwrite rule on `_prepis.txt` |
| App ↔ i18n | Module-level `_()` installed at startup | Language switch triggers re-render by re-calling widget `.config(text=_("key"))` on all registered widgets |

## Build Order Implications

Dependencies between components determine what must be built first:

1. **`utils/paths.py` + `utils/gpu.py`** — No dependencies. Everything else calls these.
2. **`services/config_service.py` + `services/keyring_service.py`** — No app dependencies. Needed before GUI and workers.
3. **`i18n/`** — Depends only on `utils/paths.py` (to find `.mo` files). Must initialise before any GUI widget is created.
4. **`services/whisper_service.py` + `services/file_service.py`** — Depend on `utils/`. Can be built and unit-tested standalone.
5. **`services/claude_service.py`** — Depends on `keyring_service`. Can be stubbed with a fake API key for early testing.
6. **`workers/transcription.py` + `workers/cleanup.py`** — Depend on their respective services. Testable without GUI by driving the job queue directly.
7. **`gui/` panels** — Depend on i18n and callbacks from App Controller. Build file_panel → log_panel → settings_panel.
8. **`app.py` (App Controller)** — Wires everything together. Build last.
9. **`whisperai.spec` + packaging** — After all code is working; validates that all bundled paths resolve correctly.

## Sources

- [alexsevas/whisper_gui architecture (DeepWiki)](https://deepwiki.com/alexsevas/whisper_gui) — MEDIUM confidence, real-world reference app
- [Tkinter threading model — runebook.dev](https://runebook.dev/en/docs/python/library/tkinter/threading-model) — HIGH confidence, reflects official Python docs
- [Whisper thread safety — openai/whisper Discussion #296](https://github.com/openai/whisper/discussions/296) — HIGH confidence, official repo discussion
- [Whisper parallelisation via multiprocessing — openai/whisper Discussion #432](https://github.com/openai/whisper/discussions/432) — HIGH confidence, official repo
- [keyring library PyPI](https://pypi.org/project/keyring/) — HIGH confidence, official package
- [platformdirs library](https://platformdirs.readthedocs.io/) — HIGH confidence, official docs
- [PyInstaller + ffmpeg bundling](https://github.com/orgs/pyinstaller/discussions/8089) — MEDIUM confidence, community discussion
- [Python gettext i18n — python.org](https://docs.python.org/3/library/gettext.html) — HIGH confidence, official stdlib docs

---
*Architecture research for: Desktop audio transcription app (Whisper + Tkinter + Claude API)*
*Researched: 2026-03-28*

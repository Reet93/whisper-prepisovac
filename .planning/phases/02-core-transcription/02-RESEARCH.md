# Phase 2: Core Transcription - Research

**Researched:** 2026-03-28
**Domain:** openai-whisper transcription, ProcessPoolExecutor, Tkinter threading, silero-vad, ttk.Treeview, ffprobe
**Confidence:** HIGH (primary stack verified from CLAUDE.md; integration patterns verified via official docs and community sources)

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Treeview table (ttk.Treeview) with four columns: Filename, File Size (human-readable), Duration (from ffprobe), Status (čeká / zpracovává / hotovo / chyba).
- **D-02:** Full file path shown as tooltip on hover over the filename cell.
- **D-03:** Toolbar buttons above the queue: "Přidat soubory" (file picker), "Přidat složku" (folder picker), "Odebrat vybrané" (remove selected rows).
- **D-04:** User can add more files to the queue while transcription is running. New files get "čeká" status and process after current batch.
- **D-05:** When status is "chyba", the status cell shows red text with a warning icon. Hovering shows a tooltip with error type and suggested user action.
- **D-06:** Errors also appear in the real-time log panel with full details.
- **D-07:** Output folder picker in the action bar next to "Přepsat" button — always visible. Shows current output path with a folder browse button.
- **D-08:** Default output location is the same folder as the source file. User can choose a different output folder via the picker.
- **D-09:** Auto-save on completion: `_prepis.txt` is saved automatically when transcription finishes. No manual save required.
- **D-10:** "Uložit jako" available for completed files — lets user re-export a selected "hotovo" file to a different location/name via save dialog.
- **D-11:** Action bar below the file queue table. Contains: output folder path + browse button, "Přepsat" button, overall progress bar.
- **D-12:** During processing, "Přepsat" button becomes "Zastavit" (stop). Clicking stops after the current file finishes.
- **D-13:** ScrolledText panel below the action bar. Read-only, auto-scrolling. Shows timestamped log lines.
- **D-14:** Per-file progress indicator in the queue table (in the status column or as an inline bar for the row being processed).
- **D-15:** Overall progress bar in the action bar showing "X of Y souborů".
- **D-16:** Auto-detect CUDA (Windows) or MPS (macOS) at startup. If GPU available, use it. If not, silently fall back to CPU.
- **D-17:** Log message confirms which device is active: "Zařízení: CUDA (GPU name)" or "GPU nedostupné, používám CPU". No blocking dialog.
- **D-18:** Use silero-vad (PyTorch-based, ~2 MB model weights). Already have PyTorch via Whisper.
- **D-19:** VAD strips silence before feeding audio to Whisper.
- **D-20:** Implement ProcessPoolExecutor in Phase 2 for parallel file processing (TRANS-04).
- **D-21:** Hardcode sensible defaults: 1 worker for GPU mode (VRAM contention), auto-detect CPU core count for CPU-only mode.

### Claude's Discretion

- Exact log line format and timestamp style
- Treeview row styling details (colors, fonts for status states)
- Threading architecture (how background thread communicates with Tkinter main loop via queue)
- ffprobe invocation pattern for reading audio duration
- Exact silero-vad integration approach (torch.hub vs pip install)
- How ProcessPoolExecutor workers load the Whisper model (once per worker process)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.

</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FILE-01 | User can add individual audio files via file picker (.mp3, .wav, .m4a, .ogg) | tkinter.filedialog.askopenfilenames with filetypes filter |
| FILE-02 | User can add all audio files from a folder via folder picker | tkinter.filedialog.askdirectory + pathlib glob for audio extensions |
| FILE-03 | User can see list of loaded files with status (čeká / zpracovává / hotovo) | ttk.Treeview with tags for status color-coding |
| FILE-04 | User can remove files from the queue before processing | Treeview.delete() on selected items; guard against removal during active row |
| FILE-05 | User can save single output via "Save as" dialog | tkinter.filedialog.asksaveasfilename; read completed transcript from memory or disk |
| FILE-06 | User can select output folder for batch auto-save (_prepis.txt naming) | StringVar for output_dir; tkinter.filedialog.askdirectory |
| TRANS-01 | Transcribe audio using Whisper medium model with Czech language | whisper.load_model("medium", download_root=...) + model.transcribe(audio, language="cs") |
| TRANS-02 | Auto-detect GPU (CUDA/MPS) with CPU fallback | torch.cuda.is_available() / torch.backends.mps.is_available(); pass device to load_model |
| TRANS-03 | Real-time log during transcription (file name, progress, device used) | tqdm override pattern injected into whisper.transcribe module; queue.Queue + root.after() |
| TRANS-04 | Configurable parallel workers (1-N) | ProcessPoolExecutor with initializer= for one model load per worker; D-21 defaults hardcoded for Phase 2 |
| TRANS-05 | VAD preprocessing to prevent hallucinations on silence | silero-vad pip package; get_speech_timestamps + torch.cat to rebuild speech-only tensor |
| TRANS-06 | Clear error messages when transcription fails | try/except in worker; error string sent via multiprocessing.Manager().Queue(); displayed in log + Treeview tag |

</phase_requirements>

---

## Summary

Phase 2 builds the complete transcription loop on top of the Phase 1 skeleton: a file-queue Treeview, a threaded dispatcher that runs ProcessPoolExecutor workers, real-time log feedback via a queue/after() pump, VAD preprocessing, GPU auto-detection, and auto-saved `_prepis.txt` output.

The most technically nuanced parts are: (1) real-time progress from Whisper, which requires injecting a custom tqdm subclass into `whisper.transcribe` because `transcribe()` has no official callback parameter; (2) cross-process progress messaging, which requires `multiprocessing.Manager().Queue()` (not `queue.Queue`, which is in-process only) passed via ProcessPoolExecutor `initializer`; and (3) silero-vad, which needs `torchaudio` for audio I/O and has a known PyInstaller/torchaudio incompatibility that must be addressed in the spec file (Phase 4) but the dependency must be added to `requirements.in` now.

The existing Phase 1 code is clean and well-structured. `content_frame`, `get_resource_path()`, `_()`, and `freeze_support()` are all in place. Phase 2 replaces the placeholder label in `content_frame` with the full transcription UI, keeping the header/footer untouched.

**Primary recommendation:** Build a `TranscriptionController` class that owns the Treeview, action bar, log panel, and the background threading/queue logic. Keep it in `src/whisperai/gui/transcription_panel.py` with a separate `src/whisperai/core/transcriber.py` for the worker-side Whisper logic.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| openai-whisper | 20250625 | Audio transcription | Project constraint; medium model for Czech accuracy |
| torch | 2.11.0 | Tensor computation + GPU backend | Required by Whisper; provides CUDA/MPS detection |
| torchaudio | 2.11.0 (match torch) | Audio I/O for silero-vad | Required by silero-vad read_audio helper |
| silero-vad | latest pip | Voice activity detection | PyTorch-native, ~2 MB model, no C extensions |
| ttkbootstrap | 1.20.2 | UI theming + ToolTip | Already installed; ToolTip class needed for path and error tooltips |
| tkinter (stdlib) | Python 3.12 stdlib | GUI framework | Project constraint |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| concurrent.futures (stdlib) | Python 3.12 stdlib | ProcessPoolExecutor for parallel transcription | Always — D-20 mandates it |
| threading (stdlib) | Python 3.12 stdlib | Background thread for ProcessPoolExecutor dispatch | Always — keeps Tkinter event loop unblocked |
| queue (stdlib) | Python 3.12 stdlib | Thread-safe in-process message passing (main thread side) | Always — Tkinter queue polling via root.after() |
| multiprocessing.Manager (stdlib) | Python 3.12 stdlib | Cross-process queue for worker → dispatcher progress messages | Required — queue.Queue cannot cross process boundaries |
| pathlib (stdlib) | Python 3.12 stdlib | File path handling | Always — already established in Phase 1 |
| logging (stdlib) | Python 3.12 stdlib | Structured log output | Already mandated by CLAUDE.md |
| json (stdlib) | Python 3.12 stdlib | Parse ffprobe duration output | Always — ffprobe -print_format json |
| subprocess (stdlib) | Python 3.12 stdlib | Invoke ffprobe for duration metadata | Always |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| silero-vad pip | torch.hub.load | torch.hub downloads at runtime; violates bundled-assets constraint. Use `pip install silero-vad` and bundle the ~2 MB model weights via PyInstaller datas. |
| multiprocessing.Manager().Queue() | multiprocessing.Queue() | multiprocessing.Queue() is also valid for this use case. Manager().Queue() is more flexible but adds a manager server process. Either works; plain multiprocessing.Queue() is simpler and preferred for Phase 2. |
| tqdm override for progress | subprocess stderr parsing | Subprocess approach runs Whisper CLI, not the Python API — breaks model reuse per worker. tqdm injection stays in-process and reuses the loaded model. |

**Installation additions to requirements.in:**
```bash
# Add to requirements.in:
openai-whisper==20250625
torch==2.11.0  # Use CUDA wheel on Windows: pip install torch==2.11.0+cu124 --index-url https://download.pytorch.org/whl/cu124
torchaudio==2.11.0  # Must match torch version
silero-vad  # Latest pip release
```

**Note on torch CUDA wheel:** The standard PyPI torch wheel is CPU-only. On Windows, install the CUDA-enabled wheel from pytorch.org. On macOS, the standard wheel includes MPS. This distinction is documented in CLAUDE.md and must be reflected in build notes, not requirements.in (which uses the standard wheel).

---

## Architecture Patterns

### Recommended Project Structure Addition

```
src/whisperai/
├── gui/
│   ├── main_window.py        # Phase 1 — do not modify structure
│   ├── transcription_panel.py  # NEW: TranscriptionPanel class (Treeview + action bar + log)
│   └── __init__.py
├── core/
│   ├── transcriber.py        # NEW: worker-side Whisper logic (runs in subprocess)
│   ├── vad.py                # NEW: silero-vad preprocessing helper
│   ├── device.py             # NEW: GPU detection helper
│   └── __init__.py           # NEW
├── utils/
│   ├── resource_path.py      # Phase 1
│   ├── i18n.py               # Phase 1
│   └── __init__.py           # Phase 1
└── app.py                    # Phase 1 — updated to instantiate TranscriptionPanel
```

### Pattern 1: Worker-Side Whisper Model Loading (once per ProcessPoolExecutor worker)

**What:** Use ProcessPoolExecutor `initializer` to load the Whisper model once per worker process. Store in a module-level global so subsequent tasks in the same worker reuse it.

**When to use:** Any time ProcessPoolExecutor processes heavy models. Loading Whisper medium takes 5-15 seconds and ~1.5 GB RAM — it must happen once per worker, not once per file.

```python
# src/whisperai/core/transcriber.py
# Source: https://superfastpython.com/processpoolexecutor-initializer/

import whisper
import torch

_model = None  # module-level, set once per worker process

def _worker_init(model_path: str, device: str) -> None:
    """Called once per worker process by ProcessPoolExecutor initializer."""
    global _model
    _model = whisper.load_model(
        "medium",
        device=device,
        download_root=model_path,
    )

def transcribe_file(
    audio_path: str,
    progress_queue: "multiprocessing.Queue",
    task_id: str,
) -> dict:
    """Transcribe one file. Returns result dict or raises on error."""
    import sys
    import tqdm as tqdm_module

    class _ProgressHook(tqdm_module.tqdm):
        def update(self, n=1):
            super().update(n)
            progress_queue.put({
                "type": "progress",
                "task_id": task_id,
                "n": self.n,
                "total": self.total,
            })

    # Inject custom tqdm into whisper's transcribe module BEFORE calling transcribe
    whisper_transcribe = sys.modules.get("whisper.transcribe")
    if whisper_transcribe:
        whisper_transcribe.tqdm.tqdm = _ProgressHook

    result = _model.transcribe(
        audio_path,
        language="cs",
        verbose=False,
    )
    return result
```

### Pattern 2: Cross-Process Progress Queue

**What:** `multiprocessing.Queue` passed to worker via task arguments. Worker sends progress dicts; dispatcher background thread drains the queue and puts messages into an in-process `queue.Queue`; Tkinter main thread polls via `root.after()`.

**When to use:** Any time worker processes must report progress back to a Tkinter GUI.

```python
# Dispatcher (background thread in main process)
# Source: Python docs https://docs.python.org/3/library/multiprocessing.html

import multiprocessing
import queue
import threading
import concurrent.futures

def run_batch(
    files: list[str],
    model_path: str,
    device: str,
    workers: int,
    ui_queue: queue.Queue,       # in-process queue → Tkinter main thread
) -> None:
    mp_queue = multiprocessing.Queue()  # cross-process queue ← workers

    def drain_mp_queue():
        """Forward messages from mp_queue to ui_queue (runs in dispatcher thread)."""
        while True:
            try:
                msg = mp_queue.get(timeout=0.1)
                if msg is None:
                    break
                ui_queue.put(msg)
            except Exception:
                pass

    drain_thread = threading.Thread(target=drain_mp_queue, daemon=True)
    drain_thread.start()

    with concurrent.futures.ProcessPoolExecutor(
        max_workers=workers,
        initializer=_worker_init,
        initargs=(model_path, device),
    ) as pool:
        futures = {
            pool.submit(transcribe_file, f, mp_queue, str(i)): f
            for i, f in enumerate(files)
        }
        for future in concurrent.futures.as_completed(futures):
            filepath = futures[future]
            try:
                result = future.result()
                ui_queue.put({"type": "done", "file": filepath, "result": result})
            except Exception as exc:
                ui_queue.put({"type": "error", "file": filepath, "error": str(exc)})

    mp_queue.put(None)  # signal drain thread to stop
```

### Pattern 3: Tkinter Queue Drain via root.after()

**What:** Tkinter is single-threaded. The only safe way to update widgets from a background thread is via `root.after()`. Poll the in-process queue, drain all pending messages, then reschedule.

**When to use:** Always — any background thread updating Tkinter widgets must use this pattern.

```python
# In TranscriptionPanel (Tkinter main thread)
# Source: Python Tkinter threading model docs

def _start_queue_poll(self) -> None:
    self._drain_ui_queue()

def _drain_ui_queue(self) -> None:
    try:
        while True:
            msg = self._ui_queue.get_nowait()
            self._handle_message(msg)
    except queue.Empty:
        pass
    # Reschedule poll every 100ms while transcription is active
    if self._running:
        self.root.after(100, self._drain_ui_queue)

def _handle_message(self, msg: dict) -> None:
    if msg["type"] == "progress":
        self._update_row_progress(msg["task_id"], msg["n"], msg["total"])
        self._append_log(f"[{msg['task_id']}] {msg['n']}/{msg['total']} segmentů")
    elif msg["type"] == "done":
        self._mark_row_done(msg["file"])
        self._save_transcript(msg["file"], msg["result"]["text"])
    elif msg["type"] == "error":
        self._mark_row_error(msg["file"], msg["error"])
```

### Pattern 4: VAD Preprocessing with silero-vad

**What:** Load silero-vad model, detect speech segments, extract and concatenate only speech audio tensors, write temporary WAV, feed that to Whisper.

**When to use:** Before every Whisper transcription call (D-19).

```python
# src/whisperai/core/vad.py
# Source: https://github.com/snakers4/silero-vad

from silero_vad import load_silero_vad, read_audio, get_speech_timestamps
import torch
import torchaudio

_vad_model = None  # loaded once per worker process alongside Whisper

def get_vad_model():
    global _vad_model
    if _vad_model is None:
        _vad_model = load_silero_vad()
    return _vad_model

def preprocess_audio(audio_path: str, sample_rate: int = 16000) -> torch.Tensor:
    """Return speech-only audio tensor at 16 kHz. Strips silence."""
    wav = read_audio(audio_path, sampling_rate=sample_rate)
    model = get_vad_model()
    timestamps = get_speech_timestamps(wav, model, return_seconds=False)
    if not timestamps:
        # No speech detected — return empty tensor (Whisper will produce no output)
        return torch.zeros(0)
    speech_chunks = [wav[ts["start"]: ts["end"]] for ts in timestamps]
    return torch.cat(speech_chunks)
```

**Important:** `read_audio` from silero-vad requires `torchaudio`. Since ffmpeg is already bundled as a static binary (PATH-prepended at startup), torchaudio can use ffmpeg as its I/O backend — this is the recommended approach given the existing ffmpeg dependency.

### Pattern 5: ffprobe Duration Extraction

**What:** Run bundled ffprobe binary via subprocess with JSON output to get audio duration. Use `get_resource_path()` to locate the binary in both dev and frozen contexts.

**When to use:** When loading files into the Treeview queue (D-01 requires duration column).

```python
# Source: https://ffmpeg.org/ffprobe.html + ffprobe JSON output pattern

import subprocess
import json
from pathlib import Path
from src.whisperai.utils.resource_path import get_resource_path

def get_audio_duration(audio_path: Path) -> float | None:
    """Return duration in seconds using bundled ffprobe. Returns None on failure."""
    # ffprobe is in the same bin/ directory as ffmpeg
    ffprobe = get_resource_path("bin/ffprobe")
    # On Windows the binary is ffprobe.exe
    if not ffprobe.exists():
        ffprobe = get_resource_path("bin/ffprobe.exe")
    if not ffprobe.exists():
        return None
    try:
        result = subprocess.run(
            [
                str(ffprobe),
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-print_format", "json",
                str(audio_path),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )
        data = json.loads(result.stdout)
        return float(data["format"]["duration"])
    except Exception:
        return None
```

### Pattern 6: GPU Detection

**What:** Check for CUDA then MPS, fall back to CPU. Return a `torch.device` string consumed by `whisper.load_model(device=...)`.

```python
# src/whisperai/core/device.py
# Source: CLAUDE.md + PyTorch docs https://docs.pytorch.org/docs/stable/mps.html

import torch

def detect_device() -> tuple[str, str]:
    """Return (torch_device_str, human_label) for the best available device."""
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        return "cuda", f"CUDA ({name})"
    if torch.backends.mps.is_available():
        return "mps", "MPS (Apple Silicon)"
    return "cpu", "CPU"
```

### Pattern 7: Treeview Tag-Based Row Styling

**What:** ttk.Treeview supports per-row tags that control foreground/background color. Define tags at widget creation; apply them when updating row status.

**When to use:** Status column color coding (D-05: chyba = red).

```python
# Source: TkDocs https://tkdocs.com/tutorial/tree.html

tree = ttk.Treeview(parent, columns=("size", "duration", "status"), show="headings")
tree.tag_configure("waiting",    foreground="#2C3E50")   # flatly text primary
tree.tag_configure("processing", foreground="#18BC9C")   # flatly teal accent
tree.tag_configure("done",       foreground="#18BC9C")   # flatly teal accent
tree.tag_configure("error",      foreground="#E74C3C")   # flatly destructive red

# When updating a row:
tree.item(row_id, tags=("error",))
```

### Pattern 8: Cell-Level Tooltip on Treeview

**What:** Bind `<Motion>` on the Treeview, use `tree.identify_column()` and `tree.identify_row()` to detect which cell is hovered, then dynamically update a ToolTip's text.

**When to use:** D-02 (full path tooltip on filename), D-05 (error tooltip on error status).

```python
# Source: ttkbootstrap ToolTip docs (community verified)
# ttkbootstrap.tooltip.ToolTip(widget, text="...", wraplength=300)

from ttkbootstrap.tooltip import ToolTip

# Create one shared tooltip instance; update text on motion
_cell_tooltip = ToolTip(tree, text="", wraplength=400, bootstyle="secondary")

def _on_tree_motion(event):
    col = tree.identify_column(event.x)
    row = tree.identify_row(event.y)
    if not row:
        return
    if col == "#1":  # Filename column → show full path
        full_path = _row_data[row]["full_path"]
        _cell_tooltip.text = full_path
    elif col == "#4" and tree.item(row)["tags"] == ("error",):  # Status → show error detail
        error_msg = _row_data[row]["error"]
        _cell_tooltip.text = error_msg

tree.bind("<Motion>", _on_tree_motion)
```

**Note:** ttkbootstrap's ToolTip is attached to a widget, not a cell. The motion-based update pattern is the standard approach for cell-level tooltips in Tkinter (no native cell tooltip API exists).

### Pattern 9: Stop-After-Current-File Pattern (D-12)

**What:** A threading.Event signals the dispatcher to not submit new futures after the current one completes.

```python
_stop_event = threading.Event()

# In dispatch loop:
for i, f in enumerate(files):
    if _stop_event.is_set():
        # Revert remaining to "čeká"
        ui_queue.put({"type": "reverted", "files": files[i:]})
        break
    future = pool.submit(transcribe_file, f, mp_queue, str(i))
```

### Anti-Patterns to Avoid

- **Calling Tkinter widget methods from a worker thread:** ALL widget updates must happen in the main thread via `root.after()` or via the queue drain pattern. Calling `tree.item()` or `log.insert()` directly from a background thread causes silent corruption or crashes.
- **Loading Whisper model per file:** Whisper medium loads in 5-15 seconds and uses ~1.5 GB RAM. Load once per worker via ProcessPoolExecutor `initializer=`.
- **Using queue.Queue across processes:** `queue.Queue` is in-process only. For worker → dispatcher communication, use `multiprocessing.Queue` (created in the main process and passed to workers as a task argument).
- **torch.hub.load for silero-vad:** Downloads the model from the internet at runtime. Use `pip install silero-vad` and bundle the model weights with PyInstaller. The torch.hub approach breaks the offline/bundled constraint.
- **Calling `model.transcribe()` in the main thread:** Blocks the Tkinter event loop completely. Always run in a background `threading.Thread` (which then dispatches to ProcessPoolExecutor workers).
- **Using `verbose=True` on transcribe() for progress:** verbose=True prints to stdout/stderr, which cannot be captured per-file in a multi-worker scenario. Use the tqdm injection pattern instead.
- **Importing `src.whisperai.*` in worker subprocess on Windows:** On Windows, ProcessPoolExecutor spawns new Python processes that re-import `__main__`. Worker modules (transcriber.py, vad.py) must be importable without triggering side effects. The `freeze_support()` call in `main.py` handles the frozen case, but dev-mode workers must also be safe.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Silence detection / VAD | Manual energy-threshold silence stripper | silero-vad | Silero uses a neural network; energy thresholds fail on background noise, low-volume speech, and non-Czech phonetics |
| GPU detection | Manual CUDA env var reading | `torch.cuda.is_available()` + `torch.backends.mps.is_available()` | PyTorch handles platform-specific driver checks, version mismatches, and CUDA initialization errors |
| Audio duration metadata | Decode audio with librosa/soundfile | ffprobe -show_entries format=duration | ffprobe is already bundled; it handles all formats including m4a/ogg container metadata correctly |
| Cross-thread UI updates | shared mutable state + mutex | queue.Queue + root.after() | The only officially supported safe pattern for Tkinter multi-threading |
| Progress bar widget | Custom Canvas animation | ttkbootstrap ttk.Progressbar | ttkbootstrap's Progressbar has `bootstyle` theming and handles indeterminate + determinate modes |
| Tooltip on Treeview cell | Custom popup Toplevel window | ttkbootstrap ToolTip class | ToolTip handles show/hide timing, positioning, and styling; building a custom popup is 50+ lines with platform-specific focus bugs |

**Key insight:** The tqdm injection for Whisper progress, while unconventional, is the established community pattern for this specific use case. `transcribe()` has no official progress callback. Building a subprocess wrapper to capture stderr output would be more complex and would break model reuse across files.

---

## Common Pitfalls

### Pitfall 1: multiprocessing.Queue vs queue.Queue

**What goes wrong:** Developer creates a `queue.Queue()` in the main process, passes it to ProcessPoolExecutor worker, and workers can't put messages on it (or silently discard them). UI never receives progress updates.

**Why it happens:** `queue.Queue` is in-process only. ProcessPoolExecutor workers run in separate OS processes with separate memory spaces. A `queue.Queue` cannot cross a process boundary — it gets pickled and unpickled as a new empty queue in each worker.

**How to avoid:** Create `multiprocessing.Queue()` (or `multiprocessing.Manager().Queue()`) in the main process. Pass it to worker tasks as a regular argument. Workers call `mp_queue.put(msg)` which uses IPC.

**Warning signs:** No progress messages appear in the UI even though transcription completes correctly.

---

### Pitfall 2: Torchaudio PyInstaller Incompatibility

**What goes wrong:** The packaged app (Phase 4) fails to start or raises a RuntimeError when importing torchaudio on Windows.

**Why it happens:** torchaudio on Windows has known PyInstaller incompatibilities (GitHub issue pytorch/audio#2470). The binary extension fails to load from `_internal/` when frozen.

**How to avoid:** In the Phase 4 PyInstaller spec, add `collect_dynamic_libs('torchaudio')` and ensure the torchaudio backend can locate ffmpeg. For Phase 2 (dev mode), this is not an issue — it will manifest only during Phase 4 packaging. Document it as a known Phase 4 concern now.

**Warning signs:** `ImportError: cannot import name '_torchaudio'` or `RuntimeError: Failed to load audio backend` in the frozen executable.

---

### Pitfall 3: Whisper Model Path in Worker Processes

**What goes wrong:** Worker process calls `whisper.load_model("medium")` without `download_root`, causing Whisper to look in `~/.cache/whisper/` — which won't exist in the packaged app, or will cause an unexpected download.

**Why it happens:** Whisper's default download directory is user-level cache. The bundled app has the model in `_internal/models/` (PyInstaller `_MEIPASS`).

**How to avoid:** Always pass `download_root=get_resource_path("models")` to `whisper.load_model()`. In worker processes, the `model_path` string is passed via `ProcessPoolExecutor(initargs=(model_path, device))`. The worker calls `str(get_resource_path(...))` before creating the executor — the resource path must be resolved in the main process and passed as a plain string (Path objects are picklable but resolving `sys._MEIPASS` in a worker process is unreliable).

**Warning signs:** Worker process starts a download to `~/.cache/whisper/` or raises `FileNotFoundError` for model files.

---

### Pitfall 4: Tkinter Widget Updates from Background Thread

**What goes wrong:** `tree.item(row_id, values=...)` or `log_text.insert(...)` called from a `threading.Thread` target — causes intermittent crashes, visual corruption, or `RuntimeError: main thread is not in main loop` on macOS.

**Why it happens:** Tkinter is not thread-safe. Its underlying Tcl/Tk interpreter is single-threaded.

**How to avoid:** All widget state changes go through `ui_queue.put(msg)` in the background thread and are consumed only in the `root.after()` drain callback which runs in the main thread.

**Warning signs:** Intermittent `_tkinter.TclError`, app freezes on macOS but not Windows (Tk's thread-safety behavior differs by platform).

---

### Pitfall 5: Stop Button Race Condition

**What goes wrong:** User clicks "Zastavit" while a file is mid-transcription. The worker finishes and puts a "done" message. The dispatcher has already set `_stop_event` but the "done" message still arrives and triggers an auto-save to the output folder.

**Why it happens:** ProcessPoolExecutor does not cancel in-flight futures. `future.cancel()` only works for futures that haven't started yet.

**How to avoid:** D-12 specifies "stops after the current file finishes" — this is the correct behavior. Completed files keep their output. The implementation must check `_stop_event` only between file submissions, not attempt to interrupt in-flight workers.

**Warning signs:** Users report partial transcriptions being saved when clicking Stop.

---

### Pitfall 6: silero-vad Audio at Wrong Sample Rate

**What goes wrong:** silero-vad receives audio at 44100 Hz (default for many .mp3 files) instead of 16000 Hz, causing incorrect speech timestamps or VAD model assertion errors.

**Why it happens:** silero-vad only supports 8000 Hz and 16000 Hz. `read_audio()` accepts a `sampling_rate` parameter — if omitted or set incorrectly, the audio is not resampled.

**How to avoid:** Always call `read_audio(path, sampling_rate=16000)`. torchaudio will resample automatically if the source sample rate differs.

**Warning signs:** VAD returns no speech timestamps for files that clearly contain speech, or assertion errors about sampling rate.

---

### Pitfall 7: Adding Files During Active Transcription (D-04)

**What goes wrong:** User adds files while ProcessPoolExecutor workers are running. The new files are not submitted to the pool because the `with ProcessPoolExecutor(...) as pool:` block has already closed.

**Why it happens:** ProcessPoolExecutor's context manager shuts down the pool on exit (joining all workers). Files added after the executor closes are silently ignored.

**How to avoid:** Implement a persistent queue model: maintain a `_pending_files` deque. The dispatcher thread processes from `_pending_files` in a loop, using `pool.submit()` directly (not iterating a snapshot list). Files added mid-run are appended to `_pending_files` and picked up by the running dispatcher thread. The executor is kept alive until `_pending_files` is empty AND `_stop_event` is set.

**Warning signs:** Files added during transcription get "čeká" status but never start processing.

---

## Code Examples

### Whisper transcribe() Return Structure

```python
# Source: https://github.com/openai/whisper/blob/main/whisper/transcribe.py
result = model.transcribe("audio.wav", language="cs", verbose=False)
# result = {
#     "text": "Přepis celého souboru...",
#     "segments": [
#         {
#             "id": 0,
#             "seek": 0,
#             "start": 0.0,
#             "end": 4.5,
#             "text": " První věta.",
#             "tokens": [...],
#             "temperature": 0.0,
#             "avg_logprob": -0.25,
#             "compression_ratio": 1.4,
#             "no_speech_prob": 0.01,
#         },
#         ...
#     ],
#     "language": "cs",
# }
output_text = result["text"]
```

### GPU Detection and Device Selection

```python
# Source: CLAUDE.md, PyTorch MPS docs https://docs.pytorch.org/docs/stable/mps.html
import torch

def detect_device() -> tuple[str, str]:
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        return "cuda", f"CUDA ({name})"
    if torch.backends.mps.is_available():
        return "mps", "MPS (Apple Silicon)"
    return "cpu", "CPU"

device_str, human_label = detect_device()
# Log: f"Zařízení: {human_label}"
```

### Auto-Save Output File Naming

```python
# Source: CONTEXT.md D-08, D-09
from pathlib import Path

def get_output_path(source_path: Path, output_dir: Path | None) -> Path:
    """Derive _prepis.txt path. Uses source folder if output_dir is None."""
    base = output_dir if output_dir else source_path.parent
    stem = source_path.stem  # "recording" from "recording.mp3"
    return base / f"{stem}_prepis.txt"

def save_transcript(source_path: Path, text: str, output_dir: Path | None) -> Path:
    out = get_output_path(source_path, output_dir)
    out.write_text(text, encoding="utf-8")
    return out
```

### Human-Readable File Size

```python
def human_size(bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if bytes < 1024:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024
    return f"{bytes:.1f} TB"
```

### Human-Readable Duration

```python
def human_duration(seconds: float | None) -> str:
    if seconds is None:
        return "—"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `torch.hub.load` for silero-vad | `pip install silero-vad` + `from silero_vad import load_silero_vad` | ~2023, pip package stable | Bundlable without internet access at runtime |
| `multiprocessing.Pool` for parallel tasks | `concurrent.futures.ProcessPoolExecutor` with `initializer=` | Established pattern, CLAUDE.md mandated | Cleaner API, handles `freeze_support()` more gracefully with PyInstaller |
| Polling `whisper.transcribe(verbose=True)` stdout | tqdm subclass injection into `whisper.transcribe` module | Community established ~2023 | In-process, per-worker, model reuse |
| `tkinter.filedialog.askopenfilename` (single) | `tkinter.filedialog.askopenfilenames` (multiple) | Available since Tkinter stdlib | FILE-01 requires multi-select |

**Deprecated/outdated:**
- `whisper.audio.load_audio()`: Still available but since we have silero-vad preprocessing, load audio via `silero_vad.read_audio()` at 16 kHz, then pass the speech-only tensor directly to `model.transcribe()` (which accepts `np.ndarray` or `torch.Tensor`).

---

## Open Questions

1. **silero-vad model bundling path**
   - What we know: `load_silero_vad()` loads from pip-installed package directory by default. In frozen PyInstaller app the package files are in `_internal/`.
   - What's unclear: Whether `load_silero_vad()` from the `silero-vad` pip package locates its own `.jit` model file correctly in a PyInstaller `--onedir` context, or whether we need to pass an explicit path.
   - Recommendation: Test in dev mode first (Phase 2). Flag as a potential Phase 4 packaging concern. If `load_silero_vad()` fails in frozen mode, pass `model_or_path=get_resource_path("silero_vad/silero_vad.jit")` explicitly.

2. **Per-row inline progress in Treeview (D-14)**
   - What we know: ttk.Treeview cells display text values only — no native widget embedding. There is no way to put a ttk.Progressbar inside a Treeview cell with standard Tkinter.
   - What's unclear: Whether a percentage string in the status column ("zpracovává 34%") is sufficient for D-14, or whether the user expects a visual bar.
   - Recommendation: Use text percentage in the status column ("zpracovává 34%") during processing. This satisfies D-14 without complex cell embedding. A visual bar inside a Treeview cell requires `window_create()` or overlay techniques that are fragile across platforms.

3. **MPS operator coverage for Whisper medium**
   - What we know: Whisper uses standard PyTorch ops. MPS backend is available since PyTorch 2.0 and improves with each release. CLAUDE.md notes MPS is "bundled since PyTorch 2.0".
   - What's unclear: Whether all Whisper medium ops are covered by MPS in PyTorch 2.11 on Apple Silicon, or whether some ops fall back to CPU silently.
   - Recommendation: STATE.md flags this as needing validation on actual hardware. Implement MPS detection as specified (D-16/D-17) but add a try/except around model load that falls back to CPU with a log warning if MPS raises `RuntimeError`.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|-------------|-----------|---------|----------|
| Python 3.12 | Full stack (Whisper/PyTorch constraint) | Partial — 3.9.13 on dev machine | 3.9.13 | **Blocking**: Must install Python 3.12 before Phase 2 work begins (STATE.md records this: "Python 3.14 used for Phase 1 dev verification — Python 3.12 required before Phase 2") |
| ffmpeg / ffprobe static binary | Audio decoding (Whisper) + duration metadata | NOT found on PATH | — | Must download and place in `bin/` subdirectory (Windows: BtbN builds; macOS: evermeet.cx) |
| openai-whisper 20250625 | TRANS-01 through TRANS-06 | Not installed | — | No fallback — must install |
| torch 2.11.0 (CUDA on Windows) | openai-whisper, silero-vad, device.py | Not installed | — | No fallback — must install |
| torchaudio 2.11.0 | silero-vad read_audio | Not installed | — | No fallback — required by silero-vad I/O |
| silero-vad (pip) | TRANS-05 VAD preprocessing | Not installed | — | No fallback — required for D-18/D-19 |
| ttkbootstrap 1.20.2 | All GUI | Installed | 1.20.2 | — |

**Missing dependencies with no fallback (blocking execution):**
- Python 3.12.x — current dev Python is 3.9.13; Phase 2 cannot proceed without upgrading (Whisper/PyTorch incompatibility with 3.9 is possible, and CLAUDE.md mandates 3.12)
- ffmpeg/ffprobe static binaries — must be downloaded and placed in `bin/` before dev or packaging
- openai-whisper 20250625 + torch 2.11.0 + torchaudio 2.11.0 — must be installed in requirements.txt

**Missing dependencies with fallback:**
- None identified. All required dependencies are either installed or have no viable fallback.

---

## Project Constraints (from CLAUDE.md)

These directives are **mandatory**. The planner must not recommend approaches that contradict them.

| Directive | Applies To |
|-----------|-----------|
| Python 3.12.x only (avoid 3.13, avoid 3.10.0) | All wave tasks |
| openai-whisper 20250625 (not faster-whisper) | TRANS-01 implementation |
| PyTorch 2.11.0 with CUDA wheel on Windows, standard on macOS | TRANS-02 dev setup |
| Tkinter + ttkbootstrap only (no PyQt, wx, CustomTkinter) | All GUI tasks |
| PyInstaller `--onedir` (not `--onefile`) | Phase 4 concern; note in spec |
| ProcessPoolExecutor (not multiprocessing.Pool) + freeze_support() in main() | TRANS-04 implementation |
| API keys in OS keyring only (not relevant to Phase 2 — no API key here) | N/A Phase 2 |
| whisper.load_model with explicit download_root | TRANS-01 |
| pathlib.Path throughout (not os.path) | All file handling tasks |
| All user-visible strings through _() i18n function | All UI tasks |
| pywin32 must be bundled for keyring (not relevant Phase 2) | N/A Phase 2 |
| ProcessPoolExecutor workers: 1 for GPU, cpu_count() for CPU | D-21 hardcoded in Phase 2 |
| Static ffmpeg binary in bin/, PATH-prepended at startup | Environment setup + transcriber.py startup |

---

## Sources

### Primary (HIGH confidence)
- CLAUDE.md (project instructions) — full stack specification, version constraints, packaging patterns
- [openai/whisper transcribe.py on GitHub](https://github.com/openai/whisper/blob/main/whisper/transcribe.py) — exact `transcribe()` signature, return structure, verbose parameter
- [PyTorch MPS backend docs](https://docs.pytorch.org/docs/stable/mps.html) — `torch.backends.mps.is_available()` API
- [Python concurrent.futures docs](https://docs.python.org/3/library/concurrent.futures.html) — ProcessPoolExecutor initializer, as_completed
- [Python multiprocessing docs](https://docs.python.org/3/library/multiprocessing.html) — multiprocessing.Queue
- [TkDocs ttk.Treeview tutorial](https://tkdocs.com/tutorial/tree.html) — tag_configure, identify_column, identify_row
- [silero-vad GitHub README](https://github.com/snakers4/silero-vad) — pip install method, load_silero_vad, read_audio, get_speech_timestamps
- [silero-vad wiki: Examples and Dependencies](https://github.com/snakers4/silero-vad/wiki/Examples-and-Dependencies) — torchaudio requirement, audio backends

### Secondary (MEDIUM confidence)
- [Whisper discussion #850: progress bar](https://github.com/openai/whisper/discussions/850) — tqdm injection pattern, community-verified workaround
- [SuperFastPython: ProcessPoolExecutor initializer](https://superfastpython.com/processpoolexecutor-initializer/) — initializer/initargs pattern for model loading
- [torchaudio PyInstaller issue #2470](https://github.com/pytorch/audio/issues/2470) — known Windows PyInstaller incompatibility with torchaudio
- [ttkbootstrap ToolTip docs (community verified)](https://www.plus2net.com/python/tkinter-ttkbootstrap-tooltip.php) — ToolTip API, wraplength, bootstyle parameters

### Tertiary (LOW confidence)
- [mad-whisper-progress on PyPI](https://pypi.org/project/mad-whisper-progress/) — mentioned as alternative progress approach; not verified for openai-whisper 20250625 compatibility

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — fully defined in CLAUDE.md, versions verified on PyPI
- Whisper API: HIGH — verified from transcribe.py source code directly
- Threading/queue architecture: HIGH — Python stdlib docs, well-established patterns
- VAD integration: MEDIUM — pip install approach verified; PyInstaller bundling (Phase 4 concern) is LOW
- Treeview tooltips: MEDIUM — ToolTip class verified; cell-level motion binding is community pattern without official Tkinter docs
- ffprobe integration: HIGH — standard subprocess + JSON output, ffprobe docs

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable libraries; PyTorch/Whisper release cadence is months, not weeks)

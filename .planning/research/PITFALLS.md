# Pitfalls Research

**Domain:** Desktop audio transcription app — Python + Whisper + PyInstaller portable folder
**Researched:** 2026-03-28
**Confidence:** HIGH (verified against official PyInstaller docs, openai/whisper GitHub issues, PyTorch forums, keyring issue tracker)

---

## Critical Pitfalls

### Pitfall 1: Whisper Asset Files Not Bundled by PyInstaller

**What goes wrong:**
The app builds and runs in development but crashes immediately on a clean machine with errors like `'multilingual.tiktoken' not found` or a FileNotFoundError for `whisper/assets/`. PyInstaller does not auto-detect Whisper's non-Python asset files (mel filter banks, tiktoken vocabulary files).

**Why it happens:**
PyInstaller discovers Python imports but does not automatically collect data files sitting inside a package's directory. Whisper requires `whisper/assets/mel_filters.npz` and `whisper/assets/multilingual.tiktoken` at runtime. These are not Python modules and are skipped unless explicitly declared.

**How to avoid:**
In the `.spec` file, declare the assets as `datas`:
```python
datas=[
    ('path/to/site-packages/whisper/assets', 'whisper/assets'),
]
```
Also add `--collect-data whisper` or use `collect_data_files('whisper')` in the spec. Test on a machine with no Python installation before considering any phase "done."

**Warning signs:**
- Build succeeds but app crashes at first transcription attempt
- Error messages mention `.tiktoken` or `mel_filters`
- App works in dev but fails on a colleague's machine

**Phase to address:**
Packaging phase — must be verified as part of the first packaging milestone, not discovered at the end.

---

### Pitfall 2: tiktoken Hidden Import Missing

**What goes wrong:**
Whisper uses tiktoken for tokenization. PyInstaller cannot statically detect the `tiktoken_ext.openai_public` import because tiktoken loads its backend dynamically. The frozen app crashes with `ImportError: No module named 'tiktoken_ext'` or a `KeyError` during tokenizer initialization.

**Why it happens:**
tiktoken uses a plugin-style registration system for its encoding backends. The actual encoder module is loaded via a `pkg_resources` entry point, which PyInstaller cannot follow statically. This is a known upstream issue — tiktoken does not ship a PyInstaller hook as of 2025.

**How to avoid:**
Add to the PyInstaller spec or command:
```
--hidden-import tiktoken_ext.openai_public
--hidden-import tiktoken_ext
```
Confirm the fix by running the frozen binary and attempting a transcription before shipping.

**Warning signs:**
- Transcription works in `python main.py` but fails in the built `.exe` / `.app`
- Stack trace shows `tiktoken` in the call chain before the crash
- No `tiktoken_ext` folder visible in the `_internal/` output directory

**Phase to address:**
Packaging phase — add to spec file as part of initial packaging setup, not as a hotfix later.

---

### Pitfall 3: multiprocessing.freeze_support() Omitted

**What goes wrong:**
On Windows, the frozen app spawns infinite child processes and locks up or crashes immediately after launch. On macOS, it may silently fail to transcribe. There is no obvious error message — the window just freezes or the system slows to a crawl.

**Why it happens:**
PyInstaller's `onedir` builds on Windows use the `spawn` multiprocessing start method. When `multiprocessing.freeze_support()` is not called before any multiprocessing code runs, each child process re-executes the entire entry point, which spawns more children, causing an exponential fork bomb.

**How to avoid:**
Place this at the very top of `main.py`, before any GUI or threading code:
```python
import multiprocessing
if __name__ == '__main__':
    multiprocessing.freeze_support()
```
This is required even if you do not directly use `multiprocessing` — PyTorch and Whisper may use it internally.

**Warning signs:**
- Task Manager (Windows) shows dozens of `whisperai.exe` processes
- App freezes immediately on launch, before the window fully renders
- CPU spikes to 100% at startup

**Phase to address:**
Core transcription phase — add `freeze_support()` the moment any threading or parallel processing is introduced.

---

### Pitfall 4: Tkinter Widget Updates from Worker Threads

**What goes wrong:**
The transcription worker thread calls `label.config(text=...)` or `progress_bar.step()` directly. The app crashes intermittently with cryptic Tcl/Tk errors, or silently corrupts the UI state. Crashes are non-deterministic and hard to reproduce.

**Why it happens:**
Tkinter is not thread-safe. The Tcl/Tk runtime underneath Tkinter assumes all widget operations happen on the main thread. Calling any widget method from a background thread is undefined behavior — it may work sometimes, crash other times, depending on OS scheduler timing.

**How to avoid:**
Use `queue.Queue` to pass status updates from worker threads to the main thread. The main thread polls the queue with `root.after(100, poll_queue)`. Never call any Tkinter widget method from a non-main thread. Log messages, progress updates, and completion signals must all go through the queue.

**Warning signs:**
- Occasional `TclError: out of stack space` or `RuntimeError: main thread is not in main loop`
- App runs fine during light testing but crashes under load or on slower machines
- Crash happens only when transcribing multiple files in parallel

**Phase to address:**
Core transcription phase — the threading architecture must be designed correctly from the start; retrofitting it is expensive.

---

### Pitfall 5: CUDA DLL Resolution Fails on End-User Windows Machines

**What goes wrong:**
The app ships with PyTorch CUDA support. On the developer's machine, CUDA transcription works. On a user's machine with a different CUDA version (or no CUDA toolkit installed, only drivers), the app crashes with `cublas64_12.dll is not found` or falls back silently to CPU without informing the user.

**Why it happens:**
PyTorch bundles some CUDA libraries but not all. When the user's system CUDA version mismatches the PyTorch-expected version, specific DLLs like `cublas64_11.dll` or `cublas64_12.dll` cannot load. PyInstaller may also break DLL resolution by modifying `PATH` inside the frozen environment.

**How to avoid:**
- Build with `torch+cpu` for the default portable distribution; document a separate CUDA-enabled build as optional
- OR: wrap `torch.cuda.is_available()` in a try/except and always have a CPU fallback that is explicitly logged to the user: "GPU not available, using CPU"
- Test the frozen build on a clean Windows VM with only display drivers, no CUDA toolkit

**Warning signs:**
- `torch.cuda.is_available()` returns `True` in dev but the frozen app falls back to CPU silently
- Users report much slower-than-expected transcription speed
- Error logs show `OSError` when loading torch DLLs

**Phase to address:**
GPU detection phase and packaging phase — the fallback logic must be robust before packaging, and packaging must be tested on a clean system.

---

### Pitfall 6: MPS Backend Missing Required Operators on macOS

**What goes wrong:**
On Apple Silicon Macs, `torch.backends.mps.is_available()` returns `True`, so the app sets `device="mps"`. Whisper then crashes with `NotImplementedError: The operator 'aten::repeat_interleave.self_int' is not currently implemented for the MPS device`.

**Why it happens:**
PyTorch's MPS backend (Metal Performance Shaders) does not implement the full set of operators that `openai-whisper` requires. The availability check returns `True` but the actual model operations fail. This affects openai-whisper's standard `transcribe()` path specifically.

**How to avoid:**
Do not treat `mps.is_available()` as sufficient. Add a runtime probe: attempt to run a tiny tensor operation through the MPS device before committing. Safer approach: use MPS only if `torch.backends.mps.is_built()` is True AND your Whisper version is confirmed compatible. Provide CPU fallback with user-visible notification. Monitor the openai/whisper repo for MPS operator coverage updates.

**Warning signs:**
- macOS build crashes during transcription with `NotImplementedError`
- Error message mentions `aten::` operator names
- MPS path works in testing with small models but fails with medium

**Phase to address:**
GPU detection phase — the MPS probe logic must be implemented and tested on Apple Silicon hardware before any macOS distribution.

---

### Pitfall 7: Bundled ffmpeg Not Found at Runtime

**What goes wrong:**
The app cannot decode `.m4a` or `.ogg` files because it cannot find the bundled `ffmpeg` binary. Either Whisper falls back to a system `ffmpeg` (which may not be installed), or it throws `FileNotFoundError`.

**Why it happens:**
Whisper calls ffmpeg as a subprocess. The ffmpeg binary must be on `PATH` or its absolute path must be passed explicitly. In a frozen PyInstaller app, the binary is inside `_internal/` (or `sys._MEIPASS`), which is not on `PATH`. Additionally, on macOS, launching from Finder strips `PATH` down to `/usr/bin:/bin:/usr/sbin:/sbin`.

**How to avoid:**
At app startup, prepend `sys._MEIPASS` to `os.environ['PATH']` so subprocess calls find the bundled ffmpeg. Also set the `FFMPEG_BINARY` environment variable explicitly to `os.path.join(sys._MEIPASS, 'ffmpeg')` (or `ffmpeg.exe` on Windows). On macOS, also clear `DYLD_LIBRARY_PATH` before subprocess calls to avoid library conflicts.

**Warning signs:**
- `.mp3` files transcribe fine (Whisper has a fallback for some formats) but `.m4a` and `.ogg` fail
- Error mentions ffmpeg or `AudioSegment` or `subprocess`
- Works from terminal but fails when launched as double-click app on macOS

**Phase to address:**
Packaging phase — ffmpeg path resolution must be part of the spec file and startup bootstrap code.

---

### Pitfall 8: keyring Fails in PyInstaller Frozen App

**What goes wrong:**
The app uses `keyring` to store the Anthropic API key. In development, it works correctly. In the frozen app, `keyring.set_password()` raises `keyring.errors.NoKeyringError: No recommended backend was available` on Windows, or on macOS raises a codesign authentication error.

**Why it happens:**
`keyring` discovers its OS-native backend via `importlib.metadata` entry points. PyInstaller does not collect these entry points automatically, so the backend discovery fails in the frozen app. On macOS, unsigned binaries cannot access the Keychain without entitlements.

**How to avoid:**
Add to the spec file:
```python
--hidden-import keyring.backends.Windows
--hidden-import keyring.backends.macOS
--collect-all keyring
```
On macOS, the distributed `.app` must be codesigned with the `keychain-access-groups` entitlement. Test keyring on a clean machine where the app has never been run before. Provide a fallback that prompts the user to re-enter the key if keyring fails, rather than crashing.

**Warning signs:**
- API key prompt appears every launch instead of once
- `NoKeyringError` in the log on Windows
- macOS shows a security dialog on first key access, which is expected — but if it never appears, keyring may be silently failing

**Phase to address:**
API key management phase — must be tested in the frozen build context, not just in Python development mode.

---

### Pitfall 9: Whisper Hallucinations on Silence and Low-Speech Segments

**What goes wrong:**
Whisper produces fabricated text like "Subtitles by..." or "Thank you for watching" or repeats the same phrase many times when processing audio with long silences, background music, or low-speech density. Czech language recordings with pauses between speakers are particularly susceptible.

**Why it happens:**
Whisper was trained on subtitles data that contained end-of-video boilerplate. When it encounters audio that resembles "end of content" (silence, ambient noise), it hallucinates subtitle-style text from training data. This is a known upstream bug in openai-whisper, not fixed as of 2025.

**How to avoid:**
- Apply VAD (Voice Activity Detection) preprocessing — use `silero-vad` or `webrtcvad` to strip silent segments before passing audio to Whisper
- Pass `condition_on_previous_text=False` to reduce hallucination propagation between chunks
- Post-process: detect and remove repeated phrases with a deduplication pass
- Log a warning when the hallucination pattern "Titulky" / "Přepsal" / "subtitles by" appears in the Czech output

**Warning signs:**
- Short audio files (under 10 seconds) of silence produce multiple lines of output
- Long recordings contain identical paragraphs repeated verbatim
- Czech output contains English phrases like "subtitles by" or "thanks for watching"

**Phase to address:**
Core transcription phase — VAD preprocessing and hallucination post-processing should be designed in, not added as a hotfix after users report garbled transcripts.

---

### Pitfall 10: Model Load Path Hardcoded — Breaks on Distribution

**What goes wrong:**
The bundled Whisper medium model (`.pt` file, ~1.5 GB) is loaded from a hardcoded path like `./models/medium.pt` or a developer's absolute path. On any other machine, model loading fails with `FileNotFoundError`.

**Why it happens:**
Developers test with a local path that works in their environment. The PyInstaller bundle places files at `sys._MEIPASS` + relative path, which is a temp directory (for `onefile`) or the `_internal/` folder (for `onedir`). A hardcoded relative path resolves against the working directory, not the bundle.

**How to avoid:**
Always resolve resource paths relative to `sys._MEIPASS`:
```python
def get_resource_path(relative_path):
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)

MODEL_PATH = get_resource_path('models/medium.pt')
```
Apply this pattern to every bundled file: model, ffmpeg, assets.

**Warning signs:**
- Transcription fails immediately on any machine other than the build machine
- Error message contains an absolute path that includes the developer's username or home directory
- Works in `python main.py` from the project root but fails when run from a different directory

**Phase to address:**
Packaging phase — establish the `get_resource_path()` helper in the earliest packaging milestone and use it everywhere.

---

### Pitfall 11: macOS Gatekeeper Blocks Unsigned Distribution

**What goes wrong:**
macOS users double-click the app and see "whisperai is damaged and can't be opened" or "developer cannot be verified." Many users do not know how to bypass this and assume the app is broken.

**Why it happens:**
macOS Gatekeeper blocks any executable not signed with an Apple Developer ID. Since macOS 10.14.5, apps must also be notarized (submitted to Apple for malware scanning) to run without user override. Unsigned PyInstaller bundles trigger this by default.

**How to avoid:**
For internal distribution (small team): document the right-click → Open workaround. Users can right-click the app and choose "Open" to bypass Gatekeeper once. For wider distribution: obtain an Apple Developer ID ($99/year), sign the app with `codesign`, and notarize with `notarytool`. The `.app` must be signed with hardened runtime + `com.apple.security.cs.allow-unsigned-executable-memory` entitlement (required by Python/PyInstaller).

**Warning signs:**
- "App is from an unidentified developer" dialog on first launch
- "Damaged and can't be opened" (common when downloaded via browser without proper quarantine attributes)
- App works when launched from Terminal but not from Finder

**Phase to address:**
Distribution/packaging phase — decide early whether to target small-team sharing (right-click workaround acceptable) or public distribution (code signing required). The answer changes the effort by 2-3 days of work.

---

## Technical Debt Patterns

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip VAD preprocessing, rely on Whisper alone | Faster to implement | Hallucinations on real recordings, user-reported "garbage output" | Never — add VAD in core transcription phase |
| Update Tkinter widgets directly from worker thread | Simpler code | Non-deterministic crashes, hard to debug | Never — queue pattern from day one |
| Hardcode model path as relative `./models/` | Works in dev | Breaks in every packaged build | Never — use `get_resource_path()` from day one |
| Use `torch.cuda.is_available()` without fallback error handling | Less code | Silent CPU fallback confuses users who expect GPU speed | Only in internal dev builds |
| Skip codesigning for macOS | Saves $99/year | Significant user friction for any user outside the immediate team | Acceptable for small-team internal use only |
| Bundle full PyTorch CUDA (3+ GB) for all users | Single build | Massive distribution size for CPU-only users | Acceptable if distribution is targeted (users known to have CUDA) |

---

## Integration Gotchas

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| openai-whisper | Calling `whisper.transcribe()` on main thread | Run transcription in a `threading.Thread`, post updates via `queue.Queue` |
| openai-whisper | Assuming model loads instantly | Model deserialization from disk takes 5-15s; show a loading state in the UI |
| PyTorch + CUDA | Building with CUDA torch on macOS | macOS does not support CUDA; build with CPU torch on Mac, CUDA torch on Windows |
| ffmpeg subprocess | Letting ffmpeg inherit the frozen app's `DYLD_LIBRARY_PATH` on macOS | Strip `DYLD_LIBRARY_PATH` before subprocess.run() on macOS to avoid library conflicts |
| keyring | Assuming the backend is always available | Wrap all keyring calls in try/except; show a "enter API key" dialog as fallback |
| Anthropic API | No retry logic for 429/529 errors | Implement exponential backoff; the SDK retries 2x by default but long audio sessions may exhaust rate limits |
| Anthropic API | Sending entire 30-min transcript in one call | Claude API has input token limits and cost implications; chunk or summarize long transcripts |

---

## Performance Traps

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| Loading Whisper model for every file in a batch | 5-15s overhead per file, batch of 10 files takes 10x longer than expected | Load model once at app startup or first use, reuse across files | Any batch of more than 1 file |
| Parallel Whisper instances sharing one GPU | OOM errors, CUDA out of memory crashes, slower than sequential | Limit GPU workers to 1; CPU workers can parallelize safely | Second parallel GPU transcription |
| Reading entire audio file into memory before processing | Memory error on files > 1 hour | Let Whisper process via file path, not in-memory bytes | Audio files over ~500MB |
| Writing transcripts synchronously on main thread | UI freezes at "saving" step for large outputs | Write output files in the worker thread or a separate I/O thread | Files larger than ~5MB |
| Queue polling with too-short interval (`root.after(10, ...)`) | High CPU usage even when idle | Use 100-250ms polling interval for progress updates | At sustained polling; measurable on low-end machines |

---

## Security Mistakes

| Mistake | Risk | Prevention |
|---------|------|------------|
| Storing Anthropic API key in a plain `.env` or `.json` file next to the executable | Key leaks if the portable folder is shared or uploaded | Use OS keyring exclusively; never write the key to any file |
| Logging the API key in the detailed processing log | Key visible in saved log files | Mask any string matching the `sk-ant-` prefix in log output |
| Passing API key via command-line argument or environment variable without clearing it | Key visible in process list | Pass key only in-process; never via `subprocess` env vars |
| No validation on API key format before storing | Silent failures, confusing UX | Validate that key starts with `sk-ant-api` before accepting it |

---

## UX Pitfalls

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| No progress indicator during model load (5-15s blank window) | User assumes app crashed, force-quits it | Show "Načítám model..." spinner immediately on startup before model loads |
| Showing raw file paths in error messages | Czech non-technical users cannot parse English path errors | Translate error messages to Czech, show friendly "Soubor nenalezen" instead of a stack trace |
| Silent GPU fallback to CPU | Users with powerful GPUs wait 10x longer, do not know why | Always log the device being used: "Používám GPU (CUDA)" or "Používám CPU (bez GPU)" |
| No confirmation before overwriting existing transcript files | Users lose previous work | Check if `_prepis.txt` exists before writing; ask "Přepsat existující soubor?" |
| Progress bar that jumps from 0% to 100% with no intermediate updates | Looks like it froze at 0% | Use Whisper's segment-level callbacks to update progress incrementally |
| Crashing without a user-visible error on model load failure | User sees a flash and nothing | Catch all exceptions at the top level; show a dialog with a Czech error message and offer to send a log |

---

## "Looks Done But Isn't" Checklist

- [ ] **PyInstaller build:** Test on a clean machine with no Python, no CUDA toolkit, no ffmpeg installed — not just on the dev machine
- [ ] **GPU detection:** Verify that CPU fallback works and is logged visibly when CUDA/MPS is unavailable
- [ ] **MPS on macOS:** Test actual transcription on Apple Silicon — `mps.is_available()` is not sufficient
- [ ] **ffmpeg bundling:** Verify `.m4a` and `.ogg` files decode correctly in the frozen build
- [ ] **keyring in frozen build:** Uninstall and reinstall the app, verify API key persists across runs
- [ ] **Whisper assets:** Run transcription in the frozen build on a machine that has never had openai-whisper pip-installed
- [ ] **Hallucination handling:** Test with a 30-second silent audio file — Whisper should produce no output or a meaningful warning, not fabricated text
- [ ] **Parallel transcription:** Run 3+ files in parallel, verify no CUDA OOM errors and UI remains responsive
- [ ] **Long file (60+ min):** Transcribe a 60-minute Czech recording, verify transcript is complete and no progress bar deadlocks
- [ ] **macOS Gatekeeper:** Download the app from a URL on a fresh Mac, confirm the user can actually open it

---

## Recovery Strategies

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Whisper assets not bundled | LOW | Add `collect_data_files('whisper')` to spec, rebuild |
| tiktoken hidden import missing | LOW | Add `--hidden-import tiktoken_ext.openai_public`, rebuild |
| freeze_support() omitted | LOW | Add 2 lines to `main.py`, rebuild |
| Tkinter threading wrong from start | HIGH | Refactor worker/queue architecture — touches all transcription code |
| Model path hardcoded throughout codebase | MEDIUM | Search-replace with `get_resource_path()` helper — tedious but mechanical |
| MPS operator failure found late | MEDIUM | Add CPU fallback guard — straightforward but requires macOS hardware to test |
| keyring broken in distribution | MEDIUM | Add fallback UI prompt; may require codesigning for macOS to fully fix |
| Hallucinations discovered by real users | MEDIUM | Add VAD preprocessing and post-processing deduplication pass |

---

## Pitfall-to-Phase Mapping

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Whisper assets not bundled | Packaging | Run frozen build on clean VM, attempt transcription |
| tiktoken hidden import | Packaging | Check `_internal/` folder for `tiktoken_ext` directory |
| freeze_support() missing | Core transcription | Launch frozen build on Windows, check Task Manager for process count |
| Tkinter thread safety | Core transcription | Run 3 parallel files, verify no TclError in logs |
| CUDA DLL resolution | GPU detection + Packaging | Test on Windows machine with GPU drivers only, no CUDA toolkit |
| MPS operator missing | GPU detection | Run transcription on Apple Silicon Mac (not just check `is_available()`) |
| ffmpeg not found at runtime | Packaging | Test `.m4a` decode in frozen build on clean machine |
| keyring frozen app failure | API key management | Install fresh build, enter key, quit, relaunch, verify key persisted |
| Whisper hallucinations | Core transcription | Test with silent audio and sparse-speech audio files |
| Hardcoded model path | Packaging | Run frozen build from a different working directory |
| macOS Gatekeeper | Distribution | Download app on a Mac that has never run the app, double-click from Finder |

---

## Sources

- [openai/whisper PyInstaller discussion #1479](https://github.com/openai/whisper/discussions/1479) — assets bundling, multiprocessing, tiktoken issues
- [openai/tiktoken issue #43](https://github.com/openai/tiktoken/issues/43) — PyInstaller hidden import for tiktoken_ext
- [openai/tiktoken issue #469](https://github.com/openai/tiktoken/issues/469) — upstream hook request, still unresolved
- [pyinstaller/pyinstaller common issues docs](https://pyinstaller.org/en/stable/common-issues-and-pitfalls.html) — freeze_support, DYLD_LIBRARY_PATH, macOS PATH
- [jaraco/keyring issue #439](https://github.com/jaraco/keyring/issues/439) — Windows Credential Manager in frozen app
- [jaraco/keyring issue #629](https://github.com/jaraco/keyring/issues/629) — macOS Keychain codesign requirement
- [openai/whisper discussion #679](https://github.com/openai/whisper/discussions/679) — hallucination on silence
- [openai/whisper discussion #1606](https://github.com/openai/whisper/discussions/1606) — hallucination on no-speech audio
- [openai/whisper discussion #1771](https://github.com/openai/whisper/discussions/1771) — CUDA errors running multiple Whisper instances in parallel
- [openai/whisper PR #382](https://github.com/openai/whisper/pull/382) — MPS support added (but incomplete operator coverage)
- [pyinstaller/pyinstaller issue #9222](https://github.com/pyinstaller/pyinstaller/issues/9222) — torch import crashes in frozen app
- [faster-whisper issue #535](https://github.com/SYSTRAN/faster-whisper/issues/535) — cublas64 DLL not found
- [pyinstaller macOS code signing gist](https://gist.github.com/txoof/0636835d3cc65245c6288b2374799c43) — codesign + notarization workflow
- [PyInstaller macOS .app bundle DYLD_LIBRARY_PATH](https://github.com/orgs/pyinstaller/discussions/8089) — ffmpeg subprocess library conflict
- [Anthropic rate limits docs](https://platform.claude.com/docs/en/api/rate-limits) — 429/529 handling, retry-after header

---
*Pitfalls research for: desktop audio transcription — Python + Whisper + PyInstaller*
*Researched: 2026-03-28*

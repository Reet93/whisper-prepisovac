<!-- GSD:project-start source:PROJECT.md -->
## Project

**Whisper Přepisovač**

A cross-platform desktop application for transcribing audio recordings to text using OpenAI Whisper, with optional AI-powered text cleanup via the Anthropic Claude API. Built for a small team with the intent to share with a wider audience. Runs locally on Windows and macOS without requiring Python installation.

**Core Value:** Reliable, one-click transcription of long Czech audio recordings into clean, structured text — no cloud dependency for the core transcription.

### Constraints

- **Tech stack**: Python + Tkinter for GUI, openai-whisper for transcription, anthropic SDK for Claude API
- **Packaging**: PyInstaller portable folder — must run without Python installed
- **Dependencies**: ffmpeg and Whisper model bundled, not downloaded at runtime
- **Security**: API keys stored in OS-native secure storage, never in plaintext files
- **Platform**: Must work on both Windows 10/11 and macOS (Intel + Apple Silicon)
<!-- GSD:project-end -->

<!-- GSD:stack-start source:research/STACK.md -->
## Technology Stack

## Recommended Stack
### Core Technologies
| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12.x | Runtime | Best sweet spot for this stack: openai-whisper 20250625 supports it, PyTorch 2.11 supports it, PyInstaller 6.19 supports it. Avoid 3.13 — openai-whisper has known incompatibilities. Avoid 3.10.0 — has a PyInstaller-specific bug. |
| openai-whisper | 20250625 | Audio transcription | The reference implementation. Project constraint mandates it. Medium model gives best Czech accuracy at ~1.5 GB. Uses PyTorch under the hood — CUDA and MPS both work natively via `torch.device`. |
| PyTorch | 2.11.0 | Tensor computation + GPU backend | Required by openai-whisper. Provides `torch.cuda.is_available()` for CUDA detection and `torch.backends.mps.is_available()` for Apple Silicon detection. Install the CUDA-enabled wheel on Windows, the standard wheel on macOS (MPS is bundled since PyTorch 2.0). |
| anthropic | 0.86.0 | Claude API client | Official Anthropic Python SDK. Requires Python >=3.9. Used for the "Přepsat + Upravit" cleanup path only — app must work without it. |
| Tkinter + ttk | stdlib (Python 3.12) | GUI framework | Project constraint. Ships with Python, zero extra dependency, works identically on Windows and macOS. Use `tkinter.ttk` widgets (not bare `tkinter`) for native-feeling controls. |
| ttkbootstrap | 1.20.2 | Modern Tkinter theming | Adds a flat, Bootstrap-inspired skin over ttk. Active maintenance (released March 2026). Provides a `ScrolledText`-equivalent, `Meter` progress widget, and 20+ themes. Eliminates the "grey box" look of stock ttk on Windows without platform-specific hacks. |
| PyInstaller | 6.19.0 | Portable folder packaging | Project constraint. Latest stable (Feb 2026). Produces a `--onedir` distribution (portable folder) rather than a single EXE — correct choice for this project given large Whisper model and CUDA binaries. Works on Python 3.12 and supports both Windows and macOS targets. |
| keyring | 25.7.0 | OS-native secure credential storage | Uses Windows Credential Manager on Windows and macOS Keychain on macOS automatically via a single `keyring.set_password()` / `keyring.get_password()` API. Requires Python >=3.9. Production/Stable, released Nov 2025. |
### Supporting Libraries
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Python `gettext` | stdlib | i18n string translation | Always — it is the standard Python i18n mechanism. Mark all user-visible strings with `_()`, generate `.po` files with `pybabel extract`, compile to binary `.mo` files. Bundle the `locale/` directory with PyInstaller `--add-data`. |
| `Babel` | 2.x (latest) | `.po` file extraction and compilation | Development-time tool only (not bundled). Used as `pybabel extract` / `pybabel compile` to produce `.mo` catalogs from source. Not needed at runtime. |
| Python `concurrent.futures` | stdlib | Parallel file processing | Always — for the configurable 1-N parallel transcription. Use `ProcessPoolExecutor` (not `ThreadPoolExecutor`) because Whisper is CPU/GPU bound, not I/O bound. Each worker process loads the model independently; the GIL is not a factor. |
| Python `threading` | stdlib | Non-blocking UI during transcription | Always — run `ProcessPoolExecutor` dispatch in a background thread so the Tkinter event loop never blocks. Pattern: `threading.Thread(target=run_batch, daemon=True).start()`. |
| Python `queue` | stdlib | Thread-to-UI progress communication | Always — the safe way to send log lines from worker threads to the Tkinter main thread. Poll with `root.after(100, drain_queue)`. |
| `ffmpeg` static binary | 7.x (bundled) | Audio decoding (mp3, m4a, ogg) | Always — Whisper calls `ffmpeg` as a subprocess. Bundle the platform-specific static binary (`ffmpeg.exe` on Windows, `ffmpeg` on macOS) in the PyInstaller dist folder and point `PATH` at it via a startup hook. Download from https://github.com/BtbN/FFmpeg-Builds (Windows) and https://evermeet.cx/ffmpeg/ (macOS). |
| Python `pathlib` | stdlib | Cross-platform file path handling | Always — use `pathlib.Path` throughout instead of `os.path`. Handles Windows/macOS path separators correctly and integrates cleanly with `tkinter.filedialog`. |
| Python `logging` | stdlib | Structured log output | Always — pipe Whisper progress and Claude API calls through the standard logger; attach a `QueueHandler` to push log records into the UI queue. |
### Development Tools
| Tool | Purpose | Notes |
|------|---------|-------|
| `pyenv` (macOS) / `pyenv-win` (Windows) | Manage Python 3.12.x | Keep build Python isolated from system Python. Critical: build on the same OS you target — PyInstaller does not cross-compile. |
| `pip-tools` | Lock exact dependency versions | `pip-compile requirements.in` → `requirements.txt`. Ensures reproducible builds on both platforms. |
| `pybabel` (from Babel) | Extract and compile i18n catalogs | `pybabel extract -F babel.cfg -o locale/messages.pot .` then compile per locale. |
| PyInstaller `.spec` file | Fine-grained packaging control | Required — command-line flags are insufficient for this project. Must declare `datas` for the Whisper model directory, `binaries` for ffmpeg, `hidden_imports` for torch and whisper internals, and `multiprocessing.freeze_support()` in `main()`. |
## Installation
# Core runtime (Python 3.12 recommended)
# Dev / build tools (not bundled in dist)
# No additional audio library needed — Whisper uses ffmpeg directly via subprocess
## Alternatives Considered
| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| `openai-whisper` | `faster-whisper` (CTranslate2 backend) | If you need 2-4x faster inference and lower RAM usage. faster-whisper bundles its own ffmpeg via PyAV, simplifying packaging. Trade-off: different model format (CTranslate2), adds a C++ extension dependency. Not applicable here — project mandates openai-whisper. |
| `ttkbootstrap` | Bare `tkinter.ttk` | If you want zero extra dependencies and accept the default OS look. Works fine; just less polished. |
| `ttkbootstrap` | `CustomTkinter` | CustomTkinter provides more modern flat widgets and is popular, but ttkbootstrap stays compatible with all standard ttk widgets and has wider adoption as of 2026. |
| `gettext` (stdlib) | `babel`-only runtime | Babel is large; for runtime use, the stdlib `gettext` module is sufficient. Use Babel only for extraction/compilation during development. |
| `ProcessPoolExecutor` | `ThreadPoolExecutor` | Use `ThreadPoolExecutor` only for I/O-bound parallelism. Whisper is CPU/GPU bound — processes bypass the GIL. |
| Static ffmpeg binary | `ffmpeg-python` wrapper lib | `ffmpeg-python` is a Python API over ffmpeg but still requires the binary. Using the binary directly avoids one abstraction layer and is simpler for PyInstaller packaging. |
| `keyring` | `cryptography` + custom store | Implementing your own encryption on top of a plaintext file is error-prone. `keyring` delegates to the OS — no custom crypto needed. |
## What NOT to Use
| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Python 3.13 | openai-whisper 20250625 has known incompatibilities with 3.13. | Python 3.12.x |
| Python 3.10.0 | Contains a bug that makes it incompatible with PyInstaller 6.x. | Python 3.12.x |
| PyInstaller `--onefile` mode | Single-EXE mode extracts everything to a temp folder on each launch. With a ~1.5 GB Whisper model bundled, startup time would be unacceptably slow and temp extraction would be enormous. | PyInstaller `--onedir` (portable folder) |
| `multiprocessing.Pool` directly | Requires `if __name__ == "__main__"` guard AND `freeze_support()` call. `concurrent.futures.ProcessPoolExecutor` handles this more cleanly with PyInstaller when `freeze_support()` is placed in `main()`. | `concurrent.futures.ProcessPoolExecutor` |
| `whisper.load_model()` with default model path | By default, Whisper downloads models to `~/.cache/whisper/`. In a bundled app, the model is embedded in the dist folder. You must override the download dir or pass the pre-downloaded model directory explicitly at launch. | Pass `download_root=bundled_model_path` to `whisper.load_model()` |
| Storing the Claude API key in a config file or `.env` | Plaintext secrets on disk are a security liability, especially for a distributed app. | `keyring.set_password()` / `keyring.get_password()` |
| `wx`, `PyQt`, `PySide6` as GUI framework | Project constraint mandates Tkinter. These are valid alternatives for new greenfield apps but would conflict with the given constraint. | Tkinter + ttkbootstrap |
## Stack Patterns by Variant
- Pre-download the model to a local directory during development: `whisper.load_model("medium", download_root="./models")`
- In the `.spec` file: `datas=[("./models", "models")]`
- At runtime: resolve the bundled path via `sys._MEIPASS` when frozen, or the repo root when running from source.
- Place platform-specific static ffmpeg binaries in `./bin/` in the repo.
- In the `.spec` file: `binaries=[("./bin/ffmpeg.exe", ".")]` (Windows) or `binaries=[("./bin/ffmpeg", ".")]` (macOS).
- At app startup, prepend the bundle directory to `PATH` so Whisper's subprocess call finds it: `os.environ["PATH"] = sys._MEIPASS + os.pathsep + os.environ["PATH"]` when frozen.
## Version Compatibility
| Package | Compatible With | Notes |
|---------|-----------------|-------|
| `openai-whisper==20250625` | `torch>=2.0`, Python 3.9-3.12 | Avoid Python 3.13. Requires ffmpeg binary on PATH. |
| `torch==2.11.0` | Python 3.10+ | Install CUDA-enabled wheel on Windows (`+cu124` suffix from pytorch.org). macOS wheel includes MPS support — no separate install. |
| `anthropic==0.86.0` | Python >=3.9 | No torch dependency; safe to add without conflicts. |
| `ttkbootstrap==1.20.2` | Python 3.8+, Tkinter (stdlib) | No extra binary dependencies. |
| `keyring==25.7.0` | Python >=3.9 | On Windows, uses `pywin32` for Credential Manager access — ensure `pywin32` is installed or bundled. |
| `PyInstaller==6.19.0` | Python 3.8-3.14 (not 3.10.0) | Torch packaging requires `--copy-metadata torch` and increased recursion limit in `.spec`. Use `collect_submodules("whisper")` for whisper hidden imports. |
## Sources
- [openai-whisper on PyPI](https://pypi.org/project/openai-whisper/) — version 20250625, Python support (HIGH confidence)
- [anthropic on PyPI](https://pypi.org/project/anthropic/) — version 0.86.0, March 2026 (HIGH confidence)
- [PyInstaller on PyPI](https://pypi.org/project/pyinstaller/) — version 6.19.0, Feb 2026 (HIGH confidence)
- [PyInstaller docs 6.19.0](https://pyinstaller.org/en/stable/index.html) — packaging patterns, spec file options (HIGH confidence)
- [keyring on PyPI](https://pypi.org/project/keyring/) — version 25.7.0, Nov 2025 (HIGH confidence)
- [ttkbootstrap on PyPI](https://pypi.org/project/ttkbootstrap/) — version 1.20.2, March 2026 (HIGH confidence)
- [torch on PyPI](https://pypi.org/project/torch/) — version 2.11.0, March 2026 (HIGH confidence)
- [PyTorch MPS backend docs](https://docs.pytorch.org/docs/stable/mps.html) — MPS availability check API (HIGH confidence)
- [How do I package whisper with PyInstaller — openai/whisper Discussion #1479](https://github.com/openai/whisper/discussions/1479) — hidden import patterns, freeze_support (MEDIUM confidence — community discussion)
- [PyInstaller + PyTorch discussion](https://github.com/orgs/pyinstaller/discussions/7621) — torch metadata and recursion limit workarounds (MEDIUM confidence)
- [Python gettext docs](https://docs.python.org/3/library/gettext.html) — stdlib i18n API (HIGH confidence)
<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->
## Conventions

Conventions not yet established. Will populate as patterns emerge during development.
<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->
## Architecture

Architecture not yet mapped. Follow existing patterns found in the codebase.
<!-- GSD:architecture-end -->

<!-- GSD:workflow-start source:GSD defaults -->
## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd:quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd:debug` for investigation and bug fixing
- `/gsd:execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->



<!-- GSD:profile-start -->
## Developer Profile

> Profile not yet configured. Run `/gsd:profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->

# Phase 4: Packaging - Research

**Researched:** 2026-03-29
**Domain:** PyInstaller onedir packaging, faster-whisper + CTranslate2, model download, GitHub publication
**Confidence:** HIGH (stack verified against installed venv; pitfalls from official issue trackers)

## Summary

Phase 4 turns the working app into a distributable Windows portable folder, sets up GitHub publication, and implements first-launch model download. The app uses faster-whisper (CTranslate2 backend), silero-vad (ONNX/JIT), torch 2.11+cu126, keyring, ttkbootstrap, and platformdirs. No nvidia-* PyPI packages are used — all CUDA DLLs are embedded in `torch/lib/` and `ctranslate2/` directly, so PyInstaller will pick them up automatically via binary collection.

The single biggest non-obvious issue is model path in frozen context: `get_resource_path("models")` points to `sys._MEIPASS/models` inside the read-only `_internal/` directory. Since D-08 defers bundling and downloads the model on first launch, a separate `get_model_path()` function must be introduced that returns `platformdirs.user_data_dir(...)` when frozen and the dev models/ directory otherwise. The current `transcription_panel.py:1067` line must call this new function.

Keyring requires `--collect-all keyring` to correctly bundle the Windows Credential Manager backend (entry point discovery breaks without it). No ctranslate2-specific PyInstaller hook exists in pyinstaller-hooks-contrib — it must be handled manually with `collect_all` or explicit binary/data collection in the spec.

**Primary recommendation:** Write a single `whisperai.spec` with explicit `collect_all` for ctranslate2, keyring, huggingface_hub, silero_vad; `copy_metadata` for torch and faster_whisper; recursion limit 5000; and all datas entries. Pair with a `build.bat` that invokes the spec.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **D-01:** Create README.md with project description, features, and install/usage instructions
- **D-02:** MIT License
- **D-03:** Exclude `.planning/`, `.claude/`, `.vexp/`, `models/`, `.venv/`, `__pycache__/`, `dist/`, `build/` from Git — only source code published
- **D-04:** Security scan for hardcoded secrets/API keys before first push (automated grep for patterns like sk-ant-*, .env files, credentials)
- **D-05:** Windows-only build for this phase (macOS deferred — requires Mac hardware, PyInstaller doesn't cross-compile)
- **D-06:** Local manual build via script (build.bat or build.py) — no CI/CD pipeline
- **D-07:** Both GitHub Release (zip of portable folder for end users) and source repo (for developers)
- **D-08:** Whisper model NOT bundled in distribution — downloaded automatically on first launch with progress dialog ("Downloading Whisper model (~1.5 GB)... This only happens once.")
- **D-09:** README documents first-launch model download requirement and approximate time/size
- **D-10:** Remove unused `medium.pt` (openai-whisper format) from models/ — only faster-whisper model used
- **D-11:** ffmpeg/ffprobe latest stable Windows static build from BtbN/FFmpeg-Builds on GitHub — bundled in the portable folder
- **D-12:** CUDA libraries picked up automatically by PyInstaller from the torch installation

### Claude's Discretion
- PyInstaller spec file structure and hidden imports — whatever works for faster-whisper + torch + ttkbootstrap
- Build script implementation details
- ffmpeg exact version — latest stable at time of build
- Model download implementation (progress bar widget, retry logic, error handling)

### Deferred Ideas (OUT OF SCOPE)
- macOS build — requires Mac hardware, deferred until hardware available
- GitHub Actions CI/CD — overkill for current project size, add later if needed
- Auto-update mechanism — tracked as PLAT-V2-01 in requirements
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| PKG-01 | PyInstaller portable folder packaging for Windows (no Python required) | Spec file patterns, torch/ctranslate2 collection, CUDA DLL bundling |
| PKG-02 | PyInstaller portable folder packaging for macOS (no Python required) | DEFERRED per D-05; macOS not in this phase |
| PKG-03 | ffmpeg binary bundled with the app (not downloaded at runtime) | BtbN static builds, bin/ directory placement, PATH prepend at startup |
| PKG-04 | Whisper medium model bundled with the app (not downloaded at runtime) | SUPERSEDED by D-08: model is NOT bundled; downloaded on first launch via platformdirs path |
| PKG-05 | PyInstaller spec file with Whisper hidden imports, tiktoken fix, and freeze_support | Spec file structure documented; tiktoken not used (faster-whisper uses its own tokenizer) |
| PKG-06 | All bundled resources accessible via get_resource_path (sys._MEIPASS aware) | Existing get_resource_path() handles this; model needs separate get_model_path() for writable dir |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| PyInstaller | 6.19.0 | Portable folder packaging | Project constraint; current stable; Python 3.12 support confirmed |
| faster-whisper | 1.2.1 | Transcription backend being packaged | Already installed in venv; confirmed version |
| ctranslate2 | 4.7.1 | C++ inference engine under faster-whisper | Installed; has its own DLLs (ctranslate2.dll, cudnn64_9.dll, libiomp5md.dll) |
| torch | 2.11.0+cu126 | GPU computation; CUDA DLLs embedded in torch/lib/ | Already installed; all CUDA DLLs confirmed present in torch/lib/ |
| keyring | 25.7.0 | Windows Credential Manager | Requires collect_all to bundle entry-point-based backend |
| platformdirs | 4.9.4 | Writable user data directory for model download | Already in requirements.in; returns APPDATA path on Windows |
| huggingface_hub | 1.8.0 | Model download engine used by faster-whisper | Transitively installed; must be collected for PyInstaller |
| silero-vad | 6.2.1 | VAD model — ships .onnx and .jit data files | Data files in silero_vad/data/ must be bundled |
| onnxruntime | 1.24.4 | ONNX inference for silero-vad | Has its own DLLs in onnxruntime/capi/; must be collected |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pip-tools | latest | Lock requirements for reproducible builds | Use pip-compile to generate requirements.txt from requirements.in before packaging |
| ffmpeg static binary | 7.x (BtbN) | Audio decoding; bundled in bin/ | Download ffmpeg-master-latest-win64-gpl.zip; extract ffmpeg.exe + ffprobe.exe to bin/ |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| platformdirs user_data_dir | sys._MEIPASS/models for model storage | _MEIPASS/_internal is read-only; cannot use for downloaded files |
| get_resource_path("models") for frozen model path | model stored in _internal/ | _internal is read-only — breaks D-08 download requirement |

**Installation (PyInstaller into venv):**
```bash
.venv\Scripts\pip install pyinstaller==6.19.0
```

**Version verification:** PyInstaller not yet installed in venv (confirmed 2026-03-29). All other packages verified against venv pip list.

## Architecture Patterns

### Recommended Project Structure (additions for Phase 4)
```
whisperai/
├── bin/                          # NEW: ffmpeg binaries (gitignored after placement)
│   ├── ffmpeg.exe               # From BtbN/FFmpeg-Builds win64-gpl
│   └── ffprobe.exe
├── whisperai.spec               # NEW: PyInstaller spec file
├── build.bat                    # NEW: build script
├── .gitignore                   # NEW: before first push
├── README.md                    # NEW: project description
├── LICENSE                      # NEW: MIT license
├── requirements.in              # exists: dependency list
├── requirements.txt             # NEW: pinned by pip-compile
├── main.py                      # exists: entry point with freeze_support
├── src/whisperai/
│   └── utils/
│       ├── resource_path.py     # exists: sys._MEIPASS aware
│       └── model_path.py        # NEW: writable model dir for frozen context
└── models/                      # gitignored: dev model cache
    └── models--Systran--faster-whisper-medium/
        └── snapshots/hash/      # actual model files
```

### Pattern 1: PyInstaller Spec File Structure

**What:** A .spec file controls exactly what gets bundled. For this project, several packages with DLLs, data files, and entry-point plugins need explicit collection.

**Key spec file requirements:**

```python
# whisperai.spec
import sys
from PyInstaller.utils.hooks import collect_all, collect_data_files, copy_metadata

block_cipher = None

# ---- Collect packages that need full collection (submodules + data + binaries) ----
ctranslate2_datas, ctranslate2_binaries, ctranslate2_hiddenimports = collect_all('ctranslate2')
keyring_datas, keyring_binaries, keyring_hiddenimports = collect_all('keyring')
silero_vad_datas, silero_vad_binaries, silero_vad_hiddenimports = collect_all('silero_vad')
hf_hub_datas, hf_hub_binaries, hf_hub_hiddenimports = collect_all('huggingface_hub')
onnxruntime_datas, onnxruntime_binaries, onnxruntime_hiddenimports = collect_all('onnxruntime')

# ---- Metadata needed by runtime importlib.metadata checks ----
meta = (
    copy_metadata('torch') +
    copy_metadata('faster-whisper') +
    copy_metadata('ttkbootstrap') +
    copy_metadata('keyring') +
    copy_metadata('platformdirs')
)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=(
        [('bin/ffmpeg.exe', 'bin'), ('bin/ffprobe.exe', 'bin')]
        + ctranslate2_binaries
        + silero_vad_binaries
        + hf_hub_binaries
        + onnxruntime_binaries
        + keyring_binaries
    ),
    datas=(
        [
            ('locale', 'locale'),       # i18n .mo files
            ('prompts', 'prompts'),     # Claude prompt templates
        ]
        + ctranslate2_datas
        + silero_vad_datas
        + hf_hub_datas
        + onnxruntime_datas
        + keyring_datas
        + meta
    ),
    hiddenimports=(
        ['faster_whisper', 'faster_whisper.transcribe', 'faster_whisper.tokenizer',
         'faster_whisper.audio', 'faster_whisper.vad',
         'tokenizers',
         'win32timezone',               # pywin32-ctypes dependency for keyring
         'keyring.backends.Windows',
         'keyring.backends._win_crypto',
         'multiprocessing.managers',    # needed for ProcessPoolExecutor cross-process
        ]
        + ctranslate2_hiddenimports
        + keyring_hiddenimports
        + silero_vad_hiddenimports
        + hf_hub_hiddenimports
        + onnxruntime_hiddenimports
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['openai.whisper', 'whisper'],  # exclude openai-whisper if installed
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# Increase recursion limit — torch module graph is very deep
import sys
sys.setrecursionlimit(5000)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WhisperPrepis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,           # UPX can corrupt CUDA DLLs — leave off
    console=False,       # no console window for GUI app
    disable_windowed_traceback=False,
    icon=None,           # add .ico path if icon exists
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='WhisperPrepis',
)
```

**Note on recursion limit:** Must be set BEFORE `Analysis()` is called — place `sys.setrecursionlimit(5000)` at the top of the spec file, not inside Analysis.

### Pattern 2: Model Path for Frozen Context

**Problem:** D-08 requires model download on first launch. `get_resource_path("models")` in frozen context returns `sys._MEIPASS/models` which is inside the read-only `_internal/` folder. Downloads to this path will fail.

**Solution:** New `get_model_path()` function in a separate utility module:

```python
# src/whisperai/utils/model_path.py
import sys
from pathlib import Path
from platformdirs import user_data_dir


def get_model_path() -> Path:
    """Return writable directory for Whisper model storage.

    - Frozen (PyInstaller): %APPDATA%\Local\WhisperPrepis\WhisperPrepis\models
    - Development: project_root/models  (existing dev cache)
    """
    if getattr(sys, "frozen", False):
        return Path(user_data_dir("WhisperPrepis", "WhisperPrepis")) / "models"
    else:
        # Development: 4 parents up from utils/ = project root
        return Path(__file__).parent.parent.parent.parent / "models"
```

**Usage change in transcription_panel.py:1067:**
```python
# OLD:
model_path = str(get_resource_path("models"))
# NEW:
from src.whisperai.utils.model_path import get_model_path
model_path = str(get_model_path())
```

### Pattern 3: First-Launch Model Download Dialog

**What:** On first launch in frozen app, if model not present in `get_model_path()`, show a blocking dialog with progress before opening main window.

**Implementation approach:**

```python
# In main.py, after i18n init and before create_app():
from src.whisperai.utils.model_path import get_model_path
from pathlib import Path

def model_is_present() -> bool:
    """Check if faster-whisper medium model is already downloaded."""
    model_dir = get_model_path()
    # faster-whisper stores: models--Systran--faster-whisper-medium/snapshots/*/model.bin
    import glob
    pattern = str(model_dir / "models--Systran--faster-whisper-medium" / "snapshots" / "*" / "model.bin")
    return len(glob.glob(pattern)) > 0

if not model_is_present():
    show_download_dialog(get_model_path())
```

**Download engine:** `faster_whisper.WhisperModel("medium", download_root=str(model_dir))` triggers the download via huggingface_hub. For progress reporting, run download in a background thread and use `root.after()` to drain a queue into a Tkinter `ttk.Progressbar`.

**Simpler alternative (no custom progress):** Use `huggingface_hub.snapshot_download()` directly — it calls back via tqdm. Disable tqdm and use a simple "please wait" dialog. Given model is ~1.5 GB this takes 2-10 min on typical broadband; a determinate progress bar is worth implementing.

**huggingface_hub progress approach:** `snapshot_download()` does not have a clean callback API for per-file bytes. Use a thread + indeterminate progress bar + file size polling as a simpler alternative.

### Pattern 4: PATH Prepend for Bundled ffmpeg

**What:** `vad.py` and `transcription_panel.py` already call `get_resource_path("bin/ffmpeg.exe")`. The PATH prepend is a defense-in-depth measure for any subprocess calls that use bare `ffmpeg`.

**In main.py, before create_app():**
```python
import os, sys
if getattr(sys, "frozen", False):
    bin_dir = str(Path(sys._MEIPASS) / "bin")
    os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")
```

This is additive — existing `get_resource_path("bin/ffmpeg.exe")` checks still work.

### Pattern 5: build.bat Structure

```bat
@echo off
setlocal

REM Ensure we're using the venv
call .venv\Scripts\activate.bat

REM Confirm PyInstaller is available
pyinstaller --version || (echo PyInstaller not found in venv & exit /b 1)

REM Remove previous build artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Run PyInstaller
pyinstaller whisperai.spec

echo.
echo Build complete: dist\WhisperPrepis\
endlocal
```

### Anti-Patterns to Avoid

- **`--onefile` mode:** Startup would extract 3+ GB to temp on each launch. Use `--onedir` (the default, which is what COLLECT produces).
- **`UPX=True` on CUDA DLLs:** UPX compression can corrupt CUDA DLLs or trigger antivirus. Leave `upx=False`.
- **Using `sys._MEIPASS` as model download location:** _internal/ is read-only. Always use `platformdirs` for writable paths in frozen apps.
- **Embedding model in dist/:** Per D-08, model is not bundled. `models/` must be in `.gitignore` and excluded from zip distribution.
- **`whisper` package conflicts:** openai-whisper is also installed in venv (version 20250625, confirmed). Must exclude it from the PyInstaller build with `excludes=['whisper']` to avoid 100+ MB of unnecessary data files and potential conflicts.
- **`collect_all()` performance warning:** The PyInstaller docs warn that `collect_all()` is expensive. For this project the packages are small enough that it is acceptable. The alternative — manually listing every hidden import — risks missing dynamic imports in ctranslate2.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Model presence check | Custom hash/checksum logic | Check for `model.bin` existence in HuggingFace hub cache path | HF hub manages integrity; model.bin is the heavy file |
| CUDA DLL collection | Manually listing every .dll | `collect_all('ctranslate2')` + PyInstaller auto-collects torch/lib DLLs | 37 torch DLLs + ctranslate2 DLLs — impossible to maintain manually |
| Keyring backend | Custom Windows Credential Manager code | `collect_all('keyring')` + `win32timezone` hidden import | Entry-point-based discovery breaks in frozen apps; collect_all fixes it |
| Model download progress | Custom HTTP download code | Run `WhisperModel.__init__` (which calls HF hub) in thread + indeterminate bar | HF hub handles chunked download, resume, hash verification |
| Security scan for secrets | Manual review | `grep -rn "sk-ant-\|sk-proj-\|api_key\s*=\s*['\"]"` in build.bat | Automated grep catches common patterns before push |

**Key insight:** The three hardest packaging problems in this stack (CUDA DLLs, keyring entry points, ctranslate2 C extensions) are all solved by `collect_all()` — the complexity is in knowing WHICH packages need it, not in implementation.

## Common Pitfalls

### Pitfall 1: Model Download Path Writes to Read-Only _internal/
**What goes wrong:** App launches, `get_resource_path("models")` returns `_MEIPASS/models`, huggingface_hub tries to write there, fails silently or throws PermissionError.
**Why it happens:** `sys._MEIPASS` points to `_internal/` inside the dist folder. PyInstaller marks this as read-only on Windows to prevent accidental modification.
**How to avoid:** Use `get_model_path()` (new function using platformdirs) in `transcription_panel.py:1067` instead of `get_resource_path("models")`. This must change BEFORE building.
**Warning signs:** First-launch download fails with "Permission denied" or model loads from wrong path.

### Pitfall 2: Keyring "No recommended backend" in Frozen App
**What goes wrong:** API key dialog fails silently; keyring raises `NoKeyringError: No recommended backend was available`.
**Why it happens:** Keyring discovers its Windows backend via Python entry points (`importlib.metadata`). PyInstaller does not preserve entry point metadata unless explicitly told to.
**How to avoid:** Add `collect_all('keyring')` to spec AND add `'win32timezone'` and `'keyring.backends.Windows'` to hiddenimports.
**Warning signs:** Keyring works in dev (running from source) but fails in built exe.

### Pitfall 3: ctranslate2 DLL Load Error at Runtime
**What goes wrong:** `ImportError: DLL load failed` when ctranslate2 attempts to initialize. Or `OSError: [WinError 193]` for wrong DLL architecture.
**Why it happens:** ctranslate2 ships its own DLLs (ctranslate2.dll, cudnn64_9.dll, libiomp5md.dll). PyInstaller may not discover them automatically because they are not `.pyd` extension files.
**How to avoid:** Use `collect_all('ctranslate2')` which captures binaries via `collect_dynamic_libs`. Verify the three ctranslate2 DLLs appear in `dist/WhisperPrepis/_internal/`.
**Warning signs:** App fails immediately on startup with DLL-related error.

### Pitfall 4: torch Recursion Error During Build
**What goes wrong:** PyInstaller build fails with `RecursionError: maximum recursion depth exceeded` during Analysis phase.
**Why it happens:** torch has an extraordinarily deep import graph. Default Python recursion limit (1000) is insufficient.
**How to avoid:** Set `sys.setrecursionlimit(5000)` at the TOP of the spec file (before Analysis is called).
**Warning signs:** Build terminates with RecursionError stack trace mentioning torch.

### Pitfall 5: openai-whisper Included in Bundle Unnecessarily
**What goes wrong:** Build succeeds but dist/ is 500+ MB larger than expected. Risk of whisper and faster-whisper model path conflicts.
**Why it happens:** openai-whisper 20250625 is installed in the venv (confirmed). PyInstaller will include it unless explicitly excluded.
**How to avoid:** Add `excludes=['whisper', 'openai.whisper']` to Analysis. The app uses `faster_whisper`, not `whisper`.
**Warning signs:** dist/ folder unexpectedly large; `whisper/` directory visible inside `_internal/`.

### Pitfall 6: ffmpeg Not Found on Clean Machine
**What goes wrong:** Transcription fails; no audio can be decoded. Error message about ffmpeg not found.
**Why it happens:** `get_resource_path("bin/ffmpeg.exe")` correctly resolves path but ffmpeg.exe was not placed in `bin/` before building, or the `binaries` spec entry was wrong.
**How to avoid:** Confirm `bin/ffmpeg.exe` and `bin/ffprobe.exe` exist before running PyInstaller. The spec `binaries=[('bin/ffmpeg.exe', 'bin'), ('bin/ffprobe.exe', 'bin')]` copies them to `_internal/bin/` in dist.
**Warning signs:** App launches but transcription immediately errors on audio loading.

### Pitfall 7: onnxruntime DLLs Missing for silero-vad
**What goes wrong:** VAD preprocessing fails; silero-vad cannot initialize ONNX model.
**Why it happens:** silero-vad uses onnxruntime for inference. onnxruntime ships `onnxruntime.dll` and `onnxruntime_pybind11_state.pyd` in `onnxruntime/capi/`. These may not be auto-collected.
**How to avoid:** Use `collect_all('onnxruntime')` in spec. Verify onnxruntime.dll appears in dist.
**Warning signs:** App launches but silero-vad crashes; VAD analyzing step never completes.

### Pitfall 8: HuggingFace Hub Model Cache Path Symlinks
**What goes wrong:** Model appears present (directory exists) but files are symlinks pointing to blobs/ which was not copied.
**Why it happens:** On older huggingface_hub versions, snapshot_download used symlinks. This is resolved in huggingface_hub ≥1.0 (no-symlinks mode is default on Windows).
**How to avoid:** The installed version is 1.8.0. The model currently in dev has regular files (blobs/ is empty, snapshot/ has actual files — confirmed). No action needed.
**Warning signs:** model.bin "exists" but has 0 bytes or is a broken symlink.

### Pitfall 9: Git Push Leaks Developer Context Files
**What goes wrong:** `.planning/`, `.claude/`, `.vexp/` (session artifacts) get committed and pushed.
**Why it happens:** No `.gitignore` exists yet (confirmed). These directories are currently only untracked.
**How to avoid:** Create `.gitignore` BEFORE the first `git add`. Once committed, removing from history requires rewriting history.
**Warning signs:** `git status` shows tracked files in `.planning/`, `.claude/`, `.vexp/`.

## Code Examples

Verified patterns from installed packages and official sources:

### Model Presence Check Pattern
```python
# src/whisperai/utils/model_path.py
import glob
import sys
from pathlib import Path
from platformdirs import user_data_dir


def get_model_path() -> Path:
    """Writable directory for faster-whisper model. Frozen: APPDATA; dev: project root."""
    if getattr(sys, "frozen", False):
        return Path(user_data_dir("WhisperPrepis", "WhisperPrepis")) / "models"
    return Path(__file__).parent.parent.parent.parent / "models"


def is_model_downloaded() -> bool:
    """True if medium model.bin is present in the model path."""
    pattern = str(
        get_model_path()
        / "models--Systran--faster-whisper-medium"
        / "snapshots"
        / "*"
        / "model.bin"
    )
    return len(glob.glob(pattern)) > 0
```

### WhisperModel Loading with Correct Path
```python
# In _worker_init (transcriber.py) — no change needed to signature,
# but the caller (transcription_panel.py) must pass get_model_path() instead
from src.whisperai.utils.model_path import get_model_path

model_path = str(get_model_path())  # replaces get_resource_path("models")

_model = WhisperModel(
    "medium",
    device=device,
    compute_type=compute_type,
    download_root=model_path,  # downloads to writable dir; loads from cache if present
)
```

### ffmpeg PATH Prepend in main.py
```python
# main.py — add after freeze_support(), before i18n init
import os, sys
from pathlib import Path

def main() -> None:
    import multiprocessing
    multiprocessing.freeze_support()

    # Prepend bundled ffmpeg dir to PATH in frozen app
    if getattr(sys, "frozen", False):
        bin_dir = str(Path(sys._MEIPASS) / "bin")
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")

    from src.whisperai.utils.i18n import detect_system_language, set_language
    # ... rest of main
```

### Security Scan in build.bat
```bat
REM Security scan before build — fail fast on potential secrets
echo Scanning for hardcoded secrets...
findstr /r /s /i "sk-ant-api\|sk-proj-\|api_key\s*=\s*[" src\ main.py 2>nul
if %errorlevel% equ 0 (
    echo WARNING: Potential hardcoded secrets found. Review before continuing.
    pause
)
```

### ffmpeg Binary Source
BtbN releases: `ffmpeg-master-latest-win64-gpl.zip` from https://github.com/BtbN/FFmpeg-Builds/releases
Contents include: `ffmpeg-master-latest-win64-gpl/bin/ffmpeg.exe` and `ffprobe.exe`.
Extract only `ffmpeg.exe` and `ffprobe.exe` to project `bin/` directory.

### GitHub Release Zip Creation (in build.bat)
```bat
REM After successful PyInstaller build, create release zip
cd dist
powershell -Command "Compress-Archive -Path 'WhisperPrepis' -DestinationPath 'WhisperPrepis-v1.0-windows.zip' -Force"
cd ..
echo Release zip: dist\WhisperPrepis-v1.0-windows.zip
```

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12 | Build runtime | ✓ | 3.12.10 (venv confirmed) | — |
| PyInstaller | PKG-01, PKG-05 | ✗ | Not installed in venv | Install: `.venv\Scripts\pip install pyinstaller==6.19.0` |
| ffmpeg.exe | PKG-03 | ✗ | Not present (bin/ doesn't exist) | Download from BtbN/FFmpeg-Builds |
| ffprobe.exe | PKG-03 | ✗ | Not present | Download from BtbN/FFmpeg-Builds |
| faster-whisper model | PKG-04 (mod by D-08) | ✓ dev | 1.5 GB in models/ (dev only) | On first frozen launch, downloads to APPDATA |
| git | D-01 to D-04 | ✓ | (used in project, master branch exists) | — |
| GitHub CLI (gh) | D-07 release | LOW | Not checked | Use GitHub web UI for release creation |

**Missing dependencies blocking build execution:**
- PyInstaller 6.19.0 — must install into venv before build can run
- ffmpeg.exe + ffprobe.exe — must download from BtbN before build (spec references bin/)

**Missing with fallback:**
- GitHub CLI — GitHub Release can be created via web UI if `gh` is not available

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Bundled model in dist/ | Download on first launch to APPDATA | D-08 decision | Distribution zip is ~500 MB not ~2 GB; requires internet on first run |
| openai-whisper | faster-whisper (CTranslate2) | Phase 2 decision | Different model format, different spec file requirements (no tiktoken) |
| nvidia-* PyPI CUDA packages | CUDA DLLs embedded in torch/lib/ | torch 2.11+cu126 wheel | No nvidia-* packages needed; PyInstaller collects torch/lib/*.dll automatically |
| PyInstaller 5.x _MEIPASS layout | PyInstaller 6.x `_internal/` subdirectory | PyInstaller 6.0 | `sys._MEIPASS` still works the same; `_internal/` is the visible folder name in dist/ |

**Deprecated/outdated:**
- openai-whisper tiktoken hidden imports: Not applicable here — faster-whisper uses its own `tokenizers` library (Rust-backed). The `tiktoken` fix mentioned in PKG-05 requirement was written for openai-whisper; for faster-whisper the relevant package is `tokenizers`.
- `local_dir_use_symlinks` in huggingface_hub: Deprecated in huggingface_hub ≥1.0. Hub 1.8.0 does not use symlinks on Windows by default (confirmed by blobs/ being empty in dev model cache).

## Open Questions

1. **openai-whisper in venv — safe to exclude?**
   - What we know: openai-whisper 20250625 is installed in the venv. The app uses only faster-whisper.
   - What's unclear: Whether any transitive import in faster-whisper or silero-vad accidentally imports from `whisper` package.
   - Recommendation: Add `excludes=['whisper']` to spec, then test build. If build fails with missing import, investigate which package pulls in whisper.

2. **Model download indeterminate vs determinate progress**
   - What we know: `snapshot_download` does not have a clean per-byte callback. Download time for 1.5 GB is 2-15 minutes.
   - What's unclear: Whether implementing a determinate progress bar (polling file size) is worth the complexity vs. indeterminate spinner.
   - Recommendation: Implement an indeterminate `ttk.Progressbar` with a clear size/time label. Determinate progress can be added post-v1 by monitoring the partial file size in a polling thread.

3. **GitHub release creation automation**
   - What we know: D-07 requires GitHub Release with a zip. User hasn't confirmed `gh` CLI availability.
   - What's unclear: Whether `gh` is installed on the build machine.
   - Recommendation: The build script creates the zip; GitHub Release can be done manually via web UI for v1. Document the steps in README.

4. **Icon file for EXE**
   - What we know: No .ico file exists in the project.
   - What's unclear: Whether user wants a custom icon for v1.
   - Recommendation: Set `icon=None` in spec for now (PyInstaller will use default Python icon). Icon can be added post-v1.

## Sources

### Primary (HIGH confidence)
- Verified against installed venv packages (pip list, directory inspection) — all versions confirmed 2026-03-29
- [keyring issue #439](https://github.com/jaraco/keyring/issues/439) — `collect_all keyring` fix for PyInstaller
- [keyring issue #468](https://github.com/jaraco/keyring/issues/468) — `win32timezone` hidden import + explicit backend import pattern
- [PyInstaller+PyTorch discussion #7621](https://github.com/orgs/pyinstaller/discussions/7621) — `copy_metadata('torch')` requirement
- [huggingface_hub snapshot_download docs](https://huggingface.co/docs/huggingface_hub/package_reference/file_download) — `cache_dir` parameter behavior
- [faster-whisper DeepWiki](https://deepwiki.com/SYSTRAN/faster-whisper/7.1-downloading-and-caching-models) — WhisperModel local path loading
- [BtbN/FFmpeg-Builds DeepWiki](https://deepwiki.com/BtbN/FFmpeg-Builds/4.1-build-variants-and-targets) — static variants include ffmpeg.exe + ffprobe.exe
- Direct filesystem inspection: torch/lib DLLs confirmed (37 DLLs including all CUDA); ctranslate2 DLLs confirmed (3); silero_vad/data/ files confirmed; blobs/ empty (no symlinks)

### Secondary (MEDIUM confidence)
- [pyinstaller-hooks-contrib CHANGELOG](https://raw.githubusercontent.com/pyinstaller/pyinstaller-hooks-contrib/master/CHANGELOG.rst) — confirmed NO dedicated hooks for ctranslate2, faster-whisper, silero-vad, ttkbootstrap (must handle manually)
- [PyInstaller pywin32-ctypes PR #5250](https://github.com/pyinstaller/pyinstaller/pull/5250) — ctypes backend always collected in recent PyInstaller

### Tertiary (LOW confidence)
- Community reports of `collect_all('ctranslate2')` pattern — no single authoritative source, inferred from package structure inspection

## Metadata

**Confidence breakdown:**
- Standard stack (versions): HIGH — all verified against installed venv
- Spec file structure: MEDIUM — no community spec file found for this exact stack; derived from package structure inspection + official PyInstaller docs + known patterns
- Keyring fix: HIGH — multiple official issue reports with confirmed solutions
- Model path writable dir: HIGH — sys._MEIPASS read-only is documented PyInstaller behavior; platformdirs is the standard solution
- Pitfalls: HIGH for items backed by official issues; MEDIUM for items inferred from package structure

**Research date:** 2026-03-29
**Valid until:** 2026-06-01 (packages stable; PyInstaller 6.x changelog moves slowly)

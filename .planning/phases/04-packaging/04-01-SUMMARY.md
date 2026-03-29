---
phase: 04-packaging
plan: 01
subsystem: infra
tags: [pyinstaller, packaging, model-path, ffmpeg, ctranslate2, faster-whisper, keyring]

# Dependency graph
requires:
  - phase: 03-claude-cleanup-settings
    provides: transcription_panel.py with model loading, main.py entry point, requirements.in

provides:
  - src/whisperai/utils/model_path.py — writable model directory resolver (frozen vs dev)
  - whisperai.spec — full PyInstaller build configuration with all collect_all calls
  - build.bat — one-click build script with validation and release zip creation
  - main.py — ffmpeg PATH prepend for frozen context

affects: [04-02, 04-03, model-download-dialog]

# Tech tracking
tech-stack:
  added: [platformdirs (user_data_dir for writable model path in frozen app)]
  patterns:
    - frozen-detection with getattr(sys, "frozen", False)
    - writable APPDATA model path via platformdirs user_data_dir
    - ffmpeg PATH prepend in main() before any subprocess usage
    - collect_all() for all packages with DLLs or entry-point plugins

key-files:
  created:
    - src/whisperai/utils/model_path.py
    - whisperai.spec
    - build.bat
  modified:
    - main.py
    - src/whisperai/gui/transcription_panel.py

key-decisions:
  - "get_model_path() uses platformdirs user_data_dir for frozen — sys._MEIPASS/_internal is read-only, cannot store downloaded model there"
  - "sys.setrecursionlimit(5000) placed before Analysis() in spec — torch module graph exceeds default 1000 limit"
  - "excludes=['whisper', 'openai.whisper'] in spec — openai-whisper is installed in venv but unused; excluding saves 100+ MB"
  - "upx=False throughout spec — UPX compression can corrupt CUDA DLLs"
  - "collect_all() for ctranslate2, keyring, silero_vad, huggingface_hub, onnxruntime — entry-point discovery and DLL collection require it"

patterns-established:
  - "Pattern: model_path.py separates writable model storage from read-only bundled resources"
  - "Pattern: build.bat validates ffmpeg binaries and runs security scan before invoking PyInstaller"

requirements-completed: [PKG-05, PKG-06, PKG-03]

# Metrics
duration: 8min
completed: 2026-03-29
---

# Phase 4 Plan 01: PyInstaller Build Infrastructure Summary

**PyInstaller spec + build script with collect_all for ctranslate2/keyring/onnxruntime, writable APPDATA model path via platformdirs, and ffmpeg PATH prepend in main()**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-29T16:49:00Z
- **Completed:** 2026-03-29T16:57:13Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- Created model_path.py providing get_model_path() (APPDATA when frozen, project models/ in dev) and is_model_downloaded() (checks for model.bin in HF hub cache pattern)
- Updated transcription_panel.py to use get_model_path() instead of get_resource_path("models") — prevents write failures to read-only _internal/ on first launch
- Added ffmpeg PATH prepend in main.py for frozen context — bin_dir prepended to PATH before any subprocess can run
- Created whisperai.spec with collect_all for all 5 packages requiring DLL/entry-point collection, copy_metadata for 5 packages, recursion limit 5000, and all data/binary entries
- Created build.bat with venv activation, ffmpeg binary validation, hardcoded secret scan, PyInstaller invocation, and PowerShell release zip creation

## Task Commits

1. **Task 1: Create model_path.py and update frozen-context paths** - `b9b0988` (feat)
2. **Task 2: Create PyInstaller spec file and build script** - `e62c41c` (feat)

## Files Created/Modified

- `src/whisperai/utils/model_path.py` — get_model_path() and is_model_downloaded() for writable model storage
- `src/whisperai/gui/transcription_panel.py` — replaced get_resource_path("models") with get_model_path()
- `main.py` — added ffmpeg PATH prepend for frozen context (sys._MEIPASS/bin)
- `whisperai.spec` — full PyInstaller build configuration with collect_all, copy_metadata, hidden imports, exclusions
- `build.bat` — one-click build with validation checks, security scan, and release zip

## Decisions Made

- get_model_path() uses platformdirs user_data_dir because sys._MEIPASS/_internal/ is read-only in PyInstaller 6.x — downloaded model files cannot be stored there
- sys.setrecursionlimit(5000) placed at the very top of whisperai.spec before Analysis() — torch import graph exceeds the default Python limit of 1000
- excludes=['whisper', 'openai.whisper'] added to Analysis — openai-whisper 20250625 is installed in venv but the app uses only faster-whisper; excluding it avoids 100+ MB of unnecessary data
- upx=False in both EXE and COLLECT — UPX can corrupt CUDA DLLs (ctranslate2.dll, cudnn64_9.dll) and trigger antivirus false positives
- build.bat uses findstr security scan (not a custom grep) — native Windows tool, no extra dependency

## Deviations from Plan

None — plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

Before running build.bat, the following must be done manually (documented in plan D-11):
- Download ffmpeg-master-latest-win64-gpl.zip from https://github.com/BtbN/FFmpeg-Builds/releases
- Extract ffmpeg.exe and ffprobe.exe into the project bin/ directory
- Install PyInstaller: `.venv\Scripts\pip install pyinstaller==6.19.0`

build.bat will check for these and fail with clear error messages if missing.

## Next Phase Readiness

- Build infrastructure is complete — whisperai.spec and build.bat are ready for plan 04-02 (model download dialog) and 04-03 (GitHub publication)
- The model download dialog (plan 04-02) can use get_model_path() and is_model_downloaded() directly from model_path.py
- ffmpeg binaries (bin/ffmpeg.exe, bin/ffprobe.exe) must be downloaded before the actual build runs — this is a human action, not automated

---
*Phase: 04-packaging*
*Completed: 2026-03-29*

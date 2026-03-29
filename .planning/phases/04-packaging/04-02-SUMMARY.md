---
phase: 04-packaging
plan: 02
subsystem: gui
tags: [model-download, dialog, i18n, pyinstaller, ffmpeg, first-build]

# Dependency graph
requires:
  - phase: 04-packaging
    plan: 01
    provides: model_path.py (get_model_path, is_model_downloaded), whisperai.spec, build.bat

provides:
  - src/whisperai/gui/model_download_dialog.py — ModelDownloadDialog Toplevel with all UI states
  - locale/cs_CZ/LC_MESSAGES/messages.po — Czech download.* strings (13 new msgid entries)
  - locale/en_US/LC_MESSAGES/messages.po — English download.* strings (13 new msgid entries)
  - locale/*/LC_MESSAGES/messages.mo — compiled binary catalogs
  - main.py — model check + download dialog flow before create_app()
  - bin/ffmpeg.exe, bin/ffprobe.exe — ffmpeg 7.x binaries for bundling
  - dist/WhisperPrepis/ — first successful PyInstaller build output

affects: [04-03]

# Tech tracking
tech-stack:
  added: [pyinstaller==6.19.0 (dev), ffmpeg 7 static binaries (bundled)]
  patterns:
    - blocking modal via ttk.Toplevel + grab_set() + wait_window()
    - background download thread with after(200, poll) for non-blocking UI
    - indeterminate progress bar for long operation without known duration
    - auto-close after 1500ms on success (matches SettingsDialog pattern)
    - inline cancel confirmation (destroy buttons, show confirm/back pair)
    - temporary dl_root window created for dialog, destroyed before create_app()

key-files:
  created:
    - src/whisperai/gui/model_download_dialog.py
    - bin/ffmpeg.exe
    - bin/ffprobe.exe
    - dist/WhisperPrepis/WhisperPrepis.exe (build artifact, not tracked)
  modified:
    - locale/cs_CZ/LC_MESSAGES/messages.po
    - locale/en_US/LC_MESSAGES/messages.po
    - locale/cs_CZ/LC_MESSAGES/messages.mo
    - locale/en_US/LC_MESSAGES/messages.mo
    - main.py

key-decisions:
  - "SettingsStore used in main.py for language — persisted language applied to download dialog strings"
  - "Temporary dl_root Window created for download dialog, destroyed before create_app() — avoids modifying create_app() internals"
  - "wait_window(dialog) blocks main thread until dialog closes — correct for startup-modal pattern"
  - "Download uses WhisperModel('medium', device='cpu', compute_type='int8') — cpu/int8 to minimize VRAM usage during download-only init"
  - "build.bat security scan false positive on settings_dialog.py api_key label — accepted, not a real secret"

requirements-completed: [PKG-04, PKG-01]

# Metrics
duration: 18min
completed: 2026-03-29
---

# Phase 4 Plan 02: Model Download Dialog Summary

**ModelDownloadDialog Toplevel with indeterminate progress, auto-close on success, retry/cancel on error, inline cancel confirmation, wired into main.py startup; first PyInstaller build succeeded producing dist/WhisperPrepis/ with ffmpeg, locale, and prompts bundled**

## Performance

- **Duration:** ~18 min
- **Started:** 2026-03-29T17:00:00Z
- **Completed:** 2026-03-29T17:18:00Z
- **Tasks:** 2
- **Files modified:** 7

## Accomplishments

- Added 13 `download.*` msgid/msgstr entries to both Czech and English .po files, compiled both to .mo
- Created `src/whisperai/gui/model_download_dialog.py` — 230-line ModelDownloadDialog class with all UI states per UI-SPEC: downloading (indeterminate progress bar), success (auto-close 1500ms), error (retry + cancel buttons), cancel confirm (inline text + confirm/back buttons), cancel confirmed (grab_release + destroy)
- Updated main.py to check `is_model_downloaded()` using SettingsStore language before calling `create_app()` — shows download dialog in temporary window when model is absent
- Downloaded ffmpeg v7 (2026-03-29 build, 208 MB zip) from BtbN, extracted ffmpeg.exe and ffprobe.exe to `bin/`
- Installed pyinstaller==6.19.0 into venv
- Ran `build.bat` — first PyInstaller build succeeded: `dist/WhisperPrepis/WhisperPrepis.exe` produced with `_internal/bin/ffmpeg.exe`, `_internal/locale/cs_CZ/` and `_internal/locale/en_US/`, `_internal/prompts/`, and all ctranslate2/onnxruntime/torch DLLs

## Task Commits

1. **Task 1: Add i18n strings and create ModelDownloadDialog** - `8ef1159` (feat)
2. **Task 2: Wire download dialog into main.py startup and run first build** - `39b70a7` (feat)

## Files Created/Modified

- `src/whisperai/gui/model_download_dialog.py` — full ModelDownloadDialog implementation
- `locale/cs_CZ/LC_MESSAGES/messages.po` — 13 new download.* msgid entries added
- `locale/en_US/LC_MESSAGES/messages.po` — 13 new download.* msgid entries added
- `locale/cs_CZ/LC_MESSAGES/messages.mo` — recompiled
- `locale/en_US/LC_MESSAGES/messages.mo` — recompiled
- `main.py` — model check + download dialog flow added before create_app()
- `bin/ffmpeg.exe` — ffmpeg 7 static binary (92 MB)
- `bin/ffprobe.exe` — ffprobe 7 static binary (92 MB)

## Decisions Made

- SettingsStore used in main.py for language retrieval — ensures persisted language (not just OS language) is applied to download dialog strings
- Temporary `dl_root` ttkbootstrap.Window created for the download dialog and destroyed before `create_app()` — keeps startup flow clean without modifying `create_app()` internals
- `wait_window(dialog)` blocks main thread until dialog closes — correct modal pattern for startup gating
- Download uses `WhisperModel("medium", device="cpu", compute_type="int8")` — cpu/int8 minimizes memory usage for a download-only init; model is reloaded for actual transcription
- build.bat security scan false positive on `settings_dialog.py` (line contains `"settings.api_key"` string — not a hardcoded key) — documented, not blocking

## Deviations from Plan

None — plan executed exactly as written.

## Build Notes

First PyInstaller build completed successfully with one non-blocking warning:
- `tbb12.dll` not found (numba dependency) — numba is not used by the app; warning is harmless

The security scan in build.bat triggered on `settings_dialog.py` due to the string `"settings.api_key"` (a translation key, not a credential). This is a false positive in the simple `findstr` scan. Not blocking.

## Self-Check: PASSED

All created files verified:
- FOUND: src/whisperai/gui/model_download_dialog.py
- FOUND: locale/cs_CZ/LC_MESSAGES/messages.mo
- FOUND: locale/en_US/LC_MESSAGES/messages.mo
- FOUND: bin/ffmpeg.exe
- FOUND: bin/ffprobe.exe
- FOUND: dist/WhisperPrepis/WhisperPrepis.exe
- FOUND: dist/WhisperPrepis/_internal/bin/ffmpeg.exe

All commits verified:
- FOUND: 8ef1159 (Task 1)
- FOUND: 39b70a7 (Task 2)

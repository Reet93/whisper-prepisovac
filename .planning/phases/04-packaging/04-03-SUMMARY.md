---
phase: 04-packaging
plan: 03
subsystem: infra
tags: [git, readme, license, gitignore, security, packaging, tkinter]

# Dependency graph
requires:
  - phase: 04-packaging plan 02
    provides: ModelDownloadDialog wired into main.py, working portable folder build
provides:
  - .gitignore excluding all non-source directories
  - README.md with installation, first-launch, usage, and build documentation
  - MIT LICENSE file
  - Verified portable folder running successfully on Windows
  - TclError fix: create_app() accepts existing_root parameter to reuse Tk interpreter
affects: []

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "create_app() accepts existing_root kwarg — allows download dialog root to be reused instead of destroyed/recreated, preventing Tk interpreter teardown"

key-files:
  created:
    - .gitignore
    - README.md
    - LICENSE
  modified:
    - src/whisperai/gui/app.py

key-decisions:
  - "TclError fix: reuse Tk root from download dialog in create_app() instead of creating a new root — destroying dl_root before create_app() killed the Tk interpreter"

patterns-established:
  - "Tk root lifecycle: if a download dialog is shown at startup, pass its root window to create_app() via existing_root kwarg so the same interpreter is reused"

requirements-completed: []

# Metrics
duration: ~30min
completed: 2026-03-29
---

# Phase 4 Plan 3: Git Publication Files + App Verification Summary

**GitHub publication files created (.gitignore, README.md, MIT LICENSE) and portable folder verified — TclError on first launch fixed by reusing the download dialog's Tk root in create_app()**

## Performance

- **Duration:** ~30 min
- **Started:** 2026-03-29
- **Completed:** 2026-03-29
- **Tasks:** 2 (1 auto + 1 human-verify)
- **Files modified:** 4

## Accomplishments

- Created `.gitignore` excluding all build artifacts, planning files, models, venvs, and secrets
- Created `README.md` documenting features, installation (portable + source), first-launch model download, usage, and build instructions
- Created `LICENSE` with MIT license text
- Security scan confirmed no hardcoded API keys in source
- Fixed TclError crash that occurred when the app was launched from the built portable folder — `create_app()` now accepts an `existing_root` parameter so the download dialog's Tk root is reused rather than destroyed
- User-verified the portable folder launches, download dialog works, and transcription runs correctly

## Task Commits

Each task was committed atomically:

1. **Task 1: Create .gitignore, README.md, LICENSE, and run security scan** - `a745b90` (feat)
2. **Task 2: Verify built portable folder runs correctly** - `b5a85fe` (fix — TclError auto-fixed during human verification)

**Plan metadata:** _(this commit)_

## Files Created/Modified

- `.gitignore` — Excludes `__pycache__/`, `.venv/`, `.vexp/`, `models/`, `build/`, `dist/`, `bin/`, `.planning/`, `.claude/`, `*.log`, `.DS_Store`, `Thumbs.db`
- `README.md` — Project documentation for GitHub: features, requirements, installation, first-launch note (~1.5 GB download), usage, build instructions
- `LICENSE` — MIT License 2026
- `src/whisperai/gui/app.py` — `create_app()` now accepts `existing_root=None` kwarg; reuses it when provided instead of creating a new `Tk()` instance

## Decisions Made

- TclError root cause: `main.py` created a `dl_root = tk.Tk()` window for the download dialog, then called `dl_root.destroy()` before calling `create_app()`. This destroyed the Tk interpreter entirely, so `create_app()` could not create a new `Tk()` instance. Fix: pass `existing_root=dl_root` and call `dl_root.deiconify()` / `dl_root.geometry(...)` to repurpose it as the main window instead of destroying and recreating.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] TclError on first launch — Tk root destroyed before create_app()**
- **Found during:** Task 2 (Verify built portable folder runs correctly)
- **Issue:** App crashed with `TclError: can't invoke "wm" command: application has been destroyed` immediately after the download dialog closed. Root cause: `dl_root.destroy()` in `main.py` invalidated the Tk interpreter; a subsequent `tk.Tk()` call in `create_app()` then failed.
- **Fix:** Added `existing_root=None` parameter to `create_app()`. When provided, the function reuses it (calls `existing_root.deiconify()` and resets geometry) rather than constructing a new `Tk()`. Updated `main.py` to pass `existing_root=dl_root` instead of destroying it.
- **Files modified:** `src/whisperai/gui/app.py`, `main.py`
- **Verification:** User confirmed app launches successfully after fix; transcription runs to completion.
- **Committed in:** `b5a85fe`

---

**Total deviations:** 1 auto-fixed (Rule 1 — bug)
**Impact on plan:** Critical fix — app would not launch at all from the portable folder without it. No scope creep.

## Issues Encountered

- First portable-folder launch failed with TclError due to Tk interpreter teardown (see Deviations). Fixed in `b5a85fe` and verified by user.

## User Setup Required

None — no external service configuration required.

## Known Stubs

None.

## Next Phase Readiness

- Phase 04 is complete. All three plans executed and verified:
  - 04-01: PyInstaller spec + build script
  - 04-02: ModelDownloadDialog wired into main.py, build produced
  - 04-03: GitHub publication files, security scan, app verification
- PKG-02 (macOS packaging) is deferred per D-05 — requires Mac hardware, PyInstaller does not cross-compile.
- Repository is ready for GitHub publication.

---
*Phase: 04-packaging*
*Completed: 2026-03-29*

## Self-Check: PASSED

- FOUND: `.planning/phases/04-packaging/04-03-SUMMARY.md`
- FOUND: commit `a745b90` (Task 1 — git publication files)
- FOUND: commit `b5a85fe` (Task 2 — TclError fix)

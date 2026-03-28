---
phase: 01-foundation
plan: 01
subsystem: foundation
tags: [i18n, gui, ttkbootstrap, resource-path, gettext]
dependency_graph:
  requires: []
  provides: [get_resource_path, set_language, detect_system_language, MainWindow, create_app]
  affects: [all-subsequent-phases]
tech_stack:
  added: [ttkbootstrap==1.20.2, Babel==2.18.0]
  patterns: [gettext-i18n, pyinstaller-resource-path, ttkbootstrap-grid-layout]
key_files:
  created:
    - src/whisperai/__init__.py
    - src/whisperai/__main__.py
    - src/whisperai/utils/__init__.py
    - src/whisperai/utils/resource_path.py
    - src/whisperai/utils/i18n.py
    - src/whisperai/gui/__init__.py
    - src/whisperai/gui/main_window.py
    - src/whisperai/app.py
    - main.py
    - locale/cs_CZ/LC_MESSAGES/messages.po
    - locale/cs_CZ/LC_MESSAGES/messages.mo
    - locale/en_US/LC_MESSAGES/messages.po
    - locale/en_US/LC_MESSAGES/messages.mo
    - babel.cfg
    - requirements.in
  modified: []
decisions:
  - "4 parent traversals in get_resource_path() for src/whisperai/utils/ depth — not 2 as shown in UI-SPEC (corrected per RESEARCH.md Pitfall 1)"
  - "Used Python 3.14 (system-installed) for dev-time verification — ttkbootstrap and foundation stdlib code works; Whisper/PyTorch not yet needed"
  - "Language switcher shows restart notice on change; live reload deferred to Phase 3"
metrics:
  duration_seconds: 112
  completed_date: "2026-03-28"
  tasks_completed: 2
  tasks_total: 3
  files_created: 15
  files_modified: 0
---

# Phase 01 Plan 01: Foundation Summary

**One-liner:** ttkbootstrap flatly-themed window with gettext i18n (Czech/English), PyInstaller-safe resource path helper, and three-frame grid layout with language switcher.

## Tasks Completed

| # | Task | Status | Commit |
|---|------|--------|--------|
| 1 | Project skeleton, resource path, i18n, locale files | Done | ea0ae77 |
| 2 | Entry point, window, layout, language switcher | Done | 60ae537 |
| 3 | Verify running application | Checkpoint — awaiting human verify | — |

## What Was Built

### Task 1: Project skeleton, resource path, i18n, and locale files

Created the complete package structure `src/whisperai/` with `gui/` and `utils/` subpackages. The `get_resource_path()` helper uses `Path(__file__).parent.parent.parent.parent` (4 levels) to correctly reach the project root from `src/whisperai/utils/resource_path.py`, and uses `sys._MEIPASS` in frozen context (PyInstaller 6.x `_internal/` subfolder pattern).

The `detect_system_language()` function uses `locale.getlocale()` after `setlocale()` (not the deprecated `getdefaultlocale()`), with a Windows `ctypes.windll.kernel32.GetUserDefaultUILanguage()` fallback. `set_language()` installs `_()` into builtins via `gettext.translation().install()`.

Czech and English `.po` files contain all 6 UI-SPEC copywriting keys with full Czech diacritics. `.mo` binary catalogs compiled via `pybabel compile`.

### Task 2: Entry point, window, layout, and language switcher

`main.py` calls `multiprocessing.freeze_support()` first, then `set_language()` before any gui import, ensuring `_()` is available when modules are first imported.

`app.py` creates a `ttkbootstrap.Window` with `themename="flatly"`, `size=(720, 480)`, `minsize=(480, 320)`, using `withdraw()`/`place_window_center()`/`deiconify()` to center before showing.

`MainWindow` builds the locked three-frame hierarchy using `grid` exclusively inside `main_frame` (header at row=0, content at row=1 with `weight=1`, footer at row=2). `pack` is used inside leaf frames only. Language Combobox is `state="readonly"`, right-aligned in footer, fires `messagebox.showinfo` with `ui.language_changed_notice` on change.

## Deviations from Plan

### Auto-fixed Issues

None — plan executed exactly as written.

### Context-Driven Adjustments

**1. Python 3.14 used for dev-time verification (not Python 3.12)**
- **Found during:** Task 1 verification setup
- **Issue:** Python 3.12 not installed on dev machine; system Python is 3.14.2
- **Assessment:** The Phase 1 foundation code (ttkbootstrap, gettext, pathlib, tkinter) is all stdlib + pure Python. Verified that ttkbootstrap 1.20.2 installs and imports correctly on Python 3.14. The Python 3.12 constraint in CLAUDE.md applies to the full stack (openai-whisper, PyTorch) which are not involved in Phase 1. Python 3.12 must be installed before Phase 2 (Whisper integration).
- **Action:** Proceeded with Python 3.14 for Phase 1 dev verification. Added note to deferred items.

## Known Stubs

| Stub | File | Description |
|------|------|-------------|
| Placeholder label | src/whisperai/gui/main_window.py:47 | `_("ui.placeholder")` shown in content_frame — intentional Phase 1 placeholder, replaced by Phase 2 file list UI |

The placeholder is intentional per the plan — it occupies the content_frame slot that Phase 2 will replace with the actual file list and log area.

## Verification Results

- `python -c "from src.whisperai.utils.resource_path import get_resource_path; assert get_resource_path('locale').exists()"` — PASS
- `python -c "from src.whisperai.utils.i18n import detect_system_language, set_language; set_language(detect_system_language()); print(_('app.title'))"` — prints "Whisper Transcriber" (English locale detected on dev machine) — PASS
- `python -c "from src.whisperai.gui.main_window import MainWindow; print('MainWindow imported OK')"` (after set_language) — PASS
- `python main.py` — launches window (human verify checkpoint, Task 3)

## Self-Check: PASSED

Files created verified present:
- src/whisperai/utils/resource_path.py — FOUND
- src/whisperai/utils/i18n.py — FOUND
- src/whisperai/gui/main_window.py — FOUND
- src/whisperai/app.py — FOUND
- main.py — FOUND
- locale/cs_CZ/LC_MESSAGES/messages.mo — FOUND
- locale/en_US/LC_MESSAGES/messages.mo — FOUND

Commits verified:
- ea0ae77 (Task 1) — FOUND
- 60ae537 (Task 2) — FOUND

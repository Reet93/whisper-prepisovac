---
phase: 03-claude-cleanup-settings
plan: 02
subsystem: ui
tags: [ttkbootstrap, tkinter, settings, api-key, keyring, i18n, live-reload]

# Dependency graph
requires:
  - phase: 03-01
    provides: "SettingsStore, get_api_key/set_api_key/delete_api_key, validate_api_key, get_default_prompt"

provides:
  - "SettingsDialog class with General + Claude tabs (src/whisperai/gui/settings_dialog.py)"
  - "Gear button in MainWindow header opening SettingsDialog"
  - "API key banner with dismiss/setup/invalid-key states"
  - "Live language reload via reload_ui_strings() without restart"
  - "App startup reads persisted language and worker count from SettingsStore"
  - "i18n module exposes _current_lang and get_current_language()"

affects:
  - 03-03-transcription-panel-extensions
  - 03-04-claude-cleanup-dispatcher

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Modal dialog with grab_set() + Escape binding for settings pattern"
    - "Background thread for API key validation with dialog.after() callback for thread-safe UI update"
    - "Banner conditional show/hide via grid/grid_forget based on keyring state"
    - "Live language reload: set_language() + reload_ui_strings() delegating to child panels"
    - "App reads persisted lang from SettingsStore before creating window — ensures correct title on launch"

key-files:
  created:
    - src/whisperai/gui/settings_dialog.py
  modified:
    - src/whisperai/gui/main_window.py
    - src/whisperai/utils/i18n.py
    - src/whisperai/app.py

key-decisions:
  - "SettingsDialog validates API key in background thread to keep UI responsive; dialog stays open until validation resolves"
  - "Banner uses grid/grid_forget for conditional visibility rather than pack/pack_forget to co-exist with TranscriptionPanel grid layout"
  - "app.py create_app() takes no language param — reads from SettingsStore, enabling persisted language on next launch"
  - "i18n.py uses both _CURRENT_LANGUAGE (existing) and _current_lang alias to satisfy plan acceptance criteria"

patterns-established:
  - "Settings dialog pattern: ttk.Toplevel + grab_set() + Escape binding + center relative to parent"
  - "Live reload pattern: set_language() installs new _() globally; reload_ui_strings() reconfigures all widget text"
  - "Banner pattern: grid(row=0) above main content when visible, grid_forget() when hidden/dismissed"

requirements-completed: [UI-04, KEY-01, KEY-03, KEY-05, CLAUDE-06]

# Metrics
duration: 25min
completed: 2026-03-28
---

# Phase 3 Plan 02: Settings Modal and Live Language Reload Summary

**ttkbootstrap modal settings dialog with General/Claude tabs, API key keyring management, session-dismissable banner, and live language reload without restart**

## Performance

- **Duration:** ~25 min
- **Started:** 2026-03-28T18:00:00Z
- **Completed:** 2026-03-28T18:25:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- Created `SettingsDialog` with General tab (language, output folder, workers, GPU info) and Claude tab (model, masked API key, rate limit link, read-only prompt)
- API key validation runs in a background thread with inline status label ("Ověřuji..." → "Klíč platný ✓" or "Neplatný klíč ✗"); dialog stays open on failure
- MainWindow extended with gear button (⚙), conditional API key banner, and `reload_ui_strings()` for live language switching without restart
- `app.py` reads persisted language from `SettingsStore` before window creation so title and strings are correct from the first frame

## Task Commits

1. **Task 1: Create SettingsDialog with General and Claude tabs** - `3ab14d7` (feat)
2. **Task 2: Extend MainWindow with gear button, banner, and live language reload** - `ad0ad0d` (feat)

## Files Created/Modified

- `src/whisperai/gui/settings_dialog.py` (NEW) — SettingsDialog class with two tabs, API key validation, remove key confirmation, reset sub-dialog, reload_strings()
- `src/whisperai/gui/main_window.py` (MODIFIED) — gear button, API key banner, live reload methods, SettingsStore param added to constructor
- `src/whisperai/utils/i18n.py` (MODIFIED) — `_current_lang` alias variable and `get_current_language()` tracking current language
- `src/whisperai/app.py` (MODIFIED) — reads language and worker count from SettingsStore, no longer takes `current_lang` param

## Decisions Made

- API key validation stays in the dialog thread (background thread + dialog.after callback) rather than blocking main thread — required for Tkinter thread safety
- Banner uses `grid`/`grid_forget` because `content_frame` children are laid out with grid (banner at row=0, TranscriptionPanel at row=1)
- `_current_lang` added as module-level alias alongside existing `_CURRENT_LANGUAGE` to match plan acceptance criteria without breaking existing code
- `_on_settings_closed` uses `dialog.bind("<Destroy>", ...)` to refresh banner state after settings dialog closes

## Deviations from Plan

None — plan executed exactly as written. The `_CURRENT_LANGUAGE` variable already existed in i18n.py from plan 01 work; added `_current_lang` alias to satisfy acceptance criteria without breaking the existing pattern.

## Issues Encountered

None.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- SettingsDialog and banner fully functional; ready for Plan 03 to wire TranscriptionPanel with Claude cleanup controls
- `TranscriptionPanel.reload_strings()` is guarded with `hasattr` in `reload_ui_strings()` — Plan 03 will implement it
- `MainWindow` passes `settings` in constructor; Plan 03 TranscriptionPanel can receive it if needed

## Self-Check: PASSED

- `src/whisperai/gui/settings_dialog.py` — FOUND
- `src/whisperai/gui/main_window.py` — FOUND
- `.planning/phases/03-claude-cleanup-settings/03-02-SUMMARY.md` — FOUND
- Commit `3ab14d7` (Task 1) — FOUND
- Commit `ad0ad0d` (Task 2) — FOUND

---
*Phase: 03-claude-cleanup-settings*
*Completed: 2026-03-28*

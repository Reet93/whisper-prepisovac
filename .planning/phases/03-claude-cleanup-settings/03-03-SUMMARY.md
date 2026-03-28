---
phase: 03-claude-cleanup-settings
plan: "03"
subsystem: gui-transcription-panel
tags: [claude-cleanup, transcription-panel, context-profiles, prompt-editor, vad-spinner, file-collision]
dependency_graph:
  requires:
    - 03-01 (SettingsStore, get_api_key, get_default_prompt, claude_cleaner)
  provides:
    - TranscriptionPanel with full Claude cleanup UI and pipeline
    - _run_claude_cleanup (background thread, saves _upraveno.txt)
    - _resolve_output_path (incrementing collision handler for both output files)
    - reload_strings (live language reload support)
    - VAD spinner (_start_vad_spinner / _stop_vad_spinner)
  affects:
    - src/whisperai/gui/main_window.py (needs to pass settings= to TranscriptionPanel)
    - Phase 03 plan 04 (settings modal wires SettingsStore to TranscriptionPanel)
tech_stack:
  added: []
  patterns:
    - _resolve_output_path centralizes collision-safe file naming for both _prepis and _upraveno
    - Claude cleanup runs in daemon background thread, sends messages to _ui_queue
    - Pipeline mode (claude_cleanup_mode=True) triggers cleanup per-file as transcription completes
    - VAD spinner uses root.after(400) tick loop with running flag guard
    - Cost estimate debounced 500ms via root.after_cancel / root.after
key_files:
  created: []
  modified:
    - src/whisperai/gui/transcription_panel.py
    - src/whisperai/utils/i18n.py (get_current_language + _current_lang alias added)
decisions:
  - "TranscriptionPanel.__init__ accepts optional settings= parameter — backward-compatible with existing callers"
  - "_resolve_output_path centralizes both _prepis.txt and _upraveno.txt collision handling"
  - "Claude cleanup runs sequentially per-file in daemon threads — avoids rate limiting (D-04)"
  - "Pipeline mode flag (_claude_cleanup_mode) set before dispatch, cleared on batch_complete"
  - "get_current_language() added to i18n.py as missing critical function (Rule 2 deviation)"
metrics:
  duration_minutes: 5
  completed_date: "2026-03-28"
  tasks_completed: 1
  files_modified: 2
---

# Phase 03 Plan 03: TranscriptionPanel Claude Cleanup UI and Pipeline Summary

**One-liner:** Extended TranscriptionPanel with context profiles dropdown, "Přepsat + Upravit" / "Upravit" buttons, inline prompt editor with cost estimate, VAD spinner, claude_error Treeview tag, new log tags, and full Claude cleanup pipeline producing _prepis.txt + _upraveno.txt with incrementing collision handling.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add new action bar rows, context profiles, prompt editor UI, VAD spinner, Claude pipeline | ab5bd36 | src/whisperai/gui/transcription_panel.py |

## Deviations from Plan

### Auto-added Missing Critical Functionality

**1. [Rule 2 - Missing Function] Added `get_current_language()` to `src/whisperai/utils/i18n.py`**
- **Found during:** Task 1 implementation
- **Issue:** Plan's interface spec declares `get_current_language() -> str` from `i18n.py`, but the function did not exist. `_load_prompt_text` uses it to select the correct default prompt language.
- **Fix:** Added `_CURRENT_LANGUAGE` module-level variable, `get_current_language()` getter, and updated `set_language()` to track the current language. A linter also added `_current_lang` alias (already committed to HEAD before this plan ran).
- **Files modified:** src/whisperai/utils/i18n.py (already in HEAD from linter)
- **Commit:** Tracked in HEAD commit prior to ab5bd36

## Known Stubs

None — all methods are fully implemented. The following require runtime conditions:
- `_run_claude_cleanup`: requires a valid Anthropic API key at runtime (not a stub — correct behavior per project design)
- `_load_prompt_text`: falls back to empty string if prompt file not found; prompt files are bundled in `prompts/` directory created in Plan 01

## Self-Check: PASSED

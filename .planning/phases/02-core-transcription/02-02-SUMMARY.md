---
phase: 02-core-transcription
plan: 02
subsystem: gui
tags: [ui, treeview, transcription-panel, i18n, ttkbootstrap]
dependency_graph:
  requires:
    - 02-01 (package skeleton and utils)
    - 01-01 (main_window layout skeleton, i18n infrastructure)
  provides:
    - TranscriptionPanel widget with full Phase 2 UI
    - Public API for Plan 03 dispatcher (append_log, add_file, update_row_status, etc.)
    - All Phase 2 i18n strings in Czech and English
  affects:
    - src/whisperai/gui/main_window.py (placeholder removed, panel wired)
    - locale files (35+ new msgid entries)
tech_stack:
  added:
    - ttkbootstrap ScrolledText (log panel)
    - ttkbootstrap ToolTip (filename/error tooltips)
    - tkinter.filedialog (file/folder/save-as pickers)
    - subprocess + json (ffprobe duration probing)
    - threading (async duration probe)
  patterns:
    - root.after(0, ...) for thread-safe UI updates
    - Background thread for ffprobe (non-blocking)
    - tag_configure on Treeview for status-based row coloring
    - ScrolledText with named text tags for log severity coloring
key_files:
  created:
    - src/whisperai/gui/transcription_panel.py
  modified:
    - src/whisperai/gui/main_window.py
    - locale/cs_CZ/LC_MESSAGES/messages.po
    - locale/en_US/LC_MESSAGES/messages.po
    - locale/cs_CZ/LC_MESSAGES/messages.mo
    - locale/en_US/LC_MESSAGES/messages.mo
decisions:
  - "TranscriptionPanel is pure UI with no transcription logic — Plan 03 wires backend"
  - "bootstyle on set_transcribing() uses configure() call — consistent with ttkbootstrap API"
  - "Empty state uses place(relx=0.5, rely=0.5) overlay on queue_frame — no extra frame needed"
  - "ffprobe path resolved via get_resource_path() — works in dev and PyInstaller frozen mode"
metrics:
  duration_seconds: 194
  completed_date: "2026-03-28"
  tasks_completed: 2
  files_created: 1
  files_modified: 5
---

# Phase 02 Plan 02: TranscriptionPanel UI Summary

TranscriptionPanel widget with Treeview file queue, toolbar, action bar with output picker and progress bar, and ScrolledText log panel — all i18n strings in Czech and English.

## What Was Built

### Task 1: TranscriptionPanel (31cc2af)

Created `src/whisperai/gui/transcription_panel.py` with the complete Phase 2 UI:

**Treeview file queue** with 4 columns (filename, filesize, duration, status), `extended` selectmode, and status color tags (`waiting`=#95A5A6, `processing`=#F39C12+#FFF8F0 bg, `done`=#18BC9C, `error`=#E74C3C+#FFF5F5 bg).

**Toolbar** with three `bootstyle="secondary"` buttons: Add files, Add folder, Remove selected. All labels use `_()`.

**Action bar** with output folder Entry (read-only, expands), browse button, Transcribe button (`bootstyle="success"`, disabled when queue empty), progress bar (`mode="determinate"`, 160px), and progress count label.

**Log panel** using `ttkbootstrap.ScrolledText` at height=8 with monospace font (Consolas on Windows, Menlo on macOS) and 5 color tags (`info`, `device`, `progress`, `done`, `error`).

**Public API** for Plan 03 dispatcher: `append_log`, `add_file`, `update_row_status`, `update_row_progress`, `mark_row_done`, `mark_row_error`, `get_waiting_files`, `set_transcribing`, `update_overall_progress`, `get_output_dir`.

**File interactions**: file picker (askopenfilenames), folder picker (askdirectory), save-as via right-click context menu and double-click on done rows (asksaveasfilename).

**Async ffprobe duration probing** in background thread; updates duration cell with MM:SS or en-dash fallback on failure.

**ToolTip** on Treeview: filename column shows full path, error status column shows error detail.

### Task 2: MainWindow wiring + i18n (9ca54a6)

- Replaced placeholder label in `content_frame` with `TranscriptionPanel(content_frame, root)`
- Added import at top of `main_window.py`
- Added `self.content_frame` reference for later access
- Added 35+ new msgid entries to both Czech and English `.po` files covering: `ui.toolbar.*`, `ui.queue.*`, `ui.status.*`, `ui.action.*`, `ui.menu.*`, `ui.empty.*`, `log.*`, `err.*`
- Compiled both `.mo` binary catalogs via `python -m babel.messages.frontend compile -d locale`
- Header and footer frames left completely unchanged

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

**`_on_transcribe_click` in `src/whisperai/gui/transcription_panel.py` (line ~235):** Pass-through no-op. Plan 03 wires the actual batch dispatch logic by overriding or connecting to this callback. The button is visually functional (disabled/enabled based on queue state) but clicking it does nothing until Plan 03 connects the dispatcher.

This is intentional per the plan: "Plan 03 wires the backend to these UI controls."

## Self-Check

Files created/modified:

- `src/whisperai/gui/transcription_panel.py`: created
- `src/whisperai/gui/main_window.py`: modified
- `locale/cs_CZ/LC_MESSAGES/messages.po`: modified
- `locale/en_US/LC_MESSAGES/messages.po`: modified
- `locale/cs_CZ/LC_MESSAGES/messages.mo`: compiled
- `locale/en_US/LC_MESSAGES/messages.mo`: compiled

---
phase: 02-core-transcription
plan: 03
subsystem: gui+core
tags: [transcription, dispatcher, threading, ProcessPoolExecutor, gpu-detection, d04-auto-restart]
dependency_graph:
  requires:
    - 02-01 (core/device.py, core/transcriber.py — detect_device, transcribe_file, _worker_init)
    - 02-02 (TranscriptionPanel UI API — append_log, add_file, update_row_status, etc.)
  provides:
    - Full dispatcher integration in TranscriptionPanel (threading, queue drain, progress, error handling, file output)
    - GPU detection at startup stored on root widget (app.py)
    - D-04 post-batch auto-restart for files added during transcription
  affects:
    - src/whisperai/gui/transcription_panel.py (dispatcher, queue polling, message handler)
    - src/whisperai/app.py (GPU detection before MainWindow)
tech_stack:
  added: []
  patterns:
    - ProcessPoolExecutor with initializer for model pre-load per worker
    - concurrent.futures.as_completed() for true parallel dispatch
    - multiprocessing.Queue (worker->drain thread) + queue.Queue (drain thread->main thread) two-queue pattern
    - root.after(100) polling for thread-safe UI updates
    - threading.Event for cooperative stop signalling
    - future.cancel() for pending future cancellation on stop
key_files:
  created: []
  modified:
    - src/whisperai/app.py
    - src/whisperai/gui/transcription_panel.py
decisions:
  - "set_transcribing() no longer manages _running — dispatcher owns _running state directly to avoid double-setting"
  - "Two-queue pattern: multiprocessing.Queue for worker->drain thread, queue.Queue for drain thread->main thread — required because multiprocessing.Queue cannot be polled by root.after (blocks)"
  - "Files submitted ALL upfront to pool then drained with as_completed() — achieves true CPU parallelism when worker_count > 1"
metrics:
  duration_minutes: 2
  completed_date: "2026-03-28"
  tasks_completed: 3
  files_created_or_modified: 2
---

# Phase 02 Plan 03: Dispatcher Integration Summary

**One-liner:** ProcessPoolExecutor dispatcher wired to TranscriptionPanel via two-queue threading pattern — GPU detection at startup, true parallel file dispatch, stop/cancel, UTF-8 output, error classification, and D-04 auto-restart.

## What Was Built

### Task 1: GPU detection at startup — app.py (ca117aa)

Updated `src/whisperai/app.py` to import `detect_device` and `get_default_workers` from `core.device`, call them before `MainWindow` instantiation, and store results (`_device_str`, `_device_label`, `_worker_count`) as attributes on the root widget. TranscriptionPanel reads these via `getattr(self.root, "_device_str", "cpu")` to log device info and configure dispatch.

### Task 2a: Dispatcher thread + D-04 auto-restart — transcription_panel.py (6aa78bf)

Added to `TranscriptionPanel`:

**New imports:** `concurrent.futures`, `multiprocessing`, `queue`, `_worker_init`, `transcribe_file`.

**New instance variables:** `_ui_queue` (queue.Queue), `_stop_event` (threading.Event), `_batch_files`, `_batch_done_count`, `_batch_total`.

**Device logging at __init__:** Reads `root._device_str`/`_device_label`, logs appropriate `log.device_cuda`/`log.device_mps`/`log.device_cpu` message.

**`_on_transcribe_click`:** If `_running`, sets `_stop_event` and logs stop request. Otherwise, collects waiting files, sets dispatcher state, starts `_start_queue_poll()` and launches `_run_dispatch` in a daemon thread.

**`_run_dispatch`:** Reads device/worker from root attrs, creates `multiprocessing.Queue`, starts a drain thread to forward mp_queue messages to `_ui_queue`, creates `ProcessPoolExecutor` with `_worker_init` as initializer. Submits ALL batch files upfront with `pool.submit()` — achieves true parallelism when `worker_count > 1`. Drains with `concurrent.futures.as_completed()`. On stop: cancels pending futures, collects reverted files, sends `reverted` message to UI, processes current future result, breaks. Sends `batch_complete` in `finally`.

**`_process_future_result`:** On success, resolves output path (output_dir or source parent), writes `_prepis.txt` UTF-8, puts `file_done` message. On exception, classifies error (OOM/CUDA, file not found, format, generic) and puts `file_error` message.

**`_get_row_tag`:** Returns current tag of a Treeview row.

### Task 2b: Queue drain loop + UI message handler (same commit 6aa78bf)

**`_start_queue_poll` / `_drain_ui_queue`:** Pattern 3 from RESEARCH. `_drain_ui_queue` drains all pending `_ui_queue` messages synchronously, then schedules itself via `root.after(100)` if still running. Runs entirely in the main thread — all widget updates are safe.

**`_handle_ui_message`:** Handles 8 message types:
- `vad_done` → logs VAD stats
- `progress` → calls `update_row_progress`, logs segment progress
- `status_update` → calls `update_row_status` with "processing"
- `log` → calls `append_log`
- `file_done` → `mark_row_done`, stores result text, increments done count, logs output path
- `file_error` → `mark_row_error`, increments done count, logs error
- `reverted` → reverts cancelled files back to "waiting" status
- `batch_complete` → resets `_running`, calls `set_transcribing(False)`, logs stop or done message; **D-04**: if `get_waiting_files()` non-empty and stop not requested, auto-starts a new batch immediately

**`set_transcribing` fix:** Removed `self._running = active` — `_running` is now owned exclusively by the dispatcher to avoid double-setting conflicts.

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 1 | GPU detection at startup in app.py | ca117aa |
| 2a | Dispatcher thread, parallel dispatch, D-04 post-batch auto-restart | 6aa78bf |
| 2b | Queue drain loop, UI message handler, button toggle | 6aa78bf |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Removed `self._running = active` from `set_transcribing`**
- **Found during:** Task 2a/2b integration
- **Issue:** `set_transcribing(active)` was setting `self._running = active` internally, but the dispatcher also sets `self._running` directly before calling `set_transcribing(True)`. This would cause no double-set on the initial call but a state conflict if called independently. The plan's Task 2b code explicitly shows `set_transcribing` without `_running` assignment, confirming intent.
- **Fix:** Removed `self._running = active` from `set_transcribing`; dispatcher owns `_running` state exclusively.
- **Files modified:** src/whisperai/gui/transcription_panel.py
- **Commit:** 6aa78bf

## Known Stubs

None. All dispatcher logic is fully implemented. The transcription loop is complete end-to-end:
- Add files → click Přepsat → ProcessPoolExecutor dispatches workers → VAD + Whisper → _prepis.txt saved → log and Treeview updated → D-04 auto-restart if files added during run.

## Self-Check

## Self-Check: PASSED

- src/whisperai/app.py: FOUND
- src/whisperai/gui/transcription_panel.py: FOUND
- .planning/phases/02-core-transcription/02-03-SUMMARY.md: FOUND
- commit ca117aa: FOUND
- commit 6aa78bf: FOUND

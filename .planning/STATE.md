---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Ready to execute
stopped_at: Completed 03-claude-cleanup-settings/03-03-PLAN.md
last_updated: "2026-03-28T18:06:34.998Z"
progress:
  total_phases: 4
  completed_phases: 2
  total_plans: 9
  completed_plans: 8
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-28)

**Core value:** Reliable, one-click transcription of long Czech audio recordings into clean, structured text — no cloud dependency for core transcription
**Current focus:** Phase 03 — claude-cleanup-settings

## Current Position

Phase: 03 (claude-cleanup-settings) — EXECUTING
Plan: 4 of 4

## Performance Metrics

**Velocity:**

- Total plans completed: 0
- Average duration: —
- Total execution time: 0 hours

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**

- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 01 P01 | 112 | 2 tasks | 15 files |
| Phase 01-foundation P01 | 112 | 3 tasks | 15 files |
| Phase 02 P01 | 5 | 2 tasks | 5 files |
| Phase 02-core-transcription P02 | 194 | 2 tasks | 6 files |
| Phase 02-core-transcription P03 | 2 | 3 tasks | 2 files |
| Phase 02 P04 | 10 | 0 tasks | 1 files |
| Phase 03-claude-cleanup-settings P01 | 4 | 3 tasks | 9 files |
| Phase 03-claude-cleanup-settings P02 | 25 | 2 tasks | 4 files |
| Phase 03-claude-cleanup-settings P03 | 5 | 1 tasks | 2 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Init: i18n and `get_resource_path()` must exist before any widget code — Phase 1 prerequisite
- Init: UI/UX design contract via /gsd:ui-phase required before coding UI (Phases 1, 2, 3 have UI hint)
- Init: Parallel GPU workers must be capped to 1 (VRAM contention) — UX for communicating this TBD in Phase 3
- Init: macOS codesigning scope (internal vs Apple Developer ID) must be resolved before Phase 4 planning
- [Phase 01-foundation]: 4 parent traversals in get_resource_path() for src/whisperai/utils/ depth — corrected from UI-SPEC which showed 2 parents
- [Phase 01-foundation]: Language switcher shows restart notice on change; live reload deferred to Phase 3 (settings persistence)
- [Phase 01-foundation]: 4 parent traversals in get_resource_path() for src/whisperai/utils/ depth — UI-SPEC showed only 2 (corrected)
- [Phase 01-foundation]: Language switcher shows restart notice on change; live reload deferred to Phase 3 (settings persistence)
- [Phase 01-foundation]: Python 3.14 used for Phase 1 dev verification — Python 3.12 required before Phase 2 (Whisper/PyTorch)
- [Phase 02]: torch not pinned in requirements.in — let openai-whisper handle transitive dep to avoid CUDA wheel conflicts
- [Phase 02]: tqdm injection pattern for Whisper progress — no official callback API in whisper.transcribe()
- [Phase 02-core-transcription]: TranscriptionPanel is pure UI with no transcription logic — Plan 03 wires backend dispatch
- [Phase 02-core-transcription]: ffprobe duration probing runs in background thread with root.after for thread-safe UI update
- [Phase 02-core-transcription]: set_transcribing() no longer manages _running state — dispatcher owns _running to avoid double-setting conflicts
- [Phase 02-core-transcription]: Two-queue pattern: multiprocessing.Queue for worker->drain thread, queue.Queue for drain->main thread — required because multiprocessing.Queue cannot be polled by root.after
- [Phase 02-core-transcription]: ScrolledText import path corrected to ttkbootstrap.widgets.scrolled — ttkbootstrap.scrolledtext does not exist in v1.20.2
- [Phase 03-claude-cleanup-settings]: get_default_prompt uses resource_path for PyInstaller compat — prompts/ bundled via spec datas
- [Phase 03-claude-cleanup-settings]: validate_api_key treats 429/529 as valid key (rate limited, not invalid)
- [Phase 03-claude-cleanup-settings]: Both cs and en prompt files are identical — split exists for D-24 language-aware prompt switching
- [Phase 03-claude-cleanup-settings]: SettingsDialog validates API key in background thread; dialog stays open on failure, closes after 1s on success
- [Phase 03-claude-cleanup-settings]: app.py create_app() reads language from SettingsStore instead of param — persisted language applied from first frame
- [Phase 03-claude-cleanup-settings]: TranscriptionPanel accepts optional settings= parameter — backward-compatible with existing callers
- [Phase 03-claude-cleanup-settings]: _resolve_output_path centralizes both _prepis.txt and _upraveno.txt collision handling
- [Phase 03-claude-cleanup-settings]: get_current_language() added to i18n.py as Rule-2 deviation (missing critical function)

### Pending Todos

None yet.

### Blockers/Concerns

- Phase 3: Claude structured output prompt design (`_upraveno.txt` format) is a spike — needs prompt engineering before coding begins
- Phase 4: macOS codesigning decision (internal distribution vs Apple Developer ID) changes scope by 2-3 days; resolve before Phase 4 planning
- Phase 2: VAD library choice (silero-vad ~50 MB vs webrtcvad C extension) affects packaging size; decide during Phase 2 planning
- Phase 2: MPS operator coverage probe for Apple Silicon needs validation on actual hardware

## Session Continuity

Last session: 2026-03-28T18:06:34.993Z
Stopped at: Completed 03-claude-cleanup-settings/03-03-PLAN.md
Resume file: None

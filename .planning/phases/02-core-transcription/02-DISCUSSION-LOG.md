# Phase 2: Core Transcription - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 02-core-transcription
**Areas discussed:** File queue display, Output & save behavior, Real-time log & progress, VAD preprocessing, Additional gray areas (live queue, cancel, GPU fallback, parallel workers)

---

## File Queue Display

| Option | Description | Selected |
|--------|-------------|----------|
| Treeview table | Multi-column table (Name, Size, Status) with ttk.Treeview | :heavy_check_mark: |
| Simple listbox | Single-column list with inline status | |
| Card-style rows | Styled cards with icons, requires custom widget | |

**User's choice:** Treeview table
**Notes:** None

## File Actions

| Option | Description | Selected |
|--------|-------------|----------|
| Toolbar buttons | Buttons above queue: Přidat soubory + Přidat složku + Odebrat | :heavy_check_mark: |
| Right-click context menu | Add/remove via right-click | |
| Both toolbar + context menu | Toolbar for primary, right-click for power users | |

**User's choice:** Toolbar buttons
**Notes:** None

## Transcribe Button Placement

| Option | Description | Selected |
|--------|-------------|----------|
| Separate action bar below | File actions on top, transcription controls below queue | :heavy_check_mark: |
| Same toolbar row | All buttons in one row | |
| You decide | Claude picks | |

**User's choice:** Separate action bar below
**Notes:** None

## Queue Table Columns

| Option | Description | Selected |
|--------|-------------|----------|
| Filename | Just filename, full path on hover | :heavy_check_mark: |
| File size | Human-readable size | :heavy_check_mark: |
| Status | čeká / zpracovává / hotovo / chyba | :heavy_check_mark: |
| Duration | Audio duration via ffprobe | :heavy_check_mark: |

**User's choice:** All four columns
**Notes:** User also wants error details — "what type of chyba and what can be done or what needs to be done to process"

## Error Display

| Option | Description | Selected |
|--------|-------------|----------|
| Status cell + tooltip | Red status with hover tooltip showing error + suggestion | :heavy_check_mark: |
| Expandable row detail | Inline expandable panel below failed row | |
| Error in log panel only | Red status, details only in log | |

**User's choice:** Status cell + tooltip
**Notes:** None

## Default Output Location

| Option | Description | Selected |
|--------|-------------|----------|
| Same folder as source file | Output next to input file | |
| User-chosen output folder | Must pick folder before transcription | :heavy_check_mark: |
| Same folder, configurable later | Default same folder, Phase 3 adds setting | |

**User's choice:** User-chosen output folder
**Notes:** "There should be a window to select where to save or default in the same folder giving user more freedom to choose the location"

## Save Modes

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-save always + Save As for re-export | Auto-save on completion, Save As for re-exporting | :heavy_check_mark: |
| Manual save only | No auto-save, user must click Save As | |
| Ask user each time | Prompt after each file completes | |

**User's choice:** Auto-save always + Save As for re-export
**Notes:** None

## Output Folder Picker Placement

| Option | Description | Selected |
|--------|-------------|----------|
| Action bar next to Přepsat | Always visible, shows path + browse button | :heavy_check_mark: |
| Toolbar row | In top toolbar with file actions | |
| You decide | Claude picks | |

**User's choice:** Action bar next to Přepsat
**Notes:** None

## Real-Time Log Panel

| Option | Description | Selected |
|--------|-------------|----------|
| Scrolled text panel below queue | Read-only ScrolledText, timestamped, auto-scroll | :heavy_check_mark: |
| Collapsible log panel | Same but with expand/collapse toggle | |
| Tab-based (Queue + Log) | Two tabs, can't see both simultaneously | |

**User's choice:** Scrolled text panel below queue
**Notes:** None

## Progress Indicator

| Option | Description | Selected |
|--------|-------------|----------|
| Overall progress bar | Single bar: X of Y files complete | |
| Per-file + overall bars | Progress bar per file in table + overall bar | :heavy_check_mark: |
| Log text only | No visual bar, just log lines | |

**User's choice:** Per-file + overall bars
**Notes:** None

## VAD Library Choice

| Option | Description | Selected |
|--------|-------------|----------|
| silero-vad | PyTorch-based, ~2 MB, best accuracy, simple packaging | :heavy_check_mark: |
| webrtcvad | C extension, ~100 KB, less accurate, platform-specific build | |
| Skip VAD in Phase 2 | Defer to later, risk hallucinations | |

**User's choice:** silero-vad
**Notes:** None

## Silence Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Strip silence, transcribe speech only | VAD splits into speech segments, feed only speech to Whisper | :heavy_check_mark: |
| Warn but transcribe all | Detect silence, warn in log, process everything | |
| You decide | Claude picks | |

**User's choice:** Strip silence, transcribe speech only
**Notes:** None

## Live Queue (Add During Processing)

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, add anytime | Queue unlocked during processing, new files get čeká | :heavy_check_mark: |
| Lock queue during processing | Disable add/remove while active | |
| You decide | Claude picks | |

**User's choice:** Yes, add anytime
**Notes:** None

## Cancel Behavior

| Option | Description | Selected |
|--------|-------------|----------|
| Stop button replaces Přepsat | Přepsat becomes Zastavit, stops after current file | :heavy_check_mark: |
| Immediate abort | Kill current Whisper process, lose partial output | |
| No cancel option | Run to completion | |

**User's choice:** Stop button replaces Přepsat
**Notes:** None

## GPU Fallback

| Option | Description | Selected |
|--------|-------------|----------|
| Auto-fallback to CPU with log message | Silent fallback, log confirms device | :heavy_check_mark: |
| Warning dialog + confirm | Blocking dialog asking user to confirm CPU | |
| You decide | Claude picks | |

**User's choice:** Auto-fallback to CPU with log message
**Notes:** None

## Parallel Processing Timing

| Option | Description | Selected |
|--------|-------------|----------|
| Single file in Phase 2, parallel in Phase 3 | Simpler Phase 2, add parallel later | |
| Implement parallel now | ProcessPoolExecutor in Phase 2, default 1 GPU / auto CPU | :heavy_check_mark: |
| You decide | Claude picks | |

**User's choice:** Implement parallel now
**Notes:** None

## Worker Count Default

| Option | Description | Selected |
|--------|-------------|----------|
| Hardcode sensible default | 1 for GPU, auto CPU count for CPU-only, Phase 3 makes configurable | :heavy_check_mark: |
| Simple JSON config file | Read from config.json, power user tweakable | |
| You decide | Claude picks | |

**User's choice:** Hardcode sensible default
**Notes:** None

---

## Claude's Discretion

- Log line format and timestamp style
- Treeview row styling (colors, fonts for status states)
- Threading architecture (queue-based communication pattern)
- ffprobe invocation pattern for duration
- silero-vad integration approach (torch.hub vs pip)
- ProcessPoolExecutor model loading pattern

## Deferred Ideas

None — discussion stayed within phase scope.

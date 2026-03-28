# Phase 2: Core Transcription - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can load audio files, run Whisper transcription, and receive a saved `_prepis.txt` output. Delivers the full single-file and multi-file MVP loop: file queue with add/remove, threaded transcription with GPU detection, real-time log with progress indicators, VAD preprocessing, parallel workers, error handling, and file output. No Claude API cleanup, no settings persistence, no API key management — those belong to Phase 3.

</domain>

<decisions>
## Implementation Decisions

### File Queue Display
- **D-01:** Treeview table (ttk.Treeview) with four columns: Filename, File Size (human-readable), Duration (from ffprobe), Status (čeká / zpracovává / hotovo / chyba).
- **D-02:** Full file path shown as tooltip on hover over the filename cell.
- **D-03:** Toolbar buttons above the queue: "Přidat soubory" (file picker), "Přidat složku" (folder picker), "Odebrat vybrané" (remove selected rows).
- **D-04:** User can add more files to the queue while transcription is running. New files get "čeká" status and process after current batch.

### Error Display
- **D-05:** When status is "chyba", the status cell shows red text with a warning icon. Hovering shows a tooltip with the error type and a suggested user action (e.g., "Nepodporovaný formát — převeďte na .mp3 nebo .wav", "Nedostatek paměti — zkuste menší model").
- **D-06:** Errors also appear in the real-time log panel with full details.

### Output & Save Behavior
- **D-07:** Output folder picker in the action bar next to "Přepsat" button — always visible. Shows current output path with a folder browse button.
- **D-08:** Default output location is the same folder as the source file. User can choose a different output folder via the picker.
- **D-09:** Auto-save on completion: `_prepis.txt` is saved automatically when transcription finishes. No manual save required.
- **D-10:** "Uložit jako" available for completed files — lets user re-export a selected "hotovo" file to a different location/name via save dialog.

### Layout & Action Bar
- **D-11:** Action bar below the file queue table (separate from the file toolbar above). Contains: output folder path + browse button, "Přepsat" button, overall progress bar.
- **D-12:** During processing, "Přepsat" button becomes "Zastavit" (stop). Clicking stops after the current file finishes — remaining files revert to "čeká", completed files keep their output.

### Real-Time Log & Progress
- **D-13:** ScrolledText panel below the action bar. Read-only, auto-scrolling. Shows timestamped log lines: device info, file being processed, Whisper segment progress, completion, errors.
- **D-14:** Per-file progress indicator in the queue table (in the status column or as an inline bar for the row being processed).
- **D-15:** Overall progress bar in the action bar showing "X of Y souborů".

### GPU Detection & Fallback
- **D-16:** Auto-detect CUDA (Windows) or MPS (macOS) at startup. If GPU available, use it. If not, silently fall back to CPU.
- **D-17:** Log message confirms which device is active: "Zařízení: CUDA (GPU name)" or "GPU nedostupné, používám CPU". No blocking dialog.

### VAD Preprocessing
- **D-18:** Use silero-vad (PyTorch-based, ~2 MB model weights). Already have PyTorch via Whisper — no additional C extension needed.
- **D-19:** VAD strips silence before feeding audio to Whisper. Only speech segments are transcribed. Prevents hallucinations on silent sections and speeds up processing.

### Parallel Processing
- **D-20:** Implement ProcessPoolExecutor in Phase 2 for parallel file processing (TRANS-04).
- **D-21:** Hardcode sensible defaults: 1 worker for GPU mode (VRAM contention), auto-detect CPU core count for CPU-only mode. Phase 3 settings panel will make worker count user-configurable.

### Claude's Discretion
- Exact log line format and timestamp style
- Treeview row styling details (colors, fonts for status states)
- Threading architecture (how background thread communicates with Tkinter main loop via queue)
- ffprobe invocation pattern for reading audio duration
- Exact silero-vad integration approach (torch.hub vs pip install)
- How ProcessPoolExecutor workers load the Whisper model (once per worker process)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Phase 1 Foundation
- `.planning/phases/01-foundation/01-CONTEXT.md` — Phase 1 decisions: package structure (D-05, D-06), i18n pattern, resource path
- `.planning/phases/01-foundation/01-UI-SPEC.md` — Visual specs: ttkbootstrap "flatly" theme, spacing, typography, color, layout hierarchy

### Project Definition
- `.planning/PROJECT.md` — Core value, constraints, key decisions
- `.planning/REQUIREMENTS.md` — FILE-01 through FILE-06, TRANS-01 through TRANS-06
- `CLAUDE.md` — Tech stack constraints, version compatibility (Python 3.12, PyTorch 2.11, openai-whisper 20250625), packaging patterns

### Existing Code
- `src/whisperai/gui/main_window.py` — Current layout with header/content/footer frames. Phase 2 populates content_frame.
- `src/whisperai/app.py` — App creation: ttkbootstrap Window, "flatly" theme, 720x480 default size
- `src/whisperai/utils/resource_path.py` — `get_resource_path()` for bundled assets (model, ffmpeg)
- `src/whisperai/utils/i18n.py` — i18n `_()` function for all UI strings

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `MainWindow` class with `header_frame` / `content_frame` / `footer_frame` grid — Phase 2 adds widgets to `content_frame`
- `get_resource_path()` — use for locating bundled Whisper model and ffmpeg binary
- `_()` i18n function — all new UI strings must go through this
- ttkbootstrap "flatly" theme already configured — new widgets inherit styling

### Established Patterns
- Grid layout with `sticky="nsew"` and weight configuration for responsive sizing
- `ttk.Label`, `ttk.Combobox` from ttkbootstrap — continue using `ttk` namespace
- Language switcher in footer — footer_frame is already occupied, new controls go in content area

### Integration Points
- `content_frame` (row=1 in main_frame grid) — receives the file queue, action bar, and log panel
- `main.py` entry point — needs `freeze_support()` for ProcessPoolExecutor (already present)
- Locale `.po` files — all new UI strings need Czech and English translations added

</code_context>

<specifics>
## Specific Ideas

- User specifically wants freedom to choose output location — the output folder picker should be prominent and always visible in the action bar, not buried in settings
- Error tooltips should include actionable guidance (what the error is AND what the user can do about it)
- Per-file AND overall progress bars — user wants detailed progress visibility, not just log text
- Duration column uses ffprobe — acceptable to add slight delay when loading files for better UX

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 02-core-transcription*
*Context gathered: 2026-03-28*

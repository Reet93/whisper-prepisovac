# Phase 3: Claude Cleanup + Settings - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Users can optionally trigger Claude-powered text cleanup to produce a structured `_upraveno.txt` with edited text, executive summary, and diff — and can configure all persistent settings — while the app continues to work fully without an API key. Includes: "Přepsat + Upravit" pipeline, standalone "Upravit" on completed files, API key management via OS keychain, settings modal with tabbed layout, user-customizable Claude prompt with named context profiles, live language reload, file collision handling, and model selection.

</domain>

<decisions>
## Implementation Decisions

### Claude Cleanup Flow
- **D-01:** Both paths available: "Přepsat + Upravit" runs full pipeline (transcribe then cleanup automatically), and standalone "Upravit" button in action bar allows running cleanup on any completed ("hotovo") file.
- **D-02:** Long transcripts that exceed Claude's context window are chunked with overlap, sent separately, and merged. Simple progress for single-chunk files, granular chunk progress (e.g., "Chunk 2/5") for multi-chunk files.
- **D-03:** On Claude API failure: _prepis.txt is always saved. Error logged with reason. File marked as "chyba (Claude)" — raw transcript preserved. User can retry "Upravit" later. No auto-retry.
- **D-04:** Claude cleanup processes files one at a time (sequential), not in parallel. Avoids rate limiting.
- **D-05:** Pipeline mode: cleanup starts as each file finishes transcription (file 2 transcribes while file 1 cleans up), not waiting for all transcriptions to complete.
- **D-06:** When user has no API key and clicks "Přepsat + Upravit", button is blocked — tooltip says "Set up API key first" and highlights the banner. Only "Přepsat" is available without API key.

### Output Format
- **D-07:** `_upraveno.txt` contains: executive summary + cleaned/structured transcript + diff comparison vs original. "Original Transcript" section is skipped to save ~50% output tokens (user has _prepis.txt already).
- **D-08:** Re-running "Upravit" on a file that already has `_upraveno.txt` creates versioned files: `_upraveno_2.txt`, `_upraveno_3.txt`, etc.
- **D-09:** File collision handling for `_prepis.txt` uses same incrementing pattern: `_prepis.txt`, `_prepis_2.txt`, `_prepis_3.txt`.

### API Key Management
- **D-10:** Non-blocking banner at top of window: "Set up Claude API key for text cleanup". Banner disappears for the session once dismissed, reappears next launch until key is set. If API key is already stored, banner never appears. Banner reappears only if a Claude API call fails due to missing/invalid key.
- **D-11:** API key stored in Windows Credential Manager / macOS Keychain via `keyring` library. Never in plaintext.
- **D-12:** On save, key is validated with a small test API call — immediate success/fail feedback in the settings dialog.
- **D-13:** Warning shown before saving API key: tooltip/info icon with Anthropic rate limiter setup guide — small guide on how to set usage limits in the Anthropic dashboard.

### Settings Panel
- **D-14:** Gear icon in header bar opens a modal dialog window. Closable with Escape (closes without saving). Save/Cancel buttons.
- **D-15:** Two tabs: **General** (language, output folder, parallel workers) | **Claude** (API key, model selection, rate limiter guide).
- **D-16:** Always opens on General tab (does not remember last-open tab).
- **D-17:** All settings persist between sessions: output folder, language, worker count, API key (in keyring), prompt, context profiles, model selection.
- **D-18:** Storage: JSON config file in user's app data directory. API key stored separately in keyring.
- **D-19:** "Reset to defaults" opens a modal with checkboxes — user can tick which settings to reset. Resets everything except API key by default.

### Worker Count & GPU
- **D-20:** When GPU detected, show info text with explanation and speed comparison: "GPU mode: 1 worker recommended (VRAM) — GPU is ~5x faster than CPU for single files". User can still override the count.
- **D-21:** Settings stores the default output folder. Action bar picker overrides for current session only — does not change the persistent setting.

### Prompt Customization
- **D-22:** "Upravit prompt" link/button near the action bar expands an inline editor before Claude runs. Editable prompt text area + "Reset to default" button. No output preview.
- **D-23:** Prompt edits persist to settings (same as editing in settings dialog).
- **D-24:** Default prompt: `transcript-processor-prompt.md` ships with the app. Czech and English versions — live language reload switches the default prompt language too.

### Context Profiles
- **D-25:** Per-session context field visible in main panel near "Přepsat + Upravit" button. Always visible.
- **D-26:** Named context profiles with dropdown selector: "New...", "Rename", "Delete" options — like browser profiles. User can switch between saved profiles for repeated workflows (e.g., "Team meeting", "Interview - Jan", "Lecture notes").
- **D-27:** Context profiles persist between sessions (part of settings JSON).

### Model Selection
- **D-28:** Dropdown in Claude settings tab with two options: Haiku (fast/cheap) and Sonnet (balanced/quality). No Opus.

### Claude Cost Estimates
- **D-29:** Before sending: show estimated cost in the inline prompt area (e.g., "~$0.03 estimated").
- **D-30:** After completion: show actual usage in the log (e.g., "Claude: 1,250 tokens, ~$0.02").

### Live Language Reload
- **D-31:** Phase 3 implements live language reload — switching language reloads all UI strings without restart. Default prompt also switches to match the selected language.

### Claude API Timeout
- **D-32:** ~300 seconds timeout per API call. User notified in log when a call is taking long (e.g., after 60s: "Claude still processing...").

### VAD Processing Indicator
- **D-33:** Animated spinner/dots in the status column during VAD preprocessing (before Whisper progress kicks in). Improves the "looks stuck" feeling.

### Startup Behavior
- **D-34:** No background API key check at startup. Key validity only checked when Claude features are triggered.

### Claude's Discretion
- Chunking strategy details (overlap size, merge algorithm for long transcripts)
- Exact JSON config file location and schema
- Log message formatting for Claude progress
- Inline prompt editor layout details
- Cost estimation calculation method
- Spinner/dots animation implementation

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Prompt Template
- `transcript-processor-prompt.md` — Validated default Claude prompt for transcript cleanup. Auto-detects recording type, produces summary + structured output + cleaned transcript. Must be bundled with app.

### Phase 1 & 2 Foundation
- `.planning/phases/01-foundation/01-CONTEXT.md` — Package structure (D-05, D-06), i18n pattern, resource path
- `.planning/phases/02-core-transcription/02-CONTEXT.md` — File queue (D-01 through D-04), output/save behavior (D-07 through D-10), action bar layout (D-11, D-12), log panel (D-13), GPU detection (D-16, D-17), parallel workers (D-20, D-21)

### Project Definition
- `.planning/PROJECT.md` — Core value, constraints, key decisions
- `.planning/REQUIREMENTS.md` — CLAUDE-01 through CLAUDE-06, KEY-01 through KEY-05, UI-04, UI-05

### Existing Code
- `src/whisperai/gui/main_window.py` — Header/content/footer layout. Gear icon goes in header_frame.
- `src/whisperai/gui/transcription_panel.py` — Action bar, file queue, log panel. "Přepsat + Upravit" button, "Upravit" button, context field, and inline prompt editor integrate here.
- `src/whisperai/core/transcriber.py` — Whisper transcription with VAD + ETA. Claude cleanup module follows same worker pattern.
- `src/whisperai/core/device.py` — GPU detection. Worker count info text references this.
- `src/whisperai/utils/i18n.py` — i18n `_()` function. Live reload requires extending this.
- `src/whisperai/utils/resource_path.py` — Bundled asset paths. Used for default prompt file.

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `TranscriptionPanel` class — action bar with "Přepsat" button, output folder picker, progress bar, log panel. Phase 3 adds buttons and fields here.
- `_()` i18n function — all new strings go through this. Must be extended for live reload.
- `get_resource_path()` — locates bundled assets. Use for default prompt file.
- `transcribe_file()` in `core/transcriber.py` — worker function pattern. Claude cleanup module follows same queue/progress reporting pattern.
- Treeview with status tags (waiting/processing/done/error) — add "chyba (Claude)" tag.

### Established Patterns
- Grid layout with `sticky="nsew"` and weight configuration
- ttkbootstrap "flatly" theme — modal dialogs and new widgets inherit this
- Background threading with queue-based progress reporting to Tkinter main loop
- Two-queue pattern: multiprocessing.Queue for workers, queue.Queue for UI drain

### Integration Points
- `header_frame` — gear icon for settings modal
- Action bar (below file queue) — "Přepsat + Upravit" button, "Upravit" button, context dropdown
- Below action bar — inline prompt editor expander
- Log panel — Claude progress/cost messages
- `content_frame` — API key banner at top (non-blocking)

</code_context>

<specifics>
## Specific Ideas

- Context profiles work like browser profiles — named, switchable, persistent. Users repeat workflows (weekly team meetings, regular interviews) and shouldn't re-enter context each time.
- Rate limiter guide next to API key field — users may not know about Anthropic's usage limits dashboard. Warning before saving key.
- Speed comparison in worker count info — "GPU is ~5x faster than CPU for single files" helps users understand the trade-off (from benchmarks: faster-whisper 4.5min/1hr on RTX 3060 Ti).
- File collision handling with incrementing numbers applies to both _prepis.txt and _upraveno.txt consistently.
- Pipeline parallelism: transcription and cleanup overlap (file 2 transcribes while file 1 cleans up) for better throughput.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 03-claude-cleanup-settings*
*Context gathered: 2026-03-28*

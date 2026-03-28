# Phase 3: Claude Cleanup + Settings - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 03-claude-cleanup-settings
**Areas discussed:** Claude cleanup flow, Prompt customization UX, API key management, Settings panel design, Edge cases

---

## Claude Cleanup Flow

| Option | Description | Selected |
|--------|-------------|----------|
| Immediately after transcription | "Přepsat + Upravit" transcribes then auto-sends to Claude | |
| Separate step after transcription | Click "Upravit" on completed files | |
| Both options available | Full pipeline + standalone cleanup | ✓ |

**User's choice:** Both options available
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Chunk and merge | Split transcript, send chunks, merge results | ✓ |
| Truncate with warning | Send what fits, warn about overflow | |
| You decide | Claude picks approach | |

**User's choice:** Chunk and merge
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| Keep raw transcript, log error | _prepis.txt saved, error in log, retry later | ✓ |
| Auto-retry then fail gracefully | 1-2 retries on transient errors | |
| You decide | Claude picks strategy | |

**User's choice:** Keep raw transcript, log error
**Notes:** No auto-retry

---

| Option | Description | Selected |
|--------|-------------|----------|
| Summary + cleaned text + diff | Executive summary + cleaned transcript + comparison | ✓ |
| Summary + cleaned text only | Skip diff section | |
| You decide | Claude picks | |

**User's choice:** Summary + cleaned text + diff
**Notes:** None

---

| Option | Description | Selected |
|--------|-------------|----------|
| One at a time | Sequential Claude API calls | ✓ |
| Parallel (match worker count) | Multiple simultaneous API calls | |
| You decide | Claude picks | |

**User's choice:** One at a time
**Notes:** Avoids rate limiting

---

## Prompt Customization UX

| Option | Description | Selected |
|--------|-------------|----------|
| Tab in main settings panel | Prompt editor as settings tab | |
| Separate "Prompt" tab | Next to settings | |
| Advanced option during summary preparation | Inline expander before Claude runs | ✓ |

**User's choice:** Advanced option — "Upravit prompt" link expands inline editor before Claude runs
**Notes:** Not in settings, but edits persist to settings

---

| Option | Description | Selected |
|--------|-------------|----------|
| In main panel, near button (always visible) | Context field always accessible | ✓ |
| In settings panel | Must open settings to set context | |
| Both | Small inline + full in settings | |

**User's choice:** In main panel, always visible
**Notes:** Named context profiles with dropdown (New/Rename/Delete) — like browser profiles. Persist between sessions.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Yes, skip Original Transcript section | Save ~50% output tokens | ✓ |
| No, keep it for completeness | Include in _upraveno.txt | |
| You decide | Claude picks | |

**User's choice:** Skip it — _prepis.txt already has original
**Notes:** None

---

## API Key Management

| Option | Description | Selected |
|--------|-------------|----------|
| Just-in-time on first "Přepsat + Upravit" click | | |
| When user opens settings | | |
| Non-blocking banner at top | Dismissible, reappears until set | ✓ |

**User's choice:** Non-blocking banner
**Notes:** Disappears for session on dismiss. Reappears next launch. If key already set, never appears. Reappears only if API call fails due to missing key.

---

| Option | Description | Selected |
|--------|-------------|----------|
| Test key on save | Small API call, immediate feedback | ✓ |
| Don't validate on save | Report errors at runtime | |
| You decide | Claude picks | |

**User's choice:** Test on save + warning before save with rate limiter guide
**Notes:** Tooltip/info icon next to API key field with Anthropic rate limiter setup guide

---

## Settings Panel Design

| Option | Description | Selected |
|--------|-------------|----------|
| Gear icon → modal dialog | | ✓ |
| Separate tab in main window | | |
| Sidebar slides in | | |

**User's choice:** Gear icon in header, modal dialog
**Notes:** Save/Cancel + Escape closes without saving

---

| Option | Description | Selected |
|--------|-------------|----------|
| Tabs: General + Claude | | ✓ |
| Single scrollable page | | |
| You decide | | |

**User's choice:** Two tabs: General (language, output folder, workers) | Claude (API key, model, rate limiter guide)
**Notes:** Always opens on General tab

---

| Option | Description | Selected |
|--------|-------------|----------|
| All settings persist | Output folder, language, workers, API key, prompt, context, model | ✓ |
| Core only | Prompt resets each session | |
| You decide | | |

**User's choice:** All persist. API key in Windows Credential Manager / macOS Keychain. Include rate limiter setup guide.
**Notes:** JSON config in app data dir, API key in keyring separately

---

## Additional Decisions

### Live language reload
**User's choice:** Yes — live reload without restart in Phase 3. Default prompt also switches language.

### Worker count GPU info
**User's choice:** Show info with explanation and speed comparison. User can still override.

### Output folder
**User's choice:** Settings stores default. Action bar picker overrides for current session only.

### Model selection
**User's choice:** Haiku (fast/cheap) and Sonnet (balanced/quality). No Opus.

### Reset to defaults
**User's choice:** Modal with checkboxes — user ticks what to reset.

### Re-cleanup versioning
**User's choice:** _upraveno_2.txt, _upraveno_3.txt, etc.

### File collision
**User's choice:** Same incrementing pattern for _prepis.txt: _prepis_2.txt, _prepis_3.txt.

### No API key behavior
**User's choice:** "Přepsat + Upravit" blocked — tooltip "Set up API key first". Only "Přepsat" available.

### Pipeline mode
**User's choice:** Cleanup starts as each file finishes transcription (overlap with next file's transcription).

### Cost estimates
**User's choice:** Both — estimate before sending, actual after completion.

### VAD indicator
**User's choice:** Animated spinner/dots in status column during VAD.

### API timeout
**User's choice:** ~300 seconds, notify user after prolonged wait.

### Startup check
**User's choice:** No startup API check. Only when Claude features triggered.

### Inline prompt editor
**User's choice:** Just editable text area + "Reset to default". No output preview. Edits persist.

---

## Claude's Discretion

- Chunking strategy details (overlap size, merge algorithm)
- JSON config file location and schema
- Log message formatting for Claude progress
- Inline prompt editor layout details
- Cost estimation calculation method
- Spinner/dots animation implementation

## Deferred Ideas

None — discussion stayed within phase scope.

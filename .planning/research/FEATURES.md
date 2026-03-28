# Feature Research

**Domain:** Desktop audio transcription app (Whisper-based, Czech-focused, with optional LLM cleanup)
**Researched:** 2026-03-28
**Confidence:** HIGH (core table stakes), MEDIUM (differentiators — based on competitor analysis + community feedback)

---

## Feature Landscape

### Table Stakes (Users Expect These)

Features users assume exist. Missing these = product feels incomplete.

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| Load audio files via dialog or drag-and-drop | Every file-processing app works this way; users won't hunt for another entry point | LOW | Multi-file selection is the floor; folder-add is a bonus |
| Support common audio formats (.mp3, .wav, .m4a, .ogg) | These are the four formats anyone with meeting/interview recordings will have | LOW | ffmpeg bundled handles codec differences transparently |
| Show loaded file list with processing status | Users need to know what's queued, what's running, what's done — absence feels broken | LOW | Status labels: čeká / zpracovává / hotovo covers the state machine |
| Real-time progress feedback during transcription | Long recordings (30+ min) with zero feedback = users assume the app crashed | MEDIUM | Log panel or progress bar; log is more informative for power users |
| Save output to text file | The whole point of transcription is a file you can use elsewhere | LOW | Two output variants (raw + edited) must both be savable |
| Configurable output folder | Users batch-processing many files won't manually save each one | LOW | Auto-naming pattern (_prepis.txt, _upraveno.txt) removes friction |
| Clear error messages | Whisper failures, missing API key, and bad audio produce silent failures in naive implementations | LOW | Surface errors in the log; don't just stop processing |
| App runs without network connection (core path) | Privacy and offline use are primary reasons people choose local Whisper over cloud services | MEDIUM | Core transcription must never require internet; Claude API path is optional |
| Persistent settings between sessions | Users don't want to re-enter their API key or re-select their output folder every launch | LOW | OS-native keychain for API key; config file for preferences |

### Differentiators (Competitive Advantage)

Features that set this product apart. Compete here.

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| Claude API text cleanup (grammar, paragraphs, summary) | Whisper output is often unpunctuated and unstructured; an edited version ready for a report is hours of work saved | HIGH | The "Přepsat + Upravit" path is the core differentiator vs. raw Whisper tools |
| Executive summary + diff vs. original in a single output file | Reviewers can skim the summary and check what changed — no separate tool needed | MEDIUM | Structured output file design: summary → edited text → diff section |
| Original transcript always preserved separately | Trust: users never fear that "editing" destroyed the source of truth | LOW | Two-file output model enforces this structurally |
| Czech-first language handling | Most Whisper GUIs are English-centric and treat Czech as an afterthought; medium model tuned for Czech is a meaningful accuracy choice | LOW | Language hard-set to Czech in model call; no ambiguity |
| Switchable Czech/English UI | Small internal team + wider distribution audience have different language needs; this is rare in local Whisper tools | MEDIUM | i18n string dictionary; two complete string sets; toggle in settings or title bar |
| GPU auto-detection (CUDA/MPS/CPU fallback) | Users shouldn't know what a CUDA is; app should just run fast when it can | MEDIUM | torch.cuda.is_available() + MPS check at startup; log which device is active |
| Parallel file processing | Long queues of interview recordings are the primary use case; single-file-at-a-time is a bottleneck | MEDIUM | Thread pool with configurable concurrency; 1–N slider in settings |
| OS-native API key storage (Credential Manager / Keychain) | Storing API keys in plaintext config files is a user trust risk; native storage is the professional approach and rare in Python desktop apps | MEDIUM | keyring library abstracts both platforms; first-run prompt flow |
| Portable folder distribution (no install required) | Team members without admin rights or technical ability can just unzip and run | HIGH | PyInstaller folder mode + bundled ffmpeg + bundled model = zero dependencies |

### Anti-Features (Commonly Requested, Often Problematic)

Features that seem like good ideas but should be explicitly rejected for v1.

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| Live microphone recording | "Can it transcribe while I speak?" is a natural ask | Real-time audio capture, VAD, streaming Whisper are a separate engineering domain from file transcription; adds testing surface, platform audio API complexity, and no clear user need for the defined audience | Out of scope; defer to v2 if validated; note in UI that file transcription only |
| In-app transcript editor | Users want to fix Whisper errors directly | A full rich-text editor with cursor, undo, find/replace is a significant GUI project on its own in Tkinter; it competes with the LLM cleanup path which does the same job better | Claude cleanup handles most corrections; export to any text editor for manual fixes |
| Cloud sync / backup | Users might want transcripts accessible on multiple devices | Introduces authentication, server costs, and a privacy story that contradicts the "runs locally" value proposition | Users save files to their own cloud storage (Dropbox, OneDrive); the app produces standard .txt files |
| Speaker diarization | Who said what is valuable for meeting transcripts | Diarization requires pyannote.audio or WhisperX, adds a 1–2 GB speaker model dependency, is not reliable for Czech, and is a significant integration project | Noted as v2 feature if users request it post-launch |
| Video file support | Many recordings come as .mp4 from screen recorders | Adding video means ffmpeg must extract audio — achievable — but then users expect frame-accurate playback sync; scope expands fast | ffmpeg can strip audio from video as a preprocessing workaround users can do manually; v1 is audio-only |
| Multi-language transcription | Whisper supports 99 languages | Mixing languages in the same queue complicates the UI (per-file language selection), the output file naming, and the Claude cleanup prompts which are Czech-specific | Hard-code Czech for v1; language setting can be exposed in v2 |
| Single .exe packaging | Users assume "portable" means one file | PyInstaller --onefile mode is significantly slower to start (everything unpacks to a temp dir) and causes Windows Defender false positives; folder mode is faster and more stable | Portable folder in a ZIP archive is the correct distribution format; document this clearly |
| Automatic model download at runtime | Users might prefer choosing model size | Network dependency on first run breaks the offline promise; increases launch friction; Whisper medium is the right choice for Czech and should be bundled | Bundle medium model; document size; let users see model path in settings |

---

## Feature Dependencies

```
[Batch file queue]
    └──requires──> [File loading (single file)]
                       └──requires──> [Audio format support via ffmpeg]

[Claude cleanup output]
    └──requires──> [Raw Whisper transcription]
                       └──requires──> [GPU auto-detection + model loading]

[Parallel processing]
    └──requires──> [Batch file queue]
    └──requires──> [Real-time progress log]  (parallel jobs need per-file status)

[OS-native API key storage]
    └──requires──> [First-run key prompt flow]

["Přepsat + Upravit" button]
    └──requires──> [Claude API key stored and accessible]
    └──requires──> [Raw Whisper transcription]
    └──enhances──> [Two-file output model]

[Switchable UI language (CZ/EN)]
    └──enhances──> [All UI components]  (every string must be in the i18n dict)

[Configurable output folder]
    └──enhances──> [Batch file queue]  (manual save still works for single files)

[Portable distribution]
    └──requires──> [Bundled ffmpeg]
    └──requires──> [Bundled Whisper model]
    └──requires──> [PyInstaller build pipeline]
```

### Dependency Notes

- **Batch queue requires file loading:** The single-file load path is the building block; batch is a loop around it.
- **Claude cleanup requires raw transcription:** The "Přepsat + Upravit" button is always Whisper-first; Claude receives the raw transcript as input.
- **Parallel processing requires progress log:** Without per-file status, users can't tell which of several parallel jobs is running or failed. Do not add parallelism without the log.
- **i18n must be designed in from the start:** Retrofitting a switchable language onto an app where strings are hardcoded in widget constructors is painful. The CZ/EN dict must exist before the first widget is written.
- **Portable distribution constrains everything:** ffmpeg and the model must be co-located with the binary. All path resolution must use relative paths from the app root, not system paths.

---

## MVP Definition

### Launch With (v1)

Minimum viable product — validates the core value proposition.

- [ ] Load audio files individually and by folder — without this the app cannot be tested
- [ ] File list with čeká / zpracovává / hotovo status — minimum viable feedback
- [ ] Whisper medium transcription (Czech, GPU auto-detect) — the core product
- [ ] Real-time processing log — essential for long audio; users will think app is frozen otherwise
- [ ] "Přepsat" button (raw only) — validates the transcription path independently
- [ ] "Přepsat + Upravit" button (Whisper + Claude) — validates the differentiating LLM cleanup path
- [ ] Two-file output: _prepis.txt + _upraveno.txt — the designed output contract
- [ ] Save single file (dialog) + select output folder (batch auto-naming) — users must be able to get their files
- [ ] API key prompt on first use + OS-native keychain storage — required for Claude path; must be present before distribution
- [ ] App works fully without API key (core transcription path) — key requirement from PROJECT.md
- [ ] Switchable Czech/English UI — required before wider distribution; i18n must be baked in from the start
- [ ] PyInstaller portable folder build for Windows and macOS — required for distribution to non-technical users

### Add After Validation (v1.x)

Features to add once core transcription loop is confirmed working.

- [ ] Configurable parallel processing (1–N files) — add when users report queue speed as a bottleneck
- [ ] Drag-and-drop file loading — add when UX review flags it; depends on Tkinter DnD capability
- [ ] Processing history / recently transcribed files — add when users ask "where did my output go?"
- [ ] Configurable Claude prompt (custom cleanup instructions) — add when power users want different output structure
- [ ] Keyboard shortcuts for core actions — add after UI is stable and shortcut set won't change

### Future Consideration (v2+)

Features to defer until product-market fit is established.

- [ ] Speaker diarization — high complexity, Czech model availability uncertain; validate demand first
- [ ] Multi-language transcription — only needed if audience expands beyond Czech speakers
- [ ] Live microphone recording — separate engineering domain; validate if users want it
- [ ] In-app transcript editor — only if Claude cleanup path proves insufficient for user corrections
- [ ] Video file support (.mp4) — easy first step (ffmpeg strip audio), but opens scope; defer

---

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| Whisper transcription (Czech, GPU) | HIGH | MEDIUM | P1 |
| Real-time processing log | HIGH | LOW | P1 |
| File list with status | HIGH | LOW | P1 |
| Two-file output (raw + edited) | HIGH | LOW | P1 |
| Claude cleanup (Přepsat + Upravit) | HIGH | MEDIUM | P1 |
| OS-native API key storage | HIGH | MEDIUM | P1 |
| Save dialog + output folder config | HIGH | LOW | P1 |
| App works without API key | HIGH | LOW | P1 |
| Switchable CZ/EN UI | MEDIUM | MEDIUM | P1 (design constraint) |
| PyInstaller portable packaging | HIGH | HIGH | P1 (distribution blocker) |
| Parallel file processing | MEDIUM | MEDIUM | P2 |
| Drag-and-drop file loading | MEDIUM | LOW | P2 |
| Configurable Claude prompt | MEDIUM | LOW | P2 |
| Processing history | LOW | LOW | P2 |
| Speaker diarization | HIGH | HIGH | P3 |
| Video file support | MEDIUM | MEDIUM | P3 |
| Multi-language support | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch
- P2: Should have, add when possible
- P3: Nice to have, future consideration

---

## Competitor Feature Analysis

| Feature | Buzz (open-source) | MacWhisper (Mac-only, $80) | Whisper-Writer (dictation focus) | Our App |
|---------|--------------------|-----------------------------|----------------------------------|---------|
| Batch file queue | Yes | Yes | No (single-file/dictation) | Yes |
| LLM post-processing cleanup | No | No | Yes (GPT/Claude/etc.) | Yes — Claude-specific, structured output |
| Executive summary output | No | No | No | Yes (differentiator) |
| Original + edited dual output | No | No | No | Yes (differentiator) |
| Czech-first UI | No | No | No | Yes (differentiator) |
| Switchable UI language | No | No | No | Yes (differentiator) |
| OS-native key storage | No | N/A (no API keys) | No | Yes |
| GPU auto-detect | Yes | Yes (MPS only) | Yes | Yes |
| Portable (no install) | Yes | No (Mac App Store) | No | Yes |
| Windows + macOS | Yes | No (Mac only) | Yes | Yes |
| Speaker diarization | No | Yes (v12+, on-device) | No | No (v2+) |
| Live microphone | Yes | Yes | Yes | No (out of scope) |

**Key takeaway:** No existing Whisper desktop app combines LLM cleanup with structured dual-file output, Czech-first design, and cross-platform portable distribution. The Claude-powered "Přepsat + Upravit" path with executive summary is a genuine gap in the current competitive landscape.

---

## Sources

- [Buzz — open-source Whisper GUI](https://github.com/chidiwilliams/buzz) — feature list for baseline comparison
- [MacWhisper 12 release coverage](https://9to5mac.com/2025/03/18/macwhisper-12-delivers-the-most-requested-feature-to-the-leading-ai-transcription-app/) — speaker diarization as "most requested" feature signal
- [Best MacWhisper Alternatives 2026](https://www.getvoibe.com/blog/macwhisper-alternatives/) — competitor landscape
- [Whisper-Writer LLM post-processing PR](https://github.com/savbell/whisper-writer/pull/102) — how LLM post-processing is implemented in the wild
- [OpenAI Whisper Processing Guide](https://cookbook.openai.com/examples/whisper_processing_guide) — pre/post-processing best practices
- [AlternativeTo: Whisper alternatives](https://alternativeto.net/software/whisper/) — breadth of competing tools
- [Whisper Czech accuracy notes](https://medium.com/@maestrosill/openai-whisper-ai-pro-p%C5%99epis-audia-na-text-97c1ae80feb6) — medium model is the right Czech choice; small is insufficient

---

*Feature research for: Desktop audio transcription app (Whisper + Claude, Czech-focused)*
*Researched: 2026-03-28*

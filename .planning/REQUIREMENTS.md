# Requirements: Whisper Přepisovač

**Defined:** 2026-03-28
**Core Value:** Reliable, one-click transcription of long Czech audio recordings into clean, structured text

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### File Management

- [x] **FILE-01**: User can add individual audio files via file picker (.mp3, .wav, .m4a, .ogg)
- [x] **FILE-02**: User can add all audio files from a folder via folder picker
- [x] **FILE-03**: User can see list of loaded files with status (čeká / zpracovává / hotovo)
- [x] **FILE-04**: User can remove files from the queue before processing
- [x] **FILE-05**: User can save single output via "Save as" dialog
- [x] **FILE-06**: User can select output folder for batch auto-save (_prepis.txt / _upraveno.txt naming)

### Transcription

- [x] **TRANS-01**: User can transcribe audio using Whisper medium model with Czech language
- [x] **TRANS-02**: App auto-detects GPU (CUDA on Windows, MPS on Mac) with CPU fallback
- [x] **TRANS-03**: User sees detailed real-time log during transcription (file name, progress, device used)
- [x] **TRANS-04**: User can configure number of parallel file processing workers (1-N)
- [x] **TRANS-05**: App preprocesses audio with VAD to prevent Whisper hallucinations on silence
- [x] **TRANS-06**: App shows clear error messages when transcription fails (bad audio, out of memory, etc.)

### Claude API Cleanup

- [x] **CLAUDE-01**: User can trigger "Přepsat + Upravit" for transcription + Claude API text cleanup
- [x] **CLAUDE-02**: Claude cleanup produces: grammar correction, paragraph structure, executive summary, and comparison with original
- [x] **CLAUDE-03**: Output is 2 files: original transcript (_prepis.txt) + edited version with summary & diff (_upraveno.txt)
- [x] **CLAUDE-04**: Original transcript is always preserved and never deleted or overwritten
- [x] **CLAUDE-05**: "Přepsat" button works independently — raw transcription without Claude API
- [x] **CLAUDE-06**: App works fully without Claude API key (transcription-only mode)

### API Key Management

- [x] **KEY-01**: App prompts for Anthropic API key on first use of Claude features
- [x] **KEY-02**: API key stored securely via Windows Credential Manager / macOS Keychain
- [x] **KEY-03**: User can skip API key setup and use transcription-only mode
- [x] **KEY-04**: When app is moved to new PC/user, prompts for fresh API key (no hardcoded keys)
- [x] **KEY-05**: User can update or remove API key from settings

### User Interface

- [x] **UI-01**: Switchable UI language: Czech and English
- [x] **UI-02**: i18n string dictionary used from first widget — all labels translatable
- [x] **UI-03**: Modern-looking Tkinter GUI using ttkbootstrap theming
- [x] **UI-04**: Settings panel for API key, output folder, parallel workers, language, GPU preference
- [x] **UI-05**: Persistent settings between sessions (output folder, language, worker count)

### Packaging & Distribution

- [x] **PKG-01**: PyInstaller portable folder packaging for Windows (no Python required)
- [ ] **PKG-02**: PyInstaller portable folder packaging for macOS (no Python required)
- [x] **PKG-03**: ffmpeg binary bundled with the app (not downloaded at runtime)
- [x] **PKG-04**: Whisper medium model bundled with the app (not downloaded at runtime)
- [x] **PKG-05**: PyInstaller spec file with Whisper hidden imports, tiktoken fix, and freeze_support
- [x] **PKG-06**: All bundled resources accessible via get_resource_path (sys._MEIPASS aware)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Enhanced Transcription

- **TRANS-V2-01**: Speaker diarization (who said what)
- **TRANS-V2-02**: Multi-language support beyond Czech
- **TRANS-V2-03**: Drag-and-drop file loading (requires tkinterdnd2)

### Enhanced Output

- **OUT-V2-01**: Export to formats beyond .txt (DOCX, SRT subtitles)
- **OUT-V2-02**: Timestamp-aligned transcript segments

### Platform

- **PLAT-V2-01**: Auto-update mechanism for new versions

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Live microphone recording | Separate engineering domain from file transcription; no clear user need |
| In-app transcript editor | Claude cleanup handles corrections; export to text editor for manual fixes |
| Cloud sync / backup | Contradicts "runs locally" value proposition; users save to their own cloud storage |
| Video file support | Scope expands fast (playback sync expectations); audio-only for v1 |
| Single .exe packaging | Slower startup, Windows Defender false positives; folder mode is correct |
| Automatic model download | Breaks offline promise; medium model should be bundled |
| Multi-language in v1 | Complicates UI, output naming, and Claude prompts; Czech-only for v1 |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| UI-01 | Phase 1 | Complete |
| UI-02 | Phase 1 | Complete |
| UI-03 | Phase 1 | Complete |
| FILE-01 | Phase 2 | Complete |
| FILE-02 | Phase 2 | Complete |
| FILE-03 | Phase 2 | Complete |
| FILE-04 | Phase 2 | Complete |
| FILE-05 | Phase 2 | Complete |
| FILE-06 | Phase 2 | Complete |
| TRANS-01 | Phase 2 | Complete |
| TRANS-02 | Phase 2 | Complete |
| TRANS-03 | Phase 2 | Complete |
| TRANS-04 | Phase 2 | Complete |
| TRANS-05 | Phase 2 | Complete |
| TRANS-06 | Phase 2 | Complete |
| CLAUDE-01 | Phase 3 | Complete |
| CLAUDE-02 | Phase 3 | Complete |
| CLAUDE-03 | Phase 3 | Complete |
| CLAUDE-04 | Phase 3 | Complete |
| CLAUDE-05 | Phase 3 | Complete |
| CLAUDE-06 | Phase 3 | Complete |
| KEY-01 | Phase 3 | Complete |
| KEY-02 | Phase 3 | Complete |
| KEY-03 | Phase 3 | Complete |
| KEY-04 | Phase 3 | Complete |
| KEY-05 | Phase 3 | Complete |
| UI-04 | Phase 3 | Complete |
| UI-05 | Phase 3 | Complete |
| PKG-01 | Phase 4 | Complete |
| PKG-02 | Phase 4 | Pending |
| PKG-03 | Phase 4 | Complete |
| PKG-04 | Phase 4 | Complete |
| PKG-05 | Phase 4 | Complete |
| PKG-06 | Phase 4 | Complete |

**Coverage:**
- v1 requirements: 34 total (count corrected from initial 28 — all requirements enumerated)
- Mapped to phases: 34
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-28*
*Last updated: 2026-03-28 — traceability populated after roadmap creation*

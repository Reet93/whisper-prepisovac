# Requirements: Whisper Přepisovač

**Defined:** 2026-03-28
**Core Value:** Reliable, one-click transcription of long Czech audio recordings into clean, structured text

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### File Management

- [ ] **FILE-01**: User can add individual audio files via file picker (.mp3, .wav, .m4a, .ogg)
- [ ] **FILE-02**: User can add all audio files from a folder via folder picker
- [ ] **FILE-03**: User can see list of loaded files with status (čeká / zpracovává / hotovo)
- [ ] **FILE-04**: User can remove files from the queue before processing
- [ ] **FILE-05**: User can save single output via "Save as" dialog
- [ ] **FILE-06**: User can select output folder for batch auto-save (_prepis.txt / _upraveno.txt naming)

### Transcription

- [ ] **TRANS-01**: User can transcribe audio using Whisper medium model with Czech language
- [ ] **TRANS-02**: App auto-detects GPU (CUDA on Windows, MPS on Mac) with CPU fallback
- [ ] **TRANS-03**: User sees detailed real-time log during transcription (file name, progress, device used)
- [ ] **TRANS-04**: User can configure number of parallel file processing workers (1-N)
- [ ] **TRANS-05**: App preprocesses audio with VAD to prevent Whisper hallucinations on silence
- [ ] **TRANS-06**: App shows clear error messages when transcription fails (bad audio, out of memory, etc.)

### Claude API Cleanup

- [ ] **CLAUDE-01**: User can trigger "Přepsat + Upravit" for transcription + Claude API text cleanup
- [ ] **CLAUDE-02**: Claude cleanup produces: grammar correction, paragraph structure, executive summary, and comparison with original
- [ ] **CLAUDE-03**: Output is 2 files: original transcript (_prepis.txt) + edited version with summary & diff (_upraveno.txt)
- [ ] **CLAUDE-04**: Original transcript is always preserved and never deleted or overwritten
- [ ] **CLAUDE-05**: "Přepsat" button works independently — raw transcription without Claude API
- [ ] **CLAUDE-06**: App works fully without Claude API key (transcription-only mode)

### API Key Management

- [ ] **KEY-01**: App prompts for Anthropic API key on first use of Claude features
- [ ] **KEY-02**: API key stored securely via Windows Credential Manager / macOS Keychain
- [ ] **KEY-03**: User can skip API key setup and use transcription-only mode
- [ ] **KEY-04**: When app is moved to new PC/user, prompts for fresh API key (no hardcoded keys)
- [ ] **KEY-05**: User can update or remove API key from settings

### User Interface

- [x] **UI-01**: Switchable UI language: Czech and English
- [x] **UI-02**: i18n string dictionary used from first widget — all labels translatable
- [x] **UI-03**: Modern-looking Tkinter GUI using ttkbootstrap theming
- [ ] **UI-04**: Settings panel for API key, output folder, parallel workers, language, GPU preference
- [ ] **UI-05**: Persistent settings between sessions (output folder, language, worker count)

### Packaging & Distribution

- [ ] **PKG-01**: PyInstaller portable folder packaging for Windows (no Python required)
- [ ] **PKG-02**: PyInstaller portable folder packaging for macOS (no Python required)
- [ ] **PKG-03**: ffmpeg binary bundled with the app (not downloaded at runtime)
- [ ] **PKG-04**: Whisper medium model bundled with the app (not downloaded at runtime)
- [ ] **PKG-05**: PyInstaller spec file with Whisper hidden imports, tiktoken fix, and freeze_support
- [ ] **PKG-06**: All bundled resources accessible via get_resource_path (sys._MEIPASS aware)

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
| FILE-01 | Phase 2 | Pending |
| FILE-02 | Phase 2 | Pending |
| FILE-03 | Phase 2 | Pending |
| FILE-04 | Phase 2 | Pending |
| FILE-05 | Phase 2 | Pending |
| FILE-06 | Phase 2 | Pending |
| TRANS-01 | Phase 2 | Pending |
| TRANS-02 | Phase 2 | Pending |
| TRANS-03 | Phase 2 | Pending |
| TRANS-04 | Phase 2 | Pending |
| TRANS-05 | Phase 2 | Pending |
| TRANS-06 | Phase 2 | Pending |
| CLAUDE-01 | Phase 3 | Pending |
| CLAUDE-02 | Phase 3 | Pending |
| CLAUDE-03 | Phase 3 | Pending |
| CLAUDE-04 | Phase 3 | Pending |
| CLAUDE-05 | Phase 3 | Pending |
| CLAUDE-06 | Phase 3 | Pending |
| KEY-01 | Phase 3 | Pending |
| KEY-02 | Phase 3 | Pending |
| KEY-03 | Phase 3 | Pending |
| KEY-04 | Phase 3 | Pending |
| KEY-05 | Phase 3 | Pending |
| UI-04 | Phase 3 | Pending |
| UI-05 | Phase 3 | Pending |
| PKG-01 | Phase 4 | Pending |
| PKG-02 | Phase 4 | Pending |
| PKG-03 | Phase 4 | Pending |
| PKG-04 | Phase 4 | Pending |
| PKG-05 | Phase 4 | Pending |
| PKG-06 | Phase 4 | Pending |

**Coverage:**
- v1 requirements: 34 total (count corrected from initial 28 — all requirements enumerated)
- Mapped to phases: 34
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-28*
*Last updated: 2026-03-28 — traceability populated after roadmap creation*

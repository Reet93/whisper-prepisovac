# Roadmap: Whisper Přepisovač

## Overview

Four phases from skeleton to distributable portable app. Phase 1 lays the architectural foundation (i18n and resource path abstraction) that every subsequent phase builds on. Phase 2 delivers the core MVP: a working transcription loop with file queue, threading, GPU detection, and output. Phase 3 adds the primary differentiator — Claude-powered cleanup — along with API key management and the settings panel. Phase 4 turns the working app into a distributable portable folder for both Windows and macOS, verified on clean machines.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Foundation** - Project skeleton, i18n infrastructure, ttkbootstrap window, and resource path abstraction
- [ ] **Phase 2: Core Transcription** - File queue, Whisper transcription, GPU detection, real-time log, and file output — full MVP loop
- [ ] **Phase 3: Claude Cleanup + Settings** - "Přepsat + Upravit" path, API key management, settings panel, persistent preferences, and parallel workers
- [ ] **Phase 4: Packaging** - PyInstaller portable folder builds for Windows and macOS, verified on clean machines with no Python installed

## Phase Details

### Phase 1: Foundation
**Goal**: A runnable skeleton app with correct architecture exists — i18n infrastructure in place before any widget is written, all bundled resources accessible via a single path helper, and ttkbootstrap window confirmed working on both platforms
**Depends on**: Nothing (first phase)
**Requirements**: UI-01, UI-02, UI-03
**Success Criteria** (what must be TRUE):
  1. App launches and shows a ttkbootstrap-themed window on both Windows and macOS
  2. All visible strings are loaded through the i18n `_()` function — no hardcoded UI text anywhere
  3. Switching language between Czech and English changes all labels without restart (or on restart — either is acceptable at this stage)
  4. `get_resource_path()` resolves bundled asset paths correctly in both dev and frozen context
**Plans**: TBD
**UI hint**: yes

### Phase 2: Core Transcription
**Goal**: Users can load audio files, run transcription, and receive a saved `_prepis.txt` output — the full single-file MVP loop working correctly with threading, GPU detection, real-time logging, and error handling
**Depends on**: Phase 1
**Requirements**: FILE-01, FILE-02, FILE-03, FILE-04, FILE-05, FILE-06, TRANS-01, TRANS-02, TRANS-03, TRANS-04, TRANS-05, TRANS-06
**Success Criteria** (what must be TRUE):
  1. User can add individual audio files (.mp3, .wav, .m4a, .ogg) and a full folder of audio files via file pickers
  2. Loaded files appear in a list with status indicators (čeká / zpracovává / hotovo) and can be removed before processing
  3. Clicking "Přepsat" starts transcription and the real-time log shows file name, GPU device used, and live progress — UI remains responsive throughout
  4. Transcription completes and saves `_prepis.txt` to the output location; output file contains correct Czech text
  5. When transcription fails (bad audio, out of memory), a clear error message appears in the log — app does not crash
  6. App detects and uses CUDA (Windows) or MPS (Mac) GPU when available, and falls back to CPU with a log message confirming which device is active
**Plans**: TBD
**UI hint**: yes

### Phase 3: Claude Cleanup + Settings
**Goal**: Users can optionally trigger Claude-powered text cleanup to produce a structured `_upraveno.txt` with edited text, executive summary, and diff — and can configure all persistent settings — while the app continues to work fully without an API key
**Depends on**: Phase 2
**Requirements**: CLAUDE-01, CLAUDE-02, CLAUDE-03, CLAUDE-04, CLAUDE-05, CLAUDE-06, KEY-01, KEY-02, KEY-03, KEY-04, KEY-05, UI-04, UI-05
**Success Criteria** (what must be TRUE):
  1. Clicking "Přepsat + Upravit" runs transcription then calls Claude API and produces two output files: `_prepis.txt` (raw) and `_upraveno.txt` (edited text + executive summary + diff vs original)
  2. Original `_prepis.txt` is never modified or deleted by the cleanup step
  3. On first use of Claude features, app prompts for an Anthropic API key; key is stored in Windows Credential Manager or macOS Keychain (never in a plaintext file)
  4. User can skip API key setup and use "Přepsat" without Claude features working — no crash, no blocking dialog
  5. User can view and update or remove the API key from the settings panel
  6. Settings panel persists output folder, language choice, and parallel worker count between sessions
**Plans**: TBD
**UI hint**: yes

### Phase 4: Packaging
**Goal**: A portable folder build exists for both Windows and macOS that runs correctly on a clean machine with no Python, no CUDA toolkit, and no system ffmpeg installed
**Depends on**: Phase 3
**Requirements**: PKG-01, PKG-02, PKG-03, PKG-04, PKG-05, PKG-06
**Success Criteria** (what must be TRUE):
  1. Running the Windows portable folder on a clean Windows 10/11 machine (no Python, no CUDA toolkit) launches the app and completes a transcription successfully
  2. Running the macOS portable folder on a clean Mac (Intel and Apple Silicon) launches the app and completes a transcription successfully
  3. ffmpeg is found automatically by the app at startup — user does not need to install or configure it
  4. The Whisper medium model loads correctly from inside the portable folder — no download prompt at runtime
  5. API key storage (keyring) works in the frozen/packaged app on both platforms
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 0/TBD | Not started | - |
| 2. Core Transcription | 0/TBD | Not started | - |
| 3. Claude Cleanup + Settings | 0/TBD | Not started | - |
| 4. Packaging | 0/TBD | Not started | - |

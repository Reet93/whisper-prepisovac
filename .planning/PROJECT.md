# Whisper Přepisovač

## What This Is

A cross-platform desktop application for transcribing audio recordings to text using OpenAI Whisper, with optional AI-powered text cleanup via the Anthropic Claude API. Built for a small team with the intent to share with a wider audience. Runs locally on Windows and macOS without requiring Python installation.

## Core Value

Reliable, one-click transcription of long Czech audio recordings into clean, structured text — no cloud dependency for the core transcription.

## Requirements

### Validated

- [x] Switchable UI language: Czech / English — Validated in Phase 01: Foundation

### Active

- [ ] Add audio files individually or by folder (.mp3, .wav, .m4a, .ogg)
- [ ] Display list of loaded recordings with status (čeká / zpracovává / hotovo)
- [ ] Transcribe audio using Whisper medium model with Czech language
- [ ] Auto-detect GPU (CUDA on Windows, MPS on Mac) with CPU fallback
- [ ] Show detailed real-time processing log during transcription
- [ ] Configurable parallel file processing (1-N files simultaneously)
- [ ] "Přepsat" button — raw Whisper transcription only
- [ ] "Přepsat + Upravit" button — transcription + Claude API text cleanup
- [ ] Claude API cleanup: grammar correction, paragraph structure, executive summary, comparison with original
- [ ] Output 2 files: original transcript + edited version (with summary & diff)
- [ ] Original transcript always preserved, never deleted or overwritten
- [ ] "Uložit jako" — save single file with dialog
- [ ] "Vybrat výstupní složku" — batch save with auto-naming (_prepis.txt / _upraveno.txt)
- [ ] API key management: prompt on first use, store via Credential Manager (Win) / Keychain (Mac)
- [ ] Option to skip Claude API setup entirely — app works without it

- [ ] PyInstaller portable folder packaging for Windows and macOS
- [ ] Bundle ffmpeg and Whisper medium model with the app

### Out of Scope

- Real-time / live microphone recording — transcription of existing files only
- Cloud-hosted version — desktop only, runs locally
- Video file support — audio files only for v1
- Multi-language transcription — Czech only for v1
- Whisper model download at runtime — model is bundled

## Context

- Target users are Czech speakers processing meeting recordings, interviews, and lectures
- Whisper medium model provides good Czech accuracy at ~1.5GB model size
- Long recordings (30+ min) require progress feedback and efficient processing
- App will be shared/distributed — no hardcoded API keys, each user provides their own
- Users who don't have an Anthropic API key should still be able to use the core transcription
- Two platforms: Windows (CUDA GPU) and macOS (MPS GPU), both with CPU fallback
- PyInstaller produces platform-specific portable folders (not single .exe)

## Constraints

- **Tech stack**: Python + Tkinter for GUI, openai-whisper for transcription, anthropic SDK for Claude API
- **Packaging**: PyInstaller portable folder — must run without Python installed
- **Dependencies**: ffmpeg and Whisper model bundled, not downloaded at runtime
- **Security**: API keys stored in OS-native secure storage, never in plaintext files
- **Platform**: Must work on both Windows 10/11 and macOS (Intel + Apple Silicon)

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Whisper medium model | Best Czech accuracy, bundle size not a concern | — Pending |
| Tkinter for GUI | Simple, no extra dependencies, ships with Python | Implemented (Phase 01) |
| 2-file output (original + edited) | User wants original preserved + edited with summary & comparison in one file | — Pending |
| OS-native key storage | Credential Manager (Win) / Keychain (Mac) — secure, no plaintext | — Pending |
| Switchable i18n (CZ/EN) | Small team now, wider audience later — both languages needed | Implemented (Phase 01) |
| Auto-detect GPU | CUDA/MPS when available, CPU fallback — best performance without config | — Pending |
| Cross-platform from start | User needs both Win + Mac — build for both from the beginning | — Pending |
| UI/UX design before coding | User requested design contract via /gsd:ui-phase before implementation | Implemented (Phase 01) |

## Evolution

This document evolves at phase transitions and milestone boundaries.

**After each phase transition** (via `/gsd:transition`):
1. Requirements invalidated? → Move to Out of Scope with reason
2. Requirements validated? → Move to Validated with phase reference
3. New requirements emerged? → Add to Active
4. Decisions to log? → Add to Key Decisions
5. "What This Is" still accurate? → Update if drifted

**After each milestone** (via `/gsd:complete-milestone`):
1. Full review of all sections
2. Core Value check — still the right priority?
3. Audit Out of Scope — reasons still valid?
4. Update Context with current state

---
*Last updated: 2026-03-28 after Phase 01 completion*

---
phase: 03-claude-cleanup-settings
plan: "01"
subsystem: backend-foundation
tags: [settings, keyring, anthropic, i18n, claude-cleanup]
dependency_graph:
  requires: []
  provides:
    - SettingsStore (JSON config in OS app-data dir)
    - keyring helpers (get/set/delete_api_key)
    - get_default_prompt (bundled prompt loader)
    - claude_cleaner module (clean_transcript, validate_api_key, cost estimation, diff)
    - Phase 3 i18n strings (cs_CZ + en_US)
    - bilingual prompt files (prompts/)
  affects:
    - all Phase 3 UI plans (depend on SettingsStore and claude_cleaner)
    - locale loading (Phase 3 strings now compiled)
tech_stack:
  added:
    - anthropic==0.86.0
    - keyring==25.7.0
    - platformdirs==4.9.4
  patterns:
    - SettingsStore._load() merges only DEFAULTS keys — immune to schema drift
    - ProcessPoolExecutor worker pattern mirrored for Claude calls (daemon watchdog thread)
    - keyring.errors.PasswordDeleteError caught silently in delete_api_key
key_files:
  created:
    - src/whisperai/utils/settings.py
    - src/whisperai/core/claude_cleaner.py
    - prompts/transcript-processor-prompt-cs.md
    - prompts/transcript-processor-prompt-en.md
  modified:
    - requirements.in
    - locale/cs_CZ/LC_MESSAGES/messages.po
    - locale/cs_CZ/LC_MESSAGES/messages.mo
    - locale/en_US/LC_MESSAGES/messages.po
    - locale/en_US/LC_MESSAGES/messages.mo
decisions:
  - "get_default_prompt uses resource_path for PyInstaller compatibility — prompts/ bundled via spec datas"
  - "claude_cleaner raises anthropic.AuthenticationError / APIStatusError directly — UI layer classifies"
  - "_split_into_chunks prefers paragraph breaks (\\n\\n) at chunk boundary — preserves paragraph coherence"
  - "Both cs and en prompt files are identical content (prompt auto-detects transcript language) — split exists for D-24 language-aware switching"
  - "validate_api_key treats 429/529 as valid key (rate limited, not invalid)"
metrics:
  duration_minutes: 4
  completed_date: "2026-03-28"
  tasks_completed: 3
  files_modified: 9
---

# Phase 03 Plan 01: Settings Store + Claude Cleaner Backend Summary

**One-liner:** SettingsStore with platformdirs JSON persistence, keyring API key helpers, Claude cleanup pipeline with chunking/cost estimation, and 65 Phase 3 i18n strings compiled for cs_CZ + en_US.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create SettingsStore and keyring helpers | 5ac6d88 | src/whisperai/utils/settings.py, requirements.in |
| 2 | Create Claude cleaner backend and prompt files | 5f2ef53 | src/whisperai/core/claude_cleaner.py, prompts/transcript-processor-prompt-cs.md, prompts/transcript-processor-prompt-en.md |
| 3 | Add all Phase 3 i18n strings | ccce588 | locale/cs_CZ/LC_MESSAGES/messages.po+.mo, locale/en_US/LC_MESSAGES/messages.po+.mo |

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — all exported functions are fully implemented. The `clean_transcript` function requires a real API key for live calls; this is by design (credentials provided by the user at runtime, not stubbed data).

## Self-Check: PASSED

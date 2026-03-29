# Phase 4: Packaging - Context

**Gathered:** 2026-03-29
**Status:** Ready for planning

<domain>
## Phase Boundary

Turn the working app into a distributable portable folder for Windows, publish the source code on GitHub, and create a GitHub Release with a downloadable zip. The app must run on a clean Windows machine with no Python, no CUDA toolkit, and no system ffmpeg installed.

</domain>

<decisions>
## Implementation Decisions

### Git Publication
- **D-01:** Create README.md with project description, features, and install/usage instructions
- **D-02:** MIT License
- **D-03:** Exclude `.planning/`, `.claude/`, `.vexp/`, `models/`, `.venv/`, `__pycache__/`, `dist/`, `build/` from Git — only source code published
- **D-04:** Security scan for hardcoded secrets/API keys before first push (automated grep for patterns like sk-ant-*, .env files, credentials)

### Build Scope
- **D-05:** Windows-only build for this phase (macOS deferred — requires Mac hardware, PyInstaller doesn't cross-compile)
- **D-06:** Local manual build via script (build.bat or build.py) — no CI/CD pipeline

### Distribution
- **D-07:** Both GitHub Release (zip of portable folder for end users) and source repo (for developers)
- **D-08:** Whisper model NOT bundled in distribution — downloaded automatically on first launch with progress dialog ("Downloading Whisper model (~1.5 GB)... This only happens once.")
- **D-09:** README documents first-launch model download requirement and approximate time/size
- **D-10:** Remove unused `medium.pt` (openai-whisper format) from models/ — only faster-whisper model used

### Bundled Binaries
- **D-11:** ffmpeg/ffprobe latest stable Windows static build from BtbN/FFmpeg-Builds on GitHub — bundled in the portable folder
- **D-12:** CUDA libraries picked up automatically by PyInstaller from the torch installation

### Claude's Discretion
- PyInstaller spec file structure and hidden imports — whatever works for faster-whisper + torch + ttkbootstrap
- Build script implementation details
- ffmpeg exact version — latest stable at time of build
- Model download implementation (progress bar widget, retry logic, error handling)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Project
- `.planning/PROJECT.md` — Core value, constraints, key decisions
- `.planning/REQUIREMENTS.md` — PKG-01 through PKG-06 are the requirements for this phase
- `.planning/ROADMAP.md` — Phase 4 success criteria

### Existing Code
- `src/whisperai/utils/resource_path.py` — get_resource_path() already handles sys._MEIPASS for frozen context
- `main.py` — Entry point with freeze_support() already in place
- `src/whisperai/core/vad.py` — Uses get_resource_path("bin/ffmpeg_name") for ffmpeg binary lookup
- `src/whisperai/gui/transcription_panel.py:1067` — Uses get_resource_path("models") for model path
- `src/whisperai/gui/transcription_panel.py:791` — Uses get_resource_path for ffprobe binary lookup
- `requirements.in` — Current dependency list (faster-whisper, ttkbootstrap, anthropic, keyring, platformdirs, silero-vad)

### Stack Docs (from CLAUDE.md)
- CLAUDE.md "Technology Stack" section — PyInstaller 6.19, spec file patterns, ffmpeg bundling approach, torch packaging notes
- CLAUDE.md "Stack Patterns by Variant" section — sys._MEIPASS usage, ffmpeg PATH prepending, model bundling via datas

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `get_resource_path()` in resource_path.py — already sys._MEIPASS aware, all resource lookups go through it
- `main.py` — already has freeze_support() and proper entry point structure
- `requirements.in` — dependency list ready for pip-compile

### Established Patterns
- All bundled resources accessed via `get_resource_path(relative_path)` — consistent pattern
- ffmpeg referenced as `get_resource_path(f"bin/{ffmpeg_name}")` — expects bin/ subdirectory
- Model referenced as `get_resource_path("models")` — expects models/ subdirectory
- i18n catalogs at `get_resource_path("locale")` — already works in both dev and frozen

### Integration Points
- `main.py` is the PyInstaller entry point — already structured correctly
- `__main__.py` exists but bypasses freeze_support — not suitable as PyInstaller entry
- No `.spec` file exists — must be created
- No `bin/` directory exists — ffmpeg binaries must be placed there
- No `.gitignore` exists — must be created before publishing
- Model download logic needs to be added to the transcription startup path (currently assumes models/ exists)

</code_context>

<specifics>
## Specific Ideas

- First-launch model download should show a clear progress dialog in the GUI, not just a console message
- The 2.9 GB models/ directory contains both openai-whisper format (medium.pt) and faster-whisper format — only faster-whisper is used, medium.pt should be cleaned up
- User wants to publish on GitHub for public visibility and download — clean repo presentation matters

</specifics>

<deferred>
## Deferred Ideas

- macOS build — requires Mac hardware, deferred until hardware available
- GitHub Actions CI/CD — overkill for current project size, add later if needed
- Auto-update mechanism — tracked as PLAT-V2-01 in requirements

</deferred>

---

*Phase: 04-packaging*
*Context gathered: 2026-03-29*

# Phase 1: Foundation - Context

**Gathered:** 2026-03-28
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver a runnable skeleton app: ttkbootstrap-themed window with i18n infrastructure (Czech/English), a language switcher widget, and a resource path abstraction. No transcription, no file handling, no settings persistence — just the architectural foundation that every subsequent phase builds on.

</domain>

<decisions>
## Implementation Decisions

### Language Detection
- **D-01:** Auto-detect UI language from OS locale on first launch. If system locale starts with `cs`, use Czech; otherwise default to English.
- **D-02:** Language switching via Combobox in footer. Restart acceptable in Phase 1 (live reload deferred).

### Window Behavior
- **D-03:** Window is freely resizable with minimum size 480x320 (per UI-SPEC).
- **D-04:** Window centered on screen at launch. Calculate center from screen dimensions before showing.

### Project Structure
- **D-05:** Source organized as a Python package: `src/whisperai/` with subfolders (`gui/`, `utils/`).
- **D-06:** Entry point is `main.py` at project root. Contains `freeze_support()` call and imports from the package.
- **D-07:** Locale files live in `locale/` at project root (bundled via PyInstaller `--add-data`).

### Claude's Discretion
- Subfolder breakdown within `src/whisperai/` (e.g., whether `i18n.py` lives in `utils/` or at package root)
- Whether to use `__main__.py` inside the package in addition to `main.py`
- Exact `.po`/`.mo` file content structure beyond the keys defined in UI-SPEC

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### UI Design Contract
- `.planning/phases/01-foundation/01-UI-SPEC.md` -- Locked visual/interaction specs: theme, spacing, typography, color, copywriting, window layout, i18n infrastructure, resource path pattern

### Project Definition
- `.planning/PROJECT.md` -- Core value, constraints, key decisions
- `.planning/REQUIREMENTS.md` -- UI-01 (switchable language), UI-02 (i18n from first widget), UI-03 (ttkbootstrap theming)
- `CLAUDE.md` -- Tech stack constraints, version compatibility, packaging patterns

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- None — greenfield project, no existing code.

### Established Patterns
- None yet. Phase 1 establishes the foundational patterns (package structure, i18n, resource path).

### Integration Points
- `main.py` will be the PyInstaller entry point in Phase 4.
- `get_resource_path()` will be used by every module that references bundled assets (models, ffmpeg, locale).
- The `header_frame` / `content_frame` / `footer_frame` hierarchy will be populated by Phase 2 (file queue, transcription log).

</code_context>

<specifics>
## Specific Ideas

No specific requirements -- open to standard approaches within the constraints defined by the UI-SPEC and project tech stack.

</specifics>

<deferred>
## Deferred Ideas

None -- discussion stayed within phase scope.

</deferred>

---

*Phase: 01-foundation*
*Context gathered: 2026-03-28*

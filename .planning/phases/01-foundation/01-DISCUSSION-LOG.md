# Phase 1: Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md -- this log preserves the alternatives considered.

**Date:** 2026-03-28
**Phase:** 01-foundation
**Areas discussed:** Language detection, Window behavior, Project structure

---

## Language Detection

| Option | Description | Selected |
|--------|-------------|----------|
| Always start in Czech | Czech is primary audience. English users switch via Combobox. Simplest. | |
| Auto-detect from OS locale | Read system language. Czech OS -> Czech, English OS -> English. | ✓ |
| You decide | Claude picks. | |

**User's choice:** Auto-detect from OS locale
**Notes:** None

---

## Window Behavior

### Resizability

| Option | Description | Selected |
|--------|-------------|----------|
| Freely resizable | User can resize above minimum (480x320). Standard desktop behavior. | ✓ |
| Fixed size | Window locked at 720x480. Simpler layout. | |
| You decide | Claude picks. | |

**User's choice:** Freely resizable

### Launch Position

| Option | Description | Selected |
|--------|-------------|----------|
| Center on screen | Calculate center from screen dimensions. | ✓ |
| OS default position | Let window manager decide. | |
| Remember last position | Save between sessions. Needs Phase 3 persistence. | |

**User's choice:** Center on screen

---

## Project Structure

### Organization

| Option | Description | Selected |
|--------|-------------|----------|
| Package with subfolders | src/whisperai/ with gui/, utils/, locale/. Standard Python layout. | ✓ |
| Flat module layout | All .py files in root. Simpler but messy at scale. | |
| You decide | Claude picks. | |

**User's choice:** Package with subfolders (src/whisperai/)

### Entry Point

| Option | Description | Selected |
|--------|-------------|----------|
| main.py | Standard convention. Contains freeze_support(). | ✓ |
| run.py | Alternative convention. | |
| You decide | Claude picks. | |

**User's choice:** main.py (user initially asked about .exe packaging -- clarified that main.py is the source entry point, PyInstaller creates the .exe in Phase 4)

### Package Name

| Option | Description | Selected |
|--------|-------------|----------|
| src/whisperai/ | Python package under src/. Matches project name. | ✓ |
| src/app/ | Generic name. | |
| whisperai/ (no src) | Package at root without src/ wrapper. | |

**User's choice:** src/whisperai/

---

## Claude's Discretion

- Subfolder breakdown within src/whisperai/
- Whether to use __main__.py inside the package
- Exact .po/.mo file content structure beyond UI-SPEC keys

## Deferred Ideas

None -- discussion stayed within phase scope.

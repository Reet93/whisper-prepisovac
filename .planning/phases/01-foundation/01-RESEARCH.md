# Phase 1: Foundation - Research

**Researched:** 2026-03-28
**Domain:** Python/Tkinter app skeleton — ttkbootstrap theming, gettext i18n, PyInstaller resource paths, OS locale detection
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Auto-detect UI language from OS locale on first launch. If system locale starts with `cs`, use Czech; otherwise default to English.
- **D-02:** Language switching via Combobox in footer. Restart acceptable in Phase 1 (live reload deferred).
- **D-03:** Window is freely resizable with minimum size 480x320 (per UI-SPEC).
- **D-04:** Window centered on screen at launch. Calculate center from screen dimensions before showing.
- **D-05:** Source organized as a Python package: `src/whisperai/` with subfolders (`gui/`, `utils/`).
- **D-06:** Entry point is `main.py` at project root. Contains `freeze_support()` call and imports from the package.
- **D-07:** Locale files live in `locale/` at project root (bundled via PyInstaller `--add-data`).

### Claude's Discretion

- Subfolder breakdown within `src/whisperai/` (e.g., whether `i18n.py` lives in `utils/` or at package root)
- Whether to use `__main__.py` inside the package in addition to `main.py`
- Exact `.po`/`.mo` file content structure beyond the keys defined in UI-SPEC

### Deferred Ideas (OUT OF SCOPE)

None -- discussion stayed within phase scope.

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| UI-01 | Switchable UI language: Czech and English | gettext + pybabel workflow; Combobox language switcher in footer; restart-on-switch acceptable in Phase 1 |
| UI-02 | i18n string dictionary used from first widget — all labels translatable | `gettext.translation().install()` must run before `ttkbootstrap.Window()` is instantiated; dot-notation msgid keys |
| UI-03 | Modern-looking Tkinter GUI using ttkbootstrap theming | `ttkbootstrap.Window(themename="flatly")` with grid layout hierarchy; `bootstyle` parameter for semantic colors |

</phase_requirements>

---

## Summary

Phase 1 establishes the architectural skeleton that all subsequent phases build on. The three interlocking concerns are: (1) a ttkbootstrap-themed window with the correct root frame hierarchy, (2) a fully-wired i18n infrastructure that is active before any widget is created, and (3) a `get_resource_path()` helper that resolves bundled asset paths correctly in both development and PyInstaller-frozen contexts.

All three technologies are well-understood with high-confidence documentation. The main gotchas are: `locale.getdefaultlocale()` is deprecated in Python 3.11+ and removed in 3.15 — the safe replacement uses `locale.getlocale()` after calling `locale.setlocale(locale.LC_ALL, '')`, with a Windows-specific fallback via `ctypes.windll.kernel32.GetUserDefaultUILanguage()`; PyInstaller 6.0 introduced an `_internal` subdirectory in onedir mode which changes where `sys._MEIPASS` points; and gettext's `.install()` must be called before any `_()` call anywhere in the codebase.

The i18n workflow requires Babel as a dev-time extraction and compilation tool, but only the stdlib `gettext` module is needed at runtime. Dot-notation msgid keys (e.g., `app.title`) are a valid convention — gettext performs simple string matching on whatever `msgid` you choose.

**Primary recommendation:** Build in the order — `get_resource_path()` → `set_language()` → `ttkbootstrap.Window()` → layout hierarchy. This ordering guarantees i18n is ready before any widget uses `_()`.

---

## Project Constraints (from CLAUDE.md)

All directives from `CLAUDE.md` that apply to Phase 1:

| Directive | Impact on Phase 1 |
|-----------|-------------------|
| Python 3.12.x only (not 3.13, not 3.10.0) | Ensure dev environment matches; affects `locale` API choices |
| ttkbootstrap 1.20.2 | Use `ttkbootstrap.Window`, not bare `tkinter.Tk` |
| PyInstaller 6.19.0 `--onedir` only | `sys._MEIPASS` points to `_internal/` subfolder; `get_resource_path()` must use `sys._MEIPASS`, not `os.path.dirname(sys.executable)` |
| `pathlib.Path` throughout, never `os.path` | All path construction uses `Path` objects |
| API keys in OS keyring — not config files | Not applicable in Phase 1 (no API keys yet) |
| `multiprocessing.freeze_support()` in `main()` | `main.py` must call `multiprocessing.freeze_support()` before anything else |
| Use `tkinter.ttk` (ttkbootstrap widgets), never bare `tkinter` widgets | All widgets from `ttkbootstrap` / `ttk` namespace |
| `get_resource_path()` is the only approved way to reference bundled assets | Must be the first thing built; locale dir must go through it |
| Locale files in `locale/` at project root, bundled via `--add-data` | PyInstaller spec must include `datas=[("locale", "locale")]` |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python | 3.12.x | Runtime | Project constraint. openai-whisper requires < 3.13. |
| ttkbootstrap | 1.20.2 | Themed Tkinter window and widgets | Project constraint. `flatly` theme required by UI-SPEC. Released March 2026. |
| gettext (stdlib) | Python 3.12 stdlib | Runtime i18n string loading | Project constraint. Zero extra runtime dependency. |
| pathlib (stdlib) | Python 3.12 stdlib | Cross-platform path handling | Project constraint. Used everywhere instead of `os.path`. |

### Supporting (dev-time only, not bundled)

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| Babel | 2.17.0 | `.pot`/`.po` extraction and `.mo` compilation | Dev-time only. `pybabel extract`, `pybabel init`, `pybabel compile`. Not bundled in dist. |
| pip-tools | latest | Lock dependency versions | Dev-time. `pip-compile requirements.in` → `requirements.txt`. |

### Installation

```bash
# Runtime dependencies
pip install ttkbootstrap==1.20.2

# Dev-time tools (not bundled)
pip install Babel pip-tools PyInstaller==6.19.0
```

**Version verification (confirmed 2026-03-28):**
- `ttkbootstrap==1.20.2` — released March 8, 2026 (confirmed via GitHub)
- `Babel==2.17.0` — latest stable (confirmed via Babel docs search result Feb 2026)
- `PyInstaller==6.19.0` — latest stable (confirmed via CLAUDE.md sourced from PyPI)

---

## Architecture Patterns

### Recommended Project Structure

```
whisperai/                      # project root
├── main.py                     # PyInstaller entry point; freeze_support() call
├── requirements.in             # abstract deps (ttkbootstrap, anthropic, etc.)
├── requirements.txt            # pip-compile locked deps
├── babel.cfg                   # pybabel extraction config
├── locale/                     # i18n catalogs (bundled via --add-data)
│   ├── cs_CZ/
│   │   └── LC_MESSAGES/
│   │       ├── messages.po
│   │       └── messages.mo
│   └── en_US/
│       └── LC_MESSAGES/
│           ├── messages.po
│           └── messages.mo
└── src/
    └── whisperai/              # Python package
        ├── __init__.py
        ├── __main__.py         # optional; enables `python -m whisperai`
        ├── app.py              # ttkbootstrap Window creation and layout
        ├── gui/
        │   ├── __init__.py
        │   └── main_window.py  # MainWindow class with frame hierarchy
        └── utils/
            ├── __init__.py
            ├── resource_path.py  # get_resource_path()
            └── i18n.py           # set_language(), detect_system_language()
```

### Pattern 1: Resource Path Resolution

`get_resource_path()` must handle two contexts: running from source (development) and running from a PyInstaller `--onedir` bundle. In PyInstaller 6.0+, the `_internal/` subdirectory was introduced — `sys._MEIPASS` correctly points to `_internal/` already, so no adjustment is needed. The key is to NOT use `os.path.dirname(sys.executable)` as that now points to the folder above `_internal/`.

The UI-SPEC provides the canonical implementation. One important note: the `__file__` path in the `resource_path.py` module will be `src/whisperai/utils/resource_path.py`, so `.parent.parent` gives `src/whisperai/` which is NOT the project root. The base should be `.parent.parent.parent` (up three levels) or navigate relative to project root another way. See the Pitfalls section.

```python
# src/whisperai/utils/resource_path.py
import sys
from pathlib import Path

def get_resource_path(relative_path: str) -> Path:
    """Resolve path to a bundled resource.

    Works in both development (relative to project root) and PyInstaller
    frozen context (relative to sys._MEIPASS / _internal/).
    """
    if getattr(sys, "frozen", False):
        # PyInstaller 6.x: sys._MEIPASS points to the _internal/ subfolder
        # which is where --add-data files land
        base = Path(sys._MEIPASS)
    else:
        # Development: resource_path.py is at src/whisperai/utils/resource_path.py
        # .parent = utils/, .parent.parent = whisperai/, .parent.parent.parent = src/
        # .parent.parent.parent.parent = project root (where locale/ lives)
        base = Path(__file__).parent.parent.parent.parent
    return base / relative_path
```

**Source:** PyInstaller 6.19.0 runtime-information docs (via WebSearch, MEDIUM confidence — Cloudflare blocked direct fetch but content confirmed by multiple search result excerpts)

### Pattern 2: i18n Infrastructure

The `set_language()` function installs `_()` into Python builtins via `gettext.translation().install()`. This must be called before any module-level code executes a `_()` call. The correct place is at the top of `main.py`, before importing from the package.

```python
# src/whisperai/utils/i18n.py
import gettext
import locale
import sys
from .resource_path import get_resource_path

_LOCALE_MAP = {"cs": "cs_CZ", "en": "en_US"}

def detect_system_language() -> str:
    """Return 'cs' if OS UI language starts with 'cs', else 'en'.

    Uses locale.getlocale() (Python 3.11+ safe; getdefaultlocale is deprecated).
    On Windows, falls back to ctypes kernel32 API if locale is unset.
    """
    # First try: locale module (works on macOS and most Linux)
    try:
        locale.setlocale(locale.LC_ALL, "")
        lang_code, _ = locale.getlocale()
        if lang_code and lang_code.lower().startswith("cs"):
            return "cs"
    except locale.Error:
        pass

    # Second try: Windows ctypes (reliable on all Windows versions)
    if sys.platform == "win32":
        try:
            import ctypes
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            # locale.windows_locale maps LANGID -> 'cs_CZ', 'en_US', etc.
            locale_name = locale.windows_locale.get(lang_id, "")
            if locale_name.lower().startswith("cs"):
                return "cs"
        except Exception:
            pass

    return "en"

def set_language(lang_code: str) -> None:
    """Install _() into builtins for the selected language.

    lang_code: 'cs' or 'en'. Falls back to Czech if .mo file not found.
    Must be called before any widget code runs.
    """
    locale_dir = get_resource_path("locale")
    gettext.translation(
        "messages",
        localedir=str(locale_dir),
        languages=[_LOCALE_MAP.get(lang_code, "cs_CZ")],
        fallback=True,
    ).install()
```

**Source:** Python 3.12 gettext stdlib docs (HIGH confidence); locale deprecation via Python cpython issues (HIGH confidence); Windows ctypes approach via WebSearch (MEDIUM confidence — multiple sources confirm pattern)

### Pattern 3: ttkbootstrap Window with Grid Layout

The `ttkbootstrap.Window` constructor accepts `themename` directly. The `place_window_center()` method handles centering. The UI-SPEC mandates a strict three-frame hierarchy using grid layout exclusively.

```python
# src/whisperai/gui/main_window.py
import ttkbootstrap as ttk
from ttkbootstrap.constants import *

class MainWindow:
    def __init__(self, root: ttk.Window) -> None:
        self.root = root
        self._build_layout()

    def _build_layout(self) -> None:
        root = self.root

        # Outer padding frame — fills the entire window
        main_frame = ttk.Frame(root, padding=16)
        main_frame.grid(row=0, column=0, sticky="nsew")

        # Make root expand main_frame
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Three-row layout inside main_frame
        # Row 0: header (fixed height)
        # Row 1: content (expands)
        # Row 2: footer (fixed height)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)  # only content row expands

        # Header
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew")

        app_title_label = ttk.Label(
            header_frame,
            text=_("app.title"),
            font=("", 13, "bold"),
        )
        app_title_label.pack(side=LEFT)

        # Content (placeholder in Phase 1)
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=1, column=0, sticky="nsew")

        placeholder = ttk.Label(
            content_frame,
            text=_("ui.placeholder"),
        )
        placeholder.pack(expand=True)

        # Footer — language switcher right-aligned
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=2, column=0, sticky="ew")

        lang_label = ttk.Label(footer_frame, text=_("ui.language_label"), font=("", 9))
        lang_label.pack(side=RIGHT, padx=(4, 0))

        lang_combo = ttk.Combobox(
            footer_frame,
            values=[_("ui.language_cs"), _("ui.language_en")],
            state="readonly",
            width=12,
        )
        lang_combo.pack(side=RIGHT)
```

**Source:** ttkbootstrap GitHub (window.py inspected via WebFetch — HIGH confidence); Tkinter grid docs (HIGH confidence)

### Pattern 4: main.py Entry Point

```python
# main.py (project root)
import multiprocessing

def main() -> None:
    multiprocessing.freeze_support()  # Required for PyInstaller + ProcessPoolExecutor

    # i18n MUST be initialized before any import of gui modules
    from src.whisperai.utils.i18n import detect_system_language, set_language
    lang = detect_system_language()
    set_language(lang)

    import ttkbootstrap as ttk
    from src.whisperai.gui.main_window import MainWindow

    root = ttk.Window(
        title=_("app.title"),
        themename="flatly",
        size=(720, 480),
        minsize=(480, 320),
        resizable=(True, True),
    )
    root.withdraw()          # hide while centering
    root.place_window_center()
    root.deiconify()         # show centered

    MainWindow(root)
    root.mainloop()

if __name__ == "__main__":
    main()
```

**Source:** ttkbootstrap Window API (HIGH confidence via GitHub source); PyInstaller freeze_support requirement (HIGH confidence via CLAUDE.md)

### Pattern 5: Babel i18n Workflow

**babel.cfg** (project root — Python-only project):

```ini
[python: src/**.py]
[python: main.py]
```

**Full dev workflow:**

```bash
# 1. Extract all _() calls to a template
pybabel extract -F babel.cfg -o locale/messages.pot .

# 2. First-time: create locale catalogs
pybabel init -i locale/messages.pot -d locale -l cs_CZ
pybabel init -i locale/messages.pot -d locale -l en_US

# 3. After editing .po files: compile to binary .mo
pybabel compile -d locale

# 4. When new strings are added: update existing catalogs (merges new keys)
pybabel update -i locale/messages.pot -d locale
pybabel compile -d locale
```

**Source:** Flask Mega-Tutorial i18n chapter (MEDIUM confidence — community source verified against Babel 2.17.0 docs search result)

### Pattern 6: Initial .po File Keys (from UI-SPEC)

The UI-SPEC mandates dot-notation msgid keys. The initial `.po` file for Czech (`locale/cs_CZ/LC_MESSAGES/messages.po`):

```po
# Czech translations for Whisper Přepisovač
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Language: cs_CZ\n"

msgid "app.title"
msgstr "Whisper Přepisovač"

msgid "ui.language_label"
msgstr "Jazyk:"

msgid "ui.language_cs"
msgstr "Čeština"

msgid "ui.language_en"
msgstr "English"

msgid "ui.placeholder"
msgstr "Vítejte. Funkce přepisu budou přidány v dalších fázích."

msgid "ui.language_changed_notice"
msgstr "Jazyk byl změněn. Restartujte aplikaci pro použití změn."
```

The English catalog (`locale/en_US/LC_MESSAGES/messages.po`) mirrors this with English `msgstr` values (including `"Whisper Transcriber"` for `app.title`).

**Source:** UI-SPEC (locked — HIGH confidence)

### Anti-Patterns to Avoid

- **Mixing `pack` and `grid` in the same parent widget:** Causes geometry manager conflict at runtime. UI-SPEC mandates `grid` only inside `main_frame`. Use `pack` only inside leaf frames (like `header_frame` or `footer_frame`) where no `grid` children exist.
- **Calling `set_language()` after importing gui modules:** Any module with a module-level `_()` call will silently use the fallback (empty string) if `install()` hasn't run yet. Always call `set_language()` before any gui import.
- **Using `os.path.dirname(sys.executable)` in resource path:** Broke in PyInstaller 6.0 — executable is now one level above `_internal/`. Use `sys._MEIPASS` for frozen context.
- **Using `locale.getdefaultlocale()`:** Deprecated since Python 3.11, removed in Python 3.15. Will produce a `DeprecationWarning` on Python 3.12 and will not exist in future Python. Use `locale.getlocale()` after `setlocale()`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| OS-native themed widgets | Custom widget drawing with `canvas` | `ttkbootstrap` + `bootstyle` parameter | Cross-platform consistency; handles DPI scaling; supports accessibility |
| Window centering | Manual geometry string calculation before `update_idletasks()` | `root.place_window_center()` | ttkbootstrap Window already provides this method; handles multi-monitor edge cases |
| `.mo` file generation | Hand-writing binary MO format | `pybabel compile -d locale` | MO format is a binary indexed format — must be machine-generated |
| `.po` string extraction | Manually scanning source for `_()` calls | `pybabel extract -F babel.cfg -o locale/messages.pot .` | Will miss strings; becomes unmanageable as codebase grows |
| Frozen/dev path detection | Env var or config flag | `getattr(sys, "frozen", False)` check | PyInstaller sets this attribute reliably; no config needed |

**Key insight:** The gettext/pybabel toolchain has a well-defined split: Babel for extraction and compilation (dev-time), `gettext` stdlib for loading (runtime). Do not try to merge these or skip compilation — `gettext.translation()` requires binary `.mo` files, not `.po` files.

---

## Common Pitfalls

### Pitfall 1: `get_resource_path()` parent traversal depth

**What goes wrong:** The `__file__` for `resource_path.py` is `src/whisperai/utils/resource_path.py`. If you write `Path(__file__).parent.parent` you get `src/whisperai/`, not the project root. `locale/` lives at the project root, so the lookup fails silently (with `fallback=True`) or raises `FileNotFoundError` with `fallback=False`.

**Why it happens:** The UI-SPEC pattern shows `Path(__file__).parent.parent` — this assumed a two-level-deep module. The actual depth is three levels deep (`utils/` inside `whisperai/` inside `src/`).

**How to avoid:** Use `Path(__file__).parent.parent.parent.parent` to reach project root, OR resolve relative to `main.py` location instead. The recommended implementation in Pattern 1 above uses four `.parent` calls and is correct for the `src/whisperai/utils/resource_path.py` depth.

**Warning signs:** `gettext.translation()` called with `fallback=True` silently falls through and `_("app.title")` returns `"app.title"` instead of translated text.

### Pitfall 2: `_()` called before `install()`

**What goes wrong:** If any module has `_("some string")` at module-level (not inside a function), and that module is imported before `set_language()` is called, Python raises `NameError: name '_' is not defined`.

**Why it happens:** Python's builtins namespace doesn't have `_` until `gettext.translation().install()` is called. Module-level code runs at import time.

**How to avoid:** In `main.py`, call `set_language()` as the very first statement before any package import. The Pattern 4 `main.py` structure above enforces this. As a safety net, `i18n.py` itself can define a no-op `_` before `install()` but this is not necessary if import order is correct.

**Warning signs:** `NameError: name '_' is not defined` at launch, OR all translated strings show the raw key (e.g., `"app.title"`) without translation.

### Pitfall 3: `locale.getdefaultlocale()` DeprecationWarning

**What goes wrong:** Python 3.12 emits `DeprecationWarning: Use locale.getlocale() instead` when `getdefaultlocale()` is called. This becomes an error in Python 3.15+.

**Why it happens:** The function was deprecated in Python 3.11 (bpo-90817).

**How to avoid:** Use the two-step approach: `locale.setlocale(locale.LC_ALL, "")` followed by `locale.getlocale()`. Add the Windows `ctypes` fallback for robustness (Pattern 2 above). Do not use `getdefaultlocale()` anywhere.

**Warning signs:** `DeprecationWarning` in stderr during development.

### Pitfall 4: Mixing `pack` and `grid` in `main_frame`

**What goes wrong:** If `content_frame` uses `pack` inside `main_frame` while `header_frame` uses `grid`, Tkinter raises `_tkinter.TclError: cannot use geometry manager pack inside .!frame which already has slaves managed by grid`.

**Why it happens:** A parent widget can only use one geometry manager for its direct children.

**How to avoid:** Inside `main_frame`, use `grid()` exclusively for all three child frames. Inside the child frames (`header_frame`, `footer_frame`), `pack()` is fine because those are separate parent contexts.

**Warning signs:** `TclError` at window creation, often only manifesting when the second widget is added.

### Pitfall 5: PyInstaller 6.x onedir `_internal/` confusion

**What goes wrong:** Adding data files with `datas=[("locale", "locale")]` in the spec file and then loading them with `os.path.dirname(sys.executable) + "/locale"` fails because in PyInstaller 6.0+ the executable is at the top of the bundle but all data files are in the `_internal/` subfolder.

**Why it happens:** PyInstaller 6.0 introduced `_internal/` to keep the top-level folder clean. `sys._MEIPASS` was updated to reflect this, but code using `sys.executable` was not.

**How to avoid:** Always use `sys._MEIPASS` (via `get_resource_path()`) for data files, never `os.path.dirname(sys.executable)`.

**Warning signs:** `FileNotFoundError` for locale directory only when running the packaged binary (works fine in dev).

### Pitfall 6: Forgetting `messages.mo` compilation

**What goes wrong:** Editing `.po` files and testing without running `pybabel compile` means `gettext.translation()` reads stale `.mo` files (or no `.mo` at all if this is a fresh setup). With `fallback=True`, it silently falls through and shows raw keys.

**Why it happens:** `.po` files are human-readable sources; `gettext` reads binary `.mo` files. There is no auto-compilation.

**How to avoid:** Always run `pybabel compile -d locale` after editing `.po` files. Consider a Makefile target or a developer-facing script `scripts/compile-locales.sh`.

**Warning signs:** Translations not updating despite editing `.po` files.

---

## Code Examples

### Window Creation (complete minimal working example)

```python
# Source: ttkbootstrap GitHub window.py (HIGH confidence)
import multiprocessing
import ttkbootstrap as ttk

multiprocessing.freeze_support()

# i18n must be active before Window is created (title uses _())
import gettext
gettext.translation("messages", localedir="locale", languages=["cs_CZ"], fallback=True).install()

root = ttk.Window(
    title=_("app.title"),
    themename="flatly",
    size=(720, 480),
    minsize=(480, 320),
    resizable=(True, True),
)
root.withdraw()
root.place_window_center()
root.deiconify()
root.mainloop()
```

### `ttkbootstrap.Window` Constructor Parameters (confirmed)

```python
# Source: ttkbootstrap GitHub window.py (HIGH confidence)
ttk.Window(
    title: str = "ttkbootstrap",
    themename: str = "litera",   # "flatly" for this project
    size: Optional[Tuple[int, int]] = None,       # (width, height)
    position: Optional[Tuple[int, int]] = None,   # (x, y) — skipped in favor of place_window_center()
    minsize: Optional[Tuple[int, int]] = None,    # (480, 320)
    resizable: Optional[Tuple[bool, bool]] = None,  # (True, True)
)
```

### OS Locale Detection (safe for Python 3.12+)

```python
# Source: Python locale docs + Windows ctypes pattern (MEDIUM confidence)
import locale, sys

def detect_system_language() -> str:
    try:
        locale.setlocale(locale.LC_ALL, "")
        lang, _ = locale.getlocale()
        if lang and lang.lower().startswith("cs"):
            return "cs"
    except locale.Error:
        pass
    if sys.platform == "win32":
        try:
            import ctypes
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            name = locale.windows_locale.get(lang_id, "")
            if name.lower().startswith("cs"):
                return "cs"
        except Exception:
            pass
    return "en"
```

### PyInstaller Spec `datas` Entry for Locale

```python
# Source: PyInstaller 6.19.0 spec file docs (MEDIUM confidence)
# In whisperai.spec:
a = Analysis(
    ["main.py"],
    ...
    datas=[
        ("locale", "locale"),   # copies locale/ tree into _internal/locale/ in the bundle
    ],
    ...
)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `locale.getdefaultlocale()` | `locale.setlocale()` + `locale.getlocale()` | Python 3.11 (deprecated), 3.15 (removed) | Must not use on Python 3.12 target |
| `os.path.dirname(sys.executable)` for bundle path | `sys._MEIPASS` | PyInstaller 6.0 | `_internal/` subfolder changed where data files live |
| `ttkbootstrap` Style-only approach (older) | `ttkbootstrap.Window(themename=...)` + `bootstyle` param | ttkbootstrap 1.x | Window class directly accepts theme; no separate Style object needed |

**Deprecated/outdated:**
- `locale.getdefaultlocale()`: removed in Python 3.15; do not use.
- `os.path.dirname(sys.executable) == sys._MEIPASS`: false assumption since PyInstaller 6.0.

---

## Open Questions

1. **`__main__.py` for `python -m whisperai` support**
   - What we know: CONTEXT.md lists this as Claude's Discretion
   - What's unclear: Whether the planner should include creation of `__main__.py` in Phase 1 tasks
   - Recommendation: Include it — it's a two-line file that enables clean `python -m whisperai` invocation during dev and is a best practice for packages. Content: `from .app import main; main()` (or equivalent).

2. **Language switch restart mechanism**
   - What we know: D-02 says restart is acceptable; UI-SPEC says show `ui.language_changed_notice` string
   - What's unclear: Whether Phase 1 implements actual restart (using `os.execv`) or just shows the notice without acting
   - Recommendation: Phase 1 should persist the language selection to a temp file or env var, show the notice, and instruct the user to restart manually. Actual `os.execv` restart is a Phase 3 concern (settings persistence). This keeps Phase 1 minimal.

3. **Language selection persistence between sessions in Phase 1**
   - What we know: Phase 1 auto-detects from OS locale on first launch; settings persistence (UI-05) is Phase 3
   - What's unclear: If user switches language in the Combobox but doesn't restart, and then restarts, it reverts to OS locale detection — is this acceptable?
   - Recommendation: Yes, this is acceptable for Phase 1. The CONTEXT.md explicitly defers live-reload and settings persistence. Phase 3 will add a settings file that stores the language preference.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python 3.12.x | Runtime | Not verified on dev machine | Dev machine has Python 3.9.13 (from shell probe) | Install Python 3.12.x via pyenv-win; 3.9 cannot be used for this project |
| pip | Package management | Yes | 25.3 (Python 3.14 pip) | — |
| ttkbootstrap 1.20.2 | GUI theming | Not installed (greenfield) | — | Must install: `pip install ttkbootstrap==1.20.2` |
| Babel (pybabel) | .po/.mo workflow | Not installed | — | Must install: `pip install Babel` |
| PyInstaller 6.19.0 | Packaging (Phase 4) | Not installed | — | Not needed for Phase 1 runtime; needed only in Phase 4 |

**Missing dependencies with no fallback:**
- Python 3.12.x: Dev machine has Python 3.9.13. Project requires 3.12.x. Must install before Phase 1 can run. Use `pyenv-win install 3.12.x` on Windows.

**Missing dependencies with fallback:**
- PyInstaller 6.19.0: Not required until Phase 4. Phase 1 runs from source only.

---

## Sources

### Primary (HIGH confidence)
- ttkbootstrap GitHub (israel-dryer/ttkbootstrap) — `window.py` source, `Window.__init__` signature, `place_window_center()` implementation, version 1.20.2 confirmed
- Python 3.12 gettext stdlib docs (docs.python.org/3/library/gettext.html) — `translation().install()` behavior, `fallback` parameter, builtins installation
- CLAUDE.md project instructions — tech stack constraints, version compatibility table, packaging patterns (all HIGH — project authority)
- UI-SPEC (01-UI-SPEC.md) — window layout, i18n infrastructure contract, copywriting keys (HIGH — locked design contract)

### Secondary (MEDIUM confidence)
- PyInstaller 6.x `_internal/` change — confirmed via multiple WebSearch result excerpts from official pyinstaller.org docs; could not directly fetch due to Cloudflare blocks
- PyInstaller `datas=` spec file syntax — confirmed via WebSearch against pyinstaller.org/en/stable/spec-files.html
- pybabel workflow (extract/init/compile) — confirmed via Flask Mega-Tutorial (community source) and Babel 2.17.0 search result excerpts
- Windows ctypes locale detection — multiple sources agree on `GetUserDefaultUILanguage()` + `locale.windows_locale` pattern

### Tertiary (LOW confidence)
- Exact behavior of `locale.setlocale()` on macOS in all edge cases — not directly verified with a macOS Python 3.12 environment; the ctypes fallback pattern is Windows-only

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all versions confirmed via PyPI/GitHub, CLAUDE.md provides authoritative source
- Architecture: HIGH — patterns derived from official docs and locked design contract (UI-SPEC)
- Pitfalls: HIGH — each pitfall is tied to a specific documented change or stdlib behavior
- OS locale detection: MEDIUM — multiple sources confirm the pattern but macOS edge cases not verified on actual hardware

**Research date:** 2026-03-28
**Valid until:** 2026-04-28 (stable libraries; ttkbootstrap and PyInstaller release cadence is slow)

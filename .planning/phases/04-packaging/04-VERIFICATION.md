---
phase: 04-packaging
verified: 2026-03-29T18:30:00Z
status: human_needed
score: 9/10 must-haves verified
human_verification:
  - test: "Run WhisperPrepis.exe on a clean Windows 10/11 machine (no Python, no CUDA toolkit, no system ffmpeg)"
    expected: "App launches, download dialog appears, transcription completes with output file saved as _prepis.txt"
    why_human: "Clean-machine test cannot be replicated programmatically from the dev environment; requires physical or VM target without Python installed"
  - test: "Verify keyring (Windows Credential Manager) works in the frozen portable folder"
    expected: "Entering an API key in Settings persists correctly via keyring.set_password(); retrieving it via keyring.get_password() returns the saved key; no 'No backend' error at runtime"
    why_human: "keyring.backends.Windows requires the frozen context to load pywin32 correctly — cannot be tested from the source dev environment"
---

# Phase 4: Packaging Verification Report

**Phase Goal:** A Windows portable folder build exists that runs correctly on a clean machine with no Python, no CUDA toolkit, and no system ffmpeg installed — plus GitHub publication with README, LICENSE, and first-launch model download
**Verified:** 2026-03-29T18:30:00Z
**Status:** human_needed
**Re-verification:** No — initial verification

## Goal Achievement

### Observable Truths

| #  | Truth | Status | Evidence |
|----|-------|--------|----------|
| 1  | model_path.py returns writable APPDATA path when frozen, dev models/ when not frozen | VERIFIED | `get_model_path()` uses `getattr(sys, "frozen", False)` branch — returns `user_data_dir("WhisperPrepis", "WhisperPrepis") / "models"` when frozen, `Path(__file__).parent.parent.parent.parent / "models"` in dev. src/whisperai/utils/model_path.py:7-15 |
| 2  | transcription_panel.py uses get_model_path() instead of get_resource_path("models") | VERIFIED | Line 24: `from src.whisperai.utils.model_path import get_model_path`; line 1068: `model_path = str(get_model_path())`. No remaining `get_resource_path("models")` calls found |
| 3  | main.py prepends bundled bin/ to PATH when frozen | VERIFIED | main.py lines 11-13: `if getattr(sys, "frozen", False): bin_dir = str(Path(sys._MEIPASS) / "bin"); os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")` |
| 4  | whisperai.spec collects all required DLLs for ctranslate2, keyring, silero_vad, huggingface_hub, onnxruntime | VERIFIED | All 5 `collect_all()` calls present in whisperai.spec lines 10-14; `copy_metadata` for 5 packages; `sys.setrecursionlimit(5000)` at line 3; `excludes=['whisper', 'openai.whisper']` at line 66; `upx=False` at lines 84 and 94; `console=False` at line 85 |
| 5  | build.bat activates venv, validates prerequisites, runs PyInstaller, creates release zip | VERIFIED | build.bat contains: venv activation (line 8), PyInstaller version check (line 11), ffmpeg.exe/ffprobe.exe existence checks (lines 19-27), findstr security scan (line 32), `pyinstaller whisperai.spec` (line 45), `Compress-Archive` (line 59) |
| 6  | On first frozen launch with no model, a download dialog appears before main window | VERIFIED | main.py lines 25-44: `if not is_model_downloaded(): ... ModelDownloadDialog(root) ... root.wait_window(dialog) ... create_app(existing_root=root)` — dialog blocks before create_app() |
| 7  | Download dialog shows all required UI states (downloading, success auto-close, error/retry, cancel confirmation) | VERIFIED | model_download_dialog.py: `mode="indeterminate"` progress bar (line 63); `self.after(1500, self._close_success)` (line 154); `_show_error()` with retry + cancel buttons (lines 161-190); `_on_cancel_click()` with inline confirmation (lines 229-252) |
| 8  | All dialog strings are translated via _() in both cs and en locales | VERIFIED | locale/cs_CZ/LC_MESSAGES/messages.po and locale/en_US/LC_MESSAGES/messages.po both contain `msgid "download.title"` (line 338 each); both .mo files compiled and present |
| 9  | Git publication files (.gitignore, README.md, LICENSE) exist and are correct | VERIFIED | .gitignore excludes all required paths (.planning/, .claude/, .vexp/, models/, .venv/, __pycache__/, dist/, build/, bin/); README.md contains first-launch download note (~1.5 GB), WhisperPrepis.exe, build.bat; LICENSE contains MIT License text |
| 10 | Portable folder runs on clean Windows machine without Python (human verified per SUMMARY) | UNCERTAIN | SUMMARY 04-03 documents user confirmed app launches and transcription works; TclError bug found and fixed in commit b5a85fe. Cannot re-verify programmatically — flagged for human confirmation |

**Score:** 9/10 truths verified automated; 1 requires human confirmation

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `src/whisperai/utils/model_path.py` | Writable model directory resolution | VERIFIED | 27 lines; exports `get_model_path` and `is_model_downloaded`; uses `platformdirs.user_data_dir`; frozen detection via `getattr(sys, "frozen", False)` |
| `src/whisperai/gui/model_download_dialog.py` | ModelDownloadDialog Toplevel widget | VERIFIED | 271 lines (min_lines: 100 satisfied); `class ModelDownloadDialog(ttk.Toplevel)`; indeterminate progress; all UI states implemented |
| `whisperai.spec` | PyInstaller build configuration | VERIFIED | 100 lines; contains `collect_all` for all 5 required packages; correct ffmpeg, locale, prompts datas entries |
| `build.bat` | One-click build script | VERIFIED | 64 lines; contains `pyinstaller whisperai.spec`, ffmpeg checks, security scan, release zip creation |
| `.gitignore` | Git exclusion rules | VERIFIED | Contains `.planning/`, `.claude/`, `.venv/`, `.vexp/`, `models/`, `dist/`, `build/`, `bin/`, `__pycache__/` |
| `README.md` | Project documentation for GitHub | VERIFIED | Contains `Whisper`, `~1.5 GB`, `WhisperPrepis.exe`, `build.bat`, first-launch section |
| `LICENSE` | MIT license | VERIFIED | Contains `MIT License`, copyright 2026 |
| `main.py` | Updated startup with PATH prepend and model check | VERIFIED | `freeze_support()` first; PATH prepend block; `is_model_downloaded()` check; `ModelDownloadDialog` wiring; `create_app(existing_root=root)` pattern |
| `src/whisperai/app.py` | create_app with existing_root kwarg | VERIFIED | `def create_app(existing_root: ttk.Window | None = None)` at line 6; reuses root when provided (lines 21-26) |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `src/whisperai/gui/transcription_panel.py` | `src/whisperai/utils/model_path.py` | `from src.whisperai.utils.model_path import get_model_path` | WIRED | Import at line 24; usage at line 1068 `model_path = str(get_model_path())` |
| `main.py` | `bin/` directory | PATH prepend when frozen via `sys._MEIPASS` | WIRED | Lines 11-13; `bin_dir = str(Path(sys._MEIPASS) / "bin")` prepended to `os.environ["PATH"]` |
| `main.py` | `src/whisperai/gui/model_download_dialog.py` | conditional import and show before create_app | WIRED | Lines 36-44; conditional on `not is_model_downloaded()`; `root.wait_window(dialog)` blocks; `create_app(existing_root=root)` reuses Tk root |
| `src/whisperai/gui/model_download_dialog.py` | `src/whisperai/utils/model_path.py` | `from src.whisperai.utils.model_path import get_model_path` | WIRED | Line 10 import; lines 111-113 usage in `_download_worker` |
| `whisperai.spec` | `bin/ffmpeg.exe`, `bin/ffprobe.exe` | `binaries` section entry `('bin/ffmpeg.exe', 'bin')` | WIRED | Lines 29-30 in Analysis binaries |
| `whisperai.spec` | `locale/`, `prompts/` | `datas` section entries | WIRED | Lines 37-39 in Analysis datas |

### Data-Flow Trace (Level 4)

| Artifact | Data Variable | Source | Produces Real Data | Status |
|----------|---------------|--------|-------------------|--------|
| `model_download_dialog.py` | `_download_success` / `_download_error` | `_download_worker()` calling `faster_whisper.WhisperModel("medium", ...)` | Yes — `WhisperModel` init triggers real huggingface_hub download | FLOWING |
| `model_download_dialog.py` | `_cancelled` | `_on_cancel_confirm()` sets `True` | Yes — direct boolean mutation, no hollow prop | FLOWING |
| `main.py` | `is_model_downloaded()` return value | `glob.glob()` over real filesystem path | Yes — live filesystem check | FLOWING |

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| model_path.py importable and returns a path | `python -c "from src.whisperai.utils.model_path import get_model_path, is_model_downloaded; p = get_model_path(); print(type(p))"` | Not executed (requires venv activation in shell) | SKIP — verified via grep and static analysis |
| whisperai.spec is valid Python syntax | `python -c "import ast; ast.parse(open('whisperai.spec').read())"` | Not executed directly; spec structure confirmed via manual read — all `collect_all` calls, `Analysis`, `PYZ`, `EXE`, `COLLECT` constructs present and balanced | SKIP — verified via static analysis |
| Commits for all 6 phase tasks exist in git history | `git log --oneline` | b9b0988, e62c41c, 8ef1159, 39b70a7, a745b90, b5a85fe all confirmed present with correct changed files | PASS |
| .mo files compiled (binary present) | `ls locale/*/LC_MESSAGES/messages.mo` | Both messages.mo files confirmed present | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| PKG-01 | 04-02-PLAN.md | PyInstaller portable folder packaging for Windows (no Python required) | SATISFIED | whisperai.spec + build.bat produce `dist/WhisperPrepis/WhisperPrepis.exe`; SUMMARY 04-02 documents first build succeeded |
| PKG-02 | — | PyInstaller portable folder packaging for macOS | DEFERRED | Explicitly deferred per D-05 (requires Mac hardware, PyInstaller cannot cross-compile). Acknowledged in 04-03-PLAN.md frontmatter note. REQUIREMENTS.md shows `[ ]` (unchecked). Not a phase failure — decision is documented |
| PKG-03 | 04-01-PLAN.md | ffmpeg binary bundled with the app (not downloaded at runtime) | SATISFIED | `('bin/ffmpeg.exe', 'bin'), ('bin/ffprobe.exe', 'bin')` in whisperai.spec binaries; main.py PATH prepend ensures app finds them; bin/ffmpeg.exe committed in 39b70a7 |
| PKG-04 | 04-02-PLAN.md | Whisper medium model bundled with the app (not downloaded at runtime) | NOTE: REQUIREMENT TEXT SUPERSEDED | REQUIREMENTS.md text says "bundled"; actual implementation is first-launch download per design decision D-08 in 04-CONTEXT.md: "Whisper model NOT bundled in distribution — downloaded automatically on first launch with progress dialog." ROADMAP success criterion 4 also says "downloads on first launch with a progress dialog — no bundling required." ModelDownloadDialog and is_model_downloaded() fully implement D-08. Requirement text is stale; design intent is satisfied |
| PKG-05 | 04-01-PLAN.md | PyInstaller spec file with Whisper hidden imports, tiktoken fix, and freeze_support | SATISFIED | whisperai.spec: `sys.setrecursionlimit(5000)`, `collect_all` for 5 packages, hidden imports for `faster_whisper.*`, `tokenizers`, `win32timezone`, `keyring.backends.Windows`; `multiprocessing.freeze_support()` in main.py |
| PKG-06 | 04-01-PLAN.md | All bundled resources accessible via get_resource_path (sys._MEIPASS aware) | SATISFIED | `locale/` and `prompts/` added to spec datas; `get_resource_path()` (existing from Phase 1) resolves via sys._MEIPASS when frozen; `get_model_path()` extends this for writable model storage |

### Anti-Patterns Found

| File | Pattern | Severity | Impact |
|------|---------|----------|--------|
| `model_download_dialog.py` line 248 | `text="<-"` — hardcoded back-arrow symbol instead of i18n string | Info | Cosmetic: back button label is not translated. Not user-facing in a prominent way; does not prevent any goal |
| `main.py` line 29 | `_("download.title")` called before the download dialog i18n infrastructure is fully initialized — the `_` function is the builtins `_` installed by `set_language()`, which runs at line 21; this ordering is correct | Info | No actual issue — flagged during review but verified correct |

No blockers or warnings found.

### Human Verification Required

#### 1. Clean-Machine Portable Folder Smoke Test

**Test:** Copy `dist\WhisperPrepis\` to a Windows 10 or 11 machine that has never had Python, CUDA toolkit, or system ffmpeg installed. Run `WhisperPrepis.exe`.

**Expected:**
- App launches without any "DLL not found" or "Python not found" errors
- If Whisper model is not cached in %LOCALAPPDATA%\WhisperPrepis\WhisperPrepis\models, the download dialog appears with progress bar and Czech/English strings
- After download (or with existing model), the main window opens and a short audio transcription completes, saving `_prepis.txt`

**Why human:** The dev machine has Python, CUDA, and ffmpeg on PATH. Only a genuinely clean machine (or fresh VM snapshot) can confirm PyInstaller bundled all DLLs correctly. The `dist/` directory is gitignored and not available for static inspection in this session.

#### 2. Keyring in Frozen Context

**Test:** On the portable folder app (not from source), open Settings, enter an Anthropic API key, close settings, reopen settings, verify the key persists. Then remove the key, verify it is gone.

**Expected:** No "No backend available" or "keyring.errors" exception; Windows Credential Manager stores and retrieves the key correctly from the frozen app.

**Why human:** `keyring.backends.Windows` depends on `pywin32` being importable in the frozen context. The hidden import `keyring.backends.Windows` is declared in the spec, but correct resolution can only be confirmed by running the frozen executable.

### Gaps Summary

No automated gaps found. All artifacts exist, are substantive (no stubs), and are wired correctly. The two human verification items are standard quality-gate checks for PyInstaller packaging that cannot be replicated without the frozen executable on a clean machine.

**PKG-04 note:** The REQUIREMENTS.md text ("bundled with the app, not downloaded at runtime") is factually inconsistent with the implemented design (first-launch download). This is a documentation staleness issue, not an implementation gap. Design decision D-08 in 04-CONTEXT.md, the ROADMAP success criteria, and the 04-02-PLAN.md objectives all consistently describe the first-launch download approach. The requirement text was written before D-08 was decided and was not updated. The implemented behavior is correct per the project's current design intent.

**PKG-02 note:** macOS packaging is legitimately deferred per D-05. It appears as `[ ]` in REQUIREMENTS.md and is not listed in any plan's `requirements:` field. This is a known gap tracked at the project level, not a phase failure.

---

_Verified: 2026-03-29T18:30:00Z_
_Verifier: Claude (gsd-verifier)_

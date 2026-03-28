# Project Research Summary

**Project:** Whisper Přepisovač
**Domain:** Cross-platform desktop audio transcription app (Python + Tkinter + Whisper + Claude API)
**Researched:** 2026-03-28
**Confidence:** HIGH

## Executive Summary

Whisper Přepisovač is a Czech-first, offline-capable desktop app that transcribes audio files via local OpenAI Whisper inference and optionally refines output using the Anthropic Claude API. The expert approach for this class of app is a layered architecture with strict thread separation: all Whisper inference runs in worker threads (never the main thread), all GUI updates go through a `queue.Queue` polled by `root.after()`, and all bundled resources (model, ffmpeg, locale files) are accessed through a `sys._MEIPASS`-aware path helper. Python 3.12 + openai-whisper 20250625 + PyTorch 2.11 + ttkbootstrap is the correct, version-locked stack — deviating from these versions introduces known incompatibilities.

The recommended approach is to build the project in four phases: foundation and infrastructure first (utilities, i18n, project skeleton), then the core transcription loop (Whisper service, worker thread, queue-based GUI updates), then the Claude cleanup path and API key management, and finally the PyInstaller portable packaging. This ordering is driven by hard architectural dependencies: i18n must exist before the first widget is written, the threading architecture must be correct before parallel processing is added, and packaging must be validated on clean machines before any distribution milestone is called done. Every phase has a "does it work on a machine with no Python?" verification gate.

The primary risks are packaging-time failures that only appear on clean machines: Whisper asset files and tiktoken hidden imports not bundled, ffmpeg not on PATH, and keyring backend discovery broken in frozen apps. None of these are hard to fix once known, but all are invisible in development. The second risk is Whisper hallucinations on silent or low-speech audio — this is a known upstream bug that requires VAD preprocessing and must be addressed in the core transcription phase, not discovered by users post-launch. MPS operator coverage on Apple Silicon is incomplete for openai-whisper and requires a runtime probe beyond `torch.backends.mps.is_available()`.

---

## Key Findings

### Recommended Stack

The stack is fully constraint-driven and well-researched. Python 3.12 is the mandatory runtime — 3.13 has known openai-whisper incompatibilities and 3.10.0 has a PyInstaller-specific bug. PyTorch 2.11 provides both CUDA and MPS GPU backends via a single detection API. ttkbootstrap 1.20.2 transforms bare Tkinter into a polished, modern UI without adding binary dependencies. The `keyring` library abstracts Windows Credential Manager and macOS Keychain behind a single API — no custom crypto needed. All supporting libraries (concurrent.futures, threading, queue, gettext, pathlib) are stdlib.

**Core technologies:**
- **Python 3.12.x:** Runtime — best compatibility across all required libraries; avoid 3.13 and 3.10.0
- **openai-whisper 20250625:** Audio transcription — project constraint; medium model gives best Czech accuracy at ~1.5 GB
- **PyTorch 2.11.0:** GPU backend — required by Whisper; provides `torch.cuda` (CUDA) and `torch.backends.mps` (Apple Silicon) detection
- **ttkbootstrap 1.20.2:** Modern Tkinter theming — eliminates the grey-box default Tkinter look without platform hacks
- **anthropic 0.86.0:** Claude API client — used exclusively for the "Přepsat + Upravit" cleanup path; app must work without it
- **keyring 25.7.0:** OS-native API key storage — Windows Credential Manager / macOS Keychain via one API
- **PyInstaller 6.19.0:** Portable folder packaging — `--onedir` mode is required; `--onefile` would be unacceptably slow with a 1.5 GB model
- **ffmpeg 7.x (static binary):** Audio decoding — must be bundled, not assumed to be on PATH; PATH must be patched at startup
- **gettext (stdlib):** i18n — standard Python mechanism; `.mo` files compiled with Babel (dev-only) and bundled

See `.planning/research/STACK.md` for full version compatibility matrix and PyInstaller spec patterns.

### Expected Features

No existing Whisper desktop app combines LLM cleanup with structured dual-file output, Czech-first design, and cross-platform portable distribution. This is a genuine competitive gap. The Claude-powered "Přepsat + Upravit" path with executive summary is the primary differentiator.

**Must have (table stakes):**
- Load audio files via dialog (multi-file and folder) — users expect this as the entry point
- Support .mp3, .wav, .m4a, .ogg — the four formats anyone with meeting/interview recordings will have
- File list with čeká / zpracovává / hotovo status — absence feels broken
- Real-time processing log — 30+ minute audio with no feedback = users assume the app crashed
- Save output to text file with configurable output folder — the whole point of transcription
- Clear error messages surfaced in the log — silent failures are common in naive implementations
- App runs without network connection (core Whisper path) — primary reason users choose local inference
- Persistent settings between sessions (API key via keyring, preferences via config file)

**Should have (competitive differentiators):**
- Claude API cleanup: grammar, paragraphs, summary — the "Přepsat + Upravit" path is hours of work saved
- Structured dual-file output: `_prepis.txt` (raw) + `_upraveno.txt` (edited + summary + diff) — no competitor does this
- Czech-first language handling — medium model hard-set to Czech; most tools treat Czech as an afterthought
- Switchable Czech/English UI — rare in local Whisper tools; must be designed in from day one
- GPU auto-detection (CUDA/MPS/CPU fallback) — users should not need to know what CUDA is
- OS-native API key storage — rare in Python desktop apps; keyring is the professional approach
- Portable folder distribution (no install required) — critical for non-technical team members

**Defer (v2+):**
- Speaker diarization — high complexity, Czech model reliability uncertain; validate demand first
- Multi-language transcription — only needed if audience expands beyond Czech speakers
- Live microphone recording — separate engineering domain; not the defined audience use case
- In-app transcript editor — Claude cleanup path handles this better; Tkinter rich text is a significant subproject
- Video file support — scope expansion risk; recommend manual ffmpeg pre-processing for v1
- Parallel file processing (configurable 1-N) — add after core loop is validated; design threading correctly from the start

See `.planning/research/FEATURES.md` for full competitor matrix and feature dependency graph.

### Architecture Approach

The architecture is a clean four-layer design: GUI Layer (main thread only, Tkinter widgets), App Controller (event bus, queue polling via `root.after(100ms)`), Worker Layer (background threads for Whisper and Claude), and Service/Utility Layer (stateless domain logic, testable without GUI). The critical invariant is that worker threads never touch Tkinter widgets — all state flows through a central `queue.Queue`. Each parallel Whisper worker loads its own model instance (model inference is not thread-safe). A `get_resource_path()` utility at `utils/paths.py` is the single place that knows about `sys._MEIPASS` and must be used for every bundled asset reference.

**Major components:**
1. **App Controller (`app.py`)** — wires GUI events to workers, polls result queue with `root.after()`, dispatches all widget mutations
2. **Transcription Worker Pool (`workers/transcription.py`)** — one thread per parallel slot; each loads its own Whisper model instance; communicates exclusively via `queue.Queue`
3. **Claude Cleanup Worker (`workers/cleanup.py`)** — single sequential thread; calls Claude API, parses structured response; API key retrieved from keyring
4. **Whisper Service (`services/whisper_service.py`)** — pure function wrapper: GPU detection, model load, `model.transcribe()`, returns segments
5. **Claude Service (`services/claude_service.py`)** — stateless: builds cleanup prompt, sends API call, parses `{edited, summary, diff}` response
6. **i18n Module (`i18n/`)** — installs `_()` globally at startup; must exist before any widget is created
7. **PyInstaller Bootstrap (`utils/paths.py`)** — resolves `sys._MEIPASS` for all bundled resources; called by every service that accesses model/ffmpeg/locale

Build order: `utils/` → `services/config + keyring` → `i18n/` → `services/whisper + file` → `services/claude` → `workers/` → `gui/` panels → `app.py` → `.spec` + packaging.

See `.planning/research/ARCHITECTURE.md` for full data flow diagrams and anti-pattern catalogue.

### Critical Pitfalls

All 11 pitfalls in PITFALLS.md are verified against official documentation. The top 5 by recovery cost and frequency:

1. **Tkinter widget updates from worker threads** — causes non-deterministic crashes that only appear under load or on macOS; recovery cost is HIGH (full architecture refactor). Prevent by using the `queue.Queue` + `root.after()` pattern from day one. Never call any widget method from a background thread.

2. **Whisper hallucinations on silence / sparse speech** — Whisper produces fabricated subtitle text on recordings with long pauses; affects real Czech meeting recordings. Prevent by adding VAD preprocessing (`silero-vad` or `webrtcvad`) and passing `condition_on_previous_text=False`. Design this into the core transcription phase.

3. **PyInstaller: Whisper assets and tiktoken hidden imports not bundled** — app crashes on clean machines with `tiktoken_ext` or `mel_filters.npz` errors. Easy fix (2 lines in `.spec`) but invisible in development. Must be verified as part of the first packaging milestone on a clean VM.

4. **MPS backend missing required operators on macOS** — `torch.backends.mps.is_available()` returns `True` but `openai-whisper` transcription crashes with `NotImplementedError` for `aten::repeat_interleave`. Requires a runtime probe beyond the availability check. Must be tested on actual Apple Silicon hardware.

5. **keyring backend discovery broken in frozen app** — `keyring.set_password()` raises `NoKeyringError` in the PyInstaller build because entry point metadata is not collected. Fix: add `--collect-all keyring` and `--hidden-import keyring.backends.Windows/macOS` to spec. On macOS, unsigned apps cannot access Keychain without codesigning.

Additional notable pitfalls: `multiprocessing.freeze_support()` must be called before any threading code in `main.py` or Windows will spawn an infinite process fork bomb; CUDA DLL resolution fails on end-user Windows machines with different CUDA versions (ship CPU build by default, CUDA build as optional); bundled ffmpeg binary must be placed on PATH at app startup via `os.environ["PATH"]` prepend.

See `.planning/research/PITFALLS.md` for full pitfall catalogue, recovery cost estimates, and the "Looks Done But Isn't" checklist.

---

## Implications for Roadmap

Based on combined research, a 5-phase structure is recommended. The ordering is derived from hard architectural dependencies (i18n before widgets, threading before parallelism, resource path abstraction before any bundled asset access) and pitfall-phase mappings from PITFALLS.md.

### Phase 1: Foundation and Infrastructure

**Rationale:** Three things must exist before any other code is written: (1) the `get_resource_path()` utility — hardcoding any path now creates mechanical search-replace work later; (2) the i18n module — retrofitting switchable language onto an app with hardcoded strings is painful and affects every widget; (3) project skeleton with correct module boundaries — the separation between `gui/`, `workers/`, `services/`, and `utils/` must be established before any feature code lands.
**Delivers:** Runnable skeleton app with correct architecture, translatable string infrastructure, and resource path abstraction in place.
**Addresses:** i18n design constraint (FEATURES.md), build order requirements (ARCHITECTURE.md)
**Avoids:** Hardcoded path pitfall (PITFALLS.md #10), i18n retrofit pain (FEATURES.md dependency notes)

### Phase 2: Core Transcription Loop

**Rationale:** This is the minimum viable product — everything else builds on it. The threading architecture (worker thread, queue, `root.after()` poll) must be correct before parallelism is added. Whisper hallucination mitigation (VAD preprocessing, `condition_on_previous_text=False`) must be included here, not deferred, because retrofitting it after users report garbage output is a trust problem.
**Delivers:** Working single-file transcription with correct threading, GPU auto-detection (CUDA/MPS/CPU with explicit logging), real-time log panel, file list with status, `_prepis.txt` output, VAD hallucination mitigation.
**Uses:** `openai-whisper 20250625`, `PyTorch 2.11.0`, `threading` + `queue` (stdlib), `pathlib`
**Implements:** TranscriptionWorker, WhisperService, FileService, queue/after() pattern
**Avoids:** Tkinter thread-safety pitfall (#4), hallucination pitfall (#9), model load path pitfall (#10), `freeze_support()` pitfall (#3 — add immediately)

### Phase 3: Claude Cleanup Path and API Key Management

**Rationale:** The "Přepsat + Upravit" differentiator depends on the raw transcription path being solid. This phase adds ClaudeService, ClaudeWorker, keyring-based API key storage, and the lazy first-use prompt flow. The key architectural requirement is that the app must continue to function completely without an API key — Claude is an enhancement, not a dependency.
**Delivers:** "Přepsat + Upravit" button, Claude cleanup producing `_upraveno.txt` with edited text + executive summary + diff, OS-native API key storage via keyring, first-run prompt flow, graceful degradation when key is absent.
**Uses:** `anthropic 0.86.0`, `keyring 25.7.0`
**Implements:** ClaudeService, ClaudeWorker, KeyringService, lazy key prompt pattern (ARCHITECTURE.md Pattern 3)
**Avoids:** Plaintext API key storage (PITFALLS.md security section), Claude rate-limit pitfall (add exponential backoff)

### Phase 4: Settings, Batch Processing, and UX Polish

**Rationale:** Batch queue and parallel processing are deferred until the single-file core is validated. Configurable parallelism requires the threading architecture to already be correct. Settings panel (output folder, language toggle, parallelism slider) and UX details (model load spinner, GPU device logging, overwrite confirmation) are grouped here as they share the same UI surface.
**Delivers:** Configurable output folder with auto-naming, Czech/English language toggle, model load progress indication, parallel file processing (1-N configurable, default 1), keyboard shortcuts for core actions, drag-and-drop file loading, overwrite confirmation dialog.
**Uses:** `concurrent.futures.ProcessPoolExecutor` for parallel workers, `configparser` + `platformdirs` for settings
**Implements:** ConfigService, Settings panel, parallel transcription worker pool
**Avoids:** Parallel CUDA OOM pitfall (cap GPU workers to 1, PITFALLS.md performance traps), model reload-per-file trap (load once, reuse)

### Phase 5: PyInstaller Portable Packaging and Distribution

**Rationale:** Packaging is its own engineering phase for this project. The `.spec` file must declare Whisper assets, tiktoken hidden imports, ffmpeg binaries, locale files, and model weights. Verification must happen on clean machines (no Python, no CUDA toolkit, no system ffmpeg) for both Windows and macOS. macOS Gatekeeper and keyring codesigning are distribution decisions that must be made before shipping.
**Delivers:** Portable folder build for Windows (`_CUDA` optional variant) and macOS, verified on clean VMs, `_prepis.txt` and `_upraveno.txt` correct in frozen build, keyring working in frozen context, ffmpeg bundled and auto-found, macOS Gatekeeper strategy documented.
**Uses:** `PyInstaller 6.19.0`, bundled static ffmpeg 7.x (Windows: BtbN build, macOS: evermeet.cx build)
**Avoids:** All 5 packaging pitfalls (Whisper assets, tiktoken, freeze_support, ffmpeg PATH, keyring backend), model path pitfall, macOS Gatekeeper pitfall

### Phase Ordering Rationale

- **Foundation before features:** i18n and `get_resource_path()` are cross-cutting concerns that touch every other component. Building them first eliminates the two most expensive retrofits identified in research.
- **Single-file before batch:** The batch queue is a loop around the single-file path. Getting threading correct for one file is prerequisite to parallelism being safe.
- **Transcription before Claude:** Claude's input is the raw transcript. The core path must be solid and independently verifiable before the cleanup path is added.
- **Features before packaging:** The `.spec` file should reflect final feature set. Packaging incrementally is possible but each round of spec changes requires a clean-machine test — minimize rounds by completing features first.
- **Pitfall-driven gates:** Each phase ends with a specific verification checklist derived from PITFALLS.md. Phase 2 must pass the threading test (3 parallel files, no TclError). Phase 5 must pass the clean-VM test (no Python, no CUDA toolkit).

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 5 (Packaging):** macOS codesigning + notarization workflow is documented but version-specific; the entitlements required for Python/PyInstaller hardened runtime need verification against current Apple toolchain. Decision on whether to pursue Apple Developer ID ($99/year) or internal-only distribution changes the scope by 2-3 days.
- **Phase 3 (Claude Cleanup):** The structured output format (edited text + executive summary + diff in a single `_upraveno.txt`) requires prompt engineering to produce reliable, parseable output. The exact prompt design and response parsing strategy needs a research or spike phase.

Phases with standard patterns (skip research-phase):
- **Phase 1 (Foundation):** `gettext` i18n, `sys._MEIPASS` path pattern, and module skeleton are thoroughly documented in official Python and PyInstaller docs.
- **Phase 2 (Core Transcription):** Whisper threading pattern, queue/after() architecture, and GPU detection are all HIGH confidence with code examples in ARCHITECTURE.md and STACK.md.
- **Phase 4 (Settings/Batch):** `configparser` + `platformdirs`, `ProcessPoolExecutor`, and ttkbootstrap widgets are standard patterns with official docs.

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All versions verified against PyPI and official docs as of 2026-03-28. Version pinning rationale (Python 3.12, not 3.13) confirmed against openai-whisper GitHub issues. |
| Features | HIGH (table stakes), MEDIUM (differentiators) | Table stakes derived from established UX patterns. Competitor analysis (Buzz, MacWhisper, Whisper-Writer) provides solid baseline. Differentiator value is inferred from competitive gap analysis — needs market validation. |
| Architecture | HIGH | Threading model and Tkinter thread-safety are official Python docs. Whisper thread-safety confirmed in official openai/whisper discussions. PyInstaller patterns are from official docs with community-verified workarounds. |
| Pitfalls | HIGH | All 11 pitfalls verified against official sources (PyInstaller docs, openai/whisper GitHub, keyring issue tracker, PyTorch forums). Recovery costs are estimated, not measured. |

**Overall confidence:** HIGH

### Gaps to Address

- **MPS operator coverage:** The specific set of `aten::` operators that openai-whisper medium model requires on MPS is not fully documented. The runtime probe approach (attempt a small tensor operation before committing to MPS) is the recommended mitigation, but the exact probe implementation needs validation on Apple Silicon hardware.
- **Claude prompt design:** The structured output format for `_upraveno.txt` (edited text + summary + diff) requires prompt engineering. The exact prompt and response parsing logic is not researched — this is a spike task in Phase 3.
- **keyring + macOS codesigning scope:** Whether the distribution target is small-team internal (right-click workaround acceptable) or wider public distribution (Apple Developer ID required) is a business decision that changes Phase 5 scope. This should be resolved before Phase 5 planning.
- **VAD library choice:** PITFALLS.md recommends `silero-vad` or `webrtcvad` for hallucination prevention. Neither was researched in depth. `silero-vad` adds a ~50 MB PyTorch model dependency; `webrtcvad` is a smaller C extension. The choice affects packaging size and PyInstaller complexity.
- **Parallel GPU workers:** Research confirms GPU workers must be capped to 1 (VRAM contention). The UX for communicating this constraint to users (e.g., auto-detect and enforce the cap, or warn and allow override) is not designed.

---

## Sources

### Primary (HIGH confidence)
- [openai-whisper PyPI](https://pypi.org/project/openai-whisper/) — version 20250625, Python support matrix
- [anthropic PyPI](https://pypi.org/project/anthropic/) — version 0.86.0, March 2026
- [PyInstaller PyPI + docs 6.19.0](https://pyinstaller.org/en/stable/index.html) — packaging patterns, spec file, common pitfalls
- [keyring PyPI](https://pypi.org/project/keyring/) — version 25.7.0, backend discovery
- [ttkbootstrap PyPI](https://pypi.org/project/ttkbootstrap/) — version 1.20.2, March 2026
- [torch PyPI](https://pypi.org/project/torch/) — version 2.11.0, MPS/CUDA backend APIs
- [Python gettext docs](https://docs.python.org/3/library/gettext.html) — stdlib i18n API
- [Tkinter threading model — runebook.dev](https://runebook.dev/en/docs/python/library/tkinter/threading-model) — reflects official Python docs
- [Whisper thread safety — openai/whisper Discussion #296](https://github.com/openai/whisper/discussions/296) — model instance sharing
- [Whisper parallelisation — openai/whisper Discussion #432](https://github.com/openai/whisper/discussions/432)
- [platformdirs docs](https://platformdirs.readthedocs.io/) — config path resolution
- [Anthropic rate limits docs](https://platform.claude.com/docs/en/api/rate-limits)

### Secondary (MEDIUM confidence)
- [openai/whisper PyInstaller Discussion #1479](https://github.com/openai/whisper/discussions/1479) — hidden imports, freeze_support, asset bundling
- [PyInstaller + PyTorch discussion #7621](https://github.com/orgs/pyinstaller/discussions/7621) — torch metadata workarounds
- [jaraco/keyring issues #439, #629](https://github.com/jaraco/keyring/issues/) — frozen app backend discovery, macOS codesigning
- [openai/whisper hallucination discussions #679, #1606, #1771](https://github.com/openai/whisper/discussions/) — silence hallucinations, parallel CUDA errors
- [Buzz GitHub](https://github.com/chidiwilliams/buzz) — competitor feature baseline
- [PyInstaller macOS ffmpeg discussion #8089](https://github.com/orgs/pyinstaller/discussions/8089) — DYLD_LIBRARY_PATH subprocess conflict
- [Whisper Czech accuracy notes](https://medium.com/@maestrosill/openai-whisper-ai-pro-p%C5%99epis-audia-na-text-97c1ae80feb6) — medium model for Czech

### Tertiary (LOW confidence)
- [alexsevas/whisper_gui DeepWiki](https://deepwiki.com/alexsevas/whisper_gui) — real-world architecture reference; structure verified against official patterns
- [Best MacWhisper Alternatives 2026](https://www.getvoibe.com/blog/macwhisper-alternatives/) — competitor landscape (marketing source)
- [faster-whisper issue #535](https://github.com/SYSTRAN/faster-whisper/issues/535) — cublas DLL behavior; applicable by analogy

---
*Research completed: 2026-03-28*
*Ready for roadmap: yes*

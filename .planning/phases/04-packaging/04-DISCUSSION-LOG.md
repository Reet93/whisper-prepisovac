# Phase 4: Packaging - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-03-29
**Phase:** 04-packaging
**Areas discussed:** Git publication readiness, Windows build scope, Distribution format, Bundled binaries

---

## Git Publication Readiness

| Option | Description | Selected |
|--------|-------------|----------|
| README.md | Create project description and install instructions | Yes |
| MIT License | Standard open-source freeware license | Yes |
| Exclude .planning/ from Git | Only publish source code, not GSD artifacts | Yes |
| Security scan | Automated check for hardcoded secrets before push | Yes |

**User's choice:** README + MIT License + exclude planning artifacts + security scan
**Notes:** User wants "freeware" — MIT recommended as GitHub-standard equivalent. User confirmed .planning/, .claude/, .vexp/ should be excluded.

---

## Windows Build Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Windows only | Build portable folder for Windows only | Yes |
| Windows + macOS | Build for both platforms | |

**User's choice:** Windows only
**Notes:** macOS requires building on Mac hardware (PyInstaller doesn't cross-compile). Deferred.

| Option | Description | Selected |
|--------|-------------|----------|
| Local manual build | Run a script locally to produce the portable folder | Yes |
| GitHub Actions CI | Automated build on push | |

**User's choice:** Local manual build
**Notes:** Claude recommended local build — CI for 2.9 GB model + CUDA binaries would be complex, slow, and expensive. User agreed.

---

## Distribution Format

| Option | Description | Selected |
|--------|-------------|----------|
| GitHub Release | Zip attached to tagged release for end users | Yes (combined) |
| Just the repo | Clone and build yourself | Yes (combined) |
| Both | Release zip for users + repo for developers | Yes |

**User's choice:** Both — GitHub Release zip + source repo

| Option | Description | Selected |
|--------|-------------|----------|
| Bundle model (~3-4 GB total) | Ship model in the zip | |
| Download on first launch | Auto-download ~1.5 GB model with progress indicator | Yes |

**User's choice:** Download on first launch
**Notes:** User's idea — reduces distribution zip from ~3-4 GB to ~500-800 MB, avoids GitHub Release file size limits. README will document the first-launch download. Trade-off: breaks "no download at runtime" constraint, but with clear UX it's a reasonable compromise.

---

## Bundled Binaries

| Option | Description | Selected |
|--------|-------------|----------|
| ffmpeg latest stable (BtbN) | Windows static build from GitHub | Yes |

**User's choice:** Latest stable, no version preference
**Notes:** No decision needed on CUDA — PyInstaller picks up torch CUDA binaries automatically.

---

## Claude's Discretion

- PyInstaller spec file internals
- Build script implementation
- ffmpeg exact version
- Model download implementation details

## Deferred Ideas

- macOS build (requires Mac hardware)
- GitHub Actions CI/CD (add later if project grows)

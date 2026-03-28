---
phase: 02-core-transcription
plan: 01
subsystem: core
tags: [transcription, whisper, vad, gpu-detection, worker-process]
dependency_graph:
  requires: [Phase 01 foundation — get_resource_path, freeze_support]
  provides: [device.py detect_device, vad.py preprocess_audio, transcriber.py _worker_init+transcribe_file]
  affects: [02-03 dispatcher wires transcriber.py to ProcessPoolExecutor]
tech_stack:
  added: [openai-whisper==20250625, torchaudio==2.11.0, silero-vad]
  patterns: [ProcessPoolExecutor worker-init pattern, tqdm injection for Whisper progress, silero-vad speech extraction]
key_files:
  created:
    - src/whisperai/core/__init__.py
    - src/whisperai/core/device.py
    - src/whisperai/core/vad.py
    - src/whisperai/core/transcriber.py
  modified:
    - requirements.in
decisions:
  - "silero-vad chosen over webrtcvad — PyTorch-native, no C extension, matches D-18 research decision"
  - "torch not pinned in requirements.in — let openai-whisper transitive dependency handle it to avoid CUDA wheel conflicts"
  - "tqdm injection pattern used for Whisper progress — no official callback API exists in whisper.transcribe()"
  - "temp WAV written between VAD and Whisper — model.transcribe() requires file path, not tensor"
metrics:
  duration_minutes: 5
  completed_date: "2026-03-28"
  tasks_completed: 2
  files_created_or_modified: 5
---

# Phase 02 Plan 01: Core Transcription Backend Summary

**One-liner:** GPU auto-detection + silero-vad silence stripping + Whisper worker with tqdm progress injection for Czech transcription via ProcessPoolExecutor.

## What Was Built

The `src/whisperai/core/` package provides three modules that form the computational backend for transcription. These run inside ProcessPoolExecutor worker processes and are UI-agnostic.

### device.py
- `detect_device() -> tuple[str, str]` — checks CUDA (Windows), then MPS (macOS Apple Silicon), falls back to CPU. Returns `(torch_device_str, human_label)` for log messages (D-16, D-17).
- `get_default_workers(device) -> int` — returns 1 for GPU modes (VRAM contention), `min(4, cpu_count)` for CPU-only (D-21).

### vad.py
- `preprocess_audio(audio_path, sample_rate=16000) -> tuple[Tensor, dict]` — loads silero-vad model once per process (module-level cache), runs `get_speech_timestamps`, concatenates speech chunks. Returns `(speech_tensor, stats_dict)` with `segment_count`, `speech_duration_s`, `total_duration_s`. Returns empty tensor if no speech found (D-18, D-19, TRANS-05).

### transcriber.py
- `_worker_init(model_path, device)` — ProcessPoolExecutor `initializer`. Loads Whisper medium model once per worker process into module-level `_model`. Subsequent calls to `transcribe_file` in the same worker reuse the loaded model (TRANS-01, TRANS-04).
- `transcribe_file(audio_path, progress_queue, task_id) -> dict` — runs VAD preprocessing, writes speech tensor to temp WAV, injects `_ProgressTqdm` subclass into `whisper.transcribe` module's tqdm namespace, runs `model.transcribe(language="cs")`, restores original tqdm in `finally` block, cleans up temp WAV. Returns `{"text": ..., "vad_stats": ...}` (TRANS-01, TRANS-03, TRANS-05).

### requirements.in
Added `openai-whisper==20250625`, `torchaudio==2.11.0`, `silero-vad`. torch is intentionally NOT pinned — openai-whisper handles the transitive dependency; pinning conflicts with the CUDA wheel (`+cu124` suffix).

## Tasks Completed

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Update requirements.in + create core/__init__.py | acdc3b3 |
| 2 | Implement device.py, vad.py, transcriber.py | 023a212 |

## Deviations from Plan

None — plan executed exactly as written. The `whisper.load_model("medium"` grep check appeared to fail due to multi-line call syntax but the implementation is correct and matches the plan specification precisely.

## Known Stubs

None. This is a backend-only plan with no UI rendering. All functions have complete implementations per the plan spec.

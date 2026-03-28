"""GPU device detection for Whisper transcription."""
import torch


def detect_device() -> tuple[str, str]:
    """Return (torch_device_str, human_label) for the best available compute device.

    Checks CUDA first (Windows), then MPS (macOS), falls back to CPU.
    The human_label is used for log messages (D-17).
    """
    if torch.cuda.is_available():
        name = torch.cuda.get_device_name(0)
        return "cuda", f"CUDA ({name})"
    if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
        return "mps", "MPS (Apple Silicon)"
    return "cpu", "CPU"


def get_default_workers(device: str) -> int:
    """Return default parallel worker count based on device type (D-21).

    GPU mode: 1 worker (VRAM contention). CPU mode: min(4, cpu_count).
    """
    if device in ("cuda", "mps"):
        return 1
    import os
    cpu_count = os.cpu_count() or 2
    return min(4, cpu_count)

import glob
import sys
from pathlib import Path
from platformdirs import user_data_dir


def get_model_path() -> Path:
    """Writable directory for faster-whisper model storage.

    Frozen (PyInstaller): %LOCALAPPDATA%/WhisperPrepis/WhisperPrepis/models
    Development: project_root/models (existing dev cache)
    """
    if getattr(sys, "frozen", False):
        return Path(user_data_dir("WhisperPrepis", "WhisperPrepis")) / "models"
    return Path(__file__).parent.parent.parent.parent / "models"


def is_model_downloaded() -> bool:
    """True if faster-whisper medium model.bin is present in model path."""
    pattern = str(
        get_model_path()
        / "models--Systran--faster-whisper-medium"
        / "snapshots"
        / "*"
        / "model.bin"
    )
    return len(glob.glob(pattern)) > 0

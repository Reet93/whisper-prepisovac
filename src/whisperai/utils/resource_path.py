import sys
from pathlib import Path


def get_resource_path(relative_path: str) -> Path:
    """Resolve path to a bundled resource.

    Works in both development (relative to project root) and PyInstaller
    frozen context (relative to sys._MEIPASS / _internal/).
    """
    if getattr(sys, "frozen", False):
        # PyInstaller 6.x: sys._MEIPASS points to _internal/ subfolder
        base = Path(sys._MEIPASS)
    else:
        # Development: resource_path.py is at src/whisperai/utils/resource_path.py
        # .parent = utils/, .parent.parent = whisperai/
        # .parent.parent.parent = src/, .parent^4 = project root
        base = Path(__file__).parent.parent.parent.parent
    return base / relative_path

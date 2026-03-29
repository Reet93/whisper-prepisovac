import multiprocessing
import os
import sys
from pathlib import Path


def main() -> None:
    multiprocessing.freeze_support()

    # Prepend bundled ffmpeg/ffprobe to PATH in frozen app
    if getattr(sys, "frozen", False):
        bin_dir = str(Path(sys._MEIPASS) / "bin")
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")

    # i18n MUST be initialized before any import that uses _()
    from src.whisperai.utils.i18n import detect_system_language, set_language
    lang = detect_system_language()
    set_language(lang)

    from src.whisperai.app import create_app
    create_app()


if __name__ == "__main__":
    main()

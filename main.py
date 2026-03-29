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
    from src.whisperai.utils.settings import SettingsStore

    settings = SettingsStore()
    lang = settings.get("language") or detect_system_language()
    set_language(lang)

    # Check if model needs downloading (frozen context or dev)
    from src.whisperai.utils.model_path import is_model_downloaded
    if not is_model_downloaded():
        import ttkbootstrap as ttk
        # Create a temporary root for the download dialog
        dl_root = ttk.Window(
            title=_("download.title"),
            themename="flatly",
            size=(400, 220),
            resizable=(False, False),
        )
        dl_root.withdraw()  # hide until dialog is ready

        from src.whisperai.gui.model_download_dialog import ModelDownloadDialog
        dialog = ModelDownloadDialog(dl_root)
        dl_root.place_window_center()
        dl_root.deiconify()
        dl_root.wait_window(dialog)  # block until dialog closes
        dl_root.destroy()

        # If user cancelled and model still not present, warn but continue
        # App will show error when trying to transcribe

    from src.whisperai.app import create_app
    create_app()


if __name__ == "__main__":
    main()

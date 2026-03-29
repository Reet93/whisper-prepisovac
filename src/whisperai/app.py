import ttkbootstrap as ttk
from src.whisperai.gui.main_window import MainWindow
from src.whisperai.utils.settings import SettingsStore


def create_app() -> None:
    """Create and run the ttkbootstrap application.

    Reads persisted language and worker settings from SettingsStore.
    Sets up device detection and launches the main window.
    """
    settings = SettingsStore()
    current_lang = settings.get("language") or "cs"

    from src.whisperai.utils.i18n import set_language
    set_language(current_lang)

    root = ttk.Window(
        title=_("app.title"),
        themename="flatly",
        size=(1080, 720),
        minsize=(480, 320),
        resizable=(True, True),
    )
    root.withdraw()
    root.place_window_center()
    root.deiconify()

    from src.whisperai.core.device import detect_device, get_default_workers
    device_str, device_label = detect_device()
    worker_count = settings.get("worker_count") or get_default_workers(device_str)
    root._device_str = device_str
    root._device_label = device_label
    root._worker_count = worker_count

    MainWindow(root, settings, current_lang)
    root.mainloop()

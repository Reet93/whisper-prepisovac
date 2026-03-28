import ttkbootstrap as ttk
from src.whisperai.gui.main_window import MainWindow


def create_app(current_lang: str = "cs") -> None:
    """Create and run the ttkbootstrap application."""
    root = ttk.Window(
        title=_("app.title"),
        themename="flatly",
        size=(720, 480),
        minsize=(480, 320),
        resizable=(True, True),
    )
    root.withdraw()
    root.place_window_center()
    root.deiconify()

    # GPU detection at startup (D-16, TRANS-02)
    from src.whisperai.core.device import detect_device, get_default_workers
    device_str, device_label = detect_device()
    worker_count = get_default_workers(device_str)
    root._device_str = device_str
    root._device_label = device_label
    root._worker_count = worker_count

    MainWindow(root, current_lang)
    root.mainloop()

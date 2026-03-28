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

    MainWindow(root, current_lang)
    root.mainloop()

import tkinter as tk
from tkinter import messagebox
import ttkbootstrap as ttk
from ttkbootstrap.constants import LEFT, RIGHT


class MainWindow:
    """Main application window with header/content/footer layout."""

    def __init__(self, root: ttk.Window, current_lang: str = "cs") -> None:
        self.root = root
        self.current_lang = current_lang
        self._build_layout()

    def _build_layout(self) -> None:
        root = self.root

        # main_frame with 16px padding — fills entire window
        main_frame = ttk.Frame(root, padding=16)
        main_frame.grid(row=0, column=0, sticky="nsew")
        root.columnconfigure(0, weight=1)
        root.rowconfigure(0, weight=1)

        # Three-row grid: header (fixed), content (expands), footer (fixed)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)

        # --- Header ---
        header_frame = ttk.Frame(main_frame)
        header_frame.grid(row=0, column=0, sticky="ew")

        app_title_label = ttk.Label(
            header_frame,
            text=_("app.title"),
            font=("", 13, "bold"),
        )
        app_title_label.pack(side=LEFT)

        # --- Content (placeholder for Phase 1) ---
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=1, column=0, sticky="nsew")

        placeholder = ttk.Label(
            content_frame,
            text=_("ui.placeholder"),
        )
        placeholder.pack(expand=True)

        # --- Footer ---
        footer_frame = ttk.Frame(main_frame)
        footer_frame.grid(row=2, column=0, sticky="ew")

        # Language switcher — right-aligned (per UI-SPEC)
        lang_combo = ttk.Combobox(
            footer_frame,
            values=[_("ui.language_cs"), _("ui.language_en")],
            state="readonly",
            width=12,
        )
        # Set current selection based on active language
        if self.current_lang == "cs":
            lang_combo.current(0)
        else:
            lang_combo.current(1)
        lang_combo.pack(side=RIGHT)
        lang_combo.bind("<<ComboboxSelected>>", self._on_language_changed)

        lang_label = ttk.Label(
            footer_frame,
            text=_("ui.language_label"),
            font=("", 9),
        )
        lang_label.pack(side=RIGHT, padx=(0, 4))

        self._lang_combo = lang_combo

    def _on_language_changed(self, event: tk.Event) -> None:
        """Handle language Combobox selection. Show restart notice (per D-02)."""
        selected_index = self._lang_combo.current()
        codes = ["cs", "en"]
        new_lang = codes[selected_index]
        if new_lang != self.current_lang:
            messagebox.showinfo(
                _("app.title"),
                _("ui.language_changed_notice"),
            )

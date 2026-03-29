import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import LEFT, RIGHT
from ttkbootstrap.tooltip import ToolTip

from src.whisperai.gui.transcription_panel import TranscriptionPanel
from src.whisperai.utils.settings import SettingsStore


class MainWindow:
    """Main application window with header/content/footer layout."""

    def __init__(
        self,
        root: ttk.Window,
        settings: SettingsStore,
        current_lang: str = "cs",
    ) -> None:
        self.root = root
        self._settings = settings
        self.current_lang = current_lang
        self._banner_dismissed = False
        self._settings_dialog = None
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

        # Gear button — right-aligned in header (per UI-SPEC section 1)
        self._btn_settings = ttk.Button(
            header_frame,
            text="\u2699",
            width=2,
            bootstyle="secondary",  # type: ignore[call-arg]
            command=self._on_open_settings,
        )
        self._btn_settings.pack(side=RIGHT, padx=(4, 0))
        ToolTip(self._btn_settings, text=_("settings.tooltip"))

        # Store reference for live reload
        self._app_title_label = app_title_label

        # --- Content ---
        content_frame = ttk.Frame(main_frame)
        content_frame.grid(row=1, column=0, sticky="nsew")
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(1, weight=1)
        self.content_frame = content_frame

        # Experimental feature banner (Claude cleanup coming soon)
        self._banner_frame = ttk.Frame(content_frame, bootstyle="warning")  # type: ignore[call-arg]
        self._lbl_banner = ttk.Label(
            self._banner_frame,
            text=_("banner.experimental"),
            foreground="#2C3E50",
        )
        self._lbl_banner.pack(side=LEFT, padx=(16, 0))
        self._btn_banner_dismiss = ttk.Button(
            self._banner_frame,
            text="\u00d7",
            bootstyle="link",  # type: ignore[call-arg]
            command=self._on_banner_dismiss,
        )
        self._btn_banner_dismiss.pack(side=RIGHT)
        self._update_banner()

        # TranscriptionPanel at row 1 (always present, expands)
        panel_frame = ttk.Frame(content_frame)
        panel_frame.grid(row=1, column=0, sticky="nsew")
        self.transcription_panel = TranscriptionPanel(panel_frame, root)

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
        self._lang_label = lang_label

    # ------------------------------------------------------------------
    # Banner
    # ------------------------------------------------------------------

    def _update_banner(self) -> None:
        """Show or hide the experimental feature banner."""
        if self._banner_dismissed:
            self._banner_frame.grid_forget()
        else:
            self._banner_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
            self.content_frame.rowconfigure(1, weight=1)

    def _on_banner_dismiss(self) -> None:
        """Dismiss the banner for this session."""
        self._banner_dismissed = True
        self._banner_frame.grid_forget()

    def _on_banner_setup(self) -> None:
        """Open settings dialog on the Claude tab."""
        self._on_open_settings(tab="claude")

    def show_banner_invalid_key(self) -> None:
        """Show banner with invalid key text (D-10: reappears on failed key)."""
        self._banner_dismissed = False
        self._lbl_banner.configure(text=_("banner.invalid_key"))
        self._update_banner()

    # ------------------------------------------------------------------
    # Settings
    # ------------------------------------------------------------------

    def _on_open_settings(self, tab: str = "general") -> None:
        """Open the settings modal dialog."""
        from src.whisperai.gui.settings_dialog import SettingsDialog
        self._settings_dialog = SettingsDialog(
            self.root, self._settings,
            on_language_changed=self._on_settings_language_changed,
        )
        if tab == "claude":
            self._settings_dialog.open_on_claude_tab()
        # After dialog closes, refresh banner state
        self.dialog = self._settings_dialog.dialog
        self.dialog.bind("<Destroy>", lambda e: self._on_settings_closed(), add="+")

    def _on_settings_closed(self) -> None:
        """Called when settings dialog is closed."""
        self._update_banner()
        self._settings_dialog = None

    # ------------------------------------------------------------------
    # Language
    # ------------------------------------------------------------------

    def _on_language_changed(self, event: tk.Event) -> None:
        """Handle language Combobox selection — live reload (D-31)."""
        selected_index = self._lang_combo.current()
        codes = ["cs", "en"]
        new_lang = codes[selected_index]
        if new_lang != self.current_lang:
            from src.whisperai.utils.i18n import set_language
            set_language(new_lang)
            self.current_lang = new_lang
            self._settings.set("language", new_lang)
            self._settings.save()
            self.reload_ui_strings()

    def _on_settings_language_changed(self, new_lang: str) -> None:
        """Called by SettingsDialog when language changes via settings save."""
        from src.whisperai.utils.i18n import set_language
        set_language(new_lang)
        self.current_lang = new_lang
        # Update footer combo selection
        codes = ["cs", "en"]
        if new_lang in codes:
            self._lang_combo.current(codes.index(new_lang))
        self.reload_ui_strings()

    def reload_ui_strings(self) -> None:
        """Reload all UI strings for the current language. Called after live language switch."""
        # Header
        self._app_title_label.configure(text=_("app.title"))
        self.root.title(_("app.title"))

        # Footer
        self._lang_label.configure(text=_("ui.language_label"))
        self._lang_combo.configure(values=[_("ui.language_cs"), _("ui.language_en")])

        # Banner
        self._lbl_banner.configure(text=_("banner.experimental"))

        # Gear button tooltip (recreate tooltip)
        ToolTip(self._btn_settings, text=_("settings.tooltip"))

        # Delegate to transcription panel if it supports reload
        if hasattr(self.transcription_panel, "reload_strings"):
            self.transcription_panel.reload_strings()

        # Delegate to settings dialog if open
        if self._settings_dialog is not None:
            if hasattr(self._settings_dialog, "reload_strings"):
                self._settings_dialog.reload_strings()

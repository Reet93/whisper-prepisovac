"""Settings modal dialog for Whisper Přepisovač.

Provides General tab (language, output folder, workers) and Claude tab
(API key management, model selection, default prompt view).
"""
from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox
from pathlib import Path

import ttkbootstrap as ttk
from ttkbootstrap.constants import LEFT, RIGHT
from ttkbootstrap.tooltip import ToolTip

from src.whisperai.utils.settings import SettingsStore
from src.whisperai.core.device import detect_device


class SettingsDialog:
    """Modal settings dialog with General and Claude tabs."""

    def __init__(
        self,
        parent_root: ttk.Window,
        settings: SettingsStore,
        on_language_changed: callable = None,
    ) -> None:
        self._settings = settings
        self._parent = parent_root
        self._on_language_changed_cb = on_language_changed

        self.dialog = ttk.Toplevel(parent_root)
        self.dialog.title(_("settings.title"))
        self.dialog.grab_set()  # blocks main window
        self.dialog.minsize(480, 360)
        self.dialog.bind("<Escape>", lambda e: self.dialog.destroy())

        # Center dialog relative to parent
        self.dialog.geometry(
            f"+{parent_root.winfo_x() + 60}+{parent_root.winfo_y() + 40}"
        )

        self._build()

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def _build(self) -> None:
        """Build the full dialog layout."""
        frame = ttk.Frame(self.dialog, padding=16)
        frame.pack(fill="both", expand=True)

        self._notebook = ttk.Notebook(frame)
        self._notebook.pack(fill="both", expand=True, pady=(0, 16))

        self._build_general_tab()
        self._build_claude_tab()

        # Always open on General tab (D-16)
        self._notebook.select(0)

        # Button row
        btn_row = ttk.Frame(frame)
        btn_row.pack(fill="x")

        ttk.Button(
            btn_row,
            text=_("settings.reset_defaults"),
            bootstyle="secondary",  # type: ignore[call-arg]
            command=self._on_reset,
        ).pack(side=LEFT)

        ttk.Button(
            btn_row,
            text=_("settings.save"),
            bootstyle="success",  # type: ignore[call-arg]
            command=self._on_save,
        ).pack(side=RIGHT)

        ttk.Button(
            btn_row,
            text=_("settings.cancel"),
            bootstyle="secondary",  # type: ignore[call-arg]
            command=self.dialog.destroy,
        ).pack(side=RIGHT, padx=(0, 8))

    def _build_general_tab(self) -> None:
        """Build General tab: language, output folder, workers, GPU info."""
        tab = ttk.Frame(self._notebook, padding=16)
        self._notebook.add(tab, text=_("settings.tab_general"))
        tab.columnconfigure(1, weight=1)

        # Row 0: Language
        ttk.Label(tab, text=_("settings.language")).grid(
            row=0, column=0, sticky="w", padx=(0, 8), pady=4
        )
        self._lang_combo = ttk.Combobox(
            tab,
            values=[_("ui.language_cs"), _("ui.language_en")],
            state="readonly",
        )
        lang = self._settings.get("language")
        self._lang_combo.current(0 if lang == "cs" else 1)
        self._lang_combo.grid(row=0, column=1, sticky="ew", pady=4)

        # Row 1: Output folder
        ttk.Label(tab, text=_("settings.output_folder")).grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=4
        )
        folder_frame = ttk.Frame(tab)
        folder_frame.grid(row=1, column=1, sticky="ew", pady=4)
        folder_frame.columnconfigure(0, weight=1)

        self._output_var = tk.StringVar(value=self._settings.get("output_folder") or "")
        output_entry = ttk.Entry(folder_frame, textvariable=self._output_var, state="readonly")
        output_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        ttk.Button(
            folder_frame, text="...", width=3,
            bootstyle="secondary",  # type: ignore[call-arg]
            command=self._on_browse_output,
        ).grid(row=0, column=1)

        # Row 2: Workers
        ttk.Label(tab, text=_("settings.workers")).grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=4
        )
        self._workers_spin = ttk.Spinbox(tab, from_=1, to=8, width=5)
        self._workers_spin.set(self._settings.get("worker_count") or 1)
        self._workers_spin.grid(row=2, column=1, sticky="w", pady=4)

        # Row 3: GPU info
        try:
            device_str, _label = detect_device()
        except Exception:
            device_str = "cpu"

        if device_str in ("cuda", "mps"):
            gpu_text = _("settings.gpu_info_gpu")
        else:
            gpu_text = _("settings.gpu_info_cpu")

        self._gpu_info_label = ttk.Label(
            tab, text=gpu_text, font=("", 9), foreground="#95A5A6"
        )
        self._gpu_info_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(8, 0))

        # Error label for folder validation
        self._folder_error_label = ttk.Label(tab, text="", foreground="#E74C3C", font=("", 9))
        self._folder_error_label.grid(row=4, column=0, columnspan=2, sticky="w")

    def _build_claude_tab(self) -> None:
        """Build Claude tab: experimental warning — all controls disabled."""
        tab = ttk.Frame(self._notebook, padding=16)
        self._notebook.add(tab, text=_("settings.tab_claude"))
        tab.columnconfigure(1, weight=1)

        # Row 0: Experimental warning
        ttk.Label(
            tab,
            text=_("settings.claude_experimental"),
            font=("", 10, "bold"),
            foreground="#F39C12",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 12))

        # Row 1: Model (disabled)
        ttk.Label(tab, text=_("settings.model"), state="disabled").grid(
            row=1, column=0, sticky="w", padx=(0, 8), pady=4
        )
        model_values = [_("model.haiku"), _("model.sonnet")]
        self._model_combo = ttk.Combobox(tab, values=model_values, state="disabled")
        stored_model = self._settings.get("claude_model") or "claude-haiku-4-5"
        self._model_combo.current(0 if "haiku" in stored_model else 1)
        self._model_combo.grid(row=1, column=1, sticky="ew", pady=4)

        # Row 2: API key (disabled)
        ttk.Label(tab, text=_("settings.api_key"), state="disabled").grid(
            row=2, column=0, sticky="w", padx=(0, 8), pady=4
        )
        key_frame = ttk.Frame(tab)
        key_frame.grid(row=2, column=1, sticky="ew", pady=4)
        key_frame.columnconfigure(0, weight=1)

        self._key_var = tk.StringVar(value="")
        self._key_entry = ttk.Entry(key_frame, textvariable=self._key_var, show="*", state="disabled")
        self._key_entry.grid(row=0, column=0, sticky="ew", padx=(0, 4))
        self._key_show_btn = ttk.Button(
            key_frame,
            text=_("settings.show_hide"),
            bootstyle="secondary",  # type: ignore[call-arg]
            state="disabled",
        )
        self._key_show_btn.grid(row=0, column=1)

        # Row 3: Key status label (not used but kept for reload_strings compat)
        self._key_status_label = ttk.Label(tab, text="", font=("", 9))
        self._key_status_label.grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 4))

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def _on_browse_output(self) -> None:
        """Open folder picker and update output folder variable."""
        folder = filedialog.askdirectory(title=_("settings.output_folder"))
        if folder:
            self._output_var.set(folder)

    def _on_save(self) -> None:
        """Validate and persist settings. Runs API key validation in background if key changed."""
        # Language
        lang = "cs" if self._lang_combo.current() == 0 else "en"
        lang_changed = lang != self._settings.get("language")

        # Output folder
        folder = self._output_var.get()
        if folder and not Path(folder).exists():
            self._folder_error_label.configure(text=_("settings.folder_not_found"))
            return
        self._folder_error_label.configure(text="")

        # Workers
        try:
            workers = int(self._workers_spin.get())
        except (ValueError, tk.TclError):
            workers = 1

        # Persist general settings
        self._settings.set("language", lang)
        self._settings.set("output_folder", folder)
        self._settings.set("worker_count", workers)
        self._settings.save()

        # Claude API key disabled (experimental) — skip validation
        if lang_changed:
            self._trigger_lang_reload(lang)
        self.dialog.destroy()

    def _trigger_lang_reload(self, lang: str) -> None:
        """Trigger live language reload in the main window."""
        if self._on_language_changed_cb:
            self._on_language_changed_cb(lang)

    def _on_reset(self) -> None:
        """Open reset-to-defaults sub-dialog with per-setting checkboxes."""
        reset_dialog = ttk.Toplevel(self.dialog)
        reset_dialog.title(_("reset.title"))
        reset_dialog.grab_set()
        reset_dialog.resizable(False, False)
        reset_dialog.bind("<Escape>", lambda e: reset_dialog.destroy())

        frame = ttk.Frame(reset_dialog, padding=16)
        frame.pack(fill="both", expand=True)

        # Checkboxes (all checked by default)
        checks: list[tuple[tk.BooleanVar, str]] = []
        items = [
            ("reset.language", "language"),
            ("reset.output_folder", "output_folder"),
            ("reset.workers", "worker_count"),
            ("reset.prompt", "claude_prompt"),
            ("reset.profiles", "context_profiles"),
        ]
        for i, (label_key, settings_key) in enumerate(items):
            var = tk.BooleanVar(value=True)
            checks.append((var, settings_key))
            ttk.Checkbutton(frame, text=_(label_key), variable=var).grid(
                row=i, column=0, sticky="w", pady=2
            )

        # Key note
        ttk.Label(frame, text=_("reset.key_note"), font=("", 9), foreground="#95A5A6").grid(
            row=len(items), column=0, sticky="w", pady=(8, 8)
        )

        # Buttons
        btn_frame = ttk.Frame(frame)
        btn_frame.grid(row=len(items) + 1, column=0, sticky="ew")

        def _apply_reset() -> None:
            keys_to_reset = [key for var, key in checks if var.get()]
            if keys_to_reset:
                self._settings.reset(keys_to_reset)
                self._settings.save()
                # Refresh dialog widgets to reflect new values
                self._refresh_general_widgets()
            reset_dialog.destroy()

        ttk.Button(
            btn_frame,
            text=_("reset.apply"),
            bootstyle="warning",  # type: ignore[call-arg]
            command=_apply_reset,
        ).pack(side=LEFT, padx=(0, 8))

        ttk.Button(
            btn_frame,
            text=_("reset.keep"),
            bootstyle="secondary",  # type: ignore[call-arg]
            command=reset_dialog.destroy,
        ).pack(side=LEFT)

    def _refresh_general_widgets(self) -> None:
        """Refresh General tab widgets to reflect current settings values."""
        lang = self._settings.get("language") or "cs"
        self._lang_combo.current(0 if lang == "cs" else 1)
        self._output_var.set(self._settings.get("output_folder") or "")
        workers = self._settings.get("worker_count") or 1
        self._workers_spin.set(workers)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def open_on_claude_tab(self) -> None:
        """Switch to the Claude tab. Called when banner 'Setup' is clicked."""
        self._notebook.select(1)

    def reload_strings(self) -> None:
        """Update all widget text to the current language. Called during live reload."""
        self.dialog.title(_("settings.title"))
        # Notebook tabs
        self._notebook.tab(0, text=_("settings.tab_general"))
        self._notebook.tab(1, text=_("settings.tab_claude"))
        # General tab widgets are rebuilt on next open; combo values need refresh
        self._lang_combo.configure(values=[_("ui.language_cs"), _("ui.language_en")])
        self._model_combo.configure(values=[_("model.haiku"), _("model.sonnet")])

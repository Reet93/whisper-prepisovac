"""TranscriptionPanel — file queue, action bar, and log panel for transcription workflow.

Pure UI class. Transcription logic is wired by Plan 03's dispatcher.
"""
from __future__ import annotations

import concurrent.futures
import json
import multiprocessing
import queue
import subprocess
import sys
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
import tkinter as tk

import ttkbootstrap as ttk
from ttkbootstrap.widgets.scrolled import ScrolledText
from ttkbootstrap.tooltip import ToolTip

from src.whisperai.utils.resource_path import get_resource_path


def _format_filesize(size_bytes: int) -> str:
    """Return a human-readable file size string using IEC binary units (1024-based).

    Examples: '1.4 MB', '320 KB', '512.0 B'
    """
    if size_bytes >= 1024 ** 2:
        return f"{size_bytes / (1024 ** 2):.1f} MB"
    if size_bytes >= 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes:.1f} B"


class TranscriptionPanel:
    """File queue, action bar, and log panel for transcription workflow.

    Pure UI — transcription logic wired by Plan 03's dispatcher.
    """

    AUDIO_EXTENSIONS = (".mp3", ".wav", ".m4a", ".ogg")

    def __init__(self, parent: ttk.Frame, root: ttk.Window, settings=None) -> None:
        self.parent = parent
        self.root = root
        self._settings = settings
        # iid -> {full_path, error_msg, result_text}
        self._row_data: dict[str, dict] = {}
        self._output_dir = tk.StringVar(value="")
        self._running = False
        # Claude cleanup mode flag
        self._claude_cleanup_mode = False
        # Dispatcher state
        self._ui_queue: queue.Queue = queue.Queue()  # In-process queue: dispatcher thread -> main thread
        self._stop_event = threading.Event()
        self._batch_files: list[tuple[str, str]] = []  # (iid, path) for current batch
        self._batch_done_count = 0
        self._batch_total = 0
        self._build_ui()

        # Log GPU device at startup (D-17)
        device_label = getattr(self.root, "_device_label", "CPU")
        device_str = getattr(self.root, "_device_str", "cpu")
        if device_str == "cuda":
            self.append_log(_("log.device_cuda").format(name=device_label.replace("CUDA (", "").rstrip(")")), "device")
        elif device_str == "mps":
            self.append_log(_("log.device_mps"), "device")
        else:
            self.append_log(_("log.device_cpu"), "device")

    # ------------------------------------------------------------------
    # UI Construction
    # ------------------------------------------------------------------

    def _build_ui(self) -> None:
        """Build the full TranscriptionPanel layout inside self.parent."""
        parent = self.parent

        # Allow panel to fill parent completely
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)  # queue_frame expands

        # Row 0: Toolbar
        toolbar_frame = ttk.Frame(parent)
        toolbar_frame.grid(row=0, column=0, sticky="ew", pady=(0, 4))
        self._build_toolbar(toolbar_frame)

        # Row 1: Queue (Treeview) — expands vertically
        queue_frame = ttk.Frame(parent)
        queue_frame.grid(row=1, column=0, sticky="nsew")
        queue_frame.columnconfigure(0, weight=1)
        queue_frame.rowconfigure(0, weight=1)
        self._build_queue(queue_frame)

        # Row 2: Action bar
        action_frame = ttk.Frame(parent)
        action_frame.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        self._build_action_bar(action_frame)

        # Row 3: Log panel (fixed height, does not expand)
        log_frame = ttk.Frame(parent)
        log_frame.grid(row=3, column=0, sticky="ew", pady=(8, 0))
        log_frame.columnconfigure(0, weight=1)
        self._build_log_panel(log_frame)

    def _build_toolbar(self, frame: ttk.Frame) -> None:
        """Build the toolbar with Add Files, Add Folder, and Remove buttons."""
        self.btn_add_files = ttk.Button(
            frame,
            text=_("ui.toolbar.add_files"),
            bootstyle="secondary",  # type: ignore[call-arg]
            command=self._on_add_files,
        )
        self.btn_add_files.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_add_folder = ttk.Button(
            frame,
            text=_("ui.toolbar.add_folder"),
            bootstyle="secondary",  # type: ignore[call-arg]
            command=self._on_add_folder,
        )
        self.btn_add_folder.pack(side=tk.LEFT, padx=(0, 8))

        self.btn_remove = ttk.Button(
            frame,
            text=_("ui.toolbar.remove_selected"),
            bootstyle="secondary",  # type: ignore[call-arg]
            command=self._on_remove_selected,
        )
        self.btn_remove.pack(side=tk.LEFT)

    def _build_queue(self, frame: ttk.Frame) -> None:
        """Build the Treeview file queue with vertical scrollbar and empty-state label."""
        # Treeview
        self.tree = ttk.Treeview(
            frame,
            columns=("filename", "filesize", "duration", "status"),
            show="headings",
            selectmode="extended",
        )

        # Column configuration
        self.tree.heading("filename", text=_("ui.queue.col_file"))
        self.tree.column("filename", minwidth=200, stretch=True, anchor="w")

        self.tree.heading("filesize", text=_("ui.queue.col_size"))
        self.tree.column("filesize", width=80, stretch=False, anchor="e")

        self.tree.heading("duration", text=_("ui.queue.col_duration"))
        self.tree.column("duration", width=80, stretch=False, anchor="e")

        self.tree.heading("status", text=_("ui.queue.col_status"))
        self.tree.column("status", width=120, stretch=False, anchor="center")

        # Status tag colors
        self.tree.tag_configure("waiting", foreground="#95A5A6")
        self.tree.tag_configure("processing", foreground="#F39C12", background="#FFF8F0")
        self.tree.tag_configure("done", foreground="#18BC9C")
        self.tree.tag_configure("error", foreground="#E74C3C", background="#FFF5F5")
        self.tree.tag_configure("claude_error", foreground="#E74C3C", background="#FFF5F5")

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Tooltip for full path / error detail
        self._tooltip = ToolTip(self.tree, text="", bootstyle="secondary")  # type: ignore[call-arg]
        self.tree.bind("<Motion>", self._on_tree_motion)

        # Context menu (right-click) for save-as on done rows
        right_click_event = "<Button-3>" if sys.platform != "darwin" else "<Button-2>"
        self.tree.bind(right_click_event, self._on_tree_right_click)
        self.tree.bind("<Double-1>", self._on_tree_double_click)

        # Empty state overlay
        self._empty_label = ttk.Label(
            frame,
            text=f"{_('ui.empty.heading')}\n{_('ui.empty.body')}",
            justify="center",
            anchor="center",
        )
        self._empty_label.place(relx=0.5, rely=0.5, anchor="center")
        self._update_empty_state()

    def _build_action_bar(self, frame: ttk.Frame) -> None:
        """Build the action bar: output folder picker, transcribe button, progress bar,
        plus new Claude controls (row 1) and inline prompt editor (row 2)."""
        frame.columnconfigure(1, weight=1)  # entry_output_dir expands

        # --- Row 0 (existing): output folder + transcribe + progress ---
        # Column 0: Output label
        lbl_output = ttk.Label(frame, text=_("ui.action.output_label"), font=("", 9))
        lbl_output.grid(row=0, column=0, sticky="w", padx=(0, 8))

        # Column 1: Output directory entry (read-only, expands)
        entry_output = ttk.Entry(frame, textvariable=self._output_dir, state="readonly")
        entry_output.grid(row=0, column=1, sticky="ew", padx=(0, 4))

        # Column 2: Browse button
        btn_browse = ttk.Button(
            frame,
            text="...",
            width=3,
            bootstyle="secondary",  # type: ignore[call-arg]
            command=self._on_browse_output,
        )
        btn_browse.grid(row=0, column=2, padx=(0, 8))

        # Column 3: Transcribe button
        self.btn_transcribe = ttk.Button(
            frame,
            text=_("ui.action.transcribe"),
            bootstyle="success",  # type: ignore[call-arg]
            width=15,
            command=self._on_transcribe_click,
            state="disabled",
        )
        self.btn_transcribe.grid(row=0, column=3, padx=(0, 8))

        # Column 4: Progress bar
        self.progressbar = ttk.Progressbar(
            frame,
            mode="determinate",
            length=160,
        )
        self.progressbar.grid(row=0, column=4, padx=(0, 8))

        # Column 5: Progress count label
        self.lbl_progress_count = ttk.Label(frame, text="", font=("", 9), foreground="#95A5A6")
        self.lbl_progress_count.grid(row=0, column=5)

        # --- Row 1 (NEW): context + Claude controls ---
        context_row = ttk.Frame(frame)
        context_row.grid(row=1, column=0, columnspan=6, sticky="ew", pady=(8, 0))
        context_row.columnconfigure(3, weight=1)  # entry_context expands

        # Col 0: Context label
        ttk.Label(context_row, text=_("ui.action.context_label"), font=("", 9)).grid(row=0, column=0, padx=(0, 4))

        # Col 1: Profile dropdown
        self._combo_profile = ttk.Combobox(context_row, width=20, state="readonly")
        self._combo_profile.grid(row=0, column=1, padx=(0, 4))
        self._combo_profile.bind("<<ComboboxSelected>>", self._on_profile_selected)
        self._refresh_profile_combo()

        # Col 2: Profile manage button "..."
        self._btn_manage_profile = ttk.Button(
            context_row, text="...", width=3,
            bootstyle="secondary",  # type: ignore[call-arg]
            command=self._on_manage_profile,
        )
        self._btn_manage_profile.grid(row=0, column=2, padx=(0, 8))

        # Col 3: Context text entry (expands)
        self._context_var = tk.StringVar(value="")
        self._entry_context = ttk.Entry(context_row, textvariable=self._context_var)
        self._entry_context.grid(row=0, column=3, sticky="ew", padx=(0, 8))

        # Col 4: "Přepsat + Upravit" button
        self._btn_transcribe_edit = ttk.Button(
            context_row, text=_("ui.action.transcribe_edit"),
            bootstyle="success",  # type: ignore[call-arg]
            width=18, command=self._on_transcribe_edit_click,
        )
        self._btn_transcribe_edit.grid(row=0, column=4, padx=(0, 4))

        # Col 5: "Upravit" standalone button
        self._btn_edit_only = ttk.Button(
            context_row, text=_("ui.action.edit_only"),
            bootstyle="secondary",  # type: ignore[call-arg]
            width=8, command=self._on_edit_only_click,
            state="disabled",
        )
        self._btn_edit_only.grid(row=0, column=5)

        # Prompt toggle link (between row 1 and row 2)
        self._btn_toggle_prompt = ttk.Button(
            frame, text=_("ui.action.toggle_prompt_show"),
            bootstyle="link",  # type: ignore[call-arg]
            command=self._toggle_prompt_editor,
        )
        self._btn_toggle_prompt.grid(row=2, column=0, columnspan=6, sticky="w", pady=(4, 0))

        # --- Row 3 (NEW): inline prompt editor (collapsed by default) ---
        self._prompt_frame = ttk.Frame(frame)
        # NOT gridded initially — hidden by default

        self._prompt_frame.columnconfigure(1, weight=1)
        ttk.Label(self._prompt_frame, text=_("ui.action.prompt_label"), font=("", 9)).grid(
            row=0, column=0, sticky="nw", padx=(0, 4),
        )

        self._txt_prompt = ScrolledText(self._prompt_frame, height=6)
        self._txt_prompt.grid(row=0, column=1, sticky="ew")
        # Load default prompt
        self._load_prompt_text()

        self._btn_reset_prompt = ttk.Button(
            self._prompt_frame, text=_("ui.action.reset_prompt"),
            bootstyle="secondary",  # type: ignore[call-arg]
            command=self._reset_prompt,
        )
        self._btn_reset_prompt.grid(row=0, column=2, padx=(4, 0), sticky="n")

        self._lbl_cost_estimate = ttk.Label(
            self._prompt_frame, text="", font=("", 9), foreground="#95A5A6",
        )
        self._lbl_cost_estimate.grid(row=1, column=1, sticky="w", pady=(4, 0))

        self._prompt_visible = False

        # Bind prompt text change to cost estimate update (debounced)
        self._cost_update_after_id: str | None = None
        self._txt_prompt.text.bind("<KeyRelease>", self._on_prompt_text_changed)

        # Initial button state
        self._update_claude_button_states()

    def _build_log_panel(self, frame: ttk.Frame) -> None:
        """Build the read-only log panel with monospace font and color tags."""
        log_font = ("Consolas", 9) if sys.platform == "win32" else ("Menlo", 9)
        self.log = ScrolledText(
            frame,
            height=8,
            font=log_font,
            state="disabled",
            wrap="word",
        )
        self.log.pack(fill=tk.BOTH, expand=True)

        # Configure log line color tags
        self.log.text.tag_configure("info", foreground="#2C3E50")
        self.log.text.tag_configure("device", foreground="#2C3E50", font=(*log_font, "bold"))
        self.log.text.tag_configure("progress", foreground="#95A5A6")
        self.log.text.tag_configure("done", foreground="#18BC9C")
        self.log.text.tag_configure("error", foreground="#E74C3C")
        self.log.text.tag_configure("claude", foreground="#2C3E50")
        self.log.text.tag_configure("claude_done", foreground="#18BC9C")
        self.log.text.tag_configure("cost", foreground="#95A5A6")

    # ------------------------------------------------------------------
    # Public API (called by Plan 03 dispatcher)
    # ------------------------------------------------------------------

    def append_log(self, message: str, tag: str = "info") -> None:
        """Append a timestamped line to the log panel. Thread-safe via root.after."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        line = f"[{timestamp}] {message}\n"

        def _do_append() -> None:
            self.log.text.configure(state="normal")
            self.log.text.insert(tk.END, line, tag)
            self.log.text.configure(state="disabled")
            self.log.text.see(tk.END)

        # If called from a non-main thread, schedule via root.after
        if threading.current_thread() is threading.main_thread():
            _do_append()
        else:
            self.root.after(0, _do_append)

    def add_file(self, file_path: Path) -> str | None:
        """Add a file to the queue. Returns iid or None if duplicate/invalid extension."""
        if file_path.suffix.lower() not in self.AUDIO_EXTENSIONS:
            return None

        # Check for duplicates (by full path)
        full_path_str = str(file_path.resolve())
        for iid, data in self._row_data.items():
            if data["full_path"] == full_path_str:
                return None  # Already in queue

        # Get file size
        try:
            size_bytes = file_path.stat().st_size
            size_str = _format_filesize(size_bytes)
        except OSError:
            size_str = "–"

        status_text = _("ui.status.waiting")
        iid = self.tree.insert(
            "",
            tk.END,
            values=(file_path.name, size_str, "...", status_text),
            tags=("waiting",),
        )

        self._row_data[iid] = {
            "full_path": full_path_str,
            "error_msg": "",
            "result_text": "",
        }

        self._update_empty_state()
        self._update_transcribe_button_state()

        # Log the addition
        self.append_log(_("log.file_added").format(filename=file_path.name))

        # Probe duration asynchronously
        self.root.after(0, lambda: self._start_duration_probe(iid, file_path))

        return iid

    def update_row_status(self, iid: str, status: str, tag: str, detail: str = "") -> None:
        """Update the status column and tag for a row."""
        current_values = list(self.tree.item(iid, "values"))
        current_values[3] = status
        self.tree.item(iid, values=current_values, tags=(tag,))
        if detail and iid in self._row_data:
            self._row_data[iid]["error_msg"] = detail

    def update_row_progress(self, iid: str, pct: int, eta_str: str = "") -> None:
        """Update status cell to show percentage and ETA for the active row."""
        progress_text = f"{pct}%"
        if eta_str:
            progress_text += f" (~{eta_str})"
        current_values = list(self.tree.item(iid, "values"))
        current_values[3] = progress_text
        self.tree.item(iid, values=current_values, tags=("processing",))

    def mark_row_done(self, iid: str) -> None:
        """Set row to 'hotovo' status with done tag."""
        self.update_row_status(iid, _("ui.status.done"), "done")

    def mark_row_error(self, iid: str, error_msg: str) -> None:
        """Set row to 'chyba' status with error tag. Store error_msg for tooltip."""
        self.update_row_status(iid, _("ui.status.error"), "error", detail=error_msg)

    def get_waiting_files(self) -> list[tuple[str, str]]:
        """Return list of (iid, full_path) for all rows with 'waiting' tag."""
        result = []
        for iid in self.tree.get_children():
            tags = self.tree.item(iid, "tags")
            if "waiting" in tags:
                result.append((iid, self._row_data[iid]["full_path"]))
        return result

    def set_transcribing(self, active: bool) -> None:
        """Toggle UI between idle and transcribing states (button label, disable/enable)."""
        if active:
            self.btn_transcribe.configure(
                text=_("ui.action.stop"),
                bootstyle="danger",  # type: ignore[call-arg]
            )
        else:
            self.btn_transcribe.configure(
                text=_("ui.action.transcribe"),
                bootstyle="success",  # type: ignore[call-arg]
            )
        self._update_transcribe_button_state()

    def update_overall_progress(self, done: int, total: int) -> None:
        """Update the progress bar and 'X / Y souboru' label."""
        self.progressbar.configure(maximum=max(total, 1), value=done)
        count_text = _("ui.action.progress_count").format(done=done, total=total)
        self.lbl_progress_count.configure(text=count_text)

    def get_output_dir(self) -> str:
        """Return current output directory. Empty string means 'same as source file'."""
        return self._output_dir.get()

    def reload_strings(self) -> None:
        """Reload all translatable strings in response to a language switch."""
        # Toolbar buttons
        self.btn_add_files.configure(text=_("ui.toolbar.add_files"))
        self.btn_add_folder.configure(text=_("ui.toolbar.add_folder"))
        self.btn_remove.configure(text=_("ui.toolbar.remove_selected"))
        # Queue headings
        self.tree.heading("filename", text=_("ui.queue.col_file"))
        self.tree.heading("filesize", text=_("ui.queue.col_size"))
        self.tree.heading("duration", text=_("ui.queue.col_duration"))
        self.tree.heading("status", text=_("ui.queue.col_status"))
        # Action bar
        if not self._running:
            self.btn_transcribe.configure(text=_("ui.action.transcribe"))
        # New buttons
        self._btn_transcribe_edit.configure(text=_("ui.action.transcribe_edit"))
        self._btn_edit_only.configure(text=_("ui.action.edit_only"))
        # Prompt toggle
        if self._prompt_visible:
            self._btn_toggle_prompt.configure(text=_("ui.action.toggle_prompt_hide"))
        else:
            self._btn_toggle_prompt.configure(text=_("ui.action.toggle_prompt_show"))
        # Empty label
        self._empty_label.configure(text=f"{_('ui.empty.heading')}\n{_('ui.empty.body')}")
        # Reload default prompt if not customized
        self._load_prompt_text()

    # ------------------------------------------------------------------
    # Claude UI helpers
    # ------------------------------------------------------------------

    def _update_claude_button_states(self) -> None:
        """Enable/disable Claude buttons based on API key, queue state, and running status."""
        from src.whisperai.utils.settings import get_api_key
        has_key = get_api_key() is not None
        has_files = bool(self.tree.get_children())
        has_done = any(
            "done" in self.tree.item(iid, "tags")
            for iid in self.tree.get_children()
        )

        if self._running:
            self._btn_transcribe_edit.configure(state="disabled")
            self._btn_edit_only.configure(state="disabled")
            return

        # "Přepsat + Upravit" — needs key and files
        if has_key and has_files:
            self._btn_transcribe_edit.configure(state="normal")
        else:
            self._btn_transcribe_edit.configure(state="disabled")
            if not has_key and has_files:
                ToolTip(self._btn_transcribe_edit, text=_("ui.action.no_key_tooltip"))

        # "Upravit" — needs at least one done row
        if has_done:
            self._btn_edit_only.configure(state="normal")
        else:
            self._btn_edit_only.configure(state="disabled")

    def _refresh_profile_combo(self) -> None:
        """Reload the profile dropdown from settings."""
        no_profile = _("ui.action.no_profile") if "_" in dir(__builtins__) else "No profile"
        try:
            no_profile = _("ui.action.no_profile")
        except Exception:
            no_profile = "No profile"

        profiles: dict = {}
        if self._settings is not None:
            profiles = self._settings.get("context_profiles") or {}

        values = [no_profile] + sorted(profiles.keys())
        self._combo_profile.configure(values=values)

        active = ""
        if self._settings is not None:
            active = self._settings.get("active_profile") or ""

        if active and active in profiles:
            self._combo_profile.set(active)
        else:
            self._combo_profile.current(0)

    def _on_profile_selected(self, event: tk.Event) -> None:
        """Load profile text into the context entry when a profile is selected."""
        selected = self._combo_profile.get()
        try:
            no_profile = _("ui.action.no_profile")
        except Exception:
            no_profile = "No profile"

        if selected == no_profile:
            self._context_var.set("")
        else:
            if self._settings is not None:
                profiles = self._settings.get("context_profiles") or {}
                text = profiles.get(selected, "")
                self._context_var.set(text)
                self._settings.set("active_profile", selected)

    def _on_manage_profile(self) -> None:
        """Show profile management menu (New / Rename / Delete)."""
        menu = tk.Menu(self.root, tearoff=False)
        menu.add_command(
            label=_("ui.action.new_profile"),
            command=self._profile_new,
        )
        menu.add_command(
            label=_("ui.action.rename_profile"),
            command=self._profile_rename,
        )
        menu.add_command(
            label=_("ui.action.delete_profile"),
            command=self._profile_delete,
        )
        try:
            x = self._btn_manage_profile.winfo_rootx()
            y = self._btn_manage_profile.winfo_rooty() + self._btn_manage_profile.winfo_height()
            menu.tk_popup(x, y)
        finally:
            menu.grab_release()

    def _profile_new(self) -> None:
        """Create a new context profile from the current context text."""
        name = simpledialog.askstring(
            _("ui.action.new_profile"),
            _("ui.action.new_profile"),
            parent=self.root,
        )
        if not name or not name.strip():
            return
        name = name.strip()
        if self._settings is not None:
            profiles = dict(self._settings.get("context_profiles") or {})
            profiles[name] = self._context_var.get()
            self._settings.set("context_profiles", profiles)
            self._settings.set("active_profile", name)
            self._settings.save()
        self._refresh_profile_combo()
        self._combo_profile.set(name)

    def _profile_rename(self) -> None:
        """Rename the currently selected profile."""
        current = self._combo_profile.get()
        try:
            no_profile = _("ui.action.no_profile")
        except Exception:
            no_profile = "No profile"
        if current == no_profile or not current:
            return
        new_name = simpledialog.askstring(
            _("ui.action.rename_profile"),
            _("ui.action.rename_profile"),
            initialvalue=current,
            parent=self.root,
        )
        if not new_name or not new_name.strip():
            return
        new_name = new_name.strip()
        if self._settings is not None:
            profiles = dict(self._settings.get("context_profiles") or {})
            text = profiles.pop(current, "")
            profiles[new_name] = text
            self._settings.set("context_profiles", profiles)
            self._settings.set("active_profile", new_name)
            self._settings.save()
        self._refresh_profile_combo()
        self._combo_profile.set(new_name)

    def _profile_delete(self) -> None:
        """Delete the currently selected profile after confirmation."""
        current = self._combo_profile.get()
        try:
            no_profile = _("ui.action.no_profile")
        except Exception:
            no_profile = "No profile"
        if current == no_profile or not current:
            return
        confirm = messagebox.askyesno(
            _("ui.action.delete_profile"),
            _("ui.action.delete_profile_confirm").format(name=current),
            parent=self.root,
        )
        if not confirm:
            return
        if self._settings is not None:
            profiles = dict(self._settings.get("context_profiles") or {})
            profiles.pop(current, None)
            self._settings.set("context_profiles", profiles)
            self._settings.set("active_profile", "")
            self._settings.save()
        self._refresh_profile_combo()

    def _toggle_prompt_editor(self) -> None:
        """Toggle visibility of the inline prompt editor."""
        self._prompt_visible = not self._prompt_visible
        if self._prompt_visible:
            self._prompt_frame.grid(row=3, column=0, columnspan=6, sticky="ew", pady=(4, 0))
            self._btn_toggle_prompt.configure(text=_("ui.action.toggle_prompt_hide"))
            self._update_cost_estimate()
        else:
            self._prompt_frame.grid_forget()
            self._btn_toggle_prompt.configure(text=_("ui.action.toggle_prompt_show"))

    def _load_prompt_text(self) -> None:
        """Load prompt text from settings, or fall back to the bundled default."""
        prompt_text = ""
        if self._settings is not None:
            prompt_text = self._settings.get("claude_prompt") or ""

        if not prompt_text:
            try:
                from src.whisperai.utils.settings import get_default_prompt
                from src.whisperai.utils.i18n import get_current_language
                prompt_text = get_default_prompt(get_current_language())
            except Exception:
                prompt_text = ""

        if hasattr(self, "_txt_prompt"):
            self._txt_prompt.text.configure(state="normal")
            self._txt_prompt.text.delete("1.0", tk.END)
            self._txt_prompt.text.insert("1.0", prompt_text)

    def _reset_prompt(self) -> None:
        """Reset the prompt to the bundled default."""
        if self._settings is not None:
            self._settings.set("claude_prompt", "")
        self._load_prompt_text()

    def _on_prompt_text_changed(self, event: tk.Event) -> None:
        """Debounce cost estimate update on prompt text change."""
        if self._cost_update_after_id is not None:
            self.root.after_cancel(self._cost_update_after_id)
        self._cost_update_after_id = self.root.after(500, self._update_cost_estimate)

    def _update_cost_estimate(self) -> None:
        """Update the cost estimate label based on current prompt + context length."""
        if not hasattr(self, "_lbl_cost_estimate"):
            return
        try:
            from src.whisperai.core.claude_cleaner import estimate_cost_pre_send
            prompt_text = self._txt_prompt.text.get("1.0", tk.END)
            context_text = self._context_var.get()
            # Estimate ~500 chars for a typical short audio transcript chunk
            sample_transcript_chars = 500
            char_count = len(prompt_text) + len(context_text) + sample_transcript_chars
            model = "claude-haiku-4-5"
            if self._settings is not None:
                model = self._settings.get("claude_model") or model
            cost = estimate_cost_pre_send(char_count, model)
            self._lbl_cost_estimate.configure(
                text=_("ui.action.cost_estimate").format(estimate=f"{cost:.4f}"),
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # VAD spinner
    # ------------------------------------------------------------------

    def _start_vad_spinner(self, iid: str) -> None:
        """Start animated dots in the status column during VAD preprocessing."""
        dots = ["\u00b7", "\u00b7\u00b7", "\u00b7\u00b7\u00b7"]
        self._vad_spinner_state: dict = {"index": 0, "running": True, "iid": iid}

        def tick() -> None:
            if not self._vad_spinner_state["running"]:
                return
            d = dots[self._vad_spinner_state["index"] % 3]
            self._vad_spinner_state["index"] += 1
            try:
                current_values = list(self.tree.item(iid, "values"))
                current_values[3] = f"{_('ui.status.processing')} {d}"
                self.tree.item(iid, values=current_values, tags=("processing",))
            except Exception:
                return
            self.root.after(400, tick)

        tick()

    def _stop_vad_spinner(self) -> None:
        """Stop the VAD spinner."""
        if hasattr(self, "_vad_spinner_state"):
            self._vad_spinner_state["running"] = False

    # ------------------------------------------------------------------
    # File collision handling
    # ------------------------------------------------------------------

    def _resolve_output_path(self, source_path: Path, suffix: str, output_dir: str) -> Path:
        """Return a non-colliding output path for the given source file and suffix.

        If the target already exists, adds incrementing counter: _prepis_2.txt, etc.
        Logs a collision notice when fallback naming is used.
        """
        base_dir = Path(output_dir) if output_dir else source_path.parent
        out_path = base_dir / (source_path.stem + suffix + ".txt")
        if out_path.exists():
            counter = 2
            while True:
                out_path = base_dir / (source_path.stem + f"{suffix}_{counter}.txt")
                if not out_path.exists():
                    break
                counter += 1
            self.append_log(
                _("log.saved_collision").format(filename=out_path.name),
                "info",
            )
        return out_path

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _update_empty_state(self) -> None:
        """Show or hide the empty-state label based on queue contents."""
        if self.tree.get_children():
            self._empty_label.place_forget()
        else:
            self._empty_label.place(relx=0.5, rely=0.5, anchor="center")

    def _update_transcribe_button_state(self) -> None:
        """Enable transcribe button when files exist; disable when queue is empty."""
        if self.tree.get_children():
            self.btn_transcribe.configure(state="normal")
        else:
            self.btn_transcribe.configure(state="disabled")
        self._update_claude_button_states()

    def _start_duration_probe(self, iid: str, file_path: Path) -> None:
        """Launch a background thread to probe the file duration via ffprobe."""
        thread = threading.Thread(
            target=self._probe_duration,
            args=(iid, file_path),
            daemon=True,
        )
        thread.start()

    def _probe_duration(self, iid: str, file_path: Path) -> None:
        """Probe file duration using ffprobe; update tree cell on completion."""
        duration_str = "\u2013"  # en-dash fallback
        try:
            # Try bundled ffprobe first, then system PATH
            ffprobe_name = "ffprobe.exe" if sys.platform == "win32" else "ffprobe"
            ffprobe_path = get_resource_path(f"bin/{ffprobe_name}")
            cmd = str(ffprobe_path) if ffprobe_path.exists() else "ffprobe"

            result = subprocess.run(
                [
                    cmd,
                    "-v", "quiet",
                    "-print_format", "json",
                    "-show_format",
                    str(file_path),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if result.returncode == 0:
                data = json.loads(result.stdout)
                duration_secs = float(data.get("format", {}).get("duration", 0))
                minutes = int(duration_secs // 60)
                seconds = int(duration_secs % 60)
                duration_str = f"{minutes:02d}:{seconds:02d}"
        except Exception:
            pass  # Silently fall back to en-dash

        # Update tree cell from the main thread
        def _update() -> None:
            if iid in self._row_data and self.tree.exists(iid):
                current_values = list(self.tree.item(iid, "values"))
                current_values[2] = duration_str
                self.tree.item(iid, values=current_values)

        self.root.after(0, _update)

    # ------------------------------------------------------------------
    # Toolbar callbacks
    # ------------------------------------------------------------------

    def _on_add_files(self) -> None:
        """Open file picker for audio files and add them to the queue."""
        ext_list = " ".join(f"*{ext}" for ext in self.AUDIO_EXTENSIONS)
        files = filedialog.askopenfilenames(
            title=_("ui.toolbar.add_files"),
            filetypes=[
                (_("ui.toolbar.add_files"), ext_list),
                ("All files", "*.*"),
            ],
        )
        for f in files:
            self.add_file(Path(f))

    def _on_add_folder(self) -> None:
        """Open folder picker and add all audio files from the chosen directory."""
        folder = filedialog.askdirectory(title=_("ui.toolbar.add_folder"))
        if not folder:
            return
        folder_path = Path(folder)
        audio_files = sorted(
            f for f in folder_path.glob("*")
            if f.suffix.lower() in self.AUDIO_EXTENSIONS
        )
        if not audio_files:
            self.append_log(
                _("log.folder_no_audio").format(folder=folder_path.name),
                "info",
            )
            return
        for file_path in audio_files:
            self.add_file(file_path)

    def _on_remove_selected(self) -> None:
        """Remove selected waiting rows from the queue (no-op for processing rows)."""
        selected = self.tree.selection()
        for iid in selected:
            tags = self.tree.item(iid, "tags")
            if "processing" in tags:
                continue  # Guard: cannot remove active row
            self.tree.delete(iid)
            self._row_data.pop(iid, None)
        self._update_empty_state()
        self._update_transcribe_button_state()

    def _on_browse_output(self) -> None:
        """Open folder picker for output directory and update the entry field."""
        folder = filedialog.askdirectory(title=_("ui.action.output_label"))
        if folder:
            self._output_dir.set(folder)

    def _on_transcribe_click(self) -> None:
        """Handle transcribe / stop button click (transcription only, no Claude)."""
        if self._running:
            # Stop requested (D-12)
            self._stop_event.set()
            self.append_log(_("log.stop_requested"), "info")
            return

        waiting = self.get_waiting_files()
        if not waiting:
            return

        self._claude_cleanup_mode = False
        self._running = True
        self._stop_event.clear()
        self._batch_files = waiting
        self._batch_done_count = 0
        self._batch_total = len(waiting)
        self.set_transcribing(True)
        self.update_overall_progress(0, self._batch_total)
        self.append_log(_("log.batch_start").format(count=self._batch_total), "info")

        # Start queue polling
        self._start_queue_poll()

        # Launch dispatcher in background thread
        thread = threading.Thread(target=self._run_dispatch, daemon=True)
        thread.start()

    def _on_transcribe_edit_click(self) -> None:
        """Handle 'Přepsat + Upravit' button — transcription + Claude cleanup pipeline."""
        if self._running:
            return

        waiting = self.get_waiting_files()
        if not waiting:
            return

        self._claude_cleanup_mode = True
        self._running = True
        self._stop_event.clear()
        self._batch_files = waiting
        self._batch_done_count = 0
        self._batch_total = len(waiting)
        self.set_transcribing(True)
        self._update_claude_button_states()
        self.update_overall_progress(0, self._batch_total)
        self.append_log(_("log.batch_start").format(count=self._batch_total), "info")

        # Persist current prompt text to settings before starting
        if self._settings is not None and hasattr(self, "_txt_prompt"):
            prompt_text = self._txt_prompt.text.get("1.0", tk.END).strip()
            self._settings.set("claude_prompt", prompt_text)

        # Start queue polling
        self._start_queue_poll()

        # Launch dispatcher in background thread
        thread = threading.Thread(target=self._run_dispatch, daemon=True)
        thread.start()

    def _on_edit_only_click(self) -> None:
        """Handle standalone 'Upravit' — Claude cleanup on all completed files."""
        done_iids = [
            iid for iid in self.tree.get_children()
            if "done" in self.tree.item(iid, "tags")
        ]
        if not done_iids:
            return

        # Persist current prompt text to settings
        if self._settings is not None and hasattr(self, "_txt_prompt"):
            prompt_text = self._txt_prompt.text.get("1.0", tk.END).strip()
            self._settings.set("claude_prompt", prompt_text)

        for iid in done_iids:
            filepath = self._row_data[iid]["full_path"]
            text = self._row_data[iid].get("result_text", "")
            thread = threading.Thread(
                target=self._run_claude_cleanup,
                args=(iid, text, filepath),
                daemon=True,
            )
            thread.start()

    def _run_claude_cleanup(self, iid: str, text: str, filepath: str) -> None:
        """Run Claude cleanup for one file. Called from a background thread.

        Saves _upraveno.txt with summary + cleaned transcript + diff.
        Always assumes _prepis.txt was already saved before this point (CLAUDE-04).
        """
        from src.whisperai.utils.settings import get_api_key, get_default_prompt
        from src.whisperai.utils.i18n import get_current_language
        from src.whisperai.core.claude_cleaner import (
            clean_transcript,
            calculate_actual_cost,
            generate_diff,
        )

        api_key = get_api_key()
        if api_key is None:
            self.append_log(_("log.claude_no_key"), "error")
            return

        model = "claude-haiku-4-5"
        if self._settings is not None:
            model = self._settings.get("claude_model") or model

        # Get prompt: from prompt editor if visible, else from settings, else default
        prompt = ""
        if self._prompt_visible and hasattr(self, "_txt_prompt"):
            # Read from the text widget in a thread-safe way
            prompt = self._txt_prompt.text.get("1.0", tk.END).strip()
        if not prompt and self._settings is not None:
            prompt = self._settings.get("claude_prompt") or ""
        if not prompt:
            try:
                prompt = get_default_prompt(get_current_language())
            except Exception:
                prompt = ""

        context_text = self._context_var.get()

        try:
            result = clean_transcript(
                text=text,
                system_prompt=prompt,
                context_text=context_text,
                model=model,
                api_key=api_key,
                progress_queue=self._ui_queue,
                task_id=iid,
                timeout=300.0,
            )
        except Exception as exc:
            reason = str(exc)
            self._ui_queue.put({
                "type": "claude_error",
                "iid": iid,
                "reason": reason,
            })
            return

        # Save _upraveno.txt with output format (D-07)
        output_dir = self._output_dir.get()
        source_path = Path(filepath)
        out_path = self._resolve_output_path(source_path, "_upraveno", output_dir)

        cleaned_text = result["result"]
        diff = generate_diff(text, cleaned_text)

        file_content = cleaned_text
        if diff.strip():
            file_content += "\n\n---\n\n## Comparison with Original\n\n" + diff

        try:
            out_path.write_text(file_content, encoding="utf-8")
        except Exception as exc:
            self._ui_queue.put({
                "type": "claude_error",
                "iid": iid,
                "reason": f"Write failed: {exc}",
            })
            return

        # Calculate cost and report
        cost = calculate_actual_cost(result["input_tokens"], result["output_tokens"], model)
        total_tokens = result["input_tokens"] + result["output_tokens"]
        self._ui_queue.put({
            "type": "claude_done",
            "iid": iid,
            "tokens": total_tokens,
            "cost": cost,
        })

    def _run_dispatch(self) -> None:
        """Background thread: dispatches files to ProcessPoolExecutor workers."""
        try:
            from src.whisperai.core.transcriber import transcribe_file, _worker_init
        except ImportError as e:
            self._ui_queue.put({
                "type": "log",
                "message": f"Transcription unavailable: {e}. Install whisper and torch.",
                "tag": "error",
            })
            self._ui_queue.put({"type": "batch_complete"})
            return
        device_str = getattr(self.root, "_device_str", "cpu")
        worker_count = getattr(self.root, "_worker_count", 1)
        model_path = str(get_resource_path("models"))

        mp_queue = multiprocessing.Queue()

        # Drain thread: forward mp_queue messages to ui_queue
        def drain_mp():
            while True:
                try:
                    msg = mp_queue.get(timeout=0.2)
                    if msg is None:
                        break
                    self._ui_queue.put(msg)
                except Exception:
                    if self._stop_event.is_set() and mp_queue.empty():
                        break

        drain_thread = threading.Thread(target=drain_mp, daemon=True)
        drain_thread.start()

        try:
            with concurrent.futures.ProcessPoolExecutor(
                max_workers=worker_count,
                initializer=_worker_init,
                initargs=(model_path, device_str, mp_queue),
            ) as pool:
                # Submit ALL files upfront for true parallelism (TRANS-04)
                future_to_iid: dict[concurrent.futures.Future, tuple[str, str]] = {}
                for iid, filepath in self._batch_files:
                    # Mark as processing in UI
                    self._ui_queue.put({
                        "type": "status_update",
                        "iid": iid,
                        "status": "processing",
                    })
                    self._ui_queue.put({
                        "type": "log",
                        "message": _("log.file_processing").format(filename=Path(filepath).name),
                        "tag": "info",
                    })
                    future = pool.submit(transcribe_file, filepath, iid)
                    future_to_iid[future] = (iid, filepath)

                # Drain results as they complete
                for future in concurrent.futures.as_completed(future_to_iid):
                    iid, filepath = future_to_iid[future]

                    # Check stop event — cancel remaining pending futures
                    if self._stop_event.is_set():
                        # Cancel all futures that haven't started yet
                        for pending_future in future_to_iid:
                            if pending_future is not future and not pending_future.done():
                                pending_future.cancel()
                        # Revert un-started files to waiting
                        remaining = []
                        for f, (r_iid, r_path) in future_to_iid.items():
                            if f.cancelled() or (f is not future and not f.done()):
                                remaining.append((r_iid, r_path))
                        if remaining:
                            self._ui_queue.put({
                                "type": "reverted",
                                "files": remaining,
                            })
                        # Still process THIS completed future's result below
                        # Then break out of the loop
                        self._process_future_result(future, iid, filepath)
                        break

                    self._process_future_result(future, iid, filepath)

        finally:
            mp_queue.put(None)  # Signal drain thread to stop
            drain_thread.join(timeout=5)
            self._ui_queue.put({"type": "batch_complete"})

    def _process_future_result(
        self, future: concurrent.futures.Future, iid: str, filepath: str
    ) -> None:
        """Process the result of a completed transcription future. Called from _run_dispatch thread."""
        try:
            result = future.result()

            # Determine output path using collision-safe helper (D-08, D-09)
            output_dir = self._output_dir.get()
            source_path = Path(filepath)
            out_path = self._resolve_output_path(source_path, "_prepis", output_dir)

            # Save transcript (D-09: auto-save, UTF-8 encoding)
            out_path.write_text(result["text"], encoding="utf-8")

            self._ui_queue.put({
                "type": "file_done",
                "iid": iid,
                "filepath": filepath,
                "output_path": str(out_path),
                "text": result["text"],
            })

            # Pipeline mode: trigger Claude cleanup after each transcription (D-05)
            if self._claude_cleanup_mode and not self._stop_event.is_set():
                thread = threading.Thread(
                    target=self._run_claude_cleanup,
                    args=(iid, result["text"], filepath),
                    daemon=True,
                )
                thread.start()

        except Exception as exc:
            error_str = str(exc)
            # Classify error for user-friendly message (TRANS-06)
            if "out of memory" in error_str.lower() or "cuda" in error_str.lower():
                user_error = _("err.out_of_memory")
            elif "no such file" in error_str.lower() or "not found" in error_str.lower():
                user_error = _("err.file_not_found")
            elif "invalid" in error_str.lower() or "format" in error_str.lower():
                user_error = _("err.unsupported_format")
            else:
                user_error = _("err.generic")

            self._ui_queue.put({
                "type": "file_error",
                "iid": iid,
                "filepath": filepath,
                "error": error_str,
                "user_error": user_error,
            })

    def _get_row_tag(self, iid: str) -> str:
        """Return the current tag of a row (waiting/processing/done/error)."""
        try:
            tags = self.tree.item(iid, "tags")
            return tags[0] if tags else "waiting"
        except Exception:
            return "waiting"

    def _start_queue_poll(self) -> None:
        """Start polling the ui_queue for messages from the dispatcher thread."""
        self._drain_ui_queue()

    def _drain_ui_queue(self) -> None:
        """Drain all pending ui_queue messages and schedule next poll if still running."""
        try:
            while True:
                msg = self._ui_queue.get_nowait()
                self._handle_ui_message(msg)
        except queue.Empty:
            pass
        if self._running:
            self.root.after(100, self._drain_ui_queue)

    def _handle_ui_message(self, msg: dict) -> None:
        """Process a message from the dispatcher thread. Always called in the main thread."""
        msg_type = msg["type"]

        if msg_type == "vad_analyzing":
            iid = msg.get("task_id")
            if iid:
                self._start_vad_spinner(iid)
            self.append_log(_("log.vad_analyzing"), "info")

        elif msg_type == "vad_done":
            self._stop_vad_spinner()
            stats = msg["vad_stats"]
            self.append_log(
                _("log.vad_result").format(
                    segments=stats["segment_count"],
                    speech_s=stats["speech_duration_s"],
                    total_s=stats["total_duration_s"],
                ),
                "info",
            )

        elif msg_type == "progress":
            iid = msg["task_id"]
            n, total = msg["n"], msg["total"]
            pct = msg.get("pct", int(n / max(total, 1) * 100))
            eta = msg.get("eta_seconds", 0)
            # Format ETA as M:SS
            eta_str = f"{eta // 60}:{eta % 60:02d}" if eta > 0 else ""
            self.update_row_progress(iid, pct, eta_str)
            log_msg = _("log.whisper_progress").format(pct=pct, n=n, total=total)
            if eta_str:
                log_msg += f" — ~{eta_str}"
            self.append_log(log_msg, "progress")

        elif msg_type == "status_update":
            iid = msg["iid"]
            status = msg["status"]
            if status == "processing":
                self.update_row_status(iid, _("ui.status.processing"), "processing")

        elif msg_type == "log":
            self.append_log(msg["message"], msg.get("tag", "info"))

        elif msg_type == "file_done":
            iid = msg["iid"]
            self.mark_row_done(iid)
            self._row_data[iid]["result_text"] = msg["text"]
            self._batch_done_count += 1
            self.update_overall_progress(self._batch_done_count, self._batch_total)
            self.append_log(
                _("log.file_done").format(
                    filename=Path(msg["filepath"]).name,
                    output_path=msg["output_path"],
                ),
                "done",
            )
            # Update Claude button states (Upravit may become enabled)
            self._update_claude_button_states()

        elif msg_type == "file_error":
            iid = msg["iid"]
            self.mark_row_error(iid, msg["user_error"])
            self._batch_done_count += 1
            self.update_overall_progress(self._batch_done_count, self._batch_total)
            self.append_log(
                _("log.error").format(
                    filename=Path(msg["filepath"]).name,
                    error=msg["error"],
                ),
                "error",
            )

        elif msg_type == "reverted":
            for iid, _path in msg["files"]:
                self.update_row_status(iid, _("ui.status.waiting"), "waiting")

        elif msg_type == "claude_processing":
            self.append_log(_("log.claude_processing"), "claude")

        elif msg_type == "claude_chunk":
            self.append_log(
                _("log.claude_chunk").format(n=msg["n"], total=msg["total"]),
                "claude",
            )

        elif msg_type == "claude_slow":
            self.append_log(
                _("log.claude_slow").format(elapsed=msg["elapsed"]),
                "claude",
            )

        elif msg_type == "claude_done":
            self.append_log(
                _("log.claude_done").format(tokens=msg["tokens"], cost=f"{msg['cost']:.4f}"),
                "claude_done",
            )

        elif msg_type == "claude_error":
            iid = msg["iid"]
            self.update_row_status(iid, _("ui.status.claude_error"), "claude_error")
            self.append_log(
                _("log.claude_error").format(reason=msg["reason"]),
                "error",
            )

        elif msg_type == "batch_complete":
            self._running = False
            self._claude_cleanup_mode = False
            self.set_transcribing(False)
            self._update_claude_button_states()
            if self._stop_event.is_set():
                remaining = self._batch_total - self._batch_done_count
                self.append_log(
                    _("log.batch_stopped").format(done=self._batch_done_count, remaining=remaining),
                    "info",
                )
            else:
                self.append_log(
                    _("log.batch_done").format(count=self._batch_done_count),
                    "done",
                )

            # D-04: After batch completes, check if new waiting files were added during transcription.
            # If so, automatically start a new batch for them.
            new_waiting = self.get_waiting_files()
            if new_waiting and not self._stop_event.is_set():
                self.append_log(
                    _("log.batch_start").format(count=len(new_waiting)),
                    "info",
                )
                self._running = True
                self._stop_event.clear()
                self._batch_files = new_waiting
                self._batch_done_count = 0
                self._batch_total = len(new_waiting)
                self.set_transcribing(True)
                self.update_overall_progress(0, self._batch_total)
                self._start_queue_poll()
                thread = threading.Thread(target=self._run_dispatch, daemon=True)
                thread.start()

    # ------------------------------------------------------------------
    # Treeview interaction callbacks
    # ------------------------------------------------------------------

    def _on_tree_motion(self, event: tk.Event) -> None:
        """Update tooltip text when mouse moves over the Treeview."""
        iid = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)

        if not iid or iid not in self._row_data:
            self._tooltip.text = ""
            return

        tags = self.tree.item(iid, "tags")

        if col == "#1":
            # Filename column: show full path
            self._tooltip.text = self._row_data[iid]["full_path"]
        elif col == "#4" and ("error" in tags or "claude_error" in tags):
            # Status column for error rows: show error detail
            error_msg = self._row_data[iid]["error_msg"]
            self._tooltip.text = error_msg if error_msg else ""
        else:
            self._tooltip.text = ""

    def _on_tree_right_click(self, event: tk.Event) -> None:
        """Show context menu with save-as option for done rows."""
        iid = self.tree.identify_row(event.y)
        if not iid or iid not in self._row_data:
            return
        tags = self.tree.item(iid, "tags")
        if "done" not in tags:
            return

        menu = tk.Menu(self.root, tearoff=False)
        menu.add_command(
            label=_("ui.menu.save_as"),
            command=lambda: self._save_row_as(iid),
        )
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _on_tree_double_click(self, event: tk.Event) -> None:
        """Trigger save-as on double-click for done rows."""
        iid = self.tree.identify_row(event.y)
        if not iid or iid not in self._row_data:
            return
        tags = self.tree.item(iid, "tags")
        if "done" in tags:
            self._save_row_as(iid)

    def _save_row_as(self, iid: str) -> None:
        """Open save-as dialog and write result text for the given row."""
        result_text = self._row_data.get(iid, {}).get("result_text", "")
        save_path = filedialog.asksaveasfilename(
            title=_("ui.menu.save_as"),
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )
        if save_path:
            Path(save_path).write_text(result_text, encoding="utf-8")

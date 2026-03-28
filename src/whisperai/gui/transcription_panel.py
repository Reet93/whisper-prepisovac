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
from tkinter import filedialog
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

    def __init__(self, parent: ttk.Frame, root: ttk.Window) -> None:
        self.parent = parent
        self.root = root
        # iid -> {full_path, error_msg, result_text}
        self._row_data: dict[str, dict] = {}
        self._output_dir = tk.StringVar(value="")
        self._running = False
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
        """Build the action bar: output folder picker, transcribe button, progress bar."""
        frame.columnconfigure(1, weight=1)  # entry_output_dir expands

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
        """Handle transcribe / stop button click."""
        if self._running:
            # Stop requested (D-12)
            self._stop_event.set()
            self.append_log(_("log.stop_requested"), "info")
            return

        waiting = self.get_waiting_files()
        if not waiting:
            return

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

    def _process_future_result(self, future: concurrent.futures.Future, iid: str, filepath: str) -> None:
        """Process the result of a completed transcription future. Called from _run_dispatch thread."""
        try:
            result = future.result()

            # Determine output path (D-08, D-09)
            output_dir = self._output_dir.get()
            source_path = Path(filepath)
            base_dir = Path(output_dir) if output_dir else source_path.parent
            out_path = base_dir / (source_path.stem + "_prepis.txt")

            # Avoid overwriting existing files — add counter suffix
            if out_path.exists():
                counter = 2
                while True:
                    out_path = base_dir / (source_path.stem + f"_prepis_{counter}.txt")
                    if not out_path.exists():
                        break
                    counter += 1

            # Save transcript (D-09: auto-save, UTF-8 encoding)
            out_path.write_text(result["text"], encoding="utf-8")

            self._ui_queue.put({
                "type": "file_done",
                "iid": iid,
                "filepath": filepath,
                "output_path": str(out_path),
                "text": result["text"],
            })

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
            self.append_log(_("log.vad_analyzing"), "info")

        elif msg_type == "vad_done":
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

        elif msg_type == "batch_complete":
            self._running = False
            self.set_transcribing(False)
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
        elif col == "#4" and "error" in tags:
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

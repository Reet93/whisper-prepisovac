"""First-launch model download dialog.

Shows a blocking modal dialog with indeterminate progress bar while the
faster-whisper medium model is downloaded via huggingface_hub.
"""
import threading
import ttkbootstrap as ttk
from ttkbootstrap.constants import BOTH, YES, W, X, RIGHT, LEFT

from src.whisperai.utils.model_path import get_model_path


class ModelDownloadDialog(ttk.Toplevel):
    """Blocking modal dialog for first-launch model download.

    States: downloading -> success (auto-close 1500ms)
            downloading -> error (retry/cancel)
            downloading -> cancel_confirm -> cancelled
    """

    def __init__(self, parent: ttk.Window):
        super().__init__(parent)
        self.title(_("download.title"))
        self.resizable(False, False)
        self.minsize(400, 220)
        self.protocol("WM_DELETE_WINDOW", self._on_cancel_click)
        self.grab_set()  # modal

        self._parent = parent
        self._download_thread = None
        self._cancelled = False
        self._download_success = False

        self._build_ui()
        self._start_download()

    def _build_ui(self):
        """Build the dialog layout per UI-SPEC."""
        self._frame = ttk.Frame(self, padding=16)
        self._frame.pack(fill=BOTH, expand=YES)

        # Title label
        self._title_label = ttk.Label(
            self._frame,
            text=_("download.title"),
            font=("", 13, "bold"),
        )
        self._title_label.pack(anchor=W, pady=(0, 8))

        # Body text
        self._body_label = ttk.Label(
            self._frame,
            text=_("download.body"),
            wraplength=360,
            font=("", 9),
        )
        self._body_label.pack(anchor=W, pady=(0, 8))

        # Progress bar (indeterminate)
        self._progress = ttk.Progressbar(
            self._frame,
            mode="indeterminate",
            bootstyle="primary",
        )
        self._progress.pack(fill=X, pady=(0, 8))

        # Status label
        self._status_label = ttk.Label(
            self._frame,
            text=_("download.progress"),
            font=("", 9),
        )
        self._status_label.pack(anchor=W, pady=(0, 4))

        # Size hint
        self._hint_label = ttk.Label(
            self._frame,
            text=_("download.size_hint"),
            font=("", 9),
            foreground="#95A5A6",
        )
        self._hint_label.pack(anchor=W, pady=(0, 8))

        # Button frame
        self._btn_frame = ttk.Frame(self._frame)
        self._btn_frame.pack(fill=X, pady=(8, 0))

        self._cancel_btn = ttk.Button(
            self._btn_frame,
            text=_("download.cancel"),
            bootstyle="danger-outline",
            command=self._on_cancel_click,
        )
        self._cancel_btn.pack(side=RIGHT)

    def _start_download(self):
        """Start model download in background thread."""
        self._cancelled = False
        self._progress.start(15)  # animation interval ms

        self._download_thread = threading.Thread(
            target=self._download_worker,
            daemon=True,
        )
        self._download_thread.start()
        self._poll_download()

    def _download_worker(self):
        """Download faster-whisper medium model via WhisperModel init."""
        try:
            model_path = str(get_model_path())
            # Ensure directory exists
            get_model_path().mkdir(parents=True, exist_ok=True)

            # This triggers huggingface_hub download if model not cached
            from faster_whisper import WhisperModel
            _model = WhisperModel(
                "medium",
                device="cpu",
                compute_type="int8",
                download_root=model_path,
            )
            del _model  # release memory — model will be loaded again by transcription
            if not self._cancelled:
                self._download_success = True
        except Exception as e:
            if not self._cancelled:
                self._download_error = str(e)
                self._download_success = False

    def _poll_download(self):
        """Poll download thread status from main thread."""
        if self._cancelled:
            return

        if self._download_thread and self._download_thread.is_alive():
            self.after(200, self._poll_download)
            return

        # Thread finished
        self._progress.stop()

        if self._download_success:
            self._show_success()
        elif hasattr(self, '_download_error'):
            self._show_error(self._download_error)

    def _show_success(self):
        """Show success state and auto-close after 1500ms."""
        self._progress.pack_forget()
        self._status_label.configure(text=_("download.complete"))
        self._hint_label.pack_forget()
        self._cancel_btn.pack_forget()
        self.after(1500, self._close_success)

    def _close_success(self):
        """Close dialog and signal success."""
        self.grab_release()
        self.destroy()

    def _show_error(self, error_msg: str):
        """Show error state with retry and cancel buttons."""
        self._progress.pack_forget()
        self._status_label.configure(
            text=_("download.error_heading"),
            font=("", 13, "bold"),
            foreground="#E74C3C",
        )
        self._hint_label.configure(
            text=_("download.error_body"),
            foreground="",
        )

        # Replace buttons
        for w in self._btn_frame.winfo_children():
            w.destroy()

        ttk.Button(
            self._btn_frame,
            text=_("download.retry"),
            bootstyle="secondary",
            command=self._on_retry,
        ).pack(side=RIGHT, padx=(4, 0))

        ttk.Button(
            self._btn_frame,
            text=_("download.cancel"),
            bootstyle="danger",
            command=self._on_cancel_confirm,
        ).pack(side=RIGHT)

    def _on_retry(self):
        """Retry download after error."""
        # Rebuild progress UI
        self._status_label.configure(
            text=_("download.progress"),
            font=("", 9),
            foreground="",
        )
        self._hint_label.configure(
            text=_("download.size_hint"),
            foreground="#95A5A6",
        )

        # Re-add progress bar
        self._progress = ttk.Progressbar(
            self._frame,
            mode="indeterminate",
            bootstyle="primary",
        )
        # Insert before status label
        self._progress.pack(fill=X, pady=(0, 8), before=self._status_label)

        # Reset buttons
        for w in self._btn_frame.winfo_children():
            w.destroy()
        self._cancel_btn = ttk.Button(
            self._btn_frame,
            text=_("download.cancel"),
            bootstyle="danger-outline",
            command=self._on_cancel_click,
        )
        self._cancel_btn.pack(side=RIGHT)

        if hasattr(self, '_download_error'):
            del self._download_error
        self._start_download()

    def _on_cancel_click(self):
        """Show inline cancel confirmation."""
        for w in self._btn_frame.winfo_children():
            w.destroy()

        ttk.Label(
            self._btn_frame,
            text=_("download.cancel_confirm"),
            font=("", 9),
        ).pack(side=LEFT)

        ttk.Button(
            self._btn_frame,
            text=_("download.cancel"),
            bootstyle="danger",
            command=self._on_cancel_confirm,
        ).pack(side=RIGHT, padx=(4, 0))

        ttk.Button(
            self._btn_frame,
            text="<-",
            bootstyle="secondary",
            command=self._restore_cancel_button,
        ).pack(side=RIGHT)

    def _restore_cancel_button(self):
        """Restore normal cancel button after declining cancel confirmation."""
        for w in self._btn_frame.winfo_children():
            w.destroy()
        self._cancel_btn = ttk.Button(
            self._btn_frame,
            text=_("download.cancel"),
            bootstyle="danger-outline",
            command=self._on_cancel_click,
        )
        self._cancel_btn.pack(side=RIGHT)

    def _on_cancel_confirm(self):
        """User confirmed cancellation."""
        self._cancelled = True
        self.grab_release()
        self.destroy()

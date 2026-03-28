"""Whisper transcription worker — runs in ProcessPoolExecutor subprocess."""
import sys
import whisper
import torch
from pathlib import Path

from src.whisperai.core.vad import preprocess_audio

_model = None  # Module-level; set once per worker by _worker_init


def _worker_init(model_path: str, device: str) -> None:
    """ProcessPoolExecutor initializer. Loads Whisper model once per worker process."""
    global _model
    _model = whisper.load_model(
        "medium",
        device=device,
        download_root=model_path,
    )


def transcribe_file(
    audio_path: str,
    progress_queue,  # multiprocessing.Queue — cannot type-hint without import
    task_id: str,
) -> dict:
    """Transcribe one audio file with VAD preprocessing and progress reporting.

    Args:
        audio_path: Path to the audio file.
        progress_queue: multiprocessing.Queue for sending progress messages back to dispatcher.
        task_id: Unique identifier for this file in the queue (used for UI updates).

    Returns:
        dict with keys: "text" (full transcript), "vad_stats" (from preprocess_audio).

    Raises:
        Exception with descriptive message on failure.
    """
    import tempfile
    import torchaudio

    # Step 1: VAD preprocessing — strip silence (D-19)
    speech_tensor, vad_stats = preprocess_audio(audio_path)
    progress_queue.put({
        "type": "vad_done",
        "task_id": task_id,
        "vad_stats": vad_stats,
    })

    if vad_stats["segment_count"] == 0:
        return {"text": "", "vad_stats": vad_stats}

    # Step 2: Write speech-only audio to temp WAV for Whisper
    temp_wav = None
    try:
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_wav_path = temp_wav.name
        temp_wav.close()

        torchaudio.save(
            temp_wav_path,
            speech_tensor.unsqueeze(0),  # Add channel dimension
            16000,
        )

        # Step 3: Inject progress hook into whisper.transcribe's tqdm
        import tqdm as tqdm_module

        class _ProgressTqdm(tqdm_module.tqdm):
            def update(self, n=1):
                super().update(n)
                progress_queue.put({
                    "type": "progress",
                    "task_id": task_id,
                    "n": self.n,
                    "total": self.total,
                })

        whisper_transcribe_mod = sys.modules.get("whisper.transcribe")
        original_tqdm = None
        if whisper_transcribe_mod and hasattr(whisper_transcribe_mod, "tqdm"):
            original_tqdm = whisper_transcribe_mod.tqdm.tqdm
            whisper_transcribe_mod.tqdm.tqdm = _ProgressTqdm

        # Step 4: Run Whisper transcription (TRANS-01: Czech, medium model)
        try:
            result = _model.transcribe(
                temp_wav_path,
                language="cs",
                verbose=False,
            )
        finally:
            # Restore original tqdm to avoid side effects across calls
            if whisper_transcribe_mod and original_tqdm is not None:
                whisper_transcribe_mod.tqdm.tqdm = original_tqdm

        return {"text": result["text"], "vad_stats": vad_stats}

    finally:
        # Cleanup temp file
        if temp_wav is not None:
            import os
            try:
                os.unlink(temp_wav_path)
            except OSError:
                pass

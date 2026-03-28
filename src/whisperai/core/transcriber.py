"""Whisper transcription worker — runs in ProcessPoolExecutor subprocess."""
from pathlib import Path

from src.whisperai.core.vad import preprocess_audio

_model = None  # Module-level; set once per worker by _worker_init
_progress_queue = None  # Module-level; set once per worker by _worker_init


def _worker_init(model_path: str, device: str, progress_queue) -> None:
    """ProcessPoolExecutor initializer. Loads faster-whisper model once per worker process."""
    global _model, _progress_queue
    from faster_whisper import WhisperModel
    _progress_queue = progress_queue
    compute_type = "float16" if device == "cuda" else "int8"
    _model = WhisperModel(
        "medium",
        device=device,
        compute_type=compute_type,
        download_root=model_path,
    )


def transcribe_file(
    audio_path: str,
    task_id: str,
) -> dict:
    """Transcribe one audio file with VAD preprocessing and progress reporting.

    Args:
        audio_path: Path to the audio file.
        task_id: Unique identifier for this file in the queue (used for UI updates).

    Returns:
        dict with keys: "text" (full transcript), "vad_stats" (from preprocess_audio).

    Raises:
        Exception with descriptive message on failure.
    """
    import tempfile
    import wave
    import numpy as np

    # Step 1: VAD preprocessing — strip silence (D-19)
    speech_tensor, vad_stats = preprocess_audio(audio_path)
    _progress_queue.put({
        "type": "vad_done",
        "task_id": task_id,
        "vad_stats": vad_stats,
    })

    if vad_stats["segment_count"] == 0:
        return {"text": "", "vad_stats": vad_stats}

    # Step 2: Write speech-only audio to temp WAV for faster-whisper
    temp_wav = None
    try:
        temp_wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        temp_wav_path = temp_wav.name
        temp_wav.close()

        # Write 16-bit PCM WAV using stdlib wave
        pcm_data = (speech_tensor.numpy() * 32767).astype(np.int16)
        with wave.open(temp_wav_path, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(16000)
            wf.writeframes(pcm_data.tobytes())

        # Step 3: Run faster-whisper transcription (Czech, medium model)
        segments, info = _model.transcribe(
            temp_wav_path,
            language="cs",
            vad_filter=False,  # We already did VAD
        )

        # Collect segments and report progress
        text_parts = []
        total_duration = vad_stats["speech_duration_s"]
        for segment in segments:
            text_parts.append(segment.text)
            _progress_queue.put({
                "type": "progress",
                "task_id": task_id,
                "n": int(segment.end),
                "total": int(total_duration),
            })

        return {"text": " ".join(text_parts).strip(), "vad_stats": vad_stats}

    finally:
        # Cleanup temp file
        if temp_wav is not None:
            import os
            try:
                os.unlink(temp_wav_path)
            except OSError:
                pass

"""Voice Activity Detection preprocessing using silero-vad."""
import subprocess
import numpy as np
import torch

from src.whisperai.utils.resource_path import get_resource_path

_vad_model = None


def _get_vad_model():
    """Load silero-vad model once per process. Cached in module global."""
    global _vad_model
    if _vad_model is None:
        from silero_vad import load_silero_vad
        _vad_model = load_silero_vad()
    return _vad_model


def _read_audio_ffmpeg(audio_path: str, sample_rate: int = 16000) -> torch.Tensor:
    """Read audio file to mono float32 tensor using ffmpeg (no torchaudio needed)."""
    import sys
    ffmpeg_name = "ffmpeg.exe" if sys.platform == "win32" else "ffmpeg"
    ffmpeg_path = get_resource_path(f"bin/{ffmpeg_name}")
    # Fall back to system ffmpeg if bundled one not found
    cmd = str(ffmpeg_path) if ffmpeg_path.exists() else "ffmpeg"
    result = subprocess.run(
        [cmd, "-i", audio_path, "-f", "s16le", "-ac", "1",
         "-ar", str(sample_rate), "-loglevel", "error", "-"],
        capture_output=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"ffmpeg failed: {result.stderr.decode()}")
    pcm = np.frombuffer(result.stdout, dtype=np.int16).astype(np.float32) / 32768.0
    return torch.from_numpy(pcm)


def preprocess_audio(audio_path: str, sample_rate: int = 16000) -> tuple[torch.Tensor, dict]:
    """Strip silence from audio file. Return (speech_tensor, stats_dict).

    stats_dict contains:
      - segment_count: int  (number of speech segments found)
      - speech_duration_s: float  (total speech seconds)
      - total_duration_s: float  (original file duration in seconds)

    If no speech found, returns (empty tensor, stats with segment_count=0).
    """
    from silero_vad import get_speech_timestamps

    wav = _read_audio_ffmpeg(audio_path, sample_rate)
    total_duration_s = len(wav) / sample_rate

    model = _get_vad_model()
    timestamps = get_speech_timestamps(wav, model, return_seconds=False)

    if not timestamps:
        return torch.zeros(0), {
            "segment_count": 0,
            "speech_duration_s": 0.0,
            "total_duration_s": total_duration_s,
        }

    speech_chunks = [wav[ts["start"]:ts["end"]] for ts in timestamps]
    speech_tensor = torch.cat(speech_chunks)
    speech_duration_s = len(speech_tensor) / sample_rate

    return speech_tensor, {
        "segment_count": len(timestamps),
        "speech_duration_s": round(speech_duration_s, 1),
        "total_duration_s": round(total_duration_s, 1),
    }

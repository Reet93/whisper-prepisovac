# Whisper Prepis

Desktop application for transcribing audio recordings to text using OpenAI Whisper, with optional AI-powered text cleanup via the Anthropic Claude API.

Built for Czech audio recordings. Runs locally on Windows without cloud dependency for transcription.

## Features

- **One-click transcription** of audio files (.mp3, .wav, .m4a, .ogg) using Whisper medium model
- **GPU acceleration** — automatically detects and uses NVIDIA CUDA GPU with CPU fallback
- **Batch processing** — load multiple files or entire folders, process in parallel
- **Claude AI cleanup** (optional) — produces edited text with grammar corrections, paragraph structure, executive summary, and diff comparison
- **Bilingual UI** — Czech and English interface
- **Secure API key storage** — uses Windows Credential Manager (never stored in plaintext)
- **Persistent settings** — output folder, language, and worker count saved between sessions

## Requirements

- Windows 10 or 11
- Internet connection for first launch (model download)
- NVIDIA GPU recommended (CUDA-compatible) — CPU works but is slower
- Anthropic API key (optional, for Claude text cleanup features)

## Installation

### For Users (Portable Folder)

1. Download the latest release zip from [Releases](../../releases)
2. Extract the zip to any folder
3. Run `WhisperPrepis.exe`
4. On first launch, the app will download the Whisper model (~1.5 GB). This only happens once.

### For Developers (From Source)

1. Install Python 3.12.x
2. Clone this repository
3. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. Run the app:
   ```bash
   python main.py
   ```

## First Launch

On first launch, the app downloads the Whisper medium model (~1.5 GB). This requires an internet connection and takes 2-15 minutes depending on your connection speed. The model is saved locally and reused for all future launches.

## Usage

1. Click **"Pridat soubory"** (Add Files) or **"Pridat slozku"** (Add Folder) to load audio files
2. Click **"Prepsat"** (Transcribe) for raw transcription, or **"Prepsat + Upravit"** for transcription with Claude AI cleanup
3. Output files are saved next to the source audio:
   - `_prepis.txt` — raw transcription
   - `_upraveno.txt` — cleaned-up version with summary and diff (when using Claude)

## Building

To build the portable folder distribution:

1. Install build dependencies:
   ```bash
   .venv\Scripts\pip install pyinstaller==6.19.0
   ```
2. Download ffmpeg static build from [BtbN/FFmpeg-Builds](https://github.com/BtbN/FFmpeg-Builds/releases) and extract `ffmpeg.exe` and `ffprobe.exe` to `bin/`
3. Run the build script:
   ```bash
   build.bat
   ```
4. Output: `dist\WhisperPrepis\` (portable folder) and `dist\WhisperPrepis-v1.0-windows.zip` (release archive)

## Technology

- **Transcription**: faster-whisper (CTranslate2 backend)
- **GPU**: PyTorch with CUDA support
- **AI Cleanup**: Anthropic Claude API
- **GUI**: Tkinter + ttkbootstrap
- **Packaging**: PyInstaller portable folder

## License

MIT License — see [LICENSE](LICENSE) for details.

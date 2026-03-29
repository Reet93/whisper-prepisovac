# Whisper Prepis

Desktop application for transcribing audio recordings to text using faster-whisper, with optional AI-powered text cleanup via the Anthropic Claude API (experimental, currently disabled).

Built for Czech audio recordings. Runs locally on Windows without cloud dependency for transcription.

## Features

- **One-click transcription** of audio files (.mp3, .wav, .m4a, .ogg) using Whisper medium model
- **GPU acceleration** — automatically detects and uses NVIDIA CUDA GPU with CPU fallback
- **Batch processing** — load multiple files or entire folders, process in parallel
- **Claude AI cleanup** (experimental, disabled) — planned feature for edited text with grammar corrections, paragraph structure, executive summary, and diff comparison
- **Bilingual UI** — Czech and English interface
- **Persistent settings** — output folder, language, and worker count saved between sessions

## Requirements

- Windows 10 or 11
- Python 3.12.x
- Internet connection for first launch (model download)
- NVIDIA GPU recommended (CUDA-compatible) — CPU works but is slower

## Installation

1. Clone this repository
2. Create a virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   python main.py
   ```

## First Launch

On first launch, the app downloads the Whisper medium model (~1.5 GB). This requires an internet connection and takes 2-15 minutes depending on your connection speed. The model is saved locally and reused for all future launches.

## Usage

1. Click **"Pridat soubory"** (Add Files) or **"Pridat slozku"** (Add Folder) to load audio files
2. Click **"Prepsat"** (Transcribe) for raw transcription
3. Output files are saved next to the source audio as `_prepis.txt`

## Claude AI Cleanup (Experimental — Disabled)

The Claude API integration is built but currently disabled as experimental. The UI shows all Claude-related controls (Transcribe + Edit, Edit Only, prompt editor, context profiles) in a disabled state with an "experimental" banner.

**To enable Claude features**, a developer needs to modify these files:

- **`src/whisperai/gui/transcription_panel.py`** — method `_update_claude_button_states()` (line ~501) currently forces all Claude buttons to `state="disabled"`. Change this to check for a valid API key and enable the buttons when one is set.
- **`src/whisperai/gui/transcription_panel.py`** — lines ~222, 247, 252, 257, 261, 279, 333: Claude-related controls (Transcribe+Edit button, profile dropdown, context entry, Edit Only button, prompt toggle) are created with `state="disabled"`. Remove or conditionalize the disabled state.
- **`src/whisperai/gui/settings_dialog.py`** — method `_build_claude_tab()` (line ~154): all Claude tab controls (API key entry, model selector, save button) are created with `state="disabled"`. Enable them and uncomment/restore the API key save logic in `_on_save()` (line ~235).
- **`src/whisperai/gui/main_window.py`** — lines ~71-75: the experimental feature banner. Remove or hide it once Claude is production-ready.

The backend code (`src/whisperai/core/claude_cleaner.py`, `src/whisperai/utils/keyring_helpers.py`, prompt files in `prompts/`) is fully implemented and ready — only the UI controls need to be unblocked.

## Building (Portable Folder)

To build a standalone Windows distribution that runs without Python:

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
- **AI Cleanup**: Anthropic Claude API (experimental)
- **GUI**: Tkinter + ttkbootstrap
- **Packaging**: PyInstaller portable folder

## License

MIT License — see [LICENSE](LICENSE) for details.

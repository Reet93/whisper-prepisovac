# whisperai.spec -- PyInstaller build configuration for Whisper Prepisovac
import sys
sys.setrecursionlimit(5000)  # torch module graph is very deep -- must be before Analysis

from PyInstaller.utils.hooks import collect_all, collect_data_files, copy_metadata

block_cipher = None

# Collect packages needing full collection (submodules + data + binaries)
ctranslate2_datas, ctranslate2_binaries, ctranslate2_hiddenimports = collect_all('ctranslate2')
keyring_datas, keyring_binaries, keyring_hiddenimports = collect_all('keyring')
silero_vad_datas, silero_vad_binaries, silero_vad_hiddenimports = collect_all('silero_vad')
hf_hub_datas, hf_hub_binaries, hf_hub_hiddenimports = collect_all('huggingface_hub')
onnxruntime_datas, onnxruntime_binaries, onnxruntime_hiddenimports = collect_all('onnxruntime')

# Metadata needed by runtime importlib.metadata checks
meta = (
    copy_metadata('torch') +
    copy_metadata('faster-whisper') +
    copy_metadata('ttkbootstrap') +
    copy_metadata('keyring') +
    copy_metadata('platformdirs')
)

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=(
        [('bin/ffmpeg.exe', 'bin'), ('bin/ffprobe.exe', 'bin')]
        + ctranslate2_binaries
        + silero_vad_binaries
        + hf_hub_binaries
        + onnxruntime_binaries
        + keyring_binaries
    ),
    datas=(
        [
            ('locale', 'locale'),
            ('prompts', 'prompts'),
        ]
        + ctranslate2_datas
        + silero_vad_datas
        + hf_hub_datas
        + onnxruntime_datas
        + keyring_datas
        + meta
    ),
    hiddenimports=(
        ['faster_whisper', 'faster_whisper.transcribe', 'faster_whisper.tokenizer',
         'faster_whisper.audio', 'faster_whisper.vad',
         'tokenizers',
         'win32timezone',
         'keyring.backends.Windows',
         'keyring.backends._win_crypto',
         'multiprocessing.managers',
        ]
        + ctranslate2_hiddenimports
        + keyring_hiddenimports
        + silero_vad_hiddenimports
        + hf_hub_hiddenimports
        + onnxruntime_hiddenimports
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['whisper', 'openai.whisper'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='WhisperPrepis',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='WhisperPrepis',
)

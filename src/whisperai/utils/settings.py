"""Persistent settings store and OS-native keyring helpers for Whisper Přepisovač."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import keyring
import keyring.errors
import platformdirs

# ---------------------------------------------------------------------------
# Defaults
# ---------------------------------------------------------------------------

DEFAULTS: dict[str, Any] = {
    "language": "cs",
    "output_folder": "",
    "worker_count": 1,
    "claude_model": "claude-haiku-4-5",
    "claude_prompt": "",          # empty = use bundled default file
    "context_profiles": {},       # name -> text
    "active_profile": "",
}

# ---------------------------------------------------------------------------
# Settings store
# ---------------------------------------------------------------------------


class SettingsStore:
    """JSON-backed persistent settings stored in the OS app-data directory.

    Usage::

        store = SettingsStore()
        lang = store.get("language")
        store.set("language", "en")
        store.save()
    """

    def __init__(
        self,
        app_name: str = "WhisperPrepisovac",
        app_author: str = "WhisperAI",
    ) -> None:
        data_dir = Path(platformdirs.user_data_dir(app_name, app_author))
        data_dir.mkdir(parents=True, exist_ok=True)
        self._path = data_dir / "settings.json"
        self._data: dict[str, Any] = {}
        self._load()

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _load(self) -> None:
        """Read settings from disk, ignoring unknown keys and parse errors."""
        if not self._path.exists():
            return
        try:
            raw = self._path.read_text(encoding="utf-8")
            parsed = json.loads(raw)
            # Merge only keys present in DEFAULTS to avoid unknown-key pollution
            for key in DEFAULTS:
                if key in parsed:
                    self._data[key] = parsed[key]
        except Exception:
            # Silently use defaults on any error (corrupt JSON, permission, etc.)
            self._data = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get(self, key: str) -> Any:
        """Return the stored value for *key*, falling back to DEFAULTS."""
        if key in self._data:
            return self._data[key]
        return DEFAULTS.get(key)

    def set(self, key: str, value: Any) -> None:
        """Set *key* to *value* in memory. Call :meth:`save` to persist."""
        self._data[key] = value

    def save(self) -> None:
        """Write current settings to disk as UTF-8 JSON."""
        self._path.write_text(
            json.dumps(self._data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def reset(self, keys: list[str] | None = None) -> None:
        """Reset settings to defaults.

        If *keys* is None, reset all keys to their defaults.
        If *keys* is provided, reset only those keys.
        The API key is never touched (it is keyring-managed).
        """
        if keys is None:
            self._data = {}
        else:
            for key in keys:
                self._data.pop(key, None)


# ---------------------------------------------------------------------------
# Keyring helpers
# ---------------------------------------------------------------------------

KEYRING_SERVICE = "WhisperPrepisovac"
KEYRING_USERNAME = "anthropic_api_key"


def get_api_key() -> str | None:
    """Return the stored Anthropic API key, or None if not set."""
    return keyring.get_password(KEYRING_SERVICE, KEYRING_USERNAME)


def set_api_key(key: str) -> None:
    """Store *key* in the OS-native credential store."""
    keyring.set_password(KEYRING_SERVICE, KEYRING_USERNAME, key)


def delete_api_key() -> None:
    """Remove the API key from the credential store. No-op if not set."""
    try:
        keyring.delete_password(KEYRING_SERVICE, KEYRING_USERNAME)
    except keyring.errors.PasswordDeleteError:
        pass


# ---------------------------------------------------------------------------
# Default prompt loader
# ---------------------------------------------------------------------------


def get_default_prompt(lang: str) -> str:
    """Return the bundled default Claude prompt for *lang* ('cs' or 'en').

    Falls back to Czech if the requested language file is not found.
    """
    from src.whisperai.utils.resource_path import get_resource_path

    prompt_path = get_resource_path(f"prompts/transcript-processor-prompt-{lang}.md")
    try:
        return prompt_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        # Fallback to Czech
        fallback = get_resource_path("prompts/transcript-processor-prompt-cs.md")
        return fallback.read_text(encoding="utf-8")

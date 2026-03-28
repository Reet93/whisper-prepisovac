import gettext
import locale
import sys
from .resource_path import get_resource_path

_LOCALE_MAP = {"cs": "cs_CZ", "en": "en_US"}


def detect_system_language() -> str:
    """Return 'cs' if OS UI language starts with 'cs', else 'en'.

    Uses locale.getlocale() (Python 3.11+ safe; getdefaultlocale is deprecated).
    On Windows, falls back to ctypes kernel32 API if locale is unset.
    """
    try:
        locale.setlocale(locale.LC_ALL, "")
        lang_code, _ = locale.getlocale()
        if lang_code and lang_code.lower().startswith("cs"):
            return "cs"
    except locale.Error:
        pass

    if sys.platform == "win32":
        try:
            import ctypes
            lang_id = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            locale_name = locale.windows_locale.get(lang_id, "")
            if locale_name.lower().startswith("cs"):
                return "cs"
        except Exception:
            pass

    return "en"


def set_language(lang_code: str) -> None:
    """Install _() into builtins for the selected language.

    lang_code: 'cs' or 'en'. Falls back to NullTranslations if .mo file not found.
    Must be called before any widget code runs.
    """
    locale_dir = get_resource_path("locale")
    gettext.translation(
        "messages",
        localedir=str(locale_dir),
        languages=[_LOCALE_MAP.get(lang_code, "cs_CZ")],
        fallback=True,
    ).install()

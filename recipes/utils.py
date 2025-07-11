from typing import Optional

try:
    from google.cloud import translate_v2 as translate
except Exception:  # pragma: no cover - library might not be installed in tests
    translate = None

_TRANSLATE_CLIENT = None


def translate_text(text: str, target: str) -> Optional[str]:
    """Translate text to the given target language using Google Cloud."""
    global _TRANSLATE_CLIENT
    if not text:
        return None
    if translate is None:
        return None
    if _TRANSLATE_CLIENT is None:
        _TRANSLATE_CLIENT = translate.Client()
    result = _TRANSLATE_CLIENT.translate(text, target_language=target)
    return result.get("translatedText")

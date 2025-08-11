"""Utility helpers for language handling and translation."""

import os
from typing import Optional

import requests


SUPPORTED_LANGUAGES = ["en", "uz", "ru"]


def get_requested_lang(request) -> str:
    """Return a supported language code from request query params."""
    if not request:
        return "en"
    lang = request.query_params.get("lang", "en")
    return lang if lang in SUPPORTED_LANGUAGES else "en"


def translate_text(text: Optional[str], target_lang: str) -> str:
    """Translate ``text`` from English to ``target_lang`` using Yandex.

    If the Yandex API key is not configured or the request fails, the
    original ``text`` is returned unchanged. This keeps the application
    functional even without external translation capabilities.
    """

    if not text or target_lang not in {"ru", "uz"}:
        return text or ""

    api_key = os.getenv("YANDEX_API_KEY")
    if not api_key:
        return text

    try:
        url = "https://translate.yandex.net/api/v1.5/tr.json/translate"
        params = {
            "key": api_key,
            "text": text,
            "lang": f"en-{target_lang}",
        }
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        translated = " ".join(data.get("text", []))
        return translated or text
    except Exception:
        return text


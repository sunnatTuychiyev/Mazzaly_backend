"""Utility helpers for language handling and translation."""

from typing import Optional

import requests
from decouple import config


SUPPORTED_LANGUAGES = ["en", "uz", "ru"]


def get_requested_lang(request) -> str:
    """Return a supported language code from request query params."""
    if not request:
        return "en"
    lang = request.query_params.get("lang", "en")
    return lang if lang in SUPPORTED_LANGUAGES else "en"


def translate_text(text: Optional[str], target_lang: str) -> str:
    """Translate ``text`` into ``target_lang`` using Yandex Cloud.

    If the Yandex API credentials are missing or a request fails, the
    original ``text`` is returned unchanged so normal application
    behaviour continues even without external translation services.
    """

    if not text or target_lang not in {"ru", "uz"}:
        return text or ""

    api_key = config("YANDEX_API_KEY", default="")
    folder_id = config("YANDEX_FOLDER_ID", default="")
    if not api_key or not folder_id:
        return text

    try:
        url = "https://translate.api.cloud.yandex.net/translate/v2/translate"
        headers = {"Authorization": f"Api-Key {api_key}"}
        payload = {
            "targetLanguageCode": target_lang,
            "texts": [text],
            "folderId": folder_id,
        }
        response = requests.post(url, json=payload, timeout=10, headers=headers)
        response.raise_for_status()
        data = response.json()
        translations = data.get("translations", [])
        return translations[0].get("text", text) if translations else text
    except Exception:
        return text


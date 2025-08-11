"""Utilities for translating text using Yandex Cloud Translate API."""

from __future__ import annotations

import logging
import os
import time
from typing import List

import requests

logger = logging.getLogger("recipes")

API_KEY = os.getenv("YANDEX_TRANSLATE_API_KEY", "")
ENDPOINT = os.getenv(
    "YANDEX_TRANSLATE_ENDPOINT",
    "https://translate.api.cloud.yandex.net/translate/v2/translate",
)
FOLDER_ID = os.getenv("YANDEX_FOLDER_ID", "")

# Common culinary terms for fallback if API fails
FALLBACK_DICT = {
    "cornstarch": {"uz": "makkajo'xor kraxmali", "ru": "кукурузный крахмал"},
    "buttermilk": {"uz": "qaymoqli sut", "ru": "пахта"},
}


def _post(payload: dict) -> requests.Response:
    """Send POST request to Yandex API with authentication headers."""
    headers = {"Content-Type": "application/json"}
    if API_KEY:
        headers["Authorization"] = f"Api-Key {API_KEY}"
    if FOLDER_ID:
        payload.setdefault("folderId", FOLDER_ID)
    return requests.post(ENDPOINT, headers=headers, json=payload, timeout=10)


def translate_text(text: str, target_lang: str) -> str:
    """Translate a single string to *target_lang* using Yandex API."""
    if not text:
        return ""
    lower = text.lower()
    if lower in FALLBACK_DICT and target_lang in FALLBACK_DICT[lower]:
        return FALLBACK_DICT[lower][target_lang]
    payload = {
        "texts": [text],
        "targetLanguageCode": target_lang,
        "sourceLanguageCode": "en",
    }
    for attempt, delay in enumerate([0.5, 1, 2], start=1):
        try:
            resp = _post(payload)
            resp.raise_for_status()
            data = resp.json()
            return data["translations"][0]["text"]
        except Exception as exc:  # pragma: no cover - network errors
            logger.warning("Yandex translate failed (attempt %s): %s", attempt, exc)
            if attempt == 3:
                logger.error("Translation failed for '%s'", text)
                break
            time.sleep(delay)
    return ""


def translate_list(texts: List[str], target_lang: str) -> List[str]:
    """Translate a list of strings to *target_lang* using batching."""
    if not texts:
        return []
    payload = {
        "texts": texts,
        "targetLanguageCode": target_lang,
        "sourceLanguageCode": "en",
    }
    try:
        for attempt, delay in enumerate([0.5, 1, 2], start=1):
            try:
                resp = _post(payload)
                resp.raise_for_status()
                data = resp.json()
                translations = [t.get("text", "") for t in data.get("translations", [])]
                if len(translations) == len(texts):
                    return translations
            except Exception as exc:  # pragma: no cover - network errors
                logger.warning(
                    "Yandex batch translate failed (attempt %s): %s", attempt, exc
                )
                if attempt == 3:
                    logger.error("Batch translation failed: %s", texts)
                    break
                time.sleep(delay)
    except Exception:
        pass
    return [translate_text(t, target_lang) for t in texts]

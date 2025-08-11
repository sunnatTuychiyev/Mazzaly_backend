"""Yandex Cloud Translate API helpers with robust placeholders and culinary fixes."""

from __future__ import annotations

import logging
import re
import time
from typing import Dict, List, Tuple

import requests
from django.conf import settings

logger = logging.getLogger("recipes")

# ---------- Culinary glossary (EN -> {uz, ru}) ----------
GLOSSARY: Dict[str, Dict[str, str]] = {
    "baking soda": {"uz": "soda (quritmali)", "ru": "пищевая сода"},
    "bicarbonate of soda": {"uz": "soda (quritmali)", "ru": "пищевая сода"},
    "baking powder": {"uz": "xamir ko‘pirtirgich", "ru": "разрыхлитель теста"},
    "caster sugar": {"uz": "mayin shakar", "ru": "мелкий сахар"},
    "powdered sugar": {"uz": "pudra shakari", "ru": "сахарная пудра"},
    "confectioners sugar": {"uz": "pudra shakari", "ru": "сахарная пудра"},
    "icing sugar": {"uz": "pudra shakari", "ru": "сахарная пудра"},
    "cornstarch": {"uz": "makkajo‘xori kraxmali", "ru": "кукурузный крахмал"},
    "buttermilk": {"uz": "paxta (buttermilk)", "ru": "пахта"},
    "cilantro": {"uz": "kinza", "ru": "кинза"},
    "spring onion": {"uz": "yashil piyoz", "ru": "зелёный лук"},
    "scallion": {"uz": "yashil piyoz", "ru": "зелёный лук"},
    "ground beef": {"uz": "mol go‘shti qiymasi", "ru": "говяжий фарш"},
    "stock": {"uz": "bulyon", "ru": "бульон"},
    "broth": {"uz": "bulyon", "ru": "бульон"},
    "simmer": {"uz": "past olovda qaynating", "ru": "томите на слабом огне"},
    "broil": {"uz": "grilda qovuring (broyl)", "ru": "запекайте под грилем"},
    "teaspoon": {"uz": "choy qoshiq", "ru": "ч. л."},
    "tablespoon": {"uz": "ovqat qoshiq", "ru": "ст. л."},
    "cup": {"uz": "stakan", "ru": "стакан"},
    "ounce": {"uz": "unsiya", "ru": "унц."},
    "pound": {"uz": "funt", "ru": "фунт"},
}

# Units/quantities (NAMEd groups for safe parsing)
UNIT_CANON = r"(?P<unit>tsp|teaspoon(?:s)?|tbsp|tablespoon(?:s)?|cup(?:s)?|g|kg|mg|ml|l|oz|lb|°c|°f|cm|mm)"
NUM_TOKEN = r"(?P<num>\d+(?:[.,]\d+)?|\d+\s+\d\/\d|\d\/\d|¼|½|¾|⅓|⅔)"
QTYUNIT_RE = re.compile(rf"\b{NUM_TOKEN}\s*{UNIT_CANON}\b", re.I)

# Uzbek Cyrillic -> Latin (minimal practical map)
CYR_RE = re.compile(r"[А-Яа-яЁёЎўҚқҒғҲҳ]")
UZ_CYR_TO_LAT = {
    "А": "A", "а": "a", "Б": "B", "б": "b", "В": "V", "в": "v",
    "Г": "G", "г": "g", "Д": "D", "д": "d", "Е": "E", "е": "e",
    "Ё": "Yo", "ё": "yo", "Ж": "J", "ж": "j", "З": "Z", "з": "z",
    "И": "I", "и": "i", "Й": "Y", "й": "y", "К": "K", "к": "k",
    "Л": "L", "л": "l", "М": "M", "м": "m", "Н": "N", "н": "n",
    "О": "O", "о": "o", "П": "P", "п": "p", "Р": "R", "р": "r",
    "С": "S", "с": "s", "Т": "T", "т": "t", "У": "U", "у": "u",
    "Ф": "F", "ф": "f", "Х": "X", "х": "x", "Ҳ": "H", "ҳ": "h",
    "Ц": "Ts", "ц": "ts", "Ч": "Ch", "ч": "ch", "Ш": "Sh", "ш": "sh",
    "Щ": "Sh", "щ": "sh", "Ъ": "ʼ", "ъ": "ʼ", "Ь": "ʼ", "ь": "ʼ",
    "Ю": "Yu", "ю": "yu", "Я": "Ya", "я": "ya", "Қ": "Q", "қ": "q",
    "Ғ": "Gʻ", "ғ": "gʻ", "Ў": "Oʻ", "ў": "oʻ",
}


def _cyr_to_lat(s: str) -> str:
    """Convert Uzbek Cyrillic letters in *s* to Latin equivalents."""
    return "".join(UZ_CYR_TO_LAT.get(ch, ch) for ch in s)


# Robust placeholder template & regex (case-insensitive, supports Cyrillic lookalikes)
PH_FMT = "{YXT%d}"
PH_RE = re.compile(r"\{\s*[YУyу]\s*[XХxх]\s*[TТtт]\s*(\d+)\s*\}", re.I)

_CACHE: Dict[Tuple[str, str], str] = {}


def _target_codes(lang: str) -> List[str]:
    """Return Yandex target codes for *lang* (maps 'uz' to 'uz')."""
    return ["uz"] if lang == "uz" else [lang]


def _norm_unit(u: str) -> str:
    u = u.lower()
    if u.startswith("teaspoon"):
        return "tsp"
    if u.startswith("tablespoon"):
        return "tbsp"
    if u.startswith("cup"):
        return "cup"
    return u


def _localize_qty(num: str, unit: str, lang: str) -> str:
    u = _norm_unit(unit)
    if lang == "ru":
        mapping = {
            "tsp": "ч. л.",
            "tbsp": "ст. л.",
            "cup": "стакана",
            "g": "г",
            "kg": "кг",
            "mg": "мг",
            "ml": "мл",
            "l": "л",
            "oz": "унц.",
            "lb": "фунт",
            "°c": "°C",
            "°f": "°F",
            "cm": "см",
            "mm": "мм",
        }
    else:
        mapping = {
            "tsp": "choy qoshiq",
            "tbsp": "ovqat qoshiq",
            "cup": "stakan",
            "g": "g",
            "kg": "kg",
            "mg": "mg",
            "ml": "ml",
            "l": "l",
            "oz": "unsiya",
            "lb": "funt",
            "°c": "°C",
            "°f": "°F",
            "cm": "sm",
            "mm": "mm",
        }
    return f"{num} {mapping.get(u, unit)}"


def _apply_placeholders(text: str) -> Tuple[str, Dict[int, Tuple[str, str, str]]]:
    """Mask quantities and glossary phrases, returning masked text and mapping."""
    mapping: Dict[int, Tuple[str, str, str]] = {}
    n = 0
    out = text

    def put_qty(num: str, unit: str) -> str:
        nonlocal n
        key = PH_FMT % n
        mapping[n] = ("qty", num, unit)
        n += 1
        return key

    def put_gloss(original: str) -> str:
        nonlocal n
        key = PH_FMT % n
        mapping[n] = ("gloss", original, "")
        n += 1
        return key

    def repl_qty(m: re.Match) -> str:
        num = m.group("num")
        unit = m.group("unit")
        return put_qty(num, unit)

    out = QTYUNIT_RE.sub(repl_qty, out)

    for phrase in sorted(GLOSSARY.keys(), key=len, reverse=True):
        pattern = re.compile(re.escape(phrase), re.I)
        out = pattern.sub(lambda m, p=phrase: put_gloss(m.group(0)), out)

    return out, mapping


def _restore_placeholders(translated: str, mapping: Dict[int, Tuple[str, str, str]], lang: str) -> str:
    """Restore placeholders in *translated* string using *mapping* for *lang*."""

    def repl(m: re.Match) -> str:
        idx = int(m.group(1))
        kind, a, b = mapping.get(idx, ("", "", ""))
        if kind == "qty":
            return _localize_qty(a, b, lang)
        if kind == "gloss":
            original = a
            low = original.lower()
            if low in GLOSSARY and lang in GLOSSARY[low]:
                return GLOSSARY[low][lang]
            return original
        return m.group(0)

    out = PH_RE.sub(repl, translated)
    return re.sub(r"\s+", " ", out).strip()


def _request_yandex(texts: List[str], target_lang: str) -> List[str]:
    """Call Yandex Translate API for *texts* and return translated strings."""

    endpoint = getattr(
        settings,
        "YANDEX_TRANSLATE_ENDPOINT",
        "https://translate.api.cloud.yandex.net/translate/v2/translate",
    )
    api_key = getattr(settings, "YANDEX_TRANSLATE_API_KEY", "")
    iam_token = getattr(settings, "YANDEX_IAM_TOKEN", "")
    folder_id = getattr(settings, "YANDEX_FOLDER_ID", "")

    if not api_key and not iam_token:
        raise RuntimeError("Yandex credentials missing")

    headers = {"Content-Type": "application/json"}
    if iam_token:
        headers["Authorization"] = f"Bearer {iam_token}"
    else:
        headers["Authorization"] = f"Api-Key {api_key}"

    base = {"texts": texts, "sourceLanguageCode": "en"}

    for code in _target_codes(target_lang):
        body = dict(base)
        body["targetLanguageCode"] = code
        if folder_id:
            body["folderId"] = folder_id

        for i, wait in enumerate([0, 0.5, 1, 2], 1):
            if wait:
                time.sleep(wait)
            try:
                resp = requests.post(endpoint, headers=headers, json=body, timeout=15)
            except requests.RequestException as exc:
                logger.warning(
                    "Yandex network error (try %s, code %s): %s", i, code, exc
                )
                continue

            if resp.status_code == 200:
                try:
                    data = resp.json()
                except ValueError as exc:  # pragma: no cover - bad JSON
                    logger.error("Yandex bad JSON: %s", exc)
                    return [""] * len(texts)
                return [t.get("text", "") for t in data.get("translations", [])]

            msg = resp.text[:200]
            logger.warning(
                "Yandex HTTP %s (try %s, code %s): %s", resp.status_code, i, code, msg
            )
            if resp.status_code == 400 and (
                "unsupported target_language_code" in msg or "folder ID" in msg
            ):
                break

    return [""] * len(texts)


def translate_text(text: str, target_lang: str) -> str:
    """Translate *text* into *target_lang* using Yandex Translate."""
    if not text:
        return ""

    cache_key = (text, target_lang)
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    masked, mapping = _apply_placeholders(text)
    out_list = _request_yandex([masked], target_lang)
    translated = out_list[0] if out_list else ""

    translated = _restore_placeholders(translated or text, mapping, target_lang)
    if target_lang == "uz" and CYR_RE.search(translated):
        translated = _cyr_to_lat(translated)

    _CACHE[cache_key] = translated
    return translated


def translate_list(texts: List[str], target_lang: str) -> List[str]:
    """Translate *texts* list into *target_lang* with batching and caching."""
    if not texts:
        return []

    results: List[str] = ["" for _ in texts]
    masked_list: List[str] = []
    maps: List[Dict[int, Tuple[str, str, str]]] = []
    idxs: List[int] = []

    for i, t in enumerate(texts):
        if not t:
            continue
        ck = (t, target_lang)
        if ck in _CACHE:
            results[i] = _CACHE[ck]
            continue
        masked, mp = _apply_placeholders(t)
        masked_list.append(masked)
        maps.append(mp)
        idxs.append(i)

    if masked_list:
        translations = _request_yandex(masked_list, target_lang)
        if not any(translations):
            translations = []
            for m in masked_list:
                translations.extend(_request_yandex([m], target_lang))

        for j, idx in enumerate(idxs):
            restored = _restore_placeholders(translations[j] or texts[idx], maps[j], target_lang)
            if target_lang == "uz" and CYR_RE.search(restored):
                restored = _cyr_to_lat(restored)
            results[idx] = restored
            _CACHE[(texts[idx], target_lang)] = restored

    return results


__all__ = ["translate_text", "translate_list"]


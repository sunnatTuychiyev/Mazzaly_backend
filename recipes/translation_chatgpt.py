"""ChatGPT translation helpers with placeholders and culinary fixes."""

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


def _chatgpt_translate(text: str, target_lang: str) -> str:
    """Translate *text* to *target_lang* using OpenAI ChatGPT."""

    endpoint = getattr(
        settings,
        "OPENAI_TRANSLATE_ENDPOINT",
        "https://api.openai.com/v1/chat/completions",
    )
    api_key = getattr(settings, "OPENAI_API_KEY", "")
    model = getattr(settings, "OPENAI_TRANSLATE_MODEL", "gpt-4o-mini")

    if not api_key:
        logger.warning("OpenAI API key missing")
        return ""

    headers = {
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": f"Translate the user's text from English to {target_lang} and return only the translation.",
            },
            {"role": "user", "content": text},
        ],
        "temperature": 0,
    }

    for i, wait in enumerate([0, 0.5, 1, 2], 1):
        if wait:
            time.sleep(wait)
        try:
            resp = requests.post(endpoint, headers=headers, json=payload, timeout=15)
        except requests.RequestException as exc:
            logger.warning("ChatGPT network error (try %s): %s", i, exc)
            continue
        if resp.status_code == 200:
            try:
                data = resp.json()
                return data["choices"][0]["message"]["content"].strip()
            except Exception as exc:  # pragma: no cover - bad JSON
                logger.error("ChatGPT bad JSON: %s", exc)
                return ""
        logger.warning(
            "ChatGPT HTTP %s (try %s): %s", resp.status_code, i, resp.text[:200]
        )
    return ""


def translate_text(text: str, target_lang: str) -> str:
    """Translate *text* into *target_lang* using ChatGPT."""
    if not text:
        return ""

    cache_key = (text, target_lang)
    if cache_key in _CACHE:
        return _CACHE[cache_key]

    masked, mapping = _apply_placeholders(text)
    translated = _chatgpt_translate(masked, target_lang) or ""

    translated = _restore_placeholders(translated or text, mapping, target_lang)
    if target_lang == "uz" and CYR_RE.search(translated):
        translated = _cyr_to_lat(translated)

    _CACHE[cache_key] = translated
    return translated


def translate_list(texts: List[str], target_lang: str) -> List[str]:
    """Translate a list of *texts* into *target_lang* sequentially with caching."""
    return [translate_text(t, target_lang) for t in texts]


__all__ = ["translate_text", "translate_list"]


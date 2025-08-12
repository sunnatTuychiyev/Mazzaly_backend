import re
from typing import Any, List


def clean_text(text: str) -> str:
    """Trim and collapse consecutive whitespace in *text*."""
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def ensure_list(obj: Any) -> List[str]:
    """Return *obj* as list of cleaned strings."""
    if obj is None:
        return []
    if isinstance(obj, list):
        return [clean_text(item) for item in obj if clean_text(item)]
    return [clean_text(obj)]

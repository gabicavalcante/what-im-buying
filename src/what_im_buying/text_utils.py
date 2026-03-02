from __future__ import annotations

import re
import unicodedata


def normalize_product_name(name: str) -> str:
    value = name.strip().lower()
    value = "".join(
        c for c in unicodedata.normalize("NFD", value) if unicodedata.category(c) != "Mn"
    )
    value = re.sub(r"[^a-z0-9\s]", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    return value


def parse_brl_number(text: str) -> float | None:
    value = text.strip()
    if not value:
        return None
    value = value.replace("R$", "").replace(".", "").replace(",", ".").strip()
    try:
        return float(value)
    except ValueError:
        return None


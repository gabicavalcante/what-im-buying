from __future__ import annotations

import json
import os
from typing import Any

from .categories import CATEGORY_LABELS_PTBR
from .models import CategorizationEnrichment, NormalizationEnrichment

CANONICAL_UNITS = {
    "KG",
    "UN",
    "LT",
    "CX",
    "PC",
    "FR",
    "BJ",
    "TP",
    "BR",
    "CP",
    "GF",
    "PT",
    "SH",
    "CJ",
    "VD",
}
UNIT_FULL_NAMES = {
    "KG": "QUILOGRAMA",
    "UN": "UNIDADE",
    "LT": "LITRO",
    "CX": "CAIXA",
    "PC": "PACOTE",
    "FR": "FRASCO",
    "BJ": "BANDEJA",
    "TP": "TETRA PAK",
    "BR": "BARRA",
    "CP": "COPO",
    "GF": "GARRAFA",
    "PT": "POTE",
    "SH": "SACHE",
    "CJ": "CONJUNTO",
    "VD": "VIDRO",
}
UNIT_ALIASES = {
    "UNIT": "UN",
    "UNITS": "UN",
    "UNIDADE": "UN",
    "UNIDADES": "UN",
    "UND": "UN",
    "PCS": "PC",
    "EA": "UN",
    "LITRO": "LT",
    "LITROS": "LT",
}


def build_normalization_prompt(items: list[dict[str, Any]]) -> str:
    return (
        "You normalize grocery receipt item names from Brazilian NFC-e.\n"
        "Return valid JSON only, with this schema:\n"
        '{\n'
        '  "items": [\n'
        "    {\n"
        '      "item_id": integer,\n'
        '      "raw_name": string,\n'
        '      "canonical_name": string,\n'
        '      "brand": string or null,\n'
        '      "unit_type": string or null,\n'
        '      "unit_type_full": string or null,\n'
        '      "confidence": number,\n'
        '      "needs_review": boolean\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Rules:\n"
        "- Do not invent unknown data.\n"
        "- Keep canonical_name short and stable.\n"
        f"- unit_type must be one of: {sorted(CANONICAL_UNITS)}.\n"
        "- unit_type_full must match the full name of unit_type.\n"
        "- confidence must be between 0 and 1.\n"
        "- item_id must match input.\n\n"
        f"Input items: {json.dumps(items, ensure_ascii=True)}\n"
    )


def generate_normalized_items(items: list[dict[str, Any]]) -> list[NormalizationEnrichment]:
    prompt = build_normalization_prompt(items)
    output_text = _generate_text(prompt)
    payload = _extract_json_object(output_text)
    normalized_raw = payload.get("items")
    
    if not isinstance(normalized_raw, list):
        raise RuntimeError("Invalid normalization response: missing items array")
    
    normalized: list[NormalizationEnrichment] = []
    for row in normalized_raw:
        if not isinstance(row, dict):
            continue
        normalized.append(_normalization_from_dict(row))
    
    return normalized


def build_categorization_prompt(items: list[dict[str, Any]]) -> str:
    valid_keys = sorted(CATEGORY_LABELS_PTBR.keys())
    return (
        "You categorize Brazilian grocery invoice items.\n"
        "Return valid JSON only, with this schema:\n"
        '{\n'
        '  "items": [\n'
        "    {\n"
        '      "item_id": integer,\n'
        '      "raw_name": string,\n'
        '      "normalized_name": string,\n'
        '      "category_key": string,\n'
        '      "confidence": number,\n'
        '      "needs_review": boolean,\n'
        '      "reason": string\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Rules:\n"
        f"- category_key must be one of: {valid_keys}\n"
        "- confidence must be between 0 and 1.\n"
        "- item_id must match input.\n"
        "- If uncertain, use category_key='other' and needs_review=true.\n\n"
        f"Input items: {json.dumps(items, ensure_ascii=True)}\n"
    )


def generate_categorized_items(items: list[dict[str, Any]]) -> list[CategorizationEnrichment]:
    prompt = build_categorization_prompt(items)
    output_text = _generate_text(prompt)
    payload = _extract_json_object(output_text)
    
    categorized_raw = payload.get("items")
    
    if not isinstance(categorized_raw, list):
        raise RuntimeError("Invalid categorization response: missing items array")
    
    categorized: list[CategorizationEnrichment] = []
    for row in categorized_raw:
        if not isinstance(row, dict):
            continue
        categorized.append(_categorization_from_dict(row))
        
    return categorized


def _generate_text(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install openai package to enable AI commands") from exc

    client = OpenAI(api_key=api_key)
    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
    )
    return response.output_text


def _extract_json_object(text: str) -> dict[str, Any]:
    raw = text.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json"):
            raw = raw[4:].strip()
    try:
        payload = json.loads(raw)
        
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise RuntimeError("Model did not return valid JSON")
        payload = json.loads(raw[start : end + 1])
        
    if not isinstance(payload, dict):
        raise RuntimeError("Expected JSON object")
    return payload


def _normalization_from_dict(data: dict[str, Any]) -> NormalizationEnrichment:
    unit_type = _canonicalize_unit(data.get("unit_type"))
    unit_type_full = UNIT_FULL_NAMES.get(unit_type) if unit_type else None
    needs_review = bool(data.get("needs_review", False))

    if data.get("unit_type") not in (None, "") and unit_type is None:
        needs_review = True

    return NormalizationEnrichment(
        item_id=int(data["item_id"]),
        raw_name=str(data.get("raw_name", "")),
        canonical_name=str(data.get("canonical_name", "")),
        brand=str(data["brand"]) if data.get("brand") not in (None, "") else None,
        unit_type=unit_type,
        confidence=float(data.get("confidence", 0.0)),
        needs_review=needs_review,
        unit_type_full=unit_type_full,
    )


def _categorization_from_dict(data: dict[str, Any]) -> CategorizationEnrichment:
    category_key = str(data.get("category_key", "other")).strip().lower() or "other"
    if category_key not in CATEGORY_LABELS_PTBR:
        category_key = "other"
        
    needs_review = bool(data.get("needs_review", False))
    if category_key == "other":
        needs_review = True
        
    return CategorizationEnrichment(
        item_id=int(data["item_id"]),
        raw_name=str(data.get("raw_name", "")),
        normalized_name=str(data.get("normalized_name", "")),
        category_key=category_key,
        confidence=float(data.get("confidence", 0.0)),
        needs_review=needs_review,
        reason=str(data.get("reason", "")),
    )


def _canonicalize_unit(value: Any) -> str | None:
    if value in (None, ""):
        return None
    unit = str(value).strip().upper()
    unit = UNIT_ALIASES.get(unit, unit)
    if unit in CANONICAL_UNITS:
        return unit
    return None

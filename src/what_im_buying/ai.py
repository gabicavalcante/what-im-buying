from __future__ import annotations

import json
import os
from typing import Any

from .models import NormalizationEnrichment


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
        '      "size_value": number or null,\n'
        '      "size_unit": string or null,\n'
        '      "pack_count": integer or null,\n'
        '      "unit_type": string or null,\n'
        '      "confidence": number,\n'
        '      "needs_review": boolean\n'
        "    }\n"
        "  ]\n"
        "}\n"
        "Rules:\n"
        "- Do not invent unknown data.\n"
        "- Keep canonical_name short and stable.\n"
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


def _generate_text(prompt: str) -> str:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("Install openai package to enable AI normalization") from exc

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
    return NormalizationEnrichment(
        item_id=int(data["item_id"]),
        raw_name=str(data.get("raw_name", "")),
        canonical_name=str(data.get("canonical_name", "")),
        brand=str(data["brand"]) if data.get("brand") not in (None, "") else None,
        size_value=float(data["size_value"]) if data.get("size_value") not in (None, "") else None,
        size_unit=str(data["size_unit"]) if data.get("size_unit") not in (None, "") else None,
        pack_count=int(data["pack_count"]) if data.get("pack_count") not in (None, "") else None,
        unit_type=str(data["unit_type"]) if data.get("unit_type") not in (None, "") else None,
        confidence=float(data.get("confidence", 0.0)),
        needs_review=bool(data.get("needs_review", False)),
    )

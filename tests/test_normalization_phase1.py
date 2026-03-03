from __future__ import annotations

import sqlite3

from src.what_im_buying.ai import _extract_json_object, _normalization_from_dict
from src.what_im_buying.models import NormalizationEnrichment
from src.what_im_buying.storage import init_db, save_item_enrichments


def test_extract_json_object_from_code_fence() -> None:
    text = """```json
{"items":[{"item_id":1,"raw_name":"LEITE","canonical_name":"leite integral"}]}
```"""
    payload = _extract_json_object(text)
    assert payload["items"][0]["item_id"] == 1


def test_save_item_enrichments_accepts_numeric_item_id_string() -> None:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    conn.execute(
        """
        INSERT INTO invoices (url, issued_at, total_amount, raw_html_hash)
        VALUES ('local://a', NULL, NULL, 'hash-a')
        """
    )
    conn.execute(
        """
        INSERT INTO items (invoice_id, raw_name, normalized_name, quantity, unit_price, total_price)
        VALUES (1, 'LEITE', 'leite', 1, 4.5, 4.5)
        """
    )
    conn.commit()

    saved = save_item_enrichments(
        conn,
        stage="normalize",
        enrichments=[
            NormalizationEnrichment(
                item_id=1,
                raw_name="LEITE",
                canonical_name="leite integral",
                brand=None,
                unit_type="UN",
                confidence=0.8,
                needs_review=False,
            )
        ],
    )
    assert saved == 1
    row = conn.execute("SELECT stage, output_json FROM item_enrichment LIMIT 1").fetchone()
    assert row["stage"] == "normalize"
    assert "leite integral" in row["output_json"]


def test_normalization_unit_coercion() -> None:
    enrichment = _normalization_from_dict(
        {
            "item_id": 10,
            "raw_name": "SABONETE",
            "canonical_name": "sabonete",
            "brand": None,
            "unit_type": "units",
            "confidence": 0.7,
            "needs_review": False,
        }
    )
    assert enrichment.unit_type == "UN"


def test_normalization_marks_review_when_unit_is_invalid() -> None:
    enrichment = _normalization_from_dict(
        {
            "item_id": 11,
            "raw_name": "PRODUTO TESTE",
            "canonical_name": "produto teste",
            "brand": None,
            "unit_type": "unknown_unit",
            "confidence": 0.8,
            "needs_review": False,
        }
    )
    assert enrichment.unit_type is None
    assert enrichment.needs_review is True

from __future__ import annotations

import sqlite3

from src.what_im_buying.ai import _extract_json_object
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
                size_value=1.0,
                size_unit="L",
                pack_count=1,
                unit_type="un",
                confidence=0.8,
                needs_review=False,
            )
        ],
    )
    assert saved == 1
    row = conn.execute("SELECT stage, output_json FROM item_enrichment LIMIT 1").fetchone()
    assert row["stage"] == "normalize"
    assert "leite integral" in row["output_json"]

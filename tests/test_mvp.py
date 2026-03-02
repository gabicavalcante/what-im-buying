from __future__ import annotations

import sqlite3
from pathlib import Path

from src.what_im_buying.parser import parse_invoice
from src.what_im_buying.storage import init_db, save_invoice


def test_parse_invoice_and_storage() -> None:
    html_path = Path("tests/fixtures/sample_sp_nfce.html")
    html = html_path.read_text(encoding="utf-8")
    invoice, items = parse_invoice(html, "local://sample-1")
    assert len(items) == 2
    assert invoice.total_amount == 32.9

    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)

    invoice_id = save_invoice(conn, invoice, items)
    assert invoice_id == 1
    saved_items = conn.execute("SELECT COUNT(*) AS c FROM items WHERE invoice_id = 1").fetchone()
    assert saved_items["c"] == 2


def test_parse_sp_tabresult_layout() -> None:
    html_path = Path("tests/fixtures/sample_sp_tabresult.html")
    html = html_path.read_text(encoding="utf-8")
    invoice, items = parse_invoice(html, "local://sp-tabresult")

    assert len(items) == 2
    assert items[0].raw_name == "QJO GORG QUATA PD E"
    assert items[0].quantity == 0.17
    assert items[0].unit_price == 109.8
    assert items[0].total_price == 18.67
    assert invoice.total_amount == 543.22

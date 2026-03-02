from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from .models import Invoice, InvoiceItem


def connect(db_path: str = "data/what_im_buying.db") -> sqlite3.Connection:
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS invoices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT NOT NULL,
            issued_at TEXT NULL,
            total_amount REAL NULL,
            raw_html_hash TEXT NOT NULL UNIQUE,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id INTEGER NOT NULL,
            raw_name TEXT NOT NULL,
            normalized_name TEXT NOT NULL,
            quantity REAL NULL,
            unit_price REAL NULL,
            total_price REAL NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(invoice_id) REFERENCES invoices(id)
        )
        """
    )
    _migrate_items_columns(conn)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS item_enrichment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER NOT NULL,
            stage TEXT NOT NULL,
            output_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(item_id) REFERENCES items(id)
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_item_enrichment_item_stage
        ON item_enrichment(item_id, stage)
        """
    )
    conn.commit()


def save_invoice(conn: sqlite3.Connection, invoice: Invoice, items: list[InvoiceItem]) -> int:
    cursor = conn.execute(
        """
        INSERT OR IGNORE INTO invoices (url, issued_at, total_amount, raw_html_hash)
        VALUES (?, ?, ?, ?)
        """,
        (
            invoice.url,
            invoice.issued_at.isoformat() if invoice.issued_at else None,
            invoice.total_amount,
            invoice.raw_html_hash,
        ),
    )
    conn.commit()

    if cursor.lastrowid == 0:
        row = conn.execute(
            "SELECT id FROM invoices WHERE raw_html_hash = ?",
            (invoice.raw_html_hash,),
        ).fetchone()
        if not row:
            raise RuntimeError("Unable to retrieve existing invoice id")
        return int(row["id"])

    invoice_id = int(cursor.lastrowid)
    conn.executemany(
        """
        INSERT INTO items (invoice_id, raw_name, normalized_name, quantity, unit_price, total_price)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (
                invoice_id,
                item.raw_name,
                item.normalized_name,
                item.quantity,
                item.unit_price,
                item.total_price,
            )
            for item in items
        ],
    )
    conn.commit()
    return invoice_id


def get_latest_invoice_id(conn: sqlite3.Connection) -> int | None:
    row = conn.execute(
        """
        SELECT id
        FROM invoices
        ORDER BY COALESCE(issued_at, created_at) DESC
        LIMIT 1
        """
    ).fetchone()
    if not row:
        return None
    return int(row["id"])


def get_items_by_invoice(conn: sqlite3.Connection, invoice_id: int) -> list[sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT id, raw_name, normalized_name, quantity, unit_price, total_price
        FROM items
        WHERE invoice_id = ?
        ORDER BY id
        """,
        (invoice_id,),
    ).fetchall()
    return list(rows)


def save_item_enrichments(
    conn: sqlite3.Connection,
    stage: str,
    enrichments: list[dict[str, Any]],
) -> int:
    rows_to_insert: list[tuple[int, str, str]] = []
    for enrichment in enrichments:
        item_id = enrichment.get("item_id")
        if isinstance(item_id, str) and item_id.isdigit():
            item_id = int(item_id)
        if not isinstance(item_id, int):
            continue
        rows_to_insert.append(
            (
                item_id,
                stage,
                json.dumps(enrichment, ensure_ascii=True),
            )
        )
    if not rows_to_insert:
        return 0
    conn.executemany(
        """
        INSERT INTO item_enrichment (item_id, stage, output_json)
        VALUES (?, ?, ?)
        """,
        rows_to_insert,
    )
    conn.commit()
    return len(rows_to_insert)


def _migrate_items_columns(conn: sqlite3.Connection) -> None:
    cols = _table_columns(conn, "items")
    if "description" in cols and "raw_name" not in cols:
        conn.execute("ALTER TABLE items RENAME COLUMN description TO raw_name")
    cols = _table_columns(conn, "items")
    if "canonical_name" in cols and "normalized_name" not in cols:
        conn.execute("ALTER TABLE items RENAME COLUMN canonical_name TO normalized_name")


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
    return {str(row["name"]) for row in rows}

from __future__ import annotations

import json
import sqlite3

import streamlit as st

from what_im_buying.storage import connect as storage_connect
from what_im_buying.storage import init_db


def load_invoices(conn: sqlite3.Connection) -> list[sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT id, url, issued_at, total_amount, created_at
        FROM invoices
        ORDER BY COALESCE(issued_at, created_at) DESC
        """
    ).fetchall()
    return list(rows)


def load_items(conn: sqlite3.Connection, invoice_id: int) -> list[sqlite3.Row]:
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


def load_enrichments_for_invoice(conn: sqlite3.Connection, invoice_id: int) -> list[sqlite3.Row]:
    rows = conn.execute(
        """
        SELECT ie.id, ie.item_id, ie.stage, ie.output_json, ie.created_at
        FROM item_enrichment ie
        JOIN items i ON i.id = ie.item_id
        WHERE i.invoice_id = ?
        ORDER BY ie.created_at DESC, ie.id DESC
        """,
        (invoice_id,),
    ).fetchall()
    return list(rows)


def parse_output_json(raw: str) -> dict | str:
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return raw


def main() -> None:
    st.set_page_config(page_title="What I'm Buying - Viewer", layout="wide")
    st.title("What I'm Buying - Minimal Viewer")

    db_path = st.sidebar.text_input("SQLite DB path", value="data/what_im_buying.db")

    try:
        conn = storage_connect(db_path)
        init_db(conn)
    except sqlite3.Error as exc:
        st.error(f"Could not open database: {exc}")
        return

    try:
        invoices = load_invoices(conn)
    except sqlite3.Error as exc:
        st.error(f"Could not load invoices: {exc}")
        return

    if not invoices:
        st.info("No invoices found yet. Parse an invoice first.")
        return

    options = [
        (
            int(row["id"]),
            f"#{int(row['id'])} | issued={row['issued_at'] or 'n/a'} | total={row['total_amount']}",
        )
        for row in invoices
    ]
    selected_label = st.selectbox(
        "Select invoice",
        [label for _, label in options],
        index=0,
    )
    selected_id = next(invoice_id for invoice_id, label in options if label == selected_label)

    selected_invoice = next(row for row in invoices if int(row["id"]) == selected_id)
    st.subheader("Invoice details")
    st.write(
        {
            "id": int(selected_invoice["id"]),
            "url": selected_invoice["url"],
            "issued_at": selected_invoice["issued_at"],
            "total_amount": selected_invoice["total_amount"],
            "created_at": selected_invoice["created_at"],
        }
    )

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Items")
        items = load_items(conn, selected_id)
        st.caption(f"{len(items)} items")
        if not items:
            st.info("No items found for this invoice.")
        else:
            st.dataframe(
                [
                    {
                        "item_id": int(item["id"]),
                        "raw_name": item["raw_name"],
                        "normalized_name": item["normalized_name"],
                        "quantity": item["quantity"],
                        "unit_price": item["unit_price"],
                        "total_price": item["total_price"],
                    }
                    for item in items
                ],
                use_container_width=True,
            )

    with col2:
        st.subheader("Enrichments")
        enrichments = load_enrichments_for_invoice(conn, selected_id)
        st.caption(f"{len(enrichments)} records")
        if not enrichments:
            st.info("No enrichments found for this invoice.")
        else:
            for enr in enrichments:
                with st.expander(
                    f"enrichment #{int(enr['id'])} | item {int(enr['item_id'])} | stage={enr['stage']}"
                ):
                    st.write("created_at:", enr["created_at"])
                    st.json(parse_output_json(enr["output_json"]))


if __name__ == "__main__":
    main()

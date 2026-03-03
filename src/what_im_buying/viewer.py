from __future__ import annotations

import json
import sqlite3

import streamlit as st

from what_im_buying.categories import CATEGORY_LABELS_PTBR
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
        SELECT id, raw_name, normalized_name, quantity, unit_type, unit_price, total_price
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


def load_latest_enrichment_by_item(conn: sqlite3.Connection, invoice_id: int, stage: str) -> dict[int, dict]:
    rows = conn.execute(
        """
        SELECT ie.item_id, ie.output_json
        FROM item_enrichment ie
        JOIN items i ON i.id = ie.item_id
        WHERE i.invoice_id = ? AND ie.stage = ?
        ORDER BY ie.id DESC
        """,
        (invoice_id, stage),
    ).fetchall()
    latest_by_item: dict[int, dict] = {}
    for row in rows:
        item_id = int(row["item_id"])
        if item_id in latest_by_item:
            continue
        parsed = parse_output_json(row["output_json"])
        if isinstance(parsed, dict):
            latest_by_item[item_id] = parsed
    return latest_by_item


def format_brl(value: float | int | None) -> str:
    if value is None:
        return "-"
    formatted = f"{float(value):,.2f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


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

    st.subheader("Items + Categorization")
    items = load_items(conn, selected_id)
    categorized_by_item = load_latest_enrichment_by_item(conn, selected_id, "categorize")
    normalized_by_item = load_latest_enrichment_by_item(conn, selected_id, "normalize")

    if not items:
        st.info("No items found for this invoice.")
    else:
        available_keys = sorted(
            {str(payload.get("category_key")) for payload in categorized_by_item.values() if payload.get("category_key")}
        )
        if "uncategorized" not in available_keys:
            available_keys.append("uncategorized")
        selected_keys = st.multiselect(
            "Filter categories",
            options=available_keys,
            default=available_keys,
        )
        merged_rows: list[dict] = []
        for item in items:
            item_id = int(item["id"])
            cat = categorized_by_item.get(item_id, {})
            category_key = str(cat.get("category_key") or "uncategorized")
            if category_key not in selected_keys:
                continue
            total_price_value = float(item["total_price"] or 0.0)
            merged_rows.append(
                {
                    "item_id": item_id,
                    "raw_name": item["raw_name"],
                    "canonical_name": normalized_by_item.get(item_id, {}).get("canonical_name", item["normalized_name"]),
                    "quantity": item["quantity"],
                    "invoice_unit_type": item["unit_type"],
                    "unit_price_brl": format_brl(item["unit_price"]),
                    "total_price_brl": format_brl(total_price_value),
                    "_total_price_value": total_price_value,
                    "category_key": category_key,
                    "category_label_ptbr": CATEGORY_LABELS_PTBR.get(category_key, "Nao categorizado"),
                    "confidence": cat.get("confidence"),
                    "needs_review": cat.get("needs_review"),
                }
            )
        total_filtered = sum(float(item["_total_price_value"]) for item in merged_rows)
        st.metric("Total gasto (filtro atual)", format_brl(total_filtered))

        table_rows = [{k: v for k, v in row.items() if k != "_total_price_value"} for row in merged_rows]
        st.dataframe(
            table_rows,
            use_container_width=True,
        )

        summary: dict[str, dict[str, float | int]] = {}
        for item in merged_rows:
            key = str(item["category_key"])
            if key not in summary:
                summary[key] = {"count": 0, "total_spend": 0.0}
            summary[key]["count"] = int(summary[key]["count"]) + 1
            summary[key]["total_spend"] = float(summary[key]["total_spend"]) + float(item["_total_price_value"])

        st.caption("Summary (count and spend)")
        st.dataframe(
            [
                {
                    "category_key": key,
                    "category_label_ptbr": CATEGORY_LABELS_PTBR.get(key, "Nao categorizado"),
                    "count": int(values["count"]),
                    "total_spend": round(float(values["total_spend"]), 2),
                    "total_spend_brl": format_brl(float(values["total_spend"])),
                }
                for key, values in sorted(
                    summary.items(),
                    key=lambda x: (-float(x[1]["total_spend"]), -int(x[1]["count"]), x[0]),
                )
            ],
            use_container_width=True,
        )

    st.subheader("Raw enrichment records")
    enrichments = load_enrichments_for_invoice(conn, selected_id)
    st.caption(f"{len(enrichments)} records")
    if not enrichments:
        st.info("No enrichments found for this invoice.")
    else:
        for enr in enrichments:
            with st.expander(f"enrichment #{int(enr['id'])} | item {int(enr['item_id'])} | stage={enr['stage']}"):
                st.write("created_at:", enr["created_at"])
                st.json(parse_output_json(enr["output_json"]))


if __name__ == "__main__":
    main()

from __future__ import annotations

import argparse
from pathlib import Path

from dotenv import load_dotenv

from .ai import generate_normalized_items
from .parser import fetch_invoice_html, parse_invoice
from .storage import (
    connect,
    get_items_by_invoice,
    get_latest_invoice_id,
    init_db,
    save_invoice,
    save_item_enrichments,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="NFC-e parser and invoice normalization.")
    parser.add_argument("--db", default="data/what_im_buying.db", help="SQLite database path.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    parse_url = subparsers.add_parser("parse-url", help="Fetch invoice page from QR URL.")
    parse_url.add_argument("url", help="Public NFC-e QR URL.")
    parse_url.add_argument("--save-html", help="Optional path to save fetched HTML.")

    import_html = subparsers.add_parser("import-html", help="Parse invoice from local HTML file.")
    import_html.add_argument("file", help="HTML file path.")
    import_html.add_argument("--url", default="local://invoice", help="Logical source URL.")

    subparsers.add_parser("normalize-last-invoice", help="Normalize items from latest invoice using AI.")
    legacy = subparsers.add_parser("normalize-last-intake", help=argparse.SUPPRESS)
    legacy.set_defaults(_deprecated_alias="normalize-last-invoice")
    return parser


def cmd_parse_url(args: argparse.Namespace) -> int:
    raw_html = fetch_invoice_html(args.url)
    if args.save_html:
        output = Path(args.save_html)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(raw_html, encoding="utf-8")

    invoice, items = parse_invoice(raw_html, url=args.url)
    conn = connect(args.db)
    init_db(conn)
    invoice_id = save_invoice(conn, invoice, items)
    print(f"Invoice {invoice_id} saved with {len(items)} items.")
    _print_items(items)
    return 0


def cmd_import_html(args: argparse.Namespace) -> int:
    html = Path(args.file).read_text(encoding="utf-8")
    invoice, items = parse_invoice(html, url=args.url)
    conn = connect(args.db)
    init_db(conn)
    invoice_id = save_invoice(conn, invoice, items)
    print(f"Invoice {invoice_id} saved with {len(items)} items from {args.file}.")
    _print_items(items)
    return 0


def cmd_normalize_last_invoice(args: argparse.Namespace) -> int:
    conn = connect(args.db)
    init_db(conn)
    invoice_id = get_latest_invoice_id(conn)
    if invoice_id is None:
        print("No invoices found. Parse an invoice first.")
        return 1

    items = get_items_by_invoice(conn, invoice_id)
    if not items:
        print(f"Invoice {invoice_id} has no items.")
        return 1

    payload = []
    for row in items:
        payload.append(
            {
                "item_id": int(row["id"]),
                "raw_name": str(row["raw_name"]),
                "normalized_name": str(row["normalized_name"]),
                "quantity": row["quantity"],
                "unit_price": row["unit_price"],
                "total_price": row["total_price"],
            }
        )

    normalized = generate_normalized_items(payload)
    saved = save_item_enrichments(conn, stage="normalize", enrichments=normalized)
    print(f"Normalized {saved} items for invoice {invoice_id}.")
    _print_normalized_items(normalized)
    return 0


def _print_items(items) -> None:
    for item in items:
        print(
            f"- {item.raw_name} | qty={item.quantity} | unit={item.unit_price} | "
            f"total={item.total_price}"
        )


def _print_normalized_items(items) -> None:
    for item in items:
        print(
            "- item_id={item_id} | raw='{raw_name}' | canonical='{canonical_name}' | "
            "brand={brand} | size={size_value} {size_unit} | pack={pack_count} | unit_type={unit_type} | "
            "confidence={confidence} | needs_review={needs_review}".format(
                item_id=item.get("item_id"),
                raw_name=item.get("raw_name"),
                canonical_name=item.get("canonical_name"),
                brand=item.get("brand"),
                size_value=item.get("size_value"),
                size_unit=item.get("size_unit"),
                pack_count=item.get("pack_count"),
                unit_type=item.get("unit_type"),
                confidence=item.get("confidence"),
                needs_review=item.get("needs_review"),
            )
        )


def main() -> int:
    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()

    if getattr(args, "_deprecated_alias", None):
        print("Warning: 'normalize-last-intake' is deprecated; use 'normalize-last-invoice'.")
    if args.command == "parse-url":
        return cmd_parse_url(args)
    if args.command == "import-html":
        return cmd_import_html(args)
    if args.command == "normalize-last-intake":
        return cmd_normalize_last_invoice(args)
    if args.command == "normalize-last-invoice":
        return cmd_normalize_last_invoice(args)
    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

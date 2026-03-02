from __future__ import annotations

import hashlib
import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup

from .models import Invoice, InvoiceItem
from .text_utils import normalize_product_name, parse_brl_number

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    )
}


def fetch_invoice_html(url: str, timeout: int = 20) -> str:
    response = requests.get(url, headers=DEFAULT_HEADERS, timeout=timeout)
    response.raise_for_status()
    return response.text


def hash_html(raw_html: str) -> str:
    return hashlib.sha256(raw_html.encode("utf-8")).hexdigest()


def parse_invoice(html: str, url: str) -> tuple[Invoice, list[InvoiceItem]]:
    soup = BeautifulSoup(html, "html.parser")
    items = _extract_items_from_tables(soup)
    issued_at = _extract_issued_at(soup)
    total_amount = _extract_total_amount(soup)
    invoice = Invoice(
        url=url,
        issued_at=issued_at,
        total_amount=total_amount,
        raw_html_hash=hash_html(html),
    )
    return invoice, items


def _extract_items_from_tables(soup: BeautifulSoup) -> list[InvoiceItem]:
    # SP NFC-e responsive pages frequently use #tabResult rows with span classes
    # instead of a header-based table structure.
    tab_result_items = _extract_items_from_tab_result(soup)
    if tab_result_items:
        return tab_result_items

    parsed_items: list[InvoiceItem] = []
    for table in soup.find_all("table"):
        rows = table.find_all("tr")
        if not rows:
            continue

        headers = [cell.get_text(" ", strip=True).lower() for cell in rows[0].find_all(["th", "td"])]
        has_desc = any("desc" in h for h in headers)
        has_value = any(("valor" in h) or ("vl" in h) or ("preco" in h) for h in headers)
        if not (has_desc and has_value):
            continue

        for row in rows[1:]:
            cells = [cell.get_text(" ", strip=True) for cell in row.find_all("td")]
            if len(cells) < 2:
                continue
            maybe_item = _parse_row(cells, headers)
            if maybe_item:
                parsed_items.append(maybe_item)

    return parsed_items


def _extract_items_from_tab_result(soup: BeautifulSoup) -> list[InvoiceItem]:
    table = soup.find("table", id="tabResult")
    if table is None:
        return []

    parsed_items: list[InvoiceItem] = []
    for row in table.find_all("tr"):
        description = _get_text_from_selector(row, ".txtTit")
        total_text = _get_text_from_selector(row, ".valor")
        if not description or not total_text:
            continue

        quantity_text = _extract_number_from_text(_get_text_from_selector(row, ".Rqtd"))
        unit_price_text = _extract_number_from_text(_get_text_from_selector(row, ".RvlUnit"))

        quantity = parse_brl_number(quantity_text) if quantity_text else None
        unit_price = parse_brl_number(unit_price_text) if unit_price_text else None
        total_price = parse_brl_number(total_text)
        if total_price is None:
            continue

        parsed_items.append(
            InvoiceItem(
                description=description,
                quantity=quantity,
                unit_price=unit_price,
                total_price=total_price,
                canonical_name=normalize_product_name(description),
            )
        )
    return parsed_items


def _get_text_from_selector(node, selector: str) -> str:
    selected = node.select_one(selector)
    return selected.get_text(" ", strip=True) if selected else ""


def _extract_number_from_text(text: str) -> str | None:
    if not text:
        return None
    # Examples: "Qtde.:0,17", "Vl. Unit.: 109,8"
    match = re.search(r"([-]?\d+(?:[.,]\d+)*)", text, flags=re.I)
    if not match:
        return None
    return match.group(1)


def _parse_row(cells: list[str], headers: list[str]) -> InvoiceItem | None:
    description = None
    quantity = None
    unit_price = None
    total_price = None

    for index, header in enumerate(headers):
        if index >= len(cells):
            continue
        value = cells[index]
        header_norm = normalize_product_name(header)
        if "desc" in header_norm and value:
            description = value
        elif ("qtd" in header_norm or "quant" in header_norm) and quantity is None:
            quantity = parse_brl_number(value)
        elif ("unit" in header_norm or "preco" in header_norm or "vl unit" in header_norm) and unit_price is None:
            unit_price = parse_brl_number(value)
        elif ("total" in header_norm or "valor" in header_norm or "vl" in header_norm) and total_price is None:
            total_price = parse_brl_number(value)

    if description is None:
        description = cells[0]
    if total_price is None:
        numeric_cells = [parse_brl_number(cell) for cell in cells]
        numeric_values = [v for v in numeric_cells if v is not None]
        if numeric_values:
            total_price = max(numeric_values)

    if not description or total_price is None:
        return None

    canonical_name = normalize_product_name(description)

    return InvoiceItem(
        description=description,
        quantity=quantity,
        unit_price=unit_price,
        total_price=total_price,
        canonical_name=canonical_name,
    )


def _extract_issued_at(soup: BeautifulSoup) -> datetime | None:
    text = soup.get_text(" ", strip=True)
    patterns = [
        r"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2}:\d{2})",
        r"(\d{2}/\d{2}/\d{4}\s+\d{2}:\d{2})",
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if not match:
            continue
        for fmt in ("%d/%m/%Y %H:%M:%S", "%d/%m/%Y %H:%M"):
            try:
                return datetime.strptime(match.group(1), fmt)
            except ValueError:
                continue
    return None


def _extract_total_amount(soup: BeautifulSoup) -> float | None:
    text = soup.get_text(" ", strip=True)
    patterns = [
        r"valor a pagar\s*R?\$?\s*[:\-]?\s*([\d\.,]+)",
        r"valor total\s*R?\$?\s*[:\-]?\s*([\d\.,]+)",
        r"total\s*[:\-]?\s*R?\$?\s*([\d\.,]+)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.I)
        if match:
            return parse_brl_number(match.group(1))
    return None

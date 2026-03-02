from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class InvoiceItem:
    description: str
    quantity: float | None
    unit_price: float | None
    total_price: float
    canonical_name: str


@dataclass(slots=True)
class Invoice:
    url: str
    issued_at: datetime | None
    total_amount: float | None
    raw_html_hash: str

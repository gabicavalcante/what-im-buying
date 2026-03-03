from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class InvoiceItem:
    raw_name: str
    quantity: float | None
    unit_type: str | None
    unit_price: float | None
    total_price: float
    normalized_name: str


@dataclass(slots=True)
class Invoice:
    url: str
    issued_at: datetime | None
    total_amount: float | None
    raw_html_hash: str


@dataclass(slots=True)
class NormalizationEnrichment:
    item_id: int
    raw_name: str
    canonical_name: str
    brand: str | None
    unit_type: str | None
    confidence: float
    needs_review: bool
    unit_type_full: str | None = None


@dataclass(slots=True)
class CategorizationEnrichment:
    item_id: int
    raw_name: str
    normalized_name: str
    category_key: str
    confidence: float
    needs_review: bool
    reason: str


@dataclass(slots=True)
class CategorySummary:
    category_key: str
    count: int

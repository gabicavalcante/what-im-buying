from __future__ import annotations

from collections import Counter
from typing import Any

from .models import CategorizationEnrichment, CategorySummary

CATEGORY_LABELS_PTBR: dict[str, str] = {
    "produce": "Hortifruti",
    "meat_fish": "Carnes e Peixes",
    "dairy_eggs": "Laticinios e Ovos",
    "bakery": "Padaria",
    "pantry": "Despensa",
    "snacks_sweets": "Snacks e Doces",
    "beverages_non_alcoholic": "Bebidas nao alcoolicas",
    "alcohol": "Bebidas alcoolicas",
    "frozen": "Congelados",
    "household_cleaning": "Limpeza da Casa",
    "personal_care": "Cuidados Pessoais",
    "other": "Outros",
}


KEYWORDS_BY_CATEGORY: dict[str, tuple[str, ...]] = {
    "alcohol": ("vinho", "cerveja", "michelob", "vodka", "whisky", "gin"),
    "household_cleaning": ("limp", "amac", "agua sanit", "deterg", "desinf", "to papel", "sabao"),
    "personal_care": ("colgate", "cotonete", "shampoo", "creme dental", "sabonete"),
    "dairy_eggs": ("queijo", "qjo", "leite", "iog", "catupiry", "requeij", "manteiga", "ovo"),
    "meat_fish": ("carne", "frango", "bacon", "peru", "ling", "lingui", "hamb", "peixe"),
    "produce": ("alface", "cebola", "limao", "tomate", "banana", "maca", "pepino", "alho"),
    "frozen": ("pizza", "congel", "lasanha"),
    "bakery": ("pao", "baguet", "bisnag", "croissant"),
    "snacks_sweets": ("bisc", "biscoito", "chocolate", "bombom", "lays", "salgad"),
    "beverages_non_alcoholic": ("refrigerante", "ref ", "suco", "agua mineral", "cha"),
    "pantry": ("arroz", "feijao", "farinha", "cafe", "acucar", "most", "essencia", "molho"),
}


def categorize_item(row: dict[str, Any]) -> CategorizationEnrichment:
    normalized_name = str(row.get("normalized_name", "")).lower().strip()
    category_key = _pick_category(normalized_name)
    confidence = 0.95 if category_key != "other" else 0.4
    needs_review = category_key == "other"
    reason = "keyword_match" if category_key != "other" else "no_keyword_match"

    return CategorizationEnrichment(
        item_id=int(row["item_id"]),
        raw_name=str(row.get("raw_name", "")),
        normalized_name=normalized_name,
        category_key=category_key,
        confidence=confidence,
        needs_review=needs_review,
        reason=reason,
    )


def summarize_categories(categorized_items: list[CategorizationEnrichment]) -> list[CategorySummary]:
    counts = Counter(item.category_key for item in categorized_items)
    return [
        CategorySummary(
            category_key=key,
            count=count,
        )
        for key, count in sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    ]


def _pick_category(normalized_name: str) -> str:
    for category_key, keywords in KEYWORDS_BY_CATEGORY.items():
        if any(keyword in normalized_name for keyword in keywords):
            return category_key
    return "other"

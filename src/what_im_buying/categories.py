from __future__ import annotations

from collections import Counter

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

def summarize_categories(categorized_items: list[CategorizationEnrichment]) -> list[CategorySummary]:
    counts = Counter(item.category_key for item in categorized_items)
    return [
        CategorySummary(
            category_key=key,
            count=count,
        )
        for key, count in sorted(counts.items(), key=lambda x: (-x[1], x[0]))
    ]

from __future__ import annotations

from src.what_im_buying.categories import summarize_categories
from src.what_im_buying.models import CategorizationEnrichment


def test_summarize_categories() -> None:
    summary = summarize_categories(
        [
            CategorizationEnrichment(
                item_id=1,
                raw_name="LEITE",
                normalized_name="leite",
                category_key="dairy_eggs",
                confidence=0.9,
                needs_review=False,
                reason="model",
            ),
            CategorizationEnrichment(
                item_id=2,
                raw_name="QJO",
                normalized_name="qjo prato",
                category_key="dairy_eggs",
                confidence=0.9,
                needs_review=False,
                reason="model",
            ),
            CategorizationEnrichment(
                item_id=3,
                raw_name="AGUA SANIT",
                normalized_name="agua sanit ype",
                category_key="household_cleaning",
                confidence=0.9,
                needs_review=False,
                reason="model",
            ),
        ]
    )
    assert summary[0].category_key == "dairy_eggs"
    assert summary[0].count == 2

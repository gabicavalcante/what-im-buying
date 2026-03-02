from __future__ import annotations

from src.what_im_buying.categories import categorize_item, summarize_categories


def test_categorize_item_dairy() -> None:
    result = categorize_item(
        {"item_id": 1, "raw_name": "QJO GORG QUATA PD E", "normalized_name": "qjo gorg quata pd e"}
    )
    assert result.category_key == "dairy_eggs"
    assert result.needs_review is False


def test_categorize_item_household_cleaning() -> None:
    result = categorize_item(
        {"item_id": 2, "raw_name": "AGUA SANIT YPE", "normalized_name": "agua sanit ype"}
    )
    assert result.category_key == "household_cleaning"


def test_categorize_item_other_when_no_match() -> None:
    result = categorize_item(
        {"item_id": 3, "raw_name": "ITEM NAO MAPEADO XYZ", "normalized_name": "item nao mapeado xyz"}
    )
    assert result.category_key == "other"
    assert result.needs_review is True


def test_summarize_categories() -> None:
    summary = summarize_categories(
        [
            categorize_item({"item_id": 1, "raw_name": "LEITE", "normalized_name": "leite"}),
            categorize_item({"item_id": 2, "raw_name": "QJO", "normalized_name": "qjo prato"}),
            categorize_item({"item_id": 3, "raw_name": "AGUA SANIT", "normalized_name": "agua sanit ype"}),
        ]
    )
    assert summary[0].category_key == "dairy_eggs"
    assert summary[0].count == 2

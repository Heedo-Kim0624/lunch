from itertools import product
from types import SimpleNamespace

from recommendations.filters import cuisine_group, filter_foods
from recommendations.seed_data import FOODS

TEMPERATURES = ("hot", "cold")
STAPLES = ("rice", "bread", "noodle")
CUISINES = ("korean", "chinese", "western", "japanese", "southeast_asian", "other")
SPICE_LEVELS = ("spicy", "mild")


def catalog_foods() -> list[SimpleNamespace]:
    return [
        SimpleNamespace(
            canonical_name=item["canonical_name"],
            cuisine=item["cuisine"],
            staple_types=item["staple_types"],
            attributes=item["attributes"],
        )
        for item in FOODS
    ]


def assert_matches(food: SimpleNamespace, filters: dict[str, list[str]]) -> None:
    expected_temperature = "cold" if food.attributes["cold"] >= 0.5 else "hot"
    expected_spice = "spicy" if food.attributes["spicy"] >= 0.5 else "mild"
    assert expected_temperature in filters["temperature"]
    assert not set(filters["staples"]).isdisjoint(food.staple_types)
    assert cuisine_group(food.cuisine) in filters["cuisines"]
    assert expected_spice in filters["spice"]


def test_every_single_filter_option_has_a_substantial_candidate_pool() -> None:
    foods = catalog_foods()

    for value in TEMPERATURES:
        assert len(filter_foods(foods, {"temperature": [value]})) >= 100
    for value in STAPLES:
        assert len(filter_foods(foods, {"staples": [value]})) >= 100
    for value in CUISINES:
        assert len(filter_foods(foods, {"cuisines": [value]})) >= 100
    for value in SPICE_LEVELS:
        assert len(filter_foods(foods, {"spice": [value]})) >= 200


def test_all_72_full_single_choice_combinations_are_semantically_correct() -> None:
    foods = catalog_foods()
    nonempty_combinations = 0

    for temperature, staple, cuisine, spice in product(
        TEMPERATURES,
        STAPLES,
        CUISINES,
        SPICE_LEVELS,
    ):
        filters = {
            "temperature": [temperature],
            "staples": [staple],
            "cuisines": [cuisine],
            "spice": [spice],
        }
        matches = filter_foods(foods, filters)
        if matches:
            nonempty_combinations += 1
        for food in matches:
            assert_matches(food, filters)

    # Some intersections are intentionally empty rather than assigning an
    # inaccurate staple or temperature merely to fill the matrix.
    assert nonempty_combinations >= 40


def test_multi_select_expands_within_a_group_and_narrows_across_groups() -> None:
    foods = catalog_foods()
    korean_only = filter_foods(foods, {"cuisines": ["korean"]})
    korean_or_japanese = filter_foods(
        foods, {"cuisines": ["korean", "japanese"]}
    )
    hot_korean_or_japanese = filter_foods(
        foods,
        {"temperature": ["hot"], "cuisines": ["korean", "japanese"]},
    )

    assert len(korean_or_japanese) > len(korean_only)
    assert len(hot_korean_or_japanese) < len(korean_or_japanese)

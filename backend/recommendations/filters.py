from __future__ import annotations

from collections.abc import Iterable, Mapping

from recommendations.models import Food

TEMPERATURE_FILTERS = ("hot", "cold")
STAPLE_FILTERS = ("rice", "bread", "noodle")
CUISINE_FILTERS = (
    "korean",
    "chinese",
    "western",
    "japanese",
    "southeast_asian",
    "other",
)
SPICE_FILTERS = ("spicy", "mild")

FILTER_KEYS = ("temperature", "staples", "cuisines", "spice")

WESTERN_CUISINES = {"서양식", "이탈리아식"}
SOUTHEAST_ASIAN_CUISINES = {"베트남식", "태국식", "동남아식"}


def _attribute(food: Food, name: str) -> float:
    value = food.attributes.get(name, 0.0)
    if not isinstance(value, int | float):
        return 0.0
    return max(0.0, min(1.0, float(value)))


def cuisine_group(cuisine: str) -> str:
    if cuisine == "한식":
        return "korean"
    if cuisine == "중식":
        return "chinese"
    if cuisine == "일식":
        return "japanese"
    if cuisine in WESTERN_CUISINES:
        return "western"
    if cuisine in SOUTHEAST_ASIAN_CUISINES:
        return "southeast_asian"
    return "other"


def normalize_filters(filters: Mapping[str, object] | None) -> dict[str, list[str]]:
    if not filters:
        return {}

    normalized: dict[str, list[str]] = {}
    for key in FILTER_KEYS:
        values = filters.get(key, [])
        if not isinstance(values, list | tuple):
            continue
        unique_values = list(dict.fromkeys(str(value) for value in values))
        if unique_values:
            normalized[key] = unique_values
    return normalized


def food_matches_filters(food: Food, filters: Mapping[str, list[str]]) -> bool:
    temperatures = set(filters.get("temperature", []))
    if temperatures:
        food_temperature = "cold" if _attribute(food, "cold") >= 0.5 else "hot"
        if food_temperature not in temperatures:
            return False

    staples = set(filters.get("staples", []))
    if staples and staples.isdisjoint(food.staple_types):
        return False

    cuisines = set(filters.get("cuisines", []))
    if cuisines and cuisine_group(food.cuisine) not in cuisines:
        return False

    spice_levels = set(filters.get("spice", []))
    if spice_levels:
        food_spice = "spicy" if _attribute(food, "spicy") >= 0.5 else "mild"
        if food_spice not in spice_levels:
            return False

    return True


def filter_foods(foods: Iterable[Food], filters: Mapping[str, object] | None) -> list[Food]:
    normalized = normalize_filters(filters)
    return [food for food in foods if food_matches_filters(food, normalized)]

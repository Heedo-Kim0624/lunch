from collections import Counter
from itertools import product

from django.core.management.base import BaseCommand, CommandError

from recommendations.filters import (
    CUISINE_FILTERS,
    SPICE_FILTERS,
    STAPLE_FILTERS,
    TEMPERATURE_FILTERS,
    cuisine_group,
    filter_foods,
)
from recommendations.models import Food
from recommendations.seed_data import ATTRIBUTE_NAMES, FOODS

EXPECTED_CUISINE_COUNTS = {
    "korean": 350,
    "chinese": 120,
    "western": 150,
    "japanese": 130,
    "southeast_asian": 100,
    "other": 150,
}
EXPECTED_STAPLE_COUNTS = {"rice": 531, "bread": 122, "noodle": 196}
EXPECTED_COLD_COUNT = 115
EXPECTED_SPICY_COUNT = 233
EXPECTED_NONEMPTY_FULL_COMBINATIONS = 41


class Command(BaseCommand):
    help = "Audit the active database catalog and all supported filter combinations."

    def handle(self, *args: object, **options: object) -> None:
        foods = list(Food.objects.filter(is_active=True).order_by("canonical_name"))
        expected_by_name = {str(item["canonical_name"]): item for item in FOODS}
        actual_by_name = {food.canonical_name: food for food in foods}
        errors: list[str] = []

        if len(foods) != len(FOODS):
            errors.append(f"active count is {len(foods)}; expected {len(FOODS)}")

        missing = sorted(expected_by_name.keys() - actual_by_name.keys())
        extra = sorted(actual_by_name.keys() - expected_by_name.keys())
        if missing:
            errors.append(f"missing catalog rows: {', '.join(missing[:5])}")
        if extra:
            errors.append(f"unexpected active rows: {', '.join(extra[:5])}")

        for name in sorted(expected_by_name.keys() & actual_by_name.keys()):
            expected = expected_by_name[name]
            actual = actual_by_name[name]
            comparable = {
                "family": actual.family,
                "description": actual.description,
                "cuisine": actual.cuisine,
                "meal_style": actual.meal_style,
                "staple_types": actual.staple_types,
                "attributes": actual.attributes,
                "is_lunch_suitable": actual.is_lunch_suitable,
                "is_active": actual.is_active,
            }
            normalized_expected = {
                **{key: value for key, value in expected.items() if key != "canonical_name"},
                "staple_types": list(expected["staple_types"]),
            }
            if comparable != normalized_expected:
                errors.append(f"database row differs from curated source: {name}")
                break

        descriptions = [food.description.strip() for food in foods]
        if any(not description for description in descriptions):
            errors.append("one or more descriptions are empty")
        if len(set(descriptions)) != len(descriptions):
            errors.append("descriptions are not unique")

        for food in foods:
            if set(food.attributes) != set(ATTRIBUTE_NAMES):
                errors.append(f"attribute schema differs: {food.canonical_name}")
                break
            if any(
                not isinstance(value, int | float) or not 0.0 <= float(value) <= 1.0
                for value in food.attributes.values()
            ):
                errors.append(f"attribute value is outside 0..1: {food.canonical_name}")
                break
            if len(food.staple_types) != len(set(food.staple_types)) or not set(
                food.staple_types
            ).issubset(STAPLE_FILTERS):
                errors.append(f"invalid staple types: {food.canonical_name}")
                break

        cuisine_counts = Counter(cuisine_group(food.cuisine) for food in foods)
        staple_counts = Counter(staple for food in foods for staple in food.staple_types)
        cold_count = sum(food.attributes["cold"] >= 0.5 for food in foods)
        spicy_count = sum(food.attributes["spicy"] >= 0.5 for food in foods)
        profile_count = len(
            {tuple(food.attributes[name] for name in ATTRIBUTE_NAMES) for food in foods}
        )

        if dict(cuisine_counts) != EXPECTED_CUISINE_COUNTS:
            errors.append(f"broad cuisine counts differ: {dict(cuisine_counts)}")
        if dict(staple_counts) != EXPECTED_STAPLE_COUNTS:
            errors.append(f"staple counts differ: {dict(staple_counts)}")
        if cold_count != EXPECTED_COLD_COUNT:
            errors.append(f"cold count is {cold_count}; expected {EXPECTED_COLD_COUNT}")
        if spicy_count != EXPECTED_SPICY_COUNT:
            errors.append(f"spicy count is {spicy_count}; expected {EXPECTED_SPICY_COUNT}")
        if profile_count < 900:
            errors.append(f"only {profile_count} distinct attribute profiles")

        combination_counts = [
            len(
                filter_foods(
                    foods,
                    {
                        "temperature": [temperature],
                        "staples": [staple],
                        "cuisines": [cuisine],
                        "spice": [spice],
                    },
                )
            )
            for temperature, staple, cuisine, spice in product(
                TEMPERATURE_FILTERS,
                STAPLE_FILTERS,
                CUISINE_FILTERS,
                SPICE_FILTERS,
            )
        ]
        nonempty_combinations = sum(count > 0 for count in combination_counts)
        if nonempty_combinations != EXPECTED_NONEMPTY_FULL_COMBINATIONS:
            errors.append(
                "nonempty full filter combinations are "
                f"{nonempty_combinations}; expected {EXPECTED_NONEMPTY_FULL_COMBINATIONS}"
            )

        if errors:
            raise CommandError("Catalog audit failed:\n- " + "\n- ".join(errors))

        self.stdout.write(self.style.SUCCESS("Catalog audit passed"))
        self.stdout.write(
            f"active={len(foods)}, descriptions={len(set(descriptions))}, "
            f"families={len({food.family for food in foods})}, profiles={profile_count}"
        )
        self.stdout.write(f"cuisines={dict(cuisine_counts)}")
        self.stdout.write(f"staples={dict(staple_counts)}")
        self.stdout.write(
            f"temperature={{'hot': {len(foods) - cold_count}, 'cold': {cold_count}}}, "
            f"spice={{'spicy': {spicy_count}, 'mild': {len(foods) - spicy_count}}}"
        )
        self.stdout.write(
            f"full_filter_combinations=72, nonempty={nonempty_combinations}, "
            f"empty={72 - nonempty_combinations}"
        )

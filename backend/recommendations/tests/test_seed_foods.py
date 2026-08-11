from collections import Counter
from io import StringIO
from random import Random

import pytest
from django.core.management import call_command

from recommendations.management.commands.seed_foods import ATTRIBUTE_NAMES, FOODS
from recommendations.models import Food
from recommendations.services.scoring import CANDIDATE_POOL_SIZE, create_recommendation


def test_seed_catalog_has_large_unique_complete_menu_set() -> None:
    names = [item["canonical_name"] for item in FOODS]

    assert len(FOODS) >= 200
    assert len(names) == len(set(names))
    assert all(name == name.strip() and name for name in names)

    for item in FOODS:
        assert item["family"]
        assert item["cuisine"]
        assert item["meal_style"]
        assert item["description"]
        assert set(item["attributes"]) == set(ATTRIBUTE_NAMES)
        assert all(0.0 <= value <= 1.0 for value in item["attributes"].values())


@pytest.mark.django_db
def test_seed_command_is_idempotent() -> None:
    first_output = StringIO()
    second_output = StringIO()

    call_command("seed_foods", stdout=first_output)
    call_command("seed_foods", stdout=second_output)

    assert Food.objects.count() == len(FOODS)
    assert f"{len(FOODS)} created" in first_output.getvalue()
    assert f"{len(FOODS)} updated" in second_output.getvalue()
    assert Food.objects.filter(is_active=True, is_lunch_suitable=True).count() == len(FOODS)


@pytest.mark.django_db
def test_seed_command_normalizes_legacy_menu_name_without_losing_row() -> None:
    legacy = Food.objects.create(
        canonical_name="연어 포케",
        family="포케",
        attributes={},
    )

    call_command("seed_foods", stdout=StringIO())

    legacy.refresh_from_db()
    assert legacy.canonical_name == "연어포케"
    assert legacy.attributes == next(
        item["attributes"] for item in FOODS if item["canonical_name"] == "연어포케"
    )


@pytest.mark.django_db
def test_large_catalog_builds_a_diverse_auditable_candidate_pool() -> None:
    call_command("seed_foods", stdout=StringIO())

    exposure = create_recommendation("catalog-test", {}, rng=Random(7))
    snapshot = exposure.session.candidate_snapshot
    family_counts = Counter(candidate["family"] for candidate in snapshot)

    assert exposure.session.policy_version == "rules-v2"
    assert exposure.session.candidate_count == len(FOODS)
    assert len(snapshot) == CANDIDATE_POOL_SIZE
    assert len(family_counts) == len({item["family"] for item in FOODS})
    assert max(family_counts.values()) <= 2
    assert sum(item["selection_probability"] for item in snapshot) == pytest.approx(1)
    assert all(item["food_name"] and item["cuisine"] for item in snapshot)

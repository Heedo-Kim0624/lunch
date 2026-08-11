from collections import Counter
from io import StringIO
from random import Random

import pytest
from django.core.management import call_command

from recommendations.expanded_catalog import EXPANDED_FOODS
from recommendations.filters import cuisine_group
from recommendations.food_details import COLD_SCORES, FOOD_DETAILS
from recommendations.management.commands.seed_foods import ATTRIBUTE_NAMES, FOODS
from recommendations.models import Food
from recommendations.services.scoring import CANDIDATE_POOL_SIZE, create_recommendation

STAPLE_TYPES = {"rice", "bread", "noodle"}


def test_seed_catalog_has_large_unique_complete_menu_set() -> None:
    names = [item["canonical_name"] for item in FOODS]
    descriptions = [item["description"] for item in FOODS]
    attribute_profiles = {
        tuple(item["attributes"][name] for name in ATTRIBUTE_NAMES) for item in FOODS
    }

    assert len(FOODS) == 1_000
    assert len(EXPANDED_FOODS) == 658
    assert len(names) == len(set(names))
    assert set(FOOD_DETAILS) <= set(names)
    assert all(name == name.strip() and name for name in names)
    assert len(descriptions) == len(set(descriptions))
    assert len(attribute_profiles) >= 900
    assert set(COLD_SCORES) <= set(names)

    assert Counter(cuisine_group(str(item["cuisine"])) for item in FOODS) == {
        "korean": 350,
        "japanese": 130,
        "chinese": 120,
        "western": 150,
        "southeast_asian": 100,
        "other": 150,
    }
    assert all(
        str(item["canonical_name"]) in str(item["description"])
        for item in EXPANDED_FOODS
    )

    staple_counts = Counter(
        staple for item in FOODS for staple in item["staple_types"]
    )
    assert set(staple_counts) == STAPLE_TYPES
    assert staple_counts == {"rice": 531, "bread": 122, "noodle": 196}

    for item in FOODS:
        assert item["family"]
        assert item["cuisine"]
        assert item["meal_style"]
        assert item["description"]
        assert isinstance(item["staple_types"], list)
        assert set(item["staple_types"]) <= STAPLE_TYPES
        assert len(item["staple_types"]) == len(set(item["staple_types"]))
        assert set(item["attributes"]) == set(ATTRIBUTE_NAMES)
        assert all(0.0 <= value <= 1.0 for value in item["attributes"].values())
        if item["canonical_name"] in FOOD_DETAILS:
            assert item["attributes"]["cold"] == COLD_SCORES.get(
                item["canonical_name"], 0.0
            )


def test_individual_food_details_cover_known_edge_cases() -> None:
    by_name = {item["canonical_name"]: item for item in FOODS}

    assert "돼지갈비" in by_name["바쿠테"]["description"]
    assert by_name["바쿠테"]["attributes"]["broth"] >= 0.8
    assert by_name["바쿠테"]["attributes"]["light"] <= 0.5
    assert by_name["바쿠테"]["attributes"]["adventurous"] >= 0.6
    assert by_name["바쿠테"]["attributes"]["familiar"] <= 0.5
    assert by_name["카오만가이"]["attributes"]["spicy"] <= 0.2
    assert by_name["물냉면"]["attributes"]["cold"] >= 0.8
    assert by_name["마라탕"]["attributes"]["spicy"] >= 0.8
    assert by_name["마라탕"]["attributes"]["light"] <= 0.4
    assert by_name["닭가슴살샐러드"]["attributes"]["light"] >= 0.7
    assert "튀기" in by_name["피시앤칩스"]["description"]
    assert by_name["비빔밥"]["staple_types"] == ["rice"]
    assert by_name["반미"]["staple_types"] == ["bread"]
    assert by_name["쌀국수"]["staple_types"] == ["noodle"]
    assert set(by_name["부리토"]["staple_types"]) == {"rice", "bread"}
    assert by_name["스테이크"]["staple_types"] == []
    assert by_name["프렌치어니언수프"]["attributes"]["broth"] >= 0.75
    assert by_name["마라롱샤"]["attributes"]["spicy"] >= 0.85
    assert by_name["페루식세비체"]["attributes"]["cold"] >= 0.75
    assert by_name["연어아보카도포케"]["attributes"]["cold"] >= 0.75
    assert by_name["연어아보카도포케"]["attributes"]["light"] >= 0.7
    assert by_name["치킨아도보"]["attributes"]["spicy"] < 0.5
    assert by_name["우육탕면"]["attributes"]["broth"] >= 0.75
    assert by_name["키토김밥"]["staple_types"] == []
    assert set(by_name["이집트코샤리"]["staple_types"]) == {"rice", "noodle"}


@pytest.mark.django_db
def test_seed_command_is_idempotent() -> None:
    first_output = StringIO()
    second_output = StringIO()

    call_command("seed_foods", stdout=first_output)
    call_command("seed_foods", stdout=second_output)

    assert Food.objects.count() == len(FOODS)
    assert f"{len(FOODS)} created" in first_output.getvalue()
    assert f"{len(FOODS)} unchanged" in second_output.getvalue()
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
def test_seed_command_deactivates_rows_outside_the_curated_catalog() -> None:
    stray = Food.objects.create(
        canonical_name="검수되지 않은 임시 메뉴",
        family="임시",
        attributes={},
    )

    call_command("seed_foods", stdout=StringIO())

    stray.refresh_from_db()
    assert not stray.is_active


@pytest.mark.django_db
def test_catalog_audit_command_passes_after_seed() -> None:
    call_command("seed_foods", stdout=StringIO())
    output = StringIO()

    call_command("audit_foods", stdout=output)

    report = output.getvalue()
    assert "Catalog audit passed" in report
    assert "active=1000" in report
    assert "full_filter_combinations=72, nonempty=41, empty=31" in report
    assert Food.objects.filter(is_active=True, is_lunch_suitable=True).count() == 1_000


@pytest.mark.django_db
def test_large_catalog_builds_a_diverse_auditable_candidate_pool() -> None:
    call_command("seed_foods", stdout=StringIO())

    exposure = create_recommendation("catalog-test", {}, rng=Random(7))
    snapshot = exposure.session.candidate_snapshot
    family_counts = Counter(candidate["family"] for candidate in snapshot)

    assert exposure.session.policy_version == "rules-v4"
    assert exposure.session.candidate_count == len(FOODS)
    assert len(snapshot) == CANDIDATE_POOL_SIZE
    assert len(family_counts) == CANDIDATE_POOL_SIZE
    assert max(family_counts.values()) == 1
    assert sum(item["selection_probability"] for item in snapshot) == pytest.approx(1)
    assert all(item["food_name"] and item["cuisine"] for item in snapshot)

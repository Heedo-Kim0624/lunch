import json
from datetime import timedelta
from io import StringIO

import pytest
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient

from recommendations.models import Food, UserFoodEvent
from recommendations.services.collaborative import invalidate_collaborative_cache


@pytest.fixture(autouse=True)
def clear_graph_cache() -> None:
    invalidate_collaborative_cache()


@pytest.mark.django_db
def test_public_graph_exposes_food_relationships_without_user_identities() -> None:
    foods = [
        Food.objects.create(
            canonical_name=name,
            family=family,
            cuisine="한식",
            attributes={
                "spicy": spicy,
                "broth": broth,
                "light": 0.4,
                "protein": 0.7,
                "adventurous": 0.3,
                "cold": 0.0,
                "familiar": 0.9,
                "popularity": 0.8,
            },
        )
        for name, family, spicy, broth in (
            ("치킨", "치킨", 0.2, 0.0),
            ("라면", "라면", 0.7, 0.8),
            ("닭곰탕", "국밥", 0.1, 0.9),
        )
    ]
    for index in range(5):
        for food in foods[:2]:
            UserFoodEvent.objects.create(
                anonymous_id=f"account-{index}",
                food=food,
                event_type=UserFoodEvent.EventType.ATE,
                event_time=timezone.now() - timedelta(days=index),
            )

    response = APIClient().get(reverse("recommendation-graph"))

    assert response.status_code == 200
    payload = response.json()
    serialized = json.dumps(payload)
    assert payload["policy_version"] == "rules-v4"
    assert payload["privacy"]["minimum_shared_selectors"] == 5
    assert len(payload["nodes"]) == 3
    assert payload["edges"]
    assert any(edge["relation"] in {"collaborative", "hybrid"} for edge in payload["edges"])
    assert "account-" not in serialized
    assert "anonymous_id" not in serialized


@pytest.mark.django_db
def test_graph_still_has_content_edges_before_shared_history_exists() -> None:
    for index in range(3):
        Food.objects.create(
            canonical_name=f"메뉴-{index}",
            family=f"음식군-{index}",
            cuisine="한식",
            attributes={
                "spicy": 0.2,
                "broth": 0.7,
                "light": 0.5,
                "protein": 0.6,
                "adventurous": 0.3,
                "cold": 0.0,
                "familiar": 0.8,
                "popularity": 0.7,
            },
        )

    response = APIClient().get(reverse("recommendation-graph"))

    assert response.status_code == 200
    assert response.json()["stats"]["mode"] == "content_only"
    assert any(edge["relation"] == "content" for edge in response.json()["edges"])


@pytest.mark.django_db
def test_public_selector_counts_are_bucketed_instead_of_exact() -> None:
    food_a = Food.objects.create(
        canonical_name="치킨",
        family="치킨",
        attributes={"protein": 0.9, "popularity": 0.8},
    )
    food_b = Food.objects.create(
        canonical_name="라면",
        family="라면",
        attributes={"broth": 0.9, "popularity": 0.8},
    )
    for index in range(7):
        for food in (food_a, food_b):
            UserFoodEvent.objects.create(
                anonymous_id=f"account-{index}",
                food=food,
                event_type=UserFoodEvent.EventType.ATE,
            )
    invalidate_collaborative_cache()

    payload = APIClient().get(reverse("recommendation-graph")).json()
    shared_edge = next(edge for edge in payload["edges"] if edge["relation"] != "content")

    assert shared_edge["selector_count"] == 5
    assert payload["stats"]["contributing_accounts"] == 5


@pytest.mark.django_db
def test_graph_audit_command_is_reproducible_without_user_history() -> None:
    Food.objects.create(
        canonical_name="비빔밥",
        family="비빔밥",
        cuisine="한식",
        attributes={"familiar": 0.9, "popularity": 0.9},
    )
    output = StringIO()

    call_command("audit_recommendation_graph", stdout=output)

    report = output.getvalue()
    assert "Recommendation graph audit passed" in report
    assert "account_profiles=0" in report
    assert "identity_data_exposed=false" in report

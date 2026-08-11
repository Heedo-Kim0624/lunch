import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from recommendations.models import (
    Food,
    RecommendationExposure,
    RecommendationSession,
    UserFoodEvent,
)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def foods() -> list[Food]:
    return [
        Food.objects.create(
            canonical_name="순두부찌개",
            family="찌개",
            description="매콤하고 따뜻한 두부 국물 요리",
            attributes={"broth": 1.0, "spicy": 0.7, "popularity": 0.8},
        ),
        Food.objects.create(
            canonical_name="비빔밥",
            family="비빔밥",
            description="채소와 고추장을 비벼 먹는 밥 요리",
            attributes={"broth": 0.0, "spicy": 0.4, "popularity": 0.9},
        ),
    ]


@pytest.mark.django_db
def test_health_endpoint(api_client: APIClient) -> None:
    response = api_client.get(reverse("health"))

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.django_db
def test_recommendation_creates_session_and_exposure(
    api_client: APIClient, foods: list[Food]
) -> None:
    response = api_client.post(
        reverse("recommendation-create"),
        {
            "anonymous_id": "device-a",
            "context": {"meal_type": "LUNCH", "weather": "RAIN", "temperature": 24},
        },
        format="json",
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["food"]["name"] in {food.canonical_name for food in foods}
    assert payload["policy_version"] == "rules-v2"
    assert payload["reason"] == (
        "아직 선택 기록이 없어 인기와 메뉴 다양성을 기준으로 고른 첫 후보예요."
    )
    assert RecommendationSession.objects.count() == 1
    assert RecommendationExposure.objects.count() == 1
    session = RecommendationSession.objects.get()
    assert session.candidate_snapshot
    assert sum(
        candidate["selection_probability"] for candidate in session.candidate_snapshot
    ) == pytest.approx(1)


@pytest.mark.django_db
def test_feedback_is_linked_to_owned_exposure(api_client: APIClient, foods: list[Food]) -> None:
    recommendation = api_client.post(
        reverse("recommendation-create"),
        {"anonymous_id": "device-a", "context": {}},
        format="json",
    ).json()

    response = api_client.post(
        reverse(
            "recommendation-feedback",
            kwargs={"exposure_id": recommendation["recommendation_id"]},
        ),
        {"anonymous_id": "device-a", "event_type": "ACCEPTED"},
        format="json",
    )

    assert response.status_code == 201
    event = UserFoodEvent.objects.get()
    assert event.event_type == UserFoodEvent.EventType.ACCEPTED
    assert event.exposure_id == recommendation["recommendation_id"]


@pytest.mark.django_db
def test_duplicate_feedback_is_idempotent(api_client: APIClient, foods: list[Food]) -> None:
    recommendation = api_client.post(
        reverse("recommendation-create"),
        {"anonymous_id": "device-a", "context": {}},
        format="json",
    ).json()
    url = reverse(
        "recommendation-feedback",
        kwargs={"exposure_id": recommendation["recommendation_id"]},
    )
    payload = {"anonymous_id": "device-a", "event_type": "ACCEPTED"}

    first = api_client.post(url, payload, format="json")
    second = api_client.post(url, payload, format="json")

    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["event_id"] == second.json()["event_id"]
    assert UserFoodEvent.objects.count() == 1


@pytest.mark.django_db
def test_feedback_rejects_anonymous_id_mismatch(api_client: APIClient, foods: list[Food]) -> None:
    recommendation = api_client.post(
        reverse("recommendation-create"),
        {"anonymous_id": "device-a", "context": {}},
        format="json",
    ).json()

    response = api_client.post(
        reverse(
            "recommendation-feedback",
            kwargs={"exposure_id": recommendation["recommendation_id"]},
        ),
        {"anonymous_id": "device-b", "event_type": "ACCEPTED"},
        format="json",
    )

    assert response.status_code == 404
    assert UserFoodEvent.objects.count() == 0

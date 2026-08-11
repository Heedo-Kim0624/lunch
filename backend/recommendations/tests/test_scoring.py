from datetime import timedelta

import pytest
from django.utils import timezone

from recommendations.models import Food, UserFoodEvent
from recommendations.services.scoring import score_food


@pytest.mark.django_db
def test_rain_context_favors_broth_food() -> None:
    soup = Food.objects.create(
        canonical_name="순두부찌개",
        family="찌개",
        attributes={"broth": 1.0, "popularity": 0.7},
    )
    rice = Food.objects.create(
        canonical_name="비빔밥",
        family="비빔밥",
        attributes={"broth": 0.0, "popularity": 0.7},
    )

    soup_score = score_food(soup, {"weather": "RAIN"}, [], timezone.now())
    rice_score = score_food(rice, {"weather": "RAIN"}, [], timezone.now())

    assert soup_score.context > rice_score.context
    assert soup_score.total > rice_score.total


@pytest.mark.django_db
def test_recent_same_food_receives_repetition_penalty() -> None:
    food = Food.objects.create(
        canonical_name="제육볶음",
        family="돼지고기 볶음",
        attributes={"spicy": 0.8, "popularity": 0.8},
    )
    now = timezone.now()
    event = UserFoodEvent.objects.create(
        anonymous_id="device-a",
        food=food,
        event_type=UserFoodEvent.EventType.ATE,
        event_time=now - timedelta(days=1),
    )

    repeated = score_food(food, {}, [event], now)
    fresh = score_food(food, {}, [], now)

    assert repeated.repetition_penalty > 0
    assert repeated.total < fresh.total


@pytest.mark.django_db
def test_explicit_positive_history_increases_matching_attribute_score() -> None:
    spicy_food = Food.objects.create(
        canonical_name="마라탕",
        family="마라",
        attributes={"spicy": 1.0, "adventurous": 0.8, "popularity": 0.5},
    )
    liked_food = Food.objects.create(
        canonical_name="닭갈비",
        family="닭고기 볶음",
        attributes={"spicy": 0.9, "adventurous": 0.4, "popularity": 0.7},
    )
    now = timezone.now()
    event = UserFoodEvent.objects.create(
        anonymous_id="device-a",
        food=liked_food,
        event_type=UserFoodEvent.EventType.FAVORITED,
        event_time=now - timedelta(days=3),
    )

    personalized = score_food(spicy_food, {}, [event], now)
    cold_start = score_food(spicy_food, {}, [], now)

    assert personalized.preference > cold_start.preference

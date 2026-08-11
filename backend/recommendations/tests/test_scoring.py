from datetime import timedelta

import pytest
from django.utils import timezone

from recommendations.models import Food, UserFoodEvent
from recommendations.services.collaborative import invalidate_collaborative_cache
from recommendations.services.scoring import create_recommendation, score_food


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


def test_collaborative_signal_increases_the_hybrid_score() -> None:
    food = Food(
        canonical_name="라면",
        family="라면",
        attributes={"popularity": 0.5},
    )
    now = timezone.now()

    related = score_food(food, {}, [], now, collaborative=0.8)
    unrelated = score_food(food, {}, [], now, collaborative=0.0)

    assert related.collaborative == 0.8
    assert related.total > unrelated.total


@pytest.mark.django_db
def test_disliked_food_is_removed_before_recommendation() -> None:
    disliked = Food.objects.create(
        canonical_name="싫어하는 메뉴",
        family="싫어요",
        attributes={"popularity": 1.0},
    )
    allowed = Food.objects.create(
        canonical_name="먹을 수 있는 메뉴",
        family="허용",
        attributes={"popularity": 0.1},
    )
    UserFoodEvent.objects.create(
        anonymous_id="device-a",
        food=disliked,
        event_type=UserFoodEvent.EventType.DISLIKED,
    )

    exposure = create_recommendation("device-a", {})

    assert exposure.food_id == allowed.id
    assert exposure.session.policy_version == "rules-v4"
    assert "collaborative" in exposure.score_breakdown


@pytest.mark.django_db
def test_shared_account_choices_flow_into_the_recommendation_reason() -> None:
    chicken = Food.objects.create(
        canonical_name="치킨",
        family="치킨",
        staple_types=["bread"],
        attributes={"protein": 0.9, "popularity": 0.8},
    )
    ramen = Food.objects.create(
        canonical_name="라면",
        family="라면",
        staple_types=["noodle"],
        attributes={"broth": 0.8, "popularity": 0.7},
    )
    for index in range(5):
        for food in (chicken, ramen):
            UserFoodEvent.objects.create(
                anonymous_id=f"account-{index}",
                food=food,
                event_type=UserFoodEvent.EventType.ATE,
            )
    UserFoodEvent.objects.create(
        anonymous_id="device-b",
        food=chicken,
        event_type=UserFoodEvent.EventType.ACCEPTED,
    )
    invalidate_collaborative_cache()

    exposure = create_recommendation(
        "device-b",
        {},
        filters={"staples": ["noodle"]},
    )

    assert exposure.food_id == ramen.id
    assert exposure.score_breakdown["collaborative"] > 0
    assert exposure.reason == "비슷한 선택을 한 사람들이 함께 고른 메뉴예요."

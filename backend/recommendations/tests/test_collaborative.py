from datetime import timedelta
from types import SimpleNamespace

from django.utils import timezone

from recommendations.models import UserFoodEvent
from recommendations.services.collaborative import (
    MIN_COLLABORATIVE_SUPPORT,
    build_collaborative_snapshot,
    collaborative_candidate_scores,
)


def event(
    identity: str,
    food_id: int,
    event_type: str = UserFoodEvent.EventType.ATE,
    *,
    days_ago: int = 0,
) -> SimpleNamespace:
    return SimpleNamespace(
        anonymous_id=identity,
        food_id=food_id,
        event_type=event_type,
        event_time=timezone.now() - timedelta(days=days_ago),
    )


def test_five_distinct_accounts_create_a_private_food_affinity() -> None:
    events = [
        item
        for index in range(MIN_COLLABORATIVE_SUPPORT)
        for item in (
            event(f"account-{index}", 1),
            event(f"account-{index}", 2),
        )
    ]

    snapshot = build_collaborative_snapshot(events, timezone.now())

    assert snapshot.contributing_users == MIN_COLLABORATIVE_SUPPORT
    assert len(snapshot.edges) == 1
    edge = snapshot.edges[0]
    assert (edge.food_a_id, edge.food_b_id) == (1, 2)
    assert edge.selector_count == MIN_COLLABORATIVE_SUPPORT
    assert 0 < edge.similarity <= 1


def test_affinity_requires_five_accounts_and_ignores_anonymous_devices() -> None:
    events = [
        item
        for index in range(MIN_COLLABORATIVE_SUPPORT - 1)
        for item in (
            event(f"account-{index}", 1),
            event(f"account-{index}", 2),
        )
    ]
    events.extend((event("device-a", 1), event("device-a", 2)))

    snapshot = build_collaborative_snapshot(events, timezone.now())

    assert snapshot.contributing_users == MIN_COLLABORATIVE_SUPPORT - 1
    assert snapshot.edges == ()


def test_repeated_events_do_not_inflate_distinct_selector_support() -> None:
    events = [
        item
        for index in range(MIN_COLLABORATIVE_SUPPORT)
        for item in (
            event(f"account-{index}", 1),
            event(f"account-{index}", 1, UserFoodEvent.EventType.FAVORITED),
            event(f"account-{index}", 2),
        )
    ]

    snapshot = build_collaborative_snapshot(events, timezone.now())

    assert snapshot.edges[0].selector_count == MIN_COLLABORATIVE_SUPPORT


def test_shared_chicken_history_can_raise_ramen_for_a_new_user() -> None:
    training_events = [
        item
        for index in range(MIN_COLLABORATIVE_SUPPORT)
        for item in (
            event(f"account-{index}", 1),
            event(f"account-{index}", 2),
        )
    ]
    snapshot = build_collaborative_snapshot(training_events, timezone.now())
    current_history = [event("account-99", 1)]

    scores = collaborative_candidate_scores(
        current_history,
        snapshot,
        candidate_ids={2, 3},
        now=timezone.now(),
    )

    assert scores[2] > 0
    assert 3 not in scores


def test_negative_net_history_does_not_seed_collaborative_recommendations() -> None:
    training_events = [
        item
        for index in range(MIN_COLLABORATIVE_SUPPORT)
        for item in (
            event(f"account-{index}", 1),
            event(f"account-{index}", 2),
        )
    ]
    snapshot = build_collaborative_snapshot(training_events, timezone.now())
    current_history = [
        event("account-99", 1, UserFoodEvent.EventType.ACCEPTED),
        event("account-99", 1, UserFoodEvent.EventType.DISLIKED),
    ]

    scores = collaborative_candidate_scores(
        current_history,
        snapshot,
        candidate_ids={2},
        now=timezone.now(),
    )

    assert scores == {}


def test_cosine_similarity_reduces_ubiquitous_food_popularity_bias() -> None:
    events = [event(f"account-{index}", 1) for index in range(10)]
    for index in range(MIN_COLLABORATIVE_SUPPORT):
        events.extend(
            (
                event(f"account-{index}", 2),
                event(f"account-{index}", 3),
            )
        )

    snapshot = build_collaborative_snapshot(events, timezone.now())
    similarities = {
        (edge.food_a_id, edge.food_b_id): edge.similarity for edge in snapshot.edges
    }

    assert similarities[(2, 3)] > similarities[(1, 2)]

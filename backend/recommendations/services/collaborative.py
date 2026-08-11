from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from math import sqrt
from typing import Protocol

from django.core.cache import cache
from django.utils import timezone

from recommendations.models import UserFoodEvent

MIN_COLLABORATIVE_SUPPORT = 5
AUTHENTICATED_IDENTITY_PREFIX = "account-"
COLLABORATIVE_WINDOW_DAYS = 365
COLLABORATIVE_HALF_LIFE_DAYS = 90
MAX_PROFILE_FOODS = 30
SIMILARITY_SHRINKAGE = 5
COLLABORATIVE_CACHE_TTL = 300
COLLABORATIVE_CACHE_KEY = "recommendations:collaborative:v1"
GRAPH_CACHE_KEY = "recommendations:graph:v1"

COLLABORATIVE_EVENT_WEIGHTS = {
    UserFoodEvent.EventType.ACCEPTED: 1.0,
    UserFoodEvent.EventType.ATE: 1.5,
    UserFoodEvent.EventType.FAVORITED: 2.0,
    UserFoodEvent.EventType.REJECTED: -1.0,
    UserFoodEvent.EventType.REROLLED: -0.25,
    UserFoodEvent.EventType.DISLIKED: -2.0,
}


class EventLike(Protocol):
    anonymous_id: str
    food_id: int
    event_type: str
    event_time: datetime


@dataclass(frozen=True)
class CollaborativeEdge:
    food_a_id: int
    food_b_id: int
    similarity: float
    selector_count: int


@dataclass(frozen=True)
class CollaborativeSnapshot:
    edges: tuple[CollaborativeEdge, ...]
    item_support: dict[int, int]
    contributing_users: int
    generated_at: datetime


def _decayed_weight(event: EventLike, now: datetime) -> float:
    base_weight = COLLABORATIVE_EVENT_WEIGHTS.get(event.event_type, 0.0)
    if base_weight == 0:
        return 0.0
    age_days = max(0.0, (now - event.event_time).total_seconds() / 86_400)
    return base_weight * (0.5 ** (age_days / COLLABORATIVE_HALF_LIFE_DAYS))


def _positive_profiles(
    events: Iterable[EventLike],
    now: datetime,
    *,
    accounts_only: bool,
) -> dict[str, dict[int, float]]:
    raw_profiles: dict[str, dict[int, float]] = defaultdict(lambda: defaultdict(float))
    for event in events:
        if accounts_only and not event.anonymous_id.startswith(AUTHENTICATED_IDENTITY_PREFIX):
            continue
        raw_profiles[event.anonymous_id][event.food_id] += _decayed_weight(event, now)

    profiles: dict[str, dict[int, float]] = {}
    for identity, foods in raw_profiles.items():
        positive = [
            (food_id, min(2.0, score))
            for food_id, score in foods.items()
            if score > 0
        ]
        positive.sort(key=lambda item: (-item[1], item[0]))
        if positive:
            profiles[identity] = dict(positive[:MAX_PROFILE_FOODS])
    return profiles


def build_collaborative_snapshot(
    events: Iterable[EventLike], now: datetime | None = None
) -> CollaborativeSnapshot:
    generated_at = now or timezone.now()
    profiles = _positive_profiles(events, generated_at, accounts_only=True)
    item_norms: dict[int, float] = defaultdict(float)
    item_support: dict[int, int] = defaultdict(int)
    pair_weights: dict[tuple[int, int], float] = defaultdict(float)
    pair_support: dict[tuple[int, int], int] = defaultdict(int)

    for profile in profiles.values():
        ordered = sorted(profile.items())
        for food_id, weight in ordered:
            item_norms[food_id] += weight**2
            item_support[food_id] += 1
        for index, (food_a_id, weight_a) in enumerate(ordered):
            for food_b_id, weight_b in ordered[index + 1 :]:
                pair = (food_a_id, food_b_id)
                pair_weights[pair] += weight_a * weight_b
                pair_support[pair] += 1

    edges: list[CollaborativeEdge] = []
    for (food_a_id, food_b_id), selector_count in pair_support.items():
        if selector_count < MIN_COLLABORATIVE_SUPPORT:
            continue
        denominator = sqrt(item_norms[food_a_id] * item_norms[food_b_id])
        if denominator <= 0:
            continue
        cosine = pair_weights[(food_a_id, food_b_id)] / denominator
        confidence = selector_count / (selector_count + SIMILARITY_SHRINKAGE)
        edges.append(
            CollaborativeEdge(
                food_a_id=food_a_id,
                food_b_id=food_b_id,
                similarity=round(max(0.0, min(1.0, cosine * confidence)), 4),
                selector_count=selector_count,
            )
        )
    edges.sort(key=lambda edge: (-edge.similarity, -edge.selector_count, edge.food_a_id))
    return CollaborativeSnapshot(
        edges=tuple(edges),
        item_support=dict(item_support),
        contributing_users=len(profiles),
        generated_at=generated_at,
    )


def get_collaborative_snapshot() -> CollaborativeSnapshot:
    cached = cache.get(COLLABORATIVE_CACHE_KEY)
    if isinstance(cached, CollaborativeSnapshot):
        return cached

    cutoff = timezone.now() - timedelta(days=COLLABORATIVE_WINDOW_DAYS)
    events = list(
        UserFoodEvent.objects.filter(
            anonymous_id__startswith=AUTHENTICATED_IDENTITY_PREFIX,
            event_time__gte=cutoff,
        ).only("anonymous_id", "food_id", "event_type", "event_time")
    )
    snapshot = build_collaborative_snapshot(events)
    cache.set(COLLABORATIVE_CACHE_KEY, snapshot, COLLABORATIVE_CACHE_TTL)
    return snapshot


def collaborative_candidate_scores(
    history: Sequence[EventLike],
    snapshot: CollaborativeSnapshot,
    *,
    candidate_ids: set[int],
    now: datetime | None = None,
) -> dict[int, float]:
    if not history or not snapshot.edges or not candidate_ids:
        return {}
    generated_at = now or timezone.now()
    profiles = _positive_profiles(history, generated_at, accounts_only=False)
    if not profiles:
        return {}
    current_profile = next(iter(profiles.values()))
    raw_scores: dict[int, float] = defaultdict(float)
    normalizers: dict[int, float] = defaultdict(float)

    for edge in snapshot.edges:
        if edge.food_a_id in current_profile and edge.food_b_id in candidate_ids:
            weight = current_profile[edge.food_a_id]
            raw_scores[edge.food_b_id] += edge.similarity * weight
            normalizers[edge.food_b_id] += weight
        if edge.food_b_id in current_profile and edge.food_a_id in candidate_ids:
            weight = current_profile[edge.food_b_id]
            raw_scores[edge.food_a_id] += edge.similarity * weight
            normalizers[edge.food_a_id] += weight

    return {
        food_id: round(score / normalizers[food_id], 4)
        for food_id, score in raw_scores.items()
        if normalizers[food_id] > 0
    }


def invalidate_collaborative_cache() -> None:
    cache.delete_many((COLLABORATIVE_CACHE_KEY, GRAPH_CACHE_KEY))

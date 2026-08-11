from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from math import exp
from random import Random, SystemRandom

from django.db import transaction
from django.utils import timezone

from recommendations.filters import filter_foods, normalize_filters
from recommendations.models import (
    Food,
    RecommendationExposure,
    RecommendationSession,
    UserFoodEvent,
)

POLICY_VERSION = "rules-v3"
CANDIDATE_POOL_SIZE = 24
MAX_FOODS_PER_FAMILY = 2
SOFTMAX_TEMPERATURE = 0.18
EVENT_WEIGHTS = {
    UserFoodEvent.EventType.ACCEPTED: 2.0,
    UserFoodEvent.EventType.ATE: 3.0,
    UserFoodEvent.EventType.REJECTED: -2.0,
    UserFoodEvent.EventType.REROLLED: -0.5,
    UserFoodEvent.EventType.FAVORITED: 5.0,
    UserFoodEvent.EventType.DISLIKED: -5.0,
}
PREFERENCE_ATTRIBUTES = (
    "spicy",
    "broth",
    "light",
    "protein",
    "adventurous",
    "cold",
    "familiar",
)


class NoMatchingFoodsError(Exception):
    """Raised when active foods exist but none satisfy the selected filters."""


@dataclass(frozen=True)
class ScoreBreakdown:
    preference: float
    context: float
    novelty: float
    popularity: float
    repetition_penalty: float
    total: float

    def as_dict(self) -> dict[str, float]:
        return {key: round(value, 4) for key, value in asdict(self).items()}


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _attribute(food: Food, name: str, default: float = 0.0) -> float:
    value = food.attributes.get(name, default)
    return _clamp(float(value)) if isinstance(value, int | float) else default


def _preference_score(
    food: Food,
    events: Sequence[UserFoodEvent],
    now: datetime,
) -> float:
    if not events:
        return 0.5

    weighted_preferences: dict[str, float] = {name: 0.0 for name in PREFERENCE_ATTRIBUTES}
    normalizers: dict[str, float] = {name: 0.0 for name in PREFERENCE_ATTRIBUTES}

    for event in events:
        base_weight = EVENT_WEIGHTS.get(event.event_type, 0.0)
        if base_weight == 0:
            continue
        age_days = max(0.0, (now - event.event_time).total_seconds() / 86_400)
        weight = base_weight * (0.5 ** (age_days / 45))
        for name in PREFERENCE_ATTRIBUTES:
            value = _attribute(event.food, name)
            weighted_preferences[name] += value * weight
            normalizers[name] += abs(weight)

    candidate_weight = 0.0
    candidate_total = 0.0
    for name in PREFERENCE_ATTRIBUTES:
        candidate_value = _attribute(food, name)
        if candidate_value <= 0 or normalizers[name] <= 0:
            continue
        learned = weighted_preferences[name] / normalizers[name]
        learned_unit = _clamp((learned + 1) / 2)
        candidate_total += learned_unit * candidate_value
        candidate_weight += candidate_value

    return candidate_total / candidate_weight if candidate_weight else 0.5


def _context_score(food: Food, context: dict[str, object]) -> float:
    score = 0.5
    weather = str(context.get("weather", "")).upper()
    temperature = context.get("temperature")

    if weather == "RAIN":
        score += 0.35 * _attribute(food, "broth")
        score -= 0.1 * _attribute(food, "cold")

    if isinstance(temperature, int | float):
        if temperature >= 28:
            score += 0.3 * _attribute(food, "cold")
            score += 0.1 * _attribute(food, "light")
        elif temperature <= 10:
            score += 0.25 * _attribute(food, "broth")

    return _clamp(score)


def _novelty_score(food: Food, events: Sequence[UserFoodEvent]) -> float:
    meaningful_events = {
        UserFoodEvent.EventType.ACCEPTED,
        UserFoodEvent.EventType.ATE,
        UserFoodEvent.EventType.FAVORITED,
    }
    count = sum(
        1 for event in events if event.food_id == food.id and event.event_type in meaningful_events
    )
    return 1 / (1 + count)


def _repetition_penalty(
    food: Food,
    events: Sequence[UserFoodEvent],
    now: datetime,
) -> float:
    repeated_events = [
        event
        for event in events
        if event.food_id == food.id
        and event.event_type
        in {
            UserFoodEvent.EventType.ACCEPTED,
            UserFoodEvent.EventType.ATE,
            UserFoodEvent.EventType.FAVORITED,
        }
    ]
    if not repeated_events:
        return 0.0

    latest = max(repeated_events, key=lambda event: event.event_time)
    age_days = max(0.0, (now - latest.event_time).total_seconds() / 86_400)
    if age_days <= 2:
        return 0.45
    if age_days <= 7:
        return 0.3
    if age_days <= 14:
        return 0.15
    return 0.0


def score_food(
    food: Food,
    context: dict[str, object],
    events: Sequence[UserFoodEvent],
    now: datetime,
) -> ScoreBreakdown:
    preference = _preference_score(food, events, now)
    context_score = _context_score(food, context)
    novelty = _novelty_score(food, events)
    popularity = _attribute(food, "popularity", 0.5)
    repetition_penalty = _repetition_penalty(food, events, now)
    total = max(
        0.0,
        0.45 * preference
        + 0.2 * context_score
        + 0.15 * novelty
        + 0.2 * popularity
        - repetition_penalty,
    )
    return ScoreBreakdown(
        preference=preference,
        context=context_score,
        novelty=novelty,
        popularity=popularity,
        repetition_penalty=repetition_penalty,
        total=total,
    )


def _softmax_probabilities(
    scores: list[float], temperature: float = SOFTMAX_TEMPERATURE
) -> list[float]:
    maximum = max(scores)
    weights = [exp((score - maximum) / temperature) for score in scores]
    total = sum(weights)
    return [weight / total for weight in weights]


def _diverse_candidate_pool(
    scored: list[tuple[Food, ScoreBreakdown]],
    limit: int = CANDIDATE_POOL_SIZE,
) -> list[tuple[Food, ScoreBreakdown]]:
    selected: list[tuple[Food, ScoreBreakdown]] = []
    selected_ids: set[int] = set()
    family_counts: dict[str, int] = {}

    # Fill one slot per family before allowing a second slot from any family.
    for family_limit in range(1, MAX_FOODS_PER_FAMILY + 1):
        for candidate in scored:
            food, _ = candidate
            if food.id in selected_ids:
                continue
            family_count = family_counts.get(food.family, 0)
            if family_count >= family_limit:
                continue
            selected.append(candidate)
            selected_ids.add(food.id)
            family_counts[food.family] = family_count + 1
            if len(selected) == limit:
                return selected

    # Small or unusually concentrated catalogs still need a full pool.
    for candidate in scored:
        if candidate[0].id in selected_ids:
            continue
        selected.append(candidate)
        if len(selected) == min(limit, len(scored)):
            break
    return selected


def _sample_index(probabilities: list[float], rng: Random | SystemRandom) -> int:
    threshold = rng.random()
    cumulative = 0.0
    for index, probability in enumerate(probabilities):
        cumulative += probability
        if threshold <= cumulative:
            return index
    return len(probabilities) - 1


def _recommendation_reason(
    food: Food,
    context: dict[str, object],
    score: ScoreBreakdown,
    *,
    has_history: bool,
    has_filters: bool = False,
) -> str:
    if not has_history:
        if has_filters:
            return "선택한 조건에 맞는 메뉴 중 인기와 다양성을 기준으로 고른 첫 후보예요."
        return "아직 선택 기록이 없어 인기와 메뉴 다양성을 기준으로 고른 첫 후보예요."

    weather = str(context.get("weather", "")).upper()
    temperature = context.get("temperature")
    if weather == "RAIN" and _attribute(food, "broth") >= 0.65:
        return "비 오는 날에 잘 맞는 따뜻한 국물 메뉴예요."
    if (
        isinstance(temperature, int | float)
        and temperature >= 28
        and _attribute(food, "cold") >= 0.65
    ):
        return "더운 날 부담을 덜어 줄 시원한 메뉴예요."
    if score.preference >= 0.65:
        return "지금까지 남긴 선택과 비슷한 결을 가진 메뉴예요."
    if score.novelty >= 0.9:
        if _attribute(food, "familiar") >= 0.65:
            return "최근 선택과 겹치지 않는 익숙한 점심 후보예요."
        return "최근 선택과 겹치지 않는 새로운 점심 후보예요."
    return "취향과 최근 중복을 함께 고려한 오늘의 후보예요."


@transaction.atomic
def create_recommendation(
    anonymous_id: str,
    context: dict[str, object],
    filters: dict[str, object] | None = None,
    rng: Random | SystemRandom | None = None,
) -> RecommendationExposure:
    active_foods = list(Food.objects.filter(is_active=True, is_lunch_suitable=True))
    if not active_foods:
        raise Food.DoesNotExist("No active lunch foods are available")
    normalized_filters = normalize_filters(filters)
    foods = filter_foods(active_foods, normalized_filters)
    if not foods:
        raise NoMatchingFoodsError("No foods match the selected filters")

    now = timezone.now()
    history = list(
        UserFoodEvent.objects.filter(anonymous_id=anonymous_id)
        .select_related("food")
        .order_by("-event_time")[:100]
    )
    random_source = rng or SystemRandom()
    scored = [(food, score_food(food, context, history, now)) for food in foods]
    # Stable sorting after shuffling rotates equally scored foods within a family.
    random_source.shuffle(scored)
    scored.sort(key=lambda item: item[1].total, reverse=True)
    top_candidates = _diverse_candidate_pool(scored)
    probabilities = _softmax_probabilities([score.total for _, score in top_candidates])
    index = _sample_index(probabilities, random_source)
    food, score = top_candidates[index]
    candidate_snapshot = [
        {
            "food_id": candidate.id,
            "food_name": candidate.canonical_name,
            "family": candidate.family,
            "cuisine": candidate.cuisine,
            "staple_types": candidate.staple_types,
            "rank": rank,
            "total_score": round(candidate_score.total, 4),
            "selection_probability": round(probability, 6),
        }
        for rank, ((candidate, candidate_score), probability) in enumerate(
            zip(top_candidates, probabilities, strict=True),
            start=1,
        )
    ]

    session_context = dict(context)
    if normalized_filters:
        session_context["filters"] = normalized_filters

    session = RecommendationSession.objects.create(
        anonymous_id=anonymous_id,
        context=session_context,
        policy_version=POLICY_VERSION,
        candidate_count=len(scored),
        candidate_snapshot=candidate_snapshot,
    )
    return RecommendationExposure.objects.create(
        session=session,
        food=food,
        rank=index + 1,
        total_score=score.total,
        score_breakdown=score.as_dict(),
        selection_probability=probabilities[index],
        reason=_recommendation_reason(
            food,
            context,
            score,
            has_history=bool(history),
            has_filters=bool(normalized_filters),
        ),
    )

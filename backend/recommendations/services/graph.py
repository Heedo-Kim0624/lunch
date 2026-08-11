from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from math import sqrt

from django.core.cache import cache
from django.utils import timezone

from recommendations.filters import CUISINE_FILTERS, cuisine_group
from recommendations.models import Food
from recommendations.services.collaborative import (
    GRAPH_CACHE_KEY,
    MIN_COLLABORATIVE_SUPPORT,
    CollaborativeSnapshot,
    get_collaborative_snapshot,
)

GRAPH_NODE_LIMIT = 48
GRAPH_EDGE_LIMIT = 120
CONTENT_NEIGHBORS_PER_NODE = 2
CONTENT_SIMILARITY_THRESHOLD = 0.78
GRAPH_CACHE_TTL = 300
CONTENT_ATTRIBUTES = (
    "spicy",
    "broth",
    "light",
    "protein",
    "adventurous",
    "cold",
    "familiar",
)
PUBLIC_COUNT_BUCKETS = (5, 10, 25, 50, 100, 250, 500, 1_000)


def _attribute(food: Food, name: str) -> float:
    value = food.attributes.get(name, 0.0)
    return float(value) if isinstance(value, int | float) else 0.0


def _public_count(count: int) -> int:
    return max((bucket for bucket in PUBLIC_COUNT_BUCKETS if bucket <= count), default=0)


def _content_similarity(food_a: Food, food_b: Food) -> float:
    values_a = [_attribute(food_a, name) for name in CONTENT_ATTRIBUTES]
    values_b = [_attribute(food_b, name) for name in CONTENT_ATTRIBUTES]
    denominator = sqrt(sum(value**2 for value in values_a)) * sqrt(
        sum(value**2 for value in values_b)
    )
    if denominator <= 0:
        return 0.0
    return max(
        0.0,
        min(1.0, sum(a * b for a, b in zip(values_a, values_b, strict=True)) / denominator),
    )


def _select_graph_foods(
    foods: list[Food], snapshot: CollaborativeSnapshot
) -> list[Food]:
    by_id = {food.id: food for food in foods}
    selected: list[Food] = []
    selected_ids: set[int] = set()

    def add(food: Food | None) -> None:
        if food is None or food.id in selected_ids or len(selected) >= GRAPH_NODE_LIMIT:
            return
        selected.append(food)
        selected_ids.add(food.id)

    buckets: dict[str, list[Food]] = defaultdict(list)
    for food in foods:
        buckets[cuisine_group(food.cuisine)].append(food)
    for bucket in buckets.values():
        bucket.sort(key=lambda food: (-_attribute(food, "popularity"), food.canonical_name))

    for group in CUISINE_FILTERS:
        add(buckets[group][0] if buckets[group] else None)

    for edge in snapshot.edges:
        add(by_id.get(edge.food_a_id))
        add(by_id.get(edge.food_b_id))
        if len(selected) >= GRAPH_NODE_LIMIT // 2:
            break

    offsets = {group: 1 if buckets[group] else 0 for group in CUISINE_FILTERS}
    while len(selected) < min(GRAPH_NODE_LIMIT, len(foods)):
        added = False
        for group in CUISINE_FILTERS:
            bucket = buckets[group]
            offset = offsets[group]
            while offset < len(bucket) and bucket[offset].id in selected_ids:
                offset += 1
            offsets[group] = offset + 1
            if offset < len(bucket):
                add(bucket[offset])
                added = True
        if not added:
            break

    for food in sorted(foods, key=lambda item: item.canonical_name):
        add(food)
    return selected


def build_recommendation_graph(
    foods: list[Food],
    snapshot: CollaborativeSnapshot,
    generated_at: datetime | None = None,
) -> dict[str, object]:
    selected = _select_graph_foods(foods, snapshot)
    selected_ids = {food.id for food in selected}
    by_id = {food.id: food for food in selected}
    edges: dict[tuple[int, int], dict[str, object]] = {}

    for food in selected:
        similarities = sorted(
            (
                (_content_similarity(food, other), other)
                for other in selected
                if other.id != food.id
            ),
            key=lambda item: (-item[0], item[1].canonical_name),
        )
        for similarity, other in similarities[:CONTENT_NEIGHBORS_PER_NODE]:
            if similarity < CONTENT_SIMILARITY_THRESHOLD:
                continue
            pair = tuple(sorted((food.id, other.id)))
            edges[pair] = {
                "source": pair[0],
                "target": pair[1],
                "relation": "content",
                "similarity": round(similarity, 4),
                "content_similarity": round(similarity, 4),
                "collaborative_similarity": 0.0,
                "selector_count": 0,
            }

    for edge in snapshot.edges:
        if edge.food_a_id not in selected_ids or edge.food_b_id not in selected_ids:
            continue
        pair = (edge.food_a_id, edge.food_b_id)
        content = edges.get(pair)
        content_similarity = (
            float(content["content_similarity"])
            if content
            else round(_content_similarity(by_id[pair[0]], by_id[pair[1]]), 4)
        )
        edges[pair] = {
            "source": pair[0],
            "target": pair[1],
            "relation": (
                "hybrid"
                if content_similarity >= CONTENT_SIMILARITY_THRESHOLD
                else "collaborative"
            ),
            "similarity": max(content_similarity, edge.similarity),
            "content_similarity": content_similarity,
            "collaborative_similarity": edge.similarity,
            "selector_count": _public_count(edge.selector_count),
        }

    ordered_edges = sorted(
        edges.values(),
        key=lambda edge: (
            edge["relation"] == "content",
            -float(edge["similarity"]),
            int(edge["source"]),
        ),
    )[:GRAPH_EDGE_LIMIT]
    has_collaboration = any(edge["relation"] != "content" for edge in ordered_edges)
    visible_users = _public_count(snapshot.contributing_users)
    timestamp = generated_at or timezone.now()
    return {
        "policy_version": "rules-v4",
        "generated_at": timestamp.isoformat(),
        "nodes": [
            {
                "id": food.id,
                "name": food.canonical_name,
                "family": food.family,
                "cuisine": food.cuisine,
                "cuisine_group": cuisine_group(food.cuisine),
                "attributes": {
                    name: round(_attribute(food, name), 2) for name in CONTENT_ATTRIBUTES
                },
                "selector_count": (
                    _public_count(snapshot.item_support.get(food.id, 0))
                ),
            }
            for food in selected
        ],
        "edges": ordered_edges,
        "stats": {
            "mode": "hybrid" if has_collaboration else "content_only",
            "node_count": len(selected),
            "edge_count": len(ordered_edges),
            "contributing_accounts": visible_users,
        },
        "privacy": {
            "minimum_shared_selectors": MIN_COLLABORATIVE_SUPPORT,
            "identity_data_exposed": False,
        },
    }


def get_recommendation_graph() -> dict[str, object]:
    cached = cache.get(GRAPH_CACHE_KEY)
    if isinstance(cached, dict):
        return cached
    foods = list(Food.objects.filter(is_active=True, is_lunch_suitable=True))
    graph = build_recommendation_graph(foods, get_collaborative_snapshot())
    cache.set(GRAPH_CACHE_KEY, graph, GRAPH_CACHE_TTL)
    return graph

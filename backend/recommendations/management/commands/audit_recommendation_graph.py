import json
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from recommendations.models import Food, UserFoodEvent
from recommendations.services.collaborative import (
    COLLABORATIVE_WINDOW_DAYS,
    MIN_COLLABORATIVE_SUPPORT,
    build_collaborative_snapshot,
)
from recommendations.services.graph import (
    GRAPH_EDGE_LIMIT,
    GRAPH_NODE_LIMIT,
    build_recommendation_graph,
)


class Command(BaseCommand):
    help = "Audit privacy, bounds, and source integrity for the recommendation graph."

    def handle(self, *args: object, **options: object) -> None:
        now = timezone.now()
        cutoff = now - timedelta(days=COLLABORATIVE_WINDOW_DAYS)
        events = list(
            UserFoodEvent.objects.filter(
                anonymous_id__startswith="account-",
                event_time__gte=cutoff,
            ).only("anonymous_id", "food_id", "event_type", "event_time")
        )
        foods = list(Food.objects.filter(is_active=True, is_lunch_suitable=True))
        snapshot = build_collaborative_snapshot(events, now)
        graph = build_recommendation_graph(foods, snapshot, now)
        serialized = json.dumps(graph, ensure_ascii=False)
        errors: list[str] = []

        if len(graph["nodes"]) > GRAPH_NODE_LIMIT:
            errors.append("graph exceeds the node payload limit")
        if len(graph["edges"]) > GRAPH_EDGE_LIMIT:
            errors.append("graph exceeds the edge payload limit")
        if "account-" in serialized or "anonymous_id" in serialized:
            errors.append("graph payload exposes an identity field or value")
        if any(
            edge.selector_count < MIN_COLLABORATIVE_SUPPORT
            or not 0.0 <= edge.similarity <= 1.0
            for edge in snapshot.edges
        ):
            errors.append("collaborative edges violate support or similarity bounds")
        if any(
            edge["relation"] != "content"
            and int(edge["selector_count"]) < MIN_COLLABORATIVE_SUPPORT
            for edge in graph["edges"]
        ):
            errors.append("public collaborative edge is below the privacy threshold")

        if errors:
            raise CommandError("Recommendation graph audit failed:\n- " + "\n- ".join(errors))

        self.stdout.write(self.style.SUCCESS("Recommendation graph audit passed"))
        self.stdout.write(
            f"source_events={len(events)}, account_profiles={snapshot.contributing_users}, "
            f"qualified_collaborative_edges={len(snapshot.edges)}"
        )
        self.stdout.write(
            f"mode={graph['stats']['mode']}, nodes={len(graph['nodes'])}, "
            f"edges={len(graph['edges'])}, minimum_support={MIN_COLLABORATIVE_SUPPORT}"
        )
        self.stdout.write("identity_data_exposed=false")

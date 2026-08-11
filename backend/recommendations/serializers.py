from rest_framework import serializers

from recommendations.models import UserFoodEvent


class RecommendationFiltersSerializer(serializers.Serializer):
    temperature = serializers.ListField(
        child=serializers.ChoiceField(choices=("hot", "cold")),
        required=False,
        default=list,
        allow_empty=True,
        max_length=2,
    )
    staples = serializers.ListField(
        child=serializers.ChoiceField(choices=("rice", "bread", "noodle")),
        required=False,
        default=list,
        allow_empty=True,
        max_length=3,
    )
    cuisines = serializers.ListField(
        child=serializers.ChoiceField(
            choices=(
                "korean",
                "chinese",
                "western",
                "japanese",
                "southeast_asian",
                "other",
            )
        ),
        required=False,
        default=list,
        allow_empty=True,
        max_length=6,
    )
    spice = serializers.ListField(
        child=serializers.ChoiceField(choices=("spicy", "mild")),
        required=False,
        default=list,
        allow_empty=True,
        max_length=2,
    )

    def validate(self, attrs: dict[str, list[str]]) -> dict[str, list[str]]:
        return {key: list(dict.fromkeys(values)) for key, values in attrs.items()}


class RecommendationRequestSerializer(serializers.Serializer):
    anonymous_id = serializers.CharField(max_length=64, trim_whitespace=True)
    context = serializers.JSONField(required=False, default=dict)
    filters = RecommendationFiltersSerializer(required=False, default=dict)

    def validate_context(self, value: object) -> dict[str, object]:
        if not isinstance(value, dict):
            raise serializers.ValidationError("Context must be a JSON object.")
        return value


class FeedbackRequestSerializer(serializers.Serializer):
    anonymous_id = serializers.CharField(max_length=64, trim_whitespace=True)
    event_type = serializers.ChoiceField(choices=UserFoodEvent.EventType.choices)

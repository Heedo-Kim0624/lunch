from rest_framework import serializers

from recommendations.models import UserFoodEvent


class RecommendationRequestSerializer(serializers.Serializer):
    anonymous_id = serializers.CharField(max_length=64, trim_whitespace=True)
    context = serializers.JSONField(required=False, default=dict)

    def validate_context(self, value: object) -> dict[str, object]:
        if not isinstance(value, dict):
            raise serializers.ValidationError("Context must be a JSON object.")
        return value


class FeedbackRequestSerializer(serializers.Serializer):
    anonymous_id = serializers.CharField(max_length=64, trim_whitespace=True)
    event_type = serializers.ChoiceField(choices=UserFoodEvent.EventType.choices)

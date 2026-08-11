from django.http import Http404
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from recommendations.models import Food, RecommendationExposure, UserFoodEvent
from recommendations.serializers import FeedbackRequestSerializer, RecommendationRequestSerializer
from recommendations.services.scoring import create_recommendation


def request_identity(request: Request, anonymous_id: str) -> str:
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return f"account-{user.id}"
    return anonymous_id


class HealthView(APIView):
    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


class RecommendationCreateView(APIView):
    def post(self, request: Request) -> Response:
        serializer = RecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            exposure = create_recommendation(
                request_identity(request, serializer.validated_data["anonymous_id"]),
                serializer.validated_data["context"],
            )
        except Food.DoesNotExist:
            return Response(
                {"detail": "추천 가능한 점심 메뉴가 없습니다."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {
                "recommendation_id": exposure.id,
                "session_id": str(exposure.session_id),
                "policy_version": exposure.session.policy_version,
                "food": {
                    "id": exposure.food_id,
                    "name": exposure.food.canonical_name,
                    "family": exposure.food.family,
                    "description": exposure.food.description,
                },
                "reason": exposure.reason,
                "score_breakdown": exposure.score_breakdown,
            },
            status=status.HTTP_201_CREATED,
        )


class RecommendationFeedbackView(APIView):
    def post(self, request: Request, exposure_id: int) -> Response:
        serializer = FeedbackRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            anonymous_id = request_identity(request, serializer.validated_data["anonymous_id"])
            exposure = RecommendationExposure.objects.select_related("session", "food").get(
                id=exposure_id,
                session__anonymous_id=anonymous_id,
            )
        except RecommendationExposure.DoesNotExist as error:
            raise Http404 from error

        event, created = UserFoodEvent.objects.get_or_create(
            anonymous_id=anonymous_id,
            food=exposure.food,
            exposure=exposure,
            event_type=serializer.validated_data["event_type"],
            defaults={"context": exposure.session.context},
        )
        return Response(
            {"event_id": event.id, "event_type": event.event_type},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

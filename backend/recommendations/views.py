from django.http import Http404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from recommendations.models import Food, RecommendationExposure, UserFoodEvent
from recommendations.serializers import FeedbackRequestSerializer, RecommendationRequestSerializer
from recommendations.services.collaborative import (
    AUTHENTICATED_IDENTITY_PREFIX,
    invalidate_collaborative_cache,
)
from recommendations.services.graph import get_recommendation_graph
from recommendations.services.scoring import NoMatchingFoodsError, create_recommendation


def request_identity(request: Request, anonymous_id: str) -> str:
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        return f"{AUTHENTICATED_IDENTITY_PREFIX}{user.id}"
    if anonymous_id.startswith(AUTHENTICATED_IDENTITY_PREFIX):
        raise ValidationError(
            {"anonymous_id": ["This identifier prefix is reserved for authenticated accounts."]}
        )
    return anonymous_id


class HealthView(APIView):
    def get(self, request: Request) -> Response:
        return Response({"status": "ok"})


class RecommendationGraphView(APIView):
    def get(self, request: Request) -> Response:
        return Response(get_recommendation_graph())


class RecommendationCreateView(APIView):
    def post(self, request: Request) -> Response:
        serializer = RecommendationRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            exposure = create_recommendation(
                request_identity(request, serializer.validated_data["anonymous_id"]),
                serializer.validated_data["context"],
                serializer.validated_data["filters"],
            )
        except NoMatchingFoodsError:
            return Response(
                {
                    "code": "no_matching_foods",
                    "detail": "선택한 조건에 맞는 메뉴가 없어요. 조건을 조금 넓혀 주세요.",
                },
                status=status.HTTP_400_BAD_REQUEST,
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
                    "cuisine": exposure.food.cuisine,
                    "staple_types": exposure.food.staple_types,
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
        if created and anonymous_id.startswith(AUTHENTICATED_IDENTITY_PREFIX):
            invalidate_collaborative_cache()
        return Response(
            {"event_id": event.id, "event_type": event.event_type},
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

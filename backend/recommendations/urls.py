from django.urls import path

from recommendations.multi_views import (
    FoodSearchView,
    MultiRoomChoicesView,
    MultiRoomCreateView,
    MultiRoomDetailView,
    MultiRoomDrawView,
    MultiRoomJoinView,
)
from recommendations.views import (
    HealthView,
    RecommendationCreateView,
    RecommendationFeedbackView,
    RecommendationGraphView,
)

urlpatterns = [
    path("health", HealthView.as_view(), name="health"),
    path("foods", FoodSearchView.as_view(), name="food-search"),
    path("recommendation-graph", RecommendationGraphView.as_view(), name="recommendation-graph"),
    path("recommendations", RecommendationCreateView.as_view(), name="recommendation-create"),
    path(
        "recommendations/<int:exposure_id>/feedback",
        RecommendationFeedbackView.as_view(),
        name="recommendation-feedback",
    ),
    path("multi/rooms", MultiRoomCreateView.as_view(), name="multi-room-create"),
    path(
        "multi/rooms/<str:code>",
        MultiRoomDetailView.as_view(),
        name="multi-room-detail",
    ),
    path(
        "multi/rooms/<str:code>/join",
        MultiRoomJoinView.as_view(),
        name="multi-room-join",
    ),
    path(
        "multi/rooms/<str:code>/choices",
        MultiRoomChoicesView.as_view(),
        name="multi-room-choices",
    ),
    path(
        "multi/rooms/<str:code>/draw",
        MultiRoomDrawView.as_view(),
        name="multi-room-draw",
    ),
]

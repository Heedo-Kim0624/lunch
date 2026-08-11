from django.urls import path

from recommendations.views import (
    HealthView,
    RecommendationCreateView,
    RecommendationFeedbackView,
    RecommendationGraphView,
)

urlpatterns = [
    path("health", HealthView.as_view(), name="health"),
    path("recommendation-graph", RecommendationGraphView.as_view(), name="recommendation-graph"),
    path("recommendations", RecommendationCreateView.as_view(), name="recommendation-create"),
    path(
        "recommendations/<int:exposure_id>/feedback",
        RecommendationFeedbackView.as_view(),
        name="recommendation-feedback",
    ),
]

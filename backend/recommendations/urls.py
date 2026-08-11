from django.urls import path

from recommendations.views import HealthView, RecommendationCreateView, RecommendationFeedbackView

urlpatterns = [
    path("health", HealthView.as_view(), name="health"),
    path("recommendations", RecommendationCreateView.as_view(), name="recommendation-create"),
    path(
        "recommendations/<int:exposure_id>/feedback",
        RecommendationFeedbackView.as_view(),
        name="recommendation-feedback",
    ),
]

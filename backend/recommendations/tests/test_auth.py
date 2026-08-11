import pytest
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from recommendations.models import Food, RecommendationSession


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


def registration_payload(**overrides: str) -> dict[str, str]:
    payload = {
        "display_name": "점심러",
        "email": "Lunch@example.com",
        "password": "Tasty-lunch-2026!",
        "password_confirm": "Tasty-lunch-2026!",
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
def test_registration_creates_hashed_user_and_token(api_client: APIClient) -> None:
    response = api_client.post(reverse("auth-register"), registration_payload(), format="json")

    assert response.status_code == 201
    payload = response.json()
    user = User.objects.get()
    assert user.username == "lunch@example.com"
    assert user.email == "lunch@example.com"
    assert user.first_name == "점심러"
    assert user.check_password("Tasty-lunch-2026!")
    assert payload["token"] == Token.objects.get(user=user).key
    assert payload["user"] == {
        "id": user.id,
        "email": "lunch@example.com",
        "display_name": "점심러",
    }


@pytest.mark.django_db
def test_registration_rejects_duplicate_email(api_client: APIClient) -> None:
    first = api_client.post(reverse("auth-register"), registration_payload(), format="json")
    second = api_client.post(reverse("auth-register"), registration_payload(), format="json")

    assert first.status_code == 201
    assert second.status_code == 400
    assert User.objects.count() == 1


@pytest.mark.django_db
def test_registration_rejects_weak_or_mismatched_password(api_client: APIClient) -> None:
    weak = api_client.post(
        reverse("auth-register"),
        registration_payload(password="1234", password_confirm="1234"),
        format="json",
    )
    mismatch = api_client.post(
        reverse("auth-register"),
        registration_payload(password_confirm="Different-lunch-2026!"),
        format="json",
    )

    assert weak.status_code == 400
    assert mismatch.status_code == 400
    assert User.objects.count() == 0


@pytest.mark.django_db
def test_login_me_and_logout_lifecycle(api_client: APIClient) -> None:
    registered = api_client.post(
        reverse("auth-register"), registration_payload(), format="json"
    ).json()
    login = api_client.post(
        reverse("auth-login"),
        {"email": "LUNCH@example.com", "password": "Tasty-lunch-2026!"},
        format="json",
    )

    assert login.status_code == 200
    assert login.json()["token"] == registered["token"]

    api_client.credentials(HTTP_AUTHORIZATION=f"Token {registered['token']}")
    me = api_client.get(reverse("auth-me"))
    logout = api_client.post(reverse("auth-logout"), {}, format="json")
    after_logout = api_client.get(reverse("auth-me"))

    assert me.status_code == 200
    assert me.json()["user"]["email"] == "lunch@example.com"
    assert logout.status_code == 204
    assert after_logout.status_code == 401


@pytest.mark.django_db
def test_login_rejects_invalid_credentials(api_client: APIClient) -> None:
    api_client.post(reverse("auth-register"), registration_payload(), format="json")

    response = api_client.post(
        reverse("auth-login"),
        {"email": "lunch@example.com", "password": "wrong-password"},
        format="json",
    )

    assert response.status_code == 400
    assert "detail" in response.json()


@pytest.mark.django_db
def test_authenticated_recommendation_uses_server_owned_identity(api_client: APIClient) -> None:
    Food.objects.create(
        canonical_name="비빔밥",
        family="비빔밥·덮밥",
        attributes={"popularity": 0.8},
    )
    registered = api_client.post(
        reverse("auth-register"), registration_payload(), format="json"
    ).json()
    api_client.credentials(HTTP_AUTHORIZATION=f"Token {registered['token']}")

    response = api_client.post(
        reverse("recommendation-create"),
        {"anonymous_id": "spoofed-identity", "context": {}},
        format="json",
    )

    assert response.status_code == 201
    assert RecommendationSession.objects.get().anonymous_id == f"account-{registered['user']['id']}"

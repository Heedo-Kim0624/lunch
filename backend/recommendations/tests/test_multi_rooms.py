import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework.test import APIClient

from recommendations.models import (
    Food,
    MultiRoom,
    MultiRoomCustomFood,
    MultiRoomParticipant,
)


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def multi_foods() -> list[Food]:
    return [
        Food.objects.create(
            canonical_name=name,
            family="공유 테스트",
            cuisine="한식",
            attributes={"popularity": 0.5},
        )
        for name in ("치킨", "라면", "김밥", "돈가스")
    ]


def create_room(api_client: APIClient, nickname: str = "방장") -> dict[str, object]:
    response = api_client.post(reverse("multi-room-create"), {"nickname": nickname}, format="json")
    assert response.status_code == 201
    return response.json()


def join_room(api_client: APIClient, code: str, nickname: str) -> dict[str, object]:
    response = api_client.post(
        reverse("multi-room-join", kwargs={"code": code}),
        {"nickname": nickname},
        format="json",
    )
    assert response.status_code == 201
    return response.json()


def submit_choices(
    api_client: APIClient, code: str, token: str, food_ids: list[int]
) -> dict[str, object]:
    response = api_client.put(
        reverse("multi-room-choices", kwargs={"code": code}),
        {"food_ids": food_ids},
        format="json",
        HTTP_X_MULTI_TOKEN=token,
    )
    assert response.status_code == 200
    return response.json()


def submit_choice_items(
    api_client: APIClient,
    code: str,
    token: str,
    choices: list[dict[str, object]],
) -> dict[str, object]:
    response = api_client.put(
        reverse("multi-room-choices", kwargs={"code": code}),
        {"choices": choices},
        format="json",
        HTTP_X_MULTI_TOKEN=token,
    )
    assert response.status_code == 200
    return response.json()


@pytest.mark.django_db
def test_room_creation_returns_host_token_but_stores_only_digest(
    api_client: APIClient,
) -> None:
    payload = create_room(api_client)

    room = MultiRoom.objects.get(code=payload["room"]["code"])
    host = room.participants.get(is_host=True)
    assert len(payload["participant_token"]) >= 32
    assert host.token_digest != payload["participant_token"]
    assert payload["room"]["self"]["is_host"] is True
    assert "token" not in str(payload["room"]["participants"])


@pytest.mark.django_db
def test_guest_joins_without_an_account_and_adds_a_slot(api_client: APIClient) -> None:
    created = create_room(api_client)
    code = created["room"]["code"]

    joined = join_room(api_client, code, "민지")

    assert joined["room"]["participant_count"] == 2
    assert joined["room"]["self"]["is_host"] is False
    assert {person["nickname"] for person in joined["room"]["participants"]} == {
        "방장",
        "민지",
    }
    assert MultiRoomParticipant.objects.count() == 2


@pytest.mark.django_db
def test_public_room_state_never_exposes_any_participant_choices(
    api_client: APIClient, multi_foods: list[Food]
) -> None:
    created = create_room(api_client)
    code = created["room"]["code"]
    submit_choices(api_client, code, created["participant_token"], [multi_foods[0].id])

    response = api_client.get(reverse("multi-room-detail", kwargs={"code": code}))

    assert response.status_code == 200
    assert response.json()["room"]["self"] is None
    assert all("choices" not in person for person in response.json()["room"]["participants"])
    assert "participant_token" not in str(response.json())


@pytest.mark.django_db
def test_nicknames_are_case_insensitively_unique_per_room(api_client: APIClient) -> None:
    created = create_room(api_client, "LunchBoss")
    code = created["room"]["code"]

    response = api_client.post(
        reverse("multi-room-join", kwargs={"code": code}),
        {"nickname": "lunchboss"},
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["code"] == "nickname_taken"


@pytest.mark.django_db(transaction=True)
def test_join_lock_query_does_not_join_nullable_result_food(
    api_client: APIClient,
) -> None:
    created = create_room(api_client)

    with CaptureQueriesContext(connection) as queries:
        response = api_client.post(
            reverse("multi-room-join", kwargs={"code": created["room"]["code"]}),
            {"nickname": "guest"},
            format="json",
        )

    room_queries = [
        query["sql"].upper()
        for query in queries.captured_queries
        if 'FROM "RECOMMENDATIONS_MULTIROOM"' in query["sql"].upper()
    ]
    assert response.status_code == 201
    assert not any(
        "LEFT OUTER JOIN" in query and "RECOMMENDATIONS_FOOD" in query for query in room_queries
    )


@pytest.mark.django_db
def test_all_participants_submit_lists_and_host_draws_unique_top_food(
    api_client: APIClient, multi_foods: list[Food]
) -> None:
    created = create_room(api_client)
    code = created["room"]["code"]
    host_token = created["participant_token"]
    guest = join_room(api_client, code, "민지")
    guest_token = guest["participant_token"]

    submit_choices(api_client, code, host_token, [multi_foods[0].id, multi_foods[1].id])
    ready = submit_choices(api_client, code, guest_token, [multi_foods[0].id, multi_foods[2].id])
    assert ready["room"]["all_ready"] is True
    assert [choice["name"] for choice in ready["room"]["self"]["choices"]] == [
        "치킨",
        "김밥",
    ]
    assert ready["room"]["can_draw"] is True
    assert ready["room"]["leaders"] == [
        {
            "id": multi_foods[0].id,
            "key": f"food:{multi_foods[0].id}",
            "name": "치킨",
            "votes": 2,
            "is_custom": False,
        }
    ]

    response = api_client.post(
        reverse("multi-room-draw", kwargs={"code": code}),
        format="json",
        HTTP_X_MULTI_TOKEN=host_token,
    )

    assert response.status_code == 200
    assert response.json()["room"]["result"]["food"]["name"] == "치킨"
    assert response.json()["room"]["result"]["votes"] == 2
    assert response.json()["room"]["can_reroll"] is False

    repeated = api_client.post(
        reverse("multi-room-draw", kwargs={"code": code}),
        format="json",
        HTTP_X_MULTI_TOKEN=host_token,
    )
    assert repeated.status_code == 409
    assert repeated.json()["code"] == "decision_complete"


@pytest.mark.django_db
def test_lever_stays_locked_when_every_food_has_one_vote(
    api_client: APIClient, multi_foods: list[Food]
) -> None:
    created = create_room(api_client)
    code = created["room"]["code"]
    guest = join_room(api_client, code, "민지")
    submit_choices(api_client, code, created["participant_token"], [multi_foods[0].id])
    state = submit_choices(api_client, code, guest["participant_token"], [multi_foods[1].id])

    assert state["room"]["all_ready"] is True
    assert state["room"]["can_draw"] is False
    assert state["room"]["blocked_reason"] == "no_overlap"
    assert state["room"]["leaders"] == []

    response = api_client.post(
        reverse("multi-room-draw", kwargs={"code": code}),
        format="json",
        HTTP_X_MULTI_TOKEN=created["participant_token"],
    )
    assert response.status_code == 409
    assert response.json()["code"] == "no_overlap"


@pytest.mark.django_db
def test_tied_top_foods_can_be_redrawn_without_immediate_repeat(
    api_client: APIClient, multi_foods: list[Food]
) -> None:
    created = create_room(api_client)
    code = created["room"]["code"]
    guest = join_room(api_client, code, "민지")
    shared = [multi_foods[0].id, multi_foods[1].id]
    submit_choices(api_client, code, created["participant_token"], shared)
    submit_choices(api_client, code, guest["participant_token"], shared)

    url = reverse("multi-room-draw", kwargs={"code": code})
    first = api_client.post(url, format="json", HTTP_X_MULTI_TOKEN=created["participant_token"])
    second = api_client.post(url, format="json", HTTP_X_MULTI_TOKEN=created["participant_token"])

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["room"]["can_reroll"] is True
    assert (
        second.json()["room"]["result"]["food"]["id"]
        != first.json()["room"]["result"]["food"]["id"]
    )


@pytest.mark.django_db
def test_only_host_can_draw_and_joining_closes_after_first_draw(
    api_client: APIClient, multi_foods: list[Food]
) -> None:
    created = create_room(api_client)
    code = created["room"]["code"]
    guest = join_room(api_client, code, "민지")
    submit_choices(api_client, code, created["participant_token"], [multi_foods[0].id])
    submit_choices(api_client, code, guest["participant_token"], [multi_foods[0].id])
    draw_url = reverse("multi-room-draw", kwargs={"code": code})

    forbidden = api_client.post(
        draw_url, format="json", HTTP_X_MULTI_TOKEN=guest["participant_token"]
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["code"] == "host_only"

    assert (
        api_client.post(
            draw_url,
            format="json",
            HTTP_X_MULTI_TOKEN=created["participant_token"],
        ).status_code
        == 200
    )
    late_join = api_client.post(
        reverse("multi-room-join", kwargs={"code": code}),
        {"nickname": "늦은 참가자"},
        format="json",
    )
    assert late_join.status_code == 409
    assert late_join.json()["code"] == "room_locked"


@pytest.mark.django_db
def test_food_search_returns_active_matches_only(
    api_client: APIClient, multi_foods: list[Food]
) -> None:
    multi_foods[0].is_active = False
    multi_foods[0].save(update_fields=["is_active"])

    response = api_client.get(reverse("food-search"), {"q": "라"})

    assert response.status_code == 200
    assert [item["name"] for item in response.json()["foods"]] == ["라면"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "origin",
    [
        "https://lunch-web-ten.vercel.app",
        "https://lunch-web-heedo-kim0624s-projects.vercel.app",
        "https://lunch-abc123-heedo-kim0624s-projects.vercel.app",
    ],
)
def test_food_search_allows_project_scoped_vercel_origins(
    api_client: APIClient,
    multi_foods: list[Food],
    origin: str,
) -> None:
    response = api_client.get(reverse("food-search"), {"q": "라면"}, HTTP_ORIGIN=origin)

    assert response.status_code == 200
    assert response.headers["Access-Control-Allow-Origin"] == origin


@pytest.mark.django_db
def test_participant_search_includes_existing_room_custom_choices(
    api_client: APIClient,
) -> None:
    created = create_room(api_client)
    code = created["room"]["code"]
    guest = join_room(api_client, code, "민지")
    submit_choice_items(
        api_client,
        code,
        created["participant_token"],
        [{"custom_name": "회사 앞 제육"}],
    )

    response = api_client.get(
        reverse("food-search"),
        {"q": "회사", "room": code},
        HTTP_X_MULTI_TOKEN=guest["participant_token"],
    )

    assert response.status_code == 200
    assert response.json()["foods"] == [
        {
            "id": None,
            "key": f"custom:{MultiRoomCustomFood.objects.get(room__code=code).id}",
            "name": "회사 앞 제육",
            "family": "직접 입력",
            "cuisine": "사용자 메뉴",
            "is_custom": True,
        }
    ]

    anonymous = api_client.get(reverse("food-search"), {"q": "회사", "room": code})
    assert anonymous.status_code == 403
    assert anonymous.json()["code"] == "invalid_participant_token"

    submit_choice_items(
        api_client,
        code,
        created["participant_token"],
        [{"custom_name": "다른 메뉴"}],
    )
    removed = api_client.get(
        reverse("food-search"),
        {"q": "회사", "room": code},
        HTTP_X_MULTI_TOKEN=guest["participant_token"],
    )
    assert removed.status_code == 200
    assert removed.json()["foods"] == []


@pytest.mark.django_db
def test_equal_direct_menu_names_overlap_and_can_win(api_client: APIClient) -> None:
    created = create_room(api_client)
    code = created["room"]["code"]
    guest = join_room(api_client, code, "민지")

    submit_choice_items(
        api_client,
        code,
        created["participant_token"],
        [{"custom_name": "새우 오일 파스타"}],
    )
    ready = submit_choice_items(
        api_client,
        code,
        guest["participant_token"],
        [{"custom_name": "  새우   오일 파스타  "}],
    )

    assert ready["room"]["can_draw"] is True
    assert ready["room"]["leaders"][0]["name"] == "새우 오일 파스타"
    assert ready["room"]["leaders"][0]["is_custom"] is True
    assert ready["room"]["leaders"][0]["votes"] == 2
    assert not Food.objects.filter(canonical_name="새우 오일 파스타").exists()
    assert (
        MultiRoomCustomFood.objects.filter(
            room__code=code,
            normalized_name="새우 오일 파스타",
        ).count()
        == 1
    )

    drawn = api_client.post(
        reverse("multi-room-draw", kwargs={"code": code}),
        format="json",
        HTTP_X_MULTI_TOKEN=created["participant_token"],
    )
    assert drawn.status_code == 200
    assert drawn.json()["room"]["result"]["food"]["name"] == "새우 오일 파스타"
    assert drawn.json()["room"]["result"]["food"]["id"] is None
    assert drawn.json()["room"]["result"]["food"]["is_custom"] is True


@pytest.mark.django_db
def test_direct_exact_catalog_name_resolves_to_catalog_food(
    api_client: APIClient, multi_foods: list[Food]
) -> None:
    created = create_room(api_client)
    code = created["room"]["code"]
    guest = join_room(api_client, code, "민지")

    submit_choice_items(
        api_client,
        code,
        created["participant_token"],
        [{"custom_name": " 치킨 "}],
    )
    ready = submit_choice_items(
        api_client,
        code,
        guest["participant_token"],
        [{"food_id": multi_foods[0].id}],
    )

    assert ready["room"]["leaders"][0]["id"] == multi_foods[0].id
    assert ready["room"]["leaders"][0]["is_custom"] is False
    assert ready["room"]["max_votes"] == 2


@pytest.mark.django_db
def test_invalid_or_duplicate_direct_menu_names_are_rejected(
    api_client: APIClient,
    multi_foods: list[Food],
) -> None:
    created = create_room(api_client)
    url = reverse("multi-room-choices", kwargs={"code": created["room"]["code"]})
    headers = {"HTTP_X_MULTI_TOKEN": created["participant_token"]}

    invalid = api_client.put(
        url,
        {"choices": [{"custom_name": "<script>"}]},
        format="json",
        **headers,
    )
    duplicate = api_client.put(
        url,
        {
            "choices": [
                {"custom_name": "새우 파스타"},
                {"custom_name": "  새우   파스타 "},
            ]
        },
        format="json",
        **headers,
    )
    catalog_duplicate = api_client.put(
        url,
        {
            "choices": [
                {"food_id": multi_foods[0].id},
                {"custom_name": "치킨"},
            ]
        },
        format="json",
        **headers,
    )

    assert invalid.status_code == 400
    assert duplicate.status_code == 400
    assert catalog_duplicate.status_code == 400
    assert catalog_duplicate.json()["code"] == "duplicate_choices"

from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from recommendations.multi_serializers import (
    FoodSearchSerializer,
    MultiChoicesSerializer,
    MultiNicknameSerializer,
)
from recommendations.services.multi_room import (
    MultiRoomDomainError,
    create_room,
    draw_room,
    join_room,
    read_room,
    require_participant,
    room_payload,
    search_foods,
    search_room_custom_foods,
    submit_choices,
)

PARTICIPANT_TOKEN_HEADER = "HTTP_X_MULTI_TOKEN"


def participant_token(request: Request) -> str | None:
    value = request.META.get(PARTICIPANT_TOKEN_HEADER)
    return value.strip() if isinstance(value, str) and value.strip() else None


def domain_error_response(error: MultiRoomDomainError) -> Response:
    return Response({"code": error.code, "detail": error.detail}, status=error.status_code)


class FoodSearchView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "food_search"

    def get(self, request: Request) -> Response:
        serializer = FoodSearchSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        query = serializer.validated_data["q"]
        room_code = serializer.validated_data.get("room")
        custom_foods = []
        if room_code:
            try:
                room = read_room(room_code)
                require_participant(room, participant_token(request))
            except MultiRoomDomainError as error:
                return domain_error_response(error)
            custom_foods = list(search_room_custom_foods(room, query))

        options = [
            {
                "id": None,
                "key": f"custom:{food.id}",
                "name": food.name,
                "family": "직접 입력",
                "cuisine": "사용자 메뉴",
                "is_custom": True,
            }
            for food in custom_foods
        ]
        seen_names = {str(option["name"]).casefold() for option in options}
        for food in search_foods(query):
            if len(options) >= 30:
                break
            normalized_name = food.canonical_name.casefold()
            if normalized_name in seen_names:
                continue
            seen_names.add(normalized_name)
            options.append(
                {
                    "id": food.id,
                    "key": f"food:{food.id}",
                    "name": food.canonical_name,
                    "family": food.family,
                    "cuisine": food.cuisine,
                    "is_custom": False,
                }
            )
        return Response({"foods": options})


class MultiRoomCreateView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "multi_room_create"

    def post(self, request: Request) -> Response:
        serializer = MultiNicknameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            room, _, token = create_room(serializer.validated_data["nickname"])
        except MultiRoomDomainError as error:
            return domain_error_response(error)
        return Response(
            {"participant_token": token, "room": room_payload(room, token)},
            status=status.HTTP_201_CREATED,
        )


class MultiRoomDetailView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "multi_room_read"

    def get(self, request: Request, code: str) -> Response:
        try:
            room = read_room(code)
        except MultiRoomDomainError as error:
            return domain_error_response(error)
        return Response({"room": room_payload(room, participant_token(request))})


class MultiRoomJoinView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "multi_room_join"

    def post(self, request: Request, code: str) -> Response:
        serializer = MultiNicknameSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            room, _, token = join_room(code, serializer.validated_data["nickname"])
        except MultiRoomDomainError as error:
            return domain_error_response(error)
        return Response(
            {"participant_token": token, "room": room_payload(room, token)},
            status=status.HTTP_201_CREATED,
        )


class MultiRoomChoicesView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "multi_room_write"

    def put(self, request: Request, code: str) -> Response:
        serializer = MultiChoicesSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = participant_token(request)
        try:
            room = submit_choices(code, token, serializer.validated_data["choices"])
        except MultiRoomDomainError as error:
            return domain_error_response(error)
        return Response({"room": room_payload(room, token)})


class MultiRoomDrawView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "multi_room_draw"

    def post(self, request: Request, code: str) -> Response:
        token = participant_token(request)
        try:
            room = draw_room(code, token)
        except MultiRoomDomainError as error:
            return domain_error_response(error)
        return Response({"room": room_payload(room, token)})

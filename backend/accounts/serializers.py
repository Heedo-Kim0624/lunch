from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from rest_framework import serializers


def normalize_email(value: str) -> str:
    return value.strip().lower()


def user_payload(user: User) -> dict[str, int | str]:
    return {
        "id": user.id,
        "email": user.email,
        "display_name": user.first_name,
    }


class RegistrationSerializer(serializers.Serializer):
    display_name = serializers.CharField(max_length=50, trim_whitespace=True)
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)
    password_confirm = serializers.CharField(
        max_length=128,
        trim_whitespace=False,
        write_only=True,
    )

    def validate(self, attrs: dict[str, str]) -> dict[str, str]:
        email = normalize_email(attrs["email"])
        if User.objects.filter(username=email).exists():
            raise serializers.ValidationError({"email": "이미 가입된 이메일입니다."})
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "비밀번호가 서로 일치하지 않습니다."}
            )

        candidate = User(username=email, email=email, first_name=attrs["display_name"])
        try:
            validate_password(attrs["password"], user=candidate)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"password": list(error.messages)}) from error

        attrs["email"] = email
        return attrs

    @transaction.atomic
    def create(self, validated_data: dict[str, str]) -> User:
        return User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            first_name=validated_data["display_name"],
            password=validated_data["password"],
        )


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(max_length=128, trim_whitespace=False, write_only=True)

    def validate(self, attrs: dict[str, str]) -> dict[str, object]:
        user = authenticate(
            username=normalize_email(attrs["email"]),
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError(
                {"detail": "이메일 또는 비밀번호를 확인해 주세요."}
            )
        attrs["user"] = user
        return attrs

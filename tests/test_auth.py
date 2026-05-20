import pytest
from fastapi import HTTPException

from app.routes.dependencies import require_admin
from app.services.auth_service import create_access_token, password_hash, verify_password


class User:
    id = 1
    email = "u@example.com"
    role = "user"


class Admin:
    id = 2
    email = "a@example.com"
    role = "admin"


def test_password_hash_and_verify() -> None:
    stored = password_hash("secret")
    assert verify_password("secret", stored)
    assert not verify_password("wrong", stored)


def test_jwt_can_be_created() -> None:
    token = create_access_token(1, "u@example.com", "user")
    assert token.count(".") == 2


def test_admin_dependency_rejects_normal_user() -> None:
    with pytest.raises(HTTPException):
        require_admin(User())
    assert require_admin(Admin()).role == "admin"

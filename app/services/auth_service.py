import hashlib
import hmac
import os
from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy.orm import Session

from app.config import get_settings
from app.infra.vault import read_dev_secret
from app.repositories.users import create_user, get_user_by_email


def password_hash(password: str, salt: str | None = None) -> str:
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 120_000).hex()
    return f"pbkdf2_sha256${salt}${digest}"


def verify_password(password: str, stored: str) -> bool:
    try:
        _, salt, expected = stored.split("$", 2)
    except ValueError:
        return False
    actual = password_hash(password, salt).split("$", 2)[2]
    return hmac.compare_digest(actual, expected)


def jwt_secret() -> str:
    settings = get_settings()
    try:
        secret = read_dev_secret("jwt_secret", settings=settings)
    except Exception:
        secret = None
    # Local fallback keeps tests and first-run demos usable, while Vault remains
    # the intended source in Docker/dev environments.
    return secret or "local-dev-jwt-secret-change-me-32-bytes-min"


def create_access_token(user_id: int, email: str, role: str) -> str:
    settings = get_settings()
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    return jwt.encode(
        {"sub": str(user_id), "email": email, "role": role, "exp": expires_at},
        jwt_secret(),
        algorithm=settings.jwt_algorithm,
    )


def register_user(db: Session, email: str, password: str, role: str = "user"):
    if role not in {"user", "admin"}:
        raise ValueError("role must be user or admin")
    if get_user_by_email(db, email):
        raise ValueError("email is already registered")
    return create_user(db, email=email, hashed_password=password_hash(password), role=role)


def authenticate_user(db: Session, email: str, password: str):
    user = get_user_by_email(db, email)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

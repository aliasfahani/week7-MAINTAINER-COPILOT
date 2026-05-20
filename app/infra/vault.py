import logging
from typing import Any

import requests

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)


def _secret_url(settings: Settings) -> str:
    return f"{settings.vault_addr.rstrip('/')}/v1/{settings.vault_secret_path.lstrip('/')}"


def read_all_dev_secrets(settings: Settings | None = None) -> dict[str, Any]:
    """Read the Day 1 KV v2 secret bundle from Vault.

    The helper is intentionally tiny. Later services can wrap this with stricter
    error handling and secret-specific accessors.
    """

    settings = settings or get_settings()
    response = requests.get(
        _secret_url(settings),
        headers={"X-Vault-Token": settings.vault_token},
        timeout=3,
    )
    response.raise_for_status()
    payload = response.json()
    return payload.get("data", {}).get("data", {})


def read_dev_secret(key: str, settings: Settings | None = None) -> str | None:
    secrets = read_all_dev_secrets(settings=settings)
    value = secrets.get(key)
    if value is None:
        logger.warning("Vault secret key %s was not found", key)
    return value

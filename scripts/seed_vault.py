import os
import sys

import requests


VAULT_ADDR = os.getenv("VAULT_ADDR", "http://localhost:8200")
VAULT_TOKEN = os.getenv("VAULT_TOKEN", "dev-root-token")
SECRET_PATH = "secret/data/maintainers-copilot"


def main() -> int:
    secrets = {
        "jwt_secret": os.getenv("DEV_JWT_SECRET", "dev-only-jwt-secret-change-me"),
        "database_password": os.getenv("POSTGRES_PASSWORD", "postgres"),
        "minio_access_key": os.getenv("MINIO_ROOT_USER", "minioadmin"),
        "minio_secret_key": os.getenv("MINIO_ROOT_PASSWORD", "minioadmin"),
        "llm_api_key": os.getenv("LLM_API_KEY", "placeholder-not-a-real-key"),
    }

    response = requests.post(
        f"{VAULT_ADDR.rstrip('/')}/v1/{SECRET_PATH}",
        headers={"X-Vault-Token": VAULT_TOKEN},
        json={"data": secrets},
        timeout=5,
    )
    if response.status_code >= 400:
        print(f"Failed to seed Vault: {response.status_code} {response.text}", file=sys.stderr)
        return 1

    print(f"Seeded development secrets at {SECRET_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

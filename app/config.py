from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central runtime settings.

    Day 1 keeps values simple and local-dev friendly. Real secrets are read from
    Vault through app.infra.vault instead of being hardcoded here.
    """

    app_name: str = "Maintainer's Copilot API"
    api_port: int = 8000
    model_server_port: int = 8001

    vault_addr: str = "http://vault:8200"
    vault_token: str = "dev-root-token"
    vault_secret_path: str = "secret/data/maintainers-copilot"

    postgres_host: str = "db"
    postgres_port: int = 5432
    postgres_db: str = "maintainers_copilot"
    postgres_user: str = "postgres"
    postgres_password: str = "postgres"

    redis_host: str = "redis"
    redis_port: int = 6379

    minio_endpoint: str = "minio:9000"
    minio_bucket: str = "maintainers-copilot"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache
def get_settings() -> Settings:
    return Settings()

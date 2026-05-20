import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import get_settings
from app.infra.vault import read_dev_secret
from app.routes.auth import router as auth_router
from app.routes.chat import router as chat_router
from app.routes.health import router as health_router
from app.routes.memory import router as memory_router
from app.routes.widgets import router as widgets_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    try:
        # Day 1 Vault check: prove the API can read a secret without making app
        # startup depend on Vault being available during local development.
        read_dev_secret("jwt_secret", settings=settings)
        logger.info("Vault startup check succeeded")
    except Exception as exc:  # pragma: no cover - exercised in container smoke checks
        logger.warning("Vault startup check failed: %s", exc)
    yield


app = FastAPI(title=get_settings().app_name, lifespan=lifespan)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(chat_router)
app.include_router(memory_router)
app.include_router(widgets_router)

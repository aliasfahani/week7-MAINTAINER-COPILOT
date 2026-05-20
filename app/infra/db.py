from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


settings = get_settings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def get_db() -> Generator[Session, None, None]:
    """Provide one SQLAlchemy session per request.

    Keeping session lifecycle here prevents routes from touching SQLAlchemy
    directly and preserves the routes -> services -> repositories -> infra shape.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

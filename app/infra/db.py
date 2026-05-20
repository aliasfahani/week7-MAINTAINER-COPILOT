from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


_engine = None
_session_local = None


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_engine(settings.database_url, pool_pre_ping=True)
    return _engine


def get_session_local():
    global _session_local
    if _session_local is None:
        _session_local = sessionmaker(bind=get_engine(), autoflush=False, autocommit=False)
    return _session_local


def get_db() -> Generator[Session, None, None]:
    """Provide one SQLAlchemy session per request.

    Keeping session lifecycle here prevents routes from touching SQLAlchemy
    directly and preserves the routes -> services -> repositories -> infra shape.
    """

    db = get_session_local()()
    try:
        yield db
    finally:
        db.close()

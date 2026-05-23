from urllib.parse import urlparse

from sqlalchemy.orm import Session

from app.repositories.widgets import create_widget, get_widget, list_widgets, update_widget


def safe_widget(row) -> dict:
    return {
        "widget_id": row.widget_id,
        "theme": row.theme,
        "greeting": row.greeting,
        "enabled_tools": row.enabled_tools,
    }


def origin_allowed(allowed: list[str], origin: str | None) -> bool:
    if "*" in allowed:
        return True
    if not origin:
        return True
    parsed = urlparse(origin)
    normalized = f"{parsed.scheme}://{parsed.netloc}" if parsed.scheme and parsed.netloc else origin.rstrip("/")
    return normalized in [item.rstrip("/") for item in allowed]


def get_public_widget_config(db: Session, widget_id: str, origin: str | None) -> dict | None:
    row = get_widget(db, widget_id)
    if not row or not origin_allowed(row.allowed_origins, origin):
        return None
    return safe_widget(row)


def create_widget_config(db: Session, data: dict, created_by: int | None):
    existing = get_widget(db, data["widget_id"])
    if existing:
        # Streamlit's demo form is often submitted more than once with the
        # same widget_id. Treat that as an update so the admin page remains
        # idempotent during demos instead of surfacing a database uniqueness
        # error to a beginner-facing UI.
        return update_widget(db, data["widget_id"], data)
    return create_widget(db, data, created_by)


def list_widget_configs(db: Session) -> list[dict]:
    return [
        {
            "widget_id": row.widget_id,
            "allowed_origins": row.allowed_origins,
            "theme": row.theme,
            "greeting": row.greeting,
            "enabled_tools": row.enabled_tools,
        }
        for row in list_widgets(db)
    ]


def update_widget_config(db: Session, widget_id: str, data: dict):
    return update_widget(db, widget_id, data)

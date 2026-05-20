from sqlalchemy.orm import Session

from app.infra.models import WidgetConfig


def get_widget(db: Session, widget_id: str) -> WidgetConfig | None:
    return db.query(WidgetConfig).filter(WidgetConfig.widget_id == widget_id).first()


def list_widgets(db: Session) -> list[WidgetConfig]:
    return db.query(WidgetConfig).order_by(WidgetConfig.created_at.desc()).all()


def create_widget(db: Session, data: dict, created_by: int | None) -> WidgetConfig:
    row = WidgetConfig(**data, created_by=created_by)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def update_widget(db: Session, widget_id: str, data: dict) -> WidgetConfig | None:
    row = get_widget(db, widget_id)
    if not row:
        return None
    for key, value in data.items():
        if value is not None:
            setattr(row, key, value)
    db.commit()
    db.refresh(row)
    return row

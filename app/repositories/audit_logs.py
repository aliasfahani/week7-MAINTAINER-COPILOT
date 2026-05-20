from sqlalchemy.orm import Session

from app.infra.models import AuditLog


def create_audit_log(
    db: Session,
    actor_id: int | None,
    action: str,
    target_type: str,
    target_id: str | None,
    metadata: dict,
) -> AuditLog:
    row = AuditLog(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        metadata_=metadata,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row

from sqlalchemy.orm import Session

from app.infra.models import Memory


def create_memory(db: Session, user_id: int, text: str, embedding: list[float], metadata: dict) -> Memory:
    row = Memory(user_id=user_id, memory_type="semantic", text=text, embedding_json=embedding, metadata_=metadata)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def list_memories(db: Session, user_id: int) -> list[Memory]:
    return db.query(Memory).filter(Memory.user_id == user_id).order_by(Memory.created_at.desc()).all()


def delete_memory(db: Session, user_id: int, memory_id: int) -> bool:
    row = db.query(Memory).filter(Memory.user_id == user_id, Memory.id == memory_id).first()
    if not row:
        return False
    db.delete(row)
    db.commit()
    return True

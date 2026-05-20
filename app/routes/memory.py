from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.infra.db import get_db
from app.routes.dependencies import get_current_user
from app.schemas import MemoryCreate
from app.services.memory_service import delete_memory, list_memories, write_long_term_memory

router = APIRouter(prefix="/memory", tags=["memory"])


@router.get("")
def get_memory(user=Depends(get_current_user), db: Session = Depends(get_db)):
    return {"memories": list_memories(db, user.id)}


@router.post("")
def create_memory(payload: MemoryCreate, user=Depends(get_current_user), db: Session = Depends(get_db)):
    row = write_long_term_memory(db, user.id, payload.text, payload.metadata)
    return {"id": row.id, "text": row.text, "metadata": row.metadata_}


@router.delete("/{memory_id}")
def remove_memory(memory_id: int, user=Depends(get_current_user), db: Session = Depends(get_db)):
    if not delete_memory(db, user.id, memory_id):
        raise HTTPException(status_code=404, detail="Memory not found")
    return {"deleted": True}

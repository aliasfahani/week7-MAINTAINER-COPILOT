from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.infra.embeddings import embed_text
from app.infra.redaction import redact_text
from app.infra.redis import redis_state
from app.repositories.audit_logs import create_audit_log
from app.repositories.memories import create_memory, delete_memory as repo_delete_memory, list_memories as repo_list_memories


def _key(conversation_id: str) -> str:
    return f"conversation:{conversation_id}:messages"


def get_conversation_state(conversation_id: str) -> list[dict[str, str]]:
    return redis_state.get_json(_key(conversation_id), [])


def save_conversation_state(conversation_id: str, messages: list[dict[str, str]]) -> None:
    redis_state.set_json(_key(conversation_id), messages, ttl=get_settings().redis_ttl_seconds)


def append_message(conversation_id: str, role: str, content: str) -> None:
    messages = get_conversation_state(conversation_id)
    messages.append({"role": role, "content": redact_text(content)})
    save_conversation_state(conversation_id, messages[-20:])


def clear_conversation_state(conversation_id: str) -> None:
    redis_state.delete(_key(conversation_id))


def write_long_term_memory(db: Session, user_id: int, text: str, metadata: dict | None = None):
    safe_text = redact_text(text)
    row = create_memory(db, user_id=user_id, text=safe_text, embedding=embed_text(safe_text), metadata=metadata or {})
    create_audit_log(
        db,
        actor_id=user_id,
        action="memory.write",
        target_type="memory",
        target_id=str(row.id),
        metadata={"memory_type": "semantic"},
    )
    return row


def list_memories(db: Session, user_id: int) -> list[dict[str, Any]]:
    return [
        {"id": row.id, "memory_type": row.memory_type, "text": row.text, "metadata": row.metadata_, "created_at": str(row.created_at)}
        for row in repo_list_memories(db, user_id)
    ]


def search_long_term_memories(db: Session, user_id: int, query: str, top_k: int = 5) -> list[dict[str, Any]]:
    query_embedding = embed_text(query)
    scored = []
    for row in repo_list_memories(db, user_id):
        embedding = row.embedding_json or []
        score = sum(a * b for a, b in zip(query_embedding, embedding, strict=False))
        scored.append({"id": row.id, "text": row.text, "metadata": row.metadata_, "score": score})
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]


def delete_memory(db: Session, user_id: int, memory_id: int) -> bool:
    return repo_delete_memory(db, user_id, memory_id)

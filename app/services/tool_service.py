from typing import Any

from app.infra.model_client import ModelServerClient, get_model_client
from app.infra.redaction import redact_text
from app.services.memory_service import write_long_term_memory
from app.services.rag_service import search_hybrid


def classify_issue_tool(
    title: str,
    body: str,
    client: ModelServerClient | None = None,
) -> dict[str, Any]:
    """Tool wrapper for issue classification.

    The future single tool-calling LLM should call this function as one tool.
    It delegates model inference to model_server instead of running ML inside
    the API process.
    """

    model_client = client or get_model_client()
    return model_client.classify_issue(title=title, body=body)


def extract_entities_tool(text: str, client: ModelServerClient | None = None) -> dict[str, Any]:
    model_client = client or get_model_client()
    return model_client.extract_entities(text=text)


def summarize_thread_tool(text: str, client: ModelServerClient | None = None) -> dict[str, Any]:
    model_client = client or get_model_client()
    return model_client.summarize_text(text=text)


def rag_search_tool(
    query: str,
    filters: dict[str, Any] | None = None,
    top_k: int = 5,
) -> dict[str, Any]:
    """Tool wrapper for the future single LLM chatbot.

    This keeps RAG as one callable tool. It does not introduce an agent or a
    separate planner; the future LLM can call this function when it needs repo
    knowledge.
    """

    return search_hybrid(query=query, top_k=top_k, filters=filters, save_snapshot=True)


def write_memory_tool(user_id: int, text: str, metadata: dict[str, Any] | None = None, db=None) -> dict[str, Any]:
    if db is None:
        return {"ok": False, "error": "database session is required for memory writes"}
    row = write_long_term_memory(db, user_id=user_id, text=redact_text(text), metadata=metadata or {})
    return {"ok": True, "memory_id": row.id, "text": row.text}

from typing import Any

from sqlalchemy import text
from sqlalchemy.orm import Session


def _vector_literal(embedding: list[float]) -> str:
    return "[" + ",".join(f"{value:.8f}" for value in embedding) + "]"


def replace_rag_documents(db: Session, documents: list[dict[str, Any]], chunks: list[dict[str, Any]]) -> None:
    """Replace the RAG corpus in a small, explainable transaction.

    Day 3 keeps ingestion simple: delete old RAG documents/chunks and insert the
    freshly built corpus. This is fine for a student project and avoids complex
    incremental sync logic before the corpus shape is stable.
    """

    db.execute(text("DELETE FROM chunks WHERE document_id IN (SELECT id FROM documents WHERE source_type IN ('docs', 'issue'))"))
    db.execute(text("DELETE FROM documents WHERE source_type IN ('docs', 'issue')"))

    source_to_id: dict[tuple[str, str], int] = {}
    for document in documents:
        row = db.execute(
            text(
                """
                INSERT INTO documents (source, source_type, source_id, title, url, metadata)
                VALUES (:source, :source_type, :source_id, :title, :url, CAST(:metadata AS json))
                RETURNING id
                """
            ),
            {
                "source": document["source_type"],
                "source_type": document["source_type"],
                "source_id": document["source_id"],
                "title": document["title"],
                "url": document.get("url"),
                "metadata": document.get("metadata_json", "{}"),
            },
        ).one()
        source_to_id[(document["source_type"], document["source_id"])] = row.id

    for chunk in chunks:
        document_id = source_to_id[(chunk["source_type"], chunk["source_id"])]
        db.execute(
            text(
                """
                INSERT INTO chunks (
                    document_id, chunk_id, chunk_index, text, metadata,
                    char_count, embedding_json, embedding
                )
                VALUES (
                    :document_id, :chunk_id, :chunk_index, :text, CAST(:metadata AS json),
                    :char_count, CAST(:embedding_json AS json), CAST(:embedding AS vector)
                )
                """
            ),
            {
                "document_id": document_id,
                "chunk_id": chunk["chunk_id"],
                "chunk_index": chunk["chunk_index"],
                "text": chunk["text"],
                "metadata": chunk.get("metadata_json", "{}"),
                "char_count": chunk["char_count"],
                "embedding_json": chunk.get("embedding_json", "[]"),
                "embedding": _vector_literal(chunk["embedding"]),
            },
        )
    db.commit()


def search_pgvector_chunks(
    db: Session,
    query_embedding: list[float],
    top_k: int,
    filters: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    where = []
    params: dict[str, Any] = {"query_embedding": _vector_literal(query_embedding), "top_k": top_k}
    filters = filters or {}

    if source_type := filters.get("source_type"):
        where.append("d.source_type = :source_type")
        params["source_type"] = source_type
    if repo := filters.get("repo"):
        where.append("d.metadata ->> 'repo' = :repo")
        params["repo"] = repo
    if label := filters.get("label"):
        where.append("c.metadata -> 'labels' ? :label")
        params["label"] = label
    if issue_number := filters.get("issue_number"):
        where.append("c.metadata ->> 'issue_number' = :issue_number")
        params["issue_number"] = str(issue_number)

    where_sql = "WHERE " + " AND ".join(where) if where else ""
    rows = db.execute(
        text(
            f"""
            SELECT
                c.chunk_id,
                c.text,
                d.source_type,
                d.url,
                c.metadata,
                1 - (c.embedding <=> CAST(:query_embedding AS vector)) AS score
            FROM chunks c
            JOIN documents d ON d.id = c.document_id
            {where_sql}
            ORDER BY c.embedding <=> CAST(:query_embedding AS vector)
            LIMIT :top_k
            """
        ),
        params,
    ).mappings()

    return [dict(row) for row in rows]

import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sqlalchemy.orm import Session

from app.config import get_settings
from app.infra.embeddings import embed_text
from app.repositories.documents import search_pgvector_chunks

DEFAULT_CHUNKS_PATH = Path("data/processed/rag_chunks.jsonl")
SNAPSHOT_DIR = Path("artifacts/rag-snapshots")


def _slug(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]+", "-", value).strip("-").lower() or "chunk"


def _window_text(text: str, max_chars: int = 1600, overlap: int = 200) -> list[str]:
    """Fallback chunking for long sections.

    The primary strategy is structure-aware splitting. This window only handles
    sections that are still too large after markdown heading or issue splitting.
    """

    text = text.strip()
    if len(text) <= max_chars:
        return [text] if text else []

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_chars, len(text))
        chunks.append(text[start:end].strip())
        if end == len(text):
            break
        start = max(0, end - overlap)
    return [chunk for chunk in chunks if chunk]


def _markdown_sections(text: str) -> list[tuple[str, str]]:
    sections: list[tuple[str, list[str]]] = [("Overview", [])]
    current_title = "Overview"
    for line in text.splitlines():
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if heading:
            current_title = heading.group(2).strip()
            sections.append((current_title, []))
            continue
        sections[-1][1].append(line)
    return [(title, "\n".join(lines).strip()) for title, lines in sections if "\n".join(lines).strip()]


def chunk_document(document: dict[str, Any], max_chars: int = 1600) -> list[dict[str, Any]]:
    """Create structure-aware chunks for docs and issues.

    Docs split first by markdown headings so the section title stays with the
    text. Issues keep title/body together and comments as their own chunks when
    ingestion includes them.
    """

    source_type = document["source_type"]
    source_id = document["source_id"]
    base_metadata = {
        **document.get("metadata", {}),
        "source_id": source_id,
        "source_type": source_type,
        "title": document.get("title", ""),
        "url": document.get("url"),
    }

    chunks = []
    if source_type == "docs":
        section_parts = _markdown_sections(document.get("text", ""))
        for section_index, (section_title, section_text) in enumerate(section_parts):
            prefixed = f"{document.get('title', '')}\n{section_title}\n\n{section_text}".strip()
            for window_index, window in enumerate(_window_text(prefixed, max_chars=max_chars)):
                chunks.append(
                    {
                        "chunk_id": f"{_slug(source_id)}::s{section_index}w{window_index}",
                        "source_type": source_type,
                        "source_id": source_id,
                        "text": window,
                        "metadata": {**base_metadata, "section": section_title},
                        "url": document.get("url"),
                    }
                )
    else:
        issue_number = document.get("metadata", {}).get("issue_number")
        chunks.append(
            {
                "chunk_id": f"{_slug(source_id)}::body",
                "source_type": source_type,
                "source_id": source_id,
                "text": document.get("text", ""),
                "metadata": {**base_metadata, "issue_number": issue_number, "part": "body"},
                "url": document.get("url"),
            }
        )

    enriched = []
    for index, chunk in enumerate(chunks):
        text = chunk["text"].strip()
        if not text:
            continue
        enriched.append(
            {
                **chunk,
                "chunk_index": index,
                "char_count": len(text),
                "token_count": len(text.split()),
            }
        )
    return enriched


def chunk_documents(documents: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [chunk for document in documents for chunk in chunk_document(document)]


def load_chunks(path: Path = DEFAULT_CHUNKS_PATH) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]


def _passes_filters(chunk: dict[str, Any], filters: dict[str, Any] | None) -> bool:
    filters = filters or {}
    metadata = chunk.get("metadata", {})
    if source_type := filters.get("source_type"):
        if chunk.get("source_type") != source_type and metadata.get("source_type") != source_type:
            return False
    if repo := filters.get("repo"):
        if metadata.get("repo") != repo:
            return False
    if label := filters.get("label"):
        if label not in metadata.get("labels", []):
            return False
    if issue_number := filters.get("issue_number"):
        if str(metadata.get("issue_number")) != str(issue_number):
            return False
    return True


def _cosine(a: list[float], b: list[float]) -> float:
    if not a or not b:
        return 0.0
    numerator = sum(left * right for left, right in zip(a, b, strict=False))
    left_norm = math.sqrt(sum(value * value for value in a)) or 1.0
    right_norm = math.sqrt(sum(value * value for value in b)) or 1.0
    return numerator / (left_norm * right_norm)


def search_dense(
    query: str,
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
    db: Session | None = None,
    chunks: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    query_embedding = embed_text(query)
    if db is not None:
        return search_pgvector_chunks(db, query_embedding, top_k=top_k, filters=filters)

    candidates = [chunk for chunk in (chunks or load_chunks()) if _passes_filters(chunk, filters)]
    scored = []
    for chunk in candidates:
        embedding = chunk.get("embedding") or chunk.get("embedding_json") or []
        scored.append({**chunk, "score": _cosine(query_embedding, embedding), "dense_score": _cosine(query_embedding, embedding)})
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]


def _terms(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9_.:-]+", text.lower())


def search_sparse(
    query: str,
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
    chunks: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    candidates = [chunk for chunk in (chunks or load_chunks()) if _passes_filters(chunk, filters)]
    if not candidates:
        return []

    query_terms = _terms(query)
    doc_terms = [_terms(chunk["text"]) for chunk in candidates]
    doc_count = len(candidates)
    document_frequency = Counter(term for terms in doc_terms for term in set(terms))

    scored = []
    for chunk, terms in zip(candidates, doc_terms, strict=True):
        counts = Counter(terms)
        score = 0.0
        for term in query_terms:
            if counts[term] == 0:
                continue
            # Compact BM25-style scoring. This favors exact code terms like
            # file names and error classes without adding another dependency.
            idf = math.log((doc_count - document_frequency[term] + 0.5) / (document_frequency[term] + 0.5) + 1)
            score += idf * counts[term] / (counts[term] + 1.2)
        if score > 0:
            scored.append({**chunk, "score": score, "sparse_score": score})
    return sorted(scored, key=lambda item: item["score"], reverse=True)[:top_k]


def _normalize(items: list[dict[str, Any]], key: str) -> dict[str, float]:
    if not items:
        return {}
    max_score = max(abs(item.get(key, item.get("score", 0.0))) for item in items) or 1.0
    return {item["chunk_id"]: item.get(key, item.get("score", 0.0)) / max_score for item in items}


def rerank(query: str, candidates: list[dict[str, Any]], top_k: int = 5) -> list[dict[str, Any]]:
    query_terms = set(_terms(query))
    reranked = []
    for candidate in candidates:
        text_terms = set(_terms(candidate.get("text", "")))
        title_terms = set(_terms(candidate.get("metadata", {}).get("title", "")))
        exact_boost = 0.05 * len(query_terms & text_terms)
        title_boost = 0.10 * len(query_terms & title_terms)
        reranked.append({**candidate, "score": candidate["score"] + exact_boost + title_boost})
    return sorted(reranked, key=lambda item: item["score"], reverse=True)[:top_k]


def save_retrieval_snapshot(query: str, filters: dict[str, Any] | None, results: list[dict[str, Any]]) -> None:
    SNAPSHOT_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    payload = {
        "query": query,
        "filters": filters or {},
        "results": [{"chunk_id": item["chunk_id"], "score": item["score"]} for item in results],
        "created_at": timestamp,
        "storage": "local_json_todo_minio",
    }
    (SNAPSHOT_DIR / f"{timestamp}-{_slug(query)[:60]}.json").write_text(
        json.dumps(payload, indent=2) + "\n",
        encoding="utf-8",
    )


def search_hybrid(
    query: str,
    top_k: int = 5,
    filters: dict[str, Any] | None = None,
    db: Session | None = None,
    chunks: list[dict[str, Any]] | None = None,
    save_snapshot: bool = False,
) -> dict[str, Any]:
    settings = get_settings()
    candidate_k = max(top_k * 3, 10)
    local_chunks = chunks or load_chunks()
    dense = search_dense(query, top_k=candidate_k, filters=filters, db=db, chunks=local_chunks)
    sparse = search_sparse(query, top_k=candidate_k, filters=filters, chunks=local_chunks)

    dense_norm = _normalize(dense, "score")
    sparse_norm = _normalize(sparse, "score")
    by_id: dict[str, dict[str, Any]] = {}
    for item in dense + sparse:
        by_id[item["chunk_id"]] = item

    combined = []
    for chunk_id, item in by_id.items():
        score = settings.rag_dense_weight * dense_norm.get(chunk_id, 0.0)
        score += settings.rag_sparse_weight * sparse_norm.get(chunk_id, 0.0)
        combined.append({**item, "score": score})

    results = rerank(query, combined, top_k=top_k)
    if save_snapshot:
        save_retrieval_snapshot(query, filters, results)
    return {"query": query, "results": results}

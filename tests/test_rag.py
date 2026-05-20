from app.infra.embeddings import embed_text
from app.services.rag_service import chunk_document, search_hybrid, search_sparse
from app.services.tool_service import rag_search_tool


def tiny_chunks():
    chunks = [
        {
            "chunk_id": "docs-readme.md::s0w0",
            "text": "Authentication tokens use JWT and should be configured in settings.",
            "source_type": "docs",
            "source_id": "docs/README.md",
            "url": "https://example.test/readme",
            "metadata": {"source_type": "docs", "repo": "owner/repo", "title": "README"},
        },
        {
            "chunk_id": "issue_10::body",
            "text": "Closed issue: auth.py raised TypeError after upgrading Python 3.11.",
            "source_type": "issue",
            "source_id": "issue_10",
            "url": "https://example.test/issues/10",
            "metadata": {
                "source_type": "issue",
                "repo": "owner/repo",
                "labels": ["bug"],
                "issue_number": 10,
                "title": "auth.py TypeError",
            },
        },
    ]
    for chunk in chunks:
        chunk["embedding"] = embed_text(chunk["text"])
    return chunks


def test_chunking_uses_markdown_sections_and_metadata() -> None:
    document = {
        "source_type": "docs",
        "source_id": "docs/README.md",
        "title": "README",
        "url": "https://example.test/readme",
        "text": "# Install\nUse pip.\n\n# Auth\nConfigure JWT tokens.",
        "metadata": {"repo": "owner/repo", "path": "README.md"},
    }
    chunks = chunk_document(document)
    assert len(chunks) == 2
    assert chunks[0]["metadata"]["section"] == "Install"
    assert chunks[0]["char_count"] > 0


def test_sparse_retrieval_finds_exact_code_terms() -> None:
    results = search_sparse("TypeError auth.py Python 3.11", chunks=tiny_chunks())
    assert results[0]["chunk_id"] == "issue_10::body"


def test_hybrid_retrieval_returns_sorted_results() -> None:
    response = search_hybrid("JWT authentication token", chunks=tiny_chunks(), top_k=2)
    scores = [result["score"] for result in response["results"]]
    assert response["results"][0]["chunk_id"] == "docs-readme.md::s0w0"
    assert scores == sorted(scores, reverse=True)


def test_filters_limit_results() -> None:
    response = search_hybrid(
        "JWT authentication token",
        chunks=tiny_chunks(),
        filters={"source_type": "issue"},
        top_k=5,
    )
    assert [result["source_type"] for result in response["results"]] == ["issue"]


def test_rag_search_tool_shape(monkeypatch) -> None:
    monkeypatch.setattr("app.services.rag_service.load_chunks", lambda: tiny_chunks())
    response = rag_search_tool("JWT authentication token", top_k=1)
    assert response["query"] == "JWT authentication token"
    assert response["results"][0]["chunk_id"]

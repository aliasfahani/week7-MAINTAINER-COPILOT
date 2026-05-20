import re


def split_sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text.strip()) if sentence.strip()]


def summarize_text(text: str, max_sentences: int = 3, max_chars: int = 600) -> dict:
    """Simple extractive summarizer for Day 2.

    We keep the first few meaningful sentences because issue threads often put
    the bug report, environment, and attempted fix near the top. This gives the
    API a practical integration point before an LLM summarizer is wired in.
    """

    normalized = " ".join((text or "").split())
    if not normalized:
        return {"summary": "", "method": "simple_extractive"}

    sentences = split_sentences(normalized)
    summary = " ".join(sentences[:max_sentences]) if sentences else normalized
    if len(summary) > max_chars:
        summary = summary[: max_chars - 3].rstrip() + "..."
    return {"summary": summary, "method": "simple_extractive"}

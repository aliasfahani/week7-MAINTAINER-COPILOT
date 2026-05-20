def summarize_text(text: str) -> dict:
    """Day 1 summarization stub."""

    trimmed = " ".join(text.split())[:200]
    return {"summary": trimmed}

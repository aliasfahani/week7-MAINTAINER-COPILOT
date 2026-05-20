LABELS = ["bug", "feature", "docs", "question"]


def classify_text(text: str) -> dict:
    """Day 1 deterministic stub until the transformer is trained."""

    return {
        "label": "bug",
        "confidence": 0.5,
        "scores": {"bug": 0.5, "feature": 0.2, "docs": 0.15, "question": 0.15},
    }

import re
import os

summarizer_pipeline = None
MIN_WORDS_FOR_BART = 50


def get_summarizer():
    global summarizer_pipeline

    if summarizer_pipeline is None:
        from transformers import pipeline

        summarizer_pipeline = pipeline(
            "summarization",
            model="facebook/bart-large-cnn",
        )

    return summarizer_pipeline


def summarize_issue(text: str) -> str | None:
    text = text or ""
    if os.getenv("MODEL_SERVER_USE_BART", "").lower() not in {"1", "true", "yes"}:
        return None

    word_count = len(text.split())

    if word_count < MIN_WORDS_FOR_BART:
        return None

    try:
        summarizer = get_summarizer()

        result = summarizer(
            text,
            min_length=20,
            max_length=80,
            do_sample=False,
            truncation=True,  # Truncates the input to the model's maximum allowed size.
        )
    except Exception:
        # The demo should still summarize when the optional transformer model is
        # unavailable, for example when weights are not downloaded locally.
        return None

    return result[0]["summary_text"]


def _extractive_summary(text: str, max_chars: int = 400, max_sentences: int = 3) -> str:
    """Dependency-light summarizer used by default for Day 5 demos."""

    text = text.strip()
    if not text:
        return ""

    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", text) if part.strip()]
    if not sentences:
        return text[:max_chars]

    picked: list[str] = []
    length = 0
    for sentence in sentences:
        if length + len(sentence) > max_chars and picked:
            break
        picked.append(sentence)
        length += len(sentence)
        if len(picked) >= max_sentences:
            break

    return " ".join(picked) if picked else text[:max_chars]


def summarize_text(text: str) -> dict[str, str]:
    """Public entry point for model_server /summarize and main.py."""

    summary = summarize_issue(text)
    if summary:
        return {"summary": summary, "method": "bart-large-cnn"}
    return {"summary": _extractive_summary(text), "method": "simple_extractive"}

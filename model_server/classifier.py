from pathlib import Path

from model_server.model_loader import DEFAULT_MODEL_DIR, load_classifier

LABELS = ["bug", "feature", "docs", "question"]


def build_issue_text(title: str = "", body: str = "", text: str | None = None) -> str:
    if text:
        return text.strip()
    return f"{title}\n\n{body}".strip()


def classify_issue(
    title: str = "",
    body: str = "",
    text: str | None = None,
    model_dir: str | Path = DEFAULT_MODEL_DIR,
    max_length: int = 256,
) -> dict:
    loaded = load_classifier(model_dir)
    torch = loaded["torch"]
    tokenizer = loaded["tokenizer"]
    model = loaded["model"]

    issue_text = build_issue_text(title=title, body=body, text=text)
    encoded = tokenizer(
        issue_text,
        truncation=True,
        padding=True,
        max_length=max_length,
        return_tensors="pt",
    )

    with torch.no_grad():
        logits = model(**encoded).logits[0]
        probabilities = torch.softmax(logits, dim=-1)

    scores = {
        loaded["id_to_label"][index]: float(probabilities[index].item())
        for index in range(len(probabilities))
    }
    label = max(scores, key=scores.get)

    return {
        "label": label,
        "confidence": scores[label],
        "scores": scores,
        "model_version": loaded["model_version"],
    }

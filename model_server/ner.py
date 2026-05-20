import re


PATTERNS = [
    ("file", re.compile(r"\b[\w./-]+\.(?:py|ts|tsx|js|jsx|yaml|yml|json|md|toml|ini|css|html)\b")),
    ("version", re.compile(r"\bv?\d+\.\d+(?:\.\d+)?\b")),
    ("version", re.compile(r"\b(?:Python|Node|React|Django|FastAPI)\s+\d+(?:\.\d+)?\b", re.IGNORECASE)),
    ("error", re.compile(r"\b[A-Z][A-Za-z]+(?:Error|Exception)\b")),
    ("function", re.compile(r"\b[a-zA-Z_][\w_]*\(\)")),
    ("identifier", re.compile(r"\b[a-zA-Z_][\w_]*(?:\.[a-zA-Z_][\w_]*)+\b")),
]


def extract_entities(text: str) -> dict:
    """Extract issue-triage entities with lightweight rules.

    This is integration-focused Day 2 NER: it captures code-shaped clues that
    maintainers care about, and can later be replaced by a trained NER model.
    """

    entities = []
    seen = set()
    for entity_type, pattern in PATTERNS:
        for match in pattern.finditer(text or ""):
            value = match.group(0)
            key = (value, entity_type)
            if key in seen:
                continue
            seen.add(key)
            entities.append({"text": value, "type": entity_type})
    return {"entities": entities}

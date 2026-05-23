import re


TECH_KEYWORDS = [
    "JWT", "OAuth", "Redis", "PostgreSQL", "MySQL", "SQLite", "MongoDB",
    "FastAPI", "Flask", "Django", "React", "Next.js", "Node.js",
    "Docker", "Kubernetes", "API", "REST", "GraphQL",
    "pandas", "DataFrame", "Series", "NumPy",
    "CSV", "JSON", "Parquet", "SQL",
    "read_csv", "pd.merge", "merge", "concat", "groupby",
]


PATTERNS = [
    (
        "file",
        re.compile(
            r"\b[\w./-]+\.(?:py|ts|tsx|js|jsx|yaml|yml|json|md|toml|ini|css|html)\b"
        ),
    ),
    ("version", re.compile(r"\bv?\d+\.\d+(?:\.\d+)?\b")),
    (
        "version",
        re.compile(
            r"\b(?:Python|Node|React|Django|FastAPI|Pandas|pandas)\s+\d+(?:\.\d+)?\b",
            re.IGNORECASE,
        ),
    ),
    ("error", re.compile(r"\b[A-Z][A-Za-z]+(?:Error|Exception)\b")),
    ("function", re.compile(r"\b[a-zA-Z_][\w_]*\(\)")),
    ("function", re.compile(r"\b(?:pd\.)?[a-zA-Z_][\w_]*(?:\.[a-zA-Z_][\w_]*)?\(\)")),
    ("api", re.compile(r"\bpd\.[a-zA-Z_][\w_]*\b")),
    # Pandas issues often mention parameters such as parse_dates without
    # parentheses. Treat snake_case names as technical parameters so docs and
    # usage questions still produce useful entities.
    ("parameter", re.compile(r"\b[a-zA-Z]+_[a-zA-Z_][\w_]*\b")),
    ("identifier", re.compile(r"\b[a-zA-Z_][\w_]*(?:\.[a-zA-Z_][\w_]*)+\b")),
]


def extract_entities(text: str) -> dict:
    """Extract technical entities from issue text.

    Returns:
        {
            "entities": [
                {"text": "...", "type": "..."},
                ...
            ]
        }
    """

    entities: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    text = text or ""

    for entity_type, pattern in PATTERNS:
        for match in pattern.finditer(text):
            value = match.group(0)
            key = (value.lower(), entity_type)

            if key in seen:
                continue

            seen.add(key)
            entities.append({"text": value, "type": entity_type})

    for keyword in TECH_KEYWORDS:
        pattern = re.compile(r"\b" + re.escape(keyword) + r"\b", re.IGNORECASE)

        for match in pattern.finditer(text):
            value = match.group(0)
            key = (value.lower(), "technology")

            if key in seen:
                continue

            seen.add(key)
            entities.append({"text": value, "type": "technology"})

    return {"entities": entities}

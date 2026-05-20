import hashlib
import math
from functools import lru_cache

from app.config import get_settings


def _hash_embedding(text: str, dimension: int) -> list[float]:
    """Deterministic fallback embedding for tests and offline development.

    Real retrieval should use SentenceTransformers. This fallback keeps unit
    tests fast and lets scripts run in environments where model downloads are
    unavailable.
    """

    vector = [0.0] * dimension
    for token in text.lower().split():
        digest = hashlib.sha256(token.encode("utf-8")).digest()
        index = int.from_bytes(digest[:4], "big") % dimension
        sign = 1.0 if digest[4] % 2 == 0 else -1.0
        vector[index] += sign
    norm = math.sqrt(sum(value * value for value in vector)) or 1.0
    return [value / norm for value in vector]


@lru_cache(maxsize=1)
def _load_sentence_transformer():
    settings = get_settings()
    if settings.embedding_backend != "sentence-transformers":
        return None
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        return None
    try:
        return SentenceTransformer(settings.embedding_model_name)
    except Exception:
        # Model download may fail without network access. Retrieval still works
        # with the deterministic fallback, just with lower semantic quality.
        return None


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]


def embed_texts(texts: list[str]) -> list[list[float]]:
    settings = get_settings()
    model = _load_sentence_transformer()
    if model is None:
        return [_hash_embedding(text, settings.embedding_dimension) for text in texts]

    embeddings = model.encode(texts, normalize_embeddings=True)
    return [embedding.tolist() for embedding in embeddings]

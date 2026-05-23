import json
import logging
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

DEFAULT_MODEL_DIR = Path(os.getenv("CLASSIFIER_MODEL_DIR", "artifacts/classifier"))


class ModelArtifactMissingError(RuntimeError):
    pass


def validate_classifier_artifact(model_dir: Path = DEFAULT_MODEL_DIR) -> None:
    required = ["config.json", "tokenizer_config.json", "label_mapping.json"]
    missing = [name for name in required if not (model_dir / name).exists()]
    if missing:
        raise ModelArtifactMissingError(
            f"Classifier artifact is missing or incomplete at {model_dir}. Missing: {missing}. "
            "Run notebooks/pandas_issue_classifier_colab.ipynb and copy the exported files into artifacts/classifier."
        )


def import_inference_dependencies():
    try:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
    except ImportError as exc:
        raise ModelArtifactMissingError(
            "Classifier inference dependencies are not installed. Run pip install -r requirements.txt."
        ) from exc
    return torch, AutoTokenizer, AutoModelForSequenceClassification


@lru_cache(maxsize=1)
def load_classifier(model_dir: str | Path = DEFAULT_MODEL_DIR) -> dict[str, Any]:
    """Load and cache the classifier once per model_server process.

    Loading transformer weights is expensive. This cache keeps inference fast
    and avoids re-reading model artifacts on every `/classify` request.
    """

    model_path = Path(model_dir)
    validate_classifier_artifact(model_path)
    torch, AutoTokenizer, AutoModelForSequenceClassification = import_inference_dependencies()

    label_mapping = json.loads((model_path / "label_mapping.json").read_text(encoding="utf-8"))
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.eval()

    logger.info("Loaded classifier artifact from %s", model_path)
    return {
        "torch": torch,
        "tokenizer": tokenizer,
        "model": model,
        "label_to_id": label_mapping["label_to_id"],
        "id_to_label": {int(key): value for key, value in label_mapping["id_to_label"].items()},
        "model_version": model_path.name or "local-distilbert",
    }

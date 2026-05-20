import logging

from fastapi import FastAPI, HTTPException

from model_server.classifier import classify_issue
from model_server.model_loader import ModelArtifactMissingError
from model_server.ner import extract_entities
from model_server.schemas import ClassifyRequest, ClassifyResponse, NerResponse, SummarizeResponse, TextRequest
from model_server.summarizer import summarize_text

logger = logging.getLogger(__name__)
app = FastAPI(title="Maintainer's Copilot Model Server")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "model_server"}


@app.post("/classify", response_model=ClassifyResponse)
def classify(request: ClassifyRequest) -> dict:
    try:
        return classify_issue(title=request.title, body=request.body, text=request.text)
    except ModelArtifactMissingError as exc:
        # Missing model artifacts are expected before the first training run.
        # Return a controlled 503 instead of leaking a stack trace to callers.
        logger.warning("Classifier unavailable: %s", exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/ner", response_model=NerResponse)
def ner(request: TextRequest) -> dict:
    return extract_entities(request.text)


@app.post("/summarize", response_model=SummarizeResponse)
def summarize(request: TextRequest) -> dict:
    return summarize_text(request.text)

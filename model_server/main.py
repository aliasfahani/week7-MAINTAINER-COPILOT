from fastapi import FastAPI

from model_server.classifier import classify_text
from model_server.ner import extract_entities
from model_server.schemas import ClassifyResponse, NerResponse, SummarizeResponse, TextRequest
from model_server.summarizer import summarize_text

app = FastAPI(title="Maintainer's Copilot Model Server")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "model_server"}


@app.post("/classify", response_model=ClassifyResponse)
def classify(request: TextRequest) -> dict:
    return classify_text(request.text)


@app.post("/ner", response_model=NerResponse)
def ner(request: TextRequest) -> dict:
    return extract_entities(request.text)


@app.post("/summarize", response_model=SummarizeResponse)
def summarize(request: TextRequest) -> dict:
    return summarize_text(request.text)

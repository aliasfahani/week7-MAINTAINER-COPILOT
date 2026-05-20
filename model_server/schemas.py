from pydantic import BaseModel


class TextRequest(BaseModel):
    text: str


class ClassifyResponse(BaseModel):
    label: str
    confidence: float
    scores: dict[str, float]


class NerResponse(BaseModel):
    entities: list[dict[str, str | float]]


class SummarizeResponse(BaseModel):
    summary: str

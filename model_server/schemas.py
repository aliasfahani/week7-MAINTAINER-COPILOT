from pydantic import BaseModel, Field


class TextRequest(BaseModel):
    text: str = Field(default="", description="Plain text to process.")


class ClassifyRequest(BaseModel):
    title: str = ""
    body: str = ""
    text: str | None = None


class ClassifyResponse(BaseModel):
    label: str
    confidence: float
    scores: dict[str, float]
    model_version: str


class Entity(BaseModel):
    text: str
    type: str


class NerResponse(BaseModel):
    entities: list[Entity]


class SummarizeResponse(BaseModel):
    summary: str
    method: str

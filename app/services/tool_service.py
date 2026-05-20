from typing import Any

from app.infra.model_client import ModelServerClient, get_model_client


def classify_issue_tool(
    title: str,
    body: str,
    client: ModelServerClient | None = None,
) -> dict[str, Any]:
    """Tool wrapper for issue classification.

    The future single tool-calling LLM should call this function as one tool.
    It delegates model inference to model_server instead of running ML inside
    the API process.
    """

    model_client = client or get_model_client()
    return model_client.classify_issue(title=title, body=body)


def extract_entities_tool(text: str, client: ModelServerClient | None = None) -> dict[str, Any]:
    model_client = client or get_model_client()
    return model_client.extract_entities(text=text)


def summarize_thread_tool(text: str, client: ModelServerClient | None = None) -> dict[str, Any]:
    model_client = client or get_model_client()
    return model_client.summarize_text(text=text)

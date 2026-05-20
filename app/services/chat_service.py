from typing import Any

from app.infra.model_client import ModelServerClient
from app.services.tool_service import classify_issue_tool


def handle_internal_chat_action(
    action: str,
    title: str = "",
    body: str = "",
    client: ModelServerClient | None = None,
) -> dict[str, Any]:
    """Small Day 2 proof path for tool execution.

    This is intentionally not full chatbot orchestration. It only proves the API
    service layer can call the classifier tool that will later be exposed to one
    tool-calling LLM.
    """

    if action != "classify":
        raise ValueError(f"Unsupported Day 2 chat action: {action}")
    return classify_issue_tool(title=title, body=body, client=client)

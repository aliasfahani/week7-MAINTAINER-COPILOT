from typing import Any


def plan_tool_calls(message: str, issue: dict | None = None) -> list[dict[str, Any]]:
    """Fallback for environments without an LLM API key.

    The production design is still one tool-calling LLM. This deterministic
    planner is a clearly marked local fallback so the app can be demoed without
    pretending multiple agents exist.
    """

    lowered = message.lower()
    calls = []
    if issue and ("classify" in lowered or "issue" in lowered):
        calls.append({"name": "classify_issue", "arguments": issue})
    if "entity" in lowered or "extract" in lowered:
        calls.append({"name": "extract_entities", "arguments": {"text": message}})
    if "summarize" in lowered or "summary" in lowered:
        calls.append({"name": "summarize_thread", "arguments": {"text": issue.get("body", message) if issue else message}})
    if "similar" in lowered or "docs" in lowered or "resolved" in lowered or "rag" in lowered:
        calls.append({"name": "rag_search", "arguments": {"query": message, "top_k": 5}})
    if "remember" in lowered:
        calls.append({"name": "write_memory", "arguments": {"text": message, "metadata": {"source": "chat_explicit"}}})
    return calls


def synthesize_answer(message: str, tool_results: list[dict[str, Any]]) -> str:
    if not tool_results:
        return "I can help triage this. Ask me to classify, summarize, extract entities, search docs/issues, or remember a note."
    parts = ["Here is what I found:"]
    for result in tool_results:
        name = result["name"]
        if result.get("ok"):
            parts.append(f"- {name}: {result['result']}")
        else:
            parts.append(f"- {name} is unavailable: {result['error']}")
    return "\n".join(parts)

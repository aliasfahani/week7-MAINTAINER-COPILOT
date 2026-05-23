import json
import re
from typing import Any

import requests

from app.config import get_settings
from app.infra.redaction import redact_text


GEMINI_PLACEHOLDERS = {"", "replace-with-your-gemini-api-key", "your-gemini-api-key-here"}


def gemini_is_configured() -> bool:
    settings = get_settings()
    return settings.llm_provider.lower() == "gemini" and settings.gemini_api_key not in GEMINI_PLACEHOLDERS


def _gemini_generate_text(prompt: str) -> str:
    """Call Gemini's generateContent endpoint with a plain-text prompt.

    This keeps the project dependency-light: no Google SDK is required for the
    demo. The API key comes from `.env`, and callers fall back to deterministic
    local behavior if Gemini is not configured or temporarily fails.
    """

    settings = get_settings()
    model = settings.gemini_model.strip()
    base_url = settings.gemini_api_url.rstrip("/")
    url = f"{base_url}/models/{model}:generateContent"
    payload = {"contents": [{"role": "user", "parts": [{"text": prompt}]}]}
    response = requests.post(
        url,
        headers={"Content-Type": "application/json", "x-goog-api-key": settings.gemini_api_key},
        json=payload,
        timeout=settings.gemini_timeout_seconds,
    )
    response.raise_for_status()
    data = response.json()
    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError("Gemini returned an unexpected response shape") from exc


def _extract_json_array(text: str) -> list[dict[str, Any]]:
    """Parse JSON from Gemini even if it wraps the result in a markdown fence."""

    cleaned = text.strip()
    fence = re.search(r"```(?:json)?\s*(.*?)```", cleaned, flags=re.DOTALL | re.IGNORECASE)
    if fence:
        cleaned = fence.group(1).strip()
    parsed = json.loads(cleaned)
    if isinstance(parsed, dict) and "tool_calls" in parsed:
        parsed = parsed["tool_calls"]
    if not isinstance(parsed, list):
        raise ValueError("Gemini tool plan must be a JSON list")
    return parsed


TOOL_PLANNING_PROMPT = """
You are Maintainer's Copilot. Choose tool calls for one chat turn.
Return ONLY valid JSON, with no markdown or explanation.

Available tools:
- classify_issue: arguments {"title": string, "body": string}
- extract_entities: arguments {"text": string}
- summarize_thread: arguments {"text": string}
- rag_search: arguments {"query": string, "filters": object|null, "top_k": number}
- write_memory: arguments {"text": string, "metadata": object}

Rules:
- Use zero or more tools.
- Only write memory when the user explicitly asks you to remember something.
- If an issue object is provided and the user asks to classify or triage it, call classify_issue.
- If the user asks for similar docs/issues or resolved issues, call rag_search.
- Return this exact shape:
[
  {"name": "tool_name", "arguments": {...}}
]
"""


def plan_tool_calls(message: str, issue: dict | None = None) -> list[dict[str, Any]]:
    """Plan tools with Gemini when configured, otherwise use local fallback.

    The production path is one LLM deciding which tools to call. The keyword
    branch remains a clearly marked fallback for local demos before the user
    adds a real Gemini API key.
    """

    if gemini_is_configured():
        prompt = (
            TOOL_PLANNING_PROMPT
            + "\nUser message:\n"
            + message
            + "\n\nIssue JSON:\n"
            + json.dumps(issue or {}, ensure_ascii=False)
        )
        try:
            return _extract_json_array(_gemini_generate_text(prompt))
        except Exception as exc:
            print(f"Gemini tool planning failed; using fallback planner: {redact_text(str(exc))}")

    lowered = message.lower()
    calls = []
    if issue and ("classify" in lowered or "issue" in lowered):
        calls.append({"name": "classify_issue", "arguments": issue})
    if "entity" in lowered or "extract" in lowered:
        calls.append({"name": "extract_entities", "arguments": {"text": message}})
    if "summarize" in lowered or "summary" in lowered:
        calls.append({"name": "summarize_thread", "arguments": {"text": issue.get("body", message) if issue else message}})
    if "similar" in lowered or "docs" in lowered or "resolved" in lowered or "rag" in lowered:
        issue_context = ""
        if issue:
            issue_context = f"\n\nIssue title: {issue.get('title', '')}\nIssue body: {issue.get('body', '')}"
        calls.append({"name": "rag_search", "arguments": {"query": f"{message}{issue_context}".strip(), "top_k": 5}})
    if "remember" in lowered:
        calls.append({"name": "write_memory", "arguments": {"text": message, "metadata": {"source": "chat_explicit"}}})
    return calls


def _classification_summary(tool_results: list[dict[str, Any]]) -> str | None:
    for result in tool_results:
        if result.get("ok") and result.get("name") == "classify_issue":
            payload = result.get("result", {})
            label = payload.get("label")
            confidence = payload.get("confidence")
            if label and isinstance(confidence, int | float):
                return f"I would triage this as **{label}** with {confidence:.0%} confidence."
            if label:
                return f"I would triage this as **{label}**."
    return None


def _rag_rows(tool_results: list[dict[str, Any]]) -> list[dict[str, Any]]:
    for result in tool_results:
        if result.get("ok") and result.get("name") == "rag_search":
            return result.get("result", {}).get("results", [])
    return []


def _issue_troubleshooting_steps(issue: dict | None, rows: list[dict[str, Any]]) -> list[str]:
    """Build practical maintainer guidance when no real LLM key is configured.

    This is intentionally heuristic: the real path should use Gemini to reason
    over tool results. The fallback still needs to be useful during local demos,
    so it turns common pandas issue signals into concrete checks.
    """

    text = f"{issue.get('title', '')} {issue.get('body', '')}".lower() if issue else ""
    steps: list[str] = []

    if "merge" in text or "join" in text:
        steps.extend(
            [
                "Confirm the merge type. If rows should never be dropped, test with `how=\"left\"` or `how=\"outer\"` instead of the default inner merge.",
                "Check key quality on both DataFrames: duplicate keys, missing values, timezone-aware vs timezone-naive datetimes, and dtype mismatches can change join results.",
                "Add `indicator=True` to `pd.merge()` and inspect `left_only`, `right_only`, and `both` counts to see exactly where rows are being lost.",
            ]
        )
    if "datetime" in text or "timestamp" in text or "timezone" in text or "tz" in text:
        steps.append(
            "Normalize datetime keys before merging, for example with `pd.to_datetime(...)`, matching timezone handling, and checking `df[key].dtype` on both sides."
        )
    if "upgrade" in text or "pandas 2" in text or "2.x" in text:
        steps.append(
            "Create a minimal reproduction and run it on the old and new pandas versions so you can tell whether this is a behavior change or a data-shape issue."
        )
    if rows:
        best = rows[0]
        title = best.get("title") or best.get("chunk_id")
        url = best.get("url")
        steps.append(
            f"Compare against the closest resolved issue, **{title}**"
            + (f" ({url})" if url else "")
            + ", especially if it also involves missing rows, joins, or datetime keys."
        )

    if not steps:
        steps = [
            "Ask for a minimal reproduction with sample input, expected output, actual output, pandas version, and platform details.",
            "Search related closed issues and docs for the exact error message, API name, or behavior change.",
            "If the behavior changed after an upgrade, verify it against the previous and current versions before deciding whether it is a bug or usage question.",
        ]
    return steps


def synthesize_answer(message: str, tool_results: list[dict[str, Any]], issue: dict | None = None) -> str:
    if gemini_is_configured():
        prompt = f"""
You are Maintainer's Copilot, an assistant for open-source maintainers.
Use the tool results to answer clearly and honestly.
If a tool failed, say what is unavailable and continue with the useful results.
Recommend concrete troubleshooting steps for the user's issue. Do not only list retrieved issues.

User message:
{message}

Issue JSON:
{json.dumps(issue or {}, ensure_ascii=False)}

Tool results JSON:
{json.dumps(tool_results, ensure_ascii=False, default=str)}
"""
        try:
            return _gemini_generate_text(prompt).strip()
        except Exception as exc:
            print(f"Gemini answer synthesis failed; using fallback answer: {redact_text(str(exc))}")

    if not tool_results:
        return "I can help triage this, but I do not have tool results yet. Please include the issue title/body and ask me to classify or search related issues."

    rows = _rag_rows(tool_results)
    parts = ["Here is my triage and troubleshooting guidance:"]
    classification = _classification_summary(tool_results)
    if classification:
        parts.append(f"\n{classification}")

    steps = _issue_troubleshooting_steps(issue, rows)
    parts.append("\nRecommended next checks:")
    for step in steps:
        parts.append(f"- {step}")

    if rows:
        parts.append("\nRelated resolved issues/docs:")
        for item in rows[:3]:
            label = f"issue #{item['issue_number']}" if item.get("issue_number") else item.get("source_type", "source")
            parts.append(
                f"- {item.get('title') or item.get('chunk_id')} ({label}, score {item.get('score')}): "
                f"{item.get('snippet', '').replace(chr(10), ' ')[:220]}"
            )

    for result in tool_results:
        name = result["name"]
        if not result.get("ok"):
            parts.append(f"\n{name} is unavailable: {result['error']}")
        elif name not in {"classify_issue", "rag_search"}:
            parts.append(f"- {name}: {result['result']}")
    return "\n".join(parts)

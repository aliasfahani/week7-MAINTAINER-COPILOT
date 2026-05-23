import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.infra.llm import plan_tool_calls, synthesize_answer
from app.infra.redaction import redact_text
from app.infra.tracing import new_trace_id, trace_span
from app.services.memory_service import append_message, get_conversation_state, search_long_term_memories
from app.services.tool_service import (
    classify_issue_tool,
    extract_entities_tool,
    rag_search_tool,
    summarize_thread_tool,
    write_memory_tool,
)


def _execute_tool(call: dict[str, Any], user_id: int, db: Session) -> dict[str, Any]:
    name = call.get("name", "unknown")
    args = call.get("arguments", {})
    try:
        if name == "classify_issue":
            result = classify_issue_tool(args.get("title", ""), args.get("body", ""))
        elif name == "extract_entities":
            result = extract_entities_tool(args.get("text", ""))
        elif name == "summarize_thread":
            result = summarize_thread_tool(args.get("text", ""))
        elif name == "rag_search":
            result = rag_search_tool(args.get("query", ""), filters=args.get("filters"), top_k=args.get("top_k", 5))
        elif name == "write_memory":
            result = write_memory_tool(user_id, args.get("text", ""), args.get("metadata"), db=db)
        else:
            raise ValueError(f"unknown tool {name}")
        return {"name": name, "ok": True, "result": result}
    except Exception as exc:
        # One failed tool should not crash the whole chat. The final answer can
        # explain what failed and still include results from other tools.
        return {"name": name, "ok": False, "error": redact_text(str(exc))}


def _issue_text(issue: dict | None, fallback: str) -> str:
    if not issue:
        return fallback
    title = issue.get("title", "")
    body = issue.get("body", "")
    combined = f"{title}\n\n{body}".strip()
    return combined or fallback


def _normalize_tool_call(call: dict[str, Any], issue: dict | None, message: str) -> dict[str, Any]:
    """Make LLM/fallback tool arguments reliable for issue triage.

    Gemini may correctly decide to call NER or summarization, but pass only the
    user's instruction ("extract entities") instead of the actual issue body.
    The tools are more useful when they operate on the issue text, so the chat
    service repairs those arguments before execution.
    """

    name = call.get("name")
    args = dict(call.get("arguments") or {})
    issue_text = _issue_text(issue, message)
    if name in {"extract_entities", "summarize_thread"}:
        current_text = str(args.get("text", "")).strip()
        if not current_text or current_text.lower() == message.lower() or len(current_text) < 40:
            args["text"] = issue_text
    return {**call, "arguments": args}


def handle_chat(user, db: Session, message: str, conversation_id: str | None = None, issue: dict | None = None) -> dict:
    trace_id = new_trace_id()
    conversation_id = conversation_id or uuid.uuid4().hex
    safe_message = redact_text(message)
    issue_payload = issue or {}

    with trace_span(trace_id, "chat.request", conversation_id=conversation_id):
        short_term = get_conversation_state(conversation_id)
        memories = search_long_term_memories(db, user.id, safe_message, top_k=3)
        tool_calls = plan_tool_calls(safe_message, issue_payload)
        tool_results = []
        for call in tool_calls:
            call = _normalize_tool_call(call, issue_payload, safe_message)
            with trace_span(trace_id, "tool.call", tool=call["name"]):
                tool_results.append(_execute_tool(call, user.id, db))

        answer = synthesize_answer(safe_message, tool_results, issue_payload)
        if memories:
            answer += f"\n\nRelevant remembered context: {memories[0]['text']}"

        append_message(conversation_id, "user", safe_message)
        append_message(conversation_id, "assistant", answer)
        return {
            "conversation_id": conversation_id,
            "answer": answer,
            "tool_calls": tool_results,
            "trace_id": trace_id,
            "history_count": len(short_term) + 2,
        }


def handle_internal_chat_action(action: str, title: str = "", body: str = "", client=None) -> dict[str, Any]:
    if action != "classify":
        raise ValueError(f"Unsupported Day 2 chat action: {action}")
    return classify_issue_tool(title=title, body=body, client=client)

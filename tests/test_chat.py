import pytest

from app.services.chat_service import handle_internal_chat_action, _execute_tool


class FakeModelClient:
    def classify_issue(self, title: str, body: str) -> dict:
        return {
            "label": "bug",
            "confidence": 0.9,
            "scores": {"bug": 0.9, "feature": 0.05, "docs": 0.03, "question": 0.02},
            "model_version": "test",
        }


def test_chat_service_can_call_classifier_tool() -> None:
    result = handle_internal_chat_action(
        action="classify",
        title="Crash on startup",
        body="Traceback shows RuntimeError",
        client=FakeModelClient(),
    )
    assert result["label"] == "bug"


def test_chat_service_rejects_unknown_day_2_action() -> None:
    with pytest.raises(ValueError):
        handle_internal_chat_action(action="unknown", client=FakeModelClient())


def test_tool_failure_is_returned_not_raised() -> None:
    result = _execute_tool({"name": "unknown", "arguments": {}}, user_id=1, db=None)
    assert result["ok"] is False
    assert "unknown tool" in result["error"]

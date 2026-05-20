from app.services.memory_service import append_message, clear_conversation_state, get_conversation_state


def test_short_term_memory_stores_and_loads() -> None:
    conversation_id = "test-conversation"
    clear_conversation_state(conversation_id)
    append_message(conversation_id, "user", "hello")
    assert get_conversation_state(conversation_id) == [{"role": "user", "content": "hello"}]
    clear_conversation_state(conversation_id)
    assert get_conversation_state(conversation_id) == []

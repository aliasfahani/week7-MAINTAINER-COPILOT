from app.services.widget_service import origin_allowed, safe_widget


class Widget:
    widget_id = "demo"
    theme = {"primaryColor": "#2563eb"}
    greeting = "Hi"
    enabled_tools = ["rag_search"]


def test_origin_allowlist() -> None:
    assert origin_allowed(["https://example.com"], "https://example.com/page")
    assert not origin_allowed(["https://example.com"], "https://evil.test")
    assert origin_allowed(["*"], "https://anything.test")


def test_safe_widget_excludes_admin_fields() -> None:
    data = safe_widget(Widget())
    assert set(data) == {"widget_id", "theme", "greeting", "enabled_tools"}

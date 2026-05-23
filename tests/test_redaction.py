from app.infra.redaction import redact_text


def test_redacts_fake_tokens() -> None:
    text = "token=ghp_fakegithubtoken1234567890 and api_key=sk-test12345678901234567890 password=supersecret"
    redacted = redact_text(text)
    assert "ghp_" not in redacted
    assert "sk-" not in redacted
    assert "supersecret" not in redacted
    assert "[REDACTED]" in redacted


def test_redacts_jwt_like_string() -> None:
    redacted = redact_text("jwt eyJabc.def.ghi")
    assert "eyJabc.def.ghi" not in redacted


def test_redacts_gemini_style_key() -> None:
    redacted = redact_text("GEMINI_API_KEY=AIzaFakeGeminiKey123456789012345")
    assert "AIza" not in redacted

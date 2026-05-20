from app.infra.redaction import redact_text


def test_redacts_fake_tokens() -> None:
    text = "token=ghp_abcdefghijklmnopqrstuvwxyz123456 and api_key=sk-abcdefghijklmnopqrstuv"
    redacted = redact_text(text)
    assert "ghp_" not in redacted
    assert "sk-" not in redacted
    assert "[REDACTED]" in redacted


def test_redacts_jwt_like_string() -> None:
    redacted = redact_text("jwt eyJabc.def.ghi")
    assert "eyJabc.def.ghi" not in redacted

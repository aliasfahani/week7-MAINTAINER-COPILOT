import logging

from app.infra.redaction import redact_text


def log_safe(logger: logging.Logger, level: int, message: str, **fields) -> None:
    safe_fields = {key: redact_text(str(value)) for key, value in fields.items()}
    logger.log(level, redact_text(message), extra=safe_fields)

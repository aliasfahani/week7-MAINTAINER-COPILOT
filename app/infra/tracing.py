import logging
import time
import uuid
from contextlib import contextmanager

logger = logging.getLogger("maintainers_copilot.trace")


def new_trace_id() -> str:
    return uuid.uuid4().hex


@contextmanager
def trace_span(trace_id: str, name: str, **fields):
    started = time.time()
    logger.info("trace start", extra={"trace_id": trace_id, "span": name, **fields})
    try:
        yield
        logger.info("trace end", extra={"trace_id": trace_id, "span": name, "ms": int((time.time() - started) * 1000)})
    except Exception:
        logger.exception("trace error", extra={"trace_id": trace_id, "span": name})
        raise

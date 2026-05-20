import json
import time
from typing import Any

from app.config import get_settings

_memory_store: dict[str, tuple[float, str]] = {}


class RedisState:
    def __init__(self):
        self.settings = get_settings()
        self._client = None

    def client(self):
        if self._client is not None:
            return self._client
        try:
            import redis

            self._client = redis.Redis(
                host=self.settings.redis_host,
                port=self.settings.redis_port,
                decode_responses=True,
                socket_connect_timeout=1,
            )
            self._client.ping()
        except Exception:
            self._client = None
        return self._client

    def get_json(self, key: str, default: Any):
        client = self.client()
        if client:
            value = client.get(key)
            return json.loads(value) if value else default
        expires_at, value = _memory_store.get(key, (0, ""))
        if expires_at < time.time():
            _memory_store.pop(key, None)
            return default
        return json.loads(value)

    def set_json(self, key: str, value: Any, ttl: int) -> None:
        encoded = json.dumps(value)
        client = self.client()
        if client:
            client.setex(key, ttl, encoded)
            return
        _memory_store[key] = (time.time() + ttl, encoded)

    def delete(self, key: str) -> None:
        client = self.client()
        if client:
            client.delete(key)
        _memory_store.pop(key, None)


redis_state = RedisState()

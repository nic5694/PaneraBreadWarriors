from unittest.mock import patch

from app.services.cache import RedisCache


class FakeRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ex=None):
        self.store[key] = value

    def incr(self, key):
        value = int(self.store.get(key, 0)) + 1
        self.store[key] = str(value)
        return value


def test_redis_cache_round_trip_and_invalidation(monkeypatch):
    fake_client = FakeRedis()

    monkeypatch.setenv("REDIS_CACHE_ENABLED", "true")
    monkeypatch.setenv("REDIS_URL", "redis://example:6379/0")
    monkeypatch.setenv("REDIS_CACHE_PREFIX", "tests")
    monkeypatch.setenv("REDIS_CACHE_TTL_SECONDS", "30")

    with patch("app.services.cache.Redis.from_url", return_value=fake_client):
        cache = RedisCache()

        payload = [{"id": 1, "name": "Alice"}]
        assert cache.set_json("users", "list", 1, 10, value=payload) is True
        assert cache.get_json("users", "list", 1, 10) == payload

        assert cache.invalidate_namespace("users") is True
        assert cache.get_json("users", "list", 1, 10) is None
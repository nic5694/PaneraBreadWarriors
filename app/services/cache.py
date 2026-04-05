import json
import logging
import os

from redis import Redis
from redis.exceptions import RedisError


logger = logging.getLogger(__name__)


def _is_truthy(value):
    return str(value).lower() in {"1", "true", "yes", "on"}


class RedisCache:
    def __init__(self):
        self.enabled = _is_truthy(os.environ.get("REDIS_CACHE_ENABLED", "false"))
        self.url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
        self.prefix = os.environ.get("REDIS_CACHE_PREFIX", "gitrev")
        self.default_ttl = int(os.environ.get("REDIS_CACHE_TTL_SECONDS", "120"))
        self._client = None

    def _get_client(self):
        if not self.enabled:
            return None

        if self._client is None:
            try:
                self._client = Redis.from_url(self.url, decode_responses=True)
            except Exception as exc:
                logger.warning("Redis cache disabled: %s", exc)
                self.enabled = False
                return None

        return self._client

    def _version_key(self, namespace):
        return f"{self.prefix}:{namespace}:version"

    def _data_key(self, namespace, *parts):
        version = self._get_namespace_version(namespace)
        suffix = ":".join(str(part) for part in parts if part is not None)
        base_key = f"{self.prefix}:{namespace}:v{version}"
        return f"{base_key}:{suffix}" if suffix else base_key

    def _get_namespace_version(self, namespace):
        client = self._get_client()
        if client is None:
            return 1

        version_key = self._version_key(namespace)
        try:
            version = client.get(version_key)
            if version is None:
                client.set(version_key, 1)
                return 1
            return int(version)
        except (RedisError, TypeError, ValueError):
            logger.exception("Redis version lookup failed for namespace=%s", namespace)
            return 1

    def get_json(self, namespace, *parts):
        client = self._get_client()
        if client is None:
            return None

        try:
            cached = client.get(self._data_key(namespace, *parts))
            if cached is None:
                return None
            return json.loads(cached)
        except (RedisError, TypeError, ValueError, json.JSONDecodeError):
            logger.exception("Redis cache read failed for namespace=%s", namespace)
            return None

    def set_json(self, namespace, *parts, value, ttl=None):
        client = self._get_client()
        if client is None:
            return False

        try:
            client.set(self._data_key(namespace, *parts), json.dumps(value), ex=ttl or self.default_ttl)
            return True
        except (RedisError, TypeError, ValueError):
            logger.exception("Redis cache write failed for namespace=%s", namespace)
            return False

    def invalidate_namespace(self, namespace):
        client = self._get_client()
        if client is None:
            return False

        try:
            client.incr(self._version_key(namespace))
            return True
        except RedisError:
            logger.exception("Redis cache invalidation failed for namespace=%s", namespace)
            return False


cache = RedisCache()
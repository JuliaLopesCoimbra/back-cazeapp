import json
import redis
from typing import Optional, Any
from app.config.settings import settings
import logging

logger = logging.getLogger(__name__)


class RedisClient:
    _instance: Optional['RedisClient'] = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._client is None:
            try:
                if settings.REDIS_URL:
                    self._client = redis.from_url(settings.REDIS_URL, decode_responses=True,
                                                   socket_connect_timeout=5, socket_timeout=5, retry_on_timeout=True)
                else:
                    self._client = redis.Redis(host=settings.REDIS_HOST, port=settings.REDIS_PORT,
                                               db=settings.REDIS_DB, password=settings.REDIS_PASSWORD,
                                               decode_responses=True, socket_connect_timeout=5,
                                               socket_timeout=5, retry_on_timeout=True)
                self._client.ping()
                print("Redis conectado com sucesso")
            except Exception as e:
                print(f"Redis não disponível: {e}")
                self._client = None

    def is_connected(self) -> bool:
        if not self._client:
            return False
        try:
            self._client.ping()
            return True
        except:
            return False

    def get(self, key: str) -> Optional[Any]:
        if not self.is_connected():
            return None
        try:
            value = self._client.get(key)
            return json.loads(value) if value else None
        except Exception as e:
            logger.error(f"Erro ao buscar cache {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if not self.is_connected():
            return False
        try:
            ttl = ttl or settings.REDIS_CACHE_TTL
            return self._client.setex(key, ttl, json.dumps(value, default=str))
        except Exception as e:
            logger.error(f"Erro ao salvar cache {key}: {e}")
            return False

    def delete(self, *keys: str) -> int:
        if not self.is_connected():
            return 0
        try:
            return self._client.delete(*keys)
        except Exception as e:
            logger.error(f"Erro ao deletar cache: {e}")
            return 0

    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        if not self.is_connected():
            return None
        try:
            return self._client.incrby(key, amount)
        except Exception as e:
            logger.error(f"Erro ao incrementar {key}: {e}")
            return None

    def expire(self, key: str, ttl: int) -> bool:
        if not self.is_connected():
            return False
        try:
            return bool(self._client.expire(key, ttl))
        except:
            return False


redis_client = RedisClient()


class CacheKeys:
    @staticmethod
    def user_me(user_id: int) -> str:
        return f"user:me:{user_id}"

    @staticmethod
    def roulette_event(event_id: int) -> str:
        return f"roulette:event:{event_id}"

    @staticmethod
    def prizes_event(event_id: int) -> str:
        return f"prizes:event:{event_id}"

    @staticmethod
    def event_details(event_id: int) -> str:
        return f"event:details:{event_id}"


def check_rate_limit(identifier: str, max_requests: int, window_seconds: int = 60, critical: bool = False) -> tuple[bool, int]:
    if not redis_client.is_connected():
        if critical:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Serviço temporariamente indisponível. Tente novamente em alguns instantes.",
                                headers={"Retry-After": "60"})
        return True, max_requests

    key = f"ratelimit:{identifier}:{window_seconds}"
    current = redis_client.increment(key)

    if current is None:
        if critical:
            from fastapi import HTTPException
            raise HTTPException(status_code=503, detail="Serviço temporariamente indisponível.",
                                headers={"Retry-After": "60"})
        return True, max_requests

    if current == 1:
        redis_client.expire(key, window_seconds)

    remaining = max(0, max_requests - current)
    return current <= max_requests, remaining

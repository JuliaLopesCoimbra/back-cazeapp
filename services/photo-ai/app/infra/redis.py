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
                    self._client = redis.from_url(
                        settings.REDIS_URL,
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        retry_on_timeout=True
                    )
                else:
                    self._client = redis.Redis(
                        host=settings.REDIS_HOST,
                        port=settings.REDIS_PORT,
                        db=settings.REDIS_DB,
                        password=settings.REDIS_PASSWORD,
                        decode_responses=True,
                        socket_connect_timeout=5,
                        socket_timeout=5,
                        retry_on_timeout=True
                    )
                self._client.ping()
                print("Redis conectado com sucesso")
            except Exception as e:
                print(f"Redis não disponível: {e}")
                self._client = None

    @property
    def client(self) -> Optional[redis.Redis]:
        return self._client

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
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Erro ao buscar cache {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        if not self.is_connected():
            return False
        try:
            ttl = ttl or settings.REDIS_CACHE_TTL
            serialized = json.dumps(value, default=str)
            return self._client.setex(key, ttl, serialized)
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

    def exists(self, key: str) -> bool:
        if not self.is_connected():
            return False
        try:
            return bool(self._client.exists(key))
        except:
            return False

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

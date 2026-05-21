from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Roulette Service"
    ENV: str = "development"
    DEBUG: bool = True

    AUTH_DATABASE_URL: str
    ADMIN_DATABASE_URL: Optional[str] = None
    ROULETTE_DATABASE_URL: Optional[str] = None

    DB_POOL_SIZE: int = 50
    DB_MAX_OVERFLOW: int = 30
    DB_SSLMODE: str = "require"

    JWT_SECRET: str
    JWT_REFRESH_SECRET: str

    FRONTEND_URL: str

    AWS_ACCESS_KEY: str
    AWS_SECRET_KEY: str
    AWS_REGION: str
    AWS_BUCKET: str
    AWS_CLOUDFRONT_DOMAIN: str

    MAX_FILE_SIZE_MB: int = 20
    MAX_TOTAL_SIZE_MB: int = 100

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None
    REDIS_CACHE_TTL: int = 3600

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


settings = Settings()

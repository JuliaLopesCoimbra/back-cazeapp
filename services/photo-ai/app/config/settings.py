from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    APP_NAME: str = "Photo AI Service"
    ENV: str = "development"
    DEBUG: bool = True

    AUTH_DATABASE_URL: str
    ADMIN_DATABASE_URL: Optional[str] = None
    INTERACTION_DATABASE_URL: Optional[str] = None

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
    AWS_CLOUDFRONT_DOMAIN_REKO: str

    CLOUDFRONT_PUBLIC_KEY_ID: str
    CLOUDFRONT_PRIVATE_KEY_PATH: str

    REKOGNITION_REGION: str = "us-east-2"
    REKOGNITION_BUCKET: Optional[str] = None
    S3_FOLDER: str = "rostos/"
    REKOGNITION_COLLECTION: str = "meu_banco_de_rostos"

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

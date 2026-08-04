from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # ===== APP =====
    APP_NAME: str = "MyApp"
    ENV: str = "development"
    DEBUG: bool = True

    # ===== DATABASE =====
    AUTH_DATABASE_URL: str
    ADMIN_DATABASE_URL: Optional[str] = None
    INTERACTION_DATABASE_URL: Optional[str] = None
    ROULETTE_DATABASE_URL: Optional[str] = None
    NOTIFICATIONS_DATABASE_URL: Optional[str] = None

    # ===== DATABASE POOL =====
    # Reduce to 5/5 when using PgBouncer (multi-replica). Keep 50/30 for single-instance direct connections.
    DB_POOL_SIZE: int = 50
    DB_MAX_OVERFLOW: int = 30
    # Use "disable" when connecting through PgBouncer (internal Docker network, PgBouncer handles SSL to DB)
    DB_SSLMODE: str = "require"

    # ===== JWT =====
    JWT_SECRET: str
    JWT_REFRESH_SECRET: str

    # ===== FRONTEND URL =====
    FRONTEND_URL: str

    # ===== SMTP =====
    SMTP_HOST: str
    SMTP_PORT: int = 587
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_TLS: bool = True
    MAIL_FROM: str = "no-reply@meusite.com"

    # E-mail interno para alertas de solicitação LGPD (remoção de dados). Resend entrega no inbox; use assunto com prefixo [Remoção de dados].
    DATA_REMOVAL_NOTIFICATION_EMAIL: Optional[str] = None

    # ===== GOOGLE =====
    GOOGLE_CLIENT_ID: str
    GOOGLE_CLIENT_SECRET: str
    GOOGLE_REDIRECT_URI: str

    # ===== FACEBOOK =====
    FB_CLIENT_ID: str
    FB_CLIENT_SECRET: str
    FB_REDIRECT_URI: str

    # ===== AWS GERAL (Bucket Principal) =====
    AWS_ACCESS_KEY: str
    AWS_SECRET_KEY: str
    AWS_REGION: str
    AWS_BUCKET: str
    AWS_CLOUDFRONT_DOMAIN: str
    AWS_CLOUDFRONT_DOMAIN_REKO: str
    
    CLOUDFRONT_PUBLIC_KEY_ID: str
    CLOUDFRONT_PRIVATE_KEY_PATH: str
    
    # ===== UPLOAD LIMITS =====
    MAX_FILE_SIZE_MB: int = 20  # Aumentar de 10 para 20 MB
    MAX_TOTAL_SIZE_MB: int = 100  # Aumentar de 50 para 100 MB
    
    # ===== AWS REKOGNITION (Bucket da AI) =====
    REKOGNITION_REGION: str = "us-east-2"  # Ohio - padrão
    REKOGNITION_BUCKET: Optional[str] = None  # Se None, usa AWS_BUCKET
    S3_FOLDER: str = "rostos/"  # Pasta das imagens para indexar
    REKOGNITION_COLLECTION: str = "meu_banco_de_rostos"  # Nome da coleção

    # ===== CLOUDWATCH (infraestrutura) =====
    # IDs das instâncias EC2 separados por vírgula, ex: "i-0abc123,i-0def456"
    AWS_CLOUDWATCH_INSTANCE_IDS: Optional[str] = None
    # Sufixo do ARN do ALB, ex: "app/meu-alb/1234567890abcdef"
    AWS_CLOUDWATCH_ALB_SUFFIX: Optional[str] = None

    # ===== ONESIGNAL =====
    ONESIGNAL_APP_ID: Optional[str] = None
    ONESIGNAL_API_KEY: Optional[str] = None

    # ===== WEB PUSH (VAPID) - legado, será removido após migração OneSignal =====
    VAPID_PRIVATE_KEY: Optional[str] = None
    VAPID_PUBLIC_KEY: Optional[str] = None

    # ===== REDIS =====
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_URL: Optional[str] = None  # Se fornecido, usa esta URL completa
    REDIS_CACHE_TTL: int = 3600  # TTL padrão em segundos (1 hora)

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config.settings import settings

_pool = {
    'pool_size': settings.DB_POOL_SIZE,
    'max_overflow': settings.DB_MAX_OVERFLOW,
    'pool_timeout': 30,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
    'future': True,
    'echo': False,
    'connect_args': {"sslmode": settings.DB_SSLMODE}
}

admin_engine = create_engine(settings.ADMIN_DATABASE_URL, **_pool)
auth_engine = create_engine(settings.AUTH_DATABASE_URL, **_pool)

AdminSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=admin_engine)
AuthSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=auth_engine)

AdminBase = declarative_base()


def get_admin_db():
    db = AdminSessionLocal()
    try:
        yield db
    finally:
        db.close()

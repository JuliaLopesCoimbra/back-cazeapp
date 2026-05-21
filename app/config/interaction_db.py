from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config.settings import settings

interaction_engine = create_engine(
    settings.INTERACTION_DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=30,
    pool_recycle=3600,
    pool_pre_ping=True,
    future=True,
    echo=False,
    connect_args={"sslmode": settings.DB_SSLMODE}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=interaction_engine)

InteractionBase = declarative_base()

def get_interaction_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

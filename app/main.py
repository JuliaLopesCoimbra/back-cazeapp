from fastapi import FastAPI
from app.config.auth_db import SessionLocal
from app.core.seed.admin_seed import seed_admin
from app.config import roulette_db
from app.config.auth_db import Base, engine
from app.config.admin_db import AdminBase as admin_base, admin_engine as admin_engine
from app.config.interaction_db import InteractionBase as interaction_base, interaction_engine as interaction_engine
from app.config.roulette_db import RouletteBase as roulette_base, roulette_engine as roulette_engine
from app.config.notification_db import NotificationBase as notification_base, notification_engine as notification_engine
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings

# Importar todas as rotas
from app.domain.auth.routes.auth_routes import router as auth_router
from app.domain.auth.routes.email_routes import router as email_router
from app.domain.auth.routes.password_reset_routes import router as reset_router
from app.domain.auth.routes.email_log_routes import router as email_log_router
from app.domain.auth.routes.social_routes import router as social_router
from app.domain.users.routes.profile_routes import router as profile_router
from app.domain.admin.routes.news_routes import router as news_router
from app.domain.users.routes.comment_routes import router as comment_router
from app.domain.users.routes.like_routes import router as like_router
from app.domain.admin.routes.event_routes import router as event_router
from app.domain.admin.routes.samba_school_routes import router as samba_school_router
from app.domain.admin.routes.music_lyrics_routes import router as music_lyrics_router
from app.domain.public.routes.public_event_routes import router as public_event_router
from app.domain.admin.routes.product_event_routes import router as product_event_router
from app.domain.admin.routes.lineup_item_routes import router as lineup_item_router
from app.domain.admin.routes.parade_lineup_item_routes import router as parade_lineup_item_router
from app.domain.users.routes.notification_routes import router as notification_router
from app.domain.users.routes.notification_preference_routes import router as notification_preference_router
from app.domain.users.routes.push_routes import router as push_router
from app.domain.users.routes.downloaded_photo_routes import router as downloaded_photo_router
from app.domain.admin.routes.ad_click_routes import router as ad_click_router
from app.domain.admin.routes.world_cup_game_routes import router as world_cup_game_router
from app.domain.analytics.routes.analytics_routes import router as analytics_router
from app.domain.football.routes.football_routes import router as football_router
from app.domain.bolao.routes.bolao_routes import router as bolao_router

# Importar modelos para garantir que SQLAlchemy os registre
from app.domain.admin.models.ad_click_model import AdClick  # noqa: F401
from app.domain.admin.models.world_cup_game_model import WorldCupGame  # noqa: F401
from app.domain.admin.models.ad_view_model import AdView  # noqa: F401
from app.domain.auth.models.data_removal_request_model import DataRemovalRequest  # noqa: F401
from app.domain.privacy.routes.privacy_routes import router as privacy_router
from app.domain.analytics.models.page_view_model import PageView  # noqa: F401
from app.domain.admin.models.tshirt_reservation_model import TshirtReservation  # noqa: F401
from app.domain.admin.routes.tshirt_reservation_admin_routes import (
    router as tshirt_reservation_admin_router,
)
from app.domain.users.routes.tshirt_reservation_user_routes import (
    router as tshirt_reservation_user_router,
)
from app.domain.admin.models.tshirt_stock_item_model import TshirtStockItem  # noqa: F401
from app.domain.admin.models.tshirt_stock_movement_model import TshirtStockMovement  # noqa: F401
from app.domain.admin.routes.tshirt_stock_routes import router as tshirt_stock_router
from app.domain.admin.models.photo_sync_log_model import PhotoSyncLog  # noqa: F401
from app.domain.admin.routes.photo_sync_routes import router as photo_sync_router
from app.domain.photo_ai.models.user_face_model import UserFace  # noqa: F401
from app.domain.bolao.models.bolao_prediction_model import BolaoPredicition  # noqa: F401
from app.domain.bolao.models.bolao_prize_model import BolaoPrize  # noqa: F401
from app.domain.bolao.models.bolao_redemption_model import BolaoRedemption  # noqa: F401
from app.domain.bolao.models.bolao_user_points_model import BolaoUserPoints  # noqa: F401
from app.domain.photo_ai.routes.face_routes import router as face_router
from app.domain.users.models.user_photo_model import UserPhoto  # noqa: F401
from app.config.admin_db import AdminSessionLocal
from app.core.seed.tshirt_stock_seed import seed_tshirt_stock_if_empty

# Criar tabelas na inicialização
def init_db():
    # Criar todos os bancos
    Base.metadata.create_all(bind=engine)
    admin_base.metadata.create_all(bind=admin_engine)
    interaction_base.metadata.create_all(bind=interaction_engine)
    roulette_base.metadata.create_all(bind=roulette_engine)
    notification_base.metadata.create_all(bind=notification_engine)

_docs_url = "/docs" if settings.ENV == "development" else None
_redoc_url = "/redoc" if settings.ENV == "development" else None
_openapi_url = "/openapi.json" if settings.ENV == "development" else None

app = FastAPI(
    title="Auth API",
    version="1.0.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

# ===== CORS (configurado para produção e desenvolvimento local) =====
allowed_origins = [
    settings.FRONTEND_URL,  # URL de produção
    "http://localhost:3000",  # Next.js padrão
    "http://localhost:3001",  # FastAPI padrão
    "http://localhost:5173",  # Vite padrão
    "http://127.0.0.1:3000",
    "http://127.0.0.1:5173",
    "https://n1app.com.br", 'https://www.n1app.com.br', "https://staging.n1app.com.br", 'https://www.staging.n1app.com.br',
    "http://localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)

# ===== REGISTRO DE ROTAS =====
app.include_router(auth_router)
app.include_router(email_router)
app.include_router(reset_router)
app.include_router(email_log_router)
app.include_router(social_router)
app.include_router(profile_router)
app.include_router(tshirt_reservation_user_router)
app.include_router(news_router)
app.include_router(comment_router)
app.include_router(like_router)
app.include_router(event_router)
app.include_router(samba_school_router)
app.include_router(music_lyrics_router)
app.include_router(public_event_router)
app.include_router(product_event_router)
app.include_router(lineup_item_router)
app.include_router(parade_lineup_item_router)
app.include_router(notification_router)
app.include_router(notification_preference_router)
app.include_router(push_router)
app.include_router(downloaded_photo_router)
app.include_router(ad_click_router)
app.include_router(world_cup_game_router)
app.include_router(analytics_router)
app.include_router(football_router)
app.include_router(bolao_router)
app.include_router(tshirt_stock_router)
app.include_router(tshirt_reservation_admin_router)
app.include_router(photo_sync_router)
app.include_router(face_router)
# LGPD: duas bases de URL (/auth e /privacy) para evitar 404 em ambientes que só roteiam /auth/*
app.include_router(privacy_router, prefix="/auth")
app.include_router(privacy_router, prefix="/privacy")

@app.get("/")
def root():
    return {"message": "API está funcionando!"}
@app.get("/health")
def root():
    return {"message": "CI CD Pipeline funcionando!"}

@app.on_event("startup")
def startup():
    init_db()

    db = SessionLocal()
    seed_admin(db)
    db.close()

    admin_db = AdminSessionLocal()
    try:
        seed_tshirt_stock_if_empty(admin_db)
    finally:
        admin_db.close()
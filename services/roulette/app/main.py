from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.domain.roulette.routes.roulette_routes import router as roulette_router
from app.domain.roulette.routes.prize_routes import router as prize_router
from app.domain.roulette.routes.spin_routes import router as spin_router

from app.domain.roulette.models.roulette_model import Roulette  # noqa: F401
from app.domain.roulette.models.prize_model import Prize  # noqa: F401
from app.domain.roulette.models.spin_model import Spin  # noqa: F401
from app.domain.auth.models.user_model import User  # noqa: F401
from app.domain.admin.models.event_model import Event  # noqa: F401

_docs_url = "/docs" if settings.ENV == "development" else None
_redoc_url = "/redoc" if settings.ENV == "development" else None
_openapi_url = "/openapi.json" if settings.ENV == "development" else None

app = FastAPI(
    title="Roulette Service",
    version="1.0.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    openapi_url=_openapi_url,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        settings.FRONTEND_URL,
        "http://localhost:3000",
        "https://n1app.com.br",
        "https://www.n1app.com.br",
        "https://staging.n1app.com.br",
        "https://www.staging.n1app.com.br",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "service": "roulette"}


app.include_router(roulette_router)
app.include_router(prize_router)
app.include_router(spin_router)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import settings
from app.domain.photo_ai.routes.face_routes import router as face_router
from app.domain.photo_ai.routes.user_face_routes import router as user_face_router

# Register models with their bases so SQLAlchemy knows about them
from app.domain.photo_ai.models.face_search_model import FaceSearch  # noqa: F401
from app.domain.photo_ai.models.user_face_model import UserFace  # noqa: F401
from app.domain.users.models.downloaded_photo_model import DownloadedPhoto  # noqa: F401
from app.domain.users.models.user_photo_model import UserPhoto  # noqa: F401
from app.domain.auth.models.user_model import User  # noqa: F401

_docs_url = "/docs" if settings.ENV == "development" else None
_redoc_url = "/redoc" if settings.ENV == "development" else None
_openapi_url = "/openapi.json" if settings.ENV == "development" else None

app = FastAPI(
    title="Photo AI Service",
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
    return {"status": "ok", "service": "photo-ai"}


app.include_router(face_router)
app.include_router(user_face_router)

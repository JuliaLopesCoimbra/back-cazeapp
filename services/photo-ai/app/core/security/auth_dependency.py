from fastapi import Depends, Request, HTTPException, status
from app.core.security.jwt import JWTHandler
from app.core.exceptions.auth_exceptions import Unauthorized
from sqlalchemy.orm import Session
from app.config.auth_db import get_db
from app.domain.auth.models.user_model import User
from app.infra.redis import redis_client, CacheKeys
from typing import Optional


def get_current_user(request: Request, db: Session = Depends(get_db)):
    auth_header = request.headers.get("Authorization")

    if not auth_header:
        raise Unauthorized("Token não fornecido.")

    if not auth_header.startswith("Bearer "):
        raise Unauthorized("Formato de token inválido.")

    token = auth_header.split(" ")[1]

    try:
        payload = JWTHandler.decode_token(token)
    except Exception:
        raise Unauthorized("Token inválido ou expirado.")

    user_id = payload.get("sub")
    if not user_id:
        raise Unauthorized("Token sem usuário válido.")

    user_id_int = int(user_id)

    cached_user = _get_user_from_cache(user_id_int)

    if cached_user:
        if cached_user.get("status") != "active":
            raise Unauthorized("Usuário desativado ou banido.")
        return _create_user_from_cache(cached_user)

    user = db.query(User).filter(User.id == user_id_int).first()

    if not user:
        raise Unauthorized("Usuário não encontrado.")

    if user.status != "active":
        raise Unauthorized("Usuário desativado ou banido.")

    _cache_user(user)

    return user


def _get_user_from_cache(user_id: int) -> Optional[dict]:
    cache_key = CacheKeys.user_me(user_id)
    return redis_client.get(cache_key)


def _cache_user(user: User, ttl: int = 900) -> bool:
    cache_key = CacheKeys.user_me(user.id)
    user_data = {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "status": user.status,
        "is_email_verified": user.is_email_verified,
        "profile_photo": user.profile_photo,
    }
    return redis_client.set(cache_key, user_data, ttl=ttl)


def _create_user_from_cache(cached_data: dict) -> User:
    user = User()
    user.id = cached_data["id"]
    user.name = cached_data["name"]
    user.email = cached_data["email"]
    user.role = cached_data["role"]
    user.status = cached_data["status"]
    user.is_email_verified = cached_data.get("is_email_verified", False)
    user.profile_photo = cached_data.get("profile_photo")
    return user

from datetime import datetime, timedelta
import jwt
from app.config.settings import settings


class JWTHandler:
    @staticmethod
    def decode_token(token: str, refresh=False):
        secret = settings.JWT_REFRESH_SECRET if refresh else settings.JWT_SECRET
        return jwt.decode(token, secret, algorithms=["HS256"])

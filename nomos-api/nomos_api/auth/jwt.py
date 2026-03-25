from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import jwt


@dataclass
class TokenPayload:
    user_id: str
    email: str
    role: str  # "admin" | "user" | "officer"


def create_token(payload: TokenPayload, secret: str, expires_hours: int = 8) -> str:
    exp = datetime.now(timezone.utc) + timedelta(hours=expires_hours)
    data = {
        "sub": payload.user_id,
        "email": payload.email,
        "role": payload.role,
        "exp": exp,
        "iat": datetime.now(timezone.utc),
    }
    return jwt.encode(data, secret, algorithm="HS256")


def decode_token(token: str, secret: str) -> TokenPayload | None:
    try:
        data = jwt.decode(token, secret, algorithms=["HS256"])
        return TokenPayload(
            user_id=data["sub"],
            email=data["email"],
            role=data["role"],
        )
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError):
        return None

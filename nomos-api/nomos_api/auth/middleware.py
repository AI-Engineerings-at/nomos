from nomos_api.auth.jwt import decode_token, TokenPayload


class AuthError(Exception):
    def __init__(self, message: str, status_code: int = 401):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


def require_role(
    token: str | None,
    secret: str,
    allowed_roles: list[str],
) -> TokenPayload:
    if not token:
        raise AuthError("No token provided", 401)

    payload = decode_token(token, secret)
    if payload is None:
        raise AuthError("Invalid token", 401)

    if payload.role not in allowed_roles:
        raise AuthError(
            f"Insufficient permissions. Required: {allowed_roles}, got: {payload.role}",
            403,
        )

    return payload

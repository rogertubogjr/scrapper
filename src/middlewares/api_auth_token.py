"""
Lightweight token authentication middleware.

Best-practice notes
- Supports `x-access-token` and `Authorization: Bearer <token>` headers.
- Accepts either a static token (`TOKEN` in config) or a JWT signed
  with `SECRET_KEY` (HS256). If both are set, static token match wins,
  otherwise tries JWT decode.
- Uses Flask `current_app` to avoid import cycles; does not print secrets.
- Keeps the `requires([...])` decorator interface for compatibility.
"""

from functools import wraps
import json
import logging
from typing import Optional

import jwt
from flask import current_app, make_response, request

from src.handler.error_handler import UnauthorizedError

log = logging.getLogger(__name__)


HEADER_X_ACCESS_TOKEN = "x-access-token"
HEADER_AUTHORIZATION = "Authorization"


def _extract_token() -> Optional[str]:
    """Extract token from headers.

    Checks `x-access-token` and `Authorization: Bearer <token>`.
    Returns None if not present.
    """
    # Prefer explicit custom header
    token = request.headers.get(HEADER_X_ACCESS_TOKEN)
    if token:
        return token.strip()

    # Fall back to Authorization: Bearer <token>
    auth = request.headers.get(HEADER_AUTHORIZATION)
    if auth and isinstance(auth, str):
        parts = auth.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1]
    return None


def _verify_token(token: str) -> bool:
    """Verify token using app config.

    - If `TOKEN` is configured and matches, accept.
    - Else, if `SECRET_KEY` is configured and token looks like a JWT,
      attempt HS256 decode. Any decode error will be treated as unauthorized.
    """
    cfg = current_app.config

    static_token = cfg.get("TOKEN")
    if static_token and token == static_token:
        return True

    # Try JWT if a secret is available and the token looks like a JWT
    secret = cfg.get("SECRET_KEY")
    if secret and token.count(".") == 2:
        try:
            # We only validate signature/expiry; consumers may read claims via request context if needed
            jwt.decode(token, secret, algorithms=["HS256"])
            return True
        except jwt.ExpiredSignatureError:
            log.info("Auth token expired")
            raise UnauthorizedError("your token has been expired")
        except jwt.InvalidTokenError:
            log.info("Invalid auth token provided")
            raise UnauthorizedError()

    # No matching auth method
    return False


def _initialize_response(func, has_token: bool, token: Optional[str], *args, **kwargs):
    """Call the wrapped function and attach headers if needed."""
    code = 200
    ret = func(*args, **kwargs)
    if isinstance(ret, tuple):
        code = ret[1]
        ret = ret[0]
    try:
        response = make_response(json.dumps(ret), code)
        response.headers.setdefault("Content-Type", "application/json")
        if has_token and token:
            # Propagate token for clients that expect it (CORS exposes this header in debug)
            response.headers[HEADER_X_ACCESS_TOKEN] = token
    except Exception:
        # If `ret` is already a Response or not JSON-serializable, just return it
        response = ret
    log.debug("Auth middleware produced response with status %s", getattr(response, "status_code", code))
    return response


class requires:
    """Decorator class to protect endpoints with token authentication.

    The `permissions` parameter is accepted for compatibility but not used
    by this simple token/JWT check implementation.
    """

    def __init__(self, permissions=None):
        self.permissions = permissions

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = _extract_token()
            if not token:
                raise UnauthorizedError("token is missing")

            if not _verify_token(token):
                raise UnauthorizedError()

            return _initialize_response(func, True, token, *args, **kwargs)

        return wrapper

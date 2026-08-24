from functools import wraps
from config.clerk import clerk_client
from flask import request, jsonify, g
from clerk_backend_api import Clerk
from clerk_backend_api.security.types import AuthenticateRequestOptions
import os
from core.exceptions import AppError

IS_PROD = os.getenv("FLASK_ENV") == "production"
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

DEFAULT_ORIGINS = [FRONTEND_URL] if IS_PROD else ["http://localhost:3000"]


def authentication_middleware(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not IS_PROD:
            # In development, we can mock the user_id for testing purposes
            g.user_id = "user_3HUeuQ21EH4OGF2FdwqhqX4qMrH"
            g.user_claims = {
                "role": "ADMIN",
                "sub": "user_3HUeuQ21EH4OGF2FdwqhqX4qMrH",
            }
            return f(*args, **kwargs)
        try:
            request_state = clerk_client.authenticate_request(
                request,
                AuthenticateRequestOptions(
                    # Recommended: verify authorized frontend origins
                    authorized_parties=DEFAULT_ORIGINS
                ),
            )
        except Exception as e:
            raise AppError("Unauthorized access", 401)

        if not request_state.is_signed_in:
            raise AppError("Unauthorized access", 401)

        g.user_id = request_state.payload.get("sub")
        g.user_claims = request_state.payload

        return f(*args, **kwargs)

    return decorated


def authorization_middleware(*allowed_roles):
    def decorated(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not getattr(g, "user_id", None):
                raise AppError("Unauthorized access", 401)
            #    Extract user role from claims, considering both top-level and nested public_metadata form clerk itself
            user_claims = getattr(g, "user_claims", {})
            user_role = user_claims.get("role")
            if not user_role or user_role not in allowed_roles:
                raise AppError("Forbidden access", 403)

            return f(*args, **kwargs)

        return decorated_function

    return decorated


require_auth = authentication_middleware
admin_required = authorization_middleware("ADMIN")

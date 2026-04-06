# auth.py
import os
import functools
from typing import Optional

import requests
from jose import jwt, jwk, JWTError
from flask import request, jsonify, g

# ─── Configuration ──────────────────────────────────────────────────────────
# Load the Cognito region, user pool ID, and app client ID from environment
# variables. Never hard-code these values in source code.
COGNITO_REGION    = os.environ["COGNITO_REGION"]
COGNITO_POOL_ID   = os.environ["COGNITO_POOL_ID"]
COGNITO_CLIENT_ID = os.environ["COGNITO_CLIENT_ID"]

JWKS_URL = (
    f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/"
    f"{COGNITO_POOL_ID}/.well-known/jwks.json"
)

# Module-level cache so that Cognito's public keys are only fetched once,
# rather than on every incoming request.
_jwks_cache: Optional[dict] = None


def _get_jwks() -> dict:
    """Fetch Cognito's public keys."""
    global _jwks_cache
    if _jwks_cache is None:
        response = requests.get(JWKS_URL)
        jwks = response.json()
        _jwks_cache = {key['kid']: key for key in jwks['keys']}
    return _jwks_cache


def validate_token(token: str) -> dict:
    """Validate Cognito JWT and return claims."""
    # Get key ID from token header
    header = jwt.get_unverified_header(token)
    kid = header['kid']
    
    # Get matching public key
    jwks = _get_jwks()
    public_key = jwk.construct(jwks[kid])
    
    # Decode and verify token
    claims = jwt.decode(token, public_key, algorithms=['RS256'], audience=COGNITO_CLIENT_ID)
    
    # Verify it's an access token
    if claims['token_use'] != 'access':
        raise ValueError("Not an access token")
        
    return claims


def requires_auth(handler):
    """Require valid Cognito JWT token."""
    @functools.wraps(handler)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        try:
            g.current_user = validate_token(token)
        except Exception:
            return jsonify({'error': 'Invalid token'}), 401
        
        return handler(*args, **kwargs)
    return wrapper
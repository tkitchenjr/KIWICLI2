# auth.py
import os
import functools
from typing import Optional

import requests
from jose import jwt, jwk, JWTError
from flask import request, jsonify, g

# Load the Cognito region, user pool ID, and client ID from environment variables.
# Safe environment variable access - won't crash on import if not set
COGNITO_REGION    = os.environ.get("COGNITO_REGION")
COGNITO_POOL_ID   = os.environ.get("COGNITO_POOL_ID") 
COGNITO_CLIENT_ID = os.environ.get("COGNITO_CLIENT_ID")

# Validation helper - follows the configuration pattern
def _validate_auth_config():
    """Validate that all required auth environment variables are set."""
    if not COGNITO_REGION:
        raise ValueError('Cognito region is not configured. Please set the COGNITO_REGION environment variable.')
    if not COGNITO_POOL_ID:
        raise ValueError('Cognito pool ID is not configured. Please set the COGNITO_POOL_ID environment variable.')
    if not COGNITO_CLIENT_ID:
        raise ValueError('Cognito client ID is not configured. Please set the COGNITO_CLIENT_ID environment variable.')
    return COGNITO_REGION, COGNITO_POOL_ID, COGNITO_CLIENT_ID

# surface attributes for jwks url with helper function that validates variables
def _get_jwks_url():
    """Get JWKS URL - validates config when called."""
    region, pool_id, _ = _validate_auth_config()
    return f"https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json"

# Module-level cache so that Cognito's public keys are only fetched once,
# rather than on every incoming request.
_jwks_cache: Optional[dict] = None


def _get_jwks() -> dict:
    """Fetch Cognito's public keys."""
    global _jwks_cache
    if _jwks_cache is None:
        jwks_url = _get_jwks_url()  # Validates config here
        response = requests.get(jwks_url)
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
    region, pool_id, client_id = _validate_auth_config()  # Validates config here
    claims = jwt.decode(token, public_key, algorithms=['RS256'], audience=client_id, issuer=f"https://cognito-idp.{region}.amazonaws.com/{pool_id}")
    
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
            return jsonify({'error': 'Missing or invalid Authorization header'}), 403
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        try:
            g.current_user = validate_token(token)
        except Exception:
            return jsonify({'error': 'Invalid token'}), 403
        
        return handler(*args, **kwargs)
    return wrapper
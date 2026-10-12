from jose import jwt, jwk, JWTError
from fastapi import HTTPException, status
from typing import Optional, Dict, Any
from app.core.config import settings
import uuid
import urllib.request
import json
import logging
import time

logger = logging.getLogger(__name__)

# Cache JWKS keys in memory: kid -> JWK object, along with timestamp
_JWKS_CACHE: Dict[str, Any] = {}
_JWKS_LAST_FETCH: float = 0.0
_JWKS_TTL_SECONDS = 300.0  # 5 minutes cache

def _get_jwks_keys() -> Dict[str, Any]:
    global _JWKS_CACHE, _JWKS_LAST_FETCH
    current_time = time.time()
    if _JWKS_CACHE and (current_time - _JWKS_LAST_FETCH < _JWKS_TTL_SECONDS):
        return _JWKS_CACHE

    supabase_url = settings.SUPABASE_URL.rstrip("/")
    if not supabase_url.startswith("http"):
        return _JWKS_CACHE

    jwks_url = f"{supabase_url}/auth/v1/.well-known/jwks.json"
    try:
        req = urllib.request.Request(
            jwks_url,
            headers={"User-Agent": "DocuMind-Backend/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            keys = data.get("keys", [])
            new_cache = {}
            for k in keys:
                kid = k.get("kid")
                try:
                    constructed = jwk.construct(k)
                    if kid:
                        new_cache[kid] = constructed
                    # Also map algorithm as fallback
                    alg = k.get("alg")
                    if alg and alg not in new_cache:
                        new_cache[alg] = constructed
                except Exception as construct_err:
                    logger.warning("Failed to construct JWK for key %s: %s", kid, construct_err)
            
            if new_cache:
                _JWKS_CACHE = new_cache
                _JWKS_LAST_FETCH = current_time
    except Exception as e:
        logger.warning("Failed to fetch JWKS from %s: %s", jwks_url, e)

    return _JWKS_CACHE

def verify_token(token: str) -> uuid.UUID:
    try:
        header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    alg = header.get("alg", "HS256")
    kid = header.get("kid")

    key_to_verify = None
    algorithms_allowed = [alg]

    if alg.startswith("HS"):
        key_to_verify = settings.SUPABASE_JWT_SECRET
    elif alg in ("ES256", "RS256", "ES384", "ES512", "RS384", "RS512"):
        if settings.SUPABASE_JWT_PUBLIC_KEY:
            key_to_verify = settings.SUPABASE_JWT_PUBLIC_KEY
        else:
            jwks_keys = _get_jwks_keys()
            if kid and kid in jwks_keys:
                key_to_verify = jwks_keys[kid]
            elif alg in jwks_keys:
                key_to_verify = jwks_keys[alg]
            elif jwks_keys:
                # Use first available JWK if single key present
                key_to_verify = next(iter(jwks_keys.values()))
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not key_to_verify:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token,
            key_to_verify,
            algorithms=algorithms_allowed,
            audience="authenticated"
        )
        sub = payload.get("sub")
        if not sub:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return uuid.UUID(sub)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

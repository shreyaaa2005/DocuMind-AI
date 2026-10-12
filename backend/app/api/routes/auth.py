from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from typing import Dict, Any
from app.core.config import settings
from jose import jwt
from datetime import datetime, timedelta, timezone
import uuid

router = APIRouter()

# Fixed deterministic demo user UUIDs matching the development fixtures
DEMO_USERS = {
    "demo-a": {
        "id": "00000000-0000-0000-0000-000000000001",
        "email": "demo.analyst@documind.ai",
        "role": "Financial Analyst (Workspace A)",
    },
    "demo-b": {
        "id": "00000000-0000-0000-0000-000000000002",
        "email": "demo.auditor@documind.ai",
        "role": "Compliance Auditor (Workspace B)",
    },
}

class DemoLoginRequest(BaseModel):
    user_key: str = Field(..., description="'demo-a' or 'demo-b'")

class DemoLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str

class AuthConfigStatusResponse(BaseModel):
    supabase_configured: bool
    supabase_url_configured: bool
    supabase_jwt_secret_configured: bool
    supabase_service_role_key_configured: bool
    demo_login_enabled: bool

@router.post("/demo-login", response_model=DemoLoginResponse)
def demo_login(req: DemoLoginRequest):
    if not settings.ENABLE_DEMO_LOGIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo login is disabled in this environment",
        )
    
    user_info = DEMO_USERS.get(req.user_key)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid demo user key '{req.user_key}'. Allowed: 'demo-a', 'demo-b'",
        )

    # Issue a valid signed JWT using backend's configured JWT secret
    # Token validity: 24 hours
    now = datetime.now(timezone.utc)
    expire = now + timedelta(hours=24)
    claims = {
        "sub": user_info["id"],
        "email": user_info["email"],
        "aud": "authenticated",
        "role": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    
    token = jwt.encode(claims, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
    
    return DemoLoginResponse(
        access_token=token,
        token_type="bearer",
        user_id=user_info["id"],
        email=user_info["email"],
    )

@router.get("/config-status", response_model=AuthConfigStatusResponse)
def get_auth_config_status():
    """
    Safely reports whether backend authentication and Supabase variables
    are configured without revealing any secrets or credentials.
    """
    url_ok = bool(settings.SUPABASE_URL) and not settings.SUPABASE_URL.startswith("http://localhost:8000")
    secret_ok = bool(settings.SUPABASE_JWT_SECRET) and not settings.SUPABASE_JWT_SECRET.startswith("your-jwt-secret")
    service_role_ok = bool(settings.SUPABASE_SERVICE_ROLE_KEY)
    
    return AuthConfigStatusResponse(
        supabase_configured=url_ok and secret_ok,
        supabase_url_configured=url_ok,
        supabase_jwt_secret_configured=secret_ok,
        supabase_service_role_key_configured=service_role_ok,
        demo_login_enabled=settings.ENABLE_DEMO_LOGIN,
    )

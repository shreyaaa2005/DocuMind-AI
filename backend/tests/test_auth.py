import pytest
from fastapi import HTTPException
from app.core.security import verify_token
from tests.conftest import create_test_token, TEST_JWT_SECRET
from datetime import timedelta
import uuid

def test_verify_token_valid():
    user_id = str(uuid.uuid4())
    token = create_test_token(sub=user_id)
    result = verify_token(token)
    assert str(result) == user_id

def test_verify_token_expired():
    user_id = str(uuid.uuid4())
    token = create_test_token(sub=user_id, expires_delta=timedelta(minutes=-15))
    with pytest.raises(HTTPException) as exc:
        verify_token(token)
    assert exc.value.status_code == 401
    assert "Could not validate credentials" in exc.value.detail

def test_verify_token_invalid_signature():
    user_id = str(uuid.uuid4())
    token = create_test_token(sub=user_id)
    parts = token.split(".")
    invalid_token = f"{parts[0]}.{parts[1]}.invalidsignature12345"
    with pytest.raises(HTTPException) as exc:
        verify_token(invalid_token)
    assert exc.value.status_code == 401

def test_verify_token_missing_sub():
    token = create_test_token(sub="")
    with pytest.raises(HTTPException) as exc:
        verify_token(token)
    assert exc.value.status_code == 401

def test_verify_token_incorrect_audience():
    user_id = str(uuid.uuid4())
    token = create_test_token(sub=user_id, aud="some_other_aud")
    with pytest.raises(HTTPException) as exc:
        verify_token(token)
    assert exc.value.status_code == 401

def test_demo_login_endpoint(client):
    res_a = client.post("/api/v1/auth/demo-login", json={"user_key": "demo-a"})
    assert res_a.status_code == 200
    data_a = res_a.json()
    assert data_a["user_id"] == "00000000-0000-0000-0000-000000000001"
    assert data_a["email"] == "demo.analyst@documind.ai"
    assert "access_token" in data_a

    # Verify the generated token decodes properly via verify_token
    verified_id = verify_token(data_a["access_token"])
    assert str(verified_id) == "00000000-0000-0000-0000-000000000001"

    res_b = client.post("/api/v1/auth/demo-login", json={"user_key": "demo-b"})
    assert res_b.status_code == 200
    data_b = res_b.json()
    assert data_b["user_id"] == "00000000-0000-0000-0000-000000000002"

    # User A and User B tokens are distinct
    assert data_a["access_token"] != data_b["access_token"]

def test_demo_login_invalid_key(client):
    res = client.post("/api/v1/auth/demo-login", json={"user_key": "unknown-user"})
    assert res.status_code == 400

def test_auth_config_status_endpoint(client):
    res = client.get("/api/v1/auth/config-status")
    assert res.status_code == 200
    data = res.json()
    assert "supabase_configured" in data
    assert "supabase_url_configured" in data
    assert "supabase_jwt_secret_configured" in data
    assert "demo_login_enabled" in data
    # Secret values must NEVER be leaked in the response
    assert "supersecret" not in res.text
    assert "secret" not in res.text.lower() or "secret_configured" in res.text

def test_verify_token_es256(monkeypatch):
    import ecdsa
    from jose import jwt, jwk
    sk = ecdsa.SigningKey.generate(curve=ecdsa.NIST256p)
    vk = sk.verifying_key
    pem_priv = sk.to_pem().decode()
    pem_pub = vk.to_pem().decode()

    # Configure public key in settings
    from app.core.config import settings
    monkeypatch.setattr(settings, "SUPABASE_JWT_PUBLIC_KEY", pem_pub)

    user_id = str(uuid.uuid4())
    token = jwt.encode(
        {"sub": user_id, "aud": "authenticated"},
        pem_priv,
        algorithm="ES256"
    )
    result = verify_token(token)
    assert str(result) == user_id


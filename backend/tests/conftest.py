import pytest
from fastapi.testclient import TestClient
from jose import jwt
from datetime import datetime, timedelta, timezone
import uuid
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
TEST_JWT_SECRET = "supersecret-test-jwt-key-that-is-long-enough-for-hs256"
settings.SUPABASE_JWT_SECRET = TEST_JWT_SECRET

from app.main import app
from app.db.session import Base, engine, SessionLocal
from app.api.deps import get_db

import tempfile

@pytest.fixture(scope="session", autouse=True)
def setup_storage():
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_storage = settings.STORAGE_DIR
        settings.STORAGE_DIR = tmp_dir
        yield
        settings.STORAGE_DIR = original_storage

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield

@pytest.fixture
def db():
    connection = engine.connect()
    transaction = connection.begin()
    session = SessionLocal(bind=connection, join_transaction_mode="create_savepoint")
    
    yield session
    
    session.close()
    if transaction.is_active:
        transaction.rollback()
    connection.close()

@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()

def create_test_token(sub: str, aud: str = "authenticated", expires_delta: timedelta = timedelta(minutes=15)):
    to_encode = {"sub": sub, "aud": aud}
    expire = datetime.now(timezone.utc) + expires_delta
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, TEST_JWT_SECRET, algorithm="HS256")
    return encoded_jwt

@pytest.fixture
def user_a_id():
    return str(uuid.uuid4())

@pytest.fixture
def user_b_id():
    return str(uuid.uuid4())

@pytest.fixture
def user_a_token(user_a_id):
    return create_test_token(sub=user_a_id)

@pytest.fixture
def user_b_token(user_b_id):
    return create_test_token(sub=user_b_id)

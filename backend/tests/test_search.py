import pytest
import uuid
import numpy as np
from unittest.mock import patch
from app.db.models import Document, Chunk
from app.core.config import settings

def setup_search_data(db, user_id, doc_id, chunks_data):
    doc = Document(
        id=doc_id, owner_id=user_id, original_filename="search_test.pdf",
        stored_path="/tmp/fake", file_size=100, content_hash=str(uuid.uuid4())
    )
    db.add(doc)
    db.flush()
    
    for i, data in enumerate(chunks_data):
        chunk = Chunk(
            owner_id=user_id,
            document_id=doc_id,
            document_name="search_test.pdf",
            page_start=1,
            page_end=1,
            chunk_index=i,
            text=data["text"],
            embedding=data["embedding"]
        )
        db.add(chunk)
    db.commit()

@pytest.fixture
def search_mock_data(db, user_a_id):
    doc_id = uuid.uuid4()
    # Create simple 384-dim embeddings
    emb1 = [1.0] + [0.0] * 383
    emb2 = [0.0, 1.0] + [0.0] * 382
    setup_search_data(db, user_a_id, doc_id, [
        {"text": "Apple", "embedding": emb1},
        {"text": "Banana", "embedding": emb2}
    ])
    return doc_id

@patch("app.api.routes.search.generate_embeddings")
def test_valid_semantic_search(mock_generate, client, user_a_token, search_mock_data):
    # Mock search query embedding to match 'Apple'
    mock_generate.return_value = [[1.0] + [0.0] * 383]
    
    response = client.post("/api/v1/search/", json={"query": "Apple query", "top_k": 5, "min_similarity": 0.0}, headers={"Authorization": f"Bearer {user_a_token}"})
    assert response.status_code == 200
    results = response.json()
    
    assert len(results) == 2
    # Apple should be first (distance 0 -> similarity 1)
    assert results[0]["text"] == "Apple"
    assert results[0]["similarity_score"] == pytest.approx(1.0)
    
    # Banana should be second (orthogonal -> distance 1 -> similarity 0)
    assert results[1]["text"] == "Banana"
    assert results[1]["similarity_score"] == pytest.approx(0.0)

def test_query_validation(client, user_a_token):
    # Empty query
    r = client.post("/api/v1/search/", json={"query": ""}, headers={"Authorization": f"Bearer {user_a_token}"})
    assert r.status_code == 422
    
    # Missing query
    r = client.post("/api/v1/search/", json={}, headers={"Authorization": f"Bearer {user_a_token}"})
    assert r.status_code == 422

    # Invalid top_k (less than 1)
    r = client.post("/api/v1/search/", json={"query": "test", "top_k": 0}, headers={"Authorization": f"Bearer {user_a_token}"})
    assert r.status_code == 422
    
    # Invalid top_k (greater than 20)
    r = client.post("/api/v1/search/", json={"query": "test", "top_k": 100}, headers={"Authorization": f"Bearer {user_a_token}"})
    assert r.status_code == 422

@patch("app.api.routes.search.generate_embeddings")
def test_user_isolation(mock_generate, client, db, user_a_id, user_b_token):
    # Setup data for User A
    doc_id = uuid.uuid4()
    emb1 = [1.0] + [0.0] * 383
    setup_search_data(db, user_a_id, doc_id, [{"text": "Secret User A", "embedding": emb1}])
    
    mock_generate.return_value = [emb1]
    
    # Search as User B
    response = client.post("/api/v1/search/", json={"query": "Secret", "min_similarity": 0.0}, headers={"Authorization": f"Bearer {user_b_token}"})
    assert response.status_code == 200
    results = response.json()
    assert len(results) == 0 # User B shouldn't see User A's chunks

@patch("app.api.routes.search.generate_embeddings")
def test_no_results_for_new_user(mock_generate, client, user_a_token):
    mock_generate.return_value = [[1.0] + [0.0] * 383]
    response = client.post("/api/v1/search/", json={"query": "test", "min_similarity": 0.0}, headers={"Authorization": f"Bearer {user_a_token}"})
    assert response.status_code == 200
    assert response.json() == []

@patch("app.api.routes.search.generate_embeddings")
def test_database_failure(mock_generate, client, user_a_token):
    mock_generate.return_value = [[1.0] + [0.0] * 383]
    with patch("sqlalchemy.orm.session.Session.query") as mock_query:
        mock_query.side_effect = Exception("DB error")
        response = client.post("/api/v1/search/", json={"query": "test"}, headers={"Authorization": f"Bearer {user_a_token}"})
        assert response.status_code == 500
        assert "Database search error" in response.json()["detail"]

@patch("app.api.routes.search.generate_embeddings")
def test_embedding_service_failure(mock_generate, client, user_a_token):
    mock_generate.side_effect = RuntimeError("Service unavailable")
    response = client.post("/api/v1/search/", json={"query": "test"}, headers={"Authorization": f"Bearer {user_a_token}"})
    assert response.status_code == 503

def test_real_pgvector_integration(client, db, user_a_id, user_a_token):
    """
    Test real pgvector query execution without mocking the distance_col.
    We just mock generate_embeddings to supply a vector.
    """
    doc_id = uuid.uuid4()
    # Normalize vectors so cosine distance works properly (cosine distance = 1 - cosine similarity)
    # v1 is [1,0,0...], v2 is [0,1,0...]
    emb1 = [1.0] + [0.0] * 383
    emb2 = [0.0, 1.0] + [0.0] * 382
    setup_search_data(db, user_a_id, doc_id, [
        {"text": "A", "embedding": emb1},
        {"text": "B", "embedding": emb2}
    ])
    
    with patch("app.api.routes.search.generate_embeddings") as mock_gen:
        # Provide a vector closer to B
        mock_gen.return_value = [[0.1, 0.9] + [0.0] * 382]
        response = client.post("/api/v1/search/", json={"query": "test", "min_similarity": 0.0}, headers={"Authorization": f"Bearer {user_a_token}"})
        
        assert response.status_code == 200
        results = response.json()
        assert len(results) == 2
        # Highest similarity should be B
        assert results[0]["text"] == "B"
        assert results[1]["text"] == "A"
        # B similarity is high, A similarity is low
        assert results[0]["similarity_score"] > results[1]["similarity_score"]

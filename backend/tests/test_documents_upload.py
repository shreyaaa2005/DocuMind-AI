import pytest
import io
import os
from unittest.mock import patch
from app.core.config import settings
from app.db.models import Document

def create_mock_pdf_content(content=b"%PDF-1.4\nMock PDF Content", size_bytes=None):
    if size_bytes:
        return content.ljust(size_bytes, b"0")
    return content

def test_missing_authentication(client):
    response = client.post("/api/v1/documents/upload", files={"file": ("test.pdf", b"%PDF-1.4")})
    assert response.status_code == 403

def test_successful_pdf_upload(client, user_a_token, db, user_a_id):
    content = create_mock_pdf_content()
    files = {"file": ("test.pdf", content)}
    response = client.post(
        "/api/v1/documents/upload", 
        headers={"Authorization": f"Bearer {user_a_token}"},
        files=files
    )
    assert response.status_code == 201
    data = response.json()
    assert data["original_filename"] == "test.pdf"
    assert data["status"] == "uploaded"
    assert data["file_size"] == len(content)
    
    # Verify ownership
    doc = db.query(Document).filter(Document.id == data["id"]).first()
    assert doc is not None
    assert str(doc.owner_id) == user_a_id
    
    # Verify file stored
    assert os.path.exists(doc.stored_path)
    # Cleanup
    os.remove(doc.stored_path)

def test_invalid_magic_bytes(client, user_a_token):
    files = {"file": ("test.pdf", b"NOTAPDF_DATA")}
    response = client.post(
        "/api/v1/documents/upload", 
        headers={"Authorization": f"Bearer {user_a_token}"},
        files=files
    )
    assert response.status_code == 400
    assert "Invalid PDF file" in response.json()["detail"]

def test_empty_file(client, user_a_token):
    # Pass magic bytes but nothing else... actually empty file doesn't have magic bytes
    files = {"file": ("test.pdf", b"")}
    response = client.post(
        "/api/v1/documents/upload", 
        headers={"Authorization": f"Bearer {user_a_token}"},
        files=files
    )
    # Since it's empty, magic bytes check fails first
    assert response.status_code == 400
    assert "Invalid PDF file" in response.json()["detail"]

def test_empty_file_after_magic_bytes(client, user_a_token):
    # Passes magic bytes but is otherwise empty
    files = {"file": ("test.pdf", b"%PDF-")}
    response = client.post(
        "/api/v1/documents/upload", 
        headers={"Authorization": f"Bearer {user_a_token}"},
        files=files
    )
    assert response.status_code == 201

def test_unsupported_file_type(client, user_a_token):
    files = {"file": ("test.txt", b"%PDF-1.4\nFake text")}
    response = client.post(
        "/api/v1/documents/upload", 
        headers={"Authorization": f"Bearer {user_a_token}"},
        files=files
    )
    assert response.status_code == 400
    assert "Only PDF files are supported" in response.json()["detail"]

def test_file_size_exceeded(client, user_a_token):
    # Temporarily lower the size limit for the test
    original_size = settings.MAX_UPLOAD_SIZE_BYTES
    settings.MAX_UPLOAD_SIZE_BYTES = 100
    try:
        content = create_mock_pdf_content(size_bytes=150)
        files = {"file": ("large.pdf", content)}
        response = client.post(
            "/api/v1/documents/upload", 
            headers={"Authorization": f"Bearer {user_a_token}"},
            files=files
        )
        assert response.status_code == 413
        assert "File too large" in response.json()["detail"]
    finally:
        settings.MAX_UPLOAD_SIZE_BYTES = original_size

def test_duplicate_upload_same_user(client, user_a_token, db):
    content = create_mock_pdf_content(b"%PDF-1.4\nDuplicate test content")
    files1 = {"file": ("doc1.pdf", content)}
    response1 = client.post(
        "/api/v1/documents/upload", 
        headers={"Authorization": f"Bearer {user_a_token}"},
        files=files1
    )
    assert response1.status_code == 201
    
    # Try uploading exact same content again for same user
    files2 = {"file": ("doc1_copy.pdf", content)}
    response2 = client.post(
        "/api/v1/documents/upload", 
        headers={"Authorization": f"Bearer {user_a_token}"},
        files=files2
    )
    assert response2.status_code == 409
    assert "Document already exists" in response2.json()["detail"]

def test_duplicate_upload_different_user(client, user_a_token, user_b_token, db):
    content = create_mock_pdf_content(b"%PDF-1.4\nShared content")
    files1 = {"file": ("shared.pdf", content)}
    response1 = client.post(
        "/api/v1/documents/upload", 
        headers={"Authorization": f"Bearer {user_a_token}"},
        files=files1
    )
    assert response1.status_code == 201
    
    # Different user uploading the same file should succeed
    files2 = {"file": ("shared.pdf", content)}
    response2 = client.post(
        "/api/v1/documents/upload", 
        headers={"Authorization": f"Bearer {user_b_token}"},
        files=files2
    )
    assert response2.status_code == 201

def test_database_insertion_failure_cleanup(client, user_a_token):
    content = create_mock_pdf_content(b"%PDF-1.4\nDB failure test")
    files = {"file": ("fail.pdf", content)}
    
    with patch("app.api.routes.documents.Session.commit") as mock_commit:
        mock_commit.side_effect = Exception("Simulated DB failure")
        response = client.post(
            "/api/v1/documents/upload", 
            headers={"Authorization": f"Bearer {user_a_token}"},
            files=files
        )
        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]
        
        # Verify no files are left in the storage dir from this request
        # We can't strictly check the exact ID since it's generated inside the endpoint,
        # but we can ensure the endpoint caught it and deleted it by logic review,
        # or we could mock os.remove and check if it was called.
        
    with patch("os.remove") as mock_remove:
        with patch("app.api.routes.documents.Session.commit") as mock_commit:
            mock_commit.side_effect = Exception("Simulated DB failure")
            client.post(
                "/api/v1/documents/upload", 
                headers={"Authorization": f"Bearer {user_a_token}"},
                files=files
            )
            mock_remove.assert_called_once()

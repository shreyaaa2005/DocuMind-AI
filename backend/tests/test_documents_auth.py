import pytest
from app.db.models import Document
import uuid

def test_missing_auth_header(client):
    response = client.get("/api/v1/documents/")
    assert response.status_code == 403

def test_list_documents_isolation(client, db, user_a_id, user_b_id, user_a_token, user_b_token):
    doc_a = Document(owner_id=user_a_id, original_filename="a.pdf", stored_path="a.pdf", file_size=10, content_hash=str(uuid.uuid4()))
    doc_b = Document(owner_id=user_b_id, original_filename="b.pdf", stored_path="b.pdf", file_size=10, content_hash=str(uuid.uuid4()))
    db.add(doc_a)
    db.add(doc_b)
    db.commit()

    # User A lists
    response = client.get("/api/v1/documents/", headers={"Authorization": f"Bearer {user_a_token}"})
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 1
    assert docs[0]["original_filename"] == "a.pdf"

    # User B lists
    response = client.get("/api/v1/documents/", headers={"Authorization": f"Bearer {user_b_token}"})
    assert response.status_code == 200
    docs = response.json()
    assert len(docs) == 1
    assert docs[0]["original_filename"] == "b.pdf"

def test_get_document_isolation(client, db, user_a_id, user_b_id, user_a_token, user_b_token):
    doc_a = Document(owner_id=user_a_id, original_filename="a.pdf", stored_path="a.pdf", file_size=10, content_hash=str(uuid.uuid4()))
    db.add(doc_a)
    db.commit()
    db.refresh(doc_a)

    response = client.get(f"/api/v1/documents/{doc_a.id}", headers={"Authorization": f"Bearer {user_b_token}"})
    assert response.status_code == 404

def test_delete_document_isolation(client, db, user_a_id, user_b_id, user_a_token, user_b_token):
    doc_a = Document(owner_id=user_a_id, original_filename="a.pdf", stored_path="a.pdf", file_size=10, content_hash=str(uuid.uuid4()))
    db.add(doc_a)
    db.commit()
    db.refresh(doc_a)

    response = client.delete(f"/api/v1/documents/{doc_a.id}", headers={"Authorization": f"Bearer {user_b_token}"})
    assert response.status_code == 404

    doc_check = db.query(Document).filter(Document.id == doc_a.id).first()
    assert doc_check is not None

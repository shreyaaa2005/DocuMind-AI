import os
import io
import fitz
import pytest
from app.db.models import Document, Chunk
from app.services.llm.adapter import MockLLMAdapter
from unittest.mock import patch

def create_sample_pdf_bytes(title: str, body: str) -> bytes:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((50, 72), f"{title}\n\n{body}")
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes

def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

    response_v1 = client.get("/api/v1/health")
    assert response_v1.status_code == 200
    assert response_v1.json() == {"status": "healthy"}

def test_end_to_end_pipeline(client, db, user_a_token, user_b_token, user_a_id, user_b_id):
    """
    Full pipeline test:
    1. User A uploads PDF
    2. User A processes PDF (extraction -> chunking -> embedding)
    3. User A searches for keyword
    4. User A asks question via QA
    5. User B isolation checks (search, QA, process, get, delete)
    6. User A deletes document, confirming database and disk cleanup
    """
    pdf_content = create_sample_pdf_bytes(
        title="DocuMind AI Architecture Overview",
        body="DocuMind AI is an enterprise document intelligence system. "
             "It uses PyMuPDF for text extraction, sentence transformers for embeddings, "
             "and pgvector for high speed cosine similarity search."
    )

    # 1. Upload
    upload_res = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {user_a_token}"},
        files={"file": ("architecture.pdf", pdf_content, "application/pdf")}
    )
    assert upload_res.status_code == 201
    doc_data = upload_res.json()
    doc_id = doc_data["id"]
    assert doc_data["status"] == "uploaded"

    doc_record = db.query(Document).filter(Document.id == doc_id).first()
    assert doc_record is not None
    stored_path = doc_record.stored_path
    assert os.path.exists(stored_path)

    # 2. Process (Extraction -> Chunking -> Embeddings)
    # Using real sentence-transformers and real Postgres pgvector
    process_res = client.post(
        f"/api/v1/documents/{doc_id}/process",
        headers={"Authorization": f"Bearer {user_a_token}"}
    )
    assert process_res.status_code == 200
    processed_doc = process_res.json()
    assert processed_doc["status"] == "completed"
    assert processed_doc["chunk_count"] >= 1

    # Verify chunks in DB
    chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).all()
    assert len(chunks) >= 1
    assert chunks[0].embedding is not None

    # 3. Semantic Search
    search_res = client.post(
        "/api/v1/search/",
        headers={"Authorization": f"Bearer {user_a_token}"},
        json={"query": "document intelligence system pgvector", "top_k": 3, "min_similarity": 0.2}
    )
    assert search_res.status_code == 200
    search_hits = search_res.json()
    assert len(search_hits) >= 1
    assert search_hits[0]["document_id"] == doc_id
    assert search_hits[0]["document_name"] == "architecture.pdf"
    assert "DocuMind AI" in search_hits[0]["text"]
    assert search_hits[0]["similarity_score"] > 0.2

    # 4. RAG Question Answering (using Mock LLM adapter to avoid paid external calls)
    with patch("app.api.routes.qa.get_llm_adapter") as mock_adapter_getter:
        mock_adapter_getter.return_value = MockLLMAdapter(
            default_response="DocuMind AI uses PyMuPDF, sentence-transformers, and pgvector."
        )
        qa_res = client.post(
            "/api/v1/qa/ask",
            headers={"Authorization": f"Bearer {user_a_token}"},
            json={"question": "What technologies does DocuMind AI use?", "top_k": 3, "min_similarity": 0.2}
        )
        assert qa_res.status_code == 200
        qa_data = qa_res.json()
        assert "DocuMind AI uses PyMuPDF" in qa_data["answer"]
        assert len(qa_data["citations"]) >= 1
        citation = qa_data["citations"][0]
        assert citation["document_id"] == doc_id
        assert citation["document_name"] == "architecture.pdf"
        assert citation["page_start"] == 1

    # 5. Cross-User Isolation
    # User B searches: should see 0 hits
    b_search = client.post(
        "/api/v1/search/",
        headers={"Authorization": f"Bearer {user_b_token}"},
        json={"query": "DocuMind AI", "min_similarity": 0.0}
    )
    assert b_search.status_code == 200
    assert len(b_search.json()) == 0

    # User B asks QA: should find no passages
    b_qa = client.post(
        "/api/v1/qa/ask",
        headers={"Authorization": f"Bearer {user_b_token}"},
        json={"question": "What is DocuMind AI?"}
    )
    assert b_qa.status_code == 200
    assert "not contain sufficient information" in b_qa.json()["answer"].lower()
    assert b_qa.json()["citations"] == []

    # User B tries targeted query on User A's doc -> 404
    b_target_qa = client.post(
        "/api/v1/qa/ask",
        headers={"Authorization": f"Bearer {user_b_token}"},
        json={"question": "What is DocuMind AI?", "document_id": doc_id}
    )
    assert b_target_qa.status_code == 404

    # User B tries to process User A's doc -> 404
    b_process = client.post(
        f"/api/v1/documents/{doc_id}/process",
        headers={"Authorization": f"Bearer {user_b_token}"}
    )
    assert b_process.status_code == 404

    # User B tries to delete User A's doc -> 404
    b_delete = client.delete(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {user_b_token}"}
    )
    assert b_delete.status_code == 404

    # 6. User A Deletes Document
    delete_res = client.delete(
        f"/api/v1/documents/{doc_id}",
        headers={"Authorization": f"Bearer {user_a_token}"}
    )
    assert delete_res.status_code == 200

    # Verify DB cleanup
    doc_after_delete = db.query(Document).filter(Document.id == doc_id).first()
    assert doc_after_delete is None
    chunks_after_delete = db.query(Chunk).filter(Chunk.document_id == doc_id).all()
    assert len(chunks_after_delete) == 0

    # Verify disk file cleanup
    assert not os.path.exists(stored_path)

def test_empty_pdf_pipeline_graceful_handling(client, db, user_a_token):
    """
    Test that an empty/scanned PDF without extractable text gracefully finishes with warnings
    and returns 0 chunks without breaking the search or QA pipeline.
    """
    # Create PDF with blank page
    doc = fitz.open()
    doc.new_page()
    empty_pdf_bytes = doc.write()
    doc.close()

    upload_res = client.post(
        "/api/v1/documents/upload",
        headers={"Authorization": f"Bearer {user_a_token}"},
        files={"file": ("blank.pdf", empty_pdf_bytes, "application/pdf")}
    )
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    process_res = client.post(
        f"/api/v1/documents/{doc_id}/process",
        headers={"Authorization": f"Bearer {user_a_token}"}
    )
    assert process_res.status_code == 200
    data = process_res.json()
    assert data["status"] == "completed_with_warnings"
    assert data["chunk_count"] == 0

    # Search should safely return 0 results
    search_res = client.post(
        "/api/v1/search/",
        headers={"Authorization": f"Bearer {user_a_token}"},
        json={"query": "anything"}
    )
    assert search_res.status_code == 200
    assert search_res.json() == []

    # Clean up
    client.delete(f"/api/v1/documents/{doc_id}", headers={"Authorization": f"Bearer {user_a_token}"})

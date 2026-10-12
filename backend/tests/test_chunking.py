import pytest
import os
import uuid
from unittest.mock import patch
from app.db.models import Document, DocumentPage, Chunk, DocumentStatus, PageExtractionMethod, ExtractionMethod
from app.core.config import settings
from app.services.chunking import chunk_text

def test_chunk_text_short():
    chunks = chunk_text("short text", 100, 20)
    assert len(chunks) == 1
    assert chunks[0] == "short text"

def test_chunk_text_long_with_overlap():
    text = "A" * 100 + "B" * 100
    # chunk size 120, overlap 20
    # chunk 1: 0-120 (100 As, 20 Bs)
    # start moves to 120 - 20 = 100
    # chunk 2: 100-220 (100 Bs)
    chunks = chunk_text(text, 120, 20)
    assert len(chunks) == 2
    assert chunks[0] == "A" * 100 + "B" * 20
    assert chunks[1] == "B" * 100

def test_chunk_text_empty():
    assert chunk_text("", 100, 20) == []

def setup_mock_doc(db, user_a_id, pages_text=[]):
    doc_id = uuid.uuid4()
    doc = Document(id=doc_id, owner_id=user_a_id, original_filename="test.pdf", 
                   stored_path="/tmp/fake", file_size=100, content_hash=str(uuid.uuid4()), status=DocumentStatus.completed)
    db.add(doc)
    db.commit()
    
    pages = []
    for i, t in enumerate(pages_text):
        pages.append(DocumentPage(
            document_id=doc_id,
            owner_id=user_a_id,
            page_number=i+1,
            extraction_method=PageExtractionMethod.text if t else PageExtractionMethod.empty,
            text=t if t else None
        ))
    db.add_all(pages)
    db.commit()
    return doc_id

def test_integration_chunking(client, db, user_a_id, user_a_token):
    # This assumes we hit the process endpoint, which runs extraction then chunking.
    # But wait! If we hit the process endpoint, it will try to open /tmp/fake as a PDF and fail.
    # We should directly test `process_document_chunking` or mock extraction.
    from app.services.chunking import process_document_chunking
    
    # We will use the service directly for these tests to isolate chunking logic
    text = "A" * 900 # with chunk size 800, overlap 120
    doc_id = setup_mock_doc(db, user_a_id, [text, "", "B" * 800])
    
    doc = process_document_chunking(db, doc_id, user_a_id)
    
    assert doc.status == DocumentStatus.generating_embeddings
    
    chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).order_by(Chunk.chunk_index).all()
    # Page 1: "A"*900 -> chunk 0 (800 chars), chunk 1 (220 chars: overlap 120 + 100)
    # wait, start 0: 0-800. Next start: 800 - 120 = 680. 680-1480 (gets 680-900 which is 220 chars).
    # Page 2: empty (no chunks)
    # Page 3: "B"*800 -> chunk 2 (800 chars). Total 3 chunks.
    assert len(chunks) == 3
    
    assert chunks[0].page_start == 1
    assert chunks[0].page_end == 1
    assert len(chunks[0].text) == 800
    assert chunks[0].chunk_index == 0
    
    assert chunks[1].page_start == 1
    assert len(chunks[1].text) == 220
    assert chunks[1].chunk_index == 1
    
    assert chunks[2].page_start == 3
    assert len(chunks[2].text) == 800
    assert chunks[2].chunk_index == 2

def test_chunking_idempotency(db, user_a_id):
    from app.services.chunking import process_document_chunking
    doc_id = setup_mock_doc(db, user_a_id, ["A" * 100])
    
    process_document_chunking(db, doc_id, user_a_id)
    chunks1 = db.query(Chunk).filter(Chunk.document_id == doc_id).count()
    assert chunks1 == 1
    
    # Run again (simulate status being reset)
    doc = db.query(Document).filter(Document.id == doc_id).first()
    doc.status = DocumentStatus.completed
    db.commit()
    
    process_document_chunking(db, doc_id, user_a_id)
    chunks2 = db.query(Chunk).filter(Chunk.document_id == doc_id).count()
    assert chunks2 == 1 # still 1 chunk, no duplicates

def test_unauthorized_chunking(db, user_a_id, user_b_id):
    from app.services.chunking import process_document_chunking
    doc_id = setup_mock_doc(db, user_a_id, ["A" * 100])
    
    with pytest.raises(ValueError) as exc:
        process_document_chunking(db, doc_id, user_b_id)
    assert "not found or unauthorized" in str(exc.value)

def test_database_failure_in_chunking(db, user_a_id):
    from app.services.chunking import process_document_chunking
    doc_id = setup_mock_doc(db, user_a_id, ["A" * 100])
    
    with patch("sqlalchemy.orm.session.Session.add_all") as mock_add_all:
        mock_add_all.side_effect = Exception("DB failure")
        doc = process_document_chunking(db, doc_id, user_a_id)
        assert doc.status == DocumentStatus.failed
        assert doc.error_code == "CHUNKING_ERROR"

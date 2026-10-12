import pytest
import uuid
import numpy as np
from unittest.mock import patch, MagicMock
from app.db.models import Document, Chunk, DocumentStatus
from app.services.embeddings import process_document_embeddings

def setup_mock_doc_with_chunks(db, user_a_id, chunk_texts=[]):
    doc_id = uuid.uuid4()
    doc = Document(id=doc_id, owner_id=user_a_id, original_filename="test.pdf", 
                   stored_path="/tmp/fake", file_size=100, content_hash=str(uuid.uuid4()), status=DocumentStatus.generating_embeddings)
    db.add(doc)
    db.commit()
    
    chunks = []
    for i, t in enumerate(chunk_texts):
        chunks.append(Chunk(
            owner_id=user_a_id,
            document_id=doc_id,
            document_name="test.pdf",
            page_start=1,
            page_end=1,
            chunk_index=i,
            text=t
        ))
    db.add_all(chunks)
    db.commit()
    return doc_id

@patch("app.services.embeddings.generate_embeddings")
def test_successful_embeddings(mock_generate, db, user_a_id):
    doc_id = setup_mock_doc_with_chunks(db, user_a_id, ["Chunk 1", "Chunk 2"])
    
    # Mock returning 384-dim vectors
    mock_generate.return_value = [[0.1] * 384, [0.2] * 384]
    
    doc = process_document_embeddings(db, doc_id, user_a_id)
    assert doc.status == DocumentStatus.completed
    
    chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).order_by(Chunk.chunk_index).all()
    assert len(chunks) == 2
    
    # pgvector returns numpy array or list depending on the driver, but we can check shape
    assert len(chunks[0].embedding) == 384
    
    # Convert whatever vector format pgvector returns into a list/array to check values
    # In pgvector-sqlalchemy, it's typically a numpy array
    emb1 = chunks[0].embedding
    if isinstance(emb1, np.ndarray):
        assert emb1[0] == pytest.approx(0.1)
    else:
        assert emb1[0] == pytest.approx(0.1)
        
    # Embeddings service generates contextual text representations including document and page info
    expected_texts = [
        "Document: test | Page 1 | Chunk 1",
        "Document: test | Page 1 | Chunk 2"
    ]
    mock_generate.assert_called_once_with(expected_texts)

def test_empty_input_embeddings(db, user_a_id):
    # Empty chunk list
    doc_id = setup_mock_doc_with_chunks(db, user_a_id, [])
    
    doc = process_document_embeddings(db, doc_id, user_a_id)
    assert doc.status == DocumentStatus.completed
    
    chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).all()
    assert len(chunks) == 0

def test_unauthorized_embeddings(db, user_a_id, user_b_id):
    doc_id = setup_mock_doc_with_chunks(db, user_a_id, ["Chunk 1"])
    with pytest.raises(ValueError) as exc:
        process_document_embeddings(db, doc_id, user_b_id)
    assert "not found or unauthorized" in str(exc.value)

@patch("app.services.embeddings.generate_embeddings")
def test_database_failure_embeddings(mock_generate, db, user_a_id):
    doc_id = setup_mock_doc_with_chunks(db, user_a_id, ["Chunk 1"])
    mock_generate.side_effect = Exception("Model or DB failure")
    
    doc = process_document_embeddings(db, doc_id, user_a_id)
    assert doc.status == DocumentStatus.failed
    assert doc.error_code == "EMBEDDING_ERROR"

@patch("app.services.embeddings.generate_embeddings")
def test_repeated_processing_embeddings(mock_generate, db, user_a_id):
    doc_id = setup_mock_doc_with_chunks(db, user_a_id, ["Chunk 1"])
    mock_generate.return_value = [[0.1] * 384]
    
    doc = process_document_embeddings(db, doc_id, user_a_id)
    assert doc.status == DocumentStatus.completed
    
    # Try again
    with pytest.raises(ValueError) as exc:
        process_document_embeddings(db, doc_id, user_a_id)
    assert "cannot generate embeddings" in str(exc.value)

@patch("app.services.embeddings.generate_embeddings")
def test_batching_embeddings(mock_generate, db, user_a_id):
    # Generate 65 chunks to force batching (batch size 32 -> 3 batches)
    chunk_texts = [f"Chunk {i}" for i in range(65)]
    doc_id = setup_mock_doc_with_chunks(db, user_a_id, chunk_texts)
    
    def side_effect(texts):
        return [[0.1] * 384 for _ in texts]
        
    mock_generate.side_effect = side_effect
    
    doc = process_document_embeddings(db, doc_id, user_a_id)
    assert doc.status == DocumentStatus.completed
    
    assert mock_generate.call_count == 3
    
    chunks = db.query(Chunk).filter(Chunk.document_id == doc_id).all()
    assert all(len(c.embedding) == 384 for c in chunks)

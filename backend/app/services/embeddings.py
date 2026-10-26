import uuid
from typing import List
from sqlalchemy.orm import Session
from app.db.models import Document, Chunk, DocumentStatus
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


# Load the embedding model only when first needed.
_model = None

def get_model():
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            _model = SentenceTransformer("all-MiniLM-L6-v2")
        except Exception as e:
            logger.exception("Failed to load SentenceTransformer")
            raise RuntimeError("SentenceTransformer model is unavailable") from e
    return _model



def generate_embeddings(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []

    model = get_model()
    embeddings = model.encode(
        texts,
        batch_size=4,
        convert_to_numpy=True
    )
    return embeddings.tolist()


def process_document_embeddings(db: Session, document_id: uuid.UUID, user_id: uuid.UUID, reprocess: bool = False) -> Document:
    doc = db.query(Document).filter(Document.id == document_id, Document.owner_id == user_id).first()
    if not doc:
        raise ValueError("Document not found or unauthorized")
        
    allowed_statuses = [DocumentStatus.generating_embeddings, DocumentStatus.completed_with_warnings]
    if reprocess:
        allowed_statuses.append(DocumentStatus.completed)

    if doc.status not in allowed_statuses:
        raise ValueError(f"Document is in status {doc.status}, cannot generate embeddings.")
        
    original_status = doc.status
    doc.status = DocumentStatus.generating_embeddings
    db.commit()
    
    try:
        chunks = db.query(Chunk).filter(Chunk.document_id == doc.id).order_by(Chunk.chunk_index).all()
        
        if chunks:
            batch_size = 32
            for i in range(0, len(chunks), batch_size):
                batch = chunks[i:i+batch_size]
                texts = [chunk.text for chunk in batch]
                
                # Build contextual text representation for dense embedding
                texts_to_embed = []
                valid_chunks = []
                for chunk in batch:
                    if chunk.text:
                        # Normalize document filename for clean contextual prefix
                        doc_clean_name = chunk.document_name.rsplit('.', 1)[0].replace('_', ' ')
                        page_ref = f"Page {chunk.page_start}" if chunk.page_start == chunk.page_end else f"Pages {chunk.page_start}-{chunk.page_end}"
                        contextual_text = f"Document: {doc_clean_name} | {page_ref} | {chunk.text}"
                        texts_to_embed.append(contextual_text)
                        valid_chunks.append(chunk)
                
                if texts_to_embed:
                    embeddings = generate_embeddings(texts_to_embed)
                    for chunk, emb in zip(valid_chunks, embeddings):
                        chunk.embedding = emb
                        
        if original_status == DocumentStatus.completed_with_warnings:
            doc.status = DocumentStatus.completed_with_warnings
        else:
            doc.status = DocumentStatus.completed
            
        db.commit()
        
    except Exception as e:
        db.rollback()
        doc = db.query(Document).filter(Document.id == doc.id).first()
        doc.status = DocumentStatus.failed
        doc.error_code = "EMBEDDING_ERROR"
        doc.error_message = str(e)
        db.commit()
        
    return doc

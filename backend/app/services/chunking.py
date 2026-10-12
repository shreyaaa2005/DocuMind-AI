import uuid
from typing import List
from sqlalchemy.orm import Session
from app.db.models import Document, DocumentPage, Chunk, DocumentStatus
from app.core.config import settings

def chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
    if not text:
        return []
    
    chunks = []
    start = 0
    text_len = len(text)
    
    while start < text_len:
        end = start + chunk_size
        chunks.append(text[start:end])
        if end >= text_len:
            break
        start += chunk_size - chunk_overlap
        
    return chunks

def process_document_chunking(db: Session, document_id: uuid.UUID, user_id: uuid.UUID) -> Document:
    doc = db.query(Document).filter(Document.id == document_id, Document.owner_id == user_id).first()
    if not doc:
        raise ValueError("Document not found or unauthorized")
        
    if doc.status not in [DocumentStatus.completed, DocumentStatus.completed_with_warnings, DocumentStatus.chunking]:
        raise ValueError(f"Document is in status {doc.status}, cannot process chunking.")
        
    original_status = doc.status
    doc.status = DocumentStatus.chunking
    db.commit()
    
    try:
        db.query(Chunk).filter(Chunk.document_id == doc.id).delete()
        
        pages = db.query(DocumentPage).filter(DocumentPage.document_id == doc.id).order_by(DocumentPage.page_number).all()
        
        chunks_to_add = []
        chunk_index = 0
        
        for page in pages:
            if not page.text:
                continue
                
            page_chunks = chunk_text(page.text, settings.CHUNK_SIZE_CHARS, settings.CHUNK_OVERLAP_CHARS)
            
            for chunk_text_content in page_chunks:
                clean_text = " ".join(chunk_text_content.split())
                if not clean_text:
                    continue
                    
                db_chunk = Chunk(
                    owner_id=doc.owner_id,
                    document_id=doc.id,
                    document_name=doc.original_filename,
                    page_start=page.page_number,
                    page_end=page.page_number,
                    chunk_index=chunk_index,
                    text=clean_text,
                    extraction_method=page.extraction_method,
                    ocr_confidence=page.ocr_confidence
                )
                chunks_to_add.append(db_chunk)
                chunk_index += 1
                
        db.add_all(chunks_to_add)
        doc.chunk_count = chunk_index
        
        if original_status == DocumentStatus.completed_with_warnings:
            doc.status = DocumentStatus.completed_with_warnings
        else:
            doc.status = DocumentStatus.generating_embeddings
            
        db.commit()
        
    except Exception as e:
        db.rollback()
        doc = db.query(Document).filter(Document.id == doc.id).first()
        doc.status = DocumentStatus.failed
        doc.error_code = "CHUNKING_ERROR"
        doc.error_message = str(e)
        db.commit()
        
    return doc

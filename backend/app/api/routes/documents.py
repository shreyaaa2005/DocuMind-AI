import os
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from app.api.deps import get_current_user, get_db
from app.db.models import Document, DocumentStatus
from app.services.pdf_extraction import process_document_extraction
from app.services.chunking import process_document_chunking
from app.services.embeddings import process_document_embeddings
from app.core.config import settings
import uuid

router = APIRouter()

@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: uuid.UUID = Depends(get_current_user)
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    header = await file.read(5)
    if header != b"%PDF-":
        raise HTTPException(status_code=400, detail="Invalid PDF file")
    
    await file.seek(0)
    
    os.makedirs(settings.STORAGE_DIR, exist_ok=True)
    file_id = uuid.uuid4()
    stored_path = os.path.join(settings.STORAGE_DIR, f"{file_id}.pdf")
    
    hasher = hashlib.sha256()
    file_size = 0
    
    try:
        with open(stored_path, "wb") as out_file:
            while chunk := await file.read(8192):
                file_size += len(chunk)
                if file_size > settings.MAX_UPLOAD_SIZE_BYTES:
                    out_file.close()
                    os.remove(stored_path)
                    raise HTTPException(status_code=413, detail="File too large")
                hasher.update(chunk)
                out_file.write(chunk)
    except Exception as e:
        if os.path.exists(stored_path):
            os.remove(stored_path)
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail="Error saving file")
        
    if file_size == 0:
        os.remove(stored_path)
        raise HTTPException(status_code=400, detail="Empty file")

    content_hash = hasher.hexdigest()
    
    existing_doc = db.query(Document).filter(
        Document.owner_id == current_user, 
        Document.content_hash == content_hash
    ).first()
    
    if existing_doc:
        os.remove(stored_path)
        raise HTTPException(status_code=409, detail="Document already exists")
        
    doc = Document(
        id=file_id,
        owner_id=current_user,
        original_filename=os.path.basename(file.filename),
        stored_path=stored_path,
        file_size=file_size,
        content_hash=content_hash,
        status=DocumentStatus.uploaded
    )
    
    try:
        db.add(doc)
        db.commit()
        db.refresh(doc)
    except Exception:
        db.rollback()
        os.remove(stored_path)
        raise HTTPException(status_code=500, detail="Database error")
        
    return {
        "id": doc.id,
        "original_filename": doc.original_filename,
        "status": doc.status,
        "file_size": doc.file_size
    }

@router.post("/{document_id}/process")
def process_document(
    document_id: uuid.UUID,
    reprocess: bool = Query(default=False, description="Force re-extraction and re-embedding"),
    db: Session = Depends(get_db),
    current_user: uuid.UUID = Depends(get_current_user)
):
    try:
        doc = process_document_extraction(db, document_id, current_user, reprocess=reprocess)
        if doc.status in [DocumentStatus.completed, DocumentStatus.completed_with_warnings]:
            doc = process_document_chunking(db, document_id, current_user)
        if doc.status == DocumentStatus.generating_embeddings or (doc.status == DocumentStatus.completed_with_warnings and doc.chunk_count and doc.chunk_count > 0):
            doc = process_document_embeddings(db, document_id, current_user, reprocess=reprocess)
        return {
            "id": doc.id,
            "original_filename": doc.original_filename,
            "status": doc.status,
            "page_count": doc.page_count,
            "chunk_count": doc.chunk_count,
            "extraction_method": doc.extraction_method,
            "warnings": doc.warnings,
            "error_code": doc.error_code,
            "error_message": doc.error_message
        }
    except ValueError as e:
        if "not found or unauthorized" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Document file not found")

@router.get("/")
def list_documents(db: Session = Depends(get_db), current_user: uuid.UUID = Depends(get_current_user)):
    docs = db.query(Document).filter(Document.owner_id == current_user).all()
    return docs

@router.get("/{document_id}")
def get_document(document_id: uuid.UUID, db: Session = Depends(get_db), current_user: uuid.UUID = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id, Document.owner_id == current_user).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    return doc

@router.delete("/{document_id}")
def delete_document(document_id: uuid.UUID, db: Session = Depends(get_db), current_user: uuid.UUID = Depends(get_current_user)):
    doc = db.query(Document).filter(Document.id == document_id, Document.owner_id == current_user).first()
    if not doc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
    stored_path = doc.stored_path
    db.delete(doc)
    db.commit()
    if stored_path and os.path.exists(stored_path):
        try:
            os.remove(stored_path)
        except OSError:
            pass
    return {"message": "Document deleted"}

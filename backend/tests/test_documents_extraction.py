import pytest
import os
import uuid
import fitz
from app.db.models import Document, DocumentPage, DocumentStatus, ExtractionMethod, PageExtractionMethod
from app.core.config import settings

def generate_test_pdf(path: str, pages_spec: list):
    """
    pages_spec is a list of dicts: [{'text': 'Hello'}, {}]
    """
    doc = fitz.open()
    for spec in pages_spec:
        page = doc.new_page()
        if "text" in spec:
            page.insert_text((50, 50), spec["text"])
    doc.save(path)
    doc.close()

def test_successful_extraction(client, db, user_a_id, user_a_token):
    doc_id = uuid.uuid4()
    pdf_path = os.path.join(settings.STORAGE_DIR, f"{doc_id}.pdf")
    long_text = "This is a very long text to ensure it passes the fifty characters limit for OCR detection."
    generate_test_pdf(pdf_path, [{"text": long_text}, {"text": long_text}])
    
    doc = Document(id=doc_id, owner_id=user_a_id, original_filename="test.pdf", 
                   stored_path=pdf_path, file_size=100, content_hash=str(uuid.uuid4()), status=DocumentStatus.uploaded)
    db.add(doc)
    db.commit()
    
    response = client.post(f"/api/v1/documents/{doc_id}/process", headers={"Authorization": f"Bearer {user_a_token}"})
    assert response.status_code == 200
    
    db.refresh(doc)
    assert doc.status == DocumentStatus.completed
    assert doc.extraction_method == ExtractionMethod.text
    
    pages = db.query(DocumentPage).filter(DocumentPage.document_id == doc.id).order_by(DocumentPage.page_number).all()
    assert len(pages) == 2
    assert pages[0].page_number == 1
    assert long_text in pages[0].text
    assert pages[0].extraction_method == PageExtractionMethod.text
    assert pages[1].page_number == 2

def test_empty_scanned_pdf(client, db, user_a_id, user_a_token):
    doc_id = uuid.uuid4()
    pdf_path = os.path.join(settings.STORAGE_DIR, f"{doc_id}.pdf")
    generate_test_pdf(pdf_path, [{}])
    
    doc = Document(id=doc_id, owner_id=user_a_id, original_filename="empty.pdf", 
                   stored_path=pdf_path, file_size=100, content_hash=str(uuid.uuid4()), status=DocumentStatus.uploaded)
    db.add(doc)
    db.commit()
    
    response = client.post(f"/api/v1/documents/{doc_id}/process", headers={"Authorization": f"Bearer {user_a_token}"})
    assert response.status_code == 200
    
    db.refresh(doc)
    assert doc.status == DocumentStatus.completed_with_warnings
    assert doc.extraction_method == ExtractionMethod.ocr
    assert "ocr_needed" in doc.warnings
    
    pages = db.query(DocumentPage).filter(DocumentPage.document_id == doc.id).all()
    assert len(pages) == 1
    assert pages[0].extraction_method == PageExtractionMethod.empty
    assert pages[0].text is None

def test_invalid_pdf(client, db, user_a_id, user_a_token):
    doc_id = uuid.uuid4()
    pdf_path = os.path.join(settings.STORAGE_DIR, f"{doc_id}.pdf")
    with open(pdf_path, "wb") as f:
        f.write(b"not a valid pdf")
        
    doc = Document(id=doc_id, owner_id=user_a_id, original_filename="invalid.pdf", 
                   stored_path=pdf_path, file_size=10, content_hash=str(uuid.uuid4()), status=DocumentStatus.uploaded)
    db.add(doc)
    db.commit()
    
    response = client.post(f"/api/v1/documents/{doc_id}/process", headers={"Authorization": f"Bearer {user_a_token}"})
    assert response.status_code == 200
    
    db.refresh(doc)
    assert doc.status == DocumentStatus.failed
    assert doc.error_code == "INVALID_PDF"

def test_repeated_processing(client, db, user_a_id, user_a_token):
    doc_id = uuid.uuid4()
    pdf_path = os.path.join(settings.STORAGE_DIR, f"{doc_id}.pdf")
    generate_test_pdf(pdf_path, [{"text": "Retry processing with a text string that is long enough to pass."}])
    
    doc = Document(id=doc_id, owner_id=user_a_id, original_filename="retry.pdf", 
                   stored_path=pdf_path, file_size=100, content_hash=str(uuid.uuid4()), status=DocumentStatus.failed)
    db.add(doc)
    db.commit()
    
    response = client.post(f"/api/v1/documents/{doc_id}/process", headers={"Authorization": f"Bearer {user_a_token}"})
    assert response.status_code == 200
    db.refresh(doc)
    assert doc.status == DocumentStatus.completed

    response2 = client.post(f"/api/v1/documents/{doc_id}/process", headers={"Authorization": f"Bearer {user_a_token}"})
    assert response2.status_code == 400
    assert "cannot process" in response2.json()["detail"]

def test_unauthorized_access(client, db, user_a_id, user_b_token):
    doc_id = uuid.uuid4()
    pdf_path = os.path.join(settings.STORAGE_DIR, f"{doc_id}.pdf")
    generate_test_pdf(pdf_path, [{"text": "Secret"}])
    
    doc = Document(id=doc_id, owner_id=user_a_id, original_filename="secret.pdf", 
                   stored_path=pdf_path, file_size=100, content_hash=str(uuid.uuid4()), status=DocumentStatus.uploaded)
    db.add(doc)
    db.commit()
    
    response = client.post(f"/api/v1/documents/{doc_id}/process", headers={"Authorization": f"Bearer {user_b_token}"})
    assert response.status_code == 404

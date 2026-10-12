import fitz # PyMuPDF
import os
import uuid
from sqlalchemy.orm import Session
from app.db.models import Document, DocumentPage, DocumentStatus, PageExtractionMethod, ExtractionMethod
from app.core.config import settings

def process_document_extraction(db: Session, document_id: uuid.UUID, user_id: uuid.UUID, reprocess: bool = False) -> Document:
    # 1. Fetch document and verify ownership
    doc = db.query(Document).filter(Document.id == document_id, Document.owner_id == user_id).first()
    if not doc:
        raise ValueError("Document not found or unauthorized")
        
    allowed_statuses = [
        DocumentStatus.uploaded,
        DocumentStatus.validating,
        DocumentStatus.extracting_text,
        DocumentStatus.failed
    ]
    if reprocess:
        allowed_statuses.extend([DocumentStatus.completed, DocumentStatus.completed_with_warnings])

    if doc.status not in allowed_statuses:
        raise ValueError(f"Document is in status {doc.status}, cannot process text extraction.")
        
    doc.status = DocumentStatus.extracting_text
    doc.error_code = None
    doc.error_message = None
    db.commit()
    
    # Check file exists
    if not os.path.exists(doc.stored_path):
        doc.status = DocumentStatus.failed
        doc.error_code = "FILE_NOT_FOUND"
        doc.error_message = "Stored file is missing from disk"
        db.commit()
        raise FileNotFoundError("Stored file is missing")

    try:
        # Open PDF
        try:
            pdf_doc = fitz.open(doc.stored_path)
        except Exception as e:
            doc.status = DocumentStatus.failed
            doc.error_code = "INVALID_PDF"
            doc.error_message = f"Could not open PDF: {str(e)}"
            db.commit()
            return doc
            
        if pdf_doc.needs_pass:
            doc.status = DocumentStatus.failed
            doc.error_code = "ENCRYPTED_PDF"
            doc.error_message = "Password-protected PDFs are not supported"
            db.commit()
            pdf_doc.close()
            return doc
            
        if pdf_doc.page_count == 0:
            doc.status = DocumentStatus.failed
            doc.error_code = "EMPTY_PDF"
            doc.error_message = "PDF has no pages"
            db.commit()
            pdf_doc.close()
            return doc
            
        doc.page_count = pdf_doc.page_count
        db.commit()
        
        # Clear existing pages if retry
        db.query(DocumentPage).filter(DocumentPage.document_id == doc.id).delete()
        
        empty_pages = 0
        has_text_pages = False
        pages_to_add = []
        
        for page_num in range(pdf_doc.page_count):
            page = pdf_doc[page_num]
            text = page.get_text()
            
            page_method = PageExtractionMethod.text
            page_warnings = {}
            
            if not text or len(text.strip()) < settings.OCR_MIN_CHARS_PER_PAGE:
                page_method = PageExtractionMethod.empty
                text = None
                empty_pages += 1
                page_warnings["message"] = "Scanned page or no extractable text. OCR may be required."
            else:
                has_text_pages = True
                
            db_page = DocumentPage(
                document_id=doc.id,
                owner_id=doc.owner_id,
                page_number=page_num + 1,
                extraction_method=page_method,
                text=text,
                warnings=page_warnings if page_warnings else None,
                status="processed" if text else "needs_ocr"
            )
            pages_to_add.append(db_page)
            
        db.add_all(pages_to_add)
        
        # Temporary terminal status for this phase
        if empty_pages > 0:
            doc.warnings = doc.warnings or {}
            doc.warnings["ocr_needed"] = f"{empty_pages} pages appear to be scanned or empty and may require OCR."
            doc.status = DocumentStatus.completed_with_warnings
            doc.extraction_method = ExtractionMethod.mixed if has_text_pages else ExtractionMethod.ocr
        else:
            doc.status = DocumentStatus.completed
            doc.extraction_method = ExtractionMethod.text
            
        db.commit()
        pdf_doc.close()
        
    except Exception as e:
        db.rollback()
        # Reload doc state
        doc = db.query(Document).filter(Document.id == doc.id).first()
        doc.status = DocumentStatus.failed
        doc.error_code = "EXTRACTION_ERROR"
        doc.error_message = str(e)
        db.commit()
        
    return doc

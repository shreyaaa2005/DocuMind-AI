import uuid
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.db.models import Document, Chunk
from app.services.embeddings import generate_embeddings
from app.services.llm import (
    get_llm_adapter,
    LLMServiceUnavailableError,
    LLMTimeoutError,
    LLMExecutionError,
    LLMError
)
from app.core.config import settings

router = APIRouter()

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="Question to ask over uploaded documents")
    document_id: Optional[uuid.UUID] = Field(default=None, description="Optional document ID to restrict QA retrieval")
    top_k: int = Field(default=settings.TOP_K, ge=1, le=20, description="Number of passages to retrieve for context")
    min_similarity: Optional[float] = Field(default=settings.MIN_SIMILARITY, ge=0.0, le=1.0, description="Minimum similarity threshold")

class Citation(BaseModel):
    document_id: uuid.UUID
    document_name: str
    page_start: int
    page_end: int
    text: str
    similarity_score: float

class AskResponse(BaseModel):
    answer: str
    citations: List[Citation]

@router.post("/ask", response_model=AskResponse)
def ask_question(
    request: AskRequest,
    db: Session = Depends(get_db),
    current_user: uuid.UUID = Depends(get_current_user)
):
    question = request.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question cannot be empty")

    # If document_id is provided, verify ownership and existence
    if request.document_id is not None:
        doc = db.query(Document).filter(
            Document.id == request.document_id,
            Document.owner_id == current_user
        ).first()
        if not doc:
            raise HTTPException(
                status_code=404,
                detail="Document not found or unauthorized"
            )

    # 1. Embed user question
    try:
        embeddings = generate_embeddings([question])
        if not embeddings:
            raise HTTPException(status_code=500, detail="Failed to generate question embedding")
        query_vector = embeddings[0]
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Embedding service unavailable")
    except Exception:
        raise HTTPException(status_code=500, detail="Error generating question embedding")

    # 2. Retrieve relevant chunks via pgvector cosine distance
    try:
        distance_col = Chunk.embedding.cosine_distance(query_vector).label("distance")
        query = (
            db.query(Chunk, distance_col)
            .filter(Chunk.owner_id == current_user)
            .filter(Chunk.embedding.is_not(None))
        )
        if request.document_id is not None:
            query = query.filter(Chunk.document_id == request.document_id)

        results = query.order_by(distance_col).limit(request.top_k).all()

        passages = []
        citations = []
        min_threshold = request.min_similarity if request.min_similarity is not None else settings.MIN_SIMILARITY
        
        # Safe diagnostics logging (IDs, document names, scores, preview only)
        import logging
        qa_logger = logging.getLogger("app.api.routes.qa")
        qa_logger.info(
            "QA retrieval for query '%s' (doc_filter=%s, top_k=%s, min_sim=%s): found %d total chunks in DB",
            question[:50], request.document_id, request.top_k, min_threshold, len(results)
        )

        for chunk, distance in results:
            similarity = 1.0 - float(distance)
            preview = (chunk.text[:60] + "...") if len(chunk.text) > 60 else chunk.text
            qa_logger.info(
                "  -> Chunk ID=%s, doc='%s', pages=%s-%s, sim=%.4f (passed=%s), preview='%s'",
                chunk.id, chunk.document_name, chunk.page_start, chunk.page_end, similarity, similarity >= min_threshold, preview
            )
            if similarity >= min_threshold:
                passages.append({
                    "document_id": chunk.document_id,
                    "document_name": chunk.document_name,
                    "page_start": chunk.page_start,
                    "page_end": chunk.page_end,
                    "text": chunk.text,
                    "similarity_score": similarity
                })
                citations.append(Citation(
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    text=chunk.text,
                    similarity_score=similarity
                ))
    except Exception as e:
        import logging
        logging.getLogger("app.api.routes.qa").error("Database search error: %s", e)
        raise HTTPException(status_code=500, detail="Database search error")

    # 3. Grounded Answer Generation
    if not passages:
        return AskResponse(
            answer="The provided documents do not contain sufficient information to answer this question.",
            citations=[]
        )

    try:
        adapter = get_llm_adapter()
        answer = adapter.generate_answer(question=question, passages=passages)
        return AskResponse(answer=answer, citations=citations)
    except LLMServiceUnavailableError as e:
        raise HTTPException(status_code=503, detail=f"LLM service unavailable: {str(e)}")
    except LLMTimeoutError as e:
        raise HTTPException(status_code=504, detail=f"LLM service timed out: {str(e)}")
    except LLMExecutionError as e:
        raise HTTPException(status_code=502, detail=f"LLM provider error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating answer: {str(e)}")

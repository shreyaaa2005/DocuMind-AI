import uuid
from typing import List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.api.deps import get_current_user, get_db
from app.db.models import Chunk
from app.services.embeddings import generate_embeddings
from app.core.config import settings

router = APIRouter()

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000, description="Search query")
    top_k: int = Field(default=settings.TOP_K, ge=1, le=20, description="Number of results to return")
    min_similarity: Optional[float] = Field(default=settings.MIN_SIMILARITY, ge=0.0, le=1.0)

class SearchResult(BaseModel):
    document_id: uuid.UUID
    document_name: str
    page_start: int
    page_end: int
    text: str
    similarity_score: float

@router.post("/", response_model=List[SearchResult])
def search_documents(
    request: SearchRequest,
    db: Session = Depends(get_db),
    current_user: uuid.UUID = Depends(get_current_user)
):
    query = request.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
        
    try:
        query_embeddings = generate_embeddings([query])
        if not query_embeddings:
            raise HTTPException(status_code=500, detail="Failed to generate query embedding")
        query_vector = query_embeddings[0]
    except RuntimeError:
        raise HTTPException(status_code=503, detail="Embedding service unavailable")
    except Exception:
        raise HTTPException(status_code=500, detail="Error generating embeddings")
        
    try:
        # pgvector cosine_distance (<=>). similarity = 1 - distance
        distance_col = Chunk.embedding.cosine_distance(query_vector).label('distance')
        
        results = (
            db.query(Chunk, distance_col)
            .filter(Chunk.owner_id == current_user)
            .filter(Chunk.embedding.is_not(None))
            .order_by(distance_col)
            .limit(request.top_k)
            .all()
        )
        
        formatted_results = []
        for chunk, distance in results:
            similarity = 1.0 - float(distance)
            if similarity >= request.min_similarity:
                formatted_results.append(SearchResult(
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    page_start=chunk.page_start,
                    page_end=chunk.page_end,
                    text=chunk.text,
                    similarity_score=similarity
                ))
                
        return formatted_results
        
    except Exception:
        raise HTTPException(status_code=500, detail="Database search error")

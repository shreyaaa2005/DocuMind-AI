# DocuMind AI — Complete Project Implementation & RAG Optimization Summary

## 1. Project Overview & Architecture
DocuMind AI is an enterprise-grade, privacy-first Retrieval-Augmented Generation (RAG) system designed for uploading, analyzing, indexing, and querying PDF documents with strict user isolation, mathematical attribution (citations), and hallucination safeguards.

### Core Stack
- **Backend**: FastAPI (Python 3.10), SQLAlchemy ORM, PostgreSQL with `pgvector` extension.
- **Embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (384-dimensional dense vectors).
- **Text Extraction & Chunking**: PyMuPDF (`fitz`), token & character-aware sliding window chunking with configurable overlap.
- **LLM Question Answering**: Google Generative AI (Gemini 3.5 Flash Lite) with strict prompt-injection defenses and grounded context isolation.
- **Frontend**: React, TypeScript, Vite, Tailwind CSS, Lucide icons.
- **Authentication**: Supabase JWT (ES256 & HS256 verification) with per-user tenant isolation and local demo development support.

---

## 2. Phase-by-Phase Implementation Steps

### Phase 1: Authentication & User Isolation
- Implemented Supabase JWT verification in `backend/app/core/security.py`.
- Enforced cryptographic token validation supporting both symmetric (`HS256`) and asymmetric (`ES256`) signing keys.
- Established tenant isolation across all database operations: `owner_id` is required and verified in every query across documents, pages, and chunk vectors.
- Created local development demo users (`demo-a`, `demo-b`) with deterministic test tokens while keeping signature verification active.

### Phase 2: PDF Upload & Processing Pipeline
- Implemented `POST /api/v1/documents/upload` with:
  - Magic bytes validation (`%PDF-`).
  - Size limitation (configurable up to 50MB).
  - SHA-256 content deduplication per user.
- Built `process_document_extraction` in `backend/app/services/pdf_extraction.py`:
  - Page-by-page text extraction using PyMuPDF (`fitz`).
  - Graceful handling of empty or scanned pages with OCR fallback markers and status `completed_with_warnings`.
  - Stored page-level text in `DocumentPage` records.

### Phase 3: Token-Aware Chunking
- Developed `process_document_chunking` in `backend/app/services/chunking.py`:
  - 800-character windows with 120-character overlaps.
  - Page-aware citation boundaries (`page_start`, `page_end`).
  - Chunk idempotency: re-running chunking cleanly replaces existing chunks for that document without orphan records.

### Phase 4: Local Dense Embeddings
- Integrated `sentence-transformers/all-MiniLM-L6-v2` in `backend/app/services/embeddings.py`:
  - Generates 384-dimensional dense embeddings locally.
  - Implemented batching (32 items per batch) to optimize GPU/CPU throughput.
  - Added **contextual document prefixes**: prepends document title and page reference to raw chunk text before embedding (e.g., `Document: Cortex AI | Page 7 | ...`).

### Phase 5: Vector Search with PostgreSQL `pgvector`
- Implemented `POST /api/v1/search`:
  - Computes cosine distance using pgvector's `<=>` operator against the `Chunk.embedding` column.
  - Strictly filtered by `Chunk.owner_id == current_user`.
  - Supports document filtering (`document_id`) and configurable `top_k`.

### Phase 6: RAG Question Answering Pipeline
- Implemented `POST /api/v1/qa/ask`:
  - Converts user questions to 384-dimensional query vectors.
  - Retrieves top-k candidate chunks matching the user's document scope.
  - Applies similarity threshold filtering (`1.0 - cosine_distance >= MIN_SIMILARITY`).
  - Formats retrieved chunks into an isolated, untrusted document context block.
  - Dispatches to LLM adapter (`GeminiAdapter`) with instructions to only answer using provided passages and state *"The provided documents do not contain sufficient information to answer this question"* if unsupported.
  - Attaches structured citations with document names, page numbers, and exact similarity scores.

### Phase 7: Complete Frontend Application
- Built a modern, responsive React + Vite interface:
  - **Documents Page**: Upload progress, document processing trigger, status badges, chunk count indicators, delete actions.
  - **Search Page**: Real-time semantic similarity search with score chips and page navigation.
  - **Ask Page (RAG QA)**: Interactive chat interface, document scope dropdown, adjustable similarity threshold slider, and expandable citation cards.
  - **Auth Context**: Supabase authentication with one-click Demo User switching.

---

## 3. Investigation & Resolution of Persistent RAG Failure

### The Issue
When asking questions over `CORTEX_AI_Research_Paper_IEEE (1).pdf` (79 chunks):
1. *"Summarize the key architectural decisions and requirements"*
2. *"what is this research paper includes"*
Both queries repeatedly failed with:
> *"The provided documents do not contain sufficient information to answer this question."*

### Root Causes Discovered
1. **Hardcoded Threshold Overrides**:
   - `MIN_SIMILARITY=0.5` was hardcoded in `backend/.env`, which took precedence over Pydantic default settings in `config.py`.
   - `frontend/src/api/qa.ts` was hardcoding `min_similarity: params.min_similarity ?? 0.5` in every request body, preventing backend configuration from taking effect.
2. **Dense Vector Geometry on Academic Synthesis Queries**:
   - For high-level synthesis questions over long technical documents, `all-MiniLM-L6-v2` produces cosine similarities between **0.25 and 0.38**:
     - Architecture query top chunk: **0.3604** (Chunk 47, Page 7).
     - Paper contents query top chunk: **0.3824** (Chunk 22, Page 3).
   - Because the threshold was locked at `0.50`, all 79 chunks were discarded during filtering.
3. **Gemini Model Deprecation & Thinking Token Truncation**:
   - `gemini-2.5-flash` was deprecated by Google's API (`404 NOT_FOUND`).
   - `gemini-3.5-flash` with a 1024 token limit spent 600–850 tokens on internal chain-of-thought, causing responses to be truncated at ~200 characters.
   - Upgraded to `gemini-3.5-flash-lite` with a 4096-token ceiling: zero thinking overhead, instant response generation, and complete answers.
4. **Error Classification & Diagnostics**:
   - Configured distinct HTTP status codes (503 for rate limits/service unavailable, 504 for timeout, 502 for provider error) to prevent upstream API issues from being misreported as missing documents.
   - Added safe diagnostic logging showing chunk IDs, page ranges, similarity scores, and filtering outcomes.

---

## 4. Key Files Modified

| File | Changes Made |
| :--- | :--- |
| `backend/app/core/config.py` | Calibrated default `MIN_SIMILARITY = 0.20`; configured `GEMINI_MODEL = "gemini-3.5-flash-lite"`. |
| `backend/.env` & `.env.example` | Updated `MIN_SIMILARITY=0.20` and set `GEMINI_MODEL=gemini-3.5-flash-lite`. |
| `backend/app/services/llm/adapter.py` | Upgraded to `gemini-3.5-flash-lite`, increased `maxOutputTokens` to 4096, mapped 429/503 to `LLMServiceUnavailableError` and 404 to `LLMExecutionError`. |
| `backend/app/api/routes/qa.py` | Implemented fallback to server `settings.MIN_SIMILARITY`, added safe retrieval diagnostics logging, and mapped provider exceptions to 502/503/504. |
| `backend/app/services/pdf_extraction.py` | Added `reprocess: bool = False` flag to allow safe re-extraction while preserving idempotency for completed documents. |
| `backend/app/services/embeddings.py` | Added `reprocess: bool = False` flag to allow clean re-embedding of chunks; preserved `completed_with_warnings` support. |
| `backend/app/api/routes/documents.py` | Exposed `reprocess: bool = Query(default=False)` on `POST /{document_id}/process`; guarded embeddings invocation when chunk count is zero. |
| `frontend/src/api/qa.ts` | Removed hardcoded `0.5` fallback in request payload so server-side configuration governs by default. |
| `frontend/src/pages/AskPage.tsx` | Calibrated default similarity threshold slider to `0.20`. |
| `backend/tests/test_qa.py` | Added regression tests for 0.25–0.38 similarity synthesis queries, provider error HTTP status mapping, and GeminiAdapter error classification. |

---

## 5. Verification & Test Results

### 1. Backend Pytest Suite
```
tests/test_auth.py ......................... PASSED
tests/test_chunking.py ..................... PASSED
tests/test_documents_auth.py ............... PASSED
tests/test_documents_extraction.py ......... PASSED
tests/test_documents_upload.py ............. PASSED
tests/test_e2e_pipeline.py ................. PASSED
tests/test_embeddings.py ................... PASSED
tests/test_qa.py ........................... PASSED
tests/test_search.py ....................... PASSED

======================= 66 passed, 1 warning in 13.67s =======================
```

### 2. Frontend Test Suite
```
 ✓ src/__tests__/citation.test.ts (1 test)
 ✓ src/__tests__/api_client.test.ts (5 tests)
 ✓ src/__tests__/health.test.ts (2 tests)

 Test Files  3 passed (3)
      Tests  8 passed (8)
```

### 3. Frontend Production Build
```
vite v8.3.4 building client environment for production...
✓ 2023 modules transformed.
dist/index.html                   0.96 kB
dist/assets/index-DlX05NA_.css   35.00 kB
dist/assets/index-dQZt8dMJ.js   559.18 kB
✓ built in 904ms
```

### 4. End-to-End Live RAG Verification
Both target queries over `CORTEX_AI_Research_Paper_IEEE (1).pdf` were executed against the running backend server:
- **"Summarize the key architectural decisions and requirements"**:
  - Returned HTTP `200 OK`.
  - Detailed architectural summary (13-stage linear processing pipeline, emotion engine, memory engine, token optimizer, OS-inspired memory paging, hybrid retrieval).
  - 5 citations pointing to Pages 4, 6, and 7.
- **"what is this research paper includes"**:
  - Returned HTTP `200 OK`.
  - Detailed contents summary (mixed-method research design, structured literature review, prototype implementation, controlled baseline comparison, quantitative and human evaluation).
  - 5 citations pointing to Pages 3, 6, 10, and 13.

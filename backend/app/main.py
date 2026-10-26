from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import documents, search, qa, auth

app = FastAPI(title="DocuMind AI API")


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://documindshreyaai.netlify.app",
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
@app.get("/api/v1/health", tags=["health"])
def health_check():
    return {"status": "healthy"}

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["documents"])
app.include_router(search.router, prefix="/api/v1/search", tags=["search"])
app.include_router(qa.router, prefix="/api/v1/qa", tags=["qa"])



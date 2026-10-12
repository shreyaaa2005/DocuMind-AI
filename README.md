# 🧠 DocuMind AI — Intelligent Document Q&A Using RAG

**Chat with your documents. Get intelligent answers with citations.**

DocuMind AI is an AI-powered document question-answering application that allows users to upload PDF documents, search their contents using semantic search, and ask questions in natural language. It uses **Retrieval-Augmented Generation (RAG)** to generate context-aware answers grounded in uploaded documents, along with relevant citations.

## ✨ Features

- 📄 **PDF Upload:** Upload PDF documents for processing and analysis.
- 🧩 **Automatic Text Extraction:** Extract text from PDF pages.
- 🔍 **Semantic Search:** Find relevant information based on meaning, not just keywords.
- 💬 **AI-Powered Q&A:** Ask questions about uploaded documents in natural language.
- 📚 **Source Citations:** View supporting document references for generated answers.
- 🔐 **Authentication:** Secure user authentication with Supabase.
- 👤 **User Data Isolation:** Keep document retrieval scoped to the authenticated user.
- 🧠 **Vector Embeddings:** Convert document chunks into numerical representations for similarity search.
- 🗃️ **Vector Database:** Store and retrieve embeddings using PostgreSQL with pgvector.
- 🛡️ **Input Protection:** Apply safeguards against prompt injection and unsupported answers.

## 🏗️ System Architecture

```text
              ┌──────────────────────┐
              │   React + TypeScript │
              │      Frontend        │
              └──────────┬───────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │    FastAPI Backend   │
              │ Authentication & API │
              └──────────┬───────────┘
                         │
              ┌──────────┴───────────┐
              ▼                      ▼
     ┌─────────────────┐    ┌─────────────────┐
     │   PDF Processing│    │  Text Chunking  │
     └────────┬────────┘    └────────┬────────┘
              └──────────┬───────────┘
                         ▼
              ┌──────────────────────┐
              │ Sentence Embeddings  │
              │  all-MiniLM-L6-v2    │
              └──────────┬───────────┘
                         ▼
              ┌──────────────────────┐
              │ PostgreSQL + pgvector│
              │  Semantic Retrieval  │
              └──────────┬───────────┘
                         ▼
              ┌──────────────────────┐
              │    LLM + RAG         │
              │ Answers & Citations  │
              └──────────────────────┘
```

## ⚙️ Technology Stack

| Component | Technologies |
|---|---|
| Frontend | React, TypeScript, Vite |
| Backend | Python, FastAPI |
| Authentication | Supabase Auth |
| Database | PostgreSQL, pgvector |
| PDF Processing | PyMuPDF |
| Embeddings | Sentence Transformers, all-MiniLM-L6-v2 |
| AI Answer Generation | Configurable LLM integration |
| Testing | Pytest, Vitest |
| Containerization | Docker, Docker Compose |

## 🔄 How It Works

1. **Upload:** The user uploads a PDF document.
2. **Extract:** The backend extracts text from the PDF.
3. **Chunk:** The extracted text is divided into smaller, overlapping chunks.
4. **Embed:** Each chunk is converted into a vector embedding.
5. **Store:** The chunks and embeddings are stored in PostgreSQL with pgvector.
6. **Retrieve:** When a user asks a question, semantic search retrieves relevant chunks.
7. **Generate:** The LLM generates an answer using the retrieved context.
8. **Cite:** The application presents supporting source references alongside the answer.

## 🚀 Getting Started

### Prerequisites

Install the following tools before starting:

- Python 3.10+
- Node.js and npm
- Docker Desktop
- A Supabase project
- An API key for your configured LLM provider

### 1. Clone the Repository

```bash
git clone https://github.com/shreyaaa2005/DocuMind-AI.git
cd DocuMind-AI
```

### 2. Configure the Backend

Open a terminal in the project root:

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a local `.env` file using `.env.example` as a reference. Configure the required database, Supabase authentication, and LLM settings according to the project's environment configuration.

**Important:** Never commit your `.env` file, API keys, database passwords, or other secrets to GitHub.

### 3. Start the Database

From the project root, run:

```powershell
docker compose up -d
```

Ensure that the PostgreSQL container is healthy and that the backend database settings match your local configuration.

### 4. Run Database Migrations

From the `backend` directory, with the virtual environment activated:

```powershell
alembic upgrade head
```

### 5. Start the Backend

From the `backend` directory:

```powershell
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Backend API: http://127.0.0.1:8000

Interactive API documentation: http://127.0.0.1:8000/docs

### 6. Configure the Frontend

Open a second terminal:

```powershell
cd "put your path eaxt here "
npm install
```

Create the frontend `.env` file using `frontend/.env.example` as a reference. Set the Supabase URL, publishable key, and backend API URL required by the application.

For a local backend, the API URL should point to:

```text
http://localhost:8000/api/v1
```

Use only the Supabase publishable key in frontend configuration. Never expose service-role keys or other server-side secrets.

### 7. Start the Frontend

```powershell
npm run dev
```

Open the local URL displayed in your terminal, usually:

http://localhost:5173

## 🧪 Testing

Run the backend tests from the `backend` directory:

```powershell
pytest
```

Run frontend tests from the `frontend` directory:

```powershell
npm test
```

If the frontend test script differs, check the available scripts in `frontend/package.json`.

## 🔒 Security Considerations

- Authentication tokens are validated by the backend.
- Document access is scoped to the authenticated user.
- File uploads are subject to validation and size limits.
- API keys and credentials must remain outside version control.
- AI-generated answers should be checked against their cited source material.
- Production deployments should configure HTTPS, CORS, persistent document storage, and appropriate database access controls.

## 🛣️ Future Enhancements

- Support for additional document formats.
- Improved handling of scanned PDFs using OCR.
- Conversation history and document collections.
- Advanced retrieval and reranking strategies.
- Streaming AI responses.
- Production deployment with persistent file storage.
- Enhanced evaluation of retrieval quality and answer accuracy.

## 🎯 Project Objective

The objective of DocuMind AI is to make document analysis faster and more accessible by combining semantic search with large language models. Instead of manually searching through lengthy PDFs, users can ask questions and receive context-aware answers with source references.

## 🤝 Contributing

Contributions, suggestions, and bug reports are welcome. Fork the repository, create a feature branch, and submit a pull request.

## 📄 License

Choose and add an appropriate open-source license before distributing the project. Until a license is added, reuse and redistribution permissions are not automatically granted.

---

**Built with ❤️ using AI, RAG, and modern web technologies.**

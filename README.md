# KnowledgeHub

**A retrieval-augmented generation (RAG) API for document ingestion, semantic search and grounded question answering.**

KnowledgeHub turns PDF and TXT files into a searchable knowledge base. It creates overlapping text chunks, generates vector embeddings, stores them in PostgreSQL with pgvector, retrieves relevant passages and uses an LLM to answer questions with source references.

> **Project status:** MVP / portfolio project. Authentication, tenant isolation, background ingestion, hybrid retrieval and reranking are not implemented yet.

## Features

- PDF and TXT ingestion through a REST endpoint
- Text extraction and configurable overlapping chunking
- OpenAI embedding generation
- PostgreSQL persistence with pgvector
- Cosine-similarity retrieval
- Grounded LLM answers with source excerpts and similarity scores
- Interactive OpenAPI documentation
- Docker Compose development environment
- Unit tests for the chunking strategy

## Architecture

```text
                  +--------------------+
                  |       Client       |
                  +---------+----------+
                            |
                            v
                  +--------------------+
                  |     FastAPI        |
                  +--+--------------+--+
                     |              |
          Ingestion  |              |  Question
                     v              v
             +---------------+  +----------------+
             | PDF/TXT parse |  | Query embedding|
             +-------+-------+  +-------+--------+
                     |                  |
                     v                  v
             +---------------+  +----------------+
             | Chunking      |  | Vector search  |
             +-------+-------+  +-------+--------+
                     |                  |
                     v                  v
             +---------------+  +----------------+
             | Embeddings    |->| PostgreSQL     |
             +---------------+  | + pgvector     |
                                +-------+--------+
                                        |
                                        v
                                +----------------+
                                | LLM answer +   |
                                | source refs    |
                                +----------------+
```

## Technology

| Area | Technology |
|---|---|
| API | Python 3.12, FastAPI |
| Validation/config | Pydantic, Pydantic Settings |
| Persistence | PostgreSQL, SQLAlchemy 2 |
| Vector search | pgvector, cosine distance |
| AI | OpenAI embeddings and chat completions |
| Document parsing | pypdf |
| Infrastructure | Docker, Docker Compose |
| Tests/tooling | pytest, Ruff |

## Run locally

### Requirements

- Docker + Docker Compose
- An OpenAI API key

### 1. Clone and configure

```bash
git clone https://github.com/asunavlr/knowledge-hub.git
cd knowledge-hub
cp .env.example .env
```

Add your key to `.env`:

```env
OPENAI_API_KEY=your-api-key
```

### 2. Start the API and database

```bash
docker compose up --build
```

- API: http://localhost:8000
- Swagger UI: http://localhost:8000/docs
- Health check: http://localhost:8000/health

### 3. Run tests locally

Requires Python 3.12+.

```bash
python -m venv .venv
source .venv/bin/activate
# Windows PowerShell: .venv\\Scripts\\Activate.ps1
pip install -e ".[dev]"
pytest
```

## API reference

| Method | Endpoint | Description |
|---|---|---|
| GET | `/health` | Basic service health check |
| POST | `/documents` | Upload and index a PDF or TXT file |
| GET | `/documents` | List indexed documents and chunk counts |
| POST | `/query` | Ask a question and retrieve supporting passages |

### Upload a document

```bash
curl -X POST http://localhost:8000/documents \
  -F "file=@handbook.pdf"
```

### Ask a question

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question":"What is the vacation policy?","top_k":5}'
```

The response contains an answer and a `sources` array with the document ID, filename, chunk ID, similarity score and excerpt for each retrieved passage.

## Configuration

| Variable | Default | Description |
|---|---|---|
| `DATABASE_URL` | local PostgreSQL URL | SQLAlchemy connection string |
| `OPENAI_API_KEY` | empty | Required API key |
| `OPENAI_EMBEDDING_MODEL` | `text-embedding-3-small` | Embedding model |
| `OPENAI_CHAT_MODEL` | `gpt-4o-mini` | Answer generation model |
| `EMBEDDING_DIMENSIONS` | `1536` | Vector size; must match the embedding model output |
| `CHUNK_SIZE` | `1000` | Maximum chunk size in characters |
| `CHUNK_OVERLAP` | `150` | Overlap between chunks |
| `MAX_UPLOAD_BYTES` | `20971520` | Maximum upload size (20 MiB) |
| `DEFAULT_TOP_K` | `5` | Default number of retrieved passages |

## Engineering notes

- Chunk overlap helps preserve context when a relevant passage crosses a chunk boundary.
- The embedding dimension is configured in one place and used by the pgvector column.
- Retrieval results are returned to the caller so generated answers can be inspected.
- Retrieved document text is treated as untrusted context in the generation prompt; it is not allowed to override system instructions.
- The API currently processes ingestion synchronously. Large-scale ingestion should move to a background worker.
- The current schema is single-tenant and has no authentication. Do not expose this MVP publicly with sensitive documents.

## Roadmap

- [ ] Hybrid retrieval: PostgreSQL full-text search + vector similarity
- [ ] Cross-encoder reranking
- [ ] Background ingestion jobs and processing status
- [ ] Authentication, authorization and tenant isolation
- [ ] Document deletion and re-indexing
- [ ] Structured logs, metrics and tracing
- [ ] Retrieval evaluation dataset and regression tests
- [ ] Integration tests with a disposable PostgreSQL/pgvector database

## License

MIT

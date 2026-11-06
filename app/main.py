from contextlib import asynccontextmanager
from io import BytesIO

from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from pypdf import PdfReader
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db import get_db, initialize_database
from app.models import Document, DocumentChunk
from app.schemas import DocumentResponse, QueryRequest, QueryResponse, SourceReference
from app.services.chunking import split_text
from app.services.embeddings import embed_texts, generate_answer
from app.services.retrieval import retrieve_chunks


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database()
    yield


app = FastAPI(
    title="KnowledgeHub API",
    description="Document ingestion and retrieval-augmented question answering.",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
def health():
    return {"status": "ok"}


def extract_text(filename: str, content: bytes) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(BytesIO(content))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    if filename.lower().endswith(".txt"):
        return content.decode("utf-8-sig")
    raise HTTPException(status_code=415, detail="Only PDF and TXT files are supported")


@app.post("/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...), db: Session = Depends(get_db)):
    settings = get_settings()
    content = await file.read(settings.max_upload_bytes + 1)
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File exceeds the upload size limit")

    filename = file.filename or "unnamed"
    try:
        text = extract_text(filename, content)
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="TXT file must be UTF-8 encoded") from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Could not read the uploaded document") from exc

    chunks = split_text(text, settings.chunk_size, settings.chunk_overlap)
    if not chunks:
        raise HTTPException(status_code=422, detail="No extractable text found in document")

    try:
        vectors = embed_texts(chunks)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Embedding provider request failed") from exc

    document = Document(
        filename=filename[:255],
        content_type=file.content_type or "application/octet-stream",
    )
    document.chunks = [
        DocumentChunk(chunk_index=index, content=chunk, embedding=vector)
        for index, (chunk, vector) in enumerate(zip(chunks, vectors, strict=True))
    ]
    db.add(document)
    db.commit()
    db.refresh(document)
    return DocumentResponse(
        id=document.id,
        filename=document.filename,
        content_type=document.content_type,
        created_at=document.created_at,
        chunk_count=len(chunks),
    )


@app.get("/documents", response_model=list[DocumentResponse])
def list_documents(db: Session = Depends(get_db)):
    statement = (
        select(Document, func.count(DocumentChunk.id))
        .outerjoin(DocumentChunk, DocumentChunk.document_id == Document.id)
        .group_by(Document.id)
        .order_by(Document.created_at.desc())
    )
    return [
        DocumentResponse(
            id=document.id,
            filename=document.filename,
            content_type=document.content_type,
            created_at=document.created_at,
            chunk_count=count,
        )
        for document, count in db.execute(statement).all()
    ]


@app.post("/query", response_model=QueryResponse)
def query_knowledge_base(payload: QueryRequest, db: Session = Depends(get_db)):
    settings = get_settings()
    try:
        query_vector = embed_texts([payload.question])[0]
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Embedding provider request failed") from exc

    matches = retrieve_chunks(db, query_vector, payload.top_k or settings.default_top_k)
    if not matches:
        return QueryResponse(
            answer="The knowledge base is empty. Upload a document before asking questions.",
            sources=[],
        )

    contexts = [
        f"[Source {index}] {match['chunk'].content}"
        for index, match in enumerate(matches, start=1)
    ]
    try:
        answer = generate_answer(payload.question, contexts)
    except Exception as exc:
        raise HTTPException(status_code=502, detail="Answer generation provider request failed") from exc

    sources = [
        SourceReference(
            document_id=match["document"].id,
            filename=match["document"].filename,
            chunk_id=match["chunk"].id,
            similarity=round(match["similarity"], 4),
            excerpt=match["chunk"].content[:500],
        )
        for match in matches
    ]
    return QueryResponse(answer=answer, sources=sources)

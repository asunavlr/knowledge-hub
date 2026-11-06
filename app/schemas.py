from datetime import datetime
from pydantic import BaseModel, Field

class DocumentResponse(BaseModel):
    id: int
    filename: str
    content_type: str
    created_at: datetime
    chunk_count: int

class QueryRequest(BaseModel):
    question: str = Field(min_length=3, max_length=4000)
    top_k: int | None = Field(default=None, ge=1, le=20)

class SourceReference(BaseModel):
    document_id: int
    filename: str
    chunk_id: int
    similarity: float
    excerpt: str

class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceReference]

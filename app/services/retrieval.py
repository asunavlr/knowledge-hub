from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models import Document, DocumentChunk

def retrieve_chunks(db: Session, embedding: list[float], top_k: int):
    distance = DocumentChunk.embedding.cosine_distance(embedding)
    statement = (select(DocumentChunk, Document, distance.label("distance"))
                 .join(Document, Document.id == DocumentChunk.document_id)
                 .order_by(distance).limit(top_k))
    return [
        {"chunk": chunk, "document": document,
         "similarity": max(0.0, min(1.0, 1.0 - float(distance_value)))}
        for chunk, document, distance_value in db.execute(statement).all()
    ]

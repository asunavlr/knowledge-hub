import re

def split_text(text: str, chunk_size: int = 1000, overlap: int = 150) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("chunk_size must be greater than zero")
    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be between zero and chunk_size - 1")
    normalized = re.sub(r"\\s+", " ", text).strip()
    if not normalized:
        return []
    chunks: list[str] = []
    start = 0
    while start < len(normalized):
        end = min(start + chunk_size, len(normalized))
        if end < len(normalized):
            boundary = max(normalized.rfind(". ", start, end), normalized.rfind("? ", start, end),
                           normalized.rfind("! ", start, end), normalized.rfind(" ", start, end))
            if boundary > start + chunk_size // 2:
                end = boundary + 1
        chunk = normalized[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(normalized):
            break
        start = max(end - overlap, start + 1)
    return chunks

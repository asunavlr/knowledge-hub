import pytest
from app.services.chunking import split_text

def test_empty_text_returns_no_chunks():
    assert split_text("   ") == []

def test_short_text_returns_one_chunk():
    assert split_text("Hello world", chunk_size=100, overlap=10) == ["Hello world"]

def test_long_text_is_split_with_overlap():
    chunks = split_text("A" * 240, chunk_size=100, overlap=20)
    assert len(chunks) == 3
    assert all(0 < len(chunk) <= 100 for chunk in chunks)
    assert chunks[0][-20:] == chunks[1][:20]

def test_invalid_overlap_is_rejected():
    with pytest.raises(ValueError):
        split_text("hello", chunk_size=10, overlap=10)

def test_invalid_chunk_size_is_rejected():
    with pytest.raises(ValueError):
        split_text("hello", chunk_size=0, overlap=0)

"""
Vector 모듈 - 벡터 검색 및 임베딩

- vector_store: 벡터 저장소 (pgvector 기반)
- text_chunker: 텍스트 청킹

위치: app/core/vector/
"""
from app.core.vector.vector_store import (
    VectorStoreService,
    vector_store,
    get_chunking_settings,
)
from app.core.vector.text_chunker import (
    TextChunk,
    TextChunker,
    default_chunker,
    chunk_text,
)

__all__ = [
    "VectorStoreService",
    "vector_store",
    "get_chunking_settings",
    "TextChunk",
    "TextChunker",
    "default_chunker",
    "chunk_text",
]

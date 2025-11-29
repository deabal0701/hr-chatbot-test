"""텍스트 청킹 유틸리티"""
import hashlib
import re
from dataclasses import dataclass
from typing import List, Optional

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


@dataclass
class TextChunk:
    """청킹된 텍스트 조각"""
    content: str
    chunk_index: int
    start_char: int
    end_char: int


class TextChunker:
    """텍스트를 의미 있는 단위로 분할하는 청커"""

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 100,
        separators: Optional[List[str]] = None
    ):
        """
        Args:
            chunk_size: 청크 크기 (문자 수, 기본 1000자)
            chunk_overlap: 청크 간 중복 (문자 수, 기본 100자)
            separators: 분할 우선순위 구분자 목록
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n",      # 단락 구분
            "\n",        # 줄바꿈
            "。",        # 일본어 마침표
            ".",         # 영어 마침표
            "!",
            "?",
            ";",
            ":",
            " ",         # 공백
            ""           # 문자 단위 (최후 수단)
        ]

    def split_text(self, text: str) -> List[TextChunk]:
        """
        텍스트를 청크로 분할

        Args:
            text: 분할할 텍스트

        Returns:
            TextChunk 객체 리스트
        """
        if not text or not text.strip():
            return []

        # 텍스트 정리
        text = text.strip()

        # 청크 크기보다 작으면 그대로 반환
        if len(text) <= self.chunk_size:
            return [TextChunk(
                content=text,
                chunk_index=0,
                start_char=0,
                end_char=len(text)
            )]

        # 재귀적 분할
        chunks = self._split_recursive(text, self.separators)

        # 청크 병합 (너무 작은 청크들을 합침)
        merged_chunks = self._merge_chunks(chunks)

        # TextChunk 객체로 변환
        result = []
        current_pos = 0
        for idx, chunk_text in enumerate(merged_chunks):
            start = text.find(chunk_text, current_pos)
            if start == -1:
                start = current_pos
            end = start + len(chunk_text)

            result.append(TextChunk(
                content=chunk_text,
                chunk_index=idx,
                start_char=start,
                end_char=end
            ))
            current_pos = end - self.chunk_overlap

        logger.info(f"텍스트 청킹 완료: {len(text)}자 → {len(result)}개 청크")
        return result

    def _split_recursive(self, text: str, separators: List[str]) -> List[str]:
        """재귀적으로 텍스트 분할"""
        if not separators:
            # 구분자가 없으면 강제로 크기대로 자름
            return [text[i:i + self.chunk_size]
                    for i in range(0, len(text), self.chunk_size - self.chunk_overlap)]

        separator = separators[0]
        remaining_separators = separators[1:]

        if separator == "":
            # 빈 구분자면 문자 단위로 분할
            return [text[i:i + self.chunk_size]
                    for i in range(0, len(text), self.chunk_size - self.chunk_overlap)]

        # 현재 구분자로 분할
        if separator in text:
            splits = text.split(separator)
        else:
            # 현재 구분자가 없으면 다음 구분자로
            return self._split_recursive(text, remaining_separators)

        # 분할된 조각들 처리
        chunks = []
        current_chunk = ""

        for i, split in enumerate(splits):
            # 구분자를 다시 붙임 (마지막 제외)
            piece = split + (separator if i < len(splits) - 1 else "")

            # 현재 청크 + 새 조각이 크기 이하면 합침
            if len(current_chunk) + len(piece) <= self.chunk_size:
                current_chunk += piece
            else:
                # 현재 청크 저장
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # 새 조각이 청크 크기보다 크면 재귀 분할
                if len(piece) > self.chunk_size:
                    sub_chunks = self._split_recursive(piece, remaining_separators)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = piece

        # 마지막 청크 저장
        if current_chunk.strip():
            chunks.append(current_chunk.strip())

        return chunks

    def _merge_chunks(self, chunks: List[str]) -> List[str]:
        """너무 작은 청크들을 병합"""
        if not chunks:
            return []

        min_chunk_size = self.chunk_size // 4  # 최소 청크 크기
        merged = []
        current = ""

        for chunk in chunks:
            if not chunk.strip():
                continue

            if len(current) + len(chunk) <= self.chunk_size:
                current += ("\n" if current else "") + chunk
            else:
                if current:
                    merged.append(current)
                current = chunk

        if current:
            # 마지막 청크가 너무 작으면 이전 청크에 합침
            if len(current) < min_chunk_size and merged:
                last = merged.pop()
                if len(last) + len(current) <= self.chunk_size * 1.2:  # 20% 여유
                    merged.append(last + "\n" + current)
                else:
                    merged.append(last)
                    merged.append(current)
            else:
                merged.append(current)

        return merged

    @staticmethod
    def calculate_hash(text: str) -> str:
        """텍스트의 MD5 해시 계산"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()

    def preview_chunks(self, text: str, max_preview_length: int = 100) -> List[dict]:
        """
        청킹 미리보기 (UI용)

        Returns:
            [{"index": 0, "length": 1000, "preview": "첫 100자..."}, ...]
        """
        chunks = self.split_text(text)
        return [
            {
                "index": chunk.chunk_index,
                "length": len(chunk.content),
                "preview": chunk.content[:max_preview_length] + ("..." if len(chunk.content) > max_preview_length else "")
            }
            for chunk in chunks
        ]


# 기본 청커 인스턴스
default_chunker = TextChunker(chunk_size=1000, chunk_overlap=100)


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 100
) -> List[TextChunk]:
    """
    텍스트를 청크로 분할하는 간편 함수

    Args:
        text: 분할할 텍스트
        chunk_size: 청크 크기 (기본 1000자)
        chunk_overlap: 청크 간 중복 (기본 100자)

    Returns:
        TextChunk 리스트
    """
    chunker = TextChunker(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return chunker.split_text(text)

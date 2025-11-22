import re
from typing import List


class TextSplitter:
    """텍스트 청킹 유틸리티"""

    def __init__(
        self,
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        separator: str = "\n"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separator = separator

    def split_text(self, text: str) -> List[str]:
        """텍스트를 청크로 분할"""
        if not text:
            return []

        # 구분자로 먼저 분할
        splits = text.split(self.separator)

        chunks = []
        current_chunk = []
        current_length = 0

        for split in splits:
            split = split.strip()
            if not split:
                continue

            split_length = len(split)

            # 현재 청크에 추가 가능한지 확인
            if current_length + split_length <= self.chunk_size:
                current_chunk.append(split)
                current_length += split_length
            else:
                # 현재 청크 저장
                if current_chunk:
                    chunks.append(self.separator.join(current_chunk))

                # 오버랩 처리
                if self.chunk_overlap > 0 and current_chunk:
                    # 마지막 몇 개 문장을 다음 청크의 시작으로
                    overlap_text = self.separator.join(current_chunk[-2:]) if len(current_chunk) >= 2 else current_chunk[-1]
                    current_chunk = [overlap_text, split]
                    current_length = len(overlap_text) + split_length
                else:
                    current_chunk = [split]
                    current_length = split_length

        # 마지막 청크 추가
        if current_chunk:
            chunks.append(self.separator.join(current_chunk))

        return chunks

    def split_by_sentences(self, text: str) -> List[str]:
        """문장 단위로 텍스트 분할"""
        # 한국어와 영어 문장 구분
        sentence_endings = r'([.!?])\s+'
        sentences = re.split(sentence_endings, text)

        # 구두점과 문장 결합
        result = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                result.append(sentences[i] + sentences[i + 1])
            else:
                result.append(sentences[i])

        return [s.strip() for s in result if s.strip()]


def create_chunks(text: str, chunk_size: int = 500, chunk_overlap: int = 50) -> List[str]:
    """텍스트를 청크로 분할하는 헬퍼 함수"""
    splitter = TextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

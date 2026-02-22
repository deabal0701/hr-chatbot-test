"""파일 텍스트 추출 서비스

PDF, DOCX 파일에서 텍스트를 추출합니다.
추출된 텍스트는 기존 문서 저장 파이프라인(save_document → chunking → embedding)에 합류합니다.

DOCX 추출 범위 (RAG 최적화):
- 본문 단락 및 표 (중첩 표 포함)
- 텍스트박스, 도형 내 텍스트 (XML w:txbxContent 직접 파싱)
- 각주/미주 (정의·부연 설명 포함 가능)
- 헤더/푸터: 제외 (반복 정보 → 임베딩 노이즈 유발)

PDF 추출:
- pdfplumber 기반 텍스트 추출 + 표 추출
"""
from typing import Any, Dict, Tuple

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 허용 파일 확장자
ALLOWED_EXTENSIONS = {".pdf", ".docx"}

# 파일 크기 제한 (50MB)
MAX_FILE_SIZE = 50 * 1024 * 1024

# DOCX XML 네임스페이스 상수
_W_NS = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
_MC_NS = 'http://schemas.openxmlformats.org/markup-compatibility/2006'
_W_P = f'{{{_W_NS}}}p'
_W_T = f'{{{_W_NS}}}t'
_MC_FALLBACK = f'{{{_MC_NS}}}Fallback'


def validate_file(filename: str, file_size: int) -> Tuple[bool, str]:
    """파일 유효성 검증

    Args:
        filename: 업로드된 파일명
        file_size: 파일 크기 (bytes)

    Returns:
        (유효 여부, 오류 메시지)
    """
    if not filename:
        return False, "파일명이 없습니다."

    ext = _get_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return False, f"지원하지 않는 파일 형식입니다. 허용: {allowed}"

    if file_size > MAX_FILE_SIZE:
        max_mb = MAX_FILE_SIZE // (1024 * 1024)
        return False, f"파일 크기가 {max_mb}MB를 초과합니다."

    if file_size == 0:
        return False, "빈 파일입니다."

    return True, ""


def extract_text(filename: str, file_bytes: bytes) -> Dict[str, Any]:
    """파일에서 텍스트 추출

    Args:
        filename: 원본 파일명
        file_bytes: 파일 바이너리 데이터

    Returns:
        {
            "text": 추출된 텍스트,
            "source_type": 파일 타입 (pdf, docx),
            "page_count": 페이지 수 (PDF만),
            "file_size": 파일 크기 (bytes)
        }

    Raises:
        ValueError: 추출 실패 또는 빈 텍스트
    """
    ext = _get_extension(filename)

    if ext == ".pdf":
        return _extract_from_pdf(filename, file_bytes)
    elif ext == ".docx":
        return _extract_from_docx(filename, file_bytes)
    else:
        raise ValueError(f"지원하지 않는 파일 형식: {ext}")


def _extract_from_pdf(filename: str, file_bytes: bytes) -> Dict[str, Any]:
    """PDF에서 텍스트 추출 (텍스트 + 표)"""
    import io
    import pdfplumber

    text_parts = []
    page_count = 0

    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            page_count = len(pdf.pages)
            for page in pdf.pages:
                # 일반 텍스트 추출
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())

                # 표 추출 — extract_text()가 못 잡는 표 데이터 보완
                tables = page.extract_tables()
                for table in tables:
                    for row in table:
                        row_text = " | ".join(cell.strip() for cell in row if cell and cell.strip())
                        if row_text:
                            text_parts.append(row_text)
    except Exception as e:
        logger.error(f"PDF 텍스트 추출 실패: filename={filename}, error={e}")
        raise ValueError(f"PDF 파일을 읽을 수 없습니다: {e}")

    text = "\n\n".join(text_parts).strip()
    if not text:
        raise ValueError("PDF에서 텍스트를 추출할 수 없습니다. 이미지 기반 PDF일 수 있습니다.")

    logger.info(f"PDF 텍스트 추출 완료: filename={filename}, pages={page_count}, chars={len(text)}")

    return {
        "text": text,
        "source_type": "pdf",
        "page_count": page_count,
        "file_size": len(file_bytes),
    }


def _extract_from_docx(filename: str, file_bytes: bytes) -> Dict[str, Any]:
    """DOCX에서 텍스트 추출 (본문, 표, 텍스트박스, 각주 포함 — RAG 최적화)

    python-docx의 doc.paragraphs/doc.tables는 본문 최상위 요소만 반환하므로,
    텍스트박스(w:txbxContent), 도형 내 텍스트 등은 XML을 직접 순회하여 추출합니다.
    mc:Fallback 요소는 mc:Choice와 중복되므로 제외합니다.

    RAG 추출 범위:
    - 본문 단락, 표, 텍스트박스, 도형 내 텍스트: 핵심 콘텐츠 (포함)
    - 각주/미주: 정의·부연 설명이 있을 수 있음 (포함)
    - 헤더/푸터: 문서 제목·페이지 번호 등 반복 정보 → 임베딩 노이즈 유발 (제외)
    """
    import io
    from docx import Document

    text_parts = []

    try:
        doc = Document(io.BytesIO(file_bytes))

        # 1. 본문 전체 — 단락, 표, 텍스트박스, 도형 내 텍스트 모두 포함
        _walk_xml_text(doc.element.body, text_parts)

        # 2. 각주/미주 — 정의·부연 설명 포함 가능
        _extract_notes(doc, text_parts)

        # NOTE: 헤더/푸터는 RAG에 불필요한 반복 정보(제목, 페이지번호)이므로 제외

    except ValueError:
        raise
    except Exception as e:
        logger.error(f"DOCX 텍스트 추출 실패: filename={filename}, error={e}")
        raise ValueError(f"Word 파일을 읽을 수 없습니다: {e}")

    text = "\n\n".join(text_parts).strip()
    if not text:
        raise ValueError("Word 파일에서 텍스트를 추출할 수 없습니다.")

    logger.info(f"DOCX 텍스트 추출 완료: filename={filename}, parts={len(text_parts)}, chars={len(text)}")

    return {
        "text": text,
        "source_type": "docx",
        "page_count": None,
        "file_size": len(file_bytes),
    }


def _walk_xml_text(element, text_parts: list):
    """XML 요소를 재귀 순회하며 모든 w:p 단락의 텍스트를 추출

    mc:Fallback 블록은 mc:Choice와 내용이 중복되므로 건너뜁니다.
    중첩된 w:p(텍스트박스 내부 등)도 재귀적으로 처리합니다.
    """
    for child in element:
        if child.tag == _MC_FALLBACK:
            continue
        if child.tag == _W_P:
            line = _paragraph_direct_text(child)
            if line:
                text_parts.append(line)
            # 단락 내부에 텍스트박스 등 중첩 구조 탐색
            _walk_xml_text(child, text_parts)
        else:
            _walk_xml_text(child, text_parts)


def _paragraph_direct_text(p_elem) -> str:
    """w:p 요소에서 직접 소속된 w:t 텍스트만 추출 (중첩 w:p 내부 텍스트 제외)"""
    texts = []
    _collect_direct_text(p_elem, texts)
    return ''.join(texts).strip()


def _collect_direct_text(elem, texts: list):
    """elem 하위의 w:t 텍스트를 수집하되, 중첩 w:p 경계에서 멈춤"""
    for child in elem:
        if child.tag == _W_P:
            continue  # 중첩 단락은 _walk_xml_text에서 별도 처리
        if child.tag == _W_T:
            if child.text:
                texts.append(child.text)
        else:
            _collect_direct_text(child, texts)


def _extract_notes(doc, text_parts: list):
    """각주(footnotes) 및 미주(endnotes)에서 텍스트 추출"""
    for rel in doc.part.rels.values():
        if 'footnotes' in rel.reltype or 'endnotes' in rel.reltype:
            try:
                _walk_xml_text(rel.target_part.element, text_parts)
            except Exception:
                pass


def _get_extension(filename: str) -> str:
    """파일 확장자 추출 (소문자)"""
    import os
    _, ext = os.path.splitext(filename)
    return ext.lower()

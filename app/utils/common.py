"""공통 유틸리티 함수

비파괴적 확장: 기존 코드에 영향 없이 중복 코드를 통합
"""
import time
import uuid
from typing import Optional


def is_debug_mode() -> bool:
    """
    디버그 모드 여부 확인

    Returns:
        디버그 모드이면 True
    """
    from app.config import settings
    return settings.log_level == "DEBUG"


def truncate_with_omission(text: str, max_length: int = 500) -> str:
    """
    텍스트를 max_length로 자르고 생략 건수를 표시

    디버그 로그의 ANSWER 미리보기용.
    항상 자르기 적용 (force=True 고정).

    Returns:
        잘린 텍스트 + "[이하 N자 생략]" 또는 원본 텍스트
    """
    if not text or len(text) <= max_length:
        return text
    omitted = len(text) - max_length
    return f"{text[:max_length]}\n... [이하 {omitted}자 생략]"


def truncate_text(text: str, max_length: int = 100, force: bool = False) -> str:
    """
    텍스트 자르기 (공통 유틸리티)

    디버그 모드(LOG_LEVEL=DEBUG)에서는 전체 텍스트 반환

    Args:
        text: 자를 텍스트
        max_length: 최대 길이 (기본 100자)
        force: True이면 디버그 모드에서도 자르기 적용

    Returns:
        잘린 텍스트 (디버그 모드에서는 전체)
    """
    if not text:
        return text

    # 디버그 모드에서는 전체 텍스트 반환 (force=False일 때)
    if not force and is_debug_mode():
        return text

    if len(text) <= max_length:
        return text
    return text[:max_length] + "..."


def generate_request_id() -> str:
    """
    요청 ID 생성 (8자리 UUID)
    
    Returns:
        요청 ID (예: "a1b2c3d4")
    """
    return str(uuid.uuid4())[:8]


def format_execution_time(start_time: float) -> int:
    """
    실행 시간 계산 (밀리초)
    
    Args:
        start_time: 시작 시간 (time.time())
    
    Returns:
        실행 시간 (ms)
    """
    return int((time.time() - start_time) * 1000)


def safe_get_dict_value(data: dict, *keys, default=None):
    """
    중첩된 딕셔너리에서 안전하게 값 가져오기
    
    Args:
        data: 딕셔너리
        *keys: 키 경로 (예: 'a', 'b', 'c' → data['a']['b']['c'])
        default: 기본값
    
    Returns:
        값 또는 기본값
    
    Example:
        >>> data = {'a': {'b': {'c': 123}}}
        >>> safe_get_dict_value(data, 'a', 'b', 'c')
        123
        >>> safe_get_dict_value(data, 'x', 'y', default='N/A')
        'N/A'
    """
    try:
        result = data
        for key in keys:
            result = result[key]
        return result
    except (KeyError, TypeError, AttributeError):
        return default


def extract_llm_text_content(content) -> str:
    """
    LLM 응답 content에서 텍스트 추출 (다중 제공자 호환)

    OpenAI: content가 str로 반환
    Anthropic: content가 str 또는 list[ContentBlock]로 반환
    Google Gemini: content가 list[dict] 형태로 반환 (예: [{'type': 'text', 'text': '...', 'extras': {...}}])

    Args:
        content: LLM response.content

    Returns:
        추출된 텍스트 문자열
    """
    if content is None:
        return ""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and "text" in item:
                parts.append(item["text"])
            elif hasattr(item, "text"):
                parts.append(item.text)
            else:
                parts.append(str(item))
        return " ".join(parts).strip()
    return str(content).strip()


def strip_markdown_code_block(text: str, language: str = "sql") -> str:
    """
    마크다운 코드 블록 제거

    LLM이 SQL이나 코드를 ```sql ... ``` 형태로 반환할 때 사용

    Args:
        text: 원본 텍스트 (마크다운 코드 블록 포함 가능)
        language: 코드 언어 (기본: "sql")

    Returns:
        코드 블록이 제거된 순수 텍스트

    Example:
        >>> text = "```sql\\nSELECT * FROM users\\n```"
        >>> strip_markdown_code_block(text)
        'SELECT * FROM users'
    """
    if not text:
        return text

    text = text.strip()

    # ```로 시작하는 경우 마크다운 코드 블록으로 판단
    if text.startswith("```"):
        lines = text.split("\n")
        # 첫 줄과 마지막 줄 제거
        if len(lines) > 2:
            text = "\n".join(lines[1:-1])
        else:
            text = text  # 코드 블록이 비정상적인 경우 원본 유지

        # 언어 지정자 제거 (예: ```sql, ```python)
        text = text.replace(f"```{language}", "").replace("```", "").strip()

    return text


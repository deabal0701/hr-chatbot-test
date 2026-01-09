"""공통 유틸리티 함수
 
비파괴적 확장: 기존 코드에 영향 없이 중복 코드를 통합
"""
import time
import uuid
from typing import Optional


def truncate_text(text: str, max_length: int = 100) -> str:
    """
    텍스트 자르기 (공통 유틸리티)
    
    Args:
        text: 자를 텍스트
        max_length: 최대 길이 (기본 100자)
    
    Returns:
        잘린 텍스트
    """
    if not text or len(text) <= max_length:
        return text
    return text[:max_length] + "...[truncated]"


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


def format_number_with_commas(number: int) -> str:
    """
    숫자를 천 단위 구분자로 포맷
    
    Args:
        number: 정수
    
    Returns:
        포맷된 문자열 (예: 1000 → "1,000")
    """
    return f"{number:,}"


def sanitize_sql_identifier(identifier: str) -> str:
    """
    SQL 식별자(테이블명, 컬럼명) 검증 및 정리
    
    Args:
        identifier: SQL 식별자
    
    Returns:
        정리된 식별자
    
    Raises:
        ValueError: 유효하지 않은 식별자
    """
    import re
    
    # 알파벳, 숫자, 언더스코어만 허용
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        raise ValueError(f"유효하지 않은 SQL 식별자: {identifier}")
    
    return identifier.lower()


def mask_sensitive_data(text: str, keywords: Optional[list] = None) -> str:
    """
    민감 데이터 마스킹
    
    Args:
        text: 원본 텍스트
        keywords: 마스킹할 키워드 리스트 (기본: ['password', 'api_key', 'secret'])
    
    Returns:
        마스킹된 텍스트
    """
    if not text:
        return text
    
    if keywords is None:
        keywords = ['password', 'api_key', 'secret', 'token', 'key']
    
    import re
    
    masked_text = text
    for keyword in keywords:
        # 대소문자 구분 없이 키워드 찾기
        # f-string 내부에서 }를 사용하려면 }}로 이스케이프
        pattern = re.compile(rf'({keyword}["\']?\s*[:=]\s*["\']?)([^"\'}}\s,]+)', re.IGNORECASE)
        masked_text = pattern.sub(r'\1***MASKED***', masked_text)
    
    return masked_text


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


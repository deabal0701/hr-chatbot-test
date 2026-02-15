"""
응답 유틸리티

위치: app/core/errors/response.py
- success_response: 성공 응답 생성
- error_response: 에러 응답 생성
- raise_on_unique_violation: 유니크 제약조건 위반 처리
"""
from typing import Any, Optional

from app.core.errors.error_codes import ErrorCode, ERROR_MESSAGES


def success_response(data: Any) -> dict:
    """
    성공 응답 생성

    Args:
        data: 응답 데이터 (dict, Pydantic 모델, 리스트 등)

    Returns:
        {
            "success": True,
            "data": data,
            "error": None
        }

    사용법:
        return success_response({"query": "...", "answer": "..."})
        return success_response(search_response.model_dump())
    """
    # Pydantic 모델인 경우 dict로 변환
    if hasattr(data, "model_dump"):
        data = data.model_dump()

    return {
        "success": True,
        "data": data,
        "error": None
    }


def error_response(
    error_code: ErrorCode,
    message: Optional[str] = None,
    detail: Optional[str] = None
) -> dict:
    """
    에러 응답 생성

    Args:
        error_code: 에러 코드 (ErrorCode enum)
        message: 사용자 메시지 (None이면 기본 메시지 사용)
        detail: 개발자용 상세 정보

    Returns:
        {
            "success": False,
            "data": None,
            "error": {
                "code": "ERROR_CODE",
                "message": "메시지",
                "detail": "상세"
            }
        }

    사용법:
        return error_response(ErrorCode.SEARCH_FAILED)
        return error_response(ErrorCode.VALIDATION_ERROR, detail=str(e))
    """
    return {
        "success": False,
        "data": None,
        "error": {
            "code": error_code.value,
            "message": message or ERROR_MESSAGES.get(error_code, "오류가 발생했습니다"),
            "detail": detail
        }
    }


def raise_on_unique_violation(e: Exception, message: str) -> None:
    """유니크 제약조건 위반 시 DUPLICATE_ERROR로 변환, 아니면 원래 예외 전파

    사용법:
        try:
            cur.execute("INSERT ...")
        except Exception as e:
            raise_on_unique_violation(e, "이미 존재하는 데이터입니다")
    """
    from app.core.errors.handlers import APIException

    if "unique" in str(e).lower() or "duplicate" in str(e).lower():
        raise APIException(ErrorCode.DUPLICATE_ERROR, message) from e
    raise e

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


def get_user_friendly_error(error_str: str) -> str:
    """기술적 에러 메시지를 사용자 친화적 메시지로 변환

    DB 연결 오류, 타임아웃 등 기술적 에러를 사용자가 이해할 수 있는
    안내 메시지로 변환합니다. 매칭되지 않으면 일반 오류 메시지를 반환합니다.
    """
    error_lower = error_str.lower()

    # DB 연결 끊김/실패 (Oracle DPY 에러 계열)
    if any(kw in error_lower for kw in ["dpy-4011", "dpy-6005", "dpy-6000", "database or network closed", "cannot connect to database"]):
        return "데이터베이스 연결이 일시적으로 불안정합니다. 잠시 후 다시 시도해 주세요."

    # DB 연결 실패 / 리스너 오류
    if any(kw in error_lower for kw in ["connection refused", "could not connect", "연결 실패", "connectionerror", "listener refused", "ora-12528", "ora-12541", "no listener", "데이터베이스 연결 오류"]):
        return "데이터베이스 연결이 일시적으로 불안정합니다. 잠시 후 다시 시도해 주세요."

    # Oracle 인증 오류
    if "ora-01017" in error_lower or "invalid username/password" in error_lower:
        return "데이터베이스 인증에 실패했습니다. 관리자에게 문의해 주세요."

    # 타임아웃
    if any(kw in error_lower for kw in ["timeout", "timed out", "시간 초과"]):
        return "요청 처리 시간이 초과되었습니다. 질문을 간단히 수정하여 다시 시도해 주세요."

    # LLM API 오류
    if any(kw in error_lower for kw in ["rate limit", "429", "quota"]):
        return "AI 서비스가 일시적으로 사용량 제한에 도달했습니다. 잠시 후 다시 시도해 주세요."

    if any(kw in error_lower for kw in ["api key", "authentication", "unauthorized", "401"]):
        return "AI 서비스 인증에 문제가 발생했습니다. 관리자에게 문의해 주세요."

    # 일반 오류 (기술적 상세 노출 방지)
    return "요청을 처리하는 중 문제가 발생했습니다. 잠시 후 다시 시도해 주세요."


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

"""
전역 예외 핸들러

위치: app/core/errors/handlers.py
- APIException: 커스텀 API 예외
- register_exception_handlers: FastAPI 예외 핸들러 등록
"""
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.errors.error_codes import ErrorCode, ERROR_MESSAGES, ERROR_STATUS_CODES
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class APIException(Exception):
    """
    커스텀 API 예외

    사용법:
        raise APIException(
            error_code=ErrorCode.SEARCH_FAILED,
            message="검색 실패",  # 선택: 커스텀 메시지
            detail="원본 에러 메시지"  # 선택: 개발자용 상세 정보
        )
    """

    def __init__(
        self,
        error_code: ErrorCode,
        message: str = None,
        detail: str = None
    ):
        self.error_code = error_code
        self.message = message or ERROR_MESSAGES.get(error_code, "오류가 발생했습니다")
        self.detail = detail
        self.status_code = ERROR_STATUS_CODES.get(error_code, 500)
        super().__init__(self.message)


def register_exception_handlers(app: FastAPI):
    """
    전역 예외 핸들러 등록

    모든 예외를 통일된 응답 형식으로 변환:
    {
        "success": false,
        "data": null,
        "error": {
            "code": "ERROR_CODE",
            "message": "사용자 메시지",
            "detail": "개발자용 상세 (선택)"
        }
    }
    """

    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
        """커스텀 APIException 처리"""
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(f"[{request_id}] APIException: {exc.error_code.value} - {exc.message}")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": exc.error_code.value,
                    "message": exc.message,
                    "detail": exc.detail
                }
            }
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """기존 HTTPException을 새 형식으로 변환"""
        request_id = getattr(request.state, "request_id", "unknown")
        error_code = _map_status_to_error_code(exc.status_code)

        logger.warning(f"[{request_id}] HTTPException: {exc.status_code} - {exc.detail}")

        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": error_code,
                    "message": _get_user_message(error_code, exc.detail),
                    "detail": str(exc.detail) if exc.detail else None
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Pydantic 검증 에러 처리"""
        request_id = getattr(request.state, "request_id", "unknown")
        logger.warning(f"[{request_id}] ValidationError: {exc.errors()}")

        # 검증 에러 메시지를 사용자 친화적으로 변환
        error_details = []
        user_messages = []
        for error in exc.errors():
            loc = " -> ".join(str(l) for l in error.get("loc", []))
            msg = error.get("msg", "")
            error_details.append(f"{loc}: {msg}")
            # field_validator의 한국어 메시지 추출 (Value error, 메시지)
            if msg.startswith("Value error, "):
                user_messages.append(msg.replace("Value error, ", "", 1))

        message = "; ".join(user_messages) if user_messages else "입력값이 올바르지 않습니다"

        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": ErrorCode.VALIDATION_ERROR.value,
                    "message": message,
                    "detail": "; ".join(error_details)
                }
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        """예상치 못한 에러 처리"""
        request_id = getattr(request.state, "request_id", "unknown")
        logger.error(f"[{request_id}] UnhandledException: {type(exc).__name__} - {exc}", exc_info=True)

        # 프로덕션에서는 상세 에러 숨김
        from app.config import settings
        show_detail = settings.app_env == "development"

        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR.value,
                    "message": "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요",
                    "detail": str(exc) if show_detail else None
                }
            }
        )


def _map_status_to_error_code(status_code: int) -> str:
    """HTTP 상태 코드를 에러 코드로 매핑"""
    mapping = {
        400: ErrorCode.BAD_REQUEST.value,
        401: ErrorCode.UNAUTHORIZED.value,
        403: ErrorCode.FORBIDDEN.value,
        404: ErrorCode.NOT_FOUND.value,
        409: ErrorCode.DUPLICATE_ERROR.value,
        410: ErrorCode.SESSION_EXPIRED.value,
        500: ErrorCode.INTERNAL_ERROR.value,
        502: ErrorCode.EXTERNAL_API_ERROR.value,
        504: ErrorCode.TIMEOUT_ERROR.value,
    }
    return mapping.get(status_code, ErrorCode.INTERNAL_ERROR.value)


def _get_user_message(error_code: str, detail: str = None) -> str:
    """에러 코드에 해당하는 사용자 메시지 반환"""
    try:
        code = ErrorCode(error_code)
        return ERROR_MESSAGES.get(code, str(detail) if detail else "오류가 발생했습니다")
    except ValueError:
        return str(detail) if detail else "오류가 발생했습니다"

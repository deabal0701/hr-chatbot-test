"""
API 에러 코드 정의

위치: app/core/errors/error_codes.py
- ErrorCode: 에러 코드 Enum
- ERROR_MESSAGES: 에러 코드별 사용자 메시지
- ERROR_STATUS_CODES: 에러 코드별 HTTP 상태 코드
"""
from enum import Enum
from fastapi import status


class ErrorCode(str, Enum):
    """API 에러 코드"""

    # ========== 클라이언트 오류 (4xx) ==========
    VALIDATION_ERROR = "VALIDATION_ERROR"        # 입력값 검증 실패
    NOT_FOUND = "NOT_FOUND"                      # 리소스 없음
    UNAUTHORIZED = "UNAUTHORIZED"                # 인증 필요
    FORBIDDEN = "FORBIDDEN"                      # 권한 없음
    BAD_REQUEST = "BAD_REQUEST"                  # 잘못된 요청

    # ========== 비즈니스 오류 ==========
    SEARCH_FAILED = "SEARCH_FAILED"              # 검색 실패
    SQL_GENERATION_FAILED = "SQL_GENERATION_FAILED"  # SQL 생성 실패
    SQL_EXECUTION_FAILED = "SQL_EXECUTION_FAILED"    # SQL 실행 실패
    DOCUMENT_NOT_FOUND = "DOCUMENT_NOT_FOUND"    # 문서 없음
    EMBEDDING_FAILED = "EMBEDDING_FAILED"        # 임베딩 실패
    AGENT_FAILED = "AGENT_FAILED"                # Agent 실행 실패
    SESSION_NOT_FOUND = "SESSION_NOT_FOUND"      # 세션 없음
    SESSION_EXPIRED = "SESSION_EXPIRED"          # 세션 만료
    ACCOUNT_LOCKED = "ACCOUNT_LOCKED"            # 계정 잠금
    RATE_LIMIT_EXCEEDED = "RATE_LIMIT_EXCEEDED"  # 요청 횟수 초과
    SETTING_NOT_FOUND = "SETTING_NOT_FOUND"      # 설정 없음
    CODE_NOT_FOUND = "CODE_NOT_FOUND"            # 코드 없음
    DUPLICATE_ERROR = "DUPLICATE_ERROR"          # 중복 오류

    # ========== 서버 오류 (5xx) ==========
    INTERNAL_ERROR = "INTERNAL_ERROR"            # 내부 서버 오류
    DATABASE_ERROR = "DATABASE_ERROR"            # 데이터베이스 오류
    LLM_ERROR = "LLM_ERROR"                      # LLM API 오류
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"    # 외부 API 오류
    TIMEOUT_ERROR = "TIMEOUT_ERROR"              # 타임아웃


# 에러 코드별 사용자 친화적 메시지
ERROR_MESSAGES: dict[ErrorCode, str] = {
    # 클라이언트 오류
    ErrorCode.VALIDATION_ERROR: "입력값이 올바르지 않습니다",
    ErrorCode.NOT_FOUND: "요청한 리소스를 찾을 수 없습니다",
    ErrorCode.UNAUTHORIZED: "인증이 필요합니다",
    ErrorCode.FORBIDDEN: "접근 권한이 없습니다",
    ErrorCode.BAD_REQUEST: "잘못된 요청입니다",

    # 비즈니스 오류
    ErrorCode.SEARCH_FAILED: "검색에 실패했습니다. 다시 시도해주세요",
    ErrorCode.SQL_GENERATION_FAILED: "질문을 SQL로 변환하지 못했습니다. 다른 표현으로 시도해주세요",
    ErrorCode.SQL_EXECUTION_FAILED: "데이터 조회에 실패했습니다",
    ErrorCode.DOCUMENT_NOT_FOUND: "문서를 찾을 수 없습니다",
    ErrorCode.EMBEDDING_FAILED: "문서 인덱싱에 실패했습니다",
    ErrorCode.AGENT_FAILED: "AI Agent 처리에 실패했습니다",
    ErrorCode.SESSION_NOT_FOUND: "세션을 찾을 수 없습니다",
    ErrorCode.SESSION_EXPIRED: "세션이 만료되었습니다. 새로운 대화를 시작해주세요",
    ErrorCode.ACCOUNT_LOCKED: "계정이 잠겼습니다. 잠시 후 다시 시도해주세요",
    ErrorCode.RATE_LIMIT_EXCEEDED: "요청이 너무 많습니다. 잠시 후 다시 시도해주세요",
    ErrorCode.SETTING_NOT_FOUND: "설정을 찾을 수 없습니다",
    ErrorCode.CODE_NOT_FOUND: "코드를 찾을 수 없습니다",
    ErrorCode.DUPLICATE_ERROR: "이미 존재하는 데이터입니다",

    # 서버 오류
    ErrorCode.INTERNAL_ERROR: "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요",
    ErrorCode.DATABASE_ERROR: "데이터베이스 연결에 문제가 있습니다",
    ErrorCode.LLM_ERROR: "AI 서비스에 일시적인 문제가 있습니다",
    ErrorCode.EXTERNAL_API_ERROR: "외부 서비스 연결에 문제가 있습니다",
    ErrorCode.TIMEOUT_ERROR: "처리 시간이 초과되었습니다. 질문을 간단하게 다시 시도해주세요",
}


# 에러 코드별 HTTP 상태 코드 매핑
ERROR_STATUS_CODES: dict[ErrorCode, int] = {
    # 4xx
    ErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
    ErrorCode.BAD_REQUEST: status.HTTP_400_BAD_REQUEST,
    ErrorCode.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.FORBIDDEN: status.HTTP_403_FORBIDDEN,
    ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.DOCUMENT_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.SESSION_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.SETTING_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.CODE_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.DUPLICATE_ERROR: status.HTTP_409_CONFLICT,
    ErrorCode.SESSION_EXPIRED: status.HTTP_410_GONE,
    ErrorCode.ACCOUNT_LOCKED: status.HTTP_423_LOCKED,
    ErrorCode.RATE_LIMIT_EXCEEDED: status.HTTP_429_TOO_MANY_REQUESTS,

    # 5xx
    ErrorCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.DATABASE_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.SEARCH_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.SQL_GENERATION_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.SQL_EXECUTION_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.EMBEDDING_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.AGENT_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.LLM_ERROR: status.HTTP_502_BAD_GATEWAY,
    ErrorCode.EXTERNAL_API_ERROR: status.HTTP_502_BAD_GATEWAY,
    ErrorCode.TIMEOUT_ERROR: status.HTTP_504_GATEWAY_TIMEOUT,
}

# API 응답 표준화 설계서

## 1. 개요

### 1.1 목적
- 모든 API 응답을 일관된 구조로 통일
- 에러 코드 체계 도입으로 사용자 친화적 오류 메시지 제공
- 프론트엔드에서 일관된 응답 처리 가능

### 1.2 설계 원칙
| 요소 | 방식 |
|------|------|
| 성공/실패 판단 | HTTP 상태 코드 (1차) + `success` 필드 (2차) |
| 응답 구조 | `{success, data, error}` 통일 |
| 에러 코드 | 문자열 코드 (가독성 우선) |
| 에러 메시지 | 사용자 친화적 메시지 |

---

## 2. 응답 구조 설계

### 2.1 성공 응답 (HTTP 2xx)
```json
{
  "success": true,
  "data": {
    // 기존 응답 데이터 (SearchResponse, AgentResponse 등)
  },
  "error": null
}
```

### 2.2 실패 응답 (HTTP 4xx/5xx)
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "검색어를 입력해주세요",
    "detail": "query field is required"  // 개발자용 (선택)
  }
}
```

### 2.3 Pydantic 모델 설계

```python
# app/models/common.py

from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel, Field

T = TypeVar('T')

class ErrorDetail(BaseModel):
    """에러 상세 정보"""
    code: str = Field(..., description="에러 코드 (VALIDATION_ERROR, NOT_FOUND 등)")
    message: str = Field(..., description="사용자 친화적 에러 메시지")
    detail: Optional[str] = Field(None, description="개발자용 상세 정보")

class APIResponse(BaseModel, Generic[T]):
    """통일된 API 응답 래퍼"""
    success: bool = Field(..., description="성공 여부")
    data: Optional[T] = Field(None, description="응답 데이터")
    error: Optional[ErrorDetail] = Field(None, description="에러 정보")

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "success": True,
                    "data": {"query": "...", "answer": "..."},
                    "error": None
                },
                {
                    "success": False,
                    "data": None,
                    "error": {
                        "code": "VALIDATION_ERROR",
                        "message": "검색어를 입력해주세요"
                    }
                }
            ]
        }
    }
```

---

## 3. 에러 코드 체계

### 3.1 에러 코드 정의

```python
# app/core/errors/error_codes.py

from enum import Enum

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

    # ========== 서버 오류 (5xx) ==========
    INTERNAL_ERROR = "INTERNAL_ERROR"            # 내부 서버 오류
    DATABASE_ERROR = "DATABASE_ERROR"            # 데이터베이스 오류
    LLM_ERROR = "LLM_ERROR"                      # LLM API 오류
    EXTERNAL_API_ERROR = "EXTERNAL_API_ERROR"    # 외부 API 오류
    TIMEOUT_ERROR = "TIMEOUT_ERROR"              # 타임아웃


# 에러 코드별 사용자 메시지 매핑
ERROR_MESSAGES = {
    ErrorCode.VALIDATION_ERROR: "입력값이 올바르지 않습니다",
    ErrorCode.NOT_FOUND: "요청한 리소스를 찾을 수 없습니다",
    ErrorCode.UNAUTHORIZED: "인증이 필요합니다",
    ErrorCode.FORBIDDEN: "접근 권한이 없습니다",
    ErrorCode.BAD_REQUEST: "잘못된 요청입니다",

    ErrorCode.SEARCH_FAILED: "검색에 실패했습니다. 다시 시도해주세요",
    ErrorCode.SQL_GENERATION_FAILED: "질문을 SQL로 변환하지 못했습니다. 다른 표현으로 시도해주세요",
    ErrorCode.SQL_EXECUTION_FAILED: "데이터 조회에 실패했습니다",
    ErrorCode.DOCUMENT_NOT_FOUND: "문서를 찾을 수 없습니다",
    ErrorCode.EMBEDDING_FAILED: "문서 인덱싱에 실패했습니다",
    ErrorCode.AGENT_FAILED: "AI Agent 처리에 실패했습니다",
    ErrorCode.SESSION_NOT_FOUND: "세션을 찾을 수 없습니다",
    ErrorCode.SESSION_EXPIRED: "세션이 만료되었습니다. 새로운 대화를 시작해주세요",

    ErrorCode.INTERNAL_ERROR: "서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요",
    ErrorCode.DATABASE_ERROR: "데이터베이스 연결에 문제가 있습니다",
    ErrorCode.LLM_ERROR: "AI 서비스에 일시적인 문제가 있습니다",
    ErrorCode.EXTERNAL_API_ERROR: "외부 서비스 연결에 문제가 있습니다",
    ErrorCode.TIMEOUT_ERROR: "처리 시간이 초과되었습니다. 질문을 간단하게 다시 시도해주세요",
}
```

### 3.2 에러 코드 - HTTP 상태 코드 매핑

```python
# app/core/errors/error_codes.py (계속)

from fastapi import status

ERROR_STATUS_CODES = {
    # 4xx
    ErrorCode.VALIDATION_ERROR: status.HTTP_400_BAD_REQUEST,
    ErrorCode.BAD_REQUEST: status.HTTP_400_BAD_REQUEST,
    ErrorCode.UNAUTHORIZED: status.HTTP_401_UNAUTHORIZED,
    ErrorCode.FORBIDDEN: status.HTTP_403_FORBIDDEN,
    ErrorCode.NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.DOCUMENT_NOT_FOUND: status.HTTP_404_NOT_FOUND,
    ErrorCode.SESSION_NOT_FOUND: status.HTTP_404_NOT_FOUND,

    # 5xx
    ErrorCode.INTERNAL_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.DATABASE_ERROR: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.LLM_ERROR: status.HTTP_502_BAD_GATEWAY,
    ErrorCode.EXTERNAL_API_ERROR: status.HTTP_502_BAD_GATEWAY,
    ErrorCode.TIMEOUT_ERROR: status.HTTP_504_GATEWAY_TIMEOUT,
    ErrorCode.SEARCH_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.SQL_GENERATION_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.SQL_EXECUTION_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.EMBEDDING_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.AGENT_FAILED: status.HTTP_500_INTERNAL_SERVER_ERROR,
    ErrorCode.SESSION_EXPIRED: status.HTTP_410_GONE,
}
```

---

## 4. 구현 방식

### 4.1 방식 비교

| 방식 | 장점 | 단점 |
|------|------|------|
| **미들웨어** | 기존 코드 변경 최소화, 일괄 적용 | 복잡한 응답 변환, 디버깅 어려움 |
| **명시적 래핑** | 타입 안전, 명확한 API 계약 | 모든 엔드포인트 수정 필요 |
| **하이브리드** | 점진적 마이그레이션 가능 | 일시적 비일관성 |

### 4.2 권장: 하이브리드 방식 (예외 핸들러 + 점진적 명시적 래핑)

**1단계**: 전역 예외 핸들러로 에러 응답 통일
**2단계**: 주요 엔드포인트부터 점진적으로 성공 응답 래핑
**3단계**: 전체 엔드포인트 마이그레이션 완료

---

## 5. 구현 상세

### 5.1 전역 예외 핸들러

```python
# app/core/errors/handlers.py

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.models.common import APIResponse, ErrorDetail
from app.core.errors.error_codes import ErrorCode, ERROR_MESSAGES, ERROR_STATUS_CODES


class APIException(Exception):
    """커스텀 API 예외"""
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


def register_exception_handlers(app: FastAPI):
    """전역 예외 핸들러 등록"""

    @app.exception_handler(APIException)
    async def api_exception_handler(request: Request, exc: APIException):
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
        # 기존 HTTPException을 새 형식으로 변환
        error_code = _map_status_to_error_code(exc.status_code)
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": error_code,
                    "message": ERROR_MESSAGES.get(ErrorCode(error_code), str(exc.detail)),
                    "detail": str(exc.detail) if exc.detail else None
                }
            }
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": ErrorCode.VALIDATION_ERROR.value,
                    "message": "입력값이 올바르지 않습니다",
                    "detail": str(exc.errors())
                }
            }
        )

    @app.exception_handler(Exception)
    async def general_exception_handler(request: Request, exc: Exception):
        # 예상치 못한 에러
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "data": None,
                "error": {
                    "code": ErrorCode.INTERNAL_ERROR.value,
                    "message": "서버 오류가 발생했습니다",
                    "detail": str(exc) if app.debug else None
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
        500: ErrorCode.INTERNAL_ERROR.value,
        502: ErrorCode.EXTERNAL_API_ERROR.value,
        504: ErrorCode.TIMEOUT_ERROR.value,
    }
    return mapping.get(status_code, ErrorCode.INTERNAL_ERROR.value)
```

### 5.2 응답 래퍼 유틸리티

```python
# app/core/errors/response.py

from typing import TypeVar, Any
from app.models.common import APIResponse, ErrorDetail
from app.core.errors.error_codes import ErrorCode, ERROR_MESSAGES

T = TypeVar('T')

def success_response(data: Any) -> dict:
    """성공 응답 생성"""
    return {
        "success": True,
        "data": data,
        "error": None
    }

def error_response(
    error_code: ErrorCode,
    message: str = None,
    detail: str = None
) -> dict:
    """에러 응답 생성"""
    return {
        "success": False,
        "data": None,
        "error": {
            "code": error_code.value,
            "message": message or ERROR_MESSAGES.get(error_code),
            "detail": detail
        }
    }
```

### 5.3 라우트 적용 예시

```python
# app/api/routes/search.py (변경 후)

from app.core.errors.error_codes import ErrorCode
from app.core.errors.handlers import APIException
from app.core.errors.response import success_response

@router.post("/search")
async def search(search_request: SearchRequest, request: Request):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4())[:8])

    try:
        # 기존 로직...
        response = await nl2sql_service.search(...)

        # 성공 응답 래핑
        return success_response(response.model_dump())

    except Exception as e:
        logger.error(f"[{request_id}] 검색 실패: {e}", exc_info=True)
        raise APIException(
            error_code=ErrorCode.SEARCH_FAILED,
            detail=str(e)
        )
```

---

## 6. 프론트엔드 수정

### 6.1 axios 인터셉터 수정

```javascript
// frontend/src/api/index.js

apiClient.interceptors.response.use(
  (response) => {
    const result = response.data

    // 새 응답 형식: {success, data, error}
    if (result.success !== undefined) {
      if (result.success) {
        return result.data  // 기존 코드 호환성 유지
      }
      // success: false인 경우 에러 throw
      const error = new Error(result.error?.message || '오류가 발생했습니다')
      error.code = result.error?.code
      error.detail = result.error?.detail
      return Promise.reject(error)
    }

    // 레거시 응답 (마이그레이션 기간 동안 호환)
    return result
  },
  (error) => {
    // HTTP 에러 처리
    const errorData = error.response?.data

    // 새 형식의 에러 응답
    if (errorData?.error) {
      const customError = new Error(errorData.error.message || '오류가 발생했습니다')
      customError.code = errorData.error.code
      customError.detail = errorData.error.detail
      return Promise.reject(customError)
    }

    // 레거시 형식 (detail 필드)
    if (errorData?.detail) {
      error.message = errorData.detail
    }

    return Promise.reject(error)
  }
)
```

### 6.2 Store 에러 처리 수정

```javascript
// frontend/src/store/modules/chat.js (변경 부분)

catch (error) {
  // 새 형식: error.code, error.message 사용
  const errorCode = error.code || 'UNKNOWN_ERROR'
  const errorMessage = error.message || '검색 중 오류가 발생했습니다.'

  commit('SET_ERROR', { code: errorCode, message: errorMessage })

  commit('ADD_MESSAGE', {
    role: 'assistant',
    content: `죄송합니다. ${errorMessage}`,
    isError: true,
    errorCode: errorCode
  })
}
```

---

## 7. 영향도 분석

### 7.1 수정 파일 목록

#### 백엔드 (신규 생성)
| 파일 | 설명 |
|------|------|
| `app/core/errors/__init__.py` | 에러 모듈 |
| `app/core/errors/error_codes.py` | 에러 코드 정의 |
| `app/core/errors/handlers.py` | 전역 예외 핸들러 |
| `app/core/errors/response.py` | 응답 유틸리티 |

#### 백엔드 (수정)
| 파일 | 수정 내용 | 영향도 |
|------|----------|--------|
| `app/models/common.py` | APIResponse, ErrorDetail 추가 | 낮음 |
| `app/main.py` | 예외 핸들러 등록 | 낮음 |
| `app/api/routes/search.py` | 응답 래핑, APIException 사용 | 중간 |
| `app/api/routes/agent.py` | 응답 래핑, APIException 사용 | 중간 |
| `app/api/routes/documents.py` | 응답 래핑, APIException 사용 | 중간 |
| `app/api/routes/settings.py` | 응답 래핑, APIException 사용 | 중간 |
| `app/api/routes/codes.py` | 응답 래핑, APIException 사용 | 중간 |

#### 프론트엔드 (수정)
| 파일 | 수정 내용 | 영향도 |
|------|----------|--------|
| `frontend/src/api/index.js` | 인터셉터 수정 | 높음 (핵심) |
| `frontend/src/store/modules/chat.js` | 에러 처리 수정 | 중간 |
| `frontend/src/store/modules/document.js` | 에러 처리 수정 | 낮음 |

### 7.2 구현량 요약

| 구분 | 신규 | 수정 | 총 파일 수 |
|------|------|------|-----------|
| 백엔드 | 4개 | 6개 | **10개** |
| 프론트엔드 | 0개 | 3개 | **3개** |
| **합계** | **4개** | **9개** | **13개** |

### 7.3 코드 변경량 추정

| 작업 | 예상 라인 수 |
|------|-------------|
| 에러 코드/핸들러 (신규) | ~200줄 |
| common.py 모델 추가 | ~50줄 |
| routes 파일 수정 (5개) | ~150줄 (각 30줄) |
| 프론트엔드 인터셉터 | ~40줄 |
| 프론트엔드 store | ~30줄 |
| **총 변경량** | **~470줄** |

### 7.4 리스크 분석

| 리스크 | 영향 | 완화 방안 |
|--------|------|----------|
| 기존 API 호환성 | 중간 | 인터셉터에서 레거시 형식 지원 |
| 프론트엔드 에러 처리 누락 | 낮음 | 인터셉터에서 일괄 처리 |
| 테스트 실패 | 중간 | 응답 구조 변경에 따른 테스트 수정 필요 |

---

## 8. 구현 단계

### Phase 1: 기반 구축 (Day 1)
1. 에러 코드/핸들러 모듈 생성
2. common.py에 APIResponse 모델 추가
3. main.py에 예외 핸들러 등록
4. 프론트엔드 인터셉터 수정

### Phase 2: 주요 API 마이그레이션 (Day 2)
1. search.py 응답 래핑
2. agent.py 응답 래핑
3. 프론트엔드 chat.js 에러 처리 수정

### Phase 3: 나머지 API 마이그레이션 (Day 3)
1. documents.py 응답 래핑
2. settings.py 응답 래핑
3. codes.py 응답 래핑
4. 프론트엔드 document.js 에러 처리 수정

### Phase 4: 테스트 및 검증 (Day 4)
1. 전체 API 테스트
2. 에러 케이스 테스트
3. 프론트엔드 통합 테스트

---

## 9. 마이그레이션 전략

### 9.1 하위 호환성 유지

```javascript
// 인터셉터에서 두 형식 모두 지원
if (result.success !== undefined) {
  // 새 형식
  return result.data
}
// 레거시 형식 (기존 그대로)
return result
```

### 9.2 점진적 롤아웃

1. **1차**: 에러 응답만 새 형식 적용 (예외 핸들러)
2. **2차**: 주요 API 성공 응답 래핑 (search, agent)
3. **3차**: 나머지 API 성공 응답 래핑
4. **4차**: 레거시 지원 코드 제거

---

## 10. 예상 응답 예시

### 10.1 검색 성공
```json
// HTTP 200
{
  "success": true,
  "data": {
    "query": "2024년 입사자 수는?",
    "answer": "2024년에 총 27명이 입사했습니다.",
    "query_type": "nl2sql",
    "sql": "SELECT COUNT(*) FROM employee WHERE ...",
    "sql_result": {...},
    "response_time_ms": 1523
  },
  "error": null
}
```

### 10.2 검색 실패
```json
// HTTP 500
{
  "success": false,
  "data": null,
  "error": {
    "code": "SQL_GENERATION_FAILED",
    "message": "질문을 SQL로 변환하지 못했습니다. 다른 표현으로 시도해주세요",
    "detail": "Unable to generate valid SQL for the given query"
  }
}
```

### 10.3 입력 검증 실패
```json
// HTTP 400
{
  "success": false,
  "data": null,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력값이 올바르지 않습니다",
    "detail": "[{'loc': ['body', 'query'], 'msg': 'field required'}]"
  }
}
```

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import documents, search, agent, codes
from app.api.routes import settings as settings_router
from app.config import settings
from app.core.database.connection import db_manager
from app.core.database.external import external_db_manager
from app.core.errors import register_exception_handlers
from app.middleware import LoggingMiddleware
from app.utils.logger import setup_logger
from app.utils.langsmith import init_langsmith

logger = setup_logger(__name__)

# 앱 실행시 한번만 실행, 종료시 clean-up하는 데코레이션.
@asynccontextmanager 
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 이벤트"""
    # 시작
    logger.info(f"MUREUM 시작: env={settings.app_env}")

    # LangSmith 초기화 (옵션)
    init_langsmith()

    # 서비스 DB 초기화 (운영데이터용)
    db_manager.initialize()
    logger.info("서비스 데이터베이스 연결 풀 초기화 완료")

    # 외부 비즈니스 DB 초기화 (NL2SQL용)
    try:
        external_db_manager.initialize()
        if external_db_manager.is_enabled():
            logger.info("외부 비즈니스 데이터베이스 연결 풀 초기화 완료")
        else:
            logger.info("외부 DB 비활성화 (로컬 business 스키마 사용)")
    except Exception as e:
        logger.warning(f"외부 DB 초기화 실패 (계속 진행): {e}")

    yield

    # 종료
    logger.info("MUREUM 종료 중...")
    db_manager.close()
    external_db_manager.close()
    logger.info("데이터베이스 연결 풀 종료 완료")


# FastAPI 앱 생성
app = FastAPI(
    title="MUREUM API",
    description="기업용 지식 베이스 기반 AI 어시스턴트 API",
    version="1.0.0",
    lifespan=lifespan,
    root_path=settings.context_path
)

# CORS 설정 (환경변수 CORS_ORIGINS로 제어, 기본값: "*")
cors_origins = (
    ["*"] if settings.cors_origins == "*"
    else [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
)

# Middleware 등록 (역순 실행: 나중에 추가한 것이 먼저 실행)
# 실행 순서: LoggingMiddleware → CORSMiddleware → Handler
app.add_middleware(LoggingMiddleware)  # 요청/응답 로깅 (가장 바깥)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 라우터 등록
app.include_router(search.router)
app.include_router(documents.router)
app.include_router(settings_router.router)
app.include_router(codes.router, prefix="/api/admin/v1")  # 코드 관리 라우터 (Phase A)
app.include_router(agent.router)  # AI Agent 라우터


# 기본 엔드포인트
@app.get("/")
async def root():
    """루트 엔드포인트"""
    return {
        "service": "MUREUM API",
        "version": "1.0.0",
        "status": "running",
        "environment": settings.app_env
    }


@app.get("/health")
async def health_check():
    """헬스 체크"""
    try:
        # 데이터베이스 연결 확인
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT 1")

        return {
            "status": "healthy",
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"헬스 체크 실패: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )


@app.get("/api/v1/info")
async def api_info():
    """API 정보"""
    return {
        "api_version": "v1",
        "features": {
            "rag": "지식 베이스 문서 검색",
            "nl2sql": "자연어를 SQL로 변환하여 통계 조회",
            "auto": "자동 의도 분류",
            "agent": "AI Agent 기반 멀티스텝 검색 (ReAct 패턴)"
        },
        "models": {
            "llm": settings.llm_model,
            "embedding": settings.embedding_model
        },
        "endpoints": {
            "search": {
                "POST /api/v1/search": "통합 검색 (auto/rag/nl2sql 모드)",
                "POST /api/v1/rag": "RAG 검색 전용",
                "POST /api/v1/nl2sql": "NL2SQL 검색 전용"
            },
            "agent": {
                "POST /api/v1/agent/search": "AI Agent 검색 (멀티스텝, 멀티턴)",
                "GET /api/v1/agent/sessions": "활성 세션 목록",
                "GET /api/v1/agent/sessions/{session_id}/memory": "세션 메모리 조회",
                "DELETE /api/v1/agent/sessions/{session_id}": "세션 삭제",
                "GET /api/v1/agent/sessions/{session_id}/metrics": "세션 메트릭",
                "GET /api/v1/agent/tools": "사용 가능한 도구 목록",
                "POST /api/v1/agent/test-tool": "도구 단독 테스트"
            },
            "admin_documents": {
                "POST /api/admin/v1/documents": "문서 저장",
                "GET /api/admin/v1/documents": "문서 목록 조회",
                "GET /api/admin/v1/documents/{doc_id}": "문서 상세 조회",
                "PUT /api/admin/v1/documents/{doc_id}": "문서 수정",
                "DELETE /api/admin/v1/documents/{doc_id}": "문서 삭제",
                "POST /api/admin/v1/documents/bulk-delete": "문서 일괄 삭제",
                "POST /api/admin/v1/documents/embedding/execute": "임베딩 실행",
                "POST /api/admin/v1/documents/embedding/preview": "청킹 미리보기"
            },
            "admin_settings": {
                "GET /api/admin/v1/settings": "전체 설정 조회",
                "GET /api/admin/v1/settings/{category}": "카테고리별 설정 조회",
                "GET /api/admin/v1/settings/{category}/{key}": "단일 설정 조회",
                "PUT /api/admin/v1/settings/{category}/{key}": "단일 설정 수정",
                "PUT /api/admin/v1/settings/{category}": "카테고리 설정 일괄 수정",
                "POST /api/admin/v1/settings/{category}/reset": "카테고리 설정 초기화",
                "POST /api/admin/v1/settings/validate-api-key": "API 키 검증",
                "POST /api/admin/v1/settings/refresh-cache": "설정 캐시 새로고침",
                "POST /api/admin/v1/settings/external-database/test": "외부 DB 연결 테스트"
            },
            "admin_codes": {
                "GET /api/admin/v1/codes/groups": "코드 그룹 목록",
                "GET /api/admin/v1/codes/{code_group}": "그룹별 코드 목록",
                "GET /api/admin/v1/codes/item/{code_id}": "코드 단건 조회",
                "POST /api/admin/v1/codes": "코드 생성",
                "PUT /api/admin/v1/codes/{code_id}": "코드 수정",
                "DELETE /api/admin/v1/codes/{code_id}": "코드 삭제",
                "POST /api/admin/v1/codes/{code_group}/reorder": "코드 순서 변경"
            }
        }
    }


# 전역 예외 핸들러 등록 (통일된 API 응답 형식)
register_exception_handlers(app)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )

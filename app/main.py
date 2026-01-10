from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import documents, search, agent, codes
from app.api.routes import settings as settings_router
from app.config import settings
from app.utils.database import db_manager
from app.utils.external_database import external_db_manager
from app.utils.logger import setup_logger
from app.utils.langsmith import init_langsmith

logger = setup_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """애플리케이션 시작/종료 이벤트"""
    # 시작
    logger.info(f"MUREUM 시작: env={settings.app_env}")

    # LangSmith 초기화 (옵션)
    init_langsmith()

    # 서비스 DB 초기화 (메타데이터용)
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
    lifespan=lifespan
)

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if settings.is_development else ["https://yourdomain.com"],
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
            "search": "/api/v1/search, /api/v1/rag, /api/v1/nl2sql",
            "agent": "/api/v1/agent/search (멀티스텝, 멀티턴 대화)",
            "admin_documents": "/api/admin/v1/documents",
            "admin_settings": "/api/admin/v1/settings"
        }
    }


# 예외 처리
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """전역 예외 처리"""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "detail": str(exc) if settings.is_development else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_development,
        log_level=settings.log_level.lower()
    )

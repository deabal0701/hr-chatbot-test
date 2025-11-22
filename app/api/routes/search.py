import time
from typing import Union

from fastapi import APIRouter, HTTPException, status

from app.graphs.nl2sql_graph import nl2sql_graph
from app.graphs.rag_graph import rag_graph
from app.models.schemas import (
    ErrorResponse,
    NL2SQLResponse,
    RAGResponse,
    SearchRequest,
    SearchResponse,
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(request: SearchRequest):
    """
    통합 검색 엔드포인트
    - mode가 'auto'인 경우 자동으로 RAG/NL2SQL 선택
    - mode가 'rag'인 경우 RAG 검색만 수행
    - mode가 'nl2sql'인 경우 NL2SQL 검색만 수행
    """
    start_time = time.time()

    try:
        logger.info(f"검색 요청: query='{request.query}', mode={request.mode}")

        # 모드에 따라 처리
        if request.mode == "auto":
            # 간단한 휴리스틱으로 intent 분류
            query_type = _classify_query_intent(request.query)
        else:
            query_type = request.mode

        # 입력 데이터 구성
        inputs = {
            "question": request.query,
            "filters": request.filters.model_dump() if request.filters else {},
            "top_k": request.top_k
        }

        # 검색 실행
        if query_type == "nl2sql":
            nl2sql_result = await nl2sql_graph.ainvoke(inputs)
            response = SearchResponse(
                query=request.query,
                answer=nl2sql_result.answer,
                query_type="nl2sql",
                nl2sql_result=nl2sql_result,
                metadata=nl2sql_result.metadata,
                response_time_ms=int((time.time() - start_time) * 1000)
            )
        else:  # rag
            rag_result = await rag_graph.ainvoke(inputs)
            response = SearchResponse(
                query=request.query,
                answer=rag_result.answer,
                query_type="rag",
                rag_result=rag_result,
                metadata=rag_result.metadata,
                response_time_ms=int((time.time() - start_time) * 1000)
            )

        logger.info(
            f"검색 완료: type={response.query_type}, "
            f"time={response.response_time_ms}ms"
        )

        return response

    except Exception as e:
        logger.error(f"검색 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"검색 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/rag", response_model=RAGResponse)
async def search_rag(request: SearchRequest):
    """RAG 검색 전용 엔드포인트"""
    try:
        logger.info(f"RAG 검색 요청: query='{request.query}'")

        inputs = {
            "question": request.query,
            "filters": request.filters.model_dump() if request.filters else {},
            "top_k": request.top_k
        }

        result = await rag_graph.ainvoke(inputs)

        logger.info(f"RAG 검색 완료: sources={len(result.sources)}")
        return result

    except Exception as e:
        logger.error(f"RAG 검색 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"RAG 검색 중 오류가 발생했습니다: {str(e)}"
        )


@router.post("/nl2sql", response_model=NL2SQLResponse)
async def search_nl2sql(request: SearchRequest):
    """NL2SQL 검색 전용 엔드포인트"""
    try:
        logger.info(f"NL2SQL 검색 요청: query='{request.query}'")

        inputs = {
            "question": request.query,
            "filters": request.filters.model_dump() if request.filters else {}
        }

        result = await nl2sql_graph.ainvoke(inputs)

        logger.info(f"NL2SQL 검색 완료: sql='{result.sql[:100]}...'")
        return result

    except Exception as e:
        logger.error(f"NL2SQL 검색 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"NL2SQL 검색 중 오류가 발생했습니다: {str(e)}"
        )


def _classify_query_intent(query: str) -> str:
    """
    쿼리 의도 분류 (간단한 휴리스틱)
    실제로는 LLM을 사용하거나 더 정교한 분류기를 사용할 수 있음
    """
    query_lower = query.lower()

    # NL2SQL 키워드
    nl2sql_keywords = [
        "몇 명", "몇명", "수", "통계", "집계", "평균", "합계", "최대", "최소",
        "count", "avg", "sum", "max", "min",
        "입사자", "퇴사자", "직원", "사원",
        "월별", "연도별", "부서별", "직급별"
    ]

    # RAG 키워드
    rag_keywords = [
        "정책", "규정", "가이드", "안내", "공고",
        "설명", "요약", "무엇", "어떻게",
        "재택", "연차", "평가", "채용", "복지"
    ]

    nl2sql_score = sum(1 for keyword in nl2sql_keywords if keyword in query_lower)
    rag_score = sum(1 for keyword in rag_keywords if keyword in query_lower)

    # 숫자나 연도가 포함되어 있으면 NL2SQL 가능성 높음
    if any(year in query for year in ["2020", "2021", "2022", "2023", "2024"]):
        nl2sql_score += 2

    if nl2sql_score > rag_score:
        return "nl2sql"
    else:
        return "rag"

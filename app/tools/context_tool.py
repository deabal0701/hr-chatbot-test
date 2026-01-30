"""
SQL 컨텍스트 검색 도구

기능:
- 스키마 정보 검색 (doc_type: schema)
- Few-shot 쿼리 예제 검색 (doc_type: query_example)
- 비즈니스 용어집 검색 (doc_type: glossary)
- 통합 검색 (all)

설계 근거:
- 스키마, Few-shot, 용어집 검색은 모두 동일한 vector_store와 tb_docs 테이블 사용
- 하나의 도구로 통합하여 LLM 도구 선택 복잡도를 낮추고 프롬프트 토큰 절약
"""

from typing import Dict, Any, List, Optional, Literal
from langchain_core.tools import tool

from app.tools.base import BaseTool, ToolResult
from app.core.vector.vector_store import vector_store
from app.core.config.settings_config import settings_config
from app.models.search import SearchFilters
from app.utils.logger import setup_logger, log_step
from app.utils.common import truncate_text

logger = setup_logger(__name__)


class ContextSearchTool(BaseTool):
    """SQL 컨텍스트 검색 도구 (스키마, Few-shot, 용어집 통합)"""

    def __init__(self):
        super().__init__()
        self._cache: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        return "context_search"

    @property
    def description(self) -> str:
        return """SQL 생성에 필요한 컨텍스트를 검색합니다.

테이블 스키마, 유사 쿼리 예제, 비즈니스 용어를 통합 검색합니다.
SQL 쿼리 작성 전에 필요한 정보를 조회할 때 사용하세요.

context_type:
- "schema": 테이블 구조, 컬럼, 관계 정보
- "example": 유사 SQL 쿼리 예제 (Few-shot)
- "glossary": 비즈니스 용어 → SQL 조건 변환
- "all": 모든 유형 통합 검색 (권장)
"""

    def _execute(
        self,
        query: str,
        context_type: str = "all",
        top_k: int = 5,
        **kwargs
    ) -> ToolResult:
        """
        SQL 컨텍스트 검색 실행

        Args:
            query: 검색할 자연어 질문
            context_type: 검색 유형 ("schema", "example", "glossary", "all")
            top_k: 각 유형별 최대 결과 수

        Returns:
            ToolResult: 검색 결과
        """
        request_id = kwargs.get("request_id", "unknown")
        log_step(request_id, "TOOL", "CONTEXT", "START", f"컨텍스트 검색 시작 | type={context_type}, query={truncate_text(query, 30)}...")

        results = []
        found_counts = {"schema": 0, "example": 0, "glossary": 0}

        try:
            # 스키마 검색 (doc_type: schema)
            if context_type in ("schema", "all"):
                schemas = self._search_schemas(query, top_k, request_id)
                if schemas:
                    results.append("## 관련 테이블 스키마\n")
                    results.extend(schemas)
                    found_counts["schema"] = len(schemas)

            # Few-shot 예제 검색 (doc_type: query_example)
            if context_type in ("example", "all"):
                examples = self._search_examples(query, top_k, request_id)
                if examples:
                    results.append("\n## 유사 쿼리 예제\n")
                    results.extend(examples)
                    found_counts["example"] = len(examples)

            # 용어집 검색 (doc_type: glossary)
            if context_type in ("glossary", "all"):
                terms = self._search_glossary(query, top_k, request_id)
                if terms:
                    results.append("\n## 비즈니스 용어\n")
                    results.extend(terms)
                    found_counts["glossary"] = len(terms)

            # 결과 반환
            if results:
                output = "\n".join(results)
                log_step(request_id, "TOOL", "CONTEXT", "COMPLETE", f"검색 완료 | schema={found_counts['schema']}, example={found_counts['example']}, glossary={found_counts['glossary']}")
                return ToolResult(
                    success=True,
                    data=output,
                    metadata={"found_counts": found_counts}
                )
            else:
                log_step(request_id, "TOOL", "CONTEXT", "EMPTY", "검색 결과 없음")
                return ToolResult(
                    success=True,
                    data="관련 컨텍스트를 찾을 수 없습니다.",
                    metadata={"found_counts": found_counts}
                )

        except Exception as e:
            log_step(request_id, "TOOL", "CONTEXT", "ERROR", f"검색 실패: {e}", level="ERROR")
            return ToolResult(
                success=False,
                data="",
                error=str(e)
            )

    def _search_schemas(self, query: str, top_k: int, request_id: str) -> List[str]:
        """스키마 검색"""
        results = []
        try:
            docs = vector_store.search_similar_documents(
                query=query,
                filters=SearchFilters(usage_type="rag_action", doc_type="schema"),
                top_k=top_k,
                similarity_threshold=0.4
            )
            for doc in docs:
                title = doc.title
                similarity = doc.similarity_score
                results.append(f"### {title}")
                # content 기본 사용, context_data가 있으면 추가
                results.append(f"{doc.content}")
                if doc.context_data:
                    results.append(f"{doc.context_data}")
                results.append(f"유사도: {similarity:.2f}\n")
        except Exception as e:
            log_step(request_id, "TOOL", "CONTEXT", "ERROR", f"스키마 검색 실패: {e}", level="WARNING")
        return results

    def _search_examples(self, query: str, top_k: int, request_id: str) -> List[str]:
        """Few-shot 예제 검색"""
        results = []
        try:
            docs = vector_store.search_similar_documents(
                query=query,
                filters=SearchFilters(usage_type="rag_action", doc_type="query_example"),
                top_k=top_k,
                similarity_threshold=0.3
            )
            for i, doc in enumerate(docs, 1):
                results.append(f"### 예제 {i}: {doc.title}")
                # content 기본 사용, context_data가 있으면 추가
                results.append(f"{doc.content}")
                if doc.context_data:
                    results.append(f"{doc.context_data}\n")
        except Exception as e:
            log_step(request_id, "TOOL", "CONTEXT", "ERROR", f"예제 검색 실패: {e}", level="WARNING")
        return results

    def _search_glossary(self, query: str, top_k: int, request_id: str) -> List[str]:
        """용어집 검색"""
        results = []
        try:
            docs = vector_store.search_similar_documents(
                query=query,
                filters=SearchFilters(usage_type="rag_action", doc_type="glossary"),
                top_k=top_k,
                similarity_threshold=0.5
            )
            for doc in docs:
                # content 기본 사용, context_data가 있으면 추가
                if doc.context_data:
                    results.append(f"- **{doc.title}**: {doc.content} | {doc.context_data}")
                else:
                    results.append(f"- **{doc.title}**: {doc.content}")
        except Exception as e:
            log_step(request_id, "TOOL", "CONTEXT", "ERROR", f"용어집 검색 실패: {e}", level="WARNING")
        return results


# LangChain Tool 래퍼
@tool
def context_search_tool(
    query: str,
    context_type: str = "all",
    top_k: int = 5
) -> str:
    """
    SQL 생성에 필요한 컨텍스트를 검색합니다.

    테이블 스키마, 유사 쿼리 예제, 비즈니스 용어를 통합 검색합니다.
    SQL 쿼리 작성 전에 필요한 정보를 조회할 때 사용하세요.

    Args:
        query: 검색할 자연어 질문
        context_type: 검색 유형
            - "schema": 테이블 구조, 컬럼, 관계 정보
            - "example": 유사 SQL 쿼리 예제 (Few-shot)
            - "glossary": 비즈니스 용어 → SQL 조건 변환
            - "all": 모든 유형 통합 검색 (권장)
        top_k: 각 유형별 최대 결과 수 (기본 5)

    Returns:
        검색된 컨텍스트 정보

    Example:
        context_search_tool("부서별 입사자 수", "all")
        → 스키마 + 예제 + 용어 통합 결과

        context_search_tool("직원 테이블", "schema")
        → employee 테이블 스키마 정보

        context_search_tool("재직자", "glossary")
        → "재직자" → "WHERE status = 'active'"
    """
    # context_type 유효성 검증
    valid_types = ("schema", "example", "glossary", "all")
    if context_type not in valid_types:
        context_type = "all"

    # top_k 범위 제한
    top_k = max(1, min(top_k, 10))

    tool_instance = ContextSearchTool()
    result = tool_instance.execute(
        query=query,
        context_type=context_type,
        top_k=top_k
    )

    if result.success:
        return result.data
    else:
        return f"컨텍스트 검색 실패: {result.error}"

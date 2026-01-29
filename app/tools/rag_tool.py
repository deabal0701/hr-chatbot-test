"""
문서 검색 도구 (RAG)

기능:
- 벡터 검색으로 관련 문서 찾기
- 하이브리드 검색 지원 (확장)
- 결과 리랭킹 (확장)

확장성:
- 하이브리드 검색: 키워드 + 벡터
- 리랭킹: Cross-encoder 사용
- 문서 필터링: 메타데이터 기반
"""

from typing import Dict, Any, List, Optional
from langchain_core.tools import tool

from app.tools.base import BaseTool, ToolResult
from app.core.vector.vector_store import vector_store
from app.core.config.settings_config import settings_config
from app.models.search import SearchFilters
from app.config import settings
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)


class DocumentSearchTool(BaseTool):
    """문서 검색 도구"""

    def __init__(self):
        super().__init__()
        self._search_cache: Dict[str, Any] = {}

    @property
    def name(self) -> str:
        return "search_documents"

    @property
    def description(self) -> str:
        return """Search corporate documents and regulations.

Use this tool when you need to:
- Find company policies (e.g., "remote work policy", "travel policy")
- Look up company regulations and guidelines
- Access procedures and workflows
- Find FAQ or announcements
- Get information about benefits, compliance, training, etc.

DO NOT use this tool for:
- Data or statistics (use query_database instead)
- Calculations (use calculate instead)
- Real-time database queries (use query_database instead)

Args:
    question: Natural language question about policies/regulations
    top_k: Number of documents to retrieve (default: 5, max: 20)
    doc_type: Filter by document type (optional): policy, guide, faq, notice

Returns:
    Relevant document snippets with titles and metadata

Examples:
    - "재택근무 정책이 뭐야?" → Returns remote work policy documents
    - "법인카드 사용 규정" → Returns corporate card policy
    - "보안 가이드라인은?" → Returns security guidelines
"""

    @property
    def parameters_schema(self) -> Dict[str, Any]:
        """파라미터 스키마"""
        return {
            "type": "object",
            "properties": {
                "question": {
                    "type": "string",
                    "description": "Natural language question about policies/regulations"
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of documents to retrieve (default: 5, max: 20)",
                    "default": 5,
                    "minimum": 1,
                    "maximum": 20
                },
                "doc_type": {
                    "type": "string",
                    "description": "Filter by document type: policy, guide, faq, notice",
                    "enum": ["policy", "guide", "faq", "notice"]
                }
            },
            "required": ["question"]
        }

    def before_execute(self, **kwargs) -> Dict[str, Any]:
        """
        전처리: 캐싱 체크, 파라미터 정규화

        확장 포인트:
        - 쿼리 확장 (동의어, 관련어)
        - 쿼리 재작성 (더 나은 검색 결과)
        """
        question = kwargs.get("question", "")
        top_k = kwargs.get("top_k", 5)

        # top_k 제한
        if top_k > 20:
            log_step("SYSTEM", "TOOL", self.name, "WARN", f"top_k 초과, 20으로 제한", level="WARNING", original_top_k=top_k)
            kwargs["top_k"] = 20

        # 캐시 체크
        cache_key = f"{question.lower().strip()}:{top_k}"
        if cache_key in self._search_cache:
            log_step("SYSTEM", "TOOL", self.name, "CACHE", f"캐시 히트", level="DEBUG", cache_key=cache_key[:50])
            kwargs["_cached_result"] = self._search_cache[cache_key]

        return kwargs

    def after_execute(self, result: ToolResult) -> ToolResult:
        """
        후처리: 캐싱 저장

        확장 포인트:
        - 결과 리랭킹
        - 다양성 증진 (MMR)
        """
        # 성공한 결과만 캐싱
        if result.success and result.data:
            question = result.metadata.get("original_question", "")
            top_k = result.metadata.get("top_k", 5)
            cache_key = f"{question.lower().strip()}:{top_k}"
            self._search_cache[cache_key] = result.data

            # 캐시 크기 제한
            if len(self._search_cache) > 50:
                oldest_key = next(iter(self._search_cache))
                del self._search_cache[oldest_key]

        return result

    def _execute(
        self,
        question: str,
        top_k: int = 5,
        doc_type: Optional[str] = None,
        _cached_result: Any = None,
        **kwargs
    ) -> ToolResult:
        """실제 실행 로직"""

        # 캐시된 결과 반환
        if _cached_result is not None:
            return ToolResult(
                success=True,
                data=_cached_result,
                metadata={
                    "original_question": question,
                    "top_k": top_k,
                    "cached": True
                }
            ) # type: ignore

        try:
            # RAG 설정 가져오기
            similarity_threshold = settings_config.get_value(
                "rag",
                "similarity_threshold",
                settings.rag_similarity_threshold
            )

            # 필터 구성 (지식 문서 전용 - Action 문서 제외)
            filters = SearchFilters(usage_type="rag_knowledge", doc_type=doc_type) if doc_type else SearchFilters(usage_type="rag_knowledge")

            # 벡터 검색 (기존 vector_store 재사용)
            documents = vector_store.search_similar_documents(
                query=question,
                top_k=top_k,
                filters=filters,
                similarity_threshold=similarity_threshold
            )

            if not documents:
                return ToolResult(
                    success=True,
                    data="관련 문서를 찾을 수 없습니다. 질문을 다르게 표현해보세요.",
                    metadata={
                        "original_question": question,
                        "top_k": top_k,
                        "found_count": 0
                    }
                ) # type: ignore

            # 결과 포맷팅
            formatted_result = self._format_documents(documents)

            return ToolResult(
                success=True,
                data=formatted_result,
                metadata={
                    "original_question": question,
                    "top_k": top_k,
                    "found_count": len(documents),
                    "doc_types": list(set(doc.doc_type for doc in documents)),
                    "cached": False
                }
            ) # type: ignore

        except Exception as e:
            log_step("SYSTEM", "TOOL", self.name, "ERROR", f"문서 검색 실패: {e}", level="ERROR")
            return ToolResult(
                success=False,
                error=f"Document search failed: {str(e)}",
                metadata={"original_question": question}
            ) # type: ignore

    def _format_documents(self, documents: List) -> str:
        """
        문서 결과 포맷팅

        확장 포인트:
        - 마크다운 포맷
        - JSON 포맷
        - 하이라이트 추가
        """
        formatted = f"총 {len(documents)}개의 관련 문서를 찾았습니다:\n\n"

        for i, doc in enumerate(documents, 1):
            similarity = doc.similarity_score if doc.similarity_score is not None else 0.0

            formatted += f"[문서 {i}]\n"
            formatted += f"제목: {doc.title}\n"
            formatted += f"유형: {doc.doc_type}\n"
            formatted += f"관련도: {similarity:.2f}\n"
            formatted += f"내용: {doc.content_snippet[:300]}"

            if len(doc.content_snippet) > 300:
                formatted += "..."

            formatted += "\n\n"

        return formatted

    def _hybrid_search(
        self,
        question: str,
        top_k: int,
        filters: Optional[SearchFilters]
    ) -> List:
        """
        하이브리드 검색 (확장 기능)

        벡터 검색 + 키워드 검색 결합
        TODO: 추후 구현
        """
        # 1. 벡터 검색
        vector_results = vector_store.search_similar_documents(
            query=question,
            top_k=top_k * 2,  # 더 많이 가져와서 리랭킹
            filters=filters
        )

        # 2. 키워드 검색 (TODO: 구현)
        # keyword_results = keyword_search(question, top_k * 2)

        # 3. 결과 합치기 및 리랭킹 (TODO: Cross-encoder)
        # combined = rerank(vector_results, keyword_results)

        return vector_results[:top_k]


# LangChain tool 래퍼
@tool
def search_documents_tool(
    question: str,
    top_k: int = 5,
    doc_type: Optional[str] = None
) -> str:
    """
    회사 문서, 정책, 규정을 검색합니다.

    이 도구를 사용하는 경우:
    - 회사 정책 (예: "재택근무 정책", "출장 규정", "휴가 규정")
    - 회사 규정 및 가이드라인 (예: "보안 가이드라인", "법인카드 사용 규정")
    - 업무 절차 및 워크플로우
    - FAQ 및 공지사항
    - 복리후생, 컴플라이언스, 교육 정보

    이 도구를 사용하지 않는 경우:
    - 구조화된 데이터나 통계 (query_database_tool 사용)
    - 계산 작업 (calculate_tool 사용)

    Args:
        question: 정책/규정에 대한 자연어 질문
        top_k: 검색할 문서 수 (기본값: 5)
        doc_type: 문서 유형 필터 (선택사항: policy, guide, faq, notice)

    Returns:
        제목과 메타데이터를 포함한 관련 문서 발췌

    예시:
        - "재택근무 정책이 뭐야?" → 재택근무 정책 문서 반환
        - "출장 규정은?" → 출장 정책 반환
        - "보안 가이드라인은?" → 보안 가이드라인 반환
    """
    tool_instance = DocumentSearchTool()
    result = tool_instance.execute(
        question=question,
        top_k=top_k,
        doc_type=doc_type
    )

    if result.success:
        return str(result.data)
    else:
        return f"Error: {result.error}"

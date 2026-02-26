"""
RAG 검색 노드 (RAG Nodes)

기능:
- 쿼리 분석 (query_analysis_node): Doc ID 패턴 감지 + 키워드 추출
- 하이브리드 검색 (retrieve_documents_node): 벡터 + pg_trgm + RRF
- 리랭킹 (rerank_documents_node): passthrough (추후 구현 예정)
- 답변 생성 (generate_answer_node)

사용:
- RAGGraph 클래스의 노드로 사용
- query_analysis → retrieve → rerank → generate_answer 순서로 실행
"""
import re
from typing import Dict, Any, List
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.models.rag import DocumentSource
from app.models.search import SearchFilters
from app.core.vector.keyword_extractor import keyword_extractor
from app.core.vector.hybrid_search import hybrid_search
from app.core.llm.llm_config import LLMConfigManager
from app.core.llm.prompt_service import prompt_service
from app.utils.common import extract_llm_text_content
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)

# Doc ID 직접 조회 패턴 (query_analysis_node 사용)
DIRECT_LOOKUP_PATTERNS = [
    r'\b[A-Z]{2,}-\d+\b',           # HR-001, POL-023, ISO-27001
    r'문서\s*번호\s*[A-Z0-9\-]+',    # "문서번호 HR-001"
    r'#\d{3,}',                      # #1234 (3자리 이상)
]


# 순환 import 방지를 위해 지연 import
_settings_config = None


def _get_settings_config():
    """settings_config 지연 로드"""
    global _settings_config
    if _settings_config is None:
        from app.core.config.settings_config import settings_config
        _settings_config = settings_config
    return _settings_config


def _get_llm():
    """
    매 요청 시 DB 설정을 반영한 LLM 인스턴스 생성

    RAG는 DB 설정의 temperature를 사용 (일반적으로 0.1)
    """
    settings_config = _get_settings_config()
    temperature = settings_config.get_value("llm", "temperature", 0.1)

    return LLMConfigManager.create_llm(temperature=temperature)


def _build_context(documents: List[DocumentSource]) -> str:
    """문서 리스트를 컨텍스트 문자열로 변환"""
    context_parts = []

    rag_settings = LLMConfigManager.get_rag_settings()
    max_context_length = rag_settings["max_context_length"]

    for i, doc in enumerate(documents, 1):
        similarity = doc.similarity_score if doc.similarity_score is not None else 0.0
        doc_info = f"""[문서 {i}]
제목: {doc.title}
유형: {doc.doc_type}
유사도: {similarity:.2f}
내용: {doc.content}
"""
        context_parts.append(doc_info)

        current_length = sum(len(p) for p in context_parts)
        if current_length > max_context_length:
            log_step(logger, "SYSTEM", "RAG", "CTX", "WARN", "컨텍스트 길이 초과", level="WARNING", current=current_length, max=max_context_length)
            break

    return "\n".join(context_parts)


def query_analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    쿼리 분석 노드

    ① Doc ID 패턴 감지 (HR-001 등) → search_type = "direct_lookup"
    ② 키워드 추출 (keyword_extraction 설정에 따라 none/rule)
       - vector_query: 원본 질의 그대로 (벡터 검색용)
       - keyword_query: 추출 키워드 (pg_trgm 검색용)
    """
    question = state["question"]
    request_id = state.get("request_id", "unknown")
    sc = _get_settings_config()

    # Doc ID 패턴 감지
    direct_lookup_enabled = sc.get_value("rag", "direct_lookup_enabled", "true") == "true"
    doc_pattern = None
    search_type = "normal"

    if direct_lookup_enabled:
        for pattern in DIRECT_LOOKUP_PATTERNS:
            m = re.search(pattern, question)
            if m:
                doc_pattern = m.group(0)
                search_type = "direct_lookup"
                break

    # 키워드 추출
    if search_type == "direct_lookup":
        keyword_query = doc_pattern
    else:
        mode = sc.get_value("rag", "keyword_extraction", "rule")
        keyword_query = keyword_extractor.extract(question, mode=mode)

    log_step(logger, request_id, "RAG", "0", "ANALYSIS", "쿼리 분석 완료",
             search_type=search_type, keyword_query=(keyword_query or "")[:40])

    state["vector_query"] = question
    state["keyword_query"] = keyword_query
    state["search_type"] = search_type
    state["doc_pattern"] = doc_pattern
    return state


def retrieve_documents_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    검색 노드 (하이브리드)

    query_analysis_node의 출력(search_type, vector_query, keyword_query)을 읽어
    hybrid_search.search()를 통해 벡터+키워드 하이브리드 검색 또는 직접 조회 수행.

    Args:
        state: RAGState (Dict 형태로 전달)

    Returns:
        업데이트된 state (retrieved_docs, metadata 필드 채움)
    """
    question = state["question"]
    vector_query = state.get("vector_query") or question
    keyword_query = state.get("keyword_query") or question
    search_type = state.get("search_type") or "normal"
    doc_pattern = state.get("doc_pattern")
    filters_dict = state.get("filters", {})
    request_id = state.get("request_id", "unknown")

    rag_settings = LLMConfigManager.get_rag_settings()
    top_k = state.get("top_k") or rag_settings["top_k"]
    similarity_threshold = rag_settings["similarity_threshold"]

    filters = SearchFilters(**filters_dict) if filters_dict else None
    tenant_id = state.get("tenant_id")

    log_step(logger, request_id, "RAG", "1", "RETRIEVE", "검색 시작",
             search_type=search_type, top_k=top_k, has_filters=bool(filters_dict))

    documents = hybrid_search.search(
        vector_query=vector_query,
        keyword_query=keyword_query,
        top_k=top_k,
        filters=filters,
        similarity_threshold=similarity_threshold,
        tenant_id=tenant_id,
        search_type=search_type,
        doc_pattern=doc_pattern,
        request_id=request_id,
    )

    state["retrieved_docs"] = documents
    state["metadata"] = {
        "retrieved_count": len(documents),
        "top_k": top_k,
        "search_type": search_type,
    }

    if documents:
        doc_summaries = [f"{d.title}(점수:{d.similarity_score:.4f})" for d in documents[:3]]
        log_step(logger, request_id, "RAG", "1", "RETRIEVE", f"검색 완료 - {len(documents)}개 문서 발견", top_docs=", ".join(doc_summaries))
    else:
        log_step(logger, request_id, "RAG", "1", "RETRIEVE", "검색 완료 - 관련 문서 없음")

    return state


def rerank_documents_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    리랭킹 노드 (현재: passthrough)

    현재는 검색 결과를 그대로 통과시킵니다.
    추후 reranker_mode 설정에 따라 LLM/CrossEncoder 리랭킹 활성화 예정.
    """
    request_id = state.get("request_id", "unknown")
    doc_count = len(state.get("retrieved_docs", []))
    log_step(logger, request_id, "RAG", "2", "RERANK", f"리랭킹 통과 (passthrough) - {doc_count}개 문서")
    return state


def generate_answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    답변 생성 노드

    검색된 문서를 기반으로 LLM을 사용하여 답변을 생성합니다.

    Args:
        state: RAGState (Dict 형태로 전달)

    Returns:
        업데이트된 state (answer 필드 채움)
    """
    question = state["question"]
    documents = state["retrieved_docs"]
    request_id = state.get("request_id", "unknown")

    if not documents:
        log_step(logger, request_id, "RAG", "3", "GENERATE", "문서 없음 - 기본 응답 반환")
        state["answer"] = "관련 문서를 찾을 수 없습니다. 다른 질문을 시도해주세요."
        return state

    log_step(logger, request_id, "RAG", "3a", "CONTEXT", "컨텍스트 구성 시작", doc_count=len(documents))
    context = _build_context(documents)
    log_step(logger, request_id, "RAG", "3a", "CONTEXT", "컨텍스트 구성 완료", context_length=len(context))

    system_prompt = prompt_service.get_rag_system_prompt()

    user_prompt = f"""질문: {question}

참고 문서:
{context}

위 문서를 참고하여 질문에 답변해주세요."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    llm = _get_llm()
    settings_config = _get_settings_config()
    llm_model = settings_config.get_value("llm", "model", settings.llm_model)

    log_step(logger, request_id, "RAG", "3b", "LLM-INPUT", "LLM 호출 시작", model=llm_model, system_prompt_length=len(system_prompt), user_prompt_length=len(user_prompt), context_length=len(context))

    if logger.isEnabledFor(logging.DEBUG):
        log_step(logger, request_id, "RAG", "3b", "LLM-INPUT", "USER_PROMPT", level="DEBUG", content=user_prompt)
        log_step(logger, request_id, "RAG", "3b", "LLM-INPUT", "CONTEXT", level="DEBUG", content=context)

    try:
        response = llm.invoke(messages)
        answer = extract_llm_text_content(response.content)

        state["answer"] = answer
        state["metadata"]["llm_model"] = llm_model
        state["metadata"]["context_length"] = len(context)

        log_step(logger, request_id, "RAG", "3b", "LLM-OUTPUT", "LLM 답변 생성 완료", answer_length=len(answer))

        if logger.isEnabledFor(logging.DEBUG):
            log_step(logger, request_id, "RAG", "3b", "LLM-OUTPUT", "ANSWER", level="DEBUG", content=answer)

    except Exception as e:
        log_step(logger, request_id, "RAG", "3b", "ERROR", f"LLM 호출 실패: {e}", level="ERROR")
        state["answer"] = f"답변 생성 중 오류가 발생했습니다: {str(e)}"

    return state

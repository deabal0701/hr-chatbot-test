from typing import Any, Dict, List, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from app.config import settings
from app.models.schemas import DocumentSource, RAGResponse, SearchFilters
from app.services.settings_service import settings_service
from app.services.vector_store import vector_store
from app.utils.logger import setup_logger, log_rag_step  # 통합 로깅 유틸리티
from app.utils.llm_config import LLMConfigManager
from app.utils.common import truncate_text  # 공통 유틸리티

logger = setup_logger(__name__)


class RAGState(TypedDict):
    """RAG Graph 상태"""
    question: str
    filters: Dict[str, Any]
    top_k: int
    retrieved_docs: List[DocumentSource]
    answer: str
    metadata: Dict[str, Any]
    request_id: str  # 요청 추적용 ID


class RAGGraph:
    """RAG 검색 그래프 (LangGraph)"""

    def __init__(self):
        # 그래프 구성 (LLM은 요청 시점에 생성)
        self.graph = self._build_graph()

    def _get_llm(self):
        """
        매 요청 시 DB 설정을 반영한 LLM 인스턴스 생성 (Phase 1: init_chat_model 적용)

        RAG는 DB 설정의 temperature를 사용 (일반적으로 0.1)
        """
        # DB에서 temperature 읽기
        temperature = settings_service.get_value("llm", "temperature", 0.1)

        return LLMConfigManager.create_llm(
            temperature=temperature,
            # model과 provider는 DB 설정 사용
        )

    def _build_graph(self) -> StateGraph:
        """그래프 구성"""
        workflow = StateGraph(RAGState)

        # 노드 추가
        workflow.add_node("retrieve", self._retrieve_documents)
        workflow.add_node("generate_answer", self._generate_answer)

        # 엣지 정의
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "generate_answer")
        workflow.add_edge("generate_answer", END)

        return workflow.compile()

    def _retrieve_documents(self, state: RAGState) -> RAGState:
        """문서 검색 노드"""
        question = state["question"]
        filters_dict = state.get("filters", {})
        request_id = state.get("request_id", "unknown")

        # DB 설정에서 RAG 파라미터 가져오기
        rag_settings = LLMConfigManager.get_rag_settings()
        top_k = state.get("top_k") or rag_settings["top_k"]
        similarity_threshold = rag_settings["similarity_threshold"]

        # SearchFilters 객체 생성
        filters = SearchFilters(**filters_dict) if filters_dict else None

        log_rag_step(request_id, "1", "RETRIEVE", "벡터 검색 시작",
                     question=question[:40], top_k=top_k,
                     similarity_threshold=similarity_threshold,
                     has_filters=bool(filters_dict))

        # 벡터 검색 (similarity_threshold도 DB 설정 적용)
        documents = vector_store.search_similar_documents(
            query=question,
            top_k=top_k,
            filters=filters,
            similarity_threshold=similarity_threshold
        )

        state["retrieved_docs"] = documents
        state["metadata"] = {
            "retrieved_count": len(documents),
            "top_k": top_k
        }

        # 검색 결과 상세 로그
        if documents:
            doc_summaries = [f"{d.title}(유사도:{d.similarity_score:.2f})" for d in documents[:3]]
            log_rag_step(request_id, "1", "RETRIEVE", f"벡터 검색 완료 - {len(documents)}개 문서 발견",
                         top_docs=", ".join(doc_summaries))
        else:
            log_rag_step(request_id, "1", "RETRIEVE", "벡터 검색 완료 - 관련 문서 없음")

        return state

    def _generate_answer(self, state: RAGState) -> RAGState:
        """답변 생성 노드"""
        question = state["question"]
        documents = state["retrieved_docs"]
        request_id = state.get("request_id", "unknown")

        if not documents:
            log_rag_step(request_id, "2", "GENERATE", "문서 없음 - 기본 응답 반환")
            state["answer"] = "관련 문서를 찾을 수 없습니다. 다른 질문을 시도해주세요."
            return state

        # 컨텍스트 구성
        log_rag_step(request_id, "2a", "CONTEXT", "컨텍스트 구성 시작",
                     doc_count=len(documents))
        context = self._build_context(documents)
        log_rag_step(request_id, "2a", "CONTEXT", "컨텍스트 구성 완료",
                     context_length=len(context))

        # 시스템 프롬프트
        system_prompt = """당신은 기업용 지식 베이스 전문가입니다.
제공된 문서를 기반으로 사용자의 질문에 정확하고 친절하게 답변해주세요.

답변 시 주의사항:
1. 반드시 제공된 문서의 내용만을 기반으로 답변하세요
2. 문서에 정보가 없으면 "제공된 문서에서 해당 정보를 찾을 수 없습니다"라고 명확히 안내하세요
3. 출처를 명시하세요 (예: "지식 베이스 문서에 따르면...")
4. 답변은 명확하고 구체적으로 작성하세요
5. 필요시 불릿 포인트나 번호를 사용하여 가독성을 높이세요
"""

        user_prompt = f"""질문: {question}

참고 문서:
{context}

위 문서를 참고하여 질문에 답변해주세요."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        # 매 요청마다 DB 설정 반영된 LLM 사용
        llm = self._get_llm()
        llm_model = settings_service.get_value("llm", "model", settings.llm_model)

        # LLM 입력 로그
        log_rag_step(request_id, "2b", "LLM-INPUT", "LLM 호출 시작",
                     model=llm_model,
                     system_prompt_length=len(system_prompt),
                     user_prompt_length=len(user_prompt),
                     context_length=len(context))
        log_rag_step(request_id, "2b", "LLM-INPUT", f"USER_PROMPT: {truncate_text(user_prompt)}")
        log_rag_step(request_id, "2b", "LLM-INPUT", f"CONTEXT: {truncate_text(context)}")

        try:
            response = llm.invoke(messages)
            answer = response.content

            state["answer"] = answer
            state["metadata"]["llm_model"] = llm_model
            state["metadata"]["context_length"] = len(context)

            # LLM 출력 로그
            log_rag_step(request_id, "2b", "LLM-OUTPUT", "LLM 답변 생성 완료",
                         answer_length=len(answer))
            log_rag_step(request_id, "2b", "LLM-OUTPUT", f"ANSWER: {truncate_text(answer)}")

        except Exception as e:
            logger.error(f"[{request_id}] [RAG-2b] [LLM] LLM 호출 실패: {e}")
            state["answer"] = f"답변 생성 중 오류가 발생했습니다: {str(e)}"

        return state

    def _build_context(self, documents: List[DocumentSource]) -> str:
        """문서 리스트를 컨텍스트 문자열로 변환"""
        context_parts = []

        # DB 설정에서 max_context_length 가져오기
        rag_settings = LLMConfigManager.get_rag_settings()
        max_context_length = rag_settings["max_context_length"]

        for i, doc in enumerate(documents, 1):
            # 문서 정보
            similarity = doc.similarity_score if doc.similarity_score is not None else 0.0
            doc_info = f"""
[문서 {i}]
제목: {doc.title}
유형: {doc.doc_type}
유사도: {similarity:.2f}
내용: {doc.content_snippet}
"""
            context_parts.append(doc_info)

            # 최대 컨텍스트 길이 체크
            current_length = sum(len(p) for p in context_parts)
            if current_length > max_context_length:
                logger.warning(f"컨텍스트 길이 초과: {current_length} > {max_context_length}")
                break

        return "\n".join(context_parts)

    async def ainvoke(self, inputs: Dict[str, Any]) -> RAGResponse:
        """그래프 비동기 실행"""
        request_id = inputs.get("request_id", "unknown")

        # DB 설정에서 기본 top_k 가져오기
        rag_settings = LLMConfigManager.get_rag_settings()

        # 초기 상태 설정
        initial_state: RAGState = {
            "question": inputs["question"],
            "filters": inputs.get("filters", {}),
            "top_k": inputs.get("top_k") or rag_settings["top_k"],
            "retrieved_docs": [],
            "answer": "",
            "metadata": {},
            "request_id": request_id
        }

        log_rag_step(request_id, "0", "INIT", "RAG 그래프 실행 시작",
                     question=inputs["question"][:40], top_k=initial_state["top_k"])

        # 그래프 실행
        result = await self.graph.ainvoke(initial_state)

        log_rag_step(request_id, "3", "COMPLETE", "RAG 그래프 실행 완료",
                     docs_found=len(result["retrieved_docs"]),
                     answer_length=len(result["answer"]))

        # 응답 구성
        return RAGResponse(
            answer=result["answer"],
            sources=result["retrieved_docs"],
            metadata=result["metadata"]
        )

    def invoke(self, inputs: Dict[str, Any]) -> RAGResponse:
        """그래프 동기 실행"""
        request_id = inputs.get("request_id", "unknown")

        # DB 설정에서 기본 top_k 가져오기
        rag_settings = LLMConfigManager.get_rag_settings()

        # 초기 상태 설정
        initial_state: RAGState = {
            "question": inputs["question"],
            "filters": inputs.get("filters", {}),
            "top_k": inputs.get("top_k") or rag_settings["top_k"],
            "retrieved_docs": [],
            "answer": "",
            "metadata": {},
            "request_id": request_id
        }

        log_rag_step(request_id, "0", "INIT", "RAG 그래프 실행 시작 (동기)",
                     question=inputs["question"][:40], top_k=initial_state["top_k"])

        # 그래프 실행
        result = self.graph.invoke(initial_state)

        log_rag_step(request_id, "3", "COMPLETE", "RAG 그래프 실행 완료 (동기)",
                     docs_found=len(result["retrieved_docs"]),
                     answer_length=len(result["answer"]))

        # 응답 구성
        return RAGResponse(
            answer=result["answer"],
            sources=result["retrieved_docs"],
            metadata=result["metadata"]
        )


# 싱글톤 인스턴스
rag_graph = RAGGraph()

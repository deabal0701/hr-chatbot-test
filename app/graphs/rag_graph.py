from typing import Any, Dict, List, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from app.config import settings
from app.models.rag import DocumentSource
from app.models.search import SearchFilters, SearchResponse
from app.core.config.settings_service import settings_service
from app.core.vector.vector_store import vector_store
from app.core.llm.prompt_service import prompt_service
from app.utils.logger import setup_logger, log_step  # 통합 로깅 유틸리티
from app.core.llm.llm_config import LLMConfigManager

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
        """요청한 질의를 바탕으로 질의를 백터로 변경 후 Index 문서 검색을 하는  노드"""
        question = state["question"]
        filters_dict = state.get("filters", {})
        request_id = state.get("request_id", "unknown")

        # DB 설정에서 RAG 파라미터 가져오기
        rag_settings = LLMConfigManager.get_rag_settings()
        top_k = state.get("top_k") or rag_settings["top_k"]
        similarity_threshold = rag_settings["similarity_threshold"]

        # SearchFilters 객체 생성
        filters = SearchFilters(**filters_dict) if filters_dict else None

        log_step(request_id, "RAG", "1", "RETRIEVE", "벡터 검색 시작", question=question, top_k=top_k, similarity_threshold=similarity_threshold, has_filters=bool(filters_dict))

        # 벡터 검색 (similarity_threshold도 DB 설정 적용)
        # documents 는 DocumentSource 의 타입
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
            log_step(request_id, "RAG", "1", "RETRIEVE", f"벡터 검색 완료 - {len(documents)}개 문서 발견",
                    top_docs=", ".join(doc_summaries))
        else:
            log_step(request_id, "RAG", "1", "RETRIEVE", "벡터 검색 완료 - 관련 문서 없음")

        return state

    def _generate_answer(self, state: RAGState) -> RAGState:
        """답변 생성 노드"""
        question = state["question"]
        documents = state["retrieved_docs"]
        request_id = state.get("request_id", "unknown")

        if not documents:
            log_step(request_id, "RAG", "2", "GENERATE", "문서 없음 - 기본 응답 반환")
            state["answer"] = "관련 문서를 찾을 수 없습니다. 다른 질문을 시도해주세요."
            return state

        # 컨텍스트 구성
        log_step(request_id, "RAG", "2a", "CONTEXT", "컨텍스트 구성 시작", doc_count=len(documents))
        context = self._build_context(documents)
        log_step(request_id, "RAG", "2a", "CONTEXT", "컨텍스트 구성 완료", context_length=len(context))

        # 시스템 프롬프트 (DB에서 동적 로드)
        system_prompt = prompt_service.get_rag_system_prompt()

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
        log_step(request_id, "RAG", "2b", "LLM-INPUT", "LLM 호출 시작", model=llm_model, system_prompt_length=len(system_prompt), user_prompt_length=len(user_prompt), context_length=len(context))
        log_step(request_id, "RAG", "2b", "LLM-INPUT", f"USER_PROMPT: {user_prompt}")
        log_step(request_id, "RAG", "2b", "LLM-INPUT", f"CONTEXT: {context}")

        try:
            response = llm.invoke(messages)
            answer = response.content

            state["answer"] = answer
            state["metadata"]["llm_model"] = llm_model
            state["metadata"]["context_length"] = len(context)

            # LLM 출력 로그
            log_step(request_id, "RAG", "2b", "LLM-OUTPUT", "LLM 답변 생성 완료", answer_length=len(answer))
            log_step(request_id, "RAG", "2b", "LLM-OUTPUT", f"ANSWER: {answer}")

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
            doc_info = f"""[문서 {i}]
제목: {doc.title}
유형: {doc.doc_type}
유사도: {similarity:.2f}
내용: {doc.content}
"""
            context_parts.append(doc_info)

            # 최대 컨텍스트 길이 체크
            current_length = sum(len(p) for p in context_parts)
            if current_length > max_context_length:
                logger.warning(f"컨텍스트 길이 초과: {current_length} > {max_context_length}")
                break

        return "\n".join(context_parts)   # 각 문서를 "\n"로 구분하여 연결

    def _prepare_initial_state(self, inputs: Dict[str, Any]) -> RAGState:
        """초기 상태 준비 (ainvoke와 invoke 공통 로직)"""
        request_id = inputs.get("request_id", "unknown")

        # DB 설정에서 기본 top_k 가져오기
        rag_settings = LLMConfigManager.get_rag_settings()

        return {
            "question": inputs["question"],
            "filters": inputs.get("filters", {}),
            "top_k": inputs.get("top_k") or rag_settings["top_k"],
            "retrieved_docs": [],
            "answer": "",
            "metadata": {},
            "request_id": request_id
        }

    def _build_response(self, result: RAGState, response_time_ms: int = 0) -> SearchResponse:
        """실행 결과를 SearchResponse로 변환"""
        return SearchResponse(
            query=result["question"],
            answer=result["answer"],
            query_type="rag",
            response_time_ms=response_time_ms,
            sql=None,
            sql_result=None,
            sources=result["retrieved_docs"],
            metadata=result["metadata"]
        )

    async def ainvoke(self, inputs: Dict[str, Any]) -> SearchResponse:
        """그래프 비동기 실행"""
        import time
        start_time = time.time()

        # 초기 상태 준비 (공통 로직)
        initial_state = self._prepare_initial_state(inputs)
        request_id = initial_state["request_id"]

        log_step(request_id, "RAG", "0", "INIT", "RAG 그래프 실행 시작", question=inputs["question"], top_k=initial_state["top_k"])

        # 그래프 실행
        result = await self.graph.ainvoke(initial_state)
        response_time_ms = int((time.time() - start_time) * 1000)
        log_step(request_id, "RAG", "3", "COMPLETE", "RAG 그래프 실행 완료", docs_found=len(result["retrieved_docs"]), answer_length=len(result["answer"]))

        # 응답 구성 (공통 로직)
        return self._build_response(result, response_time_ms)

    def invoke(self, inputs: Dict[str, Any]) -> SearchResponse:
        """그래프 동기 실행"""
        import time
        start_time = time.time()

        # 초기 상태 준비 (공통 로직)
        initial_state = self._prepare_initial_state(inputs)
        request_id = initial_state["request_id"]

        log_step(request_id, "RAG", "0", "INIT", "RAG 그래프 실행 시작 (동기)", question=inputs["question"], top_k=initial_state["top_k"])

        # 그래프 실행
        result = self.graph.invoke(initial_state)
        response_time_ms = int((time.time() - start_time) * 1000)
        log_step(request_id, "RAG", "3", "COMPLETE", "RAG 그래프 실행 완료 (동기)", docs_found=len(result["retrieved_docs"]), answer_length=len(result["answer"]))

        # 응답 구성 (공통 로직)
        return self._build_response(result, response_time_ms)

# 싱글톤 인스턴스
rag_graph = RAGGraph()

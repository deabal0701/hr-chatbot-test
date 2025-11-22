from typing import Any, Dict, List, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.config import settings
from app.models.schemas import DocumentSource, RAGResponse, SearchFilters
from app.services.vector_store import vector_store
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class RAGState(TypedDict):
    """RAG Graph 상태"""
    question: str
    filters: Dict[str, Any]
    top_k: int
    retrieved_docs: List[DocumentSource]
    answer: str
    metadata: Dict[str, Any]


class RAGGraph:
    """RAG 검색 그래프 (LangGraph)"""

    def __init__(self):
        self.llm = ChatOpenAI(
            model=settings.llm_model,
            temperature=0.1,
            api_key=settings.openai_api_key
        )

        # 그래프 구성
        self.graph = self._build_graph()

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
        top_k = state.get("top_k", settings.rag_top_k)

        # SearchFilters 객체 생성
        filters = SearchFilters(**filters_dict) if filters_dict else None

        logger.info(f"문서 검색 시작: question='{question[:50]}...', top_k={top_k}")

        # 벡터 검색
        documents = vector_store.search_similar_documents(
            query=question,
            top_k=top_k,
            filters=filters
        )

        state["retrieved_docs"] = documents
        state["metadata"] = {
            "retrieved_count": len(documents),
            "top_k": top_k
        }

        logger.info(f"문서 검색 완료: {len(documents)}개 문서 발견")
        return state

    def _generate_answer(self, state: RAGState) -> RAGState:
        """답변 생성 노드"""
        question = state["question"]
        documents = state["retrieved_docs"]

        if not documents:
            state["answer"] = "관련 문서를 찾을 수 없습니다. 다른 질문을 시도해주세요."
            return state

        # 컨텍스트 구성
        context = self._build_context(documents)

        # 시스템 프롬프트
        system_prompt = """당신은 HR 시스템 전문가입니다.
제공된 문서를 기반으로 사용자의 질문에 정확하고 친절하게 답변해주세요.

답변 시 주의사항:
1. 반드시 제공된 문서의 내용만을 기반으로 답변하세요
2. 문서에 정보가 없으면 "제공된 문서에서 해당 정보를 찾을 수 없습니다"라고 명확히 안내하세요
3. 출처를 명시하세요 (예: "재택근무 정책 문서에 따르면...")
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

        logger.info(f"LLM 답변 생성 시작: model={settings.llm_model}")

        try:
            response = self.llm.invoke(messages)
            answer = response.content

            state["answer"] = answer
            state["metadata"]["llm_model"] = settings.llm_model
            state["metadata"]["context_length"] = len(context)

            logger.info(f"LLM 답변 생성 완료: answer_length={len(answer)}")

        except Exception as e:
            logger.error(f"LLM 답변 생성 실패: {e}")
            state["answer"] = f"답변 생성 중 오류가 발생했습니다: {str(e)}"

        return state

    def _build_context(self, documents: List[DocumentSource]) -> str:
        """문서 리스트를 컨텍스트 문자열로 변환"""
        context_parts = []

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
            if current_length > settings.max_context_length:
                logger.warning(f"컨텍스트 길이 초과: {current_length} > {settings.max_context_length}")
                break

        return "\n".join(context_parts)

    async def ainvoke(self, inputs: Dict[str, Any]) -> RAGResponse:
        """그래프 비동기 실행"""
        # 초기 상태 설정
        initial_state: RAGState = {
            "question": inputs["question"],
            "filters": inputs.get("filters", {}),
            "top_k": inputs.get("top_k", settings.rag_top_k),
            "retrieved_docs": [],
            "answer": "",
            "metadata": {}
        }

        # 그래프 실행
        result = await self.graph.ainvoke(initial_state)

        # 응답 구성
        return RAGResponse(
            answer=result["answer"],
            sources=result["retrieved_docs"],
            metadata=result["metadata"]
        )

    def invoke(self, inputs: Dict[str, Any]) -> RAGResponse:
        """그래프 동기 실행"""
        # 초기 상태 설정
        initial_state: RAGState = {
            "question": inputs["question"],
            "filters": inputs.get("filters", {}),
            "top_k": inputs.get("top_k", settings.rag_top_k),
            "retrieved_docs": [],
            "answer": "",
            "metadata": {}
        }

        # 그래프 실행
        result = self.graph.invoke(initial_state)

        # 응답 구성
        return RAGResponse(
            answer=result["answer"],
            sources=result["retrieved_docs"],
            metadata=result["metadata"]
        )


# 싱글톤 인스턴스
rag_graph = RAGGraph()

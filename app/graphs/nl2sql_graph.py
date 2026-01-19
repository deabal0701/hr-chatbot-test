from typing import Any, Dict, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

from app.config import settings
from app.models.search import SearchResponse
from app.models.rag import SQLResult
import time
from app.core.database.schema_loader import schema_loader
from app.core.config.settings_service import settings_service
from app.core.llm.prompt_service import prompt_service
from app.core.database.sql_executor import SQLExecutionError, SQLValidationError, sql_executor
from app.utils.logger import setup_logger, log_step  # 통합 로깅 유틸리티
from app.core.llm.llm_config import LLMConfigManager  # Phase 1: init_chat_model 사용
from app.utils.common import strip_markdown_code_block  # 공통 유틸리티

logger = setup_logger(__name__)


class NL2SQLState(TypedDict):
    """NL2SQL Graph 상태"""
    question: str                   # 사용자 질문
    schema_description: str         # DB 스키마 설명 (LLM 제공)
    generated_sql: str
    validated: bool                 # 검증 통과 여부
    validation_error: str
    sql_result: SQLResult
    answer: str                     # 최종 답변
    metadata: Dict[str, Any]        # 메타 데이터
    request_id: str                 # 요청 추적용 ID


class NL2SQLGraph:
    """NL2SQL 검색 그래프 (LangGraph)"""

    def __init__(self):
        # 스키마 로드
        self.schema_description = schema_loader.generate_schema_description()

        # 그래프 구성 (LLM은 요청 시점에 생성)
        self.graph = self._build_graph()

    def _get_llm(self):
        """
        매 요청 시 DB 설정을 반영한 LLM 인스턴스 생성 (Phase 1: init_chat_model 적용)

        NL2SQL은 temperature=0으로 고정하여 deterministic한 SQL 생성
        """
        return LLMConfigManager.create_llm(
            temperature=0,  # SQL 생성은 deterministic하게
            # model과 provider는 DB 설정 사용
        )

    def _build_graph(self) -> StateGraph:
        """그래프 구성"""
        workflow = StateGraph(NL2SQLState)

        # 노드 추가
        workflow.add_node("generate_sql", self._generate_sql)
        workflow.add_node("validate_sql", self._validate_sql)
        workflow.add_node("execute_sql", self._execute_sql)
        workflow.add_node("generate_answer", self._generate_answer)
        workflow.add_node("handle_error", self._handle_error)

        # 엣지 정의
        workflow.set_entry_point("generate_sql")
        workflow.add_edge("generate_sql", "validate_sql")

        # 조건부 엣지: 검증 성공 여부에 따라 분기
        workflow.add_conditional_edges(
            "validate_sql",
            self._should_execute,
            {
                "execute": "execute_sql",
                "error": "handle_error"
            }
        )

        workflow.add_edge("execute_sql", "generate_answer")
        workflow.add_edge("generate_answer", END)
        workflow.add_edge("handle_error", END)

        return workflow.compile()

    def _generate_sql(self, state: NL2SQLState) -> NL2SQLState:
        """SQL 생성 노드"""
        question = state["question"]
        request_id = state.get("request_id", "unknown")

        log_step(request_id, "NL2SQL", "1", "GENERATE", "SQL 생성 시작",
                question=question[:40])

        # 시스템 프롬프트 (DB에서 동적 로드, 스키마 주입)
        system_prompt = prompt_service.get_nl2sql_generation_prompt(self.schema_description)

        user_prompt = f"""질문: {question}

위 질문에 대한 PostgreSQL SELECT 쿼리를 생성해주세요.
SQL만 출력하세요 (설명 없이)."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        # 매 요청마다 DB 설정 반영된 LLM 사용
        llm = self._get_llm()
        llm_model = settings_service.get_value("llm", "model", settings.llm_model)

        # LLM 입력 로그
        log_step(request_id, "NL2SQL", "1a", "LLM-INPUT", "LLM 호출 시작", model=llm_model, system_prompt_length=len(system_prompt), user_prompt_length=len(user_prompt))
        log_step(request_id, "NL2SQL", "1a", "LLM-INPUT", f"USER_PROMPT: {user_prompt}")

        try:
            logger.info(f"[{request_id}] [LLM-INFO] LLM Original Object : {llm}")
            logger.info(f"[{request_id}] [LLM-INFO] {type(llm).__name__}(model={llm.model_name}, temp={llm.temperature})")
            # LLM 호출 전 messages 원문 로깅
            logger.info(f"[{request_id} [NL2SQL-1a] [LLM-RAW-INPUT] Message원문 SystemMessage: {messages}")
            response = llm.invoke(messages)
            # Response 원문 로깅
            logger.info(f"[{request_id}] [NL2SQL-1b] [LLM-RAW-OUTPUT] Response원문 AIMessage: {response}")
            logger.info(f"[{request_id}] [NL2SQL-1b] [LLM-RAW-OUTPUT] Response.content: {response.content}")

            # SQL 추출 및 마크다운 코드 블록 제거
            sql = strip_markdown_code_block(response.content, language="sql")

            state["generated_sql"] = sql
            state["schema_description"] = self.schema_description
            state["metadata"] = {"llm_model": llm_model}

            # LLM 출력 로그
            log_step(request_id, "NL2SQL", "1b", "LLM-OUTPUT", "SQL 생성 완료", sql_length=len(sql))
            log_step(request_id, "NL2SQL", "1b", "LLM-OUTPUT", f"GENERATED_SQL: {sql}")

        except Exception as e:
            logger.error(f"[{request_id}] [NL2SQL-1] [LLM] SQL 생성 실패: {e}")
            state["generated_sql"] = ""
            state["validation_error"] = f"SQL 생성 오류: {str(e)}"
            state["validated"] = False

        return state

    def _validate_sql(self, state: NL2SQLState) -> NL2SQLState:
        """SQL 검증 노드"""
        sql = state["generated_sql"]
        request_id = state.get("request_id", "unknown")

        if not sql:
            log_step(request_id, "NL2SQL", "2", "VALIDATE", "검증 실패 - SQL 없음")
            state["validated"] = False
            state["validation_error"] = "생성된 SQL이 없습니다"
            return state

        log_step(request_id, "NL2SQL", "2", "VALIDATE", "SQL 검증 시작")

        try:
            is_valid, error_msg = sql_executor.validate_sql(sql)

            if is_valid:
                state["validated"] = True
                state["validation_error"] = ""
                log_step(request_id, "NL2SQL", "2", "VALIDATE", "SQL 검증 성공")
            else:
                state["validated"] = False
                state["validation_error"] = error_msg
                log_step(request_id, "NL2SQL", "2", "VALIDATE", f"SQL 검증 실패",
                        error=error_msg)

        except Exception as e:
            state["validated"] = False
            state["validation_error"] = str(e)
            logger.error(f"[{request_id}] [NL2SQL-2] [VALIDATE] SQL 검증 중 오류: {e}")

        return state

    def _should_execute(self, state: NL2SQLState) -> str:
        """조건부 엣지: 검증 성공 시 execute, 실패 시 error"""
        request_id = state.get("request_id", "unknown")
        decision = "execute" if state["validated"] else "error"
        log_step(request_id, "NL2SQL", "2x", "BRANCH", f"분기 결정 → {decision.upper()}")
        return decision

    def _execute_sql(self, state: NL2SQLState) -> NL2SQLState:
        """SQL 실행 노드"""
        sql = state["generated_sql"]
        request_id = state.get("request_id", "unknown")

        log_step(request_id, "NL2SQL", "3", "EXECUTE", "SQL 실행 시작")

        try:
            result = sql_executor.execute_sql(sql, validate=False)  # 이미 검증됨
            state["sql_result"] = result
            state["metadata"]["execution_time_ms"] = result.execution_time_ms
            state["metadata"]["row_count"] = result.row_count

            log_step(request_id, "NL2SQL", "3", "EXECUTE", "SQL 실행 완료", row_count=result.row_count, execution_time_ms=result.execution_time_ms)

        except (SQLExecutionError, SQLValidationError) as e:
            logger.error(f"[{request_id}] [NL2SQL-3] [EXECUTE] SQL 실행 실패: {e}")
            state["validation_error"] = str(e)
            state["validated"] = False

        return state

    def _generate_answer(self, state: NL2SQLState) -> NL2SQLState:
        """답변 생성 노드"""
        question = state["question"]
        sql = state["generated_sql"]
        result = state.get("sql_result")
        request_id = state.get("request_id", "unknown")

        if not result or result.row_count == 0:
            log_step(request_id, "NL2SQL", "4", "ANSWER", "결과 없음 - 기본 응답 반환")
            state["answer"] = "조회된 결과가 없습니다."
            return state

        log_step(request_id, "NL2SQL", "4", "ANSWER", "답변 생성 시작",
                row_count=result.row_count)

        # 시스템 프롬프트 (DB에서 동적 로드)
        system_prompt = prompt_service.get_nl2sql_answer_prompt()

        # 결과 데이터 요약 (너무 길면 일부만)
        rows_summary = result.rows[:10] if len(result.rows) > 10 else result.rows

        user_prompt = f"""질문: {question}

                    실행된 SQL:
                    {sql}

                    조회 결과 ({result.row_count}개 행):
                    컬럼: {', '.join(result.columns)}
                    데이터 (샘플):
                    {rows_summary}

                    위 결과를 바탕으로 질문에 대한 답변을 자연어/표/리스트등 사용자가 원하는 형태로 작성하라."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt)
        ]

        # 매 요청마다 DB 설정 반영된 LLM 사용
        llm = self._get_llm()

        # LLM 입력 로그 (답변 생성)
        log_step(request_id, "NL2SQL", "4a", "LLM-INPUT", "LLM 호출 시작 (답변 생성)",
                system_prompt_length=len(system_prompt),
                user_prompt_length=len(user_prompt),
                data_rows=len(rows_summary))
        log_step(request_id, "NL2SQL", "4a", "LLM-INPUT", f"USER_PROMPT: {user_prompt}")
        log_step(request_id, "NL2SQL", "4a", "LLM-INPUT", f"DATA_SAMPLE: {rows_summary}")

        try:
            response = llm.invoke(messages)

            # RAW 응답 로그 추가
            logger.info(f"[{request_id}] [NL2SQL-4b] [LLM-RAW-OUTPUT] Response원문 AIMessage: {response}")
            logger.info(f"[{request_id}] [NL2SQL-4b] [LLM-RAW-OUTPUT] Response.content: {response.content}")

            answer = response.content

            state["answer"] = answer
            # LLM 출력 로그 (답변 생성)
            log_step(request_id, "NL2SQL", "4b", "LLM-OUTPUT", "답변 생성 완료",
                    answer_length=len(answer))
            log_step(request_id, "NL2SQL", "4b", "LLM-OUTPUT", f"ANSWER: {answer}")

        except Exception as e:
            logger.error(f"[{request_id}] [NL2SQL-4] [LLM] 답변 생성 실패: {e}")
            state["answer"] = f"조회 결과: {result.row_count}개 행이 발견되었습니다."

        return state

    def _handle_error(self, state: NL2SQLState) -> NL2SQLState:
        """에러 처리 노드"""
        error_msg = state.get("validation_error", "알 수 없는 오류")
        request_id = state.get("request_id", "unknown")

        state["answer"] = f"""SQL 생성 또는 실행 중 오류가 발생했습니다.

오류 내용: {error_msg}

다음 사항을 확인해주세요:
1. 질문이 데이터베이스 스키마에 맞는지 확인
2. 테이블명과 컬럼명이 정확한지 확인
3. 질문을 더 구체적으로 작성
"""

        log_step(request_id, "NL2SQL", "ERR", "ERROR", f"오류 처리 완료", error=error_msg)
        return state

    def _prepare_initial_state(self, inputs: Dict[str, Any]) -> NL2SQLState:
        """초기 상태 준비 (ainvoke와 invoke 공통 로직)"""
        return {
            "question": inputs["question"],
            "schema_description": "",
            "generated_sql": "",
            "validated": False,
            "validation_error": "",
            "sql_result": None,
            "answer": "",
            "metadata": {},
            "request_id": inputs.get("request_id", "unknown")
        }

    def _build_response(self, result: NL2SQLState, response_time_ms: int = 0) -> SearchResponse:
        """실행 결과를 SearchResponse로 변환"""
        return SearchResponse(
            query=result["question"],
            answer=result["answer"],
            query_type="nl2sql",
            response_time_ms=response_time_ms,
            sql=result["generated_sql"],
            sql_result=result.get("sql_result"),
            sources=None,
            metadata=result["metadata"]
        )

    async def ainvoke(self, inputs: Dict[str, Any]) -> SearchResponse:
        """그래프 비동기 실행"""
        start_time = time.time()

        # 초기 상태 준비 (공통 로직)
        initial_state = self._prepare_initial_state(inputs)
        request_id = initial_state["request_id"]

        log_step(request_id, "NL2SQL", "0", "INIT", "NL2SQL 그래프 실행 시작", question=inputs["question"])

        result = await self.graph.ainvoke(initial_state)

        response_time_ms = int((time.time() - start_time) * 1000)

        log_step(request_id, "NL2SQL", "5", "COMPLETE", "NL2SQL 그래프 실행 완료", has_sql=bool(result["generated_sql"]), answer_length=len(result["answer"]))

        # 응답 구성 (공통 로직)
        return self._build_response(result, response_time_ms)


# 싱글톤 인스턴스
nl2sql_graph = NL2SQLGraph()

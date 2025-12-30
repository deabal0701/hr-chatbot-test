from typing import Any, Dict, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, StateGraph

from app.config import settings
from app.models.schemas import NL2SQLResponse, SQLResult
from app.services.schema_loader import schema_loader
from app.services.settings_service import settings_service
from app.services.sql_executor import SQLExecutionError, SQLValidationError, sql_executor
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_llm_settings():
    """DB 설정에서 LLM 관련 설정 가져오기 (DB → 환경변수 → 기본값)"""
    return {
        "api_key": settings_service.get_value("openai", "api_key", settings.openai_api_key),
        "model": settings_service.get_value("llm", "model", settings.llm_model),
    }


def log_nl2sql_step(request_id: str, step: str, stage: str, message: str, **kwargs):
    """NL2SQL 그래프 단계별 로그 출력 헬퍼"""
    extra_info = " | ".join([f"{k}={v}" for k, v in kwargs.items()]) if kwargs else ""
    logger.info(f"[{request_id}] [NL2SQL-{step}] [{stage}] {message}" + (f" | {extra_info}" if extra_info else ""))


def truncate_text(text: str, max_length: int = 100000) -> str:
    """텍스트를 지정된 길이로 자르고 truncated 표시 (기본값 100000 = 거의 전체 출력)"""
    if not text:
        return ""
    text = text.replace("\n", " ").strip()
    if len(text) <= max_length:
        return text
    return text[:max_length] + "...[truncated]"


class NL2SQLState(TypedDict):
    """NL2SQL Graph 상태"""
    question: str                   # 사용자 질문
    schema_description: str         # DB 스키마 설명 (LLM 제공)
    generated_sql: str
    validated: bool                 # 검증 통과 여부
    validation_error: str
    sql_result: SQLResult
    answer: str                     # 죄종 답변
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
        """매 요청 시 DB 설정을 반영한 LLM 인스턴스 생성"""
        llm_settings = get_llm_settings()
        return ChatOpenAI(
            model=llm_settings["model"],
            temperature=0,  # SQL 생성은 deterministic하게
            api_key=llm_settings["api_key"]
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

        log_nl2sql_step(request_id, "1", "GENERATE", "SQL 생성 시작",
                        question=question[:40])

        # 시스템 프롬프트
        system_prompt = f"""당신은 PostgreSQL 전문가입니다.
사용자의 자연어 질문을 PostgreSQL SQL 쿼리로 변환해주세요.

# 데이터베이스 스키마
{self.schema_description}

# 중요한 규칙
1. **반드시 SELECT 문만 생성하세요** (INSERT, UPDATE, DELETE, DROP 등은 절대 사용 금지)
2. **테이블명과 컬럼명은 정확하게 사용하세요**
3. **WHERE 절을 적절히 사용하여 결과를 필터링하세요**
4. **집계 함수 사용 시 GROUP BY를 정확히 지정하세요**
5. **날짜 비교 시 적절한 형변환을 사용하세요**
6. **JOIN 시 명확한 조인 조건을 지정하세요**
7. **SQL만 출력하고, 설명이나 마크다운 코드 블록은 포함하지 마세요**

# 사용자 의도 파악 규칙
- "표로 보여줘", "목록으로", "리스트로", "상세 정보" 등의 표현이 있으면 **개별 데이터를 조회**하세요 (COUNT 사용 금지)
- "몇 명", "총 수", "개수" 등의 표현이 있을 때만 COUNT를 사용하세요
- 이미 특정 수치("27명", "10건" 등)를 언급한 경우, 해당 데이터의 **상세 내용**을 원하는 것입니다 (COUNT 사용 금지)
- 불확실한 경우, 상세 데이터를 조회하는 것이 더 유용합니다

# LIMIT 사용 규칙 (조건부 적용)
- **COUNT, SUM, AVG, MAX, MIN 등 집계 함수 사용 시**: LIMIT 절 사용 금지
- **GROUP BY 사용 시**: LIMIT 절 사용 금지 (모든 그룹 결과 필요)
- **개별 데이터 조회 시**: LIMIT 1000 사용 (대용량 방지)
- 사용자가 "상위 5개만", "10개만 보여줘" 등 명시적으로 제한을 요청한 경우에만 해당 숫자를 LIMIT에 사용

# 한국어 필드 매핑
- "입사일" = hire_date
- "직급" = position (사원, 대리, 과장, 차장, 부장)
- "직무" = job_family (개발, 기획, 디자인, HR, 마케팅, 영업)
- "부서" = department (department 테이블과 조인 필요)
- "근무지" = work_location
- "재직상태" = status (active, resigned, on_leave)
"""

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
        log_nl2sql_step(request_id, "1a", "LLM-INPUT", "LLM 호출 시작", model=llm_model, system_prompt_length=len(system_prompt), user_prompt_length=len(user_prompt))
        log_nl2sql_step(request_id, "1a", "LLM-INPUT", f"USER_PROMPT: {truncate_text(user_prompt)}")

        try:
            logger.info(f"[{request_id}] [LLM-INFO] LLM Original Object : {llm}")
            logger.info(f"[{request_id}] [LLM-INFO] {type(llm).__name__}(model={llm.model_name}, temp={llm.temperature})")
            # LLM 호출 전 messages 원문 로깅
            logger.info(f"[{request_id} [NL2SQL-1a] [LLM-RAW-INPUT] Message원문: {messages}")
            response = llm.invoke(messages)
            # Response 원문 로깅
            logger.info(f"[{request_id}] [NL2SQL-1b] [LLM-RAW-OUTPUT] Response 원문: {response}")
            logger.info(f"[{request_id}] [NL2SQL-1b] [LLM-RAW-OUTPUT] Response.content: {response.content}")
            
            sql = response.content.strip()

            # 마크다운 코드 블록 제거 (```sql ... ```)
            if sql.startswith("```"):
                lines = sql.split("\n")
                sql = "\n".join(lines[1:-1]) if len(lines) > 2 else sql
                sql = sql.replace("```sql", "").replace("```", "").strip()

            state["generated_sql"] = sql
            state["schema_description"] = self.schema_description
            state["metadata"] = {"llm_model": llm_model}

            # LLM 출력 로그
            log_nl2sql_step(request_id, "1b", "LLM-OUTPUT", "SQL 생성 완료",
                            sql_length=len(sql))
            log_nl2sql_step(request_id, "1b", "LLM-OUTPUT", f"GENERATED_SQL: {truncate_text(sql)}")

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
            log_nl2sql_step(request_id, "2", "VALIDATE", "검증 실패 - SQL 없음")
            state["validated"] = False
            state["validation_error"] = "생성된 SQL이 없습니다"
            return state

        log_nl2sql_step(request_id, "2", "VALIDATE", "SQL 검증 시작")

        try:
            is_valid, error_msg = sql_executor.validate_sql(sql)

            if is_valid:
                state["validated"] = True
                state["validation_error"] = ""
                log_nl2sql_step(request_id, "2", "VALIDATE", "SQL 검증 성공")
            else:
                state["validated"] = False
                state["validation_error"] = error_msg
                log_nl2sql_step(request_id, "2", "VALIDATE", f"SQL 검증 실패",
                                error=error_msg[:50])

        except Exception as e:
            state["validated"] = False
            state["validation_error"] = str(e)
            logger.error(f"[{request_id}] [NL2SQL-2] [VALIDATE] SQL 검증 중 오류: {e}")

        return state

    def _should_execute(self, state: NL2SQLState) -> str:
        """조건부 엣지: 검증 성공 시 execute, 실패 시 error"""
        request_id = state.get("request_id", "unknown")
        decision = "execute" if state["validated"] else "error"
        log_nl2sql_step(request_id, "2x", "BRANCH", f"분기 결정 → {decision.upper()}")
        return decision

    def _execute_sql(self, state: NL2SQLState) -> NL2SQLState:
        """SQL 실행 노드"""
        sql = state["generated_sql"]
        request_id = state.get("request_id", "unknown")

        log_nl2sql_step(request_id, "3", "EXECUTE", "SQL 실행 시작")

        try:
            result = sql_executor.execute_sql(sql, validate=False)  # 이미 검증됨
            state["sql_result"] = result
            state["metadata"]["execution_time_ms"] = result.execution_time_ms
            state["metadata"]["row_count"] = result.row_count

            log_nl2sql_step(request_id, "3", "EXECUTE", "SQL 실행 완료",
                            row_count=result.row_count,
                            execution_time_ms=result.execution_time_ms)

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
            log_nl2sql_step(request_id, "4", "ANSWER", "결과 없음 - 기본 응답 반환")
            state["answer"] = "조회된 결과가 없습니다."
            return state

        log_nl2sql_step(request_id, "4", "ANSWER", "답변 생성 시작",
                        row_count=result.row_count)

        # 시스템 프롬프트
        system_prompt = """당신은 데이터 분석 전문가입니다.
                    SQL 쿼리 결과를 사용자가 이해하기 쉽게 자연어로 요약해주세요.

                    답변 작성 시:
                    1. 핵심 통계나 수치를 강조하세요
                    2. 결과를 명확하고 간결하게 설명하세요
                    3. 필요시 불릿 포인트를 사용하세요
                    4. 데이터에서 발견되는 인사이트나 특징을 언급하세요
                    """

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
        log_nl2sql_step(request_id, "4a", "LLM-INPUT", "LLM 호출 시작 (답변 생성)",
                        system_prompt_length=len(system_prompt),
                        user_prompt_length=len(user_prompt),
                        data_rows=len(rows_summary))
        log_nl2sql_step(request_id, "4a", "LLM-INPUT", f"USER_PROMPT: {truncate_text(user_prompt)}")
        log_nl2sql_step(request_id, "4a", "LLM-INPUT", f"DATA_SAMPLE: {truncate_text(str(rows_summary))}")

        try:
            response = llm.invoke(messages)
            answer = response.content

            state["answer"] = answer
            # LLM 출력 로그 (답변 생성)
            log_nl2sql_step(request_id, "4b", "LLM-OUTPUT", "답변 생성 완료",
                            answer_length=len(answer))
            log_nl2sql_step(request_id, "4b", "LLM-OUTPUT", f"ANSWER: {truncate_text(answer)}")

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

        log_nl2sql_step(request_id, "ERR", "ERROR", f"오류 처리 완료",
                        error=error_msg[:50])
        return state

    async def ainvoke(self, inputs: Dict[str, Any]) -> NL2SQLResponse:
        """그래프 비동기 실행"""
        request_id = inputs.get("request_id", "unknown")

        initial_state: NL2SQLState = {
            "question": inputs["question"],
            "schema_description": "",
            "generated_sql": "",
            "validated": False,
            "validation_error": "",
            "sql_result": None,
            "answer": "",
            "metadata": {},
            "request_id": request_id
        }

        log_nl2sql_step(request_id, "0", "INIT", "NL2SQL 그래프 실행 시작",
                        question=inputs["question"][:40])

        result = await self.graph.ainvoke(initial_state)

        log_nl2sql_step(request_id, "5", "COMPLETE", "NL2SQL 그래프 실행 완료",
                        has_sql=bool(result["generated_sql"]),
                        answer_length=len(result["answer"]))

        return NL2SQLResponse(
            answer=result["answer"],
            sql=result["generated_sql"],
            result=result.get("sql_result"),
            metadata=result["metadata"]
        )

    def invoke(self, inputs: Dict[str, Any]) -> NL2SQLResponse:
        """그래프 동기 실행"""
        request_id = inputs.get("request_id", "unknown")

        initial_state: NL2SQLState = {
            "question": inputs["question"],
            "schema_description": "",
            "generated_sql": "",
            "validated": False,
            "validation_error": "",
            "sql_result": None,
            "answer": "",
            "metadata": {},
            "request_id": request_id
        }

        log_nl2sql_step(request_id, "0", "INIT", "NL2SQL 그래프 실행 시작 (동기)",
                        question=inputs["question"][:40])

        result = self.graph.invoke(initial_state)

        log_nl2sql_step(request_id, "5", "COMPLETE", "NL2SQL 그래프 실행 완료 (동기)",
                        has_sql=bool(result["generated_sql"]),
                        answer_length=len(result["answer"]))

        return NL2SQLResponse(
            answer=result["answer"],
            sql=result["generated_sql"],
            result=result.get("sql_result"),
            metadata=result["metadata"]
        )


# 싱글톤 인스턴스
nl2sql_graph = NL2SQLGraph()

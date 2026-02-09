"""
NL2SQL 노드 (NL2SQL Nodes)

기능:
- 스키마 검색 (schema_retrieval_node)
- Few-shot 예제 검색 (fewshot_retrieval_node)
- 프롬프트 빌드 (prompt_build_node)
- SQL 생성 (sql_generate_node)
- SQL 검증 (validate_sql_node)
- SQL 실행 (execute_sql_node)
- 답변 생성 (generate_answer_node)
- 에러 처리 (handle_error_node)
- 분기 판단 (should_execute, should_continue_after_execute)

사용:
- NL2SQLGraph 클래스의 노드로 사용
- schema_retrieval → fewshot_retrieval → prompt_build → sql_generate → validate_sql → should_execute 분기
  - execute → execute_sql → generate_answer
  - retry → fewshot_retrieval (enhanced mode)
  - error → handle_error
"""
from typing import Dict, Any
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.config import settings
from app.core.llm.llm_config import LLMConfigManager
from app.core.llm.prompt_service import prompt_service
from app.core.database.sql_executor import SQLExecutionError, SQLValidationError, sql_executor
from app.utils.logger import setup_logger, log_step
from app.utils.common import truncate_text

logger = setup_logger(__name__)


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

    NL2SQL은 temperature=0으로 고정하여 deterministic한 SQL 생성
    """
    return LLMConfigManager.create_llm(temperature=0)


def _get_lightweight_llm():
    """
    테이블 선택용 경량 LLM 인스턴스 생성

    schema_retrieval_node에서 사용 (비용 절감)

    필요시 경량 LLM을 사용할 수 있음.(현재는 동일 LLM을 사용하도록 처리함.)
    """
    settings_config = _get_settings_config()
    model = settings_config.get_value("nl2sql", "schema_retrieval_model", "gpt-4.1-nano")
    return LLMConfigManager.create_llm(temperature=0, model=model)


def _get_table_catalog_service():
    """table_catalog_service 지연 로드"""
    from app.core.database.table_catalog import table_catalog_service
    return table_catalog_service


def _get_schema_loader():
    """schema_loader 지연 로드"""
    from app.core.database.schema_loader import schema_loader
    return schema_loader


# =============================================================================
# schema_retrieval_node
# =============================================================================

def schema_retrieval_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    스키마 검색 노드 (Schema Retrieval Node)

    질문을 분석하여 필요한 테이블을 선택하고,
    해당 테이블의 스키마만 로드합니다.

    처리 흐름:
    1. 테이블 카탈로그 조회 (이름 + 설명 + 컬럼)
    2. 경량 LLM으로 관련 테이블 선택 (JSON 응답)
    3. FK 관계 테이블 자동 포함
    4. 선택된 테이블 스키마만 로드
    5. 신뢰도 낮으면 전체 스키마 fallback

    Args:
        state: NL2SQLState

    Returns:
        updated state with:
        - selected_tables: List[str]
        - schema_retrieval_confidence: float
        - schema_description: str
    """
    # 재작성된 질문이 있으면 사용 (멀티턴 대화에서 컨텍스트 반영된 완전한 질문)
    rewritten_question = state.get("rewritten_question", "")
    original_question = state["question"]
    question = rewritten_question if rewritten_question else original_question
    request_id = state.get("request_id", "unknown")

    log_step(logger, request_id, "NL2SQL", "0.5", "SCHEMA-RETRIEVAL", "스키마 검색 시작", question=truncate_text(question, 40), is_rewritten=bool(rewritten_question))

    # 설정 조회
    settings_config = _get_settings_config()
    enabled = settings_config.get_value("nl2sql", "schema_retrieval_enabled", True)
    confidence_threshold = settings_config.get_value("nl2sql", "schema_retrieval_confidence_threshold", 0.7)

    # 비활성화된 경우 전체 스키마 사용
    if not enabled:
        log_step(logger, request_id, "NL2SQL", "0.5", "SCHEMA-RETRIEVAL", "스키마 검색 비활성화 → 전체 스키마 사용")
        schema_loader = _get_schema_loader()
        return {
            "selected_tables": [],
            "schema_retrieval_confidence": 1.0,
            "schema_description": schema_loader.generate_schema_description(),
        }

    try:
        # 1. 테이블 카탈로그 조회
        catalog_service = _get_table_catalog_service()
        table_summary = catalog_service.get_table_summary_for_llm()

        # 2. 경량 LLM으로 테이블 선택
        llm = _get_lightweight_llm()

        system_prompt = """당신은 SQL 전문가입니다.
사용자 질문에 필요한 테이블을 선택하세요.

{table_summary}

## 응답 형식 (반드시 JSON으로)
{{"tables": ["테이블1", "테이블2"], "reasoning": "선택 이유", "confidence": 0.9}}

## 규칙
- 필요한 테이블만 선택 (최소한으로)
- v_ai_employee는 대부분의 질문에 필요합니다
- 1:N 관계 테이블 조인 시 v_ai_employee 포함 필수
- confidence: 확신도 (0.0~1.0)
"""

        user_prompt = f"질문: {question}\n\n위 질문에 필요한 테이블을 JSON 형식으로 응답하세요."

        messages = [
            SystemMessage(content=system_prompt.format(table_summary=table_summary)),
            HumanMessage(content=user_prompt)
        ]

        log_step(logger, request_id, "NL2SQL", "0.5a", "LLM-INPUT", "경량 LLM 호출 (테이블 선택)")

        response = llm.invoke(messages)

        # response.content가 list일 수 있음 (일부 모델)
        content = response.content
        if isinstance(content, list):
            response_text = " ".join(str(item) for item in content).strip()
        else:
            response_text = str(content).strip()

        log_step(logger, request_id, "NL2SQL", "0.5b", "LLM-OUTPUT", "LLM 응답 수신", response_length=len(response_text))

        # 3. JSON 파싱
        import json
        import re

        # JSON 블록 추출 (```json ... ``` 또는 { ... })
        json_match = re.search(r'\{[^{}]*"tables"[^{}]*\}', response_text, re.DOTALL)
        if json_match:
            json_str = json_match.group()
        else:
            # 전체 응답이 JSON인 경우
            json_str = response_text

        try:
            result = json.loads(json_str)
            selected_tables = result.get("tables", [])
            confidence = float(result.get("confidence", 0.5))
            # LLM 응답의 불필요한 줄바꿈/공백 정리
            reasoning = " ".join(result.get("reasoning", "").split())
        except json.JSONDecodeError as e:
            log_step(logger, request_id, "NL2SQL", "0.5", "WARN", f"JSON 파싱 실패: {e} → 전체 스키마 사용")
            schema_loader = _get_schema_loader()
            return {
                "selected_tables": [],
                "schema_retrieval_confidence": 0.0,
                "schema_description": schema_loader.generate_schema_description(),
            }

        # 4. FK 관계 테이블 자동 포함
        all_tables = catalog_service.get_related_tables(selected_tables)

        log_step(logger, request_id, "NL2SQL", "0.5", "SCHEMA-RETRIEVAL", "테이블 선택 완료", tables=list(all_tables), confidence=confidence, reasoning=truncate_text(reasoning, 50))

        # 5. 신뢰도 체크 (낮으면 전체 스키마)
        schema_loader = _get_schema_loader()

        if confidence < confidence_threshold:
            log_step(logger, request_id, "NL2SQL", "0.5", "SCHEMA-RETRIEVAL", "신뢰도 낮음 → 전체 스키마 사용", confidence=confidence, threshold=confidence_threshold)
            return {
                "selected_tables": [],
                "schema_retrieval_confidence": confidence,
                "schema_description": schema_loader.generate_schema_description(),
            }

        # 6. 선택된 테이블 스키마만 로드
        schema_description = schema_loader.generate_schema_description(tables=list(all_tables))

        log_step(logger, request_id, "NL2SQL", "0.5", "SCHEMA-RETRIEVAL", "선택적 스키마 로드 완료", table_count=len(all_tables), schema_length=len(schema_description))

        return {
            "selected_tables": list(all_tables),
            "schema_retrieval_confidence": confidence,
            "schema_description": schema_description,
        }

    except Exception as e:
        log_step(logger, request_id, "NL2SQL", "0.5", "ERROR", f"스키마 검색 실패: {e} → 전체 스키마 사용", level="ERROR")
        schema_loader = _get_schema_loader()
        return {
            "selected_tables": [],
            "schema_retrieval_confidence": 0.0,
            "schema_description": schema_loader.generate_schema_description(),
        }


# =============================================================================
# fewshot_retrieval_node
# =============================================================================


def fewshot_retrieval_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Few-shot 예제 검색 노드

    Vector Store에서 유사한 쿼리 예제를 검색하여
    SQL 생성 시 참조할 수 있는 컨텍스트를 제공합니다.

    처리 흐름:
    1. Vector Store에서 usage_type='rag_action', doc_type='query_example' 검색
    2. 예제를 프롬프트 형식으로 포맷팅
    3. enhanced_fewshot=True인 경우 top_k를 2배로 증가 (재시도 시)

    Args:
        state: NL2SQLState

    Returns:
        updated state with:
        - fewshot_context: str (포맷된 Few-shot 예제)
        - fewshot_examples: List[Dict] (원본 예제 데이터)
        - fewshot_count: int (검색된 예제 수)
    """
    # 재작성된 질문이 있으면 사용 (멀티턴 대화에서 컨텍스트 반영된 완전한 질문)
    rewritten_question = state.get("rewritten_question", "")
    original_question = state["question"]
    question = rewritten_question if rewritten_question else original_question
    request_id = state.get("request_id", "unknown")
    enhanced_fewshot = state.get("enhanced_fewshot", False)

    log_step(logger, request_id, "NL2SQL", "0.6", "FEWSHOT", "Few-shot 검색 시작", question=truncate_text(question, 40), enhanced=enhanced_fewshot, is_rewritten=bool(rewritten_question))

    # 설정 조회
    settings_config = _get_settings_config()
    enabled = settings_config.get_value("nl2sql", "fewshot_enabled", True)
    base_top_k = settings_config.get_value("nl2sql", "fewshot_top_k", 3)
    similarity_threshold = settings_config.get_value("nl2sql", "fewshot_similarity_threshold", 0.3)

    # 비활성화된 경우
    if not enabled:
        log_step(logger, request_id, "NL2SQL", "0.6", "FEWSHOT", "Few-shot 비활성화")
        return {
            "fewshot_context": "",
            "fewshot_examples": [],
            "fewshot_count": 0,
        }

    try:
        from app.core.vector.vector_store import vector_store
        from app.models.search import SearchFilters

        # Enhanced 모드: 재시도 시 top_k 2배
        top_k = base_top_k * 2 if enhanced_fewshot else base_top_k

        # Few-shot 예제 검색
        example_docs = vector_store.search_similar_documents(
            query=question,
            filters=SearchFilters(usage_type="rag_action", doc_type="query_example"),
            top_k=top_k,
            similarity_threshold=similarity_threshold
        )

        if not example_docs:
            log_step(logger, request_id, "NL2SQL", "0.6", "FEWSHOT", "Few-shot 예제 없음")
            return {
                "fewshot_context": "",
                "fewshot_examples": [],
                "fewshot_count": 0,
            }

        # 예제를 프롬프트 형식으로 포맷팅
        fewshot_lines = ["## 유사 쿼리 예제 (Few-shot)\n"]
        fewshot_examples = []

        for i, doc in enumerate(example_docs, 1):
            fewshot_lines.append(f"### 예제 {i}: {doc.title}")
            fewshot_lines.append(f"질문: {doc.content}")
            if doc.context_data:
                # context_data에 SQL이 포함되어 있음
                fewshot_lines.append(doc.context_data)
            fewshot_lines.append("")

            fewshot_examples.append({
                "title": doc.title,
                "question": doc.content,
                "sql": doc.context_data,
                "similarity": doc.similarity_score
            })

        fewshot_context = "\n".join(fewshot_lines)

        log_step(logger, request_id, "NL2SQL", "0.6", "FEWSHOT", "Few-shot 검색 완료", count=len(example_docs), enhanced=enhanced_fewshot)

        return {
            "fewshot_context": fewshot_context,
            "fewshot_examples": fewshot_examples,
            "fewshot_count": len(example_docs),
        }

    except Exception as e:
        log_step(logger, request_id, "NL2SQL", "0.6", "ERROR", f"Few-shot 검색 실패: {e}", level="ERROR")
        return {
            "fewshot_context": "",
            "fewshot_examples": [],
            "fewshot_count": 0,
        }


# =============================================================================
# prompt_build_node
# =============================================================================


def prompt_build_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    프롬프트 빌드 노드

    스키마, Few-shot 예제, DB 가이드라인을 조합하여
    완성된 SQL 생성 프롬프트를 구성합니다.

    단일 책임: 프롬프트 조립만 수행, LLM 호출 없음

    처리 흐름:
    1. Base 프롬프트 로드 (prompt_service)
    2. 스키마 정보 주입
    3. Few-shot 예제 추가
    4. 재시도 시 이전 오류 컨텍스트 추가

    Args:
        state: NL2SQLState

    Returns:
        updated state with:
        - sql_prompt: str (완성된 System Prompt)
        - user_prompt: str (User Prompt)
        - prompt_metadata: Dict (프롬프트 메타데이터)
    """
    # 재작성된 질문이 있으면 사용 (멀티턴 대화에서 컨텍스트 반영된 완전한 질문)
    rewritten_question = state.get("rewritten_question", "")
    original_question = state["question"]
    question = rewritten_question if rewritten_question else original_question
    request_id = state.get("request_id", "unknown")
    schema_description = state.get("schema_description", "")
    fewshot_context = state.get("fewshot_context", "")
    previous_error = state.get("previous_error", "")
    retry_count = state.get("retry_count", 0)

    log_step(logger, request_id, "NL2SQL", "0.7", "PROMPT", "프롬프트 조립 시작", schema_len=len(schema_description), fewshot_len=len(fewshot_context), is_rewritten=bool(rewritten_question))

    try:
        # DB 타입 및 SQL 방언 확인
        from app.core.database.external import external_db_manager
        db_type = external_db_manager.get_db_type()
        adapter = external_db_manager.get_adapter()
        sql_dialect = adapter.get_sql_dialect_name()

        # Base 프롬프트 로드 (prompt_service)
        base_prompt = prompt_service.get_nl2sql_generation_prompt(schema_description, db_type)

        # 프롬프트 조립
        prompt_parts = [base_prompt]

        # Few-shot 예제 추가
        if fewshot_context:
            prompt_parts.append("\n---\n")
            prompt_parts.append(fewshot_context)

        # 이전 대화 이력 컨텍스트 추가 (멀티턴 대화)
        conversation_history = state.get("conversation_history", [])
        if conversation_history:
            history_context = "\n---\n## 이전 대화 이력 (중요: 후속 질문 참조용)\n"
            history_context += """**반드시 아래 규칙을 따르세요:**
1. 사용자가 "그 중에서", "위 결과에서", "거기서", "그것들 중", "해당", "이전" 등의 표현을 사용하면 **이전 SQL의 조건을 유지**하고 추가 조건만 적용하세요.
2. 후속 질문은 이전 질문의 **결과 집합을 기반**으로 합니다. 이전 SQL의 WHERE 조건을 포함해야 합니다.
3. 예시: 이전="2024년 입사자 수" → 후속="그 중 개발부서" → SQL에 `2024년 입사 조건 AND 개발부서 조건` 모두 포함

"""
            for i, turn in enumerate(conversation_history, 1):
                # 답변은 200자로 요약 (토큰 절약)
                answer_summary = turn.get('answer', '')
                if len(answer_summary) > 200:
                    answer_summary = answer_summary[:200] + "..."
                history_context += f"""### 대화 {i}
- **질문**: {turn.get('question', '')}
- **SQL**: `{turn.get('sql', '')}`
- **답변 요약**: {answer_summary}

"""
            prompt_parts.append(history_context)
            log_step(logger, request_id, "NL2SQL", "0.7", "PROMPT", "이전 대화 이력 추가", turns=len(conversation_history))

        # 재시도 시 이전 오류 컨텍스트 추가
        if retry_count > 0 and previous_error:
            error_context = f"""
---
## 이전 시도 오류 (재시도 #{retry_count})
이전 SQL 생성 시 다음 오류가 발생했습니다. 이 오류를 피해 SQL을 생성하세요:
```
{previous_error}
```
"""
            prompt_parts.append(error_context)

        sql_prompt = "".join(prompt_parts)

        # User Prompt 구성
        user_prompt = f"""질문: {question}

위 질문에 대한 {sql_dialect} SELECT 쿼리를 생성해주세요.
SQL만 출력하세요 (설명 없이)."""

        prompt_metadata = {
            "db_type": db_type,
            "sql_dialect": sql_dialect,
            "schema_length": len(schema_description),
            "fewshot_length": len(fewshot_context),
            "fewshot_count": state.get("fewshot_count", 0),
            "has_error_context": retry_count > 0,
            "retry_count": retry_count,
            "total_prompt_length": len(sql_prompt),
            # 멀티턴 대화 메타데이터
            "current_turn": state.get("current_turn", 1),
            "max_turns": state.get("max_turns", 5),
            "history_turns": len(conversation_history),
        }

        log_step(logger, request_id, "NL2SQL", "0.7", "PROMPT", "프롬프트 조립 완료", total_len=len(sql_prompt), db=db_type, retry=retry_count)

        return {
            "sql_prompt": sql_prompt,
            "user_prompt": user_prompt,
            "prompt_metadata": prompt_metadata,
        }

    except Exception as e:
        log_step(logger, request_id, "NL2SQL", "0.7", "ERROR", f"프롬프트 조립 실패: {e}", level="ERROR")
        return {
            "sql_prompt": "",
            "user_prompt": question,
            "prompt_metadata": {"error": str(e)},
        }


# =============================================================================
# sql_generate_node (LLM 호출만)
# =============================================================================


def sql_generate_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    SQL 생성 노드

    prompt_build_node에서 준비된 프롬프트로 LLM을 호출하여 SQL을 생성합니다.

    단일 책임: LLM 호출 및 응답 처리만 수행
    - 스키마 로드: schema_retrieval_node에서 수행
    - Few-shot 검색: fewshot_retrieval_node에서 수행
    - 프롬프트 빌드: prompt_build_node에서 수행

    Args:
        state: NL2SQLState

    Returns:
        updated state with:
        - generated_sql: str
        - metadata: Dict
    """
    request_id = state.get("request_id", "unknown")
    sql_prompt = state.get("sql_prompt", "")
    user_prompt = state.get("user_prompt", "")
    prompt_metadata = state.get("prompt_metadata", {})

    log_step(logger, request_id, "NL2SQL", "1", "GENERATE", "SQL 생성 시작 (LLM 호출)")

    # 프롬프트 존재 확인
    if not sql_prompt or not user_prompt:
        log_step(logger, request_id, "NL2SQL", "1", "ERROR", "프롬프트 없음 - prompt_build_node 실패", level="ERROR")
        return {
            "generated_sql": "",
            "validated": False,
            "validation_error": "프롬프트 구성 실패",
            "metadata": prompt_metadata,
        }

    try:
        from app.utils.common import strip_markdown_code_block

        # LLM 인스턴스 생성
        llm = _get_llm()

        messages = [
            SystemMessage(content=sql_prompt),
            HumanMessage(content=user_prompt)
        ]

        # 모델 정보 조회
        settings_config = _get_settings_config()
        llm_model = settings_config.get_value("llm", "model", settings.llm_model)

        log_step(logger, request_id, "NL2SQL", "1a", "LLM-INPUT", "LLM 호출 시작", model=llm_model, system_len=len(sql_prompt), user_len=len(user_prompt))

        if logger.isEnabledFor(logging.DEBUG):
            log_step(logger, request_id, "NL2SQL", "1a", "LLM-INPUT", "SYSTEM_PROMPT", level="DEBUG", content=sql_prompt)
            log_step(logger, request_id, "NL2SQL", "1a", "LLM-INPUT", "USER_PROMPT", level="DEBUG", content=user_prompt)

        # LLM 호출
        response = llm.invoke(messages)

        # response.content가 list일 수 있음 (일부 모델)
        content = response.content
        if isinstance(content, list):
            response_text = " ".join(str(item) for item in content).strip()
        else:
            response_text = str(content).strip()

        if logger.isEnabledFor(logging.DEBUG):
            log_step(logger, request_id, "NL2SQL", "1b", "LLM-OUTPUT", "LLM_RESPONSE", level="DEBUG", content=response_text)

        # 마크다운 코드 블록 제거
        sql = strip_markdown_code_block(response_text, language="sql")

        # 메타데이터 구성
        metadata = {
            **prompt_metadata,
            "llm_model": llm_model,
            "sql_length": len(sql),
        }

        log_step(logger, request_id, "NL2SQL", "1b", "LLM-OUTPUT", "SQL 생성 완료", sql_length=len(sql))

        if logger.isEnabledFor(logging.DEBUG):
            log_step(logger, request_id, "NL2SQL", "1b", "SQL", "생성된 SQL", level="DEBUG", content=sql)

        return {
            "generated_sql": sql,
            "metadata": metadata,
        }

    except Exception as e:
        log_step(logger, request_id, "NL2SQL", "1", "ERROR", f"SQL 생성 실패: {e}", level="ERROR")
        return {
            "generated_sql": "",
            "validated": False,
            "validation_error": f"SQL 생성 오류: {str(e)}",
            "metadata": {**prompt_metadata, "error": str(e)},
        }

def validate_sql_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    SQL 검증 노드

    생성된 SQL의 안전성과 유효성을 검증합니다.

    Args:
        state: NL2SQLState (Dict 형태로 전달)

    Returns:
        업데이트된 state (validated, validation_error 필드 채움)
    """
    sql = state["generated_sql"]
    request_id = state.get("request_id", "unknown")

    if not sql:
        log_step(logger, request_id, "NL2SQL", "2", "VALIDATE", "검증 실패 - SQL 없음")
        state["validated"] = False
        state["validation_error"] = "생성된 SQL이 없습니다"
        return state

    log_step(logger, request_id, "NL2SQL", "2", "VALIDATE", "SQL 검증 시작")

    try:
        is_valid, error_msg = sql_executor.validate_sql(sql)

        if is_valid:
            state["validated"] = True
            state["validation_error"] = ""
            log_step(logger, request_id, "NL2SQL", "2", "VALIDATE", "SQL 검증 성공")
        else:
            state["validated"] = False
            state["validation_error"] = error_msg
            log_step(logger, request_id, "NL2SQL", "2", "VALIDATE", "SQL 검증 실패", error=error_msg)

    except Exception as e:
        state["validated"] = False
        state["validation_error"] = str(e)
        log_step(logger, request_id, "NL2SQL", "2", "ERROR", f"SQL 검증 중 오류: {e}", level="ERROR")

    return state


def should_execute(state: Dict[str, Any]) -> str:
    """
    조건부 분기 함수 (재시도 지원)

    SQL 검증 성공 여부에 따라 다음 노드를 결정합니다.
    검증 실패 시 재시도 가능 여부를 확인하여 분기합니다.

    Args:
        state: NL2SQLState

    Returns:
        "execute" - 검증 성공, SQL 실행
        "retry" - 재시도 가능, enhanced fewshot으로 다시 시도
        "error" - 최대 재시도 초과 또는 치명적 오류
    """
    request_id = state.get("request_id", "unknown")
    validated = state.get("validated", False)
    retry_count = state.get("retry_count", 0)
    validation_error = state.get("validation_error", "")

    # 검증 성공
    if validated:
        log_step(logger, request_id, "NL2SQL", "2x", "BRANCH", "분기 결정 → EXECUTE")
        return "execute"

    # 설정에서 재시도 활성화 여부 및 최대 재시도 횟수 확인
    settings_config = _get_settings_config()
    retry_enabled = settings_config.get_value("nl2sql", "retry_enabled", True)
    max_retries = settings_config.get_value("nl2sql", "max_retries", 2)

    # 재시도 가능 여부 확인
    if retry_enabled and retry_count < max_retries and _is_retryable_error(validation_error):
        log_step(logger, request_id, "NL2SQL", "2x", "BRANCH", "분기 결정 → RETRY", attempt=retry_count + 1, max_retries=max_retries)
        # 상태 업데이트는 prepare_retry_node에서 수행
        return "retry"

    # 최종 실패
    log_step(logger, request_id, "NL2SQL", "2x", "BRANCH", "분기 결정 → ERROR", retry_count=retry_count, max_retries=max_retries)
    return "error"


def _is_retryable_error(error: str) -> bool:
    """
    재시도 가능한 오류인지 판단

    다음 패턴의 오류는 재시도로 해결 가능성이 있음:
    - 컬럼/테이블 관련 오류
    - 문법 오류
    - 모호한 참조 오류

    Args:
        error: 오류 메시지

    Returns:
        재시도 가능 여부
    """
    if not error:
        return False

    retryable_patterns = [
        "column",
        "table",
        "syntax",
        "ambiguous",
        "unknown",
        "not found",
        "does not exist",
        "invalid",
        "ora-00904",  # Oracle: invalid identifier (컬럼 오류)
        "ora-00942",  # Oracle: table or view does not exist
        "ora-00936",  # Oracle: missing expression
        "ora-01747",  # Oracle: invalid column specification
        "컬럼",
        "테이블",
        "존재하지",
        "찾을 수 없",
    ]
    error_lower = error.lower()
    return any(pattern in error_lower for pattern in retryable_patterns)


def prepare_retry_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    재시도 준비 노드

    재시도 시 필요한 상태를 업데이트합니다.
    조건부 분기 함수에서는 상태 업데이트가 불가능하므로,
    별도 노드에서 상태를 업데이트합니다.

    Args:
        state: NL2SQLState

    Returns:
        업데이트된 state (retry_count, previous_sql, previous_error, enhanced_fewshot 등)
    """
    request_id = state.get("request_id", "unknown")
    retry_count = state.get("retry_count", 0)
    validation_error = state.get("validation_error", "")
    generated_sql = state.get("generated_sql", "")

    new_retry_count = retry_count + 1

    log_step(logger, request_id, "NL2SQL", "2r", "PREPARE-RETRY", "재시도 준비", prev_retry=retry_count, new_retry=new_retry_count)

    return {
        "retry_count": new_retry_count,
        "previous_sql": generated_sql,
        "previous_error": validation_error,
        "enhanced_fewshot": True,
        "validated": False,
        "sql_result": None,
        "generated_sql": "",
    }


def execute_sql_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    SQL 실행 노드

    검증된 SQL을 데이터베이스에서 실행합니다.

    Args:
        state: NL2SQLState (Dict 형태로 전달)

    Returns:
        업데이트된 state (sql_result, metadata 필드 채움)
    """
    sql = state["generated_sql"]
    request_id = state.get("request_id", "unknown")

    log_step(logger, request_id, "NL2SQL", "3", "EXECUTE", "SQL 실행 시작")

    try:
        result = sql_executor.execute_sql(sql, validate=False)
        state["sql_result"] = result
        state["metadata"]["execution_time_ms"] = result.execution_time_ms
        state["metadata"]["row_count"] = result.row_count

        log_step(logger, request_id, "NL2SQL", "3", "EXECUTE", "SQL 실행 완료", row_count=result.row_count, execution_time_ms=result.execution_time_ms)

    except (SQLExecutionError, SQLValidationError) as e:
        log_step(logger, request_id, "NL2SQL", "3", "ERROR", f"SQL 실행 실패: {e}", level="ERROR")
        state["validation_error"] = str(e)
        state["validated"] = False

    return state


def should_continue_after_execute(state: Dict[str, Any]) -> str:
    """
    SQL 실행 후 조건부 분기 함수

    실행 결과에 따라 다음 노드를 결정합니다.
    실행 오류 발생 시 재시도 가능 여부를 확인하여 분기합니다.

    Args:
        state: NL2SQLState

    Returns:
        "answer" - 실행 성공, 답변 생성으로
        "retry" - 재시도 가능, enhanced fewshot으로 다시 시도
        "error" - 최대 재시도 초과 또는 치명적 오류
    """
    request_id = state.get("request_id", "unknown")
    sql_result = state.get("sql_result")
    validation_error = state.get("validation_error", "")
    retry_count = state.get("retry_count", 0)

    # 실행 성공 (결과가 있음)
    if sql_result is not None:
        log_step(logger, request_id, "NL2SQL", "3x", "BRANCH", "분기 결정 → ANSWER (실행 성공)")
        return "answer"

    # 실행 실패 - 재시도 가능 여부 확인
    settings_config = _get_settings_config()
    retry_enabled = settings_config.get_value("nl2sql", "retry_enabled", True)
    max_retries = settings_config.get_value("nl2sql", "max_retries", 2)

    # 재시도 가능 여부 확인
    if retry_enabled and retry_count < max_retries and _is_retryable_error(validation_error):
        log_step(logger, request_id, "NL2SQL", "3x", "BRANCH", "분기 결정 → RETRY (실행 오류)", attempt=retry_count + 1, max_retries=max_retries)
        # 상태 업데이트는 prepare_retry_node에서 수행
        return "retry"

    # 최종 실패
    log_step(logger, request_id, "NL2SQL", "3x", "BRANCH", "분기 결정 → ERROR (실행 실패)", retry_count=retry_count, max_retries=max_retries)
    return "error"


def pii_filter_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    PII 필터 노드

    SQL 실행 결과에서 PII(개인정보)를 감지하고 마스킹합니다.
    generate_answer_node(LLM 호출) 전에 실행되어
    개인정보가 외부 LLM API로 전송되는 것을 방지합니다.

    Args:
        state: NL2SQLState (Dict 형태로 전달)

    Returns:
        업데이트된 state (sql_result.rows에서 PII 마스킹 적용)
    """
    from app.core.pii.pii_service import pii_service

    request_id = state.get("request_id", "unknown")
    sql_result = state.get("sql_result")

    if not sql_result or not sql_result.rows:
        log_step(logger, request_id, "NL2SQL", "3p", "PII", "PII 필터 스킵 (결과 없음)")
        return state

    if not pii_service.enabled:
        log_step(logger, request_id, "NL2SQL", "3p", "PII", "PII 필터 비활성화")
        return state

    masked_rows, pii_count = pii_service.mask_sql_rows(sql_result.rows)

    if pii_count > 0:
        sql_result.rows = masked_rows
        state["sql_result"] = sql_result
        log_step(logger, request_id, "NL2SQL", "3p", "PII", f"PII 마스킹 완료 | detected={pii_count}, rows={len(masked_rows)}")
    else:
        log_step(logger, request_id, "NL2SQL", "3p", "PII", "PII 미감지", level="DEBUG")

    return state


def generate_answer_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    답변 생성 노드

    SQL 실행 결과를 기반으로 자연어 답변을 생성합니다.

    Args:
        state: NL2SQLState (Dict 형태로 전달)

    Returns:
        업데이트된 state (answer 필드 채움)
    """
    question = state["question"]
    sql = state["generated_sql"]
    result = state.get("sql_result")
    request_id = state.get("request_id", "unknown")

    if not result or result.row_count == 0:
        log_step(logger, request_id, "NL2SQL", "4", "ANSWER", "결과 없음 - 기본 응답 반환")
        state["answer"] = "조회된 결과가 없습니다."
        return state

    log_step(logger, request_id, "NL2SQL", "4", "ANSWER", "답변 생성 시작", row_count=result.row_count)

    system_prompt = prompt_service.get_nl2sql_answer_prompt()

    max_rows = 100
    rows_summary = result.rows[:max_rows] if len(result.rows) > max_rows else result.rows
    is_truncated = len(result.rows) > max_rows

    # ID 컬럼은 합계 계산에서 제외 (emp_id, id, _id로 끝나는 컬럼 등)
    id_column_patterns = ("_id", "id", "seq", "no", "num", "idx")

    numeric_totals: dict[str, float] = {}
    for col in result.columns:
        # ID 성격의 컬럼은 제외
        col_lower = col.lower()
        if col_lower == "id" or col_lower.endswith(id_column_patterns):
            continue

        try:
            total = 0.0
            has_numeric = False
            for row in result.rows:
                val = row.get(col)
                # None, null 값은 건너뜀
                if val is None:
                    continue
                if isinstance(val, (int, float)):
                    total += float(val)
                    has_numeric = True
            if has_numeric:
                numeric_totals[col] = total
        except (TypeError, ValueError):
            pass

    totals_info = ""
    if numeric_totals:
        totals_str = ", ".join([f"{k}={v}" for k, v in numeric_totals.items()])
        totals_info = f"\n\n숫자 컬럼 총합 (전체 {result.row_count}개 행 기준): {totals_str}"

    truncation_note = f"\n(※ 전체 {result.row_count}개 행 중 {max_rows}개만 표시)" if is_truncated else ""

    user_prompt = f"""질문: {question}

실행된 SQL:
{sql}

조회 결과 ({result.row_count}개 행):{truncation_note}
컬럼: {', '.join(result.columns)}
실제 데이터 :
{rows_summary}{totals_info}

위 결과를 바탕으로 질문에 대한 답변을 자연어/표/리스트등 사용자가 원하는 형태로 작성하라."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    llm = _get_llm()

    log_step(logger, request_id, "NL2SQL", "4a", "LLM-INPUT", "LLM 호출 시작 (답변 생성)",
            system_prompt_length=len(system_prompt),
            user_prompt_length=len(user_prompt),
            data_rows=len(rows_summary))

    if logger.isEnabledFor(logging.DEBUG):
        log_step(logger, request_id, "NL2SQL", "4a", "LLM-INPUT", "SYSTEM_PROMPT", level="DEBUG", content=system_prompt)
        log_step(logger, request_id, "NL2SQL", "4a", "LLM-INPUT", "USER_PROMPT", level="DEBUG", content=user_prompt)
        log_step(logger, request_id, "NL2SQL", "4a", "LLM-INPUT", "DATA_ROWS", level="DEBUG", content=str(rows_summary))

    try:
        response = llm.invoke(messages)

        if logger.isEnabledFor(logging.DEBUG):
            log_step(logger, request_id, "NL2SQL", "4b", "LLM-OUTPUT", "LLM 응답", level="DEBUG", content=response.content)

        answer = response.content

        state["answer"] = answer
        log_step(logger, request_id, "NL2SQL", "4b", "LLM-OUTPUT", "답변 생성 완료", answer_length=len(answer))

        if logger.isEnabledFor(logging.DEBUG):
            log_step(logger, request_id, "NL2SQL", "4b", "ANSWER", "생성된 답변", level="DEBUG", content=answer)

    except Exception as e:
        log_step(logger, request_id, "NL2SQL", "4", "ERROR", f"답변 생성 실패: {e}", level="ERROR")
        state["answer"] = f"조회 결과: {result.row_count}개 행이 발견되었습니다."

    return state


def handle_error_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    에러 처리 노드

    SQL 생성/검증/실행 실패 시 사용자에게 안내 메시지를 생성합니다.

    Args:
        state: NL2SQLState (Dict 형태로 전달)

    Returns:
        업데이트된 state (answer 필드 채움)
    """
    error_msg = state.get("validation_error", "알 수 없는 오류")
    request_id = state.get("request_id", "unknown")

    state["answer"] = f"""SQL 생성 또는 실행 중 오류가 발생했습니다.

오류 내용: {error_msg}

다음 사항을 확인해주세요:
1. 질문이 데이터베이스 스키마에 맞는지 확인
2. 테이블명과 컬럼명이 정확한지 확인
3. 질문을 더 구체적으로 작성
"""

    log_step(logger, request_id, "NL2SQL", "ERR", "ERROR", "오류 처리 완료", error=error_msg)
    return state


# =============================================================================
# 멀티턴 대화 노드
# =============================================================================


def load_history_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    이전 대화 이력 로드 노드

    MemorySaver에서 복원된 conversation_history를 처리하고,
    max_turns 초과 시 오래된 이력을 제거합니다.

    Args:
        state: NL2SQLState

    Returns:
        업데이트된 state (conversation_history, current_turn, history_truncated)
    """
    request_id = state.get("request_id", "unknown")
    session_id = state.get("session_id", "")
    conversation_history = list(state.get("conversation_history", []))

    # 설정에서 max_turns 로드
    settings_config = _get_settings_config()
    multiturn_enabled = settings_config.get_value("nl2sql", "multiturn_enabled", True)
    max_turns = settings_config.get_value("nl2sql", "multiturn_max_turns", 5)

    # 멀티턴 비활성화 시 이력 초기화
    if not multiturn_enabled:
        log_step(logger, request_id, "NL2SQL", "0.1", "HISTORY", "멀티턴 비활성화 - 이력 초기화")
        return {
            "conversation_history": [],
            "current_turn": 1,
            "max_turns": max_turns,
            "history_truncated": False,
        }

    # max_turns 초과 시 오래된 이력 제거 (슬라이딩 윈도우)
    history_truncated = False
    if len(conversation_history) >= max_turns:
        # 최근 (max_turns - 1)개만 유지 (현재 턴 포함하여 max_turns개)
        # ★ max_turns=1이면 이력 없이 시작 (현재 턴만 허용)
        original_count = len(conversation_history)
        keep_count = max(0, max_turns - 1)
        conversation_history = conversation_history[-keep_count:] if keep_count > 0 else []
        history_truncated = True
        log_step(logger, request_id, "NL2SQL", "0.1", "HISTORY", "이력 잘림", original=original_count, current=len(conversation_history), max_turns=max_turns)

    current_turn = len(conversation_history) + 1

    log_step(logger, request_id, "NL2SQL", "0.1", "HISTORY", "이력 로드 완료", session=session_id, turn=current_turn, max_turns=max_turns, history_count=len(conversation_history))

    return {
        "conversation_history": conversation_history,
        "current_turn": current_turn,
        "max_turns": max_turns,
        "history_truncated": history_truncated,
    }


def save_history_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    현재 대화를 이력에 저장하는 노드

    질문, SQL, 전체 답변, SQL 결과 요약을 conversation_history에 추가합니다.
    MemorySaver가 자동으로 세션에 저장합니다.

    Args:
        state: NL2SQLState

    Returns:
        업데이트된 state (conversation_history)
    """
    import time

    request_id = state.get("request_id", "unknown")
    question = state.get("question", "")
    generated_sql = state.get("generated_sql", "")
    answer = state.get("answer", "")
    sql_result = state.get("sql_result")
    conversation_history = list(state.get("conversation_history", []))

    # 설정에서 멀티턴 활성화 여부 확인
    settings_config = _get_settings_config()
    multiturn_enabled = settings_config.get_value("nl2sql", "multiturn_enabled", True)

    if not multiturn_enabled:
        log_step(logger, request_id, "NL2SQL", "5.1", "HISTORY", "멀티턴 비활성화 - 이력 저장 스킵")
        return {}

    # SQL 결과 요약 추출 (최대 100행)
    sql_result_summary = []
    if sql_result and hasattr(sql_result, 'rows') and sql_result.rows:
        max_summary_rows = 100
        sql_result_summary = sql_result.rows[:max_summary_rows]

    # 현재 턴을 이력에 추가 (sql_result_summary 포함)
    conversation_history.append({
        "question": question,
        "sql": generated_sql,
        "answer": answer,
        "timestamp": time.time(),
        "sql_result_summary": sql_result_summary,  # 후속 질문 답변용
    })

    log_step(logger, request_id, "NL2SQL", "5.1", "HISTORY", "이력 저장 완료", total_turns=len(conversation_history), result_rows=len(sql_result_summary))

    return {
        "conversation_history": conversation_history,
    }


# =============================================================================
# 의도 분석 + 질문 재작성 노드
# =============================================================================


def intent_rewrite_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    의도 분석 + 질문 재작성 노드

    멀티턴 대화에서 현재 질문의 의도를 분석하고,
    필요시 이전 컨텍스트를 포함한 완전한 질문으로 재작성합니다.

    처리 흐름:
    1. 대화 이력 확인 (없으면 바로 통과)
    2. LLM 호출하여 의도 분석 + 질문 재작성
    3. query_type 결정:
       - "sql_needed": 새로운 SQL 실행 필요
       - "answer_from_history": 이전 결과에서 답변 가능

    Args:
        state: NL2SQLState

    Returns:
        업데이트된 state:
        - query_type: str
        - rewritten_question: str
        - intent_reasoning: str
        - sql_result_summary: List[Dict]
    """
    import json

    request_id = state.get("request_id", "unknown")
    question = state.get("question", "")
    conversation_history = state.get("conversation_history", [])

    log_step(logger, request_id, "NL2SQL", "0.2", "INTENT-REWRITE", "의도 분석 시작", question=truncate_text(question, 40), history_count=len(conversation_history))

    # 대화 이력이 없으면 그대로 통과
    if not conversation_history:
        log_step(logger, request_id, "NL2SQL", "0.2", "INTENT-REWRITE", "대화 이력 없음 → SQL 실행 필요")
        return {
            "query_type": "sql_needed",
            "rewritten_question": question,
            "intent_reasoning": "첫 번째 질문이므로 SQL 실행 필요",
            "sql_result_summary": [],
        }

    # 이전 SQL 결과 요약 추출 (가장 최근 데이터가 있는 턴에서)
    # ★ 마지막 턴이 answer_from_history인 경우 sql_result_summary가 비어있을 수 있음
    #    → 역순으로 탐색하여 데이터가 있는 턴 찾기
    sql_result_summary = []
    for turn in reversed(conversation_history):
        if turn.get("sql_result_summary"):
            sql_result_summary = turn["sql_result_summary"]
            break

    # 대화 이력 포맷팅
    history_text = _format_conversation_history_for_intent(conversation_history)

    # LLM 호출
    llm = _get_llm()

    system_prompt = """당신은 NL2SQL 의도 분석기입니다.

## 질문: "새로운 SQL 실행이 필요한가?"

## 응답 형식 (JSON)
```json
{
    "query_type": "sql_needed" 또는 "sql_not_needed",
    "rewritten_question": "완전한 질문 형태 (답변 아님!)",
    "reasoning": "판단 이유"
}
```

## ★ 핵심 판단 기준 ★

**sql_needed (새 SQL 실행 필요):**
- 이전 결과 컬럼에 **없는** 정보를 요청
- "상세", "자세히", "디테일" 요청
- "왜", "이유", "원인" 질문
- 새로운 테이블/컬럼 조회 필요
- 명확하게 확신이 들지 않는 경우

**sql_not_needed (기존 데이터로 답변 가능):**
- 요청 정보가 이전 결과 컬럼에 **100% 존재**


## 예시

| 질문 | 이전 결과 컬럼 | query_type | 이유 |
|------|---------------|------------|------|
| "상세 정보 보여줘" | [emp_id, name] | sql_needed | 상세=추가 컬럼 필요 |
| "1등은 누구?" | [emp_id, name, score] | sql_not_needed | score로 정렬 가능 |
| "부서는?" | [emp_id, name, score] | sql_needed | 부서 컬럼 없음 |
| "상벌내역 보여줘" | [emp_id, name] | sql_needed | 상벌 컬럼 없음 |
"""

    # 이전 결과 데이터의 컬럼 목록 추출 (LLM이 판단하기 쉽도록)
    available_columns = []
    if sql_result_summary and len(sql_result_summary) > 0:
        available_columns = list(sql_result_summary[0].keys())

    user_prompt = f"""## 이전 대화 이력
{history_text}

## 현재 질문
{question}

## 이전 SQL 결과 데이터 (최대 10행)
**★ 사용 가능한 컬럼 목록**: {available_columns if available_columns else "없음"}
**★ 이 컬럼들로만 답변 가능! 다른 정보는 새 SQL 필요!**

데이터:
{json.dumps(sql_result_summary, ensure_ascii=False, indent=2) if sql_result_summary else "없음"}

위 컨텍스트를 바탕으로:
1. 현재 질문에 필요한 정보가 "사용 가능한 컬럼 목록"에 있는지 확인
2. 없으면 → sql_needed, 있으면 → sql_not_needed
3. 질문을 재작성하세요."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    log_step(logger, request_id, "NL2SQL", "0.2a", "LLM-INPUT", "LLM 호출 (의도 분석)",
            history_text_length=len(history_text))

    try:
        response = llm.invoke(messages)
        # response.content가 리스트일 수 있음 (멀티모달 응답)
        content = response.content
        if isinstance(content, list):
            response_text = "".join(str(c) for c in content).strip()
        else:
            response_text = str(content).strip()

        # JSON 파싱
        result = _parse_intent_response(response_text)

        query_type = result.get("query_type", "sql_needed")
        rewritten_question = result.get("rewritten_question", question)
        reasoning = result.get("reasoning", "")

        log_step(logger, request_id, "NL2SQL", "0.2b", "LLM-OUTPUT", "의도 분석 완료", query_type=query_type, rewritten_question=truncate_text(rewritten_question, 50), reasoning=truncate_text(reasoning, 50))

        # ★ 안전 검사 1: sql_not_needed인데 sql_result_summary가 비어있으면 sql_needed로 변경
        if query_type == "sql_not_needed" and not sql_result_summary:
            log_step(logger, request_id, "NL2SQL", "0.2c", "FALLBACK", "sql_not_needed → sql_needed (sql_result_summary 비어있음)", level="WARNING")
            query_type = "sql_needed"
            reasoning += " (이전 결과 데이터 없어 SQL 실행으로 전환)"

        return {
            "query_type": query_type,
            "rewritten_question": rewritten_question,
            "intent_reasoning": reasoning,
            "sql_result_summary": sql_result_summary,
        }

    except Exception as e:
        log_step(logger, request_id, "NL2SQL", "0.2", "ERROR", "의도 분석 실패 → SQL 실행으로 fallback", level="WARNING", error=str(e))
        # 실패 시 기본값 (SQL 실행)
        return {
            "query_type": "sql_needed",
            "rewritten_question": question,
            "intent_reasoning": f"의도 분석 실패: {e}",
            "sql_result_summary": sql_result_summary,
        }


def _format_conversation_history_for_intent(history: list) -> str:
    """의도 분석용 대화 이력 포맷팅"""
    if not history:
        return "없음"

    lines = []
    for i, turn in enumerate(history, 1):
        q = turn.get("question", "")
        sql = turn.get("sql", "")
        answer = truncate_text(turn.get("answer", ""), 200)
        lines.append(f"[턴 {i}]\n질문: {q}\nSQL: {sql}\n답변: {answer}")

    return "\n\n".join(lines)


def _parse_intent_response(response_text: str) -> Dict[str, Any]:
    """LLM 응답에서 JSON 파싱"""
    import json
    import re

    # JSON 블록 추출 시도
    json_match = re.search(r'```json\s*(.*?)\s*```', response_text, re.DOTALL)
    if json_match:
        json_str = json_match.group(1)
    else:
        # JSON 블록이 없으면 전체를 JSON으로 시도
        json_str = response_text

    # JSON 파싱
    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # 실패 시 기본값 반환
        return {
            "query_type": "sql_needed",
            "rewritten_question": "",
            "reasoning": "JSON 파싱 실패"
        }


def answer_from_history_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    이전 결과에서 답변 생성 노드

    이전 SQL 결과 데이터를 기반으로 후속 질문에 답변합니다.
    새로운 SQL 실행 없이 기존 데이터에서 답변을 추출합니다.

    Args:
        state: NL2SQLState

    Returns:
        업데이트된 state:
        - answer: str
        - generated_sql: str (빈 문자열 - SQL 미실행)
    """
    import json

    request_id = state.get("request_id", "unknown")
    question = state.get("question", "")
    rewritten_question = state.get("rewritten_question", question)
    sql_result_summary = state.get("sql_result_summary", [])
    conversation_history = state.get("conversation_history", [])

    log_step(logger, request_id, "NL2SQL", "4h", "ANSWER-FROM-HISTORY", "이전 결과에서 답변 생성 시작", data_rows=len(sql_result_summary))

    # 이전 결과가 없으면 안내 메시지
    if not sql_result_summary:
        log_step(logger, request_id, "NL2SQL", "4h", "ANSWER-FROM-HISTORY", "이전 결과 데이터 없음", level="WARNING")
        return {
            "answer": "이전 조회 결과 데이터가 없어 답변할 수 없습니다. 질문을 다시 해주세요.",
            "generated_sql": "",
        }

    # LLM 호출
    llm = _get_llm()

    # 이전 대화 컨텍스트 포맷팅
    history_text = _format_conversation_history_for_intent(conversation_history)

    system_prompt = """당신은 데이터 분석 전문가입니다.
이전에 조회한 SQL 결과 데이터를 바탕으로 사용자의 후속 질문에 답변합니다.

## 규칙
- 주어진 데이터에서만 답변을 추출하세요
- 데이터에 없는 정보는 "데이터에 없습니다"라고 답변
- 간결하고 정확하게 답변
- 필요시 데이터를 표나 리스트로 정리
"""

    user_prompt = f"""## 이전 대화 이력
{history_text}

## 이전 SQL 결과 데이터
{json.dumps(sql_result_summary, ensure_ascii=False, indent=2)}

## 현재 질문
{question}

## 재작성된 질문 (참고용)
{rewritten_question}

위 데이터를 바탕으로 질문에 답변하세요."""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]

    try:
        response = llm.invoke(messages)
        answer = response.content

        log_step(logger, request_id, "NL2SQL", "4h", "ANSWER-FROM-HISTORY", "답변 생성 완료", answer_length=len(answer))

        return {
            "answer": answer,
            "generated_sql": "",  # SQL 미실행
        }

    except Exception as e:
        log_step(logger, request_id, "NL2SQL", "4h", "ERROR", "답변 생성 실패", level="ERROR", error=str(e))
        return {
            "answer": f"답변 생성 중 오류가 발생했습니다: {e}",
            "generated_sql": "",
        }


def should_route_after_intent(state: Dict[str, Any]) -> str:
    """
    의도 분석 후 조건부 분기 함수

    query_type에 따라 다음 노드를 결정합니다.

    Args:
        state: NL2SQLState

    Returns:
        "sql_needed" - SQL 실행 필요 → schema_retrieval
        "sql_not_needed" - 이전 결과에서 답변 → answer_from_history_node
    """
    request_id = state.get("request_id", "unknown")
    query_type = state.get("query_type", "sql_needed")

    if query_type == "sql_not_needed":
        log_step(logger, request_id, "NL2SQL", "0.2x", "BRANCH", "분기 결정 → SQL_NOT_NEEDED (이전 결과에서 답변)")
        return "sql_not_needed"
    else:
        log_step(logger, request_id, "NL2SQL", "0.2x", "BRANCH", "분기 결정 → SQL_NEEDED (SQL 실행 필요)")
        return "sql_needed"

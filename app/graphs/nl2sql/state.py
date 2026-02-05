"""
NL2SQL State 정의

NL2SQL 그래프에서 사용하는 상태(State) 타입을 정의합니다.
"""

from typing import Any, Dict, List, Optional, TypedDict

from app.models.rag import SQLResult


class NL2SQLState(TypedDict):
    """NL2SQL Graph 상태"""

    # ===== 기본 필드 =====
    question: str
    schema_description: str
    generated_sql: str
    validated: bool
    validation_error: str
    sql_result: Optional[SQLResult]
    answer: str
    metadata: Dict[str, Any]
    request_id: str

    # ===== schema_retrieval_node 필드 =====
    selected_tables: List[str]           # 선택된 테이블 목록
    schema_retrieval_confidence: float   # 테이블 선택 신뢰도

    # ===== fewshot_retrieval_node 필드 =====
    fewshot_context: str                 # 포맷된 Few-shot 예제 문자열
    fewshot_examples: List[Dict]         # 원본 예제 데이터 목록
    fewshot_count: int                   # 검색된 예제 수

    # ===== prompt_build_node 필드 =====
    sql_prompt: str                      # 완성된 System Prompt
    user_prompt: str                     # User Prompt
    prompt_metadata: Dict[str, Any]      # 프롬프트 메타데이터

    # ===== 재시도 관련 필드 =====
    retry_count: int                     # 현재 재시도 횟수
    max_retries: int                     # 최대 재시도 횟수
    previous_sql: str                    # 이전 시도 SQL
    previous_error: str                  # 이전 오류 메시지
    enhanced_fewshot: bool               # 강화된 Few-shot 모드 플래그

    # ===== 멀티턴 대화 필드 =====
    session_id: str                      # 세션 ID
    conversation_history: List[Dict]     # 이전 대화 이력 [{question, sql, answer, timestamp, sql_result_summary}, ...]
    current_turn: int                    # 현재 턴 번호
    max_turns: int                       # 최대 턴 수 (설정에서 로드)
    history_truncated: bool              # 이력 잘림 여부 (max_turns 초과 시 True)

    # ===== 의도 분석 + 질문 재작성 필드 =====
    query_type: str                      # 질의 유형: "sql_needed" | "sql_not_needed"
    rewritten_question: str              # 재작성된 질문 (완전한 독립 질문)
    intent_reasoning: str                # 의도 분석 이유
    sql_result_summary: List[Dict]       # 이전 SQL 결과 요약 (최대 10행)


def create_initial_state(
    question: str,
    request_id: str = "unknown",
    max_retries: int = 2,
    session_id: str = "",
    max_turns: int = 5,
) -> NL2SQLState:
    """
    초기 상태 생성

    Args:
        question: 사용자 질문
        request_id: 요청 ID
        max_retries: 최대 재시도 횟수
        session_id: 세션 ID (멀티턴 대화용)
        max_turns: 최대 대화 턴 수

    Returns:
        초기화된 NL2SQLState
    """
    return NL2SQLState(
        # 기본 필드
        question=question,
        schema_description="",
        generated_sql="",
        validated=False,
        validation_error="",
        sql_result=None,
        answer="",
        metadata={},
        request_id=request_id,

        # schema_retrieval_node 필드
        selected_tables=[],
        schema_retrieval_confidence=0.0,

        # fewshot_retrieval_node 필드
        fewshot_context="",
        fewshot_examples=[],
        fewshot_count=0,

        # prompt_build_node 필드
        sql_prompt="",
        user_prompt="",
        prompt_metadata={},

        # 재시도 관련 필드
        retry_count=0,
        max_retries=max_retries,
        previous_sql="",
        previous_error="",
        enhanced_fewshot=False,

        # 멀티턴 대화 필드
        session_id=session_id,
        conversation_history=[],
        current_turn=1,
        max_turns=max_turns,
        history_truncated=False,

        # 의도 분석 + 질문 재작성 필드
        query_type="sql_needed",         # 기본값: SQL 실행 필요
        rewritten_question="",           # 빈 문자열 = 재작성 필요 없음
        intent_reasoning="",             # 의도 분석 이유
        sql_result_summary=[],           # 이전 SQL 결과 요약
    )

"""
SSE Stream Manager

위치: app/core/sse/stream_manager.py
- SSE 포맷팅 유틸리티
- 스테이지 레이블 조회
- 노드→스테이지 매핑 조회
"""
import json

from app.models.sse import (
    NL2SQL_NODE_STAGE, NL2SQL_STAGE_LABELS,
    AGENT_NODE_STAGE, AGENT_STAGE_LABELS,
)


def format_sse(event_type: str, data: dict) -> str:
    """SSE 형식으로 포맷팅

    Args:
        event_type: 이벤트 타입 (node_complete, complete, error)
        data: 이벤트 데이터 딕셔너리

    Returns:
        SSE 포맷 문자열 ("event: xxx\\ndata: {...}\\n\\n")
    """
    json_data = json.dumps(data, ensure_ascii=False, default=str)
    return f"event: {event_type}\ndata: {json_data}\n\n"


def get_stage_label(stage: int, phase: str, mode: str) -> str:
    """스테이지 번호에 대한 표시 레이블을 반환합니다.

    Args:
        stage: 스테이지 번호 (1, 2, 3, 4)
        phase: "start" 또는 "complete"
        mode: "agent" 또는 "nl2sql"

    Returns:
        한글 표시 레이블

    예시:
        get_stage_label(1, "start", "nl2sql")     → "질문 분석 중..."
        get_stage_label(3, "complete", "nl2sql")   → "SQL 생성 및 실행 완료"
        get_stage_label(2, "start", "agent")       → "도구 실행 중..."
    """
    labels = AGENT_STAGE_LABELS if mode == "agent" else NL2SQL_STAGE_LABELS
    stage_info = labels.get(stage, {"start": f"단계 {stage} 처리 중...", "complete": f"단계 {stage} 완료"})
    return stage_info.get(phase, f"단계 {stage}")


def get_node_stage(node_name: str, mode: str) -> int:
    """노드가 속하는 스테이지 번호를 반환합니다.

    Args:
        node_name: LangGraph 노드 이름 (예: "schema_retrieval")
        mode: "agent" 또는 "nl2sql"

    Returns:
        스테이지 번호 (1, 2, 3, 4)
        매핑에 없는 노드이면 0을 반환합니다.

    예시:
        get_node_stage("load_history", "nl2sql")    → 1
        get_node_stage("sql_generate", "nl2sql")    → 3
        get_node_stage("tools", "agent")            → 2
    """
    stage_map = AGENT_NODE_STAGE if mode == "agent" else NL2SQL_NODE_STAGE
    return stage_map.get(node_name, 0)

"""
SSE Stream Manager

위치: app/core/sse/stream_manager.py
- SSE 포맷팅 유틸리티
- 노드 레이블 조회
- 노드 결과 요약 추출
- 다음 노드 예측 (node_start 이벤트용)
"""
import json
from typing import Any, Dict, Optional

from app.models.sse import AGENT_NODE_LABELS, NL2SQL_NODE_LABELS


# NL2SQL 다음 노드 매핑 (확정적 엣지만, 조건부 엣지는 None)
NL2SQL_NEXT_NODE = {
    "load_history": "intent_rewrite",
    "intent_rewrite": None,         # 조건부: schema_retrieval 또는 sql_not_needed
    "sql_not_needed": "save_history",
    "schema_retrieval": "fewshot_retrieval",
    "fewshot_retrieval": "prompt_build",
    "prompt_build": "sql_generate",
    "sql_generate": "validate_sql",
    "validate_sql": None,           # 조건부: execute_sql, prepare_retry, handle_error
    "execute_sql": None,            # 조건부: pii_filter, prepare_retry, handle_error
    "pii_filter": "generate_answer",
    "generate_answer": "save_history",
    "save_history": None,           # END
    "handle_error": None,           # END
    "prepare_retry": "fewshot_retrieval",
}

# Agent 다음 노드 매핑
AGENT_NEXT_NODE = {
    "agent": None,     # 조건부: tools 또는 answer
    "tools": "agent",
    "answer": None,    # END
}

# 그래프 엔트리 포인트
ENTRY_NODES = {
    "nl2sql": "load_history",
    "agent": "agent",
}


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


def get_node_label(node_name: str, phase: str, mode: str) -> str:
    """노드 이름에 대한 표시 레이블 반환

    Args:
        node_name: LangGraph 노드 이름
        phase: "start" 또는 "complete"
        mode: "agent" 또는 "nl2sql"

    Returns:
        한글 표시 레이블
    """
    labels = AGENT_NODE_LABELS if mode == "agent" else NL2SQL_NODE_LABELS
    node_info = labels.get(node_name, {"start": f"{node_name} 처리 중...", "complete": f"{node_name} 완료"})
    return node_info.get(phase, node_name)


def get_entry_node(mode: str) -> str:
    """그래프 엔트리 포인트 노드 이름 반환"""
    return ENTRY_NODES.get(mode, "")


def get_next_node(node_name: str, mode: str) -> Optional[str]:
    """현재 노드 완료 후 다음 노드 예측 (확정적 엣지만)

    Args:
        node_name: 현재 완료된 노드 이름
        mode: "agent" 또는 "nl2sql"

    Returns:
        다음 노드 이름 (조건부 엣지이면 None)
    """
    next_map = AGENT_NEXT_NODE if mode == "agent" else NL2SQL_NEXT_NODE
    return next_map.get(node_name)


def extract_node_detail(node_name: str, state_update: dict, mode: str) -> Optional[Dict[str, Any]]:
    """노드 결과에서 UI 표시용 요약 정보 추출

    Args:
        node_name: 노드 이름
        state_update: 노드가 반환한 상태 업데이트
        mode: "agent" 또는 "nl2sql"

    Returns:
        요약 딕셔너리 또는 None
    """
    detail: Dict[str, Any] = {}

    if mode == "nl2sql":
        if node_name == "schema_retrieval":
            detail["tables"] = state_update.get("selected_tables", [])
        elif node_name == "fewshot_retrieval":
            detail["example_count"] = state_update.get("fewshot_count", 0)
        elif node_name == "sql_generate":
            sql = state_update.get("generated_sql", "")
            if sql:
                detail["sql_preview"] = sql[:100] + "..." if len(sql) > 100 else sql
        elif node_name == "validate_sql":
            detail["validated"] = state_update.get("validated", False)
            if state_update.get("validation_error"):
                detail["error"] = str(state_update["validation_error"])[:100]
        elif node_name == "execute_sql":
            sql_result = state_update.get("sql_result")
            if sql_result:
                row_count = sql_result.get("row_count", 0) if isinstance(sql_result, dict) else getattr(sql_result, "row_count", 0)
                detail["row_count"] = row_count
        elif node_name == "intent_rewrite":
            detail["query_type"] = state_update.get("query_type", "")
            detail["rewritten"] = bool(state_update.get("rewritten_question", ""))

    elif mode == "agent":
        if node_name == "tools":
            detail["tools_used"] = state_update.get("tools_used", [])
        elif node_name == "agent":
            detail["iteration"] = state_update.get("iteration_count", 0)

    return detail if detail else None

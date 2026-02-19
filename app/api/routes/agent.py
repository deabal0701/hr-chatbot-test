"""Agent API 엔드포인트

위치: app/api/routes/agent.py
기능:
- Agent 기반 검색 (ReAct 패턴)
- 멀티턴 대화 지원
- 세션 관리
- 메트릭 조회

비즈니스 로직은 agent_service에 위임
"""
import uuid
from typing import Dict, Any, Optional

from fastapi import APIRouter, Body, Depends
from fastapi.responses import StreamingResponse

from app.api.services.agent_service import agent_service
from app.core.errors import APIException, ErrorCode, success_response
from app.core.security.dependencies import get_current_user
from app.core.security.tenant_context import set_tenant_id
from app.models.agent import AgentRequest
from app.models.auth import UserContext
from app.utils.logger import setup_logger
from app.utils.common import truncate_text

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


def _extract_tenant_id(current_user: UserContext) -> Optional[str]:
    """current_user에서 tenant_id 추출 (GLOBAL: None=전체, TENANT/USER: 자기 테넌트)"""
    if current_user.role_code == "GLOBAL":
        return None
    return str(current_user.tenant_id) if current_user.tenant_id else None


@router.post("/search")
async def agent_search(request: AgentRequest, current_user: UserContext = Depends(get_current_user)):
    """
    AI Agent 기반 검색 (ReAct 패턴)

    **특징:**
    - 복잡한 멀티스텝 질문 처리 가능
    - 자동으로 필요한 도구를 선택 및 실행 (SQL, 문서 검색, 계산)
    - 멀티턴 대화 지원 (session_id 사용)
    - 단계별 실행 과정 반환
    """
    request_id = str(uuid.uuid4())[:8]

    # 테넌트 격리 (Phase 3: Agent 도구가 contextvars에서 tenant_id 읽음)
    set_tenant_id(_extract_tenant_id(current_user))

    try:
        logger.info(f"[{request_id}] ========== Agent 검색 요청 처리 시작 ==========")
        logger.info(f"[{request_id}] Agent 검색 요청: {truncate_text(request.question, 100)}")

        result = await agent_service.search(question=request.question, session_id=request.session_id, request_id=request_id)

        logger.info(f"[{request_id}] Agent 검색 완료: iterations={result.total_iterations}, tools={result.tools_used}, success={result.success}")
        logger.info(f"[{request_id}] ========== Agent 검색 요청 처리 완료 ==========")

        return success_response(result.model_dump())

    except APIException:
        raise
    except Exception as e:
        logger.error(f"[{request_id}] Agent 검색 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.AGENT_FAILED, detail=str(e))


@router.post("/search/stream")
async def agent_search_stream(request: AgentRequest, current_user: UserContext = Depends(get_current_user)):
    """
    AI Agent SSE 스트리밍 검색 (ReAct 패턴)

    노드별 진행 상태를 실시간으로 전송하고,
    최종 완료 시 전체 AgentResponse를 전송합니다.

    Response: text/event-stream (SSE)
    """
    request_id = str(uuid.uuid4())[:8]

    # 테넌트 격리 (Phase 3)
    set_tenant_id(_extract_tenant_id(current_user))

    logger.info(f"[{request_id}] Agent SSE 검색 요청: {truncate_text(request.question, 100)}")

    async def event_generator():
        async for event in agent_service.search_stream(
            question=request.question,
            session_id=request.session_id,
            request_id=request_id,
        ):
            yield event

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
            "X-Request-ID": request_id,
        },
    )


@router.get("/sessions")
async def list_sessions(current_user: UserContext = Depends(get_current_user)):
    """활성 세션 목록 조회 (InMemorySaver 기반)"""
    try:
        sessions = agent_service.get_sessions()
        return success_response({"items": sessions, "total": len(sessions)})
    except Exception as e:
        logger.error(f"세션 목록 조회 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/sessions/{session_id}/memory")
async def get_session_memory(session_id: str, current_user: UserContext = Depends(get_current_user)):
    """세션 메모리 조회 (InMemorySaver 기반)"""
    try:
        result = agent_service.get_session_memory(session_id)
        if not result:
            raise APIException(error_code=ErrorCode.SESSION_NOT_FOUND, message=f"세션 {session_id}을(를) 찾을 수 없습니다")
        return success_response(result)
    except APIException:
        raise
    except Exception as e:
        logger.error(f"세션 메모리 조회 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, current_user: UserContext = Depends(get_current_user)):
    """세션 삭제 (InMemorySaver 체크포인트 삭제)"""
    try:
        result = agent_service.delete_session(session_id)
        return success_response(result)
    except ValueError as e:
        raise APIException(error_code=ErrorCode.SESSION_NOT_FOUND, detail=str(e))
    except Exception as e:
        logger.error(f"세션 삭제 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/sessions/{session_id}/metrics")
async def get_session_metrics(session_id: str, current_user: UserContext = Depends(get_current_user)):
    """세션 메트릭 조회 (기본 정보)"""
    try:
        result = agent_service.get_session_metrics(session_id)
        return success_response(result)
    except Exception as e:
        logger.error(f"세션 메트릭 조회 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.get("/tools")
async def list_tools(current_user: UserContext = Depends(get_current_user)):
    """사용 가능한 도구 목록 조회"""
    try:
        from app.graphs.agent.tools.sql_tool import SQLQueryTool
        from app.graphs.agent.tools.rag_tool import DocumentSearchTool
        from app.graphs.agent.tools.calc_tool import CalculatorTool

        tools_info = []
        for tool_class in [SQLQueryTool, DocumentSearchTool, CalculatorTool]:
            tool = tool_class()
            tools_info.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters_schema,
                "enabled": tool.enabled
            })

        return success_response({"total": len(tools_info), "tools": tools_info})

    except Exception as e:
        logger.error(f"도구 목록 조회 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))


@router.post("/test-tool")
async def test_tool(
    tool_name: str = Body(..., description="테스트할 도구 이름"),
    params: Dict[str, Any] = Body(default={}, description="도구 파라미터"),
    current_user: UserContext = Depends(get_current_user),
):
    """도구 단독 테스트 (디버깅용)"""
    try:
        from app.graphs.agent.tools.sql_tool import SQLQueryTool
        from app.graphs.agent.tools.rag_tool import DocumentSearchTool
        from app.graphs.agent.tools.calc_tool import CalculatorTool

        tool_map = {
            "query_database_tool": SQLQueryTool,
            "search_documents_tool": DocumentSearchTool,
            "calculate_tool": CalculatorTool
        }

        if tool_name not in tool_map:
            raise APIException(
                error_code=ErrorCode.BAD_REQUEST,
                message=f"알 수 없는 도구: {tool_name}",
                detail=f"사용 가능한 도구: {list(tool_map.keys())}"
            )

        tool = tool_map[tool_name]()
        result = tool.execute(**params)

        return success_response({
            "tool_name": tool_name,
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "metadata": result.metadata,
            "execution_time_ms": result.execution_time_ms
        })

    except APIException:
        raise
    except Exception as e:
        logger.error(f"도구 테스트 실패: {e}", exc_info=True)
        raise APIException(error_code=ErrorCode.INTERNAL_ERROR, detail=str(e))

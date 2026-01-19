"""Agent API 엔드포인트

위치: app/api/routes/agent.py
기능:
- Agent 기반 검색 (ReAct 패턴)
- 멀티턴 대화 지원
- 세션 관리
- 메트릭 조회

확장성:
- 스트리밍 응답 (Server-Sent Events)
- WebSocket 지원
- 세션 영속화 (Redis)

비즈니스 로직은 agent_service에 위임
"""
import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, status, Query, Body

from app.api.services.agent_service import agent_service
from app.models.agent_schemas import (
    AgentRequest,
    AgentResponse
)
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

router = APIRouter(prefix="/api/v1/agent", tags=["agent"])


@router.post("/search", response_model=AgentResponse)
async def agent_search(request: AgentRequest):
    """
    AI Agent 기반 검색 (ReAct 패턴)

    **특징:**
    - 복잡한 멀티스텝 질문 처리 가능
    - 자동으로 필요한 도구를 선택 및 실행 (SQL, 문서 검색, 계산)
    - 멀티턴 대화 지원 (session_id 사용)
    - 단계별 실행 과정 반환

    **사용 예시:**

    간단한 질문:
    ```json
    {
      "question": "2024년 입사자는 몇 명인가?"
    }
    ```

    복잡한 질문 (멀티스텝):
    ```json
    {
      "question": "2024년 입사자 중 재택근무 정책을 준수하는 사람은 몇 명이고 평균 급여는?",
      "config": {
        "max_iterations": 15,
        "enable_memory": true
      }
    }
    ```

    멀티턴 대화:
    ```json
    {
      "question": "그 중에서 개발팀만 보여줘",
      "session_id": "user123-session456"
    }
    ```

    **Parameters:**
    - question: 질문 (필수)
    - session_id: 세션 ID (멀티턴 대화용, 선택)
    - config: Agent 설정 (선택)
    - verbose: 상세 로그 출력 (선택)

    **Returns:**
    - answer: 최종 답변
    - steps: 실행 단계들 (Thought → Action → Observation)
    - total_iterations: 총 반복 횟수
    - tools_used: 사용된 도구 목록
    - success: 성공 여부
    - metadata: 메타데이터 (실행 시간, 세션 ID 등)
    """
    request_id = str(uuid.uuid4())[:8]

    try:
        logger.info(f"[{request_id}] Agent 검색 요청: {request.question[:100]}")

        # 서비스 호출 (설정 로딩 로직은 서비스에서 처리)
        result = await agent_service.search(
            question=request.question,
            session_id=request.session_id,
            config=request.config,
            request_id=request_id
        )

        logger.info(
            f"[{request_id}] Agent 검색 완료: "
            f"iterations={result.total_iterations}, "
            f"tools={result.tools_used}, "
            f"success={result.success}"
        )

        return result

    except Exception as e:
        logger.error(f"[{request_id}] Agent 검색 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Agent 검색 중 오류 발생: {str(e)}"
        )


@router.get("/sessions", response_model=List[str])
async def list_sessions():
    """
    활성 세션 목록 조회 (InMemorySaver 기반)

    **Returns:**
    - 활성 세션 ID 목록

    **확장:**
    - 세션별 메타데이터 (생성 시간, 마지막 사용 시간)
    - 페이지네이션
    """
    try:
        sessions = agent_service.get_sessions()
        return sessions

    except Exception as e:
        logger.error(f"세션 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 목록 조회 실패: {str(e)}"
        )


@router.get("/sessions/{session_id}/memory")
async def get_session_memory(session_id: str):
    """
    세션 메모리 조회 (InMemorySaver 기반)

    **Parameters:**
    - session_id: 세션 ID (thread_id)

    **Returns:**
    - 세션의 대화 히스토리 및 체크포인트 메타데이터

    **확장:**
    - 메시지 필터링 (날짜, 역할)
    - 요약 제공
    """
    try:
        result = agent_service.get_session_memory(session_id)

        if not result:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Session {session_id} not found"
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"세션 메모리 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 메모리 조회 실패: {str(e)}"
        )


@router.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """
    세션 삭제 (InMemorySaver 체크포인트 삭제)

    **Parameters:**
    - session_id: 삭제할 세션 ID (thread_id)

    **Returns:**
    - 삭제 성공 메시지

    **확장:**
    - 영구 삭제 vs 소프트 삭제
    - 삭제 전 백업
    """
    try:
        result = agent_service.delete_session(session_id)
        return result

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"세션 삭제 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 삭제 실패: {str(e)}"
        )


@router.get("/sessions/{session_id}/metrics")
async def get_session_metrics(session_id: str):
    """
    세션 메트릭 조회 (기본 정보)

    **Parameters:**
    - session_id: 세션 ID (thread_id)

    **Returns:**
    - 세션의 기본 통계 (체크포인트 수, 메시지 수 등)

    **Note:**
    - InMemorySaver는 상세 메트릭을 자동 추적하지 않음
    - 상세 메트릭이 필요하면 별도 메트릭 시스템 구축 필요 (Prometheus 등)

    **확장:**
    - 시계열 데이터 (그래프용)
    - 도구별 상세 통계
    - 비용 추정
    """
    try:
        result = agent_service.get_session_metrics(session_id)
        return result

    except Exception as e:
        logger.error(f"세션 메트릭 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"세션 메트릭 조회 실패: {str(e)}"
        )


@router.get("/tools")
async def list_tools():
    """
    사용 가능한 도구 목록 조회

    **Returns:**
    - 도구 이름, 설명, 파라미터 스키마

    **확장:**
    - 도구별 사용 통계
    - 도구 활성화/비활성화 상태
    - 도구별 성공률
    """
    try:
        from app.tools.sql_tool import SQLQueryTool
        from app.tools.rag_tool import DocumentSearchTool
        from app.tools.calculator_tool import CalculatorTool

        tools_info = []

        for tool_class in [SQLQueryTool, DocumentSearchTool, CalculatorTool]:
            tool = tool_class()
            tools_info.append({
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.parameters_schema,
                "enabled": tool.enabled
            })

        return {
            "total": len(tools_info),
            "tools": tools_info
        }

    except Exception as e:
        logger.error(f"도구 목록 조회 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"도구 목록 조회 실패: {str(e)}"
        )


@router.post("/test-tool")
async def test_tool(
    tool_name: str = Body(..., description="테스트할 도구 이름"),
    params: Dict[str, Any] = Body(default={}, description="도구 파라미터")
):
    """
    도구 단독 테스트 (디버깅용)

    **Request Body:**
    ```json
    {
        "tool_name": "calculate",
        "params": {"expression": "10 + 20"}
    }
    ```

    **Returns:**
    - 도구 실행 결과

    **확장:**
    - 도구별 벤치마크
    - 성능 프로파일링
    """
    try:
        from app.tools.sql_tool import SQLQueryTool
        from app.tools.rag_tool import DocumentSearchTool
        from app.tools.calculator_tool import CalculatorTool

        tool_map = {
            "query_database_tool": SQLQueryTool,
            "search_documents_tool": DocumentSearchTool,
            "calculate_tool": CalculatorTool
        }

        if tool_name not in tool_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown tool: {tool_name}. Available: {list(tool_map.keys())}"
            )

        # 도구 실행
        tool = tool_map[tool_name]()
        result = tool.execute(**params)

        return {
            "tool_name": tool_name,
            "success": result.success,
            "data": result.data,
            "error": result.error,
            "metadata": result.metadata,
            "execution_time_ms": result.execution_time_ms
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"도구 테스트 실패: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"도구 테스트 실패: {str(e)}"
        )

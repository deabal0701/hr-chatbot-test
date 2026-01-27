"""AI Agent 검색 서비스

위치: app/api/services/agent_service.py
- AI Agent (ReAct 패턴) 비즈니스 로직 처리
- Route와 Graph 사이의 서비스 계층
- 설정 로딩 및 세션 관리
"""
from typing import Any, Dict, List, Optional

from app.graphs.agent_graph import agent_graph
from app.models.agent import (AgentConfig, AgentResponse)
from app.core.config.settings_config import settings_config
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)

class AgentService:
    """AI Agent 검색 서비스"""

    async def search(self, question: str, session_id: Optional[str] = None, config: Optional[AgentConfig] = None, request_id: str = "unknown") -> AgentResponse:
        """
        AI Agent 검색 실행

        Args:
            question: 사용자 질문
            session_id: 세션 ID (멀티턴 대화용, 선택)
            config: Agent 설정 (선택, 미지정시 시스템 설정 사용)
            request_id: 요청 추적 ID

        Returns:
            AgentResponse: Agent 응답 (답변, 실행 단계, 메타데이터)
        """
        log_step(request_id, "SERVICE", "AGENT", "START", "Agent 서비스 시작", question=question[:50])

        # 세션 ID 자동 생성
        if not session_id: 
            session_id = f"session-{request_id}"

        # 설정 로딩 (시스템 설정 → 요청 설정 → 기본값)
        resolved_config = self._resolve_config(config, request_id)

        # 입력 데이터 구성
        inputs = self._prepare_inputs(question, session_id, resolved_config, request_id)

        # Agent 그래프 실행
        result = await agent_graph.ainvoke(inputs)
        log_step(request_id, "SERVICE", "AGENT", "END", "Agent 서비스 완료", iterations=result.total_iterations, tools_count=len(result.tools_used), success=result.success)

        return result

    def _resolve_config(self, request_config: Optional[AgentConfig], request_id: str) -> AgentConfig:
        """
        Agent 설정 결정 (보안: 사용자 입력 무시, DB/캐시에서만 로드)

        보안 정책:
        - 사용자가 API 요청으로 전달한 config 값은 무시됨
        - 모든 설정은 DB(tb_app_settings) 또는 캐시에서만 로드
        - 관리자만 Admin UI를 통해 설정 변경 가능

        Args:
            request_config: 요청에서 전달된 설정 (보안상 무시됨)
            request_id: 요청 추적 ID

        Returns:
            AgentConfig: DB/캐시에서 로드된 설정
        """
        # 보안: 사용자 입력(request_config) 무시, 새 AgentConfig 생성 후 DB에서 로드
        _ = request_config  # 명시적으로 무시 (보안 정책)
        config = AgentConfig()  # type: ignore

        # 모든 설정을 DB/캐시에서 로드 (사용자 입력 무시)
        config.max_iterations = settings_config.get_value("agent", "max_iterations", 10)
        config.timeout_seconds = settings_config.get_value("agent", "timeout_seconds", 60)
        config.llm_model = settings_config.get_value("llm", "model", "gpt-4o-mini")
        config.llm_temperature = settings_config.get_value("agent", "llm_temperature", 0.0)
        config.enable_memory = settings_config.get_value("agent", "enable_memory", True)
        config.enable_streaming = settings_config.get_value("agent", "enable_streaming", False)

        # enabled_tools: 쉼표 구분 문자열 → 리스트 변환
        tools_str = settings_config.get_value("agent", "enabled_tools", "query_database_tool,search_documents_tool,calculate_tool")
        if tools_str:
            enabled_tools = [t.strip() for t in tools_str.split(",") if t.strip()]
            if enabled_tools:
                config.tools_whitelist = enabled_tools

        # tools_blacklist는 DB에서 관리하지 않으므로 None 유지
        config.tools_blacklist = None

        logger.debug(f"[{request_id}] Agent 설정: max_iter={config.max_iterations}, timeout={config.timeout_seconds}s, model={config.llm_model}")

        return config

    def _prepare_inputs(self, question: str, session_id: str, config: AgentConfig, request_id: str) -> Dict[str, Any]:
        """
        그래프 입력 데이터 구성

        Args:
            question: 사용자 질문
            session_id: 세션 ID
            config: Agent 설정
            request_id: 요청 추적 ID

        Returns:
            Dict: 그래프 입력 데이터
        """
        return {
            "question": question,
            "session_id": session_id,
            "config": config,
            "request_id": request_id
        }

    def get_sessions(self) -> List[str]:
        """
        활성 세션 목록 조회 (InMemorySaver 기반)

        Returns:
            List[str]: 활성 세션 ID 목록
        """
        checkpointer = agent_graph.checkpointer
        sessions = []

        # InMemorySaver의 내부 storage에서 thread_id 추출
        if hasattr(checkpointer, 'storage'):
            thread_ids = set()
            for key in checkpointer.storage.keys():
                if key and len(key) > 0:
                    thread_ids.add(key[0])
            sessions = sorted(list(thread_ids))

        logger.info(f"Active sessions (InMemorySaver): {len(sessions)}")
        return sessions

    def get_session_memory(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        세션 메모리 조회

        Args:
            session_id: 세션 ID

        Returns:
            Dict: 세션 메모리 정보 (없으면 None)
        """
        checkpointer = agent_graph.checkpointer
        config = {"configurable": {"thread_id": session_id}}

        # 가장 최근 체크포인트 가져오기
        checkpoint = checkpointer.get(config) # type: ignore

        if not checkpoint:
            return None

        # 체크포인트에서 메시지 추출
        messages = checkpoint.get("channel_values", {}).get("messages", [])

        # 메시지를 직렬화 가능한 형태로 변환
        serialized_messages = []
        for msg in messages:
            if hasattr(msg, "content"):
                serialized_messages.append({
                    "type": type(msg).__name__,
                    "content": str(msg.content),
                    "role": getattr(msg, "type", "unknown")
                })

        return {
            "session_id": session_id,
            "messages": serialized_messages,
            "message_count": len(serialized_messages),
            "checkpoint_id": checkpoint.get("id"),
            "metadata": checkpoint.get("metadata", {})
        }

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        """
        세션 삭제 (InMemorySaver 체크포인트 삭제)

        Args:
            session_id: 삭제할 세션 ID

        Returns:
            Dict: 삭제 결과 정보

        Raises:
            ValueError: storage에 접근할 수 없는 경우
        """
        checkpointer = agent_graph.checkpointer

        if not hasattr(checkpointer, 'storage'):
            raise ValueError("Checkpointer storage not accessible")

        keys_to_delete = [
            key for key in checkpointer.storage.keys()
            if key and len(key) > 0 and key[0] == session_id
        ]

        for key in keys_to_delete:
            del checkpointer.storage[key]

        logger.info(
            f"Session deleted (InMemorySaver): {session_id}, "
            f"checkpoints removed: {len(keys_to_delete)}"
        )

        return {
            "success": True,
            "message": f"Session {session_id} deleted successfully",
            "checkpoints_removed": len(keys_to_delete)
        }

    def get_session_metrics(self, session_id: str) -> Dict[str, Any]:
        """
        세션 메트릭 조회

        Args:
            session_id: 세션 ID

        Returns:
            Dict: 세션 기본 통계
        """
        checkpointer = agent_graph.checkpointer

        # 해당 세션의 체크포인트 수 계산
        checkpoint_count = 0
        if hasattr(checkpointer, 'storage'):
            checkpoint_count = sum(
                1 for key in checkpointer.storage.keys()
                if key and len(key) > 0 and key[0] == session_id
            )

        # 최근 체크포인트에서 메시지 수 가져오기
        config = {"configurable": {"thread_id": session_id}}
        checkpoint = checkpointer.get(config) # type: ignore

        message_count = 0
        if checkpoint:
            messages = checkpoint.get("channel_values", {}).get("messages", [])
            message_count = len(messages)

        return {
            "session_id": session_id,
            "checkpoint_count": checkpoint_count,
            "message_count": message_count,
            "note": "InMemorySaver는 상세 메트릭을 추적하지 않습니다. 상세 메트릭이 필요하면 별도 시스템을 구축하세요."
        }


# 싱글톤 인스턴스
agent_service = AgentService()
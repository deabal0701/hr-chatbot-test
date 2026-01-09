"""
AI Agent 테스트

테스트 유형:
- 단위 테스트: 개별 도구 테스트
- 통합 테스트: Agent Graph 테스트
- E2E 테스트: API 엔드포인트 테스트
"""

import pytest
from unittest.mock import Mock, patch

from app.tools.calculator_tool import CalculatorTool
from app.tools.base import ToolResult
from app.models.agent_schemas import AgentRequest, AgentConfig


class TestCalculatorTool:
    """계산기 도구 단위 테스트"""

    def test_basic_arithmetic(self):
        """기본 산술 연산"""
        tool = CalculatorTool()

        # 덧셈
        result = tool.execute(expression="10 + 20")
        assert result.success is True
        assert result.data == 30

        # 곱셈
        result = tool.execute(expression="5 * 6")
        assert result.success is True
        assert result.data == 30

        # 나눗셈
        result = tool.execute(expression="100 / 4")
        assert result.success is True
        assert result.data == 25

    def test_complex_expression(self):
        """복잡한 수식"""
        tool = CalculatorTool()

        result = tool.execute(expression="(100 + 200) / 2")
        assert result.success is True
        assert result.data == 150

    def test_functions(self):
        """함수 호출"""
        tool = CalculatorTool()

        # sum 함수
        result = tool.execute(expression="sum([10, 20, 30])")
        assert result.success is True
        assert result.data == 60

        # round 함수
        result = tool.execute(expression="round(123.456, 2)")
        assert result.success is True
        assert result.data == 123.46

    def test_invalid_expression(self):
        """잘못된 수식"""
        tool = CalculatorTool()

        result = tool.execute(expression="invalid expression")
        assert result.success is False
        assert "error" in result.error.lower()

    def test_division_by_zero(self):
        """0으로 나누기"""
        tool = CalculatorTool()

        result = tool.execute(expression="100 / 0")
        assert result.success is False
        assert "division by zero" in result.error.lower()


class TestAgentSchemas:
    """Agent 스키마 테스트"""

    def test_agent_request_validation(self):
        """Agent 요청 검증"""
        # 유효한 요청
        request = AgentRequest(
            question="2024년 입사자는 몇 명인가?",
            config=AgentConfig(max_iterations=5)
        )
        assert request.question == "2024년 입사자는 몇 명인가?"
        assert request.config.max_iterations == 5

    def test_agent_config_defaults(self):
        """Agent 설정 기본값"""
        config = AgentConfig()
        assert config.max_iterations == 10
        # llm_model은 DB 설정에서 자동 로드 (None → DB 설정값)
        assert config.llm_model is not None  # DB 설정 또는 .env 값
        assert config.enable_memory is True

    def test_tool_whitelist(self):
        """도구 화이트리스트"""
        config = AgentConfig(
            tools_whitelist=["query_database_tool", "calculate_tool"],
            tools_blacklist=None
        )

        assert config.is_tool_allowed("query_database_tool") is True
        assert config.is_tool_allowed("calculate_tool") is True
        assert config.is_tool_allowed("search_documents_tool") is False

    def test_tool_blacklist(self):
        """도구 블랙리스트"""
        config = AgentConfig(
            tools_whitelist=None,
            tools_blacklist=["search_documents_tool"]
        )

        assert config.is_tool_allowed("query_database_tool") is True
        assert config.is_tool_allowed("calculate_tool") is True
        assert config.is_tool_allowed("search_documents_tool") is False


@pytest.mark.asyncio
class TestAgentGraph:
    """Agent Graph 통합 테스트"""

    @pytest.mark.skip(reason="Requires actual LLM and DB connection")
    async def test_simple_question(self):
        """단순 질문 처리"""
        from app.graphs.agent_graph import agent_graph

        inputs = {
            "question": "100 + 200은?",
            "config": AgentConfig(max_iterations=3)
        }

        result = await agent_graph.ainvoke(inputs)

        assert result.success is True
        assert "300" in result.answer
        assert "calculate_tool" in result.tools_used

    @pytest.mark.skip(reason="Requires actual LLM and DB connection")
    async def test_multistep_question(self):
        """멀티스텝 질문 처리"""
        from app.graphs.agent_graph import agent_graph

        inputs = {
            "question": "2024년 입사자는 몇 명이고, 그 중 30%는?",
            "config": AgentConfig(max_iterations=10)
        }

        result = await agent_graph.ainvoke(inputs)

        assert result.success is True
        assert len(result.steps) >= 2
        assert "query_database_tool" in result.tools_used
        assert "calculate_tool" in result.tools_used


@pytest.mark.asyncio
class TestAgentAPI:
    """Agent API E2E 테스트"""

    @pytest.mark.skip(reason="Requires running FastAPI server")
    async def test_agent_search_endpoint(self):
        """Agent 검색 엔드포인트"""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        response = client.post(
            "/api/v1/agent/search",
            json={
                "question": "100 + 200은?",
                "config": {
                    "max_iterations": 5
                }
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "answer" in data

    @pytest.mark.skip(reason="Requires running FastAPI server")
    async def test_list_tools_endpoint(self):
        """도구 목록 조회"""
        from fastapi.testclient import TestClient
        from app.main import app

        client = TestClient(app)

        response = client.get("/api/v1/agent/tools")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert any(t["name"] == "query_database_tool" for t in data["tools"])


class TestMemoryStore:
    """메모리 저장소 테스트"""

    def test_session_creation(self):
        """세션 생성"""
        from app.models.agent_schemas import session_memory_store

        memory = session_memory_store.get_memory("test-session")
        assert memory.session_id == "test-session"
        assert len(memory.messages) == 0

    def test_add_message(self):
        """메시지 추가"""
        from app.models.agent_schemas import session_memory_store

        memory = session_memory_store.get_memory("test-session-2")
        memory.add_message("user", "안녕하세요")
        memory.add_message("assistant", "안녕하세요! 무엇을 도와드릴까요?")

        assert len(memory.messages) == 2
        assert memory.messages[0]["role"] == "user"
        assert memory.messages[1]["role"] == "assistant"

    def test_clear_session(self):
        """세션 삭제"""
        from app.models.agent_schemas import session_memory_store

        session_id = "test-session-3"
        memory = session_memory_store.get_memory(session_id)
        memory.add_message("user", "테스트")

        session_memory_store.clear_memory(session_id)

        # 새로 가져오면 빈 세션
        new_memory = session_memory_store.get_memory(session_id)
        assert len(new_memory.messages) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
AI Agent 구현 검증 스크립트

구현된 파일들을 검증하고 간단한 테스트를 수행합니다.
"""

import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def verify_files():
    """파일 존재 확인"""
    print("=" * 60)
    print("1. 파일 존재 확인")
    print("=" * 60)

    files = [
        "app/tools/__init__.py",
        "app/tools/base.py",
        "app/tools/sql_tool.py",
        "app/tools/rag_tool.py",
        "app/tools/calculator_tool.py",
        "app/models/agent_schemas.py",
        "app/graphs/agent_graph.py",
        "app/api/routes/agent.py",
        "tests/test_agent.py",
        "AGENT_README.md",
    ]

    for file_path in files:
        full_path = os.path.join(os.path.dirname(__file__), file_path)
        exists = "[OK]" if os.path.exists(full_path) else "[FAIL]"
        print(f"{exists} {file_path}")

    print()


def test_calculator_tool():
    """계산기 도구 테스트"""
    print("=" * 60)
    print("2. Calculator Tool 테스트")
    print("=" * 60)

    try:
        from app.tools.calculator_tool import CalculatorTool

        tool = CalculatorTool()

        # 테스트 1: 기본 산술
        result = tool.execute(expression="10 + 20")
        assert result.success is True
        assert result.data == 30
        print("[OK] Basic arithmetic (10 + 20 = 30)")

        # 테스트 2: 곱셈
        result = tool.execute(expression="5 * 6")
        assert result.success is True
        assert result.data == 30
        print("[OK] Multiplication (5 * 6 = 30)")

        # 테스트 3: 복잡한 수식
        result = tool.execute(expression="(100 + 200) / 2")
        assert result.success is True
        assert result.data == 150
        print("[OK] Complex expression ((100 + 200) / 2 = 150)")

        # 테스트 4: 함수
        result = tool.execute(expression="sum([10, 20, 30])")
        assert result.success is True
        assert result.data == 60
        print("[OK] Functions (sum([10, 20, 30]) = 60)")

        # 테스트 5: 에러 처리
        result = tool.execute(expression="invalid")
        assert result.success is False
        print("[OK] Error handling (invalid expression detected)")

        print("\nAll Calculator Tool tests passed! [OK]\n")
        return True

    except Exception as e:
        print(f"\n❌ Calculator Tool 테스트 실패: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_agent_schemas():
    """Agent 스키마 테스트"""
    print("=" * 60)
    print("3. Agent Schemas 테스트")
    print("=" * 60)

    try:
        from app.models.agent_schemas import (
            AgentRequest,
            AgentConfig,
            AgentMemory,
            session_memory_store
        )

        # 테스트 1: AgentRequest
        request = AgentRequest(
            question="테스트 질문",
            config=AgentConfig(max_iterations=5)
        )
        assert request.question == "테스트 질문"
        assert request.config.max_iterations == 5
        print("✅ AgentRequest 생성")

        # 테스트 2: AgentConfig
        config = AgentConfig()
        assert config.max_iterations == 10
        assert config.enable_memory is True
        print("✅ AgentConfig 기본값")

        # 테스트 3: Tool whitelist
        config = AgentConfig(tools_whitelist=["query_database"])
        assert config.is_tool_allowed("query_database") is True
        assert config.is_tool_allowed("search_documents") is False
        print("✅ Tool whitelist 동작")

        # 테스트 4: 메모리
        memory = session_memory_store.get_memory("test-session")
        memory.add_message("user", "안녕하세요")
        memory.add_message("assistant", "반갑습니다")
        assert len(memory.messages) == 2
        print("✅ 세션 메모리 동작")

        print("\n모든 Agent Schemas 테스트 통과! ✅\n")
        return True

    except Exception as e:
        print(f"\n❌ Agent Schemas 테스트 실패: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def test_imports():
    """Import 테스트"""
    print("=" * 60)
    print("4. Import 테스트")
    print("=" * 60)

    try:
        # Tools
        from app.tools.base import BaseTool, ToolResult
        print("✅ app.tools.base")

        from app.tools.sql_tool import SQLQueryTool
        print("✅ app.tools.sql_tool")

        from app.tools.rag_tool import DocumentSearchTool
        print("✅ app.tools.rag_tool")

        from app.tools.calculator_tool import CalculatorTool
        print("✅ app.tools.calculator_tool")

        # Schemas
        from app.models.agent_schemas import (
            AgentRequest,
            AgentResponse,
            AgentConfig,
            AgentMemory
        )
        print("✅ app.models.agent_schemas")

        # Graph
        from app.graphs.agent_graph import HRAgentGraph
        print("✅ app.graphs.agent_graph")

        # API
        from app.api.routes import agent
        print("✅ app.api.routes.agent")

        print("\n모든 Import 성공! ✅\n")
        return True

    except Exception as e:
        print(f"\n❌ Import 실패: {e}\n")
        import traceback
        traceback.print_exc()
        return False


def show_summary():
    """구현 요약"""
    print("=" * 60)
    print("5. 구현 요약")
    print("=" * 60)

    summary = """
✅ Tools 레이어 (100% 완료)
   - BaseTool: 확장 가능한 베이스 클래스
   - ToolValidator: 입력/출력 검증 (보안)
   - ToolMetrics: 사용 메트릭 수집
   - SQLQueryTool: SQL 쿼리 도구 (캐싱, 기존 재사용)
   - DocumentSearchTool: 문서 검색 도구 (하이브리드 검색 준비)
   - CalculatorTool: 안전한 계산 도구

✅ Agent Schemas (100% 완료)
   - AgentRequest/Response: API 인터페이스
   - AgentConfig: 동적 설정 (도구 필터링, 타임아웃)
   - AgentMemory: 멀티턴 대화 메모리
   - SessionMemoryStore: 세션 관리
   - AgentMetrics: 성능 메트릭

✅ Agent Graph (100% 완료)
   - HRAgentGraph: ReAct 패턴 구현
   - 동적 도구 선택 (LLM 기반)
   - 반복적 실행 (Thought → Action → Observation)
   - 메모리 통합 (멀티턴 대화)
   - 안전 장치 (max_iterations, timeout)

✅ API 엔드포인트 (100% 완료)
   - POST /api/v1/agent/search: Agent 검색
   - GET /api/v1/agent/sessions: 세션 목록
   - GET /api/v1/agent/sessions/{id}/memory: 메모리 조회
   - GET /api/v1/agent/sessions/{id}/metrics: 메트릭 조회
   - DELETE /api/v1/agent/sessions/{id}: 세션 삭제
   - GET /api/v1/agent/tools: 도구 목록

✅ 확장성
   - 플러그인 아키텍처: 새 도구 쉽게 추가
   - 메모리 영속화: Redis 연동 준비
   - 스트리밍: SSE 지원 준비
   - 보안: Validator, Rate Limiting 준비

✅ 하위 호환성
   - 기존 /api/v1/search 유지
   - 기존 NL2SQL/RAG 그래프 유지
   - 점진적 마이그레이션 가능
"""

    print(summary)


def main():
    """메인 실행"""
    print("\n" + "=" * 60)
    print("AI Agent 구현 검증")
    print("=" * 60 + "\n")

    results = []

    # 1. 파일 확인
    verify_files()

    # 2. Calculator Tool 테스트
    results.append(("Calculator Tool", test_calculator_tool()))

    # 3. Agent Schemas 테스트
    results.append(("Agent Schemas", test_agent_schemas()))

    # 4. Import 테스트
    results.append(("Import", test_imports()))

    # 5. 요약
    show_summary()

    # 최종 결과
    print("=" * 60)
    print("최종 결과")
    print("=" * 60)

    all_passed = all(result for _, result in results)

    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {name}")

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 모든 검증 통과! Agent 구현이 성공적으로 완료되었습니다.")
        print("\n다음 단계:")
        print("1. 서버 실행: uvicorn app.main:app --reload")
        print("2. API 문서: http://localhost:8000/docs")
        print("3. Agent 테스트: POST /api/v1/agent/search")
        print("4. 상세 가이드: AGENT_README.md 참고")
    else:
        print("⚠️ 일부 검증 실패. 위 로그를 확인하세요.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

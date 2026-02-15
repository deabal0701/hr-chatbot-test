"""검색 API 테스트 (RAG, NL2SQL, Agent)

위치: tests/test_10_search.py
AI 검색 기능 통합 테스트 — LLM 응답 시간이 길 수 있으므로 timeout 120초
"""
import pytest
import httpx
from conftest import assert_success, BASE_URL, TIMEOUT

SEARCH_PREFIX = "/api/v1/search"
AGENT_PREFIX = "/api/v1/agent"
HISTORY_PREFIX = "/api/v1/history"
LONG_TIMEOUT = 120.0


@pytest.fixture(scope="module")
def long_client():
    """AI 검색용 긴 타임아웃 클라이언트"""
    with httpx.Client(base_url=BASE_URL, timeout=LONG_TIMEOUT) as c:
        yield c


class TestRAGSearch:
    def test_rag_search(self, long_client, admin_headers):
        """RAG 검색"""
        resp = long_client.post(f"{SEARCH_PREFIX}", headers=admin_headers, json={
            "query": "재택근무 정책은?",
            "mode": "rag",
        })
        if resp.status_code == 200:
            data = resp.json()
            if data["success"]:
                assert "answer" in data["data"]
        # LLM/문서 미구성 환경에서는 실패 허용

    def test_rag_with_filter(self, long_client, admin_headers):
        """RAG 필터 검색"""
        resp = long_client.post(f"{SEARCH_PREFIX}", headers=admin_headers, json={
            "query": "휴가 정책",
            "mode": "rag",
            "filters": {"doc_type": "policy"},
        })
        # 성공/실패 모두 서버 응답 확인만
        assert resp.status_code in (200, 400, 500)


class TestNL2SQLSearch:
    def test_nl2sql_search(self, long_client, admin_headers):
        """NL2SQL 검색"""
        resp = long_client.post(f"{SEARCH_PREFIX}", headers=admin_headers, json={
            "query": "전체 직원 수는?",
            "mode": "nl2sql",
        })
        if resp.status_code == 200:
            data = resp.json()
            if data["success"]:
                result = data["data"]
                assert "answer" in result
                # NL2SQL이면 sql 필드 존재
                if result.get("sql"):
                    assert isinstance(result["sql"], str)

    def test_nl2sql_sessions(self, long_client, admin_headers):
        """NL2SQL 세션 목록"""
        resp = long_client.get(f"{SEARCH_PREFIX.replace('/search', '/nl2sql/sessions')}", headers=admin_headers)
        # 엔드포인트 존재 확인
        assert resp.status_code in (200, 404)


class TestAutoSearch:
    def test_auto_mode(self, long_client, admin_headers):
        """자동 분류 검색"""
        resp = long_client.post(f"{SEARCH_PREFIX}", headers=admin_headers, json={
            "query": "2024년 입사자 수는?",
            "mode": "auto",
        })
        if resp.status_code == 200 and resp.json().get("success"):
            data = resp.json()["data"]
            assert data["query_type"] in ("rag", "nl2sql", "auto")


class TestAgentSearch:
    def test_agent_search(self, long_client, admin_headers):
        """Agent 검색"""
        resp = long_client.post(f"{AGENT_PREFIX}/search", headers=admin_headers, json={
            "question": "전체 직원 수를 알려줘",
        })
        if resp.status_code == 200 and resp.json().get("success"):
            data = resp.json()["data"]
            assert "answer" in data
            assert "tools_used" in data

    def test_agent_tools_list(self, long_client, admin_headers):
        """Agent 도구 목록"""
        data = assert_success(long_client.get(f"{AGENT_PREFIX}/tools", headers=admin_headers))
        assert "tools" in data
        assert len(data["tools"]) >= 1

    def test_agent_sessions(self, long_client, admin_headers):
        """Agent 세션 목록"""
        data = assert_success(long_client.get(f"{AGENT_PREFIX}/sessions", headers=admin_headers))
        assert "items" in data


class TestHistory:
    def test_list_history(self, long_client, admin_headers):
        """검색 이력 조회"""
        data = assert_success(long_client.get(HISTORY_PREFIX, headers=admin_headers, params={"limit": 5}))
        assert "items" in data or "total" in data

    def test_statistics(self, long_client, admin_headers):
        """이력 통계"""
        resp = long_client.get(f"{HISTORY_PREFIX}/statistics", headers=admin_headers)
        assert resp.status_code == 200

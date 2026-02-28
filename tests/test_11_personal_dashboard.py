"""개인 대시보드 API 테스트

위치: tests/test_11_personal_dashboard.py
- 위젯 CRUD (생성/조회/수정/삭제)
- 레이아웃 저장
- SQL 테스트 실행
- 인증 없는 접근 차단
"""
import pytest
from conftest import assert_success, assert_error

PREFIX = "/api/v1/dashboard"


class TestWidgetCRUD:
    """위젯 CRUD 테스트"""
    created_ids = []

    @pytest.fixture(autouse=True, scope="class")
    def _cleanup(self, client, admin_headers):
        """teardown: 테스트 실패 시에도 생성된 위젯 삭제"""
        yield
        for wid in TestWidgetCRUD.created_ids:
            client.delete(f"{PREFIX}/widgets/{wid}", headers=admin_headers)
        TestWidgetCRUD.created_ids.clear()

    def test_create_widget(self, client, admin_headers):
        """위젯 생성 (201)"""
        data = assert_success(client.post(f"{PREFIX}/widgets", headers=admin_headers, json={
            "title": "테스트 바 차트",
            "widget_type": "bar",
            "query": "부서별 직원 수",
            "sql": "SELECT department_name, COUNT(*) as cnt FROM employee GROUP BY department_name",
            "chart_config": {
                "x_column": "department_name",
                "y_columns": ["cnt"]
            },
            "cached_data": {
                "columns": ["department_name", "cnt"],
                "rows": [
                    {"department_name": "개발팀", "cnt": 42},
                    {"department_name": "영업팀", "cnt": 35}
                ],
                "row_count": 2
            }
        }), status_code=201)
        assert data["widget_id"] > 0
        assert data["title"] == "테스트 바 차트"
        assert data["widget_type"] == "bar"
        TestWidgetCRUD.created_ids.append(data["widget_id"])

    def test_create_kpi_widget(self, client, admin_headers):
        """KPI 위젯 생성"""
        data = assert_success(client.post(f"{PREFIX}/widgets", headers=admin_headers, json={
            "title": "전체 직원 수",
            "widget_type": "kpi",
            "query": "전체 직원 수는?",
            "sql": "SELECT COUNT(*) as total FROM employee",
            "chart_config": {
                "kpi_column": "total",
                "kpi_suffix": "명"
            },
            "cached_data": {
                "columns": ["total"],
                "rows": [{"total": 100}],
                "row_count": 1
            }
        }), status_code=201)
        assert data["widget_type"] == "kpi"
        TestWidgetCRUD.created_ids.append(data["widget_id"])

    def test_create_invalid_widget_type(self, client, admin_headers):
        """유효하지 않은 위젯 유형 → 422"""
        resp = client.post(f"{PREFIX}/widgets", headers=admin_headers, json={
            "title": "잘못된 유형",
            "widget_type": "radar"
        })
        assert resp.status_code in (400, 422)

    def test_list_widgets(self, client, admin_headers):
        """위젯 목록 조회"""
        data = assert_success(client.get(f"{PREFIX}/widgets", headers=admin_headers))
        assert "items" in data
        assert "total" in data
        assert data["total"] >= 2

    def test_update_widget(self, client, admin_headers):
        """위젯 수정"""
        wid = TestWidgetCRUD.created_ids[0]
        data = assert_success(client.put(f"{PREFIX}/widgets/{wid}", headers=admin_headers, json={
            "title": "수정된 바 차트",
            "chart_config": {
                "x_column": "department_name",
                "y_columns": ["cnt"],
                "column_aliases": {"department_name": "부서명", "cnt": "인원수"}
            }
        }))
        assert data["title"] == "수정된 바 차트"
        assert data["chart_config"]["column_aliases"]["department_name"] == "부서명"

    def test_update_nonexistent(self, client, admin_headers):
        """존재하지 않는 위젯 수정 → 에러"""
        resp = client.put(f"{PREFIX}/widgets/999999", headers=admin_headers, json={
            "title": "없는 위젯"
        })
        assert resp.status_code in (400, 422, 500)

    def test_delete_widget(self, client, admin_headers):
        """위젯 삭제"""
        wid = TestWidgetCRUD.created_ids.pop()
        data = assert_success(client.delete(f"{PREFIX}/widgets/{wid}", headers=admin_headers))
        assert data["deleted_count"] >= 1

    def test_delete_remaining(self, client, admin_headers):
        """나머지 위젯 삭제"""
        wid = TestWidgetCRUD.created_ids.pop()
        data = assert_success(client.delete(f"{PREFIX}/widgets/{wid}", headers=admin_headers))
        assert data["deleted_count"] >= 1


class TestLayout:
    """레이아웃 저장 테스트"""
    created_ids = []

    @pytest.fixture(autouse=True, scope="class")
    def _cleanup(self, client, admin_headers):
        yield
        for wid in TestLayout.created_ids:
            client.delete(f"{PREFIX}/widgets/{wid}", headers=admin_headers)
        TestLayout.created_ids.clear()

    def test_save_layout(self, client, admin_headers):
        """레이아웃 일괄 저장"""
        # 위젯 2개 생성
        for i in range(2):
            d = assert_success(client.post(f"{PREFIX}/widgets", headers=admin_headers, json={
                "title": f"레이아웃 테스트 {i}",
                "widget_type": "table"
            }), status_code=201)
            TestLayout.created_ids.append(d["widget_id"])

        # 레이아웃 저장
        layout = [
            {"widget_id": TestLayout.created_ids[0], "x": 0, "y": 0, "w": 6, "h": 10},
            {"widget_id": TestLayout.created_ids[1], "x": 6, "y": 0, "w": 6, "h": 10}
        ]
        data = assert_success(client.put(f"{PREFIX}/layout", headers=admin_headers, json={
            "layout": layout
        }))
        assert data["updated_count"] == 2

    def test_save_layout_invalid_widget(self, client, admin_headers):
        """존재하지 않는 위젯 레이아웃 저장 → 에러"""
        resp = client.put(f"{PREFIX}/layout", headers=admin_headers, json={
            "layout": [{"widget_id": 999999, "x": 0, "y": 0, "w": 6, "h": 10}]
        })
        assert resp.status_code in (400, 422, 500)


class TestExecuteSql:
    """SQL 테스트 실행"""

    def test_execute_sql_success(self, client, admin_headers):
        """SQL 실행 성공"""
        data = assert_success(client.post(f"{PREFIX}/execute-sql", headers=admin_headers, json={
            "sql": "SELECT 1 as val"
        }))
        assert "columns" in data
        assert "rows" in data
        assert "row_count" in data
        assert "execution_time_ms" in data

    def test_execute_sql_invalid(self, client, admin_headers):
        """유효하지 않은 SQL → 에러"""
        resp = client.post(f"{PREFIX}/execute-sql", headers=admin_headers, json={
            "sql": "DROP TABLE employee"
        })
        assert resp.status_code in (400, 422, 500)

    def test_execute_sql_empty(self, client, admin_headers):
        """빈 SQL → 422"""
        resp = client.post(f"{PREFIX}/execute-sql", headers=admin_headers, json={
            "sql": ""
        })
        assert resp.status_code in (400, 422)


class TestAuth:
    """인증 검증"""

    def test_no_auth_list(self, client):
        """인증 없이 위젯 목록 조회 → 401"""
        resp = client.get(f"{PREFIX}/widgets")
        assert resp.status_code == 401

    def test_no_auth_create(self, client):
        """인증 없이 위젯 생성 → 401"""
        resp = client.post(f"{PREFIX}/widgets", json={
            "title": "무인증",
            "widget_type": "table"
        })
        assert resp.status_code == 401

    def test_no_auth_execute_sql(self, client):
        """인증 없이 SQL 실행 → 401"""
        resp = client.post(f"{PREFIX}/execute-sql", json={
            "sql": "SELECT 1"
        })
        assert resp.status_code == 401

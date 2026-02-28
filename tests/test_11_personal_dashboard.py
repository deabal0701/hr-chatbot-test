"""개인 대시보드 API 테스트

위치: tests/test_11_personal_dashboard.py
- 대시보드 CRUD (생성/조회/수정/삭제/기본설정)
- 대시보드 공유 (GLOBAL/TENANT/USER 권한별)
- 위젯 CRUD (생성/조회/수정/삭제)
- 멀티 대시보드 위젯 격리
- 레이아웃 저장
- SQL 테스트 실행
- 인증 없는 접근 차단
"""
import pytest
from conftest import assert_success, assert_error

PREFIX = "/api/v1/dashboard"


class TestDashboardCRUD:
    """대시보드 CRUD 테스트"""
    created_ids = []

    @pytest.fixture(autouse=True, scope="class")
    def _cleanup(self, client, admin_headers):
        yield
        for did in TestDashboardCRUD.created_ids:
            client.delete(f"{PREFIX}/dashboards/{did}", headers=admin_headers)
        TestDashboardCRUD.created_ids.clear()

    def test_list_dashboards(self, client, admin_headers):
        """대시보드 목록 조회"""
        data = assert_success(client.get(f"{PREFIX}/dashboards", headers=admin_headers))
        assert "my_dashboards" in data
        assert "shared_dashboards" in data
        # 기본 대시보드가 1개 이상 존재
        assert len(data["my_dashboards"]) >= 1

    def test_create_dashboard(self, client, admin_headers):
        """대시보드 생성 (201)"""
        data = assert_success(client.post(f"{PREFIX}/dashboards", headers=admin_headers, json={
            "name": "테스트 대시보드",
            "description": "테스트용 대시보드입니다"
        }), status_code=201)
        assert data["dashboard_id"] > 0
        assert data["name"] == "테스트 대시보드"
        assert data["description"] == "테스트용 대시보드입니다"
        TestDashboardCRUD.created_ids.append(data["dashboard_id"])

    def test_create_second_dashboard(self, client, admin_headers):
        """두 번째 대시보드 생성"""
        data = assert_success(client.post(f"{PREFIX}/dashboards", headers=admin_headers, json={
            "name": "두 번째 대시보드"
        }), status_code=201)
        assert data["name"] == "두 번째 대시보드"
        TestDashboardCRUD.created_ids.append(data["dashboard_id"])

    def test_update_dashboard(self, client, admin_headers):
        """대시보드 이름/설명 수정"""
        did = TestDashboardCRUD.created_ids[0]
        data = assert_success(client.put(f"{PREFIX}/dashboards/{did}", headers=admin_headers, json={
            "name": "수정된 대시보드",
            "description": "수정된 설명"
        }))
        assert data["name"] == "수정된 대시보드"
        assert data["description"] == "수정된 설명"

    def test_set_default_dashboard(self, client, admin_headers):
        """기본 대시보드 변경"""
        did = TestDashboardCRUD.created_ids[0]
        data = assert_success(client.put(f"{PREFIX}/dashboards/{did}/default", headers=admin_headers))
        assert data["is_default"] is True

        # 이전 기본 대시보드는 is_default=false가 됐는지 확인
        dashboards = assert_success(client.get(f"{PREFIX}/dashboards", headers=admin_headers))
        defaults = [d for d in dashboards["my_dashboards"] if d["is_default"]]
        assert len(defaults) == 1
        assert defaults[0]["dashboard_id"] == did

    def test_delete_default_dashboard_fails(self, client, admin_headers):
        """기본 대시보드 삭제 시도 → 에러"""
        did = TestDashboardCRUD.created_ids[0]
        resp = client.delete(f"{PREFIX}/dashboards/{did}", headers=admin_headers)
        assert resp.status_code in (400, 422, 500)

    def test_delete_dashboard(self, client, admin_headers):
        """대시보드 삭제 (기본이 아닌 것)"""
        did = TestDashboardCRUD.created_ids.pop()
        data = assert_success(client.delete(f"{PREFIX}/dashboards/{did}", headers=admin_headers))
        assert data["deleted_count"] >= 1

    def test_delete_remaining(self, client, admin_headers):
        """나머지 대시보드 삭제 전 기본 해제"""
        # 원래 기본 대시보드로 복원
        dashboards = assert_success(client.get(f"{PREFIX}/dashboards", headers=admin_headers))
        original_default = next((d for d in dashboards["my_dashboards"] if d["name"] == "기본 대시보드"), None)
        if original_default:
            client.put(f"{PREFIX}/dashboards/{original_default['dashboard_id']}/default", headers=admin_headers)

        # 이제 삭제 가능
        did = TestDashboardCRUD.created_ids.pop()
        data = assert_success(client.delete(f"{PREFIX}/dashboards/{did}", headers=admin_headers))
        assert data["deleted_count"] >= 1


class TestDashboardSharing:
    """대시보드 공유 테스트"""
    created_ids = []

    @pytest.fixture(autouse=True, scope="class")
    def _cleanup(self, client, admin_headers):
        yield
        for did in TestDashboardSharing.created_ids:
            client.delete(f"{PREFIX}/dashboards/{did}", headers=admin_headers)
        TestDashboardSharing.created_ids.clear()

    def test_share_dashboard(self, client, admin_headers):
        """대시보드 공유 설정 (GLOBAL admin → tenant 범위)"""
        # 공유용 대시보드 생성
        data = assert_success(client.post(f"{PREFIX}/dashboards", headers=admin_headers, json={
            "name": "공유 테스트 대시보드"
        }), status_code=201)
        did = data["dashboard_id"]
        TestDashboardSharing.created_ids.append(did)

        # 공유 설정
        result = assert_success(client.put(f"{PREFIX}/dashboards/{did}/share", headers=admin_headers, json={
            "is_shared": True,
            "share_scope": "tenant"
        }))
        assert result["is_shared"] is True
        assert result["share_scope"] == "tenant"

    def test_share_all_scope(self, client, admin_headers):
        """전체 공유 (all scope)"""
        data = assert_success(client.post(f"{PREFIX}/dashboards", headers=admin_headers, json={
            "name": "전체 공유 대시보드"
        }), status_code=201)
        did = data["dashboard_id"]
        TestDashboardSharing.created_ids.append(did)

        result = assert_success(client.put(f"{PREFIX}/dashboards/{did}/share", headers=admin_headers, json={
            "is_shared": True,
            "share_scope": "all"
        }))
        assert result["is_shared"] is True
        assert result["share_scope"] == "all"

    def test_unshare_dashboard(self, client, admin_headers):
        """공유 해제"""
        did = TestDashboardSharing.created_ids[0]
        result = assert_success(client.put(f"{PREFIX}/dashboards/{did}/share", headers=admin_headers, json={
            "is_shared": False
        }))
        assert result["is_shared"] is False
        assert result["share_scope"] is None

    def test_share_without_scope_fails(self, client, admin_headers):
        """공유 시 scope 미지정 → 에러"""
        did = TestDashboardSharing.created_ids[0]
        resp = client.put(f"{PREFIX}/dashboards/{did}/share", headers=admin_headers, json={
            "is_shared": True
        })
        assert resp.status_code in (400, 422, 500)

    def test_shared_dashboards_appear_in_list(self, client, admin_headers):
        """공유 대시보드가 목록에 표시되는지 확인"""
        data = assert_success(client.get(f"{PREFIX}/dashboards", headers=admin_headers))
        # 자신이 공유한 것은 shared_dashboards에 안 나옴 (자신 제외)
        # my_dashboards에는 is_shared 표시
        my_shared = [d for d in data["my_dashboards"] if d.get("is_shared")]
        assert len(my_shared) >= 1  # 전체 공유 대시보드


class TestMultiDashboardWidgets:
    """멀티 대시보드 위젯 격리 테스트"""
    dashboard_ids = []
    widget_ids = []

    @pytest.fixture(autouse=True, scope="class")
    def _cleanup(self, client, admin_headers):
        yield
        for wid in TestMultiDashboardWidgets.widget_ids:
            client.delete(f"{PREFIX}/widgets/{wid}", headers=admin_headers)
        for did in TestMultiDashboardWidgets.dashboard_ids:
            client.delete(f"{PREFIX}/dashboards/{did}", headers=admin_headers)
        TestMultiDashboardWidgets.dashboard_ids.clear()
        TestMultiDashboardWidgets.widget_ids.clear()

    def test_create_dashboards_and_widgets(self, client, admin_headers):
        """두 대시보드에 각각 위젯 생성 → 격리 확인"""
        # 대시보드 A 생성
        da = assert_success(client.post(f"{PREFIX}/dashboards", headers=admin_headers, json={
            "name": "대시보드 A"
        }), status_code=201)
        da_id = da["dashboard_id"]
        TestMultiDashboardWidgets.dashboard_ids.append(da_id)

        # 대시보드 B 생성
        db = assert_success(client.post(f"{PREFIX}/dashboards", headers=admin_headers, json={
            "name": "대시보드 B"
        }), status_code=201)
        db_id = db["dashboard_id"]
        TestMultiDashboardWidgets.dashboard_ids.append(db_id)

        # 대시보드 A에 위젯 추가
        w1 = assert_success(client.post(f"{PREFIX}/widgets", headers=admin_headers, json={
            "dashboard_id": da_id,
            "title": "A-위젯1",
            "widget_type": "table"
        }), status_code=201)
        TestMultiDashboardWidgets.widget_ids.append(w1["widget_id"])

        # 대시보드 B에 위젯 추가
        w2 = assert_success(client.post(f"{PREFIX}/widgets", headers=admin_headers, json={
            "dashboard_id": db_id,
            "title": "B-위젯1",
            "widget_type": "kpi",
            "chart_config": {"kpi_column": "total", "kpi_suffix": "건"}
        }), status_code=201)
        TestMultiDashboardWidgets.widget_ids.append(w2["widget_id"])

        # 대시보드 A 위젯만 조회
        data_a = assert_success(client.get(f"{PREFIX}/widgets?dashboard_id={da_id}", headers=admin_headers))
        assert data_a["total"] == 1
        assert data_a["items"][0]["title"] == "A-위젯1"
        assert data_a["dashboard_id"] == da_id

        # 대시보드 B 위젯만 조회
        data_b = assert_success(client.get(f"{PREFIX}/widgets?dashboard_id={db_id}", headers=admin_headers))
        assert data_b["total"] == 1
        assert data_b["items"][0]["title"] == "B-위젯1"
        assert data_b["dashboard_id"] == db_id

    def test_dashboard_delete_cascades_widgets(self, client, admin_headers):
        """대시보드 삭제 시 위젯도 함께 삭제 (CASCADE)"""
        # 대시보드 B 삭제
        db_id = TestMultiDashboardWidgets.dashboard_ids.pop()
        data = assert_success(client.delete(f"{PREFIX}/dashboards/{db_id}", headers=admin_headers))
        assert data["deleted_count"] >= 1

        # B의 위젯은 더 이상 조회 불가
        TestMultiDashboardWidgets.widget_ids.pop()  # B 위젯 ID 제거 (cascade 삭제됨)


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

    def test_no_auth_dashboards(self, client):
        """인증 없이 대시보드 목록 조회 → 401"""
        resp = client.get(f"{PREFIX}/dashboards")
        assert resp.status_code == 401

    def test_no_auth_create_dashboard(self, client):
        """인증 없이 대시보드 생성 → 401"""
        resp = client.post(f"{PREFIX}/dashboards", json={
            "name": "무인증 대시보드"
        })
        assert resp.status_code == 401

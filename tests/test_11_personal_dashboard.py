"""개인 대시보드 통합 테스트

위치: tests/test_12_personal_dashboard.py
- 대시보드 생명주기 (생성 → 기본설정 → 수정 → 삭제)
- 위젯 CRUD + dashboard_id 필수 검증
- 공유 대시보드 cross-user 가시성 테스트
- 마지막(기본) 대시보드 삭제 허용
- 레이아웃 저장 + dashboard_id 필수 검증
"""
import os
import pytest
from conftest import assert_success, assert_error

PREFIX = "/api/v1/dashboard"
ADMIN_ID = os.getenv("TEST_ADMIN_ID", "admin")
ADMIN_PW = os.getenv("TEST_ADMIN_PW", "Win1234!")
USER01_ID = os.getenv("TEST_USER01_ID", "user01")
USER01_PW = os.getenv("TEST_USER01_PW", "Win1234!")


def _login(client, login_id, password):
    """로그인 헬퍼"""
    resp = client.post("/api/v1/auth/login", json={
        "login_id": login_id, "password": password,
    })
    assert resp.status_code == 200, f"{login_id} 로그인 실패: {resp.text}"
    body = resp.json()
    assert body["success"] is True, f"{login_id} 로그인 응답 실패: {body}"
    return body["data"]["access_token"]


# ── admin Fixture (비밀번호 오버라이드) ──

@pytest.fixture(scope="module")
def admin_token(client):
    """admin 로그인 → access_token"""
    return _login(client, ADMIN_ID, ADMIN_PW)


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """admin 인증 헤더"""
    return {"Authorization": f"Bearer {admin_token}"}


# ── user01 Fixture ──

@pytest.fixture(scope="module")
def user01_token(client):
    """user01 로그인 → access_token"""
    return _login(client, USER01_ID, USER01_PW)


@pytest.fixture(scope="module")
def user01_headers(user01_token):
    """user01 인증 헤더"""
    return {"Authorization": f"Bearer {user01_token}"}


# ── Helper ──

def cleanup_user01_dashboards(client, user01_headers):
    """user01의 모든 대시보드 삭제 (테스트 격리용)"""
    data = assert_success(client.get(f"{PREFIX}/dashboards", headers=user01_headers))
    my_dbs = data.get("my_dashboards", [])

    # 기본이 아닌 것 먼저 삭제
    for db in my_dbs:
        if not db.get("is_default"):
            client.delete(f"{PREFIX}/dashboards/{db['dashboard_id']}", headers=user01_headers)

    # 기본 대시보드 삭제 (마지막이면 허용)
    data = assert_success(client.get(f"{PREFIX}/dashboards", headers=user01_headers))
    for db in data.get("my_dashboards", []):
        client.delete(f"{PREFIX}/dashboards/{db['dashboard_id']}", headers=user01_headers)


# ============================================
# 1. 대시보드 생명주기 (user01 기준)
# ============================================

class TestDashboardLifecycle:
    """대시보드 생성 → 기본설정 → 수정 → 삭제 전체 흐름 (user01)"""

    @pytest.fixture(autouse=True, scope="class")
    def _cleanup(self, client, user01_headers):
        """사전/사후 정리: user01 대시보드 초기화"""
        cleanup_user01_dashboards(client, user01_headers)
        yield
        cleanup_user01_dashboards(client, user01_headers)

    def test_01_no_dashboards_initially(self, client, user01_headers):
        """user01 초기 상태: 내 대시보드 없음"""
        data = assert_success(client.get(f"{PREFIX}/dashboards", headers=user01_headers))
        assert len(data["my_dashboards"]) == 0

    def test_02_create_first_dashboard_auto_default(self, client, user01_headers):
        """첫 번째 대시보드 → 자동으로 is_default=true"""
        data = assert_success(client.post(f"{PREFIX}/dashboards", headers=user01_headers, json={
            "name": "첫 번째 대시보드"
        }), status_code=201)
        assert data["name"] == "첫 번째 대시보드"
        assert data["is_default"] is True
        self.__class__.first_id = data["dashboard_id"]

    def test_03_create_second_dashboard_not_default(self, client, user01_headers):
        """두 번째 대시보드 → is_default=false"""
        data = assert_success(client.post(f"{PREFIX}/dashboards", headers=user01_headers, json={
            "name": "두 번째 대시보드"
        }), status_code=201)
        assert data["is_default"] is False
        self.__class__.second_id = data["dashboard_id"]

    def test_04_list_shows_both(self, client, user01_headers):
        """대시보드 목록에 2개 표시"""
        data = assert_success(client.get(f"{PREFIX}/dashboards", headers=user01_headers))
        assert len(data["my_dashboards"]) == 2
        defaults = [d for d in data["my_dashboards"] if d["is_default"]]
        assert len(defaults) == 1

    def test_05_update_dashboard_name(self, client, user01_headers):
        """대시보드 이름 수정"""
        data = assert_success(client.put(
            f"{PREFIX}/dashboards/{self.second_id}", headers=user01_headers,
            json={"name": "수정된 두번째", "description": "설명 추가"}
        ))
        assert data["name"] == "수정된 두번째"
        assert data["description"] == "설명 추가"

    def test_06_set_default_dashboard(self, client, user01_headers):
        """기본 대시보드 변경"""
        data = assert_success(client.put(
            f"{PREFIX}/dashboards/{self.second_id}/default", headers=user01_headers
        ))
        assert data["is_default"] is True

        # 기존 기본은 해제됨
        dashboards = assert_success(client.get(f"{PREFIX}/dashboards", headers=user01_headers))
        defaults = [d for d in dashboards["my_dashboards"] if d["is_default"]]
        assert len(defaults) == 1
        assert defaults[0]["dashboard_id"] == self.second_id

    def test_07_delete_default_with_others_fails(self, client, user01_headers):
        """기본 대시보드 삭제 (다른 대시보드 존재) → 400"""
        resp = client.delete(f"{PREFIX}/dashboards/{self.second_id}", headers=user01_headers)
        assert resp.status_code == 400
        error = assert_error(resp, expected_code="VALIDATION_ERROR")
        assert "기본" in error["detail"]

    def test_08_delete_non_default(self, client, user01_headers):
        """기본 아닌 대시보드 삭제 → 성공"""
        data = assert_success(client.delete(
            f"{PREFIX}/dashboards/{self.first_id}", headers=user01_headers
        ))
        assert data["deleted_count"] == 1

    def test_09_delete_last_default_dashboard(self, client, user01_headers):
        """마지막 대시보드(기본) 삭제 → 허용"""
        data = assert_success(client.delete(
            f"{PREFIX}/dashboards/{self.second_id}", headers=user01_headers
        ))
        assert data["deleted_count"] == 1

        # 삭제 후 0개 확인
        list_data = assert_success(client.get(f"{PREFIX}/dashboards", headers=user01_headers))
        assert len(list_data["my_dashboards"]) == 0

    def test_10_other_user_dashboard_not_visible(self, client, user01_headers):
        """다른 사용자(admin)의 비공유 대시보드는 user01에게 보이지 않음"""
        data = assert_success(client.get(f"{PREFIX}/dashboards", headers=user01_headers))
        # admin의 비공유 대시보드가 shared_dashboards에 없어야 함
        for sd in data["shared_dashboards"]:
            assert sd.get("is_shared") is True


# ============================================
# 2. 위젯 CRUD + dashboard_id 필수 검증
# ============================================

class TestWidgetWithDashboardId:
    """위젯 생성 시 dashboard_id 필수 검증 + CRUD"""

    @pytest.fixture(autouse=True, scope="class")
    def _setup_cleanup(self, client, user01_headers):
        """대시보드 1개 생성 → 테스트 → 정리"""
        cleanup_user01_dashboards(client, user01_headers)

        data = assert_success(client.post(f"{PREFIX}/dashboards", headers=user01_headers, json={
            "name": "위젯 테스트 대시보드"
        }), status_code=201)
        self.__class__.dashboard_id = data["dashboard_id"]
        self.__class__.widget_ids = []
        yield
        cleanup_user01_dashboards(client, user01_headers)

    def test_01_create_widget_without_dashboard_id_fails(self, client, user01_headers):
        """dashboard_id 없이 위젯 생성 → 400 에러"""
        resp = client.post(f"{PREFIX}/widgets", headers=user01_headers, json={
            "title": "dashboard_id 없는 위젯",
            "widget_type": "table",
            "query": "테스트",
            "sql": "SELECT 1"
        })
        assert resp.status_code == 400
        error = assert_error(resp, expected_code="VALIDATION_ERROR")
        assert "dashboard_id" in error["detail"]

    def test_02_create_widget_with_null_dashboard_id_fails(self, client, user01_headers):
        """dashboard_id=null로 위젯 생성 → 400 에러 (프론트 에러 재현)"""
        resp = client.post(f"{PREFIX}/widgets", headers=user01_headers, json={
            "dashboard_id": None,
            "title": "null dashboard_id 위젯",
            "widget_type": "bar",
            "query": "테스트 질문",
            "sql": "SELECT 1 as val",
            "chart_config": {"x_column": "val", "y_columns": ["val"]}
        })
        assert resp.status_code == 400
        error = assert_error(resp, expected_code="VALIDATION_ERROR")
        assert "dashboard_id" in error["detail"]

    def test_03_create_widget_with_dashboard_id(self, client, user01_headers):
        """dashboard_id 포함 위젯 생성 → 성공 (201)"""
        data = assert_success(client.post(f"{PREFIX}/widgets", headers=user01_headers, json={
            "dashboard_id": self.dashboard_id,
            "title": "부서별 직원수",
            "widget_type": "bar",
            "query": "부서별 직원수",
            "sql": "SELECT department_name, COUNT(*) as cnt FROM employee GROUP BY department_name",
            "chart_config": {
                "x_column": "department_name",
                "y_columns": ["cnt"]
            },
            "cached_data": {
                "columns": ["department_name", "cnt"],
                "rows": [{"department_name": "개발팀", "cnt": 42}],
                "row_count": 1
            }
        }), status_code=201)
        assert data["widget_id"] > 0
        assert data["title"] == "부서별 직원수"
        assert data["widget_type"] == "bar"
        assert data["chart_config"]["x_column"] == "department_name"
        self.__class__.widget_ids.append(data["widget_id"])

    def test_04_create_kpi_widget(self, client, user01_headers):
        """KPI 위젯 생성"""
        data = assert_success(client.post(f"{PREFIX}/widgets", headers=user01_headers, json={
            "dashboard_id": self.dashboard_id,
            "title": "전체 직원수",
            "widget_type": "kpi",
            "query": "전체 직원수",
            "sql": "SELECT COUNT(*) as total FROM employee",
            "chart_config": {"kpi_column": "total", "kpi_suffix": "명"},
            "cached_data": {
                "columns": ["total"],
                "rows": [{"total": 342}],
                "row_count": 1
            }
        }), status_code=201)
        assert data["widget_type"] == "kpi"
        self.__class__.widget_ids.append(data["widget_id"])

    def test_05_list_widgets_by_dashboard(self, client, user01_headers):
        """특정 대시보드 위젯 조회"""
        data = assert_success(client.get(
            f"{PREFIX}/widgets?dashboard_id={self.dashboard_id}", headers=user01_headers
        ))
        assert data["total"] == 2
        assert data["dashboard_id"] == self.dashboard_id
        assert data["is_read_only"] is False
        titles = {w["title"] for w in data["items"]}
        assert "부서별 직원수" in titles
        assert "전체 직원수" in titles

    def test_06_update_widget(self, client, user01_headers):
        """위젯 제목/설정 수정"""
        wid = self.widget_ids[0]
        data = assert_success(client.put(f"{PREFIX}/widgets/{wid}", headers=user01_headers, json={
            "title": "수정된 차트",
            "chart_config": {
                "x_column": "department_name",
                "y_columns": ["cnt"],
                "column_aliases": {"department_name": "부서명", "cnt": "인원수"}
            }
        }))
        assert data["title"] == "수정된 차트"
        assert data["chart_config"]["column_aliases"]["department_name"] == "부서명"

    def test_07_save_layout_with_dashboard_id(self, client, user01_headers):
        """레이아웃 저장 (dashboard_id 필수)"""
        layout = [
            {"widget_id": self.widget_ids[0], "x": 0, "y": 0, "w": 6, "h": 10},
            {"widget_id": self.widget_ids[1], "x": 6, "y": 0, "w": 3, "h": 5},
        ]
        data = assert_success(client.put(f"{PREFIX}/layout", headers=user01_headers, json={
            "dashboard_id": self.dashboard_id,
            "layout": layout
        }))
        assert data["updated_count"] == 2

    def test_08_save_layout_without_dashboard_id_fails(self, client, user01_headers):
        """레이아웃 저장 dashboard_id 없이 → 에러"""
        resp = client.put(f"{PREFIX}/layout", headers=user01_headers, json={
            "layout": [{"widget_id": self.widget_ids[0], "x": 0, "y": 0, "w": 6, "h": 10}]
        })
        assert resp.status_code in (400, 422, 500)

    def test_09_delete_widget(self, client, user01_headers):
        """위젯 삭제"""
        wid = self.widget_ids.pop()
        data = assert_success(client.delete(f"{PREFIX}/widgets/{wid}", headers=user01_headers))
        assert data["deleted_count"] == 1

    def test_10_dashboard_widget_count_updated(self, client, user01_headers):
        """위젯 삭제 후 대시보드 widget_count 반영"""
        data = assert_success(client.get(f"{PREFIX}/dashboards", headers=user01_headers))
        db = next(d for d in data["my_dashboards"] if d["dashboard_id"] == self.dashboard_id)
        assert db["widget_count"] == 1

    def test_11_invalid_widget_type_fails(self, client, user01_headers):
        """유효하지 않은 위젯 유형 → 400 또는 422"""
        resp = client.post(f"{PREFIX}/widgets", headers=user01_headers, json={
            "dashboard_id": self.dashboard_id,
            "title": "잘못된 타입",
            "widget_type": "radar"
        })
        assert resp.status_code in (400, 422)


# ============================================
# 3. 공유 대시보드 cross-user 가시성 테스트
# ============================================

class TestSharedDashboardVisibility:
    """admin이 공유한 대시보드를 user01이 볼 수 있는지 검증"""

    @pytest.fixture(autouse=True, scope="class")
    def _setup_cleanup(self, client, admin_headers, user01_headers):
        """admin: 공유 대시보드 + 위젯 생성 → 테스트 → 정리"""
        # admin 공유용 대시보드 생성
        data = assert_success(client.post(f"{PREFIX}/dashboards", headers=admin_headers, json={
            "name": "공유테스트_admin"
        }), status_code=201)
        self.__class__.shared_db_id = data["dashboard_id"]

        # 위젯 추가
        w = assert_success(client.post(f"{PREFIX}/widgets", headers=admin_headers, json={
            "dashboard_id": self.shared_db_id,
            "title": "공유 위젯",
            "widget_type": "table",
            "cached_data": {
                "columns": ["name"],
                "rows": [{"name": "테스트"}],
                "row_count": 1
            }
        }), status_code=201)
        self.__class__.shared_widget_id = w["widget_id"]

        # 전체 공유 설정
        assert_success(client.put(
            f"{PREFIX}/dashboards/{self.shared_db_id}/share", headers=admin_headers,
            json={"is_shared": True, "share_scope": "all"}
        ))

        yield

        # 정리
        client.delete(f"{PREFIX}/widgets/{self.shared_widget_id}", headers=admin_headers)
        # 공유 해제 후 삭제
        client.put(f"{PREFIX}/dashboards/{self.shared_db_id}/share", headers=admin_headers,
                   json={"is_shared": False})
        client.delete(f"{PREFIX}/dashboards/{self.shared_db_id}", headers=admin_headers)

    def test_01_user01_sees_shared_dashboard(self, client, user01_headers):
        """user01 대시보드 목록에 admin 공유 대시보드 표시"""
        data = assert_success(client.get(f"{PREFIX}/dashboards", headers=user01_headers))
        shared = data["shared_dashboards"]
        found = [d for d in shared if d["dashboard_id"] == self.shared_db_id]
        assert len(found) == 1
        assert found[0]["name"] == "공유테스트_admin"
        assert found[0]["is_shared"] is True
        assert found[0].get("owner_name") is not None

    def test_02_user01_reads_shared_widgets(self, client, user01_headers):
        """user01이 공유 대시보드 위젯 조회 (read-only)"""
        data = assert_success(client.get(
            f"{PREFIX}/widgets?dashboard_id={self.shared_db_id}", headers=user01_headers
        ))
        assert data["total"] == 1
        assert data["is_read_only"] is True
        assert data["items"][0]["title"] == "공유 위젯"

    def test_03_user01_cannot_add_widget_to_shared(self, client, user01_headers):
        """user01이 admin 공유 대시보드에 위젯 추가 → 실패"""
        resp = client.post(f"{PREFIX}/widgets", headers=user01_headers, json={
            "dashboard_id": self.shared_db_id,
            "title": "침입 위젯",
            "widget_type": "table"
        })
        assert resp.status_code in (400, 403, 500)

    def test_04_user01_cannot_delete_shared_widget(self, client, user01_headers):
        """user01이 admin 위젯 삭제 → 실패"""
        resp = client.delete(f"{PREFIX}/widgets/{self.shared_widget_id}", headers=user01_headers)
        assert resp.status_code in (400, 403, 500)

    def test_05_user01_cannot_modify_shared_dashboard(self, client, user01_headers):
        """user01이 admin 대시보드 이름 수정 → 실패"""
        resp = client.put(
            f"{PREFIX}/dashboards/{self.shared_db_id}", headers=user01_headers,
            json={"name": "탈취 대시보드"}
        )
        assert resp.status_code in (400, 403, 500)

    def test_06_unshare_hides_from_user01(self, client, admin_headers, user01_headers):
        """공유 해제 후 user01에게 안 보임"""
        assert_success(client.put(
            f"{PREFIX}/dashboards/{self.shared_db_id}/share", headers=admin_headers,
            json={"is_shared": False}
        ))

        data = assert_success(client.get(f"{PREFIX}/dashboards", headers=user01_headers))
        found = [d for d in data["shared_dashboards"] if d["dashboard_id"] == self.shared_db_id]
        assert len(found) == 0

        # 다시 공유 복원 (다른 테스트 영향 방지)
        assert_success(client.put(
            f"{PREFIX}/dashboards/{self.shared_db_id}/share", headers=admin_headers,
            json={"is_shared": True, "share_scope": "all"}
        ))


# ============================================
# 4. 공유 권한 제한 테스트
# ============================================

class TestSharePermission:
    """USER 역할은 공유 불가, GLOBAL만 all scope 가능"""

    @pytest.fixture(autouse=True, scope="class")
    def _setup_cleanup(self, client, user01_headers):
        """user01 대시보드 1개 생성"""
        cleanup_user01_dashboards(client, user01_headers)
        data = assert_success(client.post(f"{PREFIX}/dashboards", headers=user01_headers, json={
            "name": "user01 공유시도"
        }), status_code=201)
        self.__class__.db_id = data["dashboard_id"]
        yield
        cleanup_user01_dashboards(client, user01_headers)

    def test_01_user_role_cannot_share(self, client, user01_headers):
        """USER 역할은 공유 설정 불가"""
        resp = client.put(
            f"{PREFIX}/dashboards/{self.db_id}/share", headers=user01_headers,
            json={"is_shared": True, "share_scope": "tenant"}
        )
        assert resp.status_code in (400, 403, 500)

    def test_02_share_without_scope_fails(self, client, admin_headers):
        """공유 시 scope 미지정 → 에러"""
        # admin 대시보드로 테스트
        dbs = assert_success(client.get(f"{PREFIX}/dashboards", headers=admin_headers))
        if not dbs["my_dashboards"]:
            pytest.skip("admin 대시보드 없음")
        did = dbs["my_dashboards"][0]["dashboard_id"]
        resp = client.put(
            f"{PREFIX}/dashboards/{did}/share", headers=admin_headers,
            json={"is_shared": True}
        )
        assert resp.status_code in (400, 422, 500)


# ============================================
# 5. SQL 실행 테스트
# ============================================

class TestExecuteSql:
    """SQL 테스트 실행"""

    def test_execute_valid_sql(self, client, admin_headers):
        """유효한 SELECT SQL 실행"""
        data = assert_success(client.post(f"{PREFIX}/execute-sql", headers=admin_headers, json={
            "sql": "SELECT 1 as val"
        }))
        assert "columns" in data
        assert "rows" in data
        assert data["row_count"] >= 1
        assert data["execution_time_ms"] >= 0

    def test_execute_dangerous_sql_blocked(self, client, admin_headers):
        """위험한 SQL (DROP/DELETE 등) 차단"""
        for sql in ["DROP TABLE employee", "DELETE FROM employee", "UPDATE employee SET name='x'"]:
            resp = client.post(f"{PREFIX}/execute-sql", headers=admin_headers, json={"sql": sql})
            assert resp.status_code in (400, 422, 500), f"차단 실패: {sql}"

    def test_execute_empty_sql_fails(self, client, admin_headers):
        """빈 SQL → 422"""
        resp = client.post(f"{PREFIX}/execute-sql", headers=admin_headers, json={"sql": ""})
        assert resp.status_code in (400, 422)


# ============================================
# 6. 인증 검증
# ============================================

class TestAuthRequired:
    """인증 없이 접근 시 401"""

    def test_no_auth_dashboards(self, client):
        resp = client.get(f"{PREFIX}/dashboards")
        assert resp.status_code == 401

    def test_no_auth_create_dashboard(self, client):
        resp = client.post(f"{PREFIX}/dashboards", json={"name": "무인증"})
        assert resp.status_code == 401

    def test_no_auth_widgets(self, client):
        resp = client.get(f"{PREFIX}/widgets")
        assert resp.status_code == 401

    def test_no_auth_create_widget(self, client):
        resp = client.post(f"{PREFIX}/widgets", json={"title": "무인증", "widget_type": "table"})
        assert resp.status_code == 401

    def test_no_auth_execute_sql(self, client):
        resp = client.post(f"{PREFIX}/execute-sql", json={"sql": "SELECT 1"})
        assert resp.status_code == 401

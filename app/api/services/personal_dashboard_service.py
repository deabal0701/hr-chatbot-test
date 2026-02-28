"""개인 대시보드 서비스

위치: app/api/services/personal_dashboard_service.py
- 대시보드 CRUD + 공유 관리
- 위젯 CRUD + SQL 실행 + PII 마스킹
- user_id 기반 소유권 검증 (개인 데이터 격리)
- 공유 대시보드 읽기 전용 접근 지원
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

import psycopg
from psycopg.types.json import Json

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 순환 import 방지를 위해 지연 import
_db_manager = None
_sql_executor = None
_pii_service = None


def _get_db_manager():
    global _db_manager
    if _db_manager is None:
        from app.core.database.connection import db_manager
        _db_manager = db_manager
    return _db_manager


def _get_sql_executor():
    global _sql_executor
    if _sql_executor is None:
        from app.core.database.sql_executor import sql_executor
        _sql_executor = sql_executor
    return _sql_executor


def _get_pii_service():
    global _pii_service
    if _pii_service is None:
        from app.core.pii.pii_service import pii_service
        _pii_service = pii_service
    return _pii_service


class PersonalDashboardService:
    """개인 대시보드 CRUD + 위젯 CRUD + SQL 실행 서비스"""

    MAX_DASHBOARDS_PER_USER = 10
    MAX_WIDGETS_PER_DASHBOARD = 20
    MAX_CACHED_ROWS = 500

    # 위젯 유형별 기본 그리드 크기
    DEFAULT_GRID_SIZES = {
        "kpi": {"w": 3, "h": 5},
        "pie": {"w": 5, "h": 10},
        "table": {"w": 6, "h": 10},
        "bar": {"w": 6, "h": 10},
        "hbar": {"w": 6, "h": 10},
        "line": {"w": 6, "h": 10},
        "scatter": {"w": 6, "h": 10},
    }

    # ============================================
    # 대시보드 CRUD
    # ============================================

    def list_dashboards(self, user_id: int, tenant_id: Optional[int], role_code: str) -> dict:
        """내 대시보드 + 공유 대시보드 목록 조회"""
        db_manager = _get_db_manager()
        with db_manager.get_cursor() as cur:
            # 내 대시보드 (위젯 수 포함)
            cur.execute("""
                SELECT d.*, COALESCE(wc.cnt, 0) as widget_count
                FROM tb_dashboard d
                LEFT JOIN (
                    SELECT dashboard_id, COUNT(*) as cnt
                    FROM tb_dashboard_widget WHERE is_active = true
                    GROUP BY dashboard_id
                ) wc ON d.dashboard_id = wc.dashboard_id
                WHERE d.user_id = %s AND d.is_active = true
                ORDER BY d.is_default DESC, d.sort_order, d.dashboard_id
            """, (user_id,))
            my_rows = cur.fetchall()
            my_dashboards = [self._dashboard_row_to_dict(row) for row in my_rows]

            # 공유 대시보드 (내 것 제외, 소유자 정보 포함)
            cur.execute("""
                SELECT d.*, COALESCE(wc.cnt, 0) as widget_count,
                       u.display_name as owner_name, u.login_id as owner_login_id
                FROM tb_dashboard d
                LEFT JOIN (
                    SELECT dashboard_id, COUNT(*) as cnt
                    FROM tb_dashboard_widget WHERE is_active = true
                    GROUP BY dashboard_id
                ) wc ON d.dashboard_id = wc.dashboard_id
                LEFT JOIN tb_user u ON d.user_id = u.user_id
                WHERE d.is_shared = true AND d.is_active = true AND d.user_id != %s
                AND (
                    d.share_scope = 'all'
                    OR (d.share_scope = 'tenant' AND d.tenant_id = %s)
                )
                ORDER BY d.updated_at DESC
            """, (user_id, tenant_id))
            shared_rows = cur.fetchall()
            shared_dashboards = [self._shared_dashboard_row_to_dict(row) for row in shared_rows]

        return {"my_dashboards": my_dashboards, "shared_dashboards": shared_dashboards}

    def create_dashboard(self, user_id: int, tenant_id: Optional[int], data) -> dict:
        """대시보드 생성"""
        db_manager = _get_db_manager()

        # 대시보드 수 제한 + sort_order + 기본 여부를 단일 커서로 조회
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) as cnt,
                       COALESCE(MAX(sort_order), -1) + 1 as next_sort,
                       COALESCE(SUM(CASE WHEN is_default THEN 1 ELSE 0 END), 0) as default_cnt
                FROM tb_dashboard WHERE user_id = %s AND is_active = true
            """, (user_id,))
            row = cur.fetchone()
            count, next_sort, default_cnt = row["cnt"], row["next_sort"], row["default_cnt"]

        if count >= self.MAX_DASHBOARDS_PER_USER:
            raise ValueError(f"사용자당 최대 {self.MAX_DASHBOARDS_PER_USER}개 대시보드만 생성할 수 있습니다 (현재: {count}개)")

        is_default = default_cnt == 0

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO tb_dashboard (user_id, tenant_id, name, description, is_default, sort_order)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING dashboard_id
            """, (user_id, tenant_id, data.name, data.description, is_default, next_sort))
            dashboard_id = cur.fetchone()["dashboard_id"]

        logger.info(f"[DASHBOARD] 대시보드 생성: dashboard_id={dashboard_id}, user_id={user_id}, name='{data.name}'")
        return self._get_dashboard_with_count(dashboard_id)

    def update_dashboard(self, user_id: int, dashboard_id: int, data) -> dict:
        """대시보드 이름/설명 수정"""
        self._get_dashboard(user_id, dashboard_id)

        set_clauses = []
        params = []

        if data.name is not None:
            set_clauses.append("name = %s")
            params.append(data.name)
        if data.description is not None:
            set_clauses.append("description = %s")
            params.append(data.description)

        if not set_clauses:
            return self._get_dashboard_with_count(dashboard_id)

        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([dashboard_id, user_id])

        db_manager = _get_db_manager()
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(f"""
                UPDATE tb_dashboard SET {', '.join(set_clauses)}
                WHERE dashboard_id = %s AND user_id = %s
            """, params)

        logger.info(f"[DASHBOARD] 대시보드 수정: dashboard_id={dashboard_id}, user_id={user_id}")
        return self._get_dashboard_with_count(dashboard_id)

    def delete_dashboard(self, user_id: int, dashboard_id: int) -> dict:
        """대시보드 삭제 (기본 대시보드는 다른 대시보드가 있으면 변경 필요, 마지막이면 허용)"""
        dashboard = self._get_dashboard(user_id, dashboard_id)
        db_manager = _get_db_manager()

        if dashboard.get("is_default"):
            # 다른 대시보드가 있으면 기본 변경 먼저 필요
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT COUNT(*) as cnt FROM tb_dashboard WHERE user_id = %s AND is_active = true", (user_id,))
                count = cur.fetchone()["cnt"]
            if count > 1:
                raise ValueError("기본 대시보드를 삭제하려면 다른 대시보드를 기본으로 설정해주세요")

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM tb_dashboard WHERE dashboard_id = %s AND user_id = %s", (dashboard_id, user_id))
            deleted = cur.rowcount

        logger.info(f"[DASHBOARD] 대시보드 삭제: dashboard_id={dashboard_id}, user_id={user_id}")
        return {"message": "대시보드가 삭제되었습니다", "deleted_count": deleted}

    def set_default_dashboard(self, user_id: int, dashboard_id: int) -> dict:
        """기본 대시보드 변경"""
        self._get_dashboard(user_id, dashboard_id)

        db_manager = _get_db_manager()
        with db_manager.get_cursor(commit=True) as cur:
            # 기존 기본 해제
            cur.execute("UPDATE tb_dashboard SET is_default = false, updated_at = CURRENT_TIMESTAMP WHERE user_id = %s AND is_default = true", (user_id,))
            # 새 기본 설정
            cur.execute("UPDATE tb_dashboard SET is_default = true, updated_at = CURRENT_TIMESTAMP WHERE dashboard_id = %s AND user_id = %s", (dashboard_id, user_id))

        logger.info(f"[DASHBOARD] 기본 대시보드 변경: dashboard_id={dashboard_id}, user_id={user_id}")
        return self._get_dashboard_with_count(dashboard_id)

    def share_dashboard(self, user_id: int, dashboard_id: int, role_code: str, data) -> dict:
        """대시보드 공유 설정 (GLOBAL/TENANT만 가능)"""
        if role_code not in ("GLOBAL", "TENANT"):
            raise ValueError("대시보드 공유는 GLOBAL 또는 TENANT 관리자만 가능합니다")

        self._get_dashboard(user_id, dashboard_id)

        # 공유 범위 검증
        share_scope = None
        if data.is_shared:
            if not data.share_scope:
                raise ValueError("공유 설정 시 share_scope(all 또는 tenant)를 지정해야 합니다")
            if role_code == "TENANT" and data.share_scope == "all":
                raise ValueError("TENANT 관리자는 전체 공유(all)를 설정할 수 없습니다")
            share_scope = data.share_scope

        db_manager = _get_db_manager()
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("""
                UPDATE tb_dashboard SET is_shared = %s, share_scope = %s, updated_at = CURRENT_TIMESTAMP
                WHERE dashboard_id = %s AND user_id = %s
            """, (data.is_shared, share_scope, dashboard_id, user_id))

        logger.info(f"[DASHBOARD] 공유 설정: dashboard_id={dashboard_id}, is_shared={data.is_shared}, scope={share_scope}")
        return self._get_dashboard_with_count(dashboard_id)

    # ============================================
    # 위젯 CRUD
    # ============================================

    def list_widgets(self, user_id: int, dashboard_id: Optional[int] = None, tenant_id: Optional[int] = None) -> dict:
        """대시보드 위젯 목록 조회 (공유 대시보드 읽기 허용)"""
        db_manager = _get_db_manager()

        # dashboard_id 미지정 시 기본 대시보드 조회 (자동 생성 없음)
        if dashboard_id is None:
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT dashboard_id FROM tb_dashboard WHERE user_id = %s AND is_default = true AND is_active = true", (user_id,))
                row = cur.fetchone()
            if row:
                dashboard_id = row["dashboard_id"]
            else:
                return {"items": [], "total": 0, "dashboard_id": None, "is_read_only": False}

        # 대시보드 소유권 또는 공유 접근 확인
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT * FROM tb_dashboard WHERE dashboard_id = %s AND is_active = true", (dashboard_id,))
            dashboard = cur.fetchone()

        if not dashboard:
            raise ValueError("대시보드를 찾을 수 없습니다")

        is_owner = dashboard["user_id"] == user_id
        is_shared_access = not is_owner and self._can_view_dashboard(dict(dashboard), user_id, tenant_id)

        if not is_owner and not is_shared_access:
            raise ValueError("접근 권한이 없는 대시보드입니다")

        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT * FROM tb_dashboard_widget
                WHERE dashboard_id = %s AND is_active = true
                ORDER BY sort_order, widget_id
            """, (dashboard_id,))
            rows = cur.fetchall()
            items = [self._row_to_dict(row) for row in rows]

        return {
            "items": items,
            "total": len(items),
            "dashboard_id": dashboard_id,
            "is_read_only": is_shared_access,
        }

    def create_widget(self, user_id: int, tenant_id: Optional[int], data) -> dict:
        """위젯 생성"""
        db_manager = _get_db_manager()

        # dashboard_id 필수 검증
        dashboard_id = data.dashboard_id
        if dashboard_id is None:
            raise ValueError("dashboard_id는 필수입니다. 대시보드를 먼저 생성해주세요.")
        self._get_dashboard(user_id, dashboard_id)

        # 대시보드당 위젯 수 제한 확인
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM tb_dashboard_widget WHERE dashboard_id = %s AND is_active = true", (dashboard_id,))
            count = cur.fetchone()["cnt"]
            if count >= self.MAX_WIDGETS_PER_DASHBOARD:
                raise ValueError(f"대시보드당 최대 {self.MAX_WIDGETS_PER_DASHBOARD}개 위젯만 생성할 수 있습니다 (현재: {count}개)")

        # cached_data 행 수 제한
        cached_data = {}
        if data.cached_data:
            cached_data = data.cached_data.model_dump()
            if len(cached_data.get("rows", [])) > self.MAX_CACHED_ROWS:
                cached_data["rows"] = cached_data["rows"][:self.MAX_CACHED_ROWS]
                cached_data["row_count"] = min(cached_data.get("row_count", 0), len(cached_data["rows"]))
            cached_data["cached_at"] = datetime.now().isoformat()

        chart_config = data.chart_config.model_dump() if data.chart_config else {}
        grid_position = data.grid_position.model_dump() if data.grid_position else self._auto_grid_position(dashboard_id, data.widget_type)

        # sort_order 계산 (마지막 위치)
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 as next_sort FROM tb_dashboard_widget WHERE dashboard_id = %s AND is_active = true", (dashboard_id,))
            next_sort = cur.fetchone()["next_sort"]

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO tb_dashboard_widget
                    (dashboard_id, user_id, tenant_id, title, widget_type, query, sql, chart_config, cached_data, grid_position, sort_order)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING widget_id
            """, (
                dashboard_id, user_id, tenant_id, data.title, data.widget_type,
                data.query, data.sql,
                Json(chart_config), Json(cached_data), Json(grid_position),
                next_sort
            ))
            widget_id = cur.fetchone()["widget_id"]

        logger.info(f"[DASHBOARD] 위젯 생성: widget_id={widget_id}, dashboard_id={dashboard_id}, user_id={user_id}, type={data.widget_type}")
        return self._get_widget(user_id, widget_id)

    def update_widget(self, user_id: int, widget_id: int, data) -> dict:
        """위젯 수정 (변경 필드만 업데이트)"""
        self._get_widget(user_id, widget_id)

        set_clauses = []
        params = []

        if data.title is not None:
            set_clauses.append("title = %s")
            params.append(data.title)
        if data.widget_type is not None:
            set_clauses.append("widget_type = %s")
            params.append(data.widget_type)
        if data.query is not None:
            set_clauses.append("query = %s")
            params.append(data.query)
        if data.sql is not None:
            set_clauses.append("sql = %s")
            params.append(data.sql)
        if data.chart_config is not None:
            set_clauses.append("chart_config = %s")
            params.append(Json(data.chart_config.model_dump()))
        if data.cached_data is not None:
            cd = data.cached_data.model_dump()
            if len(cd.get("rows", [])) > self.MAX_CACHED_ROWS:
                cd["rows"] = cd["rows"][:self.MAX_CACHED_ROWS]
            cd["cached_at"] = datetime.now().isoformat()
            set_clauses.append("cached_data = %s")
            params.append(Json(cd))

        if not set_clauses:
            return self._get_widget(user_id, widget_id)

        set_clauses.append("updated_at = CURRENT_TIMESTAMP")
        params.extend([widget_id, user_id])

        db_manager = _get_db_manager()
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute(f"""
                UPDATE tb_dashboard_widget
                SET {', '.join(set_clauses)}
                WHERE widget_id = %s AND user_id = %s
            """, params)

        logger.info(f"[DASHBOARD] 위젯 수정: widget_id={widget_id}, user_id={user_id}, fields={[c.split(' =')[0] for c in set_clauses[:-1]]}")
        return self._get_widget(user_id, widget_id)

    def delete_widget(self, user_id: int, widget_id: int) -> dict:
        """위젯 삭제"""
        self._get_widget(user_id, widget_id)

        db_manager = _get_db_manager()
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM tb_dashboard_widget WHERE widget_id = %s AND user_id = %s", (widget_id, user_id))
            deleted = cur.rowcount

        logger.info(f"[DASHBOARD] 위젯 삭제: widget_id={widget_id}, user_id={user_id}")
        return {"message": "위젯이 삭제되었습니다", "deleted_count": deleted}

    def save_layout(self, user_id: int, layout: list, dashboard_id: Optional[int] = None, tenant_id: Optional[int] = None) -> dict:
        """레이아웃 일괄 저장"""
        db_manager = _get_db_manager()

        # dashboard_id 필수 검증
        if dashboard_id is None:
            raise ValueError("dashboard_id는 필수입니다. 대시보드를 먼저 생성해주세요.")
        self._get_dashboard(user_id, dashboard_id)

        # 소유권 검증: 모든 widget_id가 해당 대시보드 소속인지
        widget_ids = [item.widget_id for item in layout]
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT widget_id FROM tb_dashboard_widget
                WHERE dashboard_id = %s AND user_id = %s AND widget_id = ANY(%s) AND is_active = true
            """, (dashboard_id, user_id, widget_ids))
            owned_ids = {row["widget_id"] for row in cur.fetchall()}

        invalid_ids = set(widget_ids) - owned_ids
        if invalid_ids:
            raise ValueError(f"접근 권한이 없는 위젯입니다: {invalid_ids}")

        updated = 0
        with db_manager.get_cursor(commit=True) as cur:
            for idx, item in enumerate(layout):
                cur.execute("""
                    UPDATE tb_dashboard_widget
                    SET grid_position = %s, sort_order = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE widget_id = %s AND user_id = %s
                """, (
                    Json({"x": item.x, "y": item.y, "w": item.w, "h": item.h}),
                    idx, item.widget_id, user_id
                ))
                updated += cur.rowcount

        logger.info(f"[DASHBOARD] 레이아웃 저장: dashboard_id={dashboard_id}, user_id={user_id}, updated_count={updated}")
        return {"message": "레이아웃이 저장되었습니다", "updated_count": updated}

    # ============================================
    # SQL 실행
    # ============================================

    def refresh_widget(self, user_id: int, widget_id: int, tenant_id: Optional[int] = None) -> dict:
        """위젯 데이터 새로고침 (소유 위젯 + 공유 대시보드 위젯 모두 허용)"""
        db_manager = _get_db_manager()

        # 위젯 조회
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT * FROM tb_dashboard_widget WHERE widget_id = %s AND is_active = true", (widget_id,))
            widget_row = cur.fetchone()

        if not widget_row:
            raise ValueError("위젯을 찾을 수 없습니다")

        widget = self._row_to_dict(widget_row)
        is_owner = widget_row["user_id"] == user_id

        # 소유자가 아닌 경우 공유 대시보드 접근 확인
        if not is_owner:
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT * FROM tb_dashboard WHERE dashboard_id = %s AND is_active = true", (widget_row["dashboard_id"],))
                dashboard = cur.fetchone()
            if not dashboard or not self._can_view_dashboard(dict(dashboard), user_id, tenant_id):
                raise ValueError("접근 권한이 없는 위젯입니다")

        stored_sql = widget.get("sql")
        if not stored_sql:
            raise ValueError("SQL이 없는 위젯은 새로고침할 수 없습니다")

        executor = _get_sql_executor()
        result = executor.execute_sql(stored_sql)

        # PII 마스킹
        masked_rows = result.rows
        pii_service = _get_pii_service()
        if pii_service.enabled:
            masked_rows, pii_count = pii_service.mask_sql_rows(result.rows, result.columns)
            if pii_count > 0:
                logger.info(f"[DASHBOARD] PII 마스킹: widget_id={widget_id}, pii_count={pii_count}")

        # 행 수 제한
        if len(masked_rows) > self.MAX_CACHED_ROWS:
            masked_rows = masked_rows[:self.MAX_CACHED_ROWS]

        now = datetime.now().isoformat()
        cached_data = {
            "columns": result.columns,
            "rows": masked_rows,
            "row_count": result.row_count,
            "cached_at": now
        }

        # 소유 위젯만 캐시 업데이트 (공유 위젯은 데이터만 반환)
        if is_owner:
            with db_manager.get_cursor(commit=True) as cur:
                cur.execute("""
                    UPDATE tb_dashboard_widget
                    SET cached_data = %s, last_refreshed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
                    WHERE widget_id = %s AND user_id = %s
                """, (Json(cached_data), widget_id, user_id))

        logger.info(f"[DASHBOARD] 위젯 새로고침: widget_id={widget_id}, rows={result.row_count}, time={result.execution_time_ms}ms")
        return {"widget_id": widget_id, "cached_data": cached_data, "last_refreshed_at": now}

    def execute_sql(self, sql: str) -> dict:
        """SQL 테스트 실행 (저장 안함, 미리보기용)"""
        executor = _get_sql_executor()
        result = executor.execute_sql(sql)

        # PII 마스킹
        masked_rows = result.rows
        pii_service = _get_pii_service()
        if pii_service.enabled:
            masked_rows, _ = pii_service.mask_sql_rows(result.rows, result.columns)

        return {
            "columns": result.columns,
            "rows": masked_rows[:self.MAX_CACHED_ROWS],
            "row_count": result.row_count,
            "execution_time_ms": result.execution_time_ms
        }

    # ============================================
    # 내부 메서드
    # ============================================

    def _get_dashboard(self, user_id: int, dashboard_id: int) -> dict:
        """대시보드 조회 + 소유권 검증"""
        db_manager = _get_db_manager()
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT * FROM tb_dashboard WHERE dashboard_id = %s AND user_id = %s AND is_active = true", (dashboard_id, user_id))
            row = cur.fetchone()

        if not row:
            raise ValueError("대시보드를 찾을 수 없습니다")
        return self._dashboard_row_to_dict(row)

    def _get_dashboard_with_count(self, dashboard_id: int) -> dict:
        """대시보드 조회 (위젯 수 포함)"""
        db_manager = _get_db_manager()
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT d.*, COALESCE(wc.cnt, 0) as widget_count
                FROM tb_dashboard d
                LEFT JOIN (
                    SELECT dashboard_id, COUNT(*) as cnt
                    FROM tb_dashboard_widget WHERE is_active = true
                    GROUP BY dashboard_id
                ) wc ON d.dashboard_id = wc.dashboard_id
                WHERE d.dashboard_id = %s
            """, (dashboard_id,))
            row = cur.fetchone()

        if not row:
            raise ValueError("대시보드를 찾을 수 없습니다")
        return self._dashboard_row_to_dict(row)

    def _can_view_dashboard(self, dashboard: dict, user_id: int, tenant_id: Optional[int]) -> bool:
        """공유 대시보드 조회 권한 확인"""
        if dashboard.get("user_id") == user_id:
            return True
        if not dashboard.get("is_shared"):
            return False
        scope = dashboard.get("share_scope")
        if scope == "all":
            return True
        if scope == "tenant" and dashboard.get("tenant_id") == tenant_id:
            return True
        return False

    def _get_widget(self, user_id: int, widget_id: int) -> dict:
        """위젯 조회 + 소유권 검증"""
        db_manager = _get_db_manager()
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT * FROM tb_dashboard_widget
                WHERE widget_id = %s AND user_id = %s AND is_active = true
            """, (widget_id, user_id))
            row = cur.fetchone()

        if not row:
            raise ValueError("위젯을 찾을 수 없습니다")
        return self._row_to_dict(row)

    def _auto_grid_position(self, dashboard_id: int, widget_type: str) -> dict:
        """기존 위젯 배치를 분석하여 빈 위치에 자동 배치"""
        defaults = self.DEFAULT_GRID_SIZES.get(widget_type, {"w": 6, "h": 10})
        w, h = defaults["w"], defaults["h"]

        db_manager = _get_db_manager()
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT grid_position FROM tb_dashboard_widget
                WHERE dashboard_id = %s AND is_active = true
            """, (dashboard_id,))
            rows = cur.fetchall()

        if not rows:
            return {"x": 0, "y": 0, "w": w, "h": h}

        # 기존 위젯들의 최대 y + h 를 계산하여 아래에 배치
        max_bottom = 0
        for row in rows:
            pos = row["grid_position"] if isinstance(row.get("grid_position"), dict) else {}
            bottom = pos.get("y", 0) + pos.get("h", 10)
            if bottom > max_bottom:
                max_bottom = bottom

        return {"x": 0, "y": max_bottom, "w": w, "h": h}

    @staticmethod
    def _row_to_dict(row) -> dict:
        """DB row를 딕셔너리로 변환"""
        if isinstance(row, dict):
            d = dict(row)
        else:
            d = dict(row._asdict()) if hasattr(row, '_asdict') else dict(row)

        for key in ("created_at", "updated_at", "last_refreshed_at"):
            if key in d and d[key] is not None:
                if isinstance(d[key], datetime):
                    d[key] = d[key].isoformat()

        return d

    @staticmethod
    def _dashboard_row_to_dict(row) -> dict:
        """대시보드 DB row를 딕셔너리로 변환"""
        if isinstance(row, dict):
            d = dict(row)
        else:
            d = dict(row._asdict()) if hasattr(row, '_asdict') else dict(row)

        for key in ("created_at", "updated_at"):
            if key in d and d[key] is not None:
                if isinstance(d[key], datetime):
                    d[key] = d[key].isoformat()

        # widget_count가 없으면 0으로 설정
        if "widget_count" not in d:
            d["widget_count"] = 0

        return d

    @staticmethod
    def _shared_dashboard_row_to_dict(row) -> dict:
        """공유 대시보드 DB row를 딕셔너리로 변환 (소유자 정보 포함)"""
        return PersonalDashboardService._dashboard_row_to_dict(row)


# 싱글톤 인스턴스
personal_dashboard_service = PersonalDashboardService()

"""개인 대시보드 위젯 서비스

위치: app/api/services/personal_dashboard_service.py
- 개인 대시보드 위젯 CRUD + SQL 실행 + PII 마스킹
- user_id 기반 소유권 검증 (개인 데이터 격리)
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
    """개인 대시보드 위젯 CRUD + SQL 실행 서비스"""

    MAX_WIDGETS_PER_USER = 20
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
    # 위젯 CRUD
    # ============================================

    def list_widgets(self, user_id: int) -> dict:
        """사용자 위젯 목록 조회"""
        db_manager = _get_db_manager()
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT * FROM tb_dashboard_widget
                WHERE user_id = %s AND is_active = true
                ORDER BY sort_order, widget_id
            """, (user_id,))
            rows = cur.fetchall()
            items = [self._row_to_dict(row) for row in rows]
            return {"items": items, "total": len(items)}

    def create_widget(self, user_id: int, tenant_id: Optional[int], data) -> dict:
        """위젯 생성"""
        db_manager = _get_db_manager()

        # 위젯 수 제한 확인
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT COUNT(*) as cnt FROM tb_dashboard_widget WHERE user_id = %s AND is_active = true", (user_id,))
            count = cur.fetchone()["cnt"]
            if count >= self.MAX_WIDGETS_PER_USER:
                raise ValueError(f"사용자당 최대 {self.MAX_WIDGETS_PER_USER}개 위젯만 생성할 수 있습니다 (현재: {count}개)")

        # cached_data 행 수 제한
        cached_data = {}
        if data.cached_data:
            cached_data = data.cached_data.model_dump()
            if len(cached_data.get("rows", [])) > self.MAX_CACHED_ROWS:
                cached_data["rows"] = cached_data["rows"][:self.MAX_CACHED_ROWS]
                cached_data["row_count"] = min(cached_data.get("row_count", 0), len(cached_data["rows"]))
            cached_data["cached_at"] = datetime.now().isoformat()

        chart_config = data.chart_config.model_dump() if data.chart_config else {}
        grid_position = data.grid_position.model_dump() if data.grid_position else self._auto_grid_position(user_id, data.widget_type)

        # sort_order 계산 (마지막 위치)
        with db_manager.get_cursor() as cur:
            cur.execute("SELECT COALESCE(MAX(sort_order), -1) + 1 as next_sort FROM tb_dashboard_widget WHERE user_id = %s AND is_active = true", (user_id,))
            next_sort = cur.fetchone()["next_sort"]

        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("""
                INSERT INTO tb_dashboard_widget
                    (user_id, tenant_id, title, widget_type, query, sql, chart_config, cached_data, grid_position, sort_order)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING widget_id
            """, (
                user_id, tenant_id, data.title, data.widget_type,
                data.query, data.sql,
                Json(chart_config), Json(cached_data), Json(grid_position),
                next_sort
            ))
            widget_id = cur.fetchone()["widget_id"]

        logger.info(f"[DASHBOARD] 위젯 생성: widget_id={widget_id}, user_id={user_id}, type={data.widget_type}, title='{data.title}'")
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

    def save_layout(self, user_id: int, layout: list) -> dict:
        """레이아웃 일괄 저장"""
        db_manager = _get_db_manager()

        # 소유권 검증: 모든 widget_id가 해당 사용자 소유인지
        widget_ids = [item.widget_id for item in layout]
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT widget_id FROM tb_dashboard_widget
                WHERE user_id = %s AND widget_id = ANY(%s) AND is_active = true
            """, (user_id, widget_ids))
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

        logger.info(f"[DASHBOARD] 레이아웃 저장: user_id={user_id}, updated_count={updated}")
        return {"message": "레이아웃이 저장되었습니다", "updated_count": updated}

    # ============================================
    # SQL 실행
    # ============================================

    def refresh_widget(self, user_id: int, widget_id: int) -> dict:
        """위젯 데이터 새로고침 (저장된 SQL 재실행)"""
        widget = self._get_widget(user_id, widget_id)
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

        db_manager = _get_db_manager()
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

    def _auto_grid_position(self, user_id: int, widget_type: str) -> dict:
        """기존 위젯 배치를 분석하여 빈 위치에 자동 배치"""
        defaults = self.DEFAULT_GRID_SIZES.get(widget_type, {"w": 6, "h": 10})
        w, h = defaults["w"], defaults["h"]

        db_manager = _get_db_manager()
        with db_manager.get_cursor() as cur:
            cur.execute("""
                SELECT grid_position FROM tb_dashboard_widget
                WHERE user_id = %s AND is_active = true
            """, (user_id,))
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
            # psycopg3 Row 객체
            d = dict(row._asdict()) if hasattr(row, '_asdict') else dict(row)

        # timestamp → isoformat 문자열 변환
        for key in ("created_at", "updated_at", "last_refreshed_at"):
            if key in d and d[key] is not None:
                if isinstance(d[key], datetime):
                    d[key] = d[key].isoformat()

        return d


# 싱글톤 인스턴스
personal_dashboard_service = PersonalDashboardService()

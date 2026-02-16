"""대시보드 통합 데이터 서비스

위치: app/api/services/dashboard_service.py
- 대시보드 KPI, 차트, 최근 활동, 시스템 현황을 단일 호출로 제공
- NL2SQL + RAG 검색 대상 (Agent 제외)
"""
from datetime import datetime, timedelta, time
from typing import Any, Dict, List, Optional

from app.core.database.connection import db_manager
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)

# 대시보드 대상 request_type (psycopg3: ANY(%s)에는 list 사용)
TARGET_TYPES = ['nl2sql', 'rag']


class DashboardService:
    """대시보드 통합 데이터 서비스"""

    def get_summary(
        self,
        period: str = "today",
        tenant_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """대시보드 전체 데이터를 단일 호출로 반환

        Args:
            period: 기간 필터 (today|week|month)
            tenant_id: 테넌트 ID 필터
            user_id: 사용자 ID 필터

        Returns:
            KPI, 일별 추이, 최근 요청, 시스템 현황
        """
        from_date, to_date = self._calc_date_range(period)

        try:
            with db_manager.get_cursor() as cur:
                kpi = self._get_kpi(cur, from_date, to_date, tenant_id, user_id)
                daily_trend = self._get_daily_trend(cur, from_date, to_date, tenant_id, user_id)
                recent = self._get_recent_requests(cur, tenant_id, user_id, limit=7)
                system = self._get_system_info(cur, tenant_id)

            log_step(logger, "system", "DASHBOARD", "SUMMARY", "OK", f"period={period}, total={kpi.get('total_requests', 0)}")
            return {
                "period": period,
                "kpi": kpi,
                "daily_trend": daily_trend,
                "recent_requests": recent,
                "system": system,
            }
        except Exception as e:
            logger.error(f"[DASHBOARD] Summary failed: {e}")
            return {
                "period": period,
                "kpi": self._empty_kpi(),
                "daily_trend": [],
                "recent_requests": [],
                "system": self._empty_system(),
            }

    # =========================================================================
    # 기간 계산
    # =========================================================================

    def _calc_date_range(self, period: str):
        """기간 문자열 → (from_date, to_date) 변환"""
        now = datetime.now()
        if period == "week":
            from_date = datetime.combine(now.date() - timedelta(days=6), time.min)
        elif period == "month":
            from_date = datetime.combine(now.date() - timedelta(days=29), time.min)
        else:  # today (default)
            from_date = datetime.combine(now.date(), time.min)
        return from_date, now

    # =========================================================================
    # KPI
    # =========================================================================

    def _get_kpi(self, cur, from_date, to_date, tenant_id, user_id) -> Dict[str, Any]:
        conditions = ["request_type = ANY(%s)", "created_at >= %s", "created_at <= %s"]
        params: list = [TARGET_TYPES, from_date, to_date]
        self._add_scope_filter(conditions, params, tenant_id, user_id)

        where = " AND ".join(conditions)
        cur.execute(f"""
            SELECT
                COUNT(*) as total_requests,
                COUNT(CASE WHEN success THEN 1 END) as success_count,
                COUNT(CASE WHEN NOT success THEN 1 END) as error_count,
                COUNT(CASE WHEN request_type = 'nl2sql' THEN 1 END) as nl2sql_count,
                COUNT(CASE WHEN request_type = 'rag' THEN 1 END) as rag_count
            FROM tb_api_history
            WHERE {where}
        """, params)
        row = cur.fetchone()
        if not row:
            return self._empty_kpi()

        result = dict(row)
        total = result.get("total_requests", 0)
        success = result.get("success_count", 0)
        result["success_rate"] = round((success / total * 100), 1) if total > 0 else 0.0
        return result

    # =========================================================================
    # 일별 추이
    # =========================================================================

    def _get_daily_trend(self, cur, from_date, to_date, tenant_id, user_id) -> List[Dict]:
        conditions = ["request_type = ANY(%s)", "created_at >= %s", "created_at <= %s"]
        params: list = [TARGET_TYPES, from_date, to_date]
        self._add_scope_filter(conditions, params, tenant_id, user_id)

        where = " AND ".join(conditions)
        cur.execute(f"""
            SELECT
                DATE(created_at) as date,
                COUNT(CASE WHEN request_type = 'nl2sql' THEN 1 END) as nl2sql,
                COUNT(CASE WHEN request_type = 'rag' THEN 1 END) as rag,
                COUNT(*) as total
            FROM tb_api_history
            WHERE {where}
            GROUP BY DATE(created_at)
            ORDER BY date
        """, params)
        rows = cur.fetchall()
        return [{"date": str(r["date"]), "nl2sql": r["nl2sql"], "rag": r["rag"], "total": r["total"]} for r in rows]

    # =========================================================================
    # 최근 요청
    # =========================================================================

    def _get_recent_requests(self, cur, tenant_id, user_id, limit=10) -> List[Dict]:
        conditions = ["request_type = ANY(%s)"]
        params: list = [TARGET_TYPES]
        self._add_scope_filter(conditions, params, tenant_id, user_id)

        where = " AND ".join(conditions)
        params.append(limit)
        cur.execute(f"""
            SELECT request_id, request_type, question, success,
                   response_time_ms, created_at
            FROM tb_api_history
            WHERE {where}
            ORDER BY created_at DESC
            LIMIT %s
        """, params)
        rows = cur.fetchall()
        return [
            {
                "request_id": r["request_id"],
                "request_type": r["request_type"],
                "question": r["question"][:50] if r["question"] else "",
                "success": r["success"],
                "response_time_ms": r["response_time_ms"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            }
            for r in rows
        ]

    # =========================================================================
    # 시스템 현황
    # =========================================================================

    def _get_system_info(self, cur, tenant_id) -> Dict[str, Any]:
        # 활성 사용자 수
        if tenant_id:
            cur.execute("SELECT COUNT(*) as cnt FROM tb_user WHERE is_active = true AND tenant_id = %s", (tenant_id,))
        else:
            cur.execute("SELECT COUNT(*) as cnt FROM tb_user WHERE is_active = true")
        active_users = cur.fetchone()["cnt"]

        # 활성 테넌트 수
        cur.execute("SELECT COUNT(*) as cnt FROM tb_tenant WHERE is_active = true")
        active_tenants = cur.fetchone()["cnt"]

        # 문서 현황
        doc_conditions = []
        doc_params = []
        if tenant_id:
            doc_conditions.append("tenant_id = %s")
            doc_params.append(tenant_id)
        doc_where = " WHERE " + " AND ".join(doc_conditions) if doc_conditions else ""
        cur.execute(f"""
            SELECT
                COUNT(*) as total_documents,
                COUNT(CASE WHEN indexed = true THEN 1 END) as indexed_documents,
                COUNT(CASE WHEN indexed = false OR indexed IS NULL THEN 1 END) as pending_documents
            FROM tb_docs
            {doc_where}
        """, doc_params)
        doc_row = cur.fetchone()

        # 평균 응답시간 / 마지막 요청 시간
        cur.execute("""
            SELECT ROUND(AVG(response_time_ms)) as avg_response_ms,
                   MAX(created_at) as last_request_at
            FROM tb_api_history
            WHERE request_type = ANY(%s)
        """, [TARGET_TYPES])
        perf_row = cur.fetchone()

        return {
            "active_users": active_users,
            "active_tenants": active_tenants,
            "total_documents": doc_row["total_documents"],
            "indexed_documents": doc_row["indexed_documents"],
            "pending_documents": doc_row["pending_documents"],
            "avg_response_ms": int(perf_row["avg_response_ms"] or 0),
            "last_request_at": perf_row["last_request_at"].isoformat() if perf_row["last_request_at"] else None,
        }

    # =========================================================================
    # 유틸리티
    # =========================================================================

    @staticmethod
    def _add_scope_filter(conditions: list, params: list, tenant_id, user_id):
        """tenant_id / user_id 조건 추가"""
        if tenant_id:
            conditions.append("tenant_id = %s")
            params.append(tenant_id)
        if user_id:
            conditions.append("user_id = %s")
            params.append(user_id)

    @staticmethod
    def _empty_kpi():
        return {"total_requests": 0, "success_count": 0, "error_count": 0, "nl2sql_count": 0, "rag_count": 0, "success_rate": 0.0}

    @staticmethod
    def _empty_system():
        return {"active_users": 0, "active_tenants": 0, "total_documents": 0, "indexed_documents": 0, "pending_documents": 0, "avg_response_ms": 0, "last_request_at": None}


# 싱글톤 인스턴스
dashboard_service = DashboardService()

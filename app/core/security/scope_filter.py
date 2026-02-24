"""
scope_level 기반 공통 데이터 필터 유틸리티

위치: app/core/security/scope_filter.py
역할의 scope_level에 따라 SQL WHERE 조건을 자동 추가한다.
"""
from typing import List

from app.core.database.connection import db_manager

# scope_level 상수
SCOPE_GLOBAL = 0   # 전체 (필터 없음)
SCOPE_TENANT = 1   # 테넌트 범위 (tenant_id 필터)
SCOPE_DEPT = 2     # 부서 범위 (tenant_id + dept_id 필터, recursive 하위 포함)
SCOPE_USER = 3     # 본인 범위 (tenant_id + user_id 필터)


def get_dept_scope_ids(dept_id: int) -> List[int]:
    """해당 부서 + 모든 하위 부서 ID 반환 (recursive CTE)"""
    with db_manager.get_cursor() as cur:
        cur.execute(
            "WITH RECURSIVE dept_tree AS ("
            "  SELECT dept_id FROM tb_department WHERE dept_id = %s "
            "  UNION ALL "
            "  SELECT d.dept_id FROM tb_department d "
            "  JOIN dept_tree dt ON d.parent_dept_id = dt.dept_id "
            "  WHERE d.is_active = true"
            ") "
            "SELECT dept_id FROM dept_tree",
            (dept_id,),
        )
        return [row["dept_id"] for row in cur.fetchall()]


def apply_scope_filter(
    user,
    conditions: list,
    params: list,
    tenant_col: str = "tenant_id",
    dept_col: str = "dept_id",
    user_col: str = "user_id",
) -> None:
    """scope_level 기반 공통 데이터 필터

    Args:
        user: UserContext (scope_level, tenant_id, dept_id, user_id 보유)
        conditions: WHERE 조건 리스트 (append됨)
        params: SQL 파라미터 리스트 (extend됨)
        tenant_col/dept_col/user_col: 대상 테이블의 컬럼명
    """
    if user.is_superuser:
        return

    if user.scope_level >= SCOPE_TENANT and user.tenant_id:
        conditions.append(f"{tenant_col} = %s")
        params.append(user.tenant_id)

    if user.scope_level >= SCOPE_DEPT and user.dept_id:
        dept_ids = get_dept_scope_ids(user.dept_id)
        placeholders = ",".join(["%s"] * len(dept_ids))
        conditions.append(f"{dept_col} IN ({placeholders})")
        params.extend(dept_ids)

    if user.scope_level >= SCOPE_USER:
        conditions.append(f"{user_col} = %s")
        params.append(user.user_id)

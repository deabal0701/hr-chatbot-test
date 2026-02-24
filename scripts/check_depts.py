"""기존 테넌트/부서 데이터 확인"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database.connection import db_manager

with db_manager.get_cursor() as cur:
    cur.execute("SELECT tenant_id, tenant_code, tenant_name, is_system FROM tb_tenant ORDER BY tenant_id")
    print("=== Tenants ===")
    for r in cur.fetchall():
        print(dict(r))

    cur.execute("SELECT dept_id, tenant_id, dept_code, dept_name, parent_dept_id, depth, sort_order, is_active FROM tb_department ORDER BY tenant_id, depth, sort_order, dept_id")
    print("\n=== Departments ===")
    for r in cur.fetchall():
        print(dict(r))

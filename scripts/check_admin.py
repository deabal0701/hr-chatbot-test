"""admin 계정 확인 스크립트"""
import sys
sys.path.insert(0, ".")

from app.core.database.connection import db_manager
from app.core.security.password import verify_password

db_manager.initialize()

with db_manager.get_cursor() as cur:
    cur.execute(
        "SELECT user_id, login_id, password_hash, is_active, is_superuser, "
        "login_fail_count, locked_until, role_id "
        "FROM tb_user WHERE login_id = 'admin'"
    )
    row = cur.fetchone()

if not row:
    print("admin 계정이 존재하지 않습니다!")
    db_manager.close()
    sys.exit(1)

d = dict(row)
print("=== admin 계정 정보 ===")
for k, v in d.items():
    if k == "password_hash":
        print(f"  {k}: {v[:40]}...")
    else:
        print(f"  {k}: {v}")

# 비밀번호 검증 테스트
pwd_ok = verify_password("admin123!", d["password_hash"])
print(f"\n=== 비밀번호 검증 ===")
print(f"  admin123! 검증 결과: {pwd_ok}")

# role 확인
if d["role_id"]:
    with db_manager.get_cursor() as cur:
        cur.execute("SELECT role_id, role_code, role_name FROM tb_role WHERE role_id = %s", (d["role_id"],))
        role = cur.fetchone()
    if role:
        print(f"\n=== 역할 정보 ===")
        print(f"  role_id: {role['role_id']}, role_code: {role['role_code']}, role_name: {role['role_name']}")
    else:
        print(f"\n  role_id={d['role_id']}에 해당하는 역할이 없습니다!")

db_manager.close()

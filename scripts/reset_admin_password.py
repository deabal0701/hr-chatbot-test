"""admin 비밀번호 재설정 스크립트"""
import sys
sys.path.insert(0, ".")

from app.core.database.connection import db_manager
from app.core.security.password import hash_password, verify_password

db_manager.initialize()

new_password = "admin123!"
new_hash = hash_password(new_password)

with db_manager.get_cursor(commit=True) as cur:
    cur.execute(
        "UPDATE tb_user SET password_hash = %s, login_fail_count = 0, locked_until = NULL WHERE login_id = 'admin'",
        (new_hash,),
    )
    print(f"업데이트 행 수: {cur.rowcount}")

# 검증
with db_manager.get_cursor() as cur:
    cur.execute("SELECT password_hash FROM tb_user WHERE login_id = 'admin'")
    row = cur.fetchone()

ok = verify_password(new_password, row["password_hash"])
print(f"비밀번호 검증: {ok}")

db_manager.close()
print("admin 비밀번호가 'admin123!'로 재설정되었습니다.")

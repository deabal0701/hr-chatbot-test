"""코드 수정 API 직접 테스트"""
import httpx

BASE = "http://localhost:19090"

# 로그인
resp = httpx.post(f"{BASE}/api/v1/auth/login", json={"login_id": "admin", "password": "admin123!"})
print(f"LOGIN: {resp.status_code} - {resp.json()}")
token = resp.json()["data"]["access_token"]
headers = {"Authorization": f"Bearer {token}"}

# 코드 생성
resp = httpx.post(f"{BASE}/api/admin/v1/codes", headers=headers, json={
    "code_group": "TEST_UPDATE", "code_value": "UPD_01", "code_name": "Before", "sort_order": 1,
})
print(f"CREATE: {resp.status_code} - {resp.json()['data']}")
code_id = resp.json()["data"]["code_id"]

# 코드 수정
resp = httpx.put(f"{BASE}/api/admin/v1/codes/{code_id}", headers=headers, json={
    "code_name": "After Update",
})
print(f"UPDATE: {resp.status_code} - {resp.json()['data']}")

# 정리
resp = httpx.delete(f"{BASE}/api/admin/v1/codes/{code_id}", headers=headers)
print(f"DELETE: {resp.status_code}")

# API 레퍼런스

> 최종 수정: 2026-03-10

---

## 1. 응답 형식

모든 API는 통일된 응답 형식을 사용한다.

**성공**:
```json
{ "success": true, "data": { ... }, "error": null }
```

**실패**:
```json
{ "success": false, "data": null, "error": { "code": "ERROR_CODE", "message": "...", "detail": "..." } }
```

**응답 유형별 HTTP Status**:

| 작업 | HTTP Status | data 구조 |
|------|-------------|-----------|
| CREATE | 201 | 생성된 객체 |
| GET (단건) | 200 | 객체 |
| GET (목록) | 200 | `{"items": [...], "total": N}` |
| UPDATE | 200 | 수정된 객체 |
| DELETE | 200 | `{"message": "...", "deleted_count": N}` |

---

## 2. 인증 (`/api/v1/auth`)

| Method | Endpoint | 설명 | 인증 | Content-Type |
|--------|----------|------|:---:|-------------|
| POST | /login | 로그인 → 토큰 + 메뉴 목록 | - | JSON |
| POST | /sso | SSO 토큰 교환 → JSON 응답 (API/스크립트용) | - | JSON |
| POST | /sso-redirect | SSO Hidden Form → Cookie Base64URL → 302 (브라우저용) | - | Form |
| POST | /logout | 로그아웃 (세션 삭제) | O | JSON |
| POST | /refresh | Access Token 갱신 | - | JSON |
| GET | /me | 현재 사용자 정보 + 메뉴 | O | - |
| PUT | /me/password | 비밀번호 변경 | O | JSON |

> **SSO 상세**: `11_department_sso_design.md` 섹션 6.7 참조
> - `/sso`: `{"sso_token": "eyJ..."}` → `{access_token, refresh_token, ...}` JSON 응답
> - `/sso-redirect`: `token=eyJ...` (Form) → `Set-Cookie: sso_auth` + `302 → /sso` 리다이렉트

---

## 3. AI 검색 (`/api/v1`)

### 3.1 통합 검색

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|:---:|
| POST | /search | 검색 (mode: auto/rag/nl2sql) | O |
| POST | /search/stream | SSE 스트리밍 검색 | O |
| GET | /nl2sql/sessions | NL2SQL 세션 목록 | O |
| GET | /nl2sql/sessions/{key} | 세션 대화 이력 | O |
| DELETE | /nl2sql/sessions/{key} | 세션 삭제 | O |

### 3.2 Agent 검색

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|:---:|
| POST | /agent/search | Agent 검색 | O |
| POST | /agent/search/stream | Agent SSE 스트리밍 | O |
| GET | /agent/sessions | 세션 목록 | O |
| GET | /agent/sessions/{id}/memory | 세션 메모리 | O |
| GET | /agent/sessions/{id}/metrics | 세션 메트릭스 | O |
| DELETE | /agent/sessions/{id} | 세션 삭제 | O |
| GET | /agent/tools | 사용 가능한 도구 목록 | O |
| POST | /agent/tools/{name}/test | 도구 테스트 | O |

---

## 4. 문서 관리 (`/api/admin/v1/documents`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | / | 문서 목록 (필터: doc_type, indexed 등) | DOC_MGMT:read |
| POST | / | 문서 저장 | DOC_MGMT:create |
| GET | /{doc_id} | 문서 상세 | DOC_MGMT:read |
| PUT | /{doc_id} | 문서 수정 | DOC_MGMT:update |
| DELETE | /{doc_id} | 문서 삭제 | DOC_MGMT:delete |
| POST | /bulk-delete | 일괄 삭제 | DOC_MGMT:delete |
| POST | /embedding/execute | 임베딩 실행 | DOC_MGMT:create |
| POST | /embedding/preview | 청킹 미리보기 | DOC_MGMT:read |

---

## 5. 사용자 관리 (`/api/admin/v1/users`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | /options/roles | 역할 드롭다운 (상위 역할 필터링) | USER_MGMT:read |
| GET | /options/tenants | 테넌트 드롭다운 (is_system 포함) | USER_MGMT:read |
| GET | /options/menus | 메뉴 체크박스 (assignable 플래그) | USER_MGMT:read |
| GET | / | 사용자 목록 (필터: keyword, is_active, tenant_id) | USER_MGMT:read |
| POST | / | 사용자 생성 + 메뉴 권한 | USER_MGMT:create |
| GET | /{user_id} | 사용자 상세 (본인 항상 가능) | 로그인 |
| PUT | /{user_id} | 사용자 수정 | USER_MGMT:update |
| DELETE | /{user_id} | 사용자 삭제 | USER_MGMT:delete |
| GET | /{user_id}/menus | 메뉴 권한 조회 | USER_MGMT:read |
| PUT | /{user_id}/menus | 메뉴 권한 할당 (replace) | USER_MGMT:update |

---

## 6. 역할 관리 (`/api/admin/v1/roles`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | / | 역할 목록 | ROLE_MGMT:read |
| POST | / | 역할 생성 | ROLE_MGMT:create |
| GET | /default-menus/{role_code} | 역할 기본 메뉴 조회 | ROLE_MGMT:read |
| GET | /{role_id} | 역할 상세 | ROLE_MGMT:read |
| PUT | /{role_id} | 역할 수정 | ROLE_MGMT:update |
| DELETE | /{role_id} | 역할 삭제 (is_system 불가) | ROLE_MGMT:delete |

---

## 7. 테넌트 관리 (`/api/admin/v1/tenants`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | / | 테넌트 목록 | TENANT_MGMT:read |
| POST | / | 테넌트 생성 | TENANT_MGMT:create |
| GET | /{tenant_id} | 테넌트 상세 | TENANT_MGMT:read |
| PUT | /{tenant_id} | 테넌트 수정 | TENANT_MGMT:update |
| DELETE | /{tenant_id} | 테넌트 삭제 (is_system 불가) | TENANT_MGMT:delete |

---

## 8. 부서 관리 (`/api/admin/v1/departments`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | / | 부서 트리 조회 | DEPT_MGMT:read |
| POST | / | 부서 추가 | DEPT_MGMT:create |
| PUT | /reorder | 순서 변경 (드래그앤드롭) | DEPT_MGMT:update |
| GET | /{dept_id} | 부서 상세 | DEPT_MGMT:read |
| PUT | /{dept_id} | 부서 수정 | DEPT_MGMT:update |
| DELETE | /{dept_id} | 부서 삭제 (하위부서/소속사용자 있으면 불가) | DEPT_MGMT:delete |

---

## 9. 메뉴 관리 (`/api/admin/v1/menus`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | / | 메뉴 트리 조회 | MENU_MGMT:read |
| POST | / | 메뉴 생성 | MENU_MGMT:create |
| PUT | /reorder | 순서 변경 (드래그앤드롭) | MENU_MGMT:update |
| GET | /{menu_id} | 메뉴 상세 | MENU_MGMT:read |
| PUT | /{menu_id} | 메뉴 수정 | MENU_MGMT:update |
| DELETE | /{menu_id} | 메뉴 삭제 | MENU_MGMT:delete |

---

## 10. 시스템 설정 (`/api/admin/v1/settings`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | / | 전체 설정 (마스킹) | SYS_SETTING:read |
| GET | /{category} | 카테고리별 설정 | SYS_SETTING:read |
| GET | /{category}/{key} | 단일 설정 | SYS_SETTING:read |
| GET | /{category}/{key}/reveal | 단일 설정 (언마스킹) | SYS_SETTING:read |
| PUT | /{category}/{key} | 단일 설정 수정 | SYS_SETTING:update |
| PUT | /{category} | 카테고리 일괄 수정 | SYS_SETTING:update |
| POST | /{category}/reset | 카테고리 초기화 | SYS_SETTING:update |
| POST | /validate-api-key | API 키 검증 | SYS_SETTING:read |
| POST | /refresh-cache | 캐시 갱신 | SYS_SETTING:update |
| POST | /external-database/test | 외부 DB 연결 테스트 | SYS_SETTING:update |
| GET | /prompt/history | 프롬프트 변경 이력 | SYS_SETTING:read |

---

## 11. 코드 관리

### 관리자 (`/api/admin/v1/codes`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | /groups | 코드 그룹 목록 | CODE_MGMT:read |
| GET | /{code_group} | 그룹별 코드 목록 | CODE_MGMT:read |
| GET | /item/{code_id} | 코드 상세 | CODE_MGMT:read |
| POST | / | 코드 생성 | CODE_MGMT:create |
| PUT | /{code_id} | 코드 수정 | CODE_MGMT:update |
| DELETE | /{code_id} | 코드 삭제 | CODE_MGMT:delete |
| POST | /{code_group}/reorder | 코드 순서 변경 | CODE_MGMT:update |

### 공개 조회 (`/api/v1/codes`)

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|:---:|
| GET | /{code_group} | 코드 조회 (드롭다운용) | - |

---

## 12. 대시보드 (`/api/v1/dashboard`)

### 12.1 관리자 대시보드

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|:---:|
| GET | /summary | KPI 요약 + 차트 + 시스템 현황 | O |

### 12.2 개인 대시보드

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|:---:|
| GET | /dashboards | 대시보드 목록 | O |
| POST | /dashboards | 대시보드 생성 | O |
| PUT | /dashboards/{id} | 대시보드 수정 | O |
| DELETE | /dashboards/{id} | 대시보드 삭제 | O |
| PUT | /dashboards/{id}/default | 기본 대시보드 설정 | O |
| PUT | /dashboards/{id}/share | 대시보드 공유 | O |
| GET | /widgets | 위젯 목록 | O |
| POST | /widgets | 위젯 생성 | O |
| PUT | /widgets/{id} | 위젯 수정 | O |
| DELETE | /widgets/{id} | 위젯 삭제 | O |
| PUT | /layout | 레이아웃 저장 (위젯 배치) | O |
| POST | /widgets/{id}/refresh | 위젯 데이터 갱신 | O |
| POST | /execute-sql | 위젯용 SQL 실행 | O |

---

## 13. 검색 이력 (`/api/v1/history`)

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | / | 이력 목록 (필터링) | SEARCH_HIST:read |
| GET | /statistics | 통계 | SEARCH_HIST:read |
| GET | /sessions | 세션 목록 (사이드바용) | 로그인 |
| GET | /sessions/{key} | 세션 대화 이력 | 로그인 |
| DELETE | /sessions/{key} | 세션 삭제 | 로그인 |
| GET | /{request_id} | 단일 요청 상세 | SEARCH_HIST:read |
| GET | /users/{user_id} | 사용자 요약 | SEARCH_HIST:read |
| GET | /users/{user_id}/history | 사용자 상세 이력 | SEARCH_HIST:read |
| DELETE | /cleanup | 오래된 이력 정리 | SEARCH_HIST:delete |

---

## 14. Excel 내보내기 (`/api/v1/export`)

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|:---:|
| POST | /excel | NL2SQL 결과 Excel 내보내기 | O |

---

## 15. 에러 코드

### 클라이언트 에러 (4xx)

| 코드 | HTTP | 설명 |
|------|------|------|
| VALIDATION_ERROR | 400 | 입력값 검증 실패 |
| BAD_REQUEST | 400 | 잘못된 요청 |
| UNAUTHORIZED | 401 | 인증 실패 |
| FORBIDDEN | 403 | 권한 부족 |
| NOT_FOUND | 404 | 리소스 없음 |
| DUPLICATE_ERROR | 409 | 유니크 제약조건 위반 |
| ACCOUNT_LOCKED | 423 | 계정 잠금 (로그인 실패 5회) |
| RATE_LIMIT_EXCEEDED | 429 | 요청 속도 제한 초과 |

### 비즈니스 에러

| 코드 | HTTP | 설명 |
|------|------|------|
| SEARCH_FAILED | 500 | 검색 실패 |
| SQL_GENERATION_FAILED | 500 | SQL 생성 실패 |
| SQL_EXECUTION_FAILED | 500 | SQL 실행 실패 |
| DOCUMENT_NOT_FOUND | 404 | 문서 없음 |
| EMBEDDING_FAILED | 500 | 임베딩 실패 |
| AGENT_FAILED | 500 | Agent 실행 실패 |
| SESSION_NOT_FOUND | 404 | 세션 없음 |
| SESSION_EXPIRED | 410 | 세션 만료 |
| SETTING_NOT_FOUND | 404 | 설정 없음 |
| CODE_NOT_FOUND | 404 | 코드 없음 |

### SSO 에러

| 코드 | HTTP | 설명 |
|------|------|------|
| SSO_NOT_CONFIGURED | 500 | SSO 미설정 |
| SSO_DISABLED | 403 | SSO 비활성 |
| SSO_INVALID_TOKEN | 401 | SSO 토큰 유효하지 않음 |
| SSO_TOKEN_EXPIRED | 401 | SSO 토큰 만료 |
| SSO_USER_NOT_FOUND | 404 | SSO 사용자 미등록 |

### 서버 에러 (5xx)

| 코드 | HTTP | 설명 |
|------|------|------|
| INTERNAL_ERROR | 500 | 내부 오류 |
| DATABASE_ERROR | 500 | 데이터베이스 오류 |
| LLM_ERROR | 502 | LLM API 오류 |
| EXTERNAL_API_ERROR | 502 | 외부 API 오류 |
| TIMEOUT_ERROR | 504 | 타임아웃 |

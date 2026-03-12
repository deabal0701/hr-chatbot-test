# 인증/인가 시스템 설계

> 최종 수정: 2026-03-10

---

## 1. 설계 원칙

```
tb_user_menu = "어떤 메뉴에 무엇을 할 수 있는가"  (기능 접근)
tb_role.role_code + scope_level = "어디까지 볼 수 있는가"  (데이터 범위)

같은 메뉴 권한이라도 scope_level에 따라 보이는 데이터가 다름
예: 사용자 관리 Read + scope_level=1 → 자기 테넌트 사용자만
    사용자 관리 Read + scope_level=0 → 전체 사용자
```

---

## 2. 역할 계층

| 구분 | GLOBAL (시스템관리자) | TENANT (테넌트관리자) | DEPT (부서관리자) | USER (일반사용자) |
|------|:---:|:---:|:---:|:---:|
| sort_order | 1 (최상위) | 2 | 3 | 4 |
| scope_level | 0 (전체) | 1 (테넌트) | 2 (부서) | 3 (본인) |
| landing_page | /admin/dashboard | /admin/dashboard | /admin/dashboard | /chat |
| is_superuser | true | false | false | false |
| 소속 테넌트 | 시스템 테넌트 | 소속 테넌트 | 소속 테넌트 | 소속 테넌트 |
| 데이터 범위 | **전체** | **테넌트 내** | **부서 내** | **본인만** |

> `sort_order`가 역할 계층 결정 — 낮을수록 상위. DB에서 동적 조회하므로 하드코딩 없음.

### 2.1 데이터 범위 필터링 (scope_level)

| scope_level | 범위 | 필터 조건 |
|-------------|------|----------|
| 0 | 전체 | 필터 없음 |
| 1 | 테넌트 | `WHERE tenant_id = current_user.tenant_id` |
| 2 | 부서 | `WHERE dept_id = current_user.dept_id` |
| 3 | 본인 | `WHERE user_id = current_user.user_id` |

- **파일**: `app/core/security/scope_filter.py`

---

## 3. JWT 인증

### 3.1 토큰 흐름

```
POST /api/v1/auth/login
  → 비밀번호 검증 (bcrypt)
  → Access Token 발급 (30분) — user_id, role_code, scope_level, tenant_id, dept_id 포함
  → Refresh Token 발급 (7일) — session_id 포함, DB(tb_user_session) 저장

API 요청 → Authorization: Bearer <token>
  → AuthMiddleware → JWT 검증 → request.state.current_user (UserContext)
```

### 3.2 토큰 페이로드 (TokenPayload)

| 필드 | 타입 | 설명 |
|------|------|------|
| sub | str | User ID |
| login_id | str | 로그인 ID |
| display_name | str | 표시명 |
| tenant_id | int? | 테넌트 ID |
| dept_id | int? | 부서 ID |
| role_code | str | GLOBAL/TENANT/DEPT/USER |
| scope_level | int | 0=전체, 1=테넌트, 2=부서, 3=본인 |
| is_superuser | bool | 슈퍼유저 여부 |
| exp | int | 만료 시간 |
| iat | int | 발급 시간 |
| token_type | str | "access" 또는 "refresh" |
| session_id | str? | 세션 ID (refresh 전용) |

### 3.3 알고리즘 보안

- **화이트리스트**: `HS256`, `HS384`, `HS512`만 허용 (하드코딩)
- 허용되지 않은 알고리즘 → `RuntimeError` (알고리즘 혼동 공격 방지)

### 3.4 토큰 갱신

```
Access Token 만료 → 401 응답
  → 프론트엔드 인터셉터 → POST /api/v1/auth/refresh (refresh_token)
  → DB 세션 검증 (session_id + refresh_token 매칭)
  → 최신 권한 재로드 (get_user_with_permissions)
  → 새 Access Token 발급 (기존 Refresh Token 재사용)
  → 원래 요청 재시도
  → 동시 요청 큐잉으로 중복 갱신 방지
```

### 3.5 인증 API

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|:---:|
| POST | /api/v1/auth/login | 로그인 (메뉴 목록 포함) | No |
| POST | /api/v1/auth/sso | SSO 토큰 교환 → JSON 응답 (API용) | No |
| POST | /api/v1/auth/sso-redirect | SSO Hidden Form → 쿠키 → 302 (브라우저용) | No |
| POST | /api/v1/auth/logout | 로그아웃 (세션 삭제) | Yes |
| POST | /api/v1/auth/refresh | 토큰 갱신 | No |
| GET | /api/v1/auth/me | 현재 사용자 정보 (최신 권한) | Yes |
| PUT | /api/v1/auth/me/password | 비밀번호 변경 | Yes |

### 3.6 비밀번호 정책

- 최소 8자
- 대문자 + 소문자 + 숫자 필수 (Pydantic validator)
- bcrypt 해싱 (cost factor 12)
- 로그인 실패 5회 → 30분 계정 잠금

### 3.7 계정 잠금 메커니즘

```
로그인 실패 시:
  1. login_fail_count 증가
  2. login_fail_count >= 5 → locked_until = now + 30분
  3. 잠금 상태에서 로그인 시도 → ACCOUNT_LOCKED (남은 시간 표시)
  4. 잠금 시간 경과 → 자동 해제 (locked_until=NULL, fail_count=0)
  5. 로그인 성공 → fail_count 리셋, last_login_at 갱신
```

---

## 4. 메뉴 기반 권한 체크

### 4.1 체크 메커니즘

```python
# 라우트에서 사용
@router.post("")
async def create_user(
    current_user = Depends(require_menu_permission("USER_MGMT", "create"))
):
```

`require_menu_permission(menu_code, action)`:
1. JWT에서 UserContext 추출
2. `is_superuser=true`이면 통과 (비상 우회, DB 조회 없음)
3. `tb_user_menu JOIN tb_menu`에서 `can_{action}` 확인
4. 권한 없으면 403 FORBIDDEN ("{action_label} 권한이 없습니다")

### 4.2 HTTP → CRUD 매핑

| HTTP | action | 필드 | 한글 레이블 |
|------|--------|------|------------|
| POST | create | can_create | 등록 |
| GET | read | can_read | 조회 |
| PUT | update | can_update | 수정 |
| DELETE | delete | can_delete | 삭제 |
| GET /export | export | can_export | 내보내기 |

### 4.3 역할별 기본 메뉴

| 메뉴 | GLOBAL | TENANT | DEPT | USER |
|------|:---:|:---:|:---:|:---:|
| 대시보드 | CRUDE | R | R | - |
| AI 채팅 | CR | CR | CR | - |
| 문서 관리 | CRUDE | CRUDE | R | - |
| 사용자 관리 | CRUDE | CRU | R | - |
| 메뉴 관리 | CRUDE | - | - | - |
| 역할 관리 | CRUDE | - | - | - |
| 테넌트 관리 | CRUDE | - | - | - |
| 부서 관리 | CRUDE | CRU | R | - |
| 시스템 설정 | RU | - | - | - |
| 코드 관리 | CRUD | - | - | - |
| 검색 이력 | RE | RE | R | - |
| 채팅 (/chat) | CR | CR | CR | CR |
| API (Agent/RAG/NL2SQL) | CR | CR | CR | CR |

> C=Create, R=Read, U=Update, D=Delete, E=Export

---

## 5. 보안 보호 메커니즘

### 5.1 시스템 리소스 보호

| 대상 | 보호 필드 | 보호 내용 |
|------|----------|----------|
| GLOBAL 테넌트 | `tb_tenant.is_system` | 삭제/비활성화 불가 |
| 기본 역할 | `tb_role.is_system` | 삭제 불가 |
| 슈퍼유저 | `tb_user.is_superuser` | 타인이 수정/삭제 불가 |

### 5.2 역할 권한 상승 방지

```
sort_order 기준: 낮을수록 상위 (GLOBAL=1 > TENANT=2 > DEPT=3 > USER=4)

규칙: 자신보다 상위 역할은 할당 불가
  TENANT 관리자 → sort_order >= 자신의 역할만 할당 가능
  GLOBAL 관리자 → 모든 역할 할당 가능
```

**적용 위치**: `get_role_options()`, `create_user()`, `update_user()`

### 5.3 역할-테넌트 조합 검증

```
GLOBAL 역할  → 시스템 테넌트(is_system=true) 자동 설정, 일반 테넌트 불가
TENANT 역할  → tenant_id 필수, 시스템 테넌트 불가
DEPT 역할    → tenant_id + dept_id 필수, 시스템 테넌트 불가
USER 역할    → tenant_id 필수, 시스템 테넌트 불가

금지 조합:
  × GLOBAL + 일반 테넌트 → 시스템 테넌트로 자동 보정
  × TENANT + 시스템 테넌트 → BAD_REQUEST 에러
  × USER + 테넌트 미선택 → BAD_REQUEST 에러
```

**적용 위치**:
- **백엔드**: `_validate_role_tenant()` — create_user, update_user
- **프론트엔드**: `handleRoleChange()` — GLOBAL 선택 시 자동 설정 & 비활성화

### 5.4 메뉴 권한 상승 방지

```
규칙: 자신이 보유하지 않은 메뉴는 할당 불가
  TENANT 관리자 → 본인의 tb_user_menu에 있는 메뉴만 할당 가능
  GLOBAL 관리자 → 모든 메뉴 할당 가능
```

**적용 위치**: `get_menu_options()` (assignable 플래그), `assign_menus()` (백엔드 검증)

### 5.5 사용자 삭제 보호

- 슈퍼유저 삭제 불가
- 자기 자신 삭제 불가
- 테넌트 범위 검증 (`_check_scope_access`)

---

## 6. Rate Limiting

### 6.1 개요

사용자/IP 기반 슬라이딩 윈도우 속도 제한 (인메모리).

- **파일**: `app/middleware/rate_limit.py`
- **실행 위치**: Auth 미들웨어 이후 (user_id 사용 가능)

### 6.2 설정

| 그룹 | 엔드포인트 | 기본 RPM |
|------|----------|---------|
| auth | /auth/login, /auth/refresh | 5 |
| ai | /agent/search, /search | 20 |
| admin | /api/admin/v1/* | 60 |
| default | 기타 모든 엔드포인트 | 120 |

### 6.3 클라이언트 식별

```
인증됨: "user:{user_id}:{group}"
미인증: "ip:{client_ip}:{group}"
```

### 6.4 초과 응답

- **Status**: 429 Too Many Requests
- **Headers**: `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
- **정리**: 5분마다 만료된 키 자동 정리

---

## 7. SSO 인증

### 7.1 개요

외부 IdP(HR 시스템 등)에서 RS256 개인키로 서명한 JWT 토큰으로 MUREUM에 로그인하는 SSO 연동.
**Hidden Form POST + Cookie Base64URL** 방식으로 토큰을 안전하게 전달한다.
미등록 사용자는 **JIT(Just-In-Time) 자동 생성** 후 로그인된다 (USER 역할 고정).

- **검증 모듈**: `app/core/security/sso.py`
- **라우트**: `app/api/routes/auth.py` (POST /sso, POST /sso-redirect)
- **서비스**: `app/api/services/auth_service.py` (sso_authenticate, find_or_create_sso_user)
- **프론트엔드**: `frontend/src/views/SSOCallbackView.vue`
- **설정**: `sso_enabled=False` (기본 비활성)
- **상세 설계**: `11_department_sso_design.md` §6 참조

### 7.2 SSO 인증 흐름

**경로 1: Hidden Form POST (브라우저 — 메인 방식)**
```
[외부 시스템] Hidden Form POST → POST /api/v1/auth/sso-redirect (body: token=eyJ...)
  → RS256 공개키로 서명 검증
  → 필수 클레임 확인 (sub, name, iss, exp)
  → 발급자 화이트리스트 확인 (sso_allowed_issuers)
  → 토큰 최대 수명 확인 (sso_token_max_age: 300초)
  → 사용자 검색 (sso_external_id 또는 login_id)
  ├─ 사용자 존재 → 변경 감지 (display_name, email) → 로그인
  └─ 사용자 미존재 + sso_auto_create_user=true
       → email, tenant_code 필수 확인
       → USER 역할로 사용자 자동 생성
       → USER 기본 메뉴 권한 할당 (AI_CHAT: CR)
       → 로그인
  → MUREUM JWT 발급 (HS256)
  → Set-Cookie: sso_auth = Base64URL({at, rt}) (60초 TTL)
  → 302 Redirect → /sso
  → SSOCallbackView: 쿠키 읽기 → /me API → Vuex 저장 → landing_page
```

**경로 2: JSON API (스크립트/테스트용)**
```
POST /api/v1/auth/sso (body: {"sso_token": "eyJ..."})
  → 동일한 검증 + JIT 자동 생성 로직
  → JSON 응답: {access_token, refresh_token, token_type, expires_in}
```

### 7.3 SSO 토큰 페이로드

| 필드 | 설명 | 필수 | 비고 |
|------|------|:---:|------|
| sub | 사용자 식별자 (login_id 매핑) | **O** | |
| name | 이름 (display_name) | **O** | |
| iss | 발급자 | **O** | sso_allowed_issuers 검증 |
| exp | 만료 시간 | **O** | 5분 이내 권장 |
| email | 이메일 | **O** | JIT 자동 생성 시 필수 |
| tenant_code | 테넌트 코드 | **O** | JIT 자동 생성 시 필수 |
| dept_code | 부서 코드 | △ | 부서 매핑 (없으면 NULL) |
| dept_name | 부서명 | △ | 부서 자동 생성 시 사용 |

> 기존 사용자 로그인은 sub, name, iss, exp만 있으면 됨. email/tenant_code는 JIT 생성 시 필수.

### 7.4 SSO 설정

| 설정 | 기본값 | 설명 |
|------|--------|------|
| sso_enabled | false | SSO 활성화 여부 |
| sso_public_key_path | keys/sso_public.pem | RS256 공개키 경로 |
| sso_algorithm | RS256 | 토큰 알고리즘 |
| sso_allowed_issuers | hr-system | 허용 발급자 (쉼표 구분) |
| sso_token_max_age | 300 | 토큰 최대 수명 (초) |
| sso_default_role | USER | SSO 자동 생성 사용자 역할 (USER 고정 권장) |
| sso_auto_create_user | true | 미등록 사용자 JIT 자동 생성 |
| sso_frontend_url | (빈 값) | SSO 리다이렉트 URL (빈 값이면 상대경로 /sso) |

### 7.5 SSO 에러 코드

| 코드 | HTTP | 설명 |
|------|:---:|------|
| SSO_NOT_CONFIGURED | 500 | 공개키 미설정 |
| SSO_DISABLED | 403 | SSO 비활성 |
| SSO_INVALID_TOKEN | 401 | 서명 불일치, 형식 오류, 필수 클레임 누락, 미허용 발급자, 자동등록 필수정보 누락 |
| SSO_TOKEN_EXPIRED | 401 | 토큰 만료 또는 최대 유효시간 초과 |
| SSO_USER_NOT_FOUND | 404 | 미등록 사용자 (sso_auto_create_user=false일 때) |

### 7.6 SSO 자동 생성 정책

| 항목 | 정책 |
|------|------|
| 역할 | **USER 고정** (sso_default_role) |
| 메뉴 권한 | USER 기본 메뉴 (AI_CHAT: can_create, can_read) |
| 비밀번호 | 랜덤 생성 (SSO 전용 — 직접 로그인 불가) |
| 관리자 등록 | **시스템에서만 직접 등록** (SSO로 관리자 자동 부여 안함) |
| 변경 감지 | display_name, email만 (역할/부서는 Admin UI에서 변경) |

---

## 8. 프론트엔드 연동

### 8.1 인증 상태 (Vuex auth 모듈)

```
localStorage: mureum_access_token, mureum_refresh_token, mureum_user
```

| Getter | 용도 |
|--------|------|
| `isAuthenticated` | 토큰 + 사용자 존재 여부 |
| `hasMenuPermission(menuCode, action)` | 메뉴별 CRUD 권한 확인 |
| `canAccessAdmin` | 관리자 메뉴 1개 이상 보유 여부 |
| `accessibleMenus` | 사이드바에 표시할 메뉴 목록 |

### 8.2 라우터 가드

```
router.beforeEach:
  1. 토큰 없으면 → /login 리디렉트
  2. canAccessAdmin 체크 → 관리자 접근 가능 여부
  3. 개별 라우트의 menuCode → hasMenuPermission(menuCode, 'read')
  4. 권한 없으면 → landing_page로 리디렉트
```

### 8.3 사이드바 동적 메뉴

로그인 응답의 `menus[]`로 사이드바를 동적 생성 (하드코딩 없음):
- `menu_type === 'PAGE'` 필터
- `can_read === true` 필터
- `sort_order` 정렬

---

## 9. UserContext 모델

```python
class UserContext(BaseModel):
    user_id: int
    login_id: str
    display_name: Optional[str]
    tenant_id: Optional[int]
    dept_id: Optional[int]
    is_superuser: bool = False
    role_code: str              # "GLOBAL", "TENANT", "DEPT", "USER"
    scope_level: int            # 0=전체, 1=테넌트, 2=부서, 3=본인

    # Helper properties
    is_global → is_superuser or scope_level == 0
    is_tenant_scope → scope_level == 1
    is_dept_scope → scope_level == 2
    is_user_scope → scope_level == 3
```

---

## 10. 파일 구조

| 파일 | 역할 |
|------|------|
| `app/core/security/jwt.py` | JWT 생성/검증 (HS256/384/512 화이트리스트) |
| `app/core/security/password.py` | bcrypt 해싱 (rounds=12) |
| `app/core/security/dependencies.py` | get_current_user, get_current_active_user, get_optional_user |
| `app/core/security/permission.py` | require_menu_permission, require_superuser |
| `app/core/security/scope_filter.py` | 데이터 범위 필터링 (scope_level 기반) |
| `app/core/security/tenant_context.py` | ContextVar 기반 테넌트 격리 |
| `app/core/security/sso.py` | SSO 토큰 검증 (RS256), 공개키 로드 |
| `app/middleware/auth.py` | JWT 인증 미들웨어 (선택적 모드) |
| `app/middleware/rate_limit.py` | 슬라이딩 윈도우 속도 제한 |
| `app/api/routes/auth.py` | 인증 엔드포인트 |
| `app/api/services/auth_service.py` | 인증 비즈니스 로직 |
| `app/models/auth.py` | LoginRequest, TokenResponse, UserContext, MenuPermission, SSO 모델 |
| `frontend/src/store/modules/auth.js` | Vuex 인증 상태 |
| `frontend/src/api/auth.js` | 인증 API 클라이언트 |
| `frontend/src/router/index.js` | 라우터 가드 |

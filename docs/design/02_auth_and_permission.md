# 인증/인가 시스템 설계

> 최종 수정: 2026-02-15

---

## 1. 설계 원칙

```
tb_user_menu = "어떤 메뉴에 무엇을 할 수 있는가"  (기능 접근)
tb_role.role_code = "어디까지 볼 수 있는가"       (데이터 범위)

같은 메뉴 권한이라도 role_code에 따라 보이는 데이터가 다름
예: 사용자 관리 Read + TENANT → 자기 테넌트 사용자만
    사용자 관리 Read + GLOBAL → 전체 사용자
```

---

## 2. 역할 계층

| 구분 | GLOBAL (시스템관리자) | TENANT (테넌트관리자) | USER (일반사용자) |
|------|:---:|:---:|:---:|
| sort_order | 1 (최상위) | 2 | 3 |
| landing_page | /admin/dashboard | /admin/dashboard | /chat |
| is_superuser | true | false | false |
| 소속 테넌트 | 시스템 테넌트 | 소속 테넌트 | 소속 테넌트 |
| 데이터 범위 | **전체** | **테넌트 내** | **본인만** |
| 메뉴 접근 | 전체 | 제한적 | 채팅만 |

> `sort_order`가 역할 계층 결정 — 낮을수록 상위. DB에서 동적 조회하므로 하드코딩 없음.

---

## 3. JWT 인증

### 3.1 토큰 흐름

```
POST /api/v1/auth/login
  → 비밀번호 검증 (bcrypt)
  → Access Token 발급 (30분) — user_id, role_code, tenant_id 포함
  → Refresh Token 발급 (7일) — session_id 포함, DB(tb_user_session) 저장

API 요청 → Authorization: Bearer <token>
  → AuthMiddleware → JWT 검증 → request.state.current_user (UserContext)
```

### 3.2 토큰 갱신

```
Access Token 만료 → 401 응답
  → 프론트엔드 인터셉터 → POST /api/v1/auth/refresh (refresh_token)
  → 새 Access Token 발급 → 원래 요청 재시도
  → 동시 요청 큐잉으로 중복 갱신 방지
```

### 3.3 인증 API

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|:---:|
| POST | /api/v1/auth/login | 로그인 (메뉴 목록 포함) | No |
| POST | /api/v1/auth/logout | 로그아웃 (세션 삭제) | Yes |
| POST | /api/v1/auth/refresh | 토큰 갱신 | No |
| GET | /api/v1/auth/me | 현재 사용자 정보 | Yes |
| PUT | /api/v1/auth/me/password | 비밀번호 변경 | Yes |

### 3.4 비밀번호 정책

- 최소 8자
- bcrypt 해싱 (cost factor 12)
- 로그인 실패 5회 → 30분 계정 잠금

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
2. `is_superuser=true`이면 통과 (비상 우회)
3. `tb_user_menu JOIN tb_menu`에서 `can_{action}` 확인
4. 권한 없으면 403 FORBIDDEN

### 4.2 HTTP → CRUD 매핑

| HTTP | action | 필드 |
|------|--------|------|
| POST | create | can_create |
| GET | read | can_read |
| PUT | update | can_update |
| DELETE | delete | can_delete |
| GET /export | export | can_export |

### 4.3 역할별 기본 메뉴

| 메뉴 | GLOBAL | TENANT | USER |
|------|:---:|:---:|:---:|
| 대시보드 | CRUDE | R | - |
| AI 채팅 | CR | CR | - |
| 문서 관리 | CRUDE | CRUDE | - |
| 사용자 관리 | CRUDE | CRU | - |
| 메뉴 관리 | CRUDE | - | - |
| 역할 관리 | CRUDE | - | - |
| 테넌트 관리 | CRUDE | - | - |
| 시스템 설정 | RU | - | - |
| 코드 관리 | CRUD | - | - |
| 검색 이력 | RE | RE | - |
| 채팅 (/chat) | CR | CR | CR |
| API (Agent/RAG/NL2SQL) | CR | CR | CR |

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
sort_order 기준: 낮을수록 상위 (GLOBAL=1 > TENANT=2 > USER=3)

규칙: 자신보다 상위 역할은 할당 불가
  TENANT 관리자 → sort_order >= 자신의 역할만 할당 가능
  GLOBAL 관리자 → 모든 역할 할당 가능
```

**적용 위치**: `get_role_options()`, `create_user()`, `update_user()`

### 5.3 역할-테넌트 조합 검증

```
GLOBAL 역할  → 시스템 테넌트(is_system=true) 자동 설정, 일반 테넌트 불가
TENANT 역할  → tenant_id 필수, 시스템 테넌트 불가
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

## 6. 프론트엔드 연동

### 6.1 인증 상태 (Vuex auth 모듈)

```
localStorage: mureum_access_token, mureum_refresh_token, mureum_user
```

| Getter | 용도 |
|--------|------|
| `isAuthenticated` | 토큰 + 사용자 존재 여부 |
| `hasMenuPermission(menuCode, action)` | 메뉴별 CRUD 권한 확인 |
| `canAccessAdmin` | 관리자 메뉴 1개 이상 보유 여부 |
| `accessibleMenus` | 사이드바에 표시할 메뉴 목록 |

### 6.2 라우터 가드

```
router.beforeEach:
  1. 토큰 없으면 → /login 리디렉트
  2. canAccessAdmin 체크 → 관리자 접근 가능 여부
  3. 개별 라우트의 menuCode → hasMenuPermission(menuCode, 'read')
  4. 권한 없으면 → landing_page로 리디렉트
```

### 6.3 사이드바 동적 메뉴

로그인 응답의 `menus[]`로 사이드바를 동적 생성 (하드코딩 없음):
- `menu_type === 'PAGE'` 필터
- `can_read === true` 필터
- `sort_order` 정렬

---

## 7. 파일 구조

| 파일 | 역할 |
|------|------|
| `app/core/security/jwt.py` | JWT 생성/검증 (HS256) |
| `app/core/security/password.py` | bcrypt 해싱 |
| `app/core/security/dependencies.py` | `get_current_active_user` Depends |
| `app/core/security/permission.py` | `require_menu_permission` 팩토리 |
| `app/core/security/tenant_context.py` | contextvars 테넌트 격리 |
| `app/api/routes/auth.py` | 인증 엔드포인트 |
| `app/api/services/auth_service.py` | 인증 비즈니스 로직 |
| `frontend/src/store/modules/auth.js` | Vuex 인증 상태 |
| `frontend/src/api/auth.js` | 인증 API 클라이언트 |
| `frontend/src/router/index.js` | 라우터 가드 |

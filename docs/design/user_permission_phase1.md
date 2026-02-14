# Phase 1 구현 가이드: DB 테이블 + Pydantic 모델 (v2.0)

> **문서 버전**: 2.2
> **작성일**: 2026-02-12
> **수정일**: 2026-02-14
> **상위 문서**: `docs/design/user_permission_system.md` (v2.1)
> **상태**: ✅ 구현 완료
> **목적**: Phase 1(기반 구축)의 실제 구현 절차 — 현행 코드 상태 반영 + 마이그레이션 가이드
> **현행화**: 2026-02-14 — 모든 Step 구현 완료 확인됨

---

## 목차

1. [Phase 1 개요](#1-phase-1-개요)
2. [현행 코드 상태 분석](#2-현행-코드-상태-분석)
3. [Step 1: DDL — 데이터베이스 테이블](#3-step-1-ddl-실행)
4. [Step 2: `app/models/auth.py` — 인증 모델 (v1.0→v2.0)](#4-step-2-appmodelsauthpy)
5. [Step 3: `app/models/menu.py` — 메뉴/권한 모델 (신규)](#5-step-3-appmodelsmenupy)
6. [Step 4: `app/models/user.py` — 사용자/역할 모델 (v1.0→v2.0)](#6-step-4-appmodelsuserpy)
7. [Step 5: `app/models/tenant.py` — 테넌트 모델 (완료)](#7-step-5-appmodelstenantpy)
8. [Step 6: `app/config.py` — JWT 추가 설정 (완료)](#8-step-6-appconfigpy)
9. [Phase 2 연쇄 변경 영향 분석](#9-phase-2-연쇄-변경-영향-분석)
10. [검증 체크리스트](#10-검증-체크리스트)
11. [다음 단계 (Phase 2 Preview)](#11-다음-단계)

---

## 1. Phase 1 개요

### 1.1 무엇을 하는가

Phase 1은 **모든 후속 Phase의 기반**이 되는 데이터 구조를 확립하는 단계입니다.

```
Phase 1 산출물:
  [DB]  6개 테이블 + 초기 데이터 (메뉴 14개, 역할 3개, 테스트 계정 3개)
  [MOD] app/models/auth.py      ← v1.0 → v2.0 마이그레이션 (MenuPermission, role_code 추가)
  [NEW] app/models/menu.py      ← 메뉴/사용자메뉴 권한 모델 (★ 신규)
  [MOD] app/models/user.py      ← v1.0 → v2.0 마이그레이션 (role_id 단수, permission 제거)
  [OK]  app/models/tenant.py    ← 이미 v2.0 완료
  [OK]  app/config.py           ← 이미 v2.0 완료 (JWT 추가 설정 필드)
```

### 1.2 왜 필요한가

| 산출물 | 사용처 | 없으면 어떻게 되는가 |
|--------|--------|---------------------|
| DB 테이블 | Phase 2~5 전체 | 사용자/역할/메뉴 데이터를 저장할 곳이 없음 |
| Pydantic 모델 | API 요청/응답 직렬화, 타입 검증 | FastAPI 엔드포인트가 데이터 구조를 모름 |
| menu.py | 메뉴 기반 권한 체크 | 메뉴 트리와 CRUD 권한을 표현할 수 없음 |
| config.py 확장 | JWT 토큰 만료 시간 등 설정 | Phase 2에서 JWT 모듈이 설정값을 읽지 못함 |

### 1.3 구현 순서 (의존 관계)

```
Step 1: DDL 실행 (SQL 오류 수정 후)  → 이미 v2.0 완료 (오류 수정 필요)
Step 2: auth.py 마이그레이션         → v1.0 → v2.0 변경 (핵심 변경)
Step 3: menu.py 신규 생성            → 완전히 새로 만듦 (★)
Step 4: user.py 마이그레이션         → v1.0 → v2.0 변경 (menu.py 참조)
Step 5: tenant.py                    → 이미 v2.0 완료 ✅
Step 6: config.py                    → 이미 v2.0 완료 ✅
```

---

## 2. 현행 코드 상태 분석

### 2.1 파일별 현행 상태

| # | 대상 | 현재 버전 | 상태 | 비고 |
|---|------|-----------|------|------|
| 1 | `docs/sql/tb_user_permission.sql` | v2.0 | ✅ 구현 완료 | SQL 오류 수정 완료 |
| 2 | `app/models/auth.py` | v2.0 | ✅ 구현 완료 | `role_code`/`menus` 기반으로 전환 완료 |
| 3 | `app/models/menu.py` | v2.0 | ✅ 구현 완료 | 메뉴 트리 + 사용자 메뉴 권한 모델 생성 완료 |
| 4 | `app/models/user.py` | v2.0 | ✅ 구현 완료 | `role_id` 단일 FK, Permission 관련 제거 완료 |
| 5 | `app/models/tenant.py` | v2.0 | ✅ 완료 | 변경 없음 |
| 6 | `app/config.py` | v2.0 | ✅ 완료 | 변경 없음 |

### 2.2 현행 v1.0 코드의 문제점

#### auth.py — permission 코드 기반 (v1.0)

```python
# 현행 (v1.0): roles/permissions 리스트 기반
class UserInfo(BaseModel):
    roles: List[str]           # ["SYSTEM_ADMIN"]
    role_names: List[str]      # ["시스템 관리자"]
    permissions: List[str]     # ["nl2sql:execute", "admin:users"]

class UserContext(BaseModel):
    roles: List[str]
    permissions: List[str]
    def has_permission(self, code: str) -> bool: ...  # 코드 기반 체크
```

**문제**: `tb_permission`, `tb_role_permission`, `tb_user_role` 테이블이 v2.0 DDL에서 삭제되어 실행 불가.

#### user.py — M:N 역할 + Permission 참조 (v1.0)

```python
# 현행 (v1.0): M:N 역할, permission 코드
class UserCreate(UserBase):
    role_ids: List[int]          # M:N 역할 목록

class RoleCreate(RoleBase):
    permission_ids: List[int]    # 권한 ID 목록

class UserRoleAssign(BaseModel):   # tb_user_role 전용
class RolePermissionAssign(BaseModel):  # tb_role_permission 전용
class DataFilterResponse(BaseModel):    # tb_data_filter 전용
class PermissionSimple(BaseModel):      # tb_permission 전용
class PermissionResponse(BaseModel):    # tb_permission 전용
```

**문제**: 위 모델이 참조하는 테이블(`tb_user_role`, `tb_role_permission`, `tb_permission`, `tb_data_filter`)이 모두 삭제됨.

### 2.3 v1.0 → v2.0 변경 요약

| 구분 | v1.0 (현행) | v2.0 (목표) |
|------|:---:|:---:|
| 권한 단위 | `permission_code` (코드) | **`tb_menu` (메뉴)** |
| 사용자-역할 | M:N (`tb_user_role`) | **1:N** (`tb_user.role_id` FK) |
| 권한 매핑 | `tb_role_permission` | **`tb_user_menu`** (사용자별 직접) |
| 데이터 필터 | `tb_data_filter` 테이블 | **`tb_role.scope_type`** → 코드에서 유도 |
| 관리 UI | permission 코드 체크박스 | **메뉴 트리 + CRUD 체크박스** |

---

## 3. Step 1: DDL 실행

### 3.1 현행 상태

DDL 파일(`docs/sql/tb_user_permission.sql`)은 이미 v2.0으로 작성되어 있습니다.

**단, 336행에 SQL 오류가 있습니다:**

```sql
-- 332행 부근: 불필요한 라인 + 오타
INSERT INOT   -- ← "INSERT INTO" 오타, 대상 테이블도 없음
```

이 오류 라인(332~337행)은 DDL 실행 전에 제거해야 합니다.

### 3.2 실행 방법

```bash
conda activate penv3.13-nlq

psql "postgresql://hermesuser:hermesuser123%21@115.68.223.220:5432/hermesdb" -f docs/sql/tb_user_permission.sql
```

### 3.3 DDL이 생성하는 것

#### 테이블 6개

| # | 테이블명 | 용도 | 비고 |
|---|---------|------|------|
| 1 | `tb_tenant` | 테넌트(고객사) | |
| 2 | `tb_role` | 역할 정의 | `landing_page` 추가, `scope_type` CHECK |
| 3 | `tb_user` | 사용자 계정 | `role_id` FK 직접 보유 (1:N) |
| 4 | `tb_menu` | **메뉴 트리** | ★ 신규 (self-reference) |
| 5 | `tb_user_menu` | **사용자별 메뉴 CRUD 권한** | ★ 신규 (유일한 권한 테이블) |
| 6 | `tb_user_session` | JWT 세션 | |

#### 삭제되는 v1.0 테이블

| 제거 테이블 | 대체 방안 |
|------------|----------|
| `tb_permission` | `tb_menu`로 대체 |
| `tb_role_permission` | `tb_user_menu`로 대체 |
| `tb_user_role` | `tb_user.role_id` FK로 대체 |
| `tb_data_filter` | `tb_role.scope_type` + 서비스 코드로 대체 |

#### 초기 데이터

| 데이터 | 내용 |
|--------|------|
| 역할 3개 | SYSTEM_ADMIN (GLOBAL), TENANT_ADMIN (TENANT), USER (USER) |
| 메뉴 14개 | 루트 3 + 관리자 PAGE 10 + 사용자 PAGE 1 + API 3 = 17 (루트 DIRECTORY 3 + 하위 14) |
| 테넌트 2개 | SYSTEM (내부), DEMO (테스트) |
| 계정 3개 | admin (SYSTEM_ADMIN), tenant_admin (TENANT_ADMIN), user01 (USER) |
| 메뉴 권한 | admin→전체 CRUDE, tenant_admin→9개 메뉴, user01→4개 메뉴(채팅+API) |

### 3.4 실행 후 검증 쿼리

```sql
-- 1) 테이블 존재 확인 (6개)
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name LIKE 'tb_%'
  AND table_name IN ('tb_tenant','tb_role','tb_user','tb_menu','tb_user_menu','tb_user_session')
ORDER BY table_name;

-- 2) v1.0 잔존 테이블 삭제 확인 (0건)
SELECT table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_name IN ('tb_permission', 'tb_role_permission', 'tb_user_role', 'tb_data_filter');

-- 3) 역할 확인 (landing_page 포함)
SELECT role_code, role_name, scope_type, landing_page FROM tb_role ORDER BY sort_order;

-- 4) 메뉴 트리 확인
SELECT menu_id, REPEAT('  ', depth) || menu_name AS menu_tree,
       menu_code, menu_type, menu_path, depth
FROM tb_menu ORDER BY depth, sort_order;

-- 5) 사용자 + 역할 확인 (role_id FK 직접 조인)
SELECT u.login_id, u.display_name, u.is_superuser, r.role_code, r.scope_type
FROM tb_user u
JOIN tb_role r ON r.role_id = u.role_id
ORDER BY u.user_id;

-- 6) 사용자별 메뉴 권한 확인
SELECT u.login_id, r.role_code,
       m.menu_code, m.menu_name,
       um.can_create AS c, um.can_read AS r,
       um.can_update AS u, um.can_delete AS d, um.can_export AS e
FROM tb_user_menu um
JOIN tb_user u ON u.user_id = um.user_id
JOIN tb_menu m ON m.menu_id = um.menu_id
JOIN tb_role r ON r.role_id = u.role_id
ORDER BY u.login_id, m.depth, m.sort_order;

-- 7) 사용자별 접근 가능 메뉴 수
SELECT u.login_id, r.role_code, COUNT(*) AS menu_count
FROM tb_user_menu um
JOIN tb_user u ON u.user_id = um.user_id
JOIN tb_role r ON r.role_id = u.role_id
GROUP BY u.login_id, r.role_code
ORDER BY u.login_id;
-- admin=14, tenant_admin=9, user01=4
```

### 3.5 핵심 설계 원칙

```
tb_user_menu = "어떤 메뉴에 무엇을 할 수 있는가" (기능 접근, CRUD)
tb_role.scope_type = "어디까지 볼 수 있는가" (데이터 범위)

예: 사용자 관리 메뉴 Read 권한 + scope_type=TENANT → 자기 테넌트 사용자만
    사용자 관리 메뉴 Read 권한 + scope_type=GLOBAL → 전체 사용자
```

---

## 4. Step 2: `app/models/auth.py`

### 4.1 현행 상태와 변경 사유

| 구분 | 현행 (v1.0) | 목표 (v2.0) | 변경 이유 |
|------|------------|------------|----------|
| `UserInfo` | `roles: List[str]`, `permissions: List[str]` | `role_code: str`, `menus: List[MenuPermission]` | M:N→1:N, 메뉴 기반 전환 |
| `UserContext` | `roles`, `permissions`, `has_permission()` | `role_code`, `scope_type` (메뉴 권한은 DB) | Permission 코드 체크 폐기 |
| `TokenResponse` | `permissions` 포함 | `menus` 배열 포함 | 프론트엔드 메뉴 렌더링용 |
| `LoginRequest` | `min_length=5` | `min_length=1` | 로그인 ID 5자 제한 해제 |
| (없음) | — | `MenuPermission` 추가 | 로그인 응답에 메뉴 CRUD 포함 |

### 4.2 v2.0 전체 소스코드

```python
"""
인증(Authentication) 스키마 (v2.0 - 메뉴 기반)

위치: app/models/auth.py
로그인, 토큰, 사용자 컨텍스트 관련 모델
"""
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ===================================
# 메뉴 권한 (로그인 응답용)
# ===================================

class MenuPermission(BaseModel):
    """사용자가 접근 가능한 메뉴 + CRUD 권한 (로그인 응답에 포함)"""
    menu_code: str = Field(..., description="메뉴 코드")
    menu_name: str = Field(..., description="메뉴 표시명")
    menu_path: Optional[str] = Field(None, description="프론트엔드 URL 경로")
    menu_type: str = Field(..., description="메뉴 타입 (DIRECTORY, PAGE, API)")
    icon: Optional[str] = Field(None, description="아이콘 클래스")
    parent_menu_code: Optional[str] = Field(None, description="상위 메뉴 코드")
    depth: int = Field(default=0, description="트리 깊이")
    sort_order: int = Field(default=0, description="정렬 순서")
    can_create: bool = Field(default=False, description="등록 권한")
    can_read: bool = Field(default=True, description="조회 권한")
    can_update: bool = Field(default=False, description="수정 권한")
    can_delete: bool = Field(default=False, description="삭제 권한")
    can_export: bool = Field(default=False, description="내보내기 권한")


# ===================================
# 로그인 요청/응답
# ===================================

class LoginRequest(BaseModel):
    """로그인 요청"""
    login_id: str = Field(..., min_length=1, max_length=100, description="로그인 ID")
    password: str = Field(..., min_length=1, description="비밀번호")

    model_config = {
        "json_schema_extra": {
            "example": {
                "login_id": "admin",
                "password": "admin123!"
            }
        }
    }


class UserInfo(BaseModel):
    """로그인 응답에 포함되는 사용자 정보"""
    user_id: int = Field(..., description="사용자 ID")
    login_id: str = Field(..., description="로그인 ID")
    display_name: Optional[str] = Field(None, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")
    role_code: str = Field(..., description="역할 코드 (SYSTEM_ADMIN, TENANT_ADMIN, USER)")
    scope_type: str = Field(..., description="데이터 범위 (GLOBAL, TENANT, USER)")
    landing_page: str = Field(..., description="로그인 후 랜딩 페이지")
    menus: List[MenuPermission] = Field(default_factory=list, description="접근 가능 메뉴 + CRUD 권한")


class TokenResponse(BaseModel):
    """로그인 성공 응답 (JWT 토큰 + 사용자 정보 + 메뉴 목록)"""
    access_token: str = Field(..., description="JWT Access Token")
    refresh_token: str = Field(..., description="JWT Refresh Token")
    token_type: str = Field(default="Bearer", description="토큰 타입")
    expires_in: int = Field(..., description="Access Token 만료 시간 (초)")
    user: UserInfo = Field(..., description="사용자 정보 + 메뉴 권한")

    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIs...",
                "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
                "token_type": "Bearer",
                "expires_in": 1800,
                "user": {
                    "user_id": 1,
                    "login_id": "admin",
                    "display_name": "시스템 관리자",
                    "tenant_id": None,
                    "role_code": "SYSTEM_ADMIN",
                    "scope_type": "GLOBAL",
                    "landing_page": "/admin/dashboard",
                    "menus": [
                        {
                            "menu_code": "DASHBOARD",
                            "menu_name": "대시보드",
                            "menu_path": "/admin/dashboard",
                            "menu_type": "PAGE",
                            "icon": "dashboard",
                            "depth": 1,
                            "sort_order": 1,
                            "can_create": False,
                            "can_read": True,
                            "can_update": False,
                            "can_delete": False,
                            "can_export": False
                        }
                    ]
                }
            }
        }
    }


# ===================================
# 토큰 갱신
# ===================================

class RefreshRequest(BaseModel):
    """토큰 갱신 요청"""
    refresh_token: str = Field(..., min_length=1, description="Refresh Token")


# ===================================
# 비밀번호 변경
# ===================================

class PasswordChangeRequest(BaseModel):
    """비밀번호 변경 요청"""
    current_password: str = Field(..., min_length=1, description="현재 비밀번호")
    new_password: str = Field(..., min_length=8, description="새 비밀번호 (8자 이상)")

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """새 비밀번호 복잡도 검증"""
        if len(v) < 8:
            raise ValueError("비밀번호는 8자 이상이어야 합니다")
        has_upper = any(c.isupper() for c in v)
        has_lower = any(c.islower() for c in v)
        has_digit = any(c.isdigit() for c in v)
        if not (has_upper and has_lower and has_digit):
            raise ValueError("비밀번호는 대문자, 소문자, 숫자를 포함해야 합니다")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "current_password": "oldPassword1!",
                "new_password": "newPassword2!"
            }
        }
    }


# ===================================
# 사용자 컨텍스트 (인증 미들웨어 → API 핸들러)
# ===================================

class UserContext(BaseModel):
    """
    인증된 사용자 컨텍스트 (v2.0 - 메뉴 기반)

    인증 미들웨어가 JWT를 검증한 후 생성하여 request.state.current_user에 저장.
    모든 API 핸들러에서 현재 사용자 정보를 참조할 때 사용.

    v2.0 변경: permissions 리스트 제거 → role_code + scope_type만 보유.
    메뉴 권한 체크는 require_menu_permission()에서 DB 조회로 수행.
    """
    user_id: int = Field(..., description="사용자 ID")
    login_id: str = Field(..., description="로그인 ID")
    display_name: Optional[str] = Field(None, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")
    is_superuser: bool = Field(default=False, description="슈퍼유저 여부")
    role_code: str = Field(default="USER", description="역할 코드")
    scope_type: str = Field(default="USER", description="데이터 범위 (GLOBAL, TENANT, USER)")

    @property
    def is_global(self) -> bool:
        """GLOBAL scope 여부 (전체 데이터 접근)"""
        return self.is_superuser or self.scope_type == "GLOBAL"

    @property
    def is_tenant_scope(self) -> bool:
        """TENANT scope 여부"""
        return self.scope_type == "TENANT"

    @property
    def is_user_scope(self) -> bool:
        """USER scope 여부"""
        return self.scope_type == "USER"
```

### 4.3 v1.0 → v2.0 핵심 변경 요약

#### 제거된 항목

| 항목 | 이유 |
|------|------|
| `UserInfo.roles: List[str]` | `role_code: str`로 대체 (1:N) |
| `UserInfo.role_names: List[str]` | 제거 (프론트엔드에서 불필요) |
| `UserInfo.permissions: List[str]` | `menus: List[MenuPermission]`으로 대체 |
| `UserContext.roles: List[str]` | `role_code: str`로 대체 |
| `UserContext.permissions: List[str]` | 제거 (DB 조회로 대체) |
| `UserContext.has_permission()` | 제거 (`require_menu_permission()`으로 대체) |
| `UserContext.has_any_permission()` | 제거 |
| `UserContext.has_all_permissions()` | 제거 |

#### 추가된 항목

| 항목 | 용도 |
|------|------|
| `MenuPermission` (클래스) | 로그인 응답에 메뉴+CRUD 권한 포함 |
| `UserInfo.role_code: str` | 단일 역할 코드 |
| `UserInfo.landing_page: str` | 로그인 후 랜딩 페이지 |
| `UserInfo.menus: List[MenuPermission]` | 프론트엔드 사이드바 메뉴 렌더링용 |
| `UserContext.role_code: str` | JWT에서 역할 코드 추출 |

---

## 5. Step 3: `app/models/menu.py`

### 5.1 현행 상태

**파일이 존재하지 않습니다.** v2.0에서 신규 생성해야 합니다.

### 5.2 이 파일이 필요한 이유

| 클래스 | 사용처 | 없으면 어떻게 되는가 |
|--------|--------|---------------------|
| `MenuResponse` | 메뉴 트리 조회 | 메뉴 목록을 구조화하여 반환할 수 없음 |
| `MenuCreate` | 메뉴 추가 | 메뉴 생성 요청을 검증할 수 없음 |
| `MenuUpdate` | 메뉴 수정 | 메뉴 수정 요청을 파싱할 수 없음 |
| `UserMenuPermission` | 사용자 메뉴 권한 항목 | CRUD 권한 설정 불가 |
| `UserMenuAssign` | 사용자 메뉴 권한 일괄 할당 | 사용자별 메뉴 권한 설정 불가 |
| `UserMenuResponse` | 사용자 메뉴 권한 조회 | 사용자 메뉴 권한 반환 불가 |

### 5.3 v2.0 전체 소스코드

```python
"""
메뉴 및 사용자 메뉴 권한 스키마 (v2.0)

위치: app/models/menu.py
메뉴 트리 CRUD, 사용자별 메뉴 CRUD 권한 관련 모델
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator


# ===================================
# 메뉴 (Menu)
# ===================================

class MenuBase(BaseModel):
    """메뉴 기본 필드"""
    menu_code: str = Field(..., min_length=1, max_length=50, description="메뉴 코드")
    menu_name: str = Field(..., min_length=1, max_length=100, description="메뉴 표시명")
    menu_type: str = Field(..., description="메뉴 타입 (DIRECTORY, PAGE, API)")
    parent_menu_id: Optional[int] = Field(None, description="상위 메뉴 ID (NULL이면 루트)")
    menu_path: Optional[str] = Field(None, max_length=200, description="프론트엔드 URL 경로")
    api_pattern: Optional[str] = Field(None, max_length=200, description="API 경로 패턴")
    icon: Optional[str] = Field(None, max_length=50, description="아이콘 클래스")
    sort_order: int = Field(default=0, description="정렬 순서")
    description: Optional[str] = Field(None, description="설명")

    @field_validator("menu_type")
    @classmethod
    def validate_menu_type(cls, v: str) -> str:
        valid = ["DIRECTORY", "PAGE", "API"]
        v = v.upper()
        if v not in valid:
            raise ValueError(f"menu_type은 {valid} 중 하나여야 합니다")
        return v

    @field_validator("menu_code")
    @classmethod
    def validate_menu_code(cls, v: str) -> str:
        v = v.upper().strip()
        if not all(c.isalnum() or c == "_" for c in v):
            raise ValueError("메뉴 코드는 영문, 숫자, 언더스코어(_)만 사용 가능합니다")
        return v


class MenuCreate(MenuBase):
    """메뉴 생성 요청"""
    is_active: bool = Field(default=True, description="활성 여부")

    model_config = {
        "json_schema_extra": {
            "example": {
                "menu_code": "REPORTS",
                "menu_name": "리포트",
                "menu_type": "PAGE",
                "parent_menu_id": 1,
                "menu_path": "/admin/reports",
                "icon": "chart",
                "sort_order": 11,
                "is_active": True
            }
        }
    }


class MenuUpdate(BaseModel):
    """메뉴 수정 요청 (모든 필드 Optional)"""
    menu_name: Optional[str] = Field(None, max_length=100, description="메뉴 표시명")
    menu_path: Optional[str] = Field(None, max_length=200, description="프론트엔드 URL 경로")
    api_pattern: Optional[str] = Field(None, max_length=200, description="API 경로 패턴")
    icon: Optional[str] = Field(None, max_length=50, description="아이콘 클래스")
    sort_order: Optional[int] = Field(None, description="정렬 순서")
    is_active: Optional[bool] = Field(None, description="활성 여부")
    description: Optional[str] = Field(None, description="설명")


class MenuResponse(BaseModel):
    """메뉴 상세 응답"""
    menu_id: int = Field(..., description="메뉴 ID")
    parent_menu_id: Optional[int] = Field(None, description="상위 메뉴 ID")
    menu_code: str = Field(..., description="메뉴 코드")
    menu_name: str = Field(..., description="메뉴 표시명")
    menu_type: str = Field(..., description="메뉴 타입")
    menu_path: Optional[str] = Field(None, description="프론트엔드 URL 경로")
    api_pattern: Optional[str] = Field(None, description="API 경로 패턴")
    icon: Optional[str] = Field(None, description="아이콘 클래스")
    sort_order: int = Field(default=0, description="정렬 순서")
    depth: int = Field(default=0, description="트리 깊이")
    is_active: bool = Field(default=True, description="활성 여부")
    description: Optional[str] = Field(None, description="설명")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")
    children: List["MenuResponse"] = Field(default_factory=list, description="하위 메뉴")

    model_config = {
        "json_schema_extra": {
            "example": {
                "menu_id": 4,
                "parent_menu_id": 1,
                "menu_code": "DASHBOARD",
                "menu_name": "대시보드",
                "menu_type": "PAGE",
                "menu_path": "/admin/dashboard",
                "icon": "dashboard",
                "sort_order": 1,
                "depth": 1,
                "is_active": True,
                "children": []
            }
        }
    }


class MenuTreeResponse(BaseModel):
    """메뉴 트리 응답 (전체 트리)"""
    items: List[MenuResponse] = Field(default_factory=list, description="루트 메뉴 목록 (하위 포함)")


# ===================================
# 사용자-메뉴 권한 (UserMenu)
# ===================================

class UserMenuPermission(BaseModel):
    """사용자 메뉴 권한 항목 (할당 요청 시 사용)"""
    menu_id: int = Field(..., description="메뉴 ID")
    can_create: bool = Field(default=False, description="등록 권한")
    can_read: bool = Field(default=True, description="조회 권한")
    can_update: bool = Field(default=False, description="수정 권한")
    can_delete: bool = Field(default=False, description="삭제 권한")
    can_export: bool = Field(default=False, description="내보내기 권한")


class UserMenuAssign(BaseModel):
    """사용자 메뉴 권한 일괄 할당 요청"""
    menus: List[UserMenuPermission] = Field(..., min_length=1, description="메뉴 권한 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "menus": [
                    {"menu_id": 4, "can_create": False, "can_read": True, "can_update": False, "can_delete": False, "can_export": False},
                    {"menu_id": 5, "can_create": True, "can_read": True, "can_update": False, "can_delete": False, "can_export": False}
                ]
            }
        }
    }


class UserMenuResponse(BaseModel):
    """사용자별 메뉴 권한 응답 (메뉴 정보 포함)"""
    menu_id: int = Field(..., description="메뉴 ID")
    menu_code: str = Field(..., description="메뉴 코드")
    menu_name: str = Field(..., description="메뉴 표시명")
    menu_type: str = Field(..., description="메뉴 타입")
    menu_path: Optional[str] = Field(None, description="프론트엔드 URL 경로")
    icon: Optional[str] = Field(None, description="아이콘 클래스")
    depth: int = Field(default=0, description="트리 깊이")
    sort_order: int = Field(default=0, description="정렬 순서")
    can_create: bool = Field(default=False, description="등록 권한")
    can_read: bool = Field(default=True, description="조회 권한")
    can_update: bool = Field(default=False, description="수정 권한")
    can_delete: bool = Field(default=False, description="삭제 권한")
    can_export: bool = Field(default=False, description="내보내기 권한")
    granted_at: Optional[datetime] = Field(None, description="부여일시")
```

### 5.4 주요 설계 포인트

#### MenuResponse — 재귀 트리 구조

```python
children: List["MenuResponse"] = Field(default_factory=list)
```

서비스 레이어에서 `parent_menu_id`로 그룹핑하여 트리 생성:
```json
{
  "menu_code": "ADMIN", "menu_type": "DIRECTORY",
  "children": [
    {"menu_code": "DASHBOARD", "menu_type": "PAGE", "children": []},
    {"menu_code": "CHAT", "menu_type": "PAGE", "children": []}
  ]
}
```

#### UserMenuAssign — 메뉴 권한 일괄 할당

사용자 생성/수정 시 DB 처리 흐름 (Phase 4에서 구현):
```
1. 기존 tb_user_menu에서 해당 사용자 권한 전체 삭제
2. menus 배열의 각 항목에 대해 tb_user_menu INSERT
3. granted_by에 현재 관리자 user_id 저장
```

---

## 6. Step 4: `app/models/user.py`

### 6.1 현행 상태와 변경 사유

| 구분 | 현행 (v1.0) | 목표 (v2.0) | 변경 이유 |
|------|------------|------------|----------|
| `UserCreate` | `role_ids: List[int]` (M:N) | `role_id: int` + `menus: List[UserMenuPermission]` | 1:N + 메뉴 권한 직접 지정 |
| `UserResponse` | `roles: List[RoleSimple]` | `role: RoleSimple` (단수) + `menu_count: int` | 1:N 반영 |
| `RoleSimple` | `scope_type`만 | + `landing_page: str` | 랜딩 페이지 추가 |
| `RoleCreate` | `permission_ids: List[int]` | `landing_page: str` | permission 제거 |
| `RoleResponse` | `permissions: List[PermissionSimple]` | `landing_page`, `user_count` | permission 제거 |
| 제거 대상 | `PermissionSimple`, `PermissionResponse`, `UserRoleAssign`, `RolePermissionAssign`, `DataFilterResponse` | — | v1.0 전용 모델 |

### 6.2 v2.0 전체 소스코드

```python
"""
사용자/역할 관리 스키마 (v2.0 - 메뉴 기반)

위치: app/models/user.py
사용자 CRUD, 역할 관리 관련 모델
"""
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from app.models.menu import UserMenuPermission


# ===================================
# 역할 (Role)
# ===================================

class RoleSimple(BaseModel):
    """역할 간략 정보 (UserResponse에 포함용)"""
    role_id: int = Field(..., description="역할 ID")
    role_code: str = Field(..., description="역할 코드")
    role_name: str = Field(..., description="역할명")
    scope_type: str = Field(..., description="데이터 범위")
    landing_page: str = Field(..., description="랜딩 페이지")


class RoleCreate(BaseModel):
    """역할 생성 요청"""
    role_code: str = Field(..., min_length=1, max_length=50, description="역할 코드")
    role_name: str = Field(..., min_length=1, max_length=100, description="역할명")
    description: Optional[str] = Field(None, description="설명")
    scope_type: str = Field(..., description="데이터 범위 (GLOBAL, TENANT, USER)")
    landing_page: str = Field(default="/chat", max_length=200, description="로그인 후 랜딩 페이지")

    @field_validator("scope_type")
    @classmethod
    def validate_scope_type(cls, v: str) -> str:
        valid = ["GLOBAL", "TENANT", "USER"]
        v = v.upper()
        if v not in valid:
            raise ValueError(f"scope_type은 {valid} 중 하나여야 합니다")
        return v

    model_config = {
        "json_schema_extra": {
            "example": {
                "role_code": "DEPT_ADMIN",
                "role_name": "부서 관리자",
                "description": "부서 내 데이터만 접근",
                "scope_type": "TENANT",
                "landing_page": "/admin/dashboard"
            }
        }
    }


class RoleUpdate(BaseModel):
    """역할 수정 요청 (모든 필드 Optional)"""
    role_name: Optional[str] = Field(None, max_length=100, description="역할명")
    description: Optional[str] = Field(None, description="설명")
    scope_type: Optional[str] = Field(None, description="데이터 범위")
    landing_page: Optional[str] = Field(None, max_length=200, description="랜딩 페이지")

    @field_validator("scope_type")
    @classmethod
    def validate_scope_type(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            valid = ["GLOBAL", "TENANT", "USER"]
            v = v.upper()
            if v not in valid:
                raise ValueError(f"scope_type은 {valid} 중 하나여야 합니다")
        return v


class RoleResponse(BaseModel):
    """역할 상세 응답"""
    role_id: int = Field(..., description="역할 ID")
    role_code: str = Field(..., description="역할 코드")
    role_name: str = Field(..., description="역할명")
    description: Optional[str] = Field(None, description="설명")
    scope_type: str = Field(..., description="데이터 범위")
    landing_page: str = Field(..., description="랜딩 페이지")
    is_system: bool = Field(..., description="시스템 기본 역할 여부")
    sort_order: int = Field(0, description="정렬 순서")
    user_count: int = Field(default=0, description="소속 사용자 수")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    model_config = {
        "json_schema_extra": {
            "example": {
                "role_id": 1,
                "role_code": "SYSTEM_ADMIN",
                "role_name": "시스템 관리자",
                "scope_type": "GLOBAL",
                "landing_page": "/admin/dashboard",
                "is_system": True,
                "user_count": 1,
                "sort_order": 1
            }
        }
    }


class RoleListResponse(BaseModel):
    """역할 목록 응답"""
    total: int = Field(..., description="전체 역할 수")
    items: List[RoleResponse] = Field(default_factory=list, description="역할 목록")


# ===================================
# 사용자 (User)
# ===================================

class UserBase(BaseModel):
    """사용자 기본 필드"""
    login_id: str = Field(..., min_length=1, max_length=100, description="로그인 ID")
    email: str = Field(..., max_length=255, description="이메일")
    display_name: Optional[str] = Field(None, max_length=100, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v or "." not in v.split("@")[-1]:
            raise ValueError("올바른 이메일 형식이 아닙니다")
        return v.lower().strip()


class UserCreate(UserBase):
    """사용자 생성 요청 (역할 + 메뉴 권한 포함)"""
    password: str = Field(..., min_length=8, description="비밀번호 (8자 이상)")
    role_id: int = Field(..., description="역할 ID (사용자는 하나의 역할에 소속)")
    is_active: bool = Field(default=True, description="활성화 여부")
    menus: List[UserMenuPermission] = Field(default_factory=list, description="메뉴 권한 목록")

    model_config = {
        "json_schema_extra": {
            "example": {
                "login_id": "user02",
                "email": "user02@company.com",
                "display_name": "김철수",
                "password": "Password1!",
                "tenant_id": 2,
                "role_id": 3,
                "is_active": True,
                "menus": [
                    {"menu_id": 14, "can_create": True, "can_read": True}
                ]
            }
        }
    }


class UserUpdate(BaseModel):
    """사용자 수정 요청 (모든 필드 Optional)"""
    email: Optional[str] = Field(None, max_length=255, description="이메일")
    display_name: Optional[str] = Field(None, max_length=100, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")
    role_id: Optional[int] = Field(None, description="역할 ID")
    is_active: Optional[bool] = Field(None, description="활성화 여부")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            if "@" not in v or "." not in v.split("@")[-1]:
                raise ValueError("올바른 이메일 형식이 아닙니다")
            return v.lower().strip()
        return v


class UserResponse(BaseModel):
    """사용자 상세 응답"""
    user_id: int = Field(..., description="사용자 ID")
    login_id: str = Field(..., description="로그인 ID")
    email: str = Field(..., description="이메일")
    display_name: Optional[str] = Field(None, description="표시 이름")
    tenant_id: Optional[int] = Field(None, description="소속 테넌트 ID")
    tenant_name: Optional[str] = Field(None, description="소속 테넌트명")
    role: RoleSimple = Field(..., description="역할 정보")
    is_active: bool = Field(..., description="활성화 여부")
    is_superuser: bool = Field(default=False, description="슈퍼유저 여부")
    menu_count: int = Field(default=0, description="접근 가능 메뉴 수")
    last_login_at: Optional[datetime] = Field(None, description="마지막 로그인 일시")
    created_at: datetime = Field(..., description="생성일시")
    updated_at: datetime = Field(..., description="수정일시")

    model_config = {
        "json_schema_extra": {
            "example": {
                "user_id": 1,
                "login_id": "admin",
                "email": "admin@system.local",
                "display_name": "시스템 관리자",
                "tenant_id": None,
                "tenant_name": None,
                "role": {
                    "role_id": 1,
                    "role_code": "SYSTEM_ADMIN",
                    "role_name": "시스템 관리자",
                    "scope_type": "GLOBAL",
                    "landing_page": "/admin/dashboard"
                },
                "is_active": True,
                "is_superuser": True,
                "menu_count": 14,
                "last_login_at": "2026-02-12T10:00:00+09:00"
            }
        }
    }


class UserListResponse(BaseModel):
    """사용자 목록 응답"""
    total: int = Field(..., description="전체 사용자 수")
    items: List[UserResponse] = Field(default_factory=list, description="사용자 목록")
    limit: int = Field(..., description="요청된 limit")
    offset: int = Field(..., description="요청된 offset")
```

### 6.3 v1.0 → v2.0 제거 대상

| v1.0 모델 | 제거 이유 |
|-----------|----------|
| `PermissionSimple` | `tb_permission` 테이블 삭제 → `tb_menu`로 대체 |
| `PermissionResponse` | `tb_permission` 테이블 삭제 |
| `UserRoleAssign` | `tb_user_role` M:N 삭제 → `UserUpdate.role_id`로 대체 |
| `RolePermissionAssign` | `tb_role_permission` 삭제 → `UserMenuAssign`으로 대체 |
| `DataFilterResponse` | `tb_data_filter` 삭제 → `scope_type` 코드 유도 |
| `RoleBase` | 불필요 (RoleCreate 직접 정의) |

---

## 7. Step 5: `app/models/tenant.py`

### 7.1 현행 상태

**이미 v2.0 완료. 변경 불필요.** ✅

현행 코드 확인 결과, v2.0 설계와 완전히 일치합니다:

- `TenantBase`, `TenantCreate`, `TenantUpdate`, `TenantResponse`, `TenantListResponse`
- `tenant_code` 검증 (영문 대문자 + 숫자 + 언더스코어)
- `user_count` 필드 (JOIN 계산)
- `metadata: JSONB` 지원

---

## 8. Step 6: `app/config.py`

### 8.1 현행 상태

**이미 v2.0 완료. 변경 불필요.** ✅

현행 `app/config.py`에 JWT 관련 필드가 모두 포함되어 있습니다:

```python
# Security (현재 config.py에 이미 있음)
secret_key: str = Field(..., description="JWT 시크릿 키")
algorithm: str = Field(default="HS256", description="JWT 알고리즘")
access_token_expire_minutes: int = Field(default=30, description="액세스 토큰 만료 시간(분)")
jwt_refresh_token_expire_days: int = Field(default=7, description="Refresh Token 만료 시간(일)")
password_min_length: int = Field(default=8, description="최소 비밀번호 길이")
login_max_fail_count: int = Field(default=5, description="로그인 실패 허용 횟수")
login_lock_minutes: int = Field(default=30, description="계정 잠금 시간(분)")
```

---

## 9. Phase 2 연쇄 변경 영향 분석

Phase 1에서 `auth.py`, `user.py` 모델이 v2.0으로 변경되면, 이를 참조하는 **기존 코드 전체**가 영향을 받습니다. 아래는 Phase 2에서 반드시 함께 변경해야 하는 파일 목록입니다.

### 9.1 직접 영향 파일 (반드시 동시 수정)

| 파일 | 현행 v1.0 참조 | v2.0 변경 내용 |
|------|--------------|---------------|
| `app/core/security/jwt.py` | `TokenPayload.roles`, `.permissions` | `role_code: str` 단일, permissions 제거 |
| `app/core/security/dependencies.py` | `UserContext(roles=..., permissions=...)` | `UserContext(role_code=...)` |
| `app/core/security/permission.py` | `require_permission("admin:users")` → `has_all_permissions()` | `require_menu_permission("USER_MGMT", "read")` → DB 조회 |
| `app/api/services/auth_service.py` | `tb_user_role`, `tb_role_permission`, `tb_permission` JOIN | `tb_user.role_id` → `tb_role` 직접 JOIN, `tb_user_menu` 조회 |
| `app/api/services/user_service.py` | `tb_user_role` INSERT/DELETE, `role_ids` | `tb_user.role_id` UPDATE, `tb_user_menu` INSERT |
| `app/api/routes/auth.py` | `UserInfo(roles=..., permissions=...)` | `UserInfo(role_code=..., menus=...)` |
| `app/api/routes/users.py` | `require_permission("admin:users")`, `UserRoleAssign` | `require_menu_permission("USER_MGMT", ...)`, `UserMenuAssign` |

### 9.2 현행 코드 → v2.0 변경 포인트 상세

#### 9.2.1 jwt.py — TokenPayload

```python
# 현행 (v1.0)
class TokenPayload(BaseModel):
    roles: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)

# 목표 (v2.0)
class TokenPayload(BaseModel):
    role_code: str = Field(default="USER")
    # roles, permissions 제거
```

#### 9.2.2 dependencies.py — UserContext 생성

```python
# 현행 (v1.0)
return UserContext(
    ...,
    roles=payload.roles,
    permissions=payload.permissions,
)

# 목표 (v2.0)
return UserContext(
    ...,
    role_code=payload.role_code,
    # roles, permissions 제거
)
```

#### 9.2.3 permission.py — 메뉴 기반 권한 체크

```python
# 현행 (v1.0)
def require_permission(*required_permissions: str):
    """permission 코드 기반 체크"""
    if not current_user.has_all_permissions(*required_permissions):
        raise ...

# 목표 (v2.0)
def require_menu_permission(menu_code: str, action: str):
    """메뉴 + CRUD 기반 체크 (DB 조회)"""
    query = """
        SELECT can_create, can_read, can_update, can_delete, can_export
        FROM tb_user_menu um
        JOIN tb_menu m ON m.menu_id = um.menu_id
        WHERE um.user_id = %s AND m.menu_code = %s AND m.is_active = true
    """
    if not row or not row[f"can_{action}"]:
        raise ...
```

#### 9.2.4 auth_service.py — 권한 조회 쿼리

```python
# 현행 (v1.0): tb_user_role, tb_role_permission, tb_permission JOIN
cur.execute(
    "SELECT DISTINCT r.role_code, r.role_name, r.scope_type, p.permission_code "
    "FROM tb_user_role ur "
    "JOIN tb_role r ON ur.role_id = r.role_id "
    "LEFT JOIN tb_role_permission rp ON r.role_id = rp.role_id "
    "LEFT JOIN tb_permission p ON rp.permission_id = p.permission_id "
    "WHERE ur.user_id = %s", (user_id,))

# 목표 (v2.0): tb_user.role_id → tb_role 직접 JOIN + tb_user_menu
cur.execute(
    "SELECT u.user_id, u.login_id, u.display_name, u.tenant_id, u.is_superuser, "
    "r.role_code, r.role_name, r.scope_type, r.landing_page "
    "FROM tb_user u "
    "JOIN tb_role r ON r.role_id = u.role_id "
    "WHERE u.user_id = %s", (user_id,))

# 메뉴 권한 별도 조회
cur.execute(
    "SELECT m.menu_code, m.menu_name, m.menu_path, m.menu_type, m.icon, "
    "m.depth, m.sort_order, pm.menu_code AS parent_menu_code, "
    "um.can_create, um.can_read, um.can_update, um.can_delete, um.can_export "
    "FROM tb_user_menu um "
    "JOIN tb_menu m ON m.menu_id = um.menu_id "
    "LEFT JOIN tb_menu pm ON pm.menu_id = m.parent_menu_id "
    "WHERE um.user_id = %s AND m.is_active = true "
    "ORDER BY m.depth, m.sort_order", (user_id,))
```

#### 9.2.5 user_service.py — 사용자 생성/역할할당

```python
# 현행 (v1.0)
cur.execute("INSERT INTO tb_user_role (user_id, role_id, ...) VALUES ...")

# 목표 (v2.0)
cur.execute(
    "INSERT INTO tb_user (..., role_id) VALUES (..., %s) RETURNING user_id",
    (..., data["role_id"]))
for menu in data.get("menus", []):
    cur.execute(
        "INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, ...) VALUES ...")
```

#### 9.2.6 users.py (route) — 엔드포인트 변경

```python
# 현행 (v1.0)
from app.models.user import UserRoleAssign
current_user = Depends(require_permission("admin:users"))

@router.put("/{user_id}/roles")
async def assign_roles(data: UserRoleAssign, ...):
    user_service.assign_roles(user_id, data.role_ids, ...)

@router.get("/{user_id}/permissions")
async def get_user_permissions(...):
    ...

# 목표 (v2.0)
from app.models.menu import UserMenuAssign
current_user = Depends(require_menu_permission("USER_MGMT", "read"))

@router.get("/{user_id}/menus")
async def get_user_menus(...):
    ...

@router.put("/{user_id}/menus")
async def assign_user_menus(data: UserMenuAssign, ...):
    ...
```

### 9.3 변경 순서 권장

```
Phase 1 모델 변경 완료 후, Phase 2에서 아래 순서로 진행:

1. jwt.py — TokenPayload에서 roles/permissions 제거, role_code 추가
2. dependencies.py — UserContext 생성부 수정
3. permission.py — require_menu_permission() 신규 구현
4. auth_service.py — 쿼리 전면 재작성 (가장 큰 변경)
5. user_service.py — 사용자 CRUD + 메뉴 권한 할당
6. routes (auth.py, users.py) — 모델 참조 + 권한 체크 변경

※ 1~3은 Phase 2, 4~6은 Phase 3~4에 해당
```

---

## 10. 검증 체크리스트

Phase 1 완료 후 아래 항목을 확인합니다.

### 10.1 DB 검증

- [x] 6개 테이블 모두 생성 확인 (`tb_tenant, tb_role, tb_user, tb_menu, tb_user_menu, tb_user_session`)
- [x] v1.0 잔존 테이블 삭제 확인 (`tb_permission, tb_role_permission, tb_user_role, tb_data_filter` 없음)
- [x] 3개 역할 정상 INSERT + `landing_page` 확인
- [x] 메뉴 트리 정상 확인 (루트 3 + 하위 14)
- [x] 3개 계정 존재 + `role_id` FK 정상 확인
- [x] 사용자별 메뉴 권한 정상 확인 (admin=14, tenant_admin=9, user01=4)
- [x] DDL 336행 SQL 오류 수정 확인

### 10.2 Pydantic 모델 검증

```python
conda activate penv3.13-nlq
python

# 1. auth.py import
from app.models.auth import (
    LoginRequest, TokenResponse, UserInfo, UserContext,
    MenuPermission, RefreshRequest, PasswordChangeRequest
)

# 2. menu.py import (★ 신규)
from app.models.menu import (
    MenuCreate, MenuUpdate, MenuResponse, MenuTreeResponse,
    UserMenuPermission, UserMenuAssign, UserMenuResponse
)

# 3. user.py import
from app.models.user import (
    UserCreate, UserUpdate, UserResponse, UserListResponse,
    RoleCreate, RoleUpdate, RoleResponse, RoleListResponse, RoleSimple
)

# 4. tenant.py import
from app.models.tenant import (
    TenantCreate, TenantUpdate, TenantResponse, TenantListResponse
)

# 5. v2.0 인스턴스 생성 테스트
user_ctx = UserContext(
    user_id=1, login_id="admin", role_code="SYSTEM_ADMIN",
    scope_type="GLOBAL", is_superuser=True
)
print(user_ctx.is_global)    # True
print(user_ctx.role_code)    # "SYSTEM_ADMIN"

# 6. v1.0 잔존 확인 (이것들이 import 에러 나면 정상)
# from app.models.user import PermissionSimple    → ImportError ✅
# from app.models.user import UserRoleAssign      → ImportError ✅
# from app.models.user import DataFilterResponse  → ImportError ✅

# 7. UserCreate (역할 + 메뉴 포함)
menu_perm = UserMenuPermission(menu_id=4, can_create=False, can_read=True)
user = UserCreate(
    login_id="test", email="test@test.com", password="Password1!",
    role_id=3, menus=[menu_perm]
)
print(f"role_id={user.role_id}, menus={len(user.menus)}")
# role_id=3, menus=1
```

### 10.3 최종 확인

- [x] `app/models/__init__.py`는 빈 파일 유지 (CLAUDE.md 규칙)
- [x] `app/models/menu.py` 신규 생성 확인
- [x] `app/models/auth.py`에서 `roles`, `permissions` 필드 완전 제거 확인
- [x] `app/models/user.py`에서 `PermissionSimple`, `UserRoleAssign`, `DataFilterResponse` 완전 제거 확인
- [x] v1.0 전용 모델 제거로 인한 import 오류 발생 파일 목록 확인 (→ Phase 2에서 수정 완료)

---

## 11. 다음 단계

Phase 1 완료 후 **Phase 2: 연쇄 변경 — Security 모듈 + Service + Route v2.0 마이그레이션**을 진행합니다.

### 11.1 Phase 2에서 수정할 파일

```
app/core/security/
├── jwt.py                   # TokenPayload: roles/permissions → role_code
├── dependencies.py          # UserContext 생성: roles/permissions 제거
└── permission.py            # require_permission → require_menu_permission (★ 핵심)

app/api/services/
├── auth_service.py          # 쿼리 전면 재작성 (tb_user_role → tb_user.role_id + tb_user_menu)
└── user_service.py          # 사용자 CRUD + tb_user_menu 권한 할당

app/api/routes/
├── auth.py                  # UserInfo 생성 변경 (menus 포함)
├── users.py                 # require_menu_permission + menus 엔드포인트
├── menus.py                 # ★ 신규: 메뉴 관리 API
├── roles.py                 # 기존 or 신규: 역할 관리 API
└── tenants.py               # 기존 or 신규: 테넌트 관리 API
```

### 11.2 Phase 의존 관계 (전체)

```
Phase 1: DB 테이블 + Pydantic 모델 (v2.0)     ← 현재 문서
    │
    ▼
Phase 2: Core Security (JWT, Dependencies, Permission v2.0)
    │
    ▼
Phase 3: Auth API + Auth Middleware (v2.0 모델 사용)
    │
    ├───────────────────────┐
    ▼                       ▼
Phase 4:                Phase 5:
관리 API (CRUD)         NL2SQL 필터 +
+ 메뉴 관리             프론트엔드
```

---

## 부록 A: DB 테이블 ↔ Pydantic 모델 매핑

| DB 테이블 | Create 모델 | Response 모델 | 비고 |
|-----------|------------|--------------|------|
| `tb_tenant` | `TenantCreate` | `TenantResponse` | `user_count`는 JOIN으로 계산 |
| `tb_role` | `RoleCreate` | `RoleResponse` | `landing_page` 포함, `user_count` JOIN |
| `tb_user` | `UserCreate` | `UserResponse` | `role_id` FK, `menus` 동시 할당 |
| `tb_menu` | `MenuCreate` | `MenuResponse` | 재귀 `children` 필드로 트리 표현 |
| `tb_user_menu` | `UserMenuAssign` | `UserMenuResponse` | ★ 유일한 권한 테이블 |
| `tb_user_session` | — | — | 내부 전용 (API 노출 안 함) |

## 부록 B: v1.0에서 제거된 모델

| v1.0 모델 | 위치 | 제거 이유 |
|-----------|------|----------|
| `PermissionSimple` | user.py | `tb_permission` 삭제 → `tb_menu`로 대체 |
| `PermissionResponse` | user.py | `tb_permission` 삭제 |
| `UserRoleAssign` | user.py | `tb_user_role` M:N 삭제 → `UserUpdate.role_id`로 대체 |
| `RolePermissionAssign` | user.py | `tb_role_permission` 삭제 → `UserMenuAssign`으로 대체 |
| `DataFilterResponse` | user.py | `tb_data_filter` 삭제 → `scope_type` 코드 유도 |
| `RoleBase` | user.py | `RoleCreate`에서 직접 정의 |
| `UserInfo.roles` | auth.py | `role_code: str` 단일로 대체 |
| `UserInfo.role_names` | auth.py | 제거 (불필요) |
| `UserInfo.permissions` | auth.py | `menus: List[MenuPermission]`으로 대체 |
| `UserContext.roles` | auth.py | `role_code: str`로 대체 |
| `UserContext.permissions` | auth.py | DB 조회로 대체 |
| `UserContext.has_permission()` | auth.py | `require_menu_permission()`으로 대체 |
| `UserContext.has_any_permission()` | auth.py | 제거 |
| `UserContext.has_all_permissions()` | auth.py | 제거 |

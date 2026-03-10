# 조직(부서) 관리 및 SSO 연동 설계서

> **문서 버전**: 3.0
> **작성일**: 2026-02-23
> **최종 수정**: 2026-03-09
> **상태**: Phase 1~3 구현 완료, Phase 4(SSO) 설계 확정 (RS256 + Frontend Redirect)
> **선행 문서**: `07_user_role_design.md`, `02_auth_and_permission.md`
> **마이그레이션**: `docs/sql/migration_v2_department_sso.sql`, `docs/sql/migration_v2_reorder_columns.sql`

---

## 1. 개요

### 1.1 목적

기존 3계층 역할(GLOBAL/TENANT/USER)에 **조직(부서) 기반 데이터 범위**를 추가하고,
외부 시스템과 **SSO 연동**을 통해 사용자·조직 정보를 자동 동기화한다.

### 1.2 설계 원칙 (기존 + 확장)

```
① tb_user_menu   = "어떤 기능을 쓸 수 있는가"     (기능 접근: CRUD)
② scope_level    = "어떤 범위의 데이터를 볼 수 있는가" (행 필터: 테넌트/부서/본인)
③ tb_role.role_code = "누구인가"                   (직함: 총괄, 조직관리자, 일반...)

같은 scope_level이라도 dept_id의 부서 계층 위치에 따라 조회 범위가 달라짐
예: scope_level=2(부서) + 개발본부 → 하위 전체 (개발1팀+개발2팀)
    scope_level=2(부서) + 개발1팀   → 개발1팀만
```

### 1.3 변경 범위 요약

| 구분 | 변경 내용 | 상태 |
|------|----------|:---:|
| 신규 테이블 | `tb_department` (recursive 조직 트리) | **완료** |
| 테이블 변경 | `tb_role` (scope_level 추가), `tb_user` (dept_id + SSO 컬럼 추가) | **완료** |
| 코드 데이터 | `tb_code` SSO_ROLE_MAP 직급-역할 매핑 | **완료** |
| 백엔드 인프라 | scope_filter.py, UserContext 확장, JWT 토큰 확장 | **완료** |
| 부서 CRUD API | 부서 트리 조회/생성/수정/삭제/순서변경 | **완료** |
| 부서 관리 UI | DepartmentsView.vue (트리 테이블 + CRUD) | **완료** |
| 사용자-부서 연동 | 사용자 생성/수정 시 부서 선택 드롭다운 | **완료** |
| 역할 Scope CRUD | 역할 생성/수정 시 scope_level 설정 | **완료** |
| role_code 리팩터 | 하드코딩 11곳 → scope_level 기반 공통 필터 교체 | **완료** |
| SSO 인프라 | RS256 공개키 검증, SSO 설정, Pydantic 모델 | 미구현 |
| SSO 인증 API | POST /api/v1/auth/sso (Token Exchange + JIT) | 미구현 |
| SSO 프론트엔드 | SSOCallbackView.vue, auth store/API/router 확장 | 미구현 |
| 키 생성 도구 | RS256 키 쌍 생성 스크립트 | 미구현 |
| SSO 테스트 | SSO 통합 테스트 (8개) | 미구현 |
| 배치 동기화 | 조직/사용자 배치 동기화 스크립트 | 미구현 |

---

## 2. 역할 계층 (변경 후)

### 2.1 scope_level 정의

scope_level은 **데이터 범위**를 숫자로 정의한다. 코드 상수로 관리하며 별도 테이블은 불필요하다.

```python
# app/core/security/scope_filter.py
SCOPE_GLOBAL = 0   # 전체 (필터 없음)
SCOPE_TENANT = 1   # 테넌트 범위 (tenant_id 필터)
SCOPE_DEPT   = 2   # 부서 범위 (tenant_id + dept_id 필터)
SCOPE_USER   = 3   # 본인 범위 (tenant_id + dept_id + user_id 필터)
```

### 2.2 역할 구조

| role_id | role_code | role_name | sort_order | scope_level | 데이터 범위 | landing_page |
|---------|-----------|-----------|-----------|-------------|------------|--------------|
| 1 | GLOBAL | 시스템 관리자 | 1 | 0 | 전체 | /admin/chat |
| 2 | TENANT | 테넌트 관리자 | 2 | 1 | 소속 테넌트 | /admin/chat |
| 19 | DEPT | 조직 관리자 | 3 | 2 | 소속 부서 + 하위 부서 | /admin/chat |
| 3 | USER | 일반 사용자 | 4 | 3 | 본인만 | /chat |

> **DEPT는 직책이 아닌 "데이터 범위"를 의미**:
> 본부장, 팀장, 파트장 모두 role_code=DEPT이며, 조회 범위는 dept_id의 트리 위치로 결정된다.
> 예) DEPT + 개발본부(depth=0) → 본부장 역할, DEPT + 개발1팀(depth=1) → 팀장 역할

### 2.3 scope_level별 필터 동작

scope_level은 **누적 방식**으로 동작한다. 레벨이 높을수록 필터가 추가된다.

```
scope_level 0 (GLOBAL):       필터 없음
                               SELECT * FROM employee

scope_level 1 (TENANT):       tenant_id 필터
                               SELECT * FROM employee
                               WHERE tenant_id = 10

scope_level 2 (DEPT):          tenant_id + dept_id 필터 (recursive 하위 포함)
                               SELECT * FROM employee
                               WHERE tenant_id = 10
                                 AND dept_id IN (10, 11, 12)  -- 본부 + 하위팀

scope_level 3 (USER):          tenant_id + dept_id + user_id 필터
                               SELECT * FROM employee
                               WHERE tenant_id = 10
                                 AND dept_id IN (11)
                                 AND user_id = 30
```

---

## 3. 데이터베이스 설계

### 3.1 ERD (변경 후)

```
                    ┌──────────────────────┐
                    │     tb_tenant        │
                    ├──────────────────────┤
                    │ tenant_id (PK)       │
                    │ tenant_code (UK)     │
                    │ tenant_name          │
                    │ is_active            │
                    │ is_system            │
                    │ metadata (JSONB)     │
                    └──────┬───┬───────────┘
                           │   │
                    1:N    │   │ 1:N
           ┌───────────────┘   └──────────────────┐
           ▼                                      ▼
┌─────────────────────┐              ┌────────────────────────┐
│    tb_department     │              │        tb_user         │
├─────────────────────┤              ├────────────────────────┤
│ dept_id (PK)        │◄─ 1:N ──────│ user_id (PK)           │
│ parent_dept_id (FK) │─┐ self-ref  │ login_id (UK)          │
│ tenant_id (FK)      │ │           │ email (UK)             │
│ dept_code (UK/tenant)│◄┘           │ password_hash          │
│ dept_name           │              │ display_name           │
│ depth               │              │ tenant_id (FK)         │
│ sort_order          │              │ role_id (FK)      ──┐  │
│ is_active           │              │ dept_id (FK) ★       │  │
└─────────────────────┘              │ is_active            │  │
                                     │ is_superuser         │  │
                                     │ sso_provider ★       │  │
                                     │ sso_external_id ★    │  │
                                     │ last_login_at        │  │
                                     │ login_fail_count     │  │
                                     │ locked_until         │  │
                                     └────────────────────┼──┘
                                                    N:1   │
                                     ┌────────────────────┘
                                     ▼
                          ┌────────────────────────┐
                          │       tb_role           │
                          ├────────────────────────┤
                          │ role_id (PK)           │
                          │ role_code (UK)         │
                          │ role_name              │
                          │ description            │
                          │ landing_page           │
                          │ is_system              │
                          │ sort_order             │
                          │ scope_level ★          │
                          └────────────────────────┘
```

> ★ = v2.0에서 추가된 컬럼. created_at/updated_at는 모든 테이블 공통이므로 ERD에서 생략.

### 3.2 tb_department (신규 — recursive 조직 트리)

tb_menu와 동일한 자기참조 패턴. 부서는 반드시 테넌트에 소속된다.

```sql
CREATE TABLE tb_department (
    dept_id         BIGSERIAL PRIMARY KEY,
    parent_dept_id  BIGINT REFERENCES tb_department(dept_id) ON DELETE SET NULL,
    tenant_id       BIGINT NOT NULL REFERENCES tb_tenant(tenant_id) ON DELETE CASCADE,
    dept_code       VARCHAR(50) NOT NULL,
    dept_name       VARCHAR(200) NOT NULL,
    depth           INT DEFAULT 0,
    sort_order      INT DEFAULT 0,
    is_active       BOOLEAN DEFAULT true,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_dept_tenant_code UNIQUE (tenant_id, dept_code),
    CONSTRAINT chk_dept_depth CHECK (depth >= 0 AND depth <= 10)
);

COMMENT ON TABLE tb_department IS '조직(부서) 트리 구조';
COMMENT ON COLUMN tb_department.parent_dept_id IS '상위 부서 ID (NULL이면 최상위)';
COMMENT ON COLUMN tb_department.tenant_id IS '소속 테넌트 (부서는 반드시 테넌트에 소속)';
COMMENT ON COLUMN tb_department.dept_code IS '부서 코드 (SSO/외부 시스템 매핑용, 테넌트 내 유니크)';
COMMENT ON COLUMN tb_department.depth IS '트리 깊이 (0=최상위, 최대 10)';

CREATE INDEX idx_dept_parent ON tb_department(parent_dept_id);
CREATE INDEX idx_dept_tenant ON tb_department(tenant_id);
CREATE INDEX idx_dept_active ON tb_department(is_active);
CREATE INDEX idx_dept_sort ON tb_department(depth, sort_order);
```

**컬럼 명세**:

| # | 컬럼 | 타입 | NULL | 설명 |
|---|------|------|:---:|------|
| 1 | dept_id | BIGSERIAL PK | N | 부서 ID |
| 2 | parent_dept_id | BIGINT FK(self) | Y | 상위 부서 (NULL=최상위 본부) |
| 3 | tenant_id | BIGINT FK | N | 소속 테넌트 |
| 4 | dept_code | VARCHAR(50) | N | 부서 코드 (테넌트 내 유니크, SSO 매핑용) |
| 5 | dept_name | VARCHAR(200) | N | 부서명 |
| 6 | depth | INT | Y | 트리 깊이 (0=최상위, 최대 10) |
| 7 | sort_order | INT | Y | 동일 depth 내 정렬 순서 |
| 8 | is_active | BOOLEAN | Y | 활성 여부 |
| 9 | created_at | TIMESTAMPTZ | Y | 생성일시 |
| 10 | updated_at | TIMESTAMPTZ | Y | 수정일시 |

### 3.3 tb_role (현행 DDL — scope_level 포함)

```sql
CREATE TABLE tb_role (
    role_id         BIGSERIAL PRIMARY KEY,
    role_code       VARCHAR(50) UNIQUE NOT NULL,    -- GLOBAL, TENANT, DEPT, USER
    role_name       VARCHAR(100) NOT NULL,
    description     TEXT,
    landing_page    VARCHAR(200) NOT NULL DEFAULT '/chat',
    is_system       BOOLEAN DEFAULT false,          -- 시스템 기본 역할 (삭제 불가)
    sort_order      INT DEFAULT 0,
    scope_level     INT NOT NULL DEFAULT 3,         -- ★ 0=전체, 1=테넌트, 2=부서, 3=본인
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE  tb_role IS '역할 정의';
COMMENT ON COLUMN tb_role.role_code IS '역할 코드 (GLOBAL, TENANT, DEPT, USER)';
COMMENT ON COLUMN tb_role.scope_level IS '데이터 범위 레벨: 0=전체, 1=테넌트, 2=부서, 3=본인';
COMMENT ON COLUMN tb_role.sort_order IS '역할 계층 순서 (낮을수록 상위)';
COMMENT ON COLUMN tb_role.is_system IS '시스템 기본 역할 (삭제 불가)';
```

**컬럼 명세**:

| # | 컬럼 | 타입 | NULL | 설명 |
|---|------|------|:---:|------|
| 1 | role_id | BIGSERIAL PK | N | 역할 ID |
| 2 | role_code | VARCHAR(50) UK | N | 역할 코드 |
| 3 | role_name | VARCHAR(100) | N | 역할 표시명 |
| 4 | description | TEXT | Y | 역할 설명 |
| 5 | landing_page | VARCHAR(200) | N | 로그인 후 랜딩 페이지 |
| 6 | is_system | BOOLEAN | Y | 시스템 기본 역할 (삭제 불가) |
| 7 | sort_order | INT | Y | 역할 계층 순서 (낮을수록 상위) |
| 8 | scope_level | INT | N | 데이터 범위 레벨 (0~3) ★ |
| 9 | created_at | TIMESTAMPTZ | Y | 생성일시 |
| 10 | updated_at | TIMESTAMPTZ | Y | 수정일시 |

### 3.4 tb_user (현행 DDL — dept_id + SSO 컬럼 포함)

```sql
CREATE TABLE tb_user (
    user_id          BIGSERIAL PRIMARY KEY,
    login_id         VARCHAR(100) UNIQUE NOT NULL,
    email            VARCHAR(255) UNIQUE NOT NULL,
    password_hash    VARCHAR(255) NOT NULL,          -- bcrypt 해시
    display_name     VARCHAR(100),
    tenant_id        BIGINT REFERENCES tb_tenant(tenant_id) ON DELETE SET NULL,
    role_id          BIGINT NOT NULL REFERENCES tb_role(role_id) ON DELETE RESTRICT,
    dept_id          BIGINT REFERENCES tb_department(dept_id) ON DELETE SET NULL,  -- ★
    is_active        BOOLEAN DEFAULT true,
    is_superuser     BOOLEAN DEFAULT false,          -- RBAC 비상 안전장치
    sso_provider     VARCHAR(50),                    -- ★
    sso_external_id  VARCHAR(100),                   -- ★
    last_login_at    TIMESTAMPTZ,
    login_fail_count INT DEFAULT 0,
    locked_until     TIMESTAMPTZ,
    created_at       TIMESTAMPTZ DEFAULT NOW(),
    updated_at       TIMESTAMPTZ DEFAULT NOW()
);

COMMENT ON TABLE  tb_user IS '사용자';
COMMENT ON COLUMN tb_user.dept_id IS '소속 부서 ID (FK → tb_department)';
COMMENT ON COLUMN tb_user.sso_provider IS 'SSO 제공자 식별자 (NULL이면 자체 계정)';
COMMENT ON COLUMN tb_user.sso_external_id IS 'SSO 외부 시스템 사용자 ID (사번 등)';
COMMENT ON COLUMN tb_user.is_superuser IS 'RBAC 비상 안전장치 (최소 1명 유지)';

CREATE INDEX idx_user_tenant ON tb_user(tenant_id);
CREATE INDEX idx_user_role   ON tb_user(role_id);
CREATE INDEX idx_user_active ON tb_user(is_active);
CREATE INDEX idx_user_dept   ON tb_user(dept_id);
CREATE UNIQUE INDEX idx_user_sso ON tb_user(sso_provider, sso_external_id)
    WHERE sso_provider IS NOT NULL;
```

**컬럼 명세**:

| # | 컬럼 | 타입 | NULL | 설명 |
|---|------|------|:---:|------|
| 1 | user_id | BIGSERIAL PK | N | 사용자 ID |
| 2 | login_id | VARCHAR(100) UK | N | 로그인 ID |
| 3 | email | VARCHAR(255) UK | N | 이메일 |
| 4 | password_hash | VARCHAR(255) | N | bcrypt 해시 |
| 5 | display_name | VARCHAR(100) | Y | 표시 이름 |
| 6 | tenant_id | BIGINT FK | Y | 소속 테넌트 ID |
| 7 | role_id | BIGINT FK | N | 역할 ID |
| 8 | dept_id | BIGINT FK | Y | 소속 부서 ID ★ |
| 9 | is_active | BOOLEAN | Y | 활성 상태 |
| 10 | is_superuser | BOOLEAN | Y | RBAC 비상 안전장치 |
| 11 | sso_provider | VARCHAR(50) | Y | SSO 제공자 식별자 ★ |
| 12 | sso_external_id | VARCHAR(100) | Y | SSO 외부 사용자 ID ★ |
| 13 | last_login_at | TIMESTAMPTZ | Y | 마지막 로그인 시각 |
| 14 | login_fail_count | INT | Y | 로그인 실패 횟수 |
| 15 | locked_until | TIMESTAMPTZ | Y | 계정 잠금 해제 시각 |
| 16 | created_at | TIMESTAMPTZ | Y | 생성일시 |
| 17 | updated_at | TIMESTAMPTZ | Y | 수정일시 |

> ★ = v2.0에서 추가된 컬럼
> `(sso_provider, sso_external_id)` partial unique index: SSO 사용자의 중복 등록 방지

### 3.5 역할-테넌트-부서 조합 검증 규칙

```
GLOBAL       → 시스템 테넌트, dept_id = NULL
TENANT       → 일반 테넌트 필수, dept_id = NULL 허용 (테넌트 전체 관리)
DEPT         → 일반 테넌트 필수, dept_id 필수
USER         → 일반 테넌트 필수, dept_id 필수

금지 조합:
  × GLOBAL + dept_id 설정  → dept_id를 NULL로 자동 보정
  × DEPT + dept_id 없음    → BAD_REQUEST 에러
  × USER + dept_id 없음    → BAD_REQUEST 에러 (또는 SSO 시 자동 할당)
```

---

## 4. 조직 트리 예시

### 4.1 조직도 구조

```
DEMO 테넌트
├── 경영본부 (dept_id=1, depth=0)
│     ├── 인사팀 (dept_id=3, depth=1)
│     └── 재무팀 (dept_id=4, depth=1)
└── 개발본부 (dept_id=2, depth=0)
      ├── 개발1팀 (dept_id=5, depth=1)
      │     ├── 프론트파트 (dept_id=7, depth=2)
      │     └── 백엔드파트 (dept_id=8, depth=2)
      └── 개발2팀 (dept_id=6, depth=1)
```

### 4.2 사용자 배치와 조회 범위

| 이름 | role_code | scope_level | dept_id | 조회 범위 |
|------|-----------|-------------|---------|----------|
| 관리자 | GLOBAL | 0 | NULL | 전체 |
| 테넌트장 | TENANT | 1 | NULL | DEMO 테넌트 전체 |
| 개발본부장 | DEPT | 2 | 2 (개발본부) | 개발본부 + 개발1팀 + 개발2팀 + 프론트파트 + 백엔드파트 |
| 개발1팀장 | DEPT | 2 | 5 (개발1팀) | 개발1팀 + 프론트파트 + 백엔드파트 |
| 홍길동 | USER | 3 | 7 (프론트파트) | 본인만 |

> 본부장과 팀장 모두 `DEPT (scope_level=2)`. 차이는 `dept_id`의 트리 위치.

### 4.3 예시 데이터 INSERT

```sql
-- 최상위 본부
INSERT INTO tb_department (tenant_id, dept_code, dept_name, parent_dept_id, depth, sort_order) VALUES
((SELECT tenant_id FROM tb_tenant WHERE tenant_code='DEMO'), 'HQ_MGMT', '경영본부', NULL, 0, 1),
((SELECT tenant_id FROM tb_tenant WHERE tenant_code='DEMO'), 'HQ_DEV',  '개발본부', NULL, 0, 2);

-- 경영본부 하위
INSERT INTO tb_department (tenant_id, dept_code, dept_name, parent_dept_id, depth, sort_order) VALUES
((SELECT tenant_id FROM tb_tenant WHERE tenant_code='DEMO'), 'HR_01',  '인사팀',
    (SELECT dept_id FROM tb_department WHERE dept_code='HQ_MGMT'), 1, 1),
((SELECT tenant_id FROM tb_tenant WHERE tenant_code='DEMO'), 'FIN_01', '재무팀',
    (SELECT dept_id FROM tb_department WHERE dept_code='HQ_MGMT'), 1, 2);

-- 개발본부 하위
INSERT INTO tb_department (tenant_id, dept_code, dept_name, parent_dept_id, depth, sort_order) VALUES
((SELECT tenant_id FROM tb_tenant WHERE tenant_code='DEMO'), 'DEV_01', '개발1팀',
    (SELECT dept_id FROM tb_department WHERE dept_code='HQ_DEV'), 1, 1),
((SELECT tenant_id FROM tb_tenant WHERE tenant_code='DEMO'), 'DEV_02', '개발2팀',
    (SELECT dept_id FROM tb_department WHERE dept_code='HQ_DEV'), 1, 2);
```

---

## 5. Scope 필터 구현

### 5.1 공통 필터 함수

기존 13곳에 분산된 role_code 하드코딩을 공통 유틸로 통합한다.

```python
# app/core/security/scope_filter.py

SCOPE_GLOBAL = 0
SCOPE_TENANT = 1
SCOPE_DEPT   = 2
SCOPE_USER   = 3

def get_dept_scope_ids(dept_id: int) -> list:
    """해당 부서 + 모든 하위 부서 ID 반환 (recursive CTE)"""
    with db_manager.get_cursor() as cur:
        cur.execute("""
            WITH RECURSIVE dept_tree AS (
                SELECT dept_id FROM tb_department WHERE dept_id = %s
                UNION ALL
                SELECT d.dept_id FROM tb_department d
                JOIN dept_tree dt ON d.parent_dept_id = dt.dept_id
                WHERE d.is_active = true
            )
            SELECT dept_id FROM dept_tree
        """, (dept_id,))
        return [row["dept_id"] for row in cur.fetchall()]


def apply_scope_filter(user, conditions: list, params: list,
                       tenant_col="tenant_id", dept_col="dept_id", user_col="user_id"):
    """scope_level 기반 공통 데이터 필터

    Args:
        user: UserContext (scope_level, tenant_id, dept_id, user_id 보유)
        conditions: WHERE 조건 리스트 (append됨)
        params: SQL 파라미터 리스트 (extend됨)
        tenant_col/dept_col/user_col: 대상 테이블의 컬럼명
    """
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
```

### 5.2 기존 하드코딩 교체 결과

> Phase 3에서 11곳 교체 완료. `is_global`/`is_user_scope` 프로퍼티 기반 파일은 이미 scope_level 연동되어 변경 불필요.

| 파일 | 변경 내용 | 상태 |
|------|----------|:---:|
| `routes/agent.py:34` | `role_code == "GLOBAL"` → `is_global` 프로퍼티 | **완료** |
| `routes/search.py:30` | `role_code == "GLOBAL"` → `is_global` 프로퍼티 | **완료** |
| `routes/dashboard.py:22-29` | role_code TENANT/USER 분기 → scope_level + SCOPE_TENANT/SCOPE_USER 상수 | **완료** |
| `routes/history.py:25-32` | role_code TENANT/USER 분기 → scope_level + SCOPE_TENANT/SCOPE_USER 상수 | **완료** |
| `routes/history.py:123` | `role_code == "USER"` → `is_user_scope` 프로퍼티 | **완료** |
| `routes/history.py:147` | `role_code == "USER"` → `is_user_scope` 프로퍼티 | **완료** |
| `services/user_service.py:84` | `role_code == "TENANT"` → `is_user_scope` + 테넌트 검증 | **완료** |
| `services/user_service.py:96` | role_code TENANT/else 분기 → `apply_scope_filter()` | **완료** |
| `services/user_service.py:181` | `role_code == "TENANT"` → `not is_global` | **완료** |
| `services/user_service.py:467` | `role_code == "TENANT"` → `not is_global` | **완료** |
| `services/user_service.py:486` | `role_code == "TENANT"` → `not is_global` | **완료** |
| `services/document_service.py` (4곳) | 이미 `is_global` 사용 | 변경 불필요 |
| `routes/settings.py` (8곳) | 이미 `is_global` 사용 | 변경 불필요 |

### 5.3 UserContext 변경

```python
# app/models/auth.py
class UserContext(BaseModel):
    user_id: int
    login_id: str
    display_name: Optional[str] = None
    tenant_id: Optional[int] = None
    dept_id: Optional[int] = None          # ★ 추가
    is_superuser: bool = False
    role_code: str = "USER"
    scope_level: int = 3                    # ★ 추가

    @property
    def is_global(self) -> bool:
        return self.is_superuser or self.scope_level == 0

    @property
    def is_tenant_scope(self) -> bool:
        return self.scope_level == 1

    @property
    def is_dept_scope(self) -> bool:        # ★ 추가
        return self.scope_level == 2

    @property
    def is_user_scope(self) -> bool:
        return self.scope_level == 3
```

### 5.4 JWT 토큰에 scope_level, dept_id 추가

```python
# auth_service.py — create_session()
token_data = {
    "sub": str(user_id),
    "login_id": user_info["login_id"],
    "display_name": user_info["display_name"],
    "tenant_id": user_info["tenant_id"],
    "dept_id": user_info["dept_id"],            # ★ 추가
    "role_code": user_info["role_code"],
    "scope_level": user_info["scope_level"],    # ★ 추가
    "is_superuser": user_info["is_superuser"],
}
```

---

## 6. SSO 연동

### 6.1 방식: Token Exchange + Frontend Redirect (RS256)

메인 시스템이 **RS256 개인키**로 서명한 JWT를 URL 파라미터로 전달하고,
Vue 프론트엔드가 중계하여 백엔드에 토큰 교환을 요청한다.
MUREUM은 **RS256 공개키**로만 검증하므로, 공개키 유출 시에도 토큰 위조가 불가능하다.

```
RS256 (비대칭키) 역할 분리:
  메인 시스템: 개인키(private_key.pem)로 서명 → 토큰 생성 가능
  MUREUM:     공개키(public_key.pem)로 검증  → 토큰 검증만 가능 (생성 불가)
```

#### 전체 시퀀스

```
[메인 시스템]              [Vue 프론트엔드]             [MUREUM 백엔드]
     │                        │                           │
     │ 1. 사용자 클릭           │                           │
     │    "AI 챗봇"            │                           │
     │ 2. RS256 개인키로        │                           │
     │    SSO JWT 서명          │                           │
     │                        │                           │
     │ 3. 브라우저 리다이렉트    │                           │
     │    /sso?token=eyJxxx ─▶│                           │
     │                        │ 4. URL에서 token 추출       │
     │                        │ 5. POST /api/v1/auth/sso ─▶│
     │                        │    {sso_token: "eyJ..."}   │
     │                        │                            │ 6. RS256 공개키로 서명 검증
     │                        │                            │ 7. issuer, exp 검증
     │                        │                            │ 8. 테넌트 조회
     │                        │                            │ 9. 부서 조회/생성 (JIT)
     │                        │                            │ 10. 사용자 조회/생성 (JIT)
     │                        │                            │ 11. 변경 감지 시 UPDATE
     │                        │                            │ 12. MUREUM JWT 발급 (HS256)
     │                        │ ◀── 13. TokenResponse ─────│
     │                        │    {access_token,           │
     │                        │     refresh_token, user}    │
     │                        │                            │
     │                        │ 14. localStorage 저장       │
     │                        │ 15. Vuex store 업데이트      │
     │                        │ 16. router.push(landing)   │
```

> **왜 Frontend Redirect인가?**
> 기존 MUREUM은 localStorage + Vuex 기반 인증 체계를 사용한다.
> 쿠키 방식으로 변경하면 기존 인증 체계 전체를 수정해야 하므로,
> 기존 login 플로우와 동일한 패턴(API 호출 → localStorage 저장)을 유지한다.

> **왜 RS256인가?**
> HS256(대칭키)은 MUREUM도 같은 키를 보유하므로 위조 토큰 생성 가능.
> RS256(비대칭키)은 MUREUM이 공개키만 보유하므로 검증만 가능, 위조 불가.
> 향후 여러 외부 시스템 연동 시에도 공개키만 추가하면 됨 (1:N 확장 용이).

### 6.2 메인 시스템이 보내는 SSO 토큰

```json
{
  "sub": "EMP2024001",
  "name": "홍길동",
  "email": "hong@company.com",
  "tenant_code": "TENANT_A",
  "dept_code": "DEV_01",
  "dept_name": "개발1팀",
  "position": "팀장",
  "iat": 1740000000,
  "exp": 1740000300,
  "iss": "hr-system"
}
```

| 필드 | 용도 | 필수 |
|------|------|:---:|
| sub | 사번 (사용자 고유 식별자) | O |
| name | 이름 | O |
| email | 이메일 | △ |
| tenant_code | 테넌트 코드 | O |
| dept_code | 부서 코드 | O |
| dept_name | 부서명 | O |
| position | 직급/직책 | △ |
| iss | 발급 시스템 식별자 | O |
| exp | 만료 시간 (짧게 — 5분 이내) | O |

### 6.3 사용자 자동 생성 (Just-In-Time Provisioning)

SSO 로그인 시 MUREUM에 사용자가 없으면 **즉시 생성**한다.

```python
def find_or_create_sso_user(self, sso_data: dict, request_id: str) -> dict:
    """SSO 사용자 조회/생성/업데이트"""

    # 1. 기존 사용자 조회 (sso_provider + sso_external_id)
    user = self._find_by_sso_id(sso_data["iss"], sso_data["sub"])

    if user:
        # 2a. 있음 → 변경 감지 후 업데이트 (부서 이동, 직급 변경 등)
        changes = self._detect_changes(user, sso_data)
        if changes:
            self._update_sso_user(user["user_id"], changes)
        return self.get_user_with_permissions(user["user_id"], request_id)

    # 2b. 없음 → 자동 생성
    tenant_id = self._resolve_tenant(sso_data["tenant_code"])
    dept_id = self._resolve_or_create_dept(tenant_id, sso_data)
    role_id = self._resolve_role(sso_data.get("position"))

    new_user = self._create_sso_user(
        sso_provider=sso_data["iss"],
        sso_external_id=sso_data["sub"],
        login_id=sso_data["sub"],           # 사번을 login_id로 사용
        display_name=sso_data["name"],
        email=sso_data.get("email"),
        tenant_id=tenant_id,
        dept_id=dept_id,
        role_id=role_id,
    )
    # 기본 메뉴 권한 자동 할당
    self._assign_default_menus(new_user["user_id"], role_id)

    return self.get_user_with_permissions(new_user["user_id"], request_id)
```

### 6.4 부서 자동 생성

SSO 토큰의 dept_code가 MUREUM에 없으면 **자동 생성**한다.

```python
def _resolve_or_create_dept(self, tenant_id: int, sso_data: dict) -> int:
    """부서 조회 — 없으면 생성"""
    dept_code = sso_data["dept_code"]
    dept_name = sso_data["dept_name"]

    with db_manager.get_cursor() as cur:
        cur.execute(
            "SELECT dept_id FROM tb_department WHERE tenant_id = %s AND dept_code = %s",
            (tenant_id, dept_code)
        )
        row = cur.fetchone()

    if row:
        return row["dept_id"]

    # 없으면 최상위(depth=0) 부서로 생성
    # 부서 계층은 배치 동기화 또는 Admin UI에서 정리
    with db_manager.get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO tb_department (tenant_id, dept_code, dept_name, depth, sort_order) "
            "VALUES (%s, %s, %s, 0, 0) RETURNING dept_id",
            (tenant_id, dept_code, dept_name)
        )
        return cur.fetchone()["dept_id"]
```

> 자동 생성된 부서는 `depth=0` (최상위)로 생성된다.
> 부서 계층(parent_dept_id, depth)은 **배치 동기화** 또는 **Admin UI**에서 정리한다.

### 6.5 role 자동 매핑

메인 시스템의 position(직급)을 MUREUM role_code로 변환한다.
기존 `tb_code` 테이블을 활용하여 신규 테이블 없이 처리한다.

```sql
-- 기존 코드 관리 테이블(tb_code) 활용
-- 카테고리 행 (code_group=code_value, parent=NULL → 그룹 헤더)
INSERT INTO tb_code (code_group, code_value, code_name, description, sort_order, is_active, is_system)
VALUES ('SSO_ROLE_MAP', 'SSO_ROLE_MAP', 'SSO 직급-역할 매핑',
        'SSO position → MUREUM role_code 매핑', 0, true, true);

-- 직급별 매핑 (code_value=직급, code_name=role_code, parent=SSO_ROLE_MAP)
INSERT INTO tb_code (code_group, code_value, code_name, parent, sort_order, is_active, is_system) VALUES
('SSO_ROLE_MAP', '총괄',       'GLOBAL', 'SSO_ROLE_MAP', 1, true, true),
('SSO_ROLE_MAP', '테넌트관리자', 'TENANT', 'SSO_ROLE_MAP', 2, true, true),
('SSO_ROLE_MAP', '본부장',     'DEPT',   'SSO_ROLE_MAP', 3, true, true),
('SSO_ROLE_MAP', '부서장',     'DEPT',   'SSO_ROLE_MAP', 4, true, true),
('SSO_ROLE_MAP', '팀장',       'DEPT',   'SSO_ROLE_MAP', 5, true, true),
('SSO_ROLE_MAP', '파트장',     'DEPT',   'SSO_ROLE_MAP', 6, true, true),
('SSO_ROLE_MAP', 'DEFAULT',    'USER',   'SSO_ROLE_MAP', 99, true, true);
```

> 직급 추가 시 `tb_code`에 행만 INSERT하면 됨 (코드 변경 불필요).
> Admin UI의 코드 관리 화면(CodesView.vue)에서도 추가 가능.

```python
def _resolve_role(self, position: str) -> int:
    """메인 시스템 직급 → MUREUM role_id 매핑 (tb_code 활용)"""
    role_code = "USER"  # 기본값
    if position:
        with db_manager.get_cursor() as cur:
            cur.execute(
                "SELECT code_name FROM tb_code "
                "WHERE code_group = 'SSO_ROLE_MAP' AND code_value = %s "
                "AND is_active = true",
                (position,)
            )
            row = cur.fetchone()
            if row:
                role_code = row["code_name"]

    with db_manager.get_cursor() as cur:
        cur.execute("SELECT role_id FROM tb_role WHERE role_code = %s", (role_code,))
        return cur.fetchone()["role_id"]
```

### 6.6 SSO 설정

```bash
# .env
SSO_ENABLED=false                              # SSO 활성화 여부 (기본: 비활성)
SSO_PUBLIC_KEY_PATH=./keys/sso_public.pem      # RS256 공개키 경로
SSO_ALGORITHM=RS256                            # 서명 알고리즘 (RS256 고정)
SSO_ALLOWED_ISSUERS=hr-system,erp-system       # 허용 발급자 (콤마 구분)
SSO_TOKEN_MAX_AGE=300                          # SSO 토큰 최대 유효시간 (초, 기본 5분)
SSO_DEFAULT_ROLE=USER                          # 매핑 실패 시 기본 역할
SSO_AUTO_CREATE_DEPT=true                      # 부서 자동 생성 여부
```

> **키 관리 원칙**:
> - `keys/sso_public.pem` — MUREUM이 보유 (검증 전용, 유출되어도 안전)
> - `keys/sso_private.pem` — 메인 시스템이 보유 (서명 전용, MUREUM에 저장 금지)
> - `keys/` 디렉토리는 `.gitignore`에 등록

```python
# app/config.py — Settings 클래스에 추가
class Settings(BaseSettings):
    # ... 기존 설정 ...

    # SSO
    sso_enabled: bool = False
    sso_public_key_path: str = "./keys/sso_public.pem"
    sso_algorithm: str = "RS256"
    sso_allowed_issuers: str = ""
    sso_token_max_age: int = 300
    sso_default_role: str = "USER"
    sso_auto_create_dept: bool = True
```

### 6.7 SSO API

| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|:---:|
| POST | `/api/v1/auth/sso` | SSO 토큰 교환 → MUREUM JWT 발급 | No (공개) |

**Request**:
```json
{
  "sso_token": "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJFTVAyMDI0MDAxIi..."
}
```

**Response** (기존 login API와 **동일한 TokenResponse**):
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "eyJ...",
    "token_type": "Bearer",
    "expires_in": 1800,
    "user": {
      "user_id": 10,
      "login_id": "EMP2024001",
      "display_name": "홍길동",
      "role_code": "DEPT",
      "role_name": "조직 관리자",
      "landing_page": "/admin/chat",
      "menus": [...]
    }
  }
}
```

**에러 응답**:

| 상황 | HTTP | error.code | error.message |
|------|:---:|-----------|---------------|
| SSO 비활성 | 403 | FORBIDDEN | SSO 인증이 비활성화되어 있습니다 |
| 토큰 서명 불일치 | 401 | UNAUTHORIZED | SSO 토큰 검증에 실패했습니다 |
| 토큰 만료 | 401 | UNAUTHORIZED | SSO 토큰이 만료되었습니다 |
| issuer 미허용 | 401 | UNAUTHORIZED | 허용되지 않은 SSO 발급자입니다 |
| 테넌트 미존재 | 400 | BAD_REQUEST | 테넌트를 찾을 수 없습니다: {tenant_code} |
| 사용자 비활성 | 401 | UNAUTHORIZED | 비활성화된 계정입니다 |

### 6.8 RS256 토큰 검증 모듈

```python
# app/core/security/sso.py

from jose import jwt, JWTError
from app.config import settings

_public_key = None  # 앱 시작 시 1회 로드

def load_sso_public_key():
    """공개키 로드 (앱 시작 시 호출)"""
    global _public_key
    if settings.sso_enabled and os.path.exists(settings.sso_public_key_path):
        with open(settings.sso_public_key_path, "r") as f:
            _public_key = f.read()

def verify_sso_token(sso_token: str) -> SSOTokenPayload:
    """RS256 SSO 토큰 검증"""
    if not settings.sso_enabled:
        raise APIException(ErrorCode.FORBIDDEN, "SSO 인증이 비활성화되어 있습니다")

    if not _public_key:
        raise APIException(ErrorCode.INTERNAL_ERROR, "SSO 공개키가 로드되지 않았습니다")

    allowed_issuers = [s.strip() for s in settings.sso_allowed_issuers.split(",") if s.strip()]

    try:
        payload = jwt.decode(
            sso_token,
            _public_key,
            algorithms=[settings.sso_algorithm],
            options={"require_exp": True, "require_sub": True}
        )
    except jwt.ExpiredSignatureError:
        raise APIException(ErrorCode.UNAUTHORIZED, "SSO 토큰이 만료되었습니다")
    except JWTError:
        raise APIException(ErrorCode.UNAUTHORIZED, "SSO 토큰 검증에 실패했습니다")

    # issuer 검증
    if allowed_issuers and payload.get("iss") not in allowed_issuers:
        raise APIException(ErrorCode.UNAUTHORIZED, "허용되지 않은 SSO 발급자입니다")

    return SSOTokenPayload(**payload)
```

### 6.9 Pydantic 모델 추가

```python
# app/models/auth.py — 추가

class SSOLoginRequest(BaseModel):
    """SSO 토큰 교환 요청"""
    sso_token: str

class SSOTokenPayload(BaseModel):
    """메인 시스템이 발급한 SSO JWT의 payload"""
    sub: str                          # 사번 (사용자 고유 식별자)
    name: str                         # 이름
    email: Optional[str] = None       # 이메일
    tenant_code: str                  # 테넌트 코드
    dept_code: str                    # 부서 코드
    dept_name: str                    # 부서명
    position: Optional[str] = None    # 직급/직책
    iss: str                          # 발급 시스템 식별자
    exp: int                          # 만료 시간 (Unix timestamp)
    iat: Optional[int] = None         # 발급 시간
```

### 6.10 변경 감지 항목

SSO 로그인 시 기존 사용자의 정보 변경을 자동 감지하여 업데이트한다.

| 항목 | SSO 필드 | tb_user 컬럼 | 변경 시 동작 |
|------|----------|-------------|------------|
| 이름 | name | display_name | UPDATE |
| 이메일 | email | email | UPDATE |
| 부서 | dept_code | dept_id | 부서 조회/생성 후 UPDATE |
| 직급 | position | role_id | role 매핑 후 UPDATE |

---

## 7. 배치 동기화 (보조)

SSO JIT 방식의 보조 수단으로 **배치 동기화**를 병행한다.

### 7.1 용도

| 용도 | JIT으로 불가능한 이유 |
|------|---------------------|
| 퇴직자 비활성화 | 퇴직자는 SSO 로그인하지 않으므로 JIT 트리거 안됨 |
| 대량 부서 개편 | 부서 계층(parent_dept_id, depth) 일괄 정리 |
| 초기 데이터 로딩 | 시스템 최초 구축 시 전체 사용자/부서 일괄 등록 |

### 7.2 동기화 범위

```
메인 시스템 API → MUREUM 배치 스크립트

1. 부서 동기화: 전체 조직도 → tb_department UPSERT (계층 포함)
2. 사용자 동기화: 재직자 목록 → tb_user UPSERT
3. 퇴직자 처리: 메인 시스템에 없는 SSO 사용자 → is_active = false
```

---

## 8. 부서 관리 API

### 8.1 엔드포인트

| Method | Endpoint | 설명 | 권한 |
|--------|----------|------|------|
| GET | `/api/admin/v1/departments` | 부서 트리 조회 | DEPT_MGMT:read |
| POST | `/api/admin/v1/departments` | 부서 추가 | DEPT_MGMT:create |
| GET | `/api/admin/v1/departments/{dept_id}` | 부서 상세 | DEPT_MGMT:read |
| PUT | `/api/admin/v1/departments/{dept_id}` | 부서 수정 | DEPT_MGMT:update |
| DELETE | `/api/admin/v1/departments/{dept_id}` | 부서 삭제 | DEPT_MGMT:delete |
| PUT | `/api/admin/v1/departments/reorder` | 순서 변경 | DEPT_MGMT:update |

> tb_menu에 `DEPT_MGMT` 메뉴 추가 필요

### 8.2 부서 트리 조회 응답

```json
{
  "success": true,
  "data": {
    "items": [
      {
        "dept_id": 1,
        "dept_code": "HQ_MGMT",
        "dept_name": "경영본부",
        "parent_dept_id": null,
        "depth": 0,
        "sort_order": 1,
        "user_count": 2,
        "children": [
          {
            "dept_id": 3,
            "dept_code": "HR_01",
            "dept_name": "인사팀",
            "parent_dept_id": 1,
            "depth": 1,
            "sort_order": 1,
            "user_count": 5,
            "children": []
          }
        ]
      }
    ],
    "total": 6
  }
}
```

---

## 9. 파일 구조 (추가/변경)

### 9.1 백엔드 — Phase 1~3 구현 완료

```
app/core/security/
  └── scope_filter.py          # ★ 신규: 공통 scope 필터 (apply_scope_filter, get_dept_scope_ids)  ✅

app/api/routes/
  ├── agent.py                 # 변경: _extract_tenant_id() → is_global 프로퍼티  ✅
  ├── search.py                # 변경: _extract_tenant_id() → is_global 프로퍼티  ✅
  ├── dashboard.py             # 변경: _apply_scope_filter() → scope_level 기반  ✅
  ├── history.py               # 변경: _apply_scope_filter() + 접근 제어 → scope_level 기반  ✅
  ├── departments.py           # ★ 신규: 부서 CRUD (트리 조회/생성/수정/삭제/순서변경)  ✅
  └── users.py                 # 변경: 부서 드롭다운 옵션 추가  ✅

app/api/services/
  ├── department_service.py    # ★ 신규: 부서 서비스 (트리 구축, recursive CTE)  ✅
  ├── user_service.py          # 변경: scope 검증 5곳 → scope_level 기반, apply_scope_filter() 사용  ✅
  └── role_service.py          # 변경: CRUD 쿼리에 scope_level 포함  ✅

app/models/
  ├── auth.py                  # 변경: UserContext에 dept_id, scope_level, is_dept_scope, is_user_scope 추가  ✅
  ├── user.py                  # 변경: RoleCreate/Update/Response에 scope_level 추가  ✅
  └── department.py            # ★ 신규: DeptCreate/Update/TreeResponse  ✅
```

### 9.2 백엔드 — Phase 4 (SSO) 구현 예정

```
app/config.py                          # 변경: SSO 설정 7개 추가 (sso_enabled, sso_public_key_path 등)

app/core/security/
  └── sso.py                           # ★ 신규: RS256 공개키 로드, SSO 토큰 검증 (verify_sso_token)

app/api/routes/
  └── auth.py                          # 변경: POST /sso 엔드포인트 추가

app/api/services/
  └── auth_service.py                  # 변경: SSO 메서드 4개 추가
                                       #   sso_authenticate()          — SSO 인증 진입점
                                       #   _find_or_create_sso_user()  — JIT 사용자 생성/업데이트
                                       #   _resolve_or_create_dept()   — JIT 부서 생성
                                       #   _resolve_sso_role()         — 직급→역할 매핑

app/models/
  └── auth.py                          # 변경: SSOLoginRequest, SSOTokenPayload 모델 추가

app/main.py                            # 변경: lifespan에 load_sso_public_key() 호출 추가

keys/                                  # ★ 신규 디렉토리 (.gitignore 등록)
  ├── sso_public.pem                   # RS256 공개키 (MUREUM 보유)
  └── sso_private.pem                  # RS256 개인키 (테스트용, 운영 시 메인 시스템만 보유)

scripts/
  └── generate_sso_keys.py             # ★ 신규: RS256 키 쌍 생성 도구
```

### 9.3 프론트엔드 — Phase 1~3 구현 완료

```
frontend/src/
  ├── api/departments.js       # ★ 신규: 부서 API (CRUD + reorder)  ✅
  └── views/admin/
      ├── DepartmentsView.vue  # ★ 신규: 부서 트리 관리 화면 (el-table 트리 + CRUD 다이얼로그)  ✅
      ├── RolesView.vue        # 변경: Scope 컬럼/드롭다운 추가 (0=GLOBAL~3=USER)  ✅
      └── UsersView.vue        # 변경: 부서 선택 드롭다운 추가  ✅
```

### 9.4 프론트엔드 — Phase 4 (SSO) 구현 예정

```
frontend/src/
  ├── api/auth.js              # 변경: ssoLogin(ssoToken) 메서드 추가
  ├── store/modules/auth.js    # 변경: ssoLogin 액션 추가 (기존 login과 동일 패턴)
  ├── router/index.js          # 변경: /sso 경로 추가 (meta: { public: true })
  └── views/
      └── SSOCallbackView.vue  # ★ 신규: SSO 콜백 화면
                               #   URL에서 token 추출 → POST /api/v1/auth/sso
                               #   → 토큰 저장 → landing_page 이동
                               #   에러 시 /login?error=sso_failed 리다이렉트
```

### 9.5 테스트

```
tests/
  ├── test_04_roles.py         # 변경: TestRoleScopeLevel 클래스 추가 (7개 테스트)  ✅
  ├── test_11_departments.py   # ★ 신규: 부서 CRUD 통합 테스트  ✅
  └── test_12_sso.py           # ★ 신규: SSO 통합 테스트 (8개)
                               #   test_sso_login_new_user       — 신규 사용자 JIT 생성
                               #   test_sso_login_existing_user  — 기존 사용자 + 변경 감지
                               #   test_sso_invalid_token        — 잘못된 토큰 → 401
                               #   test_sso_expired_token        — 만료 토큰 → 401
                               #   test_sso_invalid_issuer       — 미허용 issuer → 401
                               #   test_sso_dept_auto_create     — 부서 자동 생성
                               #   test_sso_role_mapping         — 직급→역할 매핑
                               #   test_sso_disabled             — SSO 비활성 시 403
```

> Phase 1~3 테스트: 86개 통과, 프론트엔드 빌드 성공 확인 (2026-02-24)

---

## 10. 구현 순서

### Phase 1~3 (조직/부서/Scope — 완료)

| 순서 | 작업 | 의존성 | 상태 |
|:---:|------|--------|:---:|
| 1 | DDL 실행 (tb_department 생성, tb_role/tb_user 변경, 컬럼 순서 정리) | 없음 | **완료** |
| 2 | scope_filter.py 공통 유틸 구현 | 1 | **완료** |
| 3 | UserContext, TokenPayload에 dept_id/scope_level 추가 | 1 | **완료** |
| 4 | auth_service에 scope_level/dept_id 토큰 포함 | 3 | **완료** |
| 5 | 기존 role_code 하드코딩 11곳 → scope_level 기반 교체 | 2, 3 | **완료** |
| 5.5 | 역할 CRUD에 scope_level 지원 (모델/서비스/UI/테스트) | 1 | **완료** |
| 6 | 부서 CRUD API + 서비스 구현 | 1 | **완료** |
| 7 | 부서 관리 Admin UI (DepartmentsView.vue) | 6 | **완료** |
| 10 | 사용자 관리 UI에 부서 선택 드롭다운 추가 | 6 | **완료** |

> **마이그레이션 스크립트**:
> - `docs/sql/migration_v2_department_sso.sql` — 테이블/컬럼/데이터 추가
> - `docs/sql/migration_v2_reorder_columns.sql` — 컬럼 순서 정리 (재생성 방식)
>
> **검증 결과** (2026-02-24):
> - 통합 테스트 86개 전체 통과 (`pytest tests/ -v`)
> - 프론트엔드 빌드 성공 (`npm run build`)

### Phase 4 (SSO — RS256 + Frontend Redirect)

| 순서 | 작업 | 의존성 | 상태 |
|:---:|------|--------|:---:|
| 8-1 | RS256 키 쌍 생성 스크립트 (`scripts/generate_sso_keys.py`) | 없음 | - |
| 8-2 | SSO 설정 추가 (`app/config.py`) | 없음 | - |
| 8-3 | Pydantic 모델 추가 (`SSOLoginRequest`, `SSOTokenPayload`) | 없음 | - |
| 8-4 | RS256 토큰 검증 모듈 (`app/core/security/sso.py`) | 8-1, 8-2 | - |
| 8-5 | SSO 서비스 로직 (`auth_service.py` — 4개 메서드) | 8-3, 8-4 | - |
| 8-6 | SSO 라우트 (`POST /api/v1/auth/sso`) | 8-5 | - |
| 8-7 | 프론트엔드 SSO API (`auth.js` — ssoLogin 메서드) | 8-6 | - |
| 8-8 | Vuex auth store (`ssoLogin` 액션) | 8-7 | - |
| 8-9 | Vue Router (`/sso` 경로 추가) | 없음 | - |
| 8-10 | SSO 콜백 화면 (`SSOCallbackView.vue`) | 8-7, 8-8, 8-9 | - |
| 8-11 | 앱 시작 시 공개키 로드 (`main.py` lifespan) | 8-4 | - |
| 8-12 | SSO 통합 테스트 (`test_12_sso.py` — 8개) | 8-6 | - |
| 8-13 | 설계서 최종 업데이트 | 전체 | - |

### Phase 5 (배치 동기화 — 미착수)

| 순서 | 작업 | 의존성 | 상태 |
|:---:|------|--------|:---:|
| 9 | 배치 동기화 스크립트 (부서/사용자/퇴직자) | Phase 4 | - |

---

## 11. 결정 사항 및 미결정 사항

### 11.1 결정 완료 (v3.0)

| 항목 | 결정 | 근거 |
|------|------|------|
| SSO 서명 방식 | **RS256 (비대칭키)** | MUREUM은 공개키만 보유 → 키 유출 시에도 토큰 위조 불가, 1:N 확장 용이 |
| SSO 토큰 전달 방식 | **URL query → Frontend Redirect** | 기존 localStorage+Vuex 인증 체계 유지, 쿠키 방식 불필요 |
| position 매핑 주체 | **MUREUM에서 매핑** | `tb_code` SSO_ROLE_MAP 활용, Admin UI에서 운영 중 추가 가능 |
| 부서 계층 동기화 | **JIT flat 생성 + 배치 정리** | JIT 시 depth=0으로 생성, 계층은 Admin UI 또는 배치에서 정리 |
| 자체 계정 + SSO 병행 | **병행 (SSO_ENABLED 플래그)** | 개발/테스트 환경은 자체 로그인, 운영은 SSO 활성화 |

### 11.2 미결정 사항

| 항목 | 설명 | 비고 |
|------|------|------|
| 퇴직자 처리 주기 | 일 1회 배치 vs 메인 시스템 이벤트 수신 | Phase 5에서 결정 |
| 다중 issuer 키 관리 | issuer별 공개키 분리 vs 단일 공개키 | 현재는 단일 공개키, 추후 확장 시 검토 |
| SSO 로그아웃 연동 (SLO) | 메인 시스템 로그아웃 시 MUREUM 세션 만료 | 필요 시 Phase 5+ |

# 조직(부서) 관리 및 SSO 연동 설계서

> **문서 버전**: 5.0
> **작성일**: 2026-02-23
> **최종 수정**: 2026-03-12
> **상태**: Phase 1~4 구현 완료, Phase 5(SSO JIT 사용자 자동 생성) 설계 완료
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
| SSO 인프라 | RS256 공개키 검증, SSO 설정, Pydantic 모델 | **완료** |
| SSO 인증 API | POST /sso (API), POST /sso-redirect (Hidden Form + Cookie) | **완료** |
| SSO 프론트엔드 | SSOCallbackView.vue (Cookie Base64URL), router /sso | **완료** |
| SSO 테스트 도구 | RS256 키 생성 스크립트 + 독립 HTML 테스트 페이지 | **완료** |
| SSO 통합 테스트 | SSO 통합 테스트 (8개) | 미구현 |
| **SSO JIT 자동 생성** | **SSO 로그인 시 미등록 사용자 자동 생성 (USER 역할 고정)** | **설계 완료** |
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

### 6.1 방식: Hidden Form POST + Cookie Base64URL (RS256)

메인 시스템이 **RS256 개인키**로 서명한 JWT를 **Hidden Form POST**로 백엔드에 직접 전달하고,
백엔드가 검증 후 win-AI JWT를 **Cookie(Base64URL)**에 담아 302 리다이렉트한다.
Vue 프론트엔드(SSOCallbackView)가 쿠키를 읽어 인증을 완료한다.

```
RS256 (비대칭키) 역할 분리:
  메인 시스템: 개인키(private_key.pem)로 서명 → 토큰 생성 가능
  win-AI:     공개키(public_key.pem)로 검증  → 토큰 검증만 가능 (생성 불가)
```

#### 전체 시퀀스

```
[메인 시스템/SSO 테스트 HTML]     [win-AI 백엔드]             [Vue 프론트엔드]
     │                              │                           │
     │ 1. 사용자 클릭 "AI 챗봇"      │                           │
     │ 2. RS256 개인키로 SSO JWT 서명 │                           │
     │                              │                           │
     │ 3. Hidden Form POST ────────▶│                           │
     │    POST /api/v1/auth/sso-redirect                        │
     │    body: token=eyJ...        │                           │
     │                              │ 4. Form에서 token 추출     │
     │                              │ 5. RS256 공개키로 서명 검증  │
     │                              │ 6. issuer, exp, iat 검증   │
     │                              │ 7. 사용자 조회 (기존 계정)   │
     │                              │ 8. win-AI JWT 발급 (HS256)  │
     │                              │ 9. Set-Cookie: sso_auth    │
     │                              │    = Base64URL({at, rt})   │
     │                              │ 10. 302 Redirect → /sso    │
     │                              │ ─────────────────────────▶ │
     │                              │                           │ 11. SSOCallbackView.vue
     │                              │                           │ 12. 쿠키 sso_auth 읽기
     │                              │                           │ 13. Base64URL 디코딩
     │                              │                           │ 14. 쿠키 즉시 삭제 (1회용)
     │                              │                           │ 15. localStorage 토큰 저장
     │                              │                           │ 16. GET /api/v1/auth/me
     │                              │ ◀───────────────────────── │    (메뉴 권한 조회)
     │                              │ ── UserInfo + menus ─────▶ │
     │                              │                           │ 17. Vuex store 저장
     │                              │                           │ 18. router.replace(landing)
```

> **왜 Hidden Form POST인가?**
> URL query string에 토큰을 노출하지 않아 보안 우수. 브라우저 히스토리/Referer에 토큰이 남지 않음.
> 기존 엔터프라이즈 SSO(SAML, CAS 등)와 동일한 패턴으로 검증된 방식.

> **왜 Cookie Base64URL인가?**
> - **Base64URL (RFC 4648 §5)**: `A-Za-z0-9-_` 문자만 사용, `=` 패딩 제거 → Starlette 쿠키 자동 인용(quoting) 문제 회피
> - 쿠키는 60초 TTL 1회용으로 즉시 삭제되며, `/me` API로 사용자 정보를 별도 조회 (쿠키 크기 제한 회피)
> - OAuth 2.1에서 Implicit Flow(hash fragment) 폐지 → Cookie 기반이 현대 표준에 부합

> **왜 RS256인가?**
> HS256(대칭키)은 win-AI도 같은 키를 보유하므로 위조 토큰 생성 가능.
> RS256(비대칭키)은 win-AI가 공개키만 보유하므로 검증만 가능, 위조 불가.
> 향후 여러 외부 시스템 연동 시에도 공개키만 추가하면 됨 (1:N 확장 용이).

### 6.2 메인 시스템이 보내는 SSO 토큰

```json
{
  "sub": "admin",
  "name": "관리자",
  "email": "admin@company.com",
  "tenant_code": "TENANT_A",
  "dept_code": "DEV_01",
  "dept_name": "개발1팀",
  "iat": 1740000000,
  "exp": 1740000300,
  "iss": "hr-system"
}
```

| 필드 | 용도 | 필수 | 비고 |
|------|------|:---:|------|
| sub | 사용자 식별자 (win-AI login_id로 매핑) | O | `tb_user.login_id`와 매칭 |
| name | 이름 | O | 표시명 (display_name) |
| email | 이메일 | **O** | **JIT 사용자 생성 시 필수** (tb_user.email UNIQUE) |
| tenant_code | 회사 코드 (Company Code → 내부 테넌트 매핑) | **O** | **JIT 사용자 생성 시 필수** |
| dept_code | 부서 코드 | △ | JIT 시 부서 매핑 (없으면 NULL) |
| dept_name | 부서명 | △ | JIT 시 부서 자동 생성에 사용 |
| iss | 발급 시스템 식별자 | O | `sso_allowed_issuers`로 검증 |
| exp | 만료 시간 (짧게 — 5분 이내) | O | PyJWT `require` 옵션으로 강제 |

> **기존 사용자 로그인**: `sub`, `name`, `iss`, `exp`만 있어도 됨 (login_id로 매칭).
> **JIT 자동 생성**: `email`, `tenant_code`가 추가로 **필수** (없으면 자동 생성 불가 → SSO_USER_NOT_FOUND 에러).
> **역할 정책**: 모든 SSO 자동 생성 사용자는 **USER 역할 고정**. 관리자는 시스템에서 직접 등록한다.

### 6.3 사용자 자동 생성 (Just-In-Time Provisioning) — 설계 완료

SSO 로그인 시 win-AI에 사용자가 없으면 **즉시 생성**한다.

> **핵심 정책**: 모든 SSO 자동 생성 사용자는 **USER 역할 고정**. 관리자(GLOBAL/TENANT/DEPT)는 시스템에서 직접 등록한다.

#### 6.3.1 JIT 흐름

```
SSO JWT 수신 → verify_sso_token()
  → _find_sso_user() (기존 사용자 검색)
  ├─ 사용자 존재 → 변경 감지 (display_name, email) → 기존 로그인 흐름
  └─ 사용자 미존재 + sso_auto_create_user=True
       → 필수 클레임 확인 (email, tenant_code)
       → tenant_code → tb_tenant.tenant_code로 테넌트 조회
       → dept_code → tb_department.dept_code로 부서 조회/자동생성 (선택)
       → USER 역할(sso_default_role) role_id 조회
       → 랜덤 패스워드 생성 (SSO 전용 — 직접 로그인 불가)
       → tb_user INSERT
       → USER 기본 메뉴 권한 할당 (tb_user_menu INSERT)
       → create_session() → TokenResponse
```

#### 6.3.2 자동 생성 조건

| 조건 | 충족 시 | 미충족 시 |
|------|---------|----------|
| `sso_auto_create_user=True` | 자동 생성 진행 | SSO_USER_NOT_FOUND (404) |
| `email` 클레임 존재 | 자동 생성 진행 | SSO_INVALID_TOKEN (401, "자동 등록에 email이 필요합니다") |
| `tenant_code` 클레임 존재 | 자동 생성 진행 | SSO_INVALID_TOKEN (401, "자동 등록에 tenant_code가 필요합니다") |
| `tenant_code` → tb_tenant 매칭 | 자동 생성 진행 | SSO_INVALID_TOKEN (401, "유효하지 않은 테넌트 코드") |
| `email` 중복 없음 | 자동 생성 진행 | SSO_INVALID_TOKEN (401, "이미 사용 중인 이메일") |

#### 6.3.3 구현 의사코드

```python
def find_or_create_sso_user(self, sso_data: SSOTokenPayload, request_id: str) -> dict:
    """SSO 사용자 조회 → 없으면 자동 생성"""

    # 1. 기존 사용자 조회 (sso_provider + sso_external_id → login_id 폴백)
    user = self._find_sso_user(sso_data.iss, sso_data.sub)

    if user:
        # 2a. 있음 → 변경 감지 후 업데이트 (display_name, email만)
        changes = self._detect_sso_changes(user, sso_data)
        if changes:
            self._update_sso_fields(user["user_id"], changes)
        return user

    # 2b. 없음 → 자동 생성 가능 여부 확인
    if not settings.sso_auto_create_user:
        raise APIException(ErrorCode.SSO_USER_NOT_FOUND, "SSO 사용자를 찾을 수 없습니다")

    # 3. 필수 클레임 검증
    if not sso_data.email:
        raise APIException(ErrorCode.SSO_INVALID_TOKEN, "자동 등록에 email이 필요합니다")
    if not sso_data.tenant_code:
        raise APIException(ErrorCode.SSO_INVALID_TOKEN, "자동 등록에 tenant_code가 필요합니다")

    # 4. 테넌트 조회
    tenant_id = self._resolve_tenant(sso_data.tenant_code)

    # 5. 부서 조회/생성 (선택 — dept_code 있을 때만)
    dept_id = None
    if sso_data.dept_code:
        dept_id = self._resolve_or_create_dept(tenant_id, sso_data.dept_code, sso_data.dept_name)

    # 6. USER 역할 ID 조회 (고정)
    role_id = self._get_default_role_id()

    # 7. 사용자 생성
    import secrets
    random_password = secrets.token_urlsafe(32)  # SSO 전용 — 직접 로그인 불가

    new_user_id = self._create_sso_user(
        login_id=sso_data.sub,
        display_name=sso_data.name,
        email=sso_data.email,
        password_hash=hash_password(random_password),
        tenant_id=tenant_id,
        dept_id=dept_id,
        role_id=role_id,
        sso_provider=sso_data.iss,
        sso_external_id=sso_data.sub,
    )

    # 8. USER 기본 메뉴 권한 할당
    self._assign_default_menus(new_user_id, role_id)

    return self._find_sso_user(sso_data.iss, sso_data.sub)
```

#### 6.3.4 자동 생성 사용자 DB 레코드

```sql
INSERT INTO tb_user (
    login_id,          -- sso_data.sub (사번 등)
    email,             -- sso_data.email
    display_name,      -- sso_data.name
    password_hash,     -- secrets.token_urlsafe(32) → bcrypt (SSO 전용, 직접 로그인 불가)
    tenant_id,         -- tenant_code → tb_tenant.tenant_id
    dept_id,           -- dept_code → tb_department.dept_id (NULL 허용)
    role_id,           -- sso_default_role(USER) → tb_role.role_id
    is_active,         -- true
    is_superuser,      -- false
    sso_provider,      -- sso_data.iss
    sso_external_id,   -- sso_data.sub
    last_login_at      -- NOW()
) VALUES (...);

-- 기본 메뉴 권한 할당 (USER 역할 기본값)
INSERT INTO tb_user_menu (user_id, menu_id, can_create, can_read, can_update, can_delete, can_export)
SELECT new_user_id, m.menu_id, true, true, false, false, false
FROM tb_menu m WHERE m.menu_code = 'AI_CHAT';
```

> **USER 기본 메뉴**: `AI_CHAT` (can_create=true, can_read=true) — `/chat` 페이지 접근만 가능.
> **비밀번호**: 랜덤 생성으로 직접 로그인 불가 → SSO로만 접속. 관리자가 비밀번호 초기화 시 자체 로그인도 가능.

### 6.4 부서 자동 생성

SSO 토큰의 `dept_code`가 있으나 win-AI에 없으면 **자동 생성**한다.
`dept_code`가 없으면 `dept_id=NULL`로 처리 (부서 미지정).

```python
def _resolve_or_create_dept(self, tenant_id: int, dept_code: str, dept_name: str = None) -> int:
    """부서 조회 — 없으면 생성"""
    with db_manager.get_cursor() as cur:
        cur.execute(
            "SELECT dept_id FROM tb_department WHERE tenant_id = %s AND dept_code = %s",
            (tenant_id, dept_code)
        )
        row = cur.fetchone()

    if row:
        return row["dept_id"]

    # 없으면 최상위(depth=0) 부서로 생성
    with db_manager.get_cursor(commit=True) as cur:
        cur.execute(
            "INSERT INTO tb_department (tenant_id, dept_code, dept_name, depth, sort_order) "
            "VALUES (%s, %s, %s, 0, 0) RETURNING dept_id",
            (tenant_id, dept_code, dept_name or dept_code)
        )
        return cur.fetchone()["dept_id"]
```

> 자동 생성된 부서는 `depth=0` (최상위)로 생성된다.
> 부서 계층(parent_dept_id, depth)은 **Admin UI**에서 정리한다.

### 6.5 역할 정책

모든 SSO 자동 생성 사용자는 **USER 역할 고정**. 관리자(GLOBAL/TENANT/DEPT)는 시스템에서 직접 등록한다.

```python
def _get_default_role_id(self) -> int:
    """SSO 기본 역할(USER) ID 조회"""
    role_code = settings.sso_default_role  # 기본값: "USER"
    with db_manager.get_cursor() as cur:
        cur.execute("SELECT role_id FROM tb_role WHERE role_code = %s", (role_code,))
        row = cur.fetchone()
        if not row:
            raise APIException(ErrorCode.NOT_FOUND, f"기본 역할 '{role_code}'을 찾을 수 없습니다")
        return row["role_id"]
```

> SSO 토큰에 `position`(직급) 필드를 포함하지 않는다. 역할은 항상 `sso_default_role` 설정값(기본: USER)을 사용한다.
> 보안상 SSO로 관리자 권한을 자동 부여하지 않는다. 필요 시 Admin UI에서 역할을 변경한다.

### 6.6 SSO 설정

```bash
# .env
SSO_ENABLED=false                              # SSO 활성화 여부 (기본: 비활성)
SSO_PUBLIC_KEY_PATH=keys/sso_public.pem        # RS256 공개키 경로
SSO_ALGORITHM=RS256                            # 서명 알고리즘 (RS256 고정)
SSO_ALLOWED_ISSUERS=hr-system                  # 허용 발급자 (콤마 구분)
SSO_TOKEN_MAX_AGE=300                          # SSO 토큰 최대 유효시간 (초, 기본 5분)
SSO_DEFAULT_ROLE=USER                          # SSO 자동 생성 사용자 역할 (USER 고정 권장)
SSO_AUTO_CREATE_USER=true                      # 사용자 자동 생성 (JIT Provisioning)
SSO_FRONTEND_URL=                              # SSO 리다이렉트 프론트엔드 URL (빈 값이면 상대경로 /sso)
```

> **키 관리 원칙**:
> - `keys/sso_public.pem` — win-AI가 보유 (검증 전용, 유출되어도 안전)
> - `keys/sso_private.pem` — 메인 시스템이 보유 (서명 전용, win-AI에 저장 금지)
> - `keys/` 디렉토리는 `.gitignore`에 등록

> **SSO_FRONTEND_URL**:
> - 개발 환경: `http://localhost:19080` (백엔드 19090 → 프론트엔드 19080 크로스 포트)
> - Docker/운영: 빈 값 (Nginx가 같은 origin에서 프록시하므로 상대경로 `/sso` 사용)

```python
# app/config.py — Settings 클래스 (구현 완료)
class Settings(BaseSettings):
    # ... 기존 설정 ...

    # SSO (Single Sign-On)
    sso_enabled: bool = Field(default=False, description="SSO 활성화 여부")
    sso_public_key_path: str = Field(default="keys/sso_public.pem", description="SSO RS256 공개키 파일 경로")
    sso_algorithm: str = Field(default="RS256", description="SSO 토큰 알고리즘")
    sso_allowed_issuers: str = Field(default="hr-system", description="허용된 SSO 발급자 (쉼표 구분)")
    sso_token_max_age: int = Field(default=300, description="SSO 토큰 최대 유효 시간(초)")
    sso_default_role: str = Field(default="USER", description="SSO 자동 생성 사용자 역할 (USER 고정 권장)")
    sso_auto_create_user: bool = Field(default=True, description="SSO 사용자 자동 생성 (JIT Provisioning)")
    sso_frontend_url: str = Field(default="", description="SSO 리다이렉트 프론트엔드 URL (빈 값이면 상대경로)")
```

### 6.7 SSO API

| Method | Endpoint | 설명 | 인증 | Content-Type |
|--------|----------|------|:---:|-------------|
| POST | `/api/v1/auth/sso` | SSO 토큰 교환 → JSON 응답 (API 직접 호출용) | No | application/json |
| POST | `/api/v1/auth/sso-redirect` | SSO Hidden Form → 쿠키 → 302 리다이렉트 (브라우저용) | No | application/x-www-form-urlencoded |

#### POST /sso (API 직접 호출용)

스크립트, 테스트 도구 등에서 직접 호출하는 JSON API.

**Request**:
```json
{
  "sso_token": "eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhZG1pbiIs..."
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
    "expires_in": 1800
  }
}
```

#### POST /sso-redirect (브라우저 Hidden Form POST용)

외부 시스템에서 Hidden Form으로 토큰을 전송하면, 백엔드가 검증 후 쿠키에 JWT를 담아 302 리다이렉트.

**Request** (Form):
```
token=eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhZG1pbiIs...
```

**Response**:
```
HTTP/1.1 302 Found
Location: http://localhost:19080/sso    (또는 상대경로 /sso)
Set-Cookie: sso_auth=eyJhdCI6ImV5Si4uLiIsInJ0IjoiZXlKLi4uIn0; Max-Age=60; Path=/; SameSite=Lax
```

쿠키 `sso_auth` 값은 Base64URL 인코딩 (RFC 4648 §5):
```json
{"at": "<access_token>", "rt": "<refresh_token>"}
```

프론트엔드 `SSOCallbackView.vue`가 쿠키를 읽고 → 즉시 삭제 → `/me` API 호출 → 로그인 완료.

#### 에러 응답

| 상황 | HTTP | error.code | error.message |
|------|:---:|-----------|---------------|
| SSO 비활성 | 403 | SSO_DISABLED | SSO 로그인이 비활성화되어 있습니다 |
| 공개키 미설정 | 500 | SSO_NOT_CONFIGURED | SSO가 설정되지 않았습니다. 공개키를 확인해주세요 |
| 토큰 서명 불일치 | 401 | SSO_INVALID_TOKEN | SSO 토큰 서명이 유효하지 않습니다 |
| 토큰 형식 오류 | 401 | SSO_INVALID_TOKEN | SSO 토큰 형식이 올바르지 않습니다 |
| 필수 클레임 누락 | 401 | SSO_INVALID_TOKEN | SSO 토큰에 필수 클레임이 없습니다 |
| 토큰 만료 | 401 | SSO_TOKEN_EXPIRED | SSO 토큰이 만료되었습니다 |
| issuer 미허용 | 401 | SSO_INVALID_TOKEN | 허용되지 않은 SSO 발급자 |
| 최대 유효시간 초과 | 401 | SSO_TOKEN_EXPIRED | SSO 토큰이 최대 유효 시간을 초과했습니다 |
| 사용자 미등록 (자동생성 off) | 404 | SSO_USER_NOT_FOUND | SSO 사용자를 찾을 수 없습니다 |
| 자동등록 시 email 누락 | 401 | SSO_INVALID_TOKEN | 자동 등록에 email이 필요합니다 |
| 자동등록 시 tenant_code 누락 | 401 | SSO_INVALID_TOKEN | 자동 등록에 tenant_code가 필요합니다 |
| 자동등록 시 테넌트 미존재 | 401 | SSO_INVALID_TOKEN | 유효하지 않은 테넌트 코드 |
| 자동등록 시 email 중복 | 401 | SSO_INVALID_TOKEN | 이미 사용 중인 이메일 |
| 사용자 비활성 | 401 | UNAUTHORIZED | 비활성화된 계정입니다 |

### 6.8 RS256 토큰 검증 모듈 (구현 완료)

```python
# app/core/security/sso.py — 실제 구현 (PyJWT 사용)

import time
import jwt  # PyJWT (not python-jose)

_sso_public_key: Optional[str] = None  # 모듈 레벨 캐시

def load_sso_public_key() -> None:
    """SSO RS256 공개키를 파일에서 로드하여 모듈 캐시에 저장 (앱 시작 시 1회 호출)"""
    global _sso_public_key
    if not settings.sso_enabled:
        return
    key_path = settings.sso_public_key_path
    try:
        with open(key_path, "r") as f:
            _sso_public_key = f.read()
    except FileNotFoundError:
        _sso_public_key = None

def verify_sso_token(token: str) -> SSOTokenPayload:
    """SSO JWT 토큰 검증 (4단계: 서명 → 발급자 → 최대수명 → 페이로드 파싱)"""
    if _sso_public_key is None:
        raise APIException(ErrorCode.SSO_NOT_CONFIGURED, "SSO가 설정되지 않았습니다")

    # 1. JWT 디코딩 + RS256 서명 검증
    payload = jwt.decode(
        token, _sso_public_key,
        algorithms=[settings.sso_algorithm],
        options={"require": ["sub", "name", "iss", "exp"]},
    )

    # 2. 발급자(iss) 화이트리스트 검증
    allowed = [iss.strip() for iss in settings.sso_allowed_issuers.split(",")]
    if payload.get("iss") not in allowed:
        raise APIException(ErrorCode.SSO_INVALID_TOKEN, "허용되지 않은 SSO 발급자")

    # 3. 토큰 최대 유효 시간 검증 (iat 기반)
    iat = payload.get("iat")
    if iat and (time.time() - iat) > settings.sso_token_max_age:
        raise APIException(ErrorCode.SSO_TOKEN_EXPIRED, "SSO 토큰이 최대 유효 시간을 초과했습니다")

    # 4. 페이로드 파싱 → SSOTokenPayload
    return SSOTokenPayload(sub=payload["sub"], name=payload["name"], ...)
```

> **라이브러리**: PyJWT (`jwt.decode`) 사용. `python-jose`가 아님에 주의.
> **에러 분기**: `ExpiredSignatureError`, `InvalidSignatureError`, `DecodeError`, `MissingRequiredClaimError` 각각 별도 에러 코드 매핑.

### 6.9 Pydantic 모델 (구현 완료)

```python
# app/models/auth.py

class SSOLoginRequest(BaseModel):
    """SSO 토큰 교환 요청 (POST /sso JSON API용)"""
    sso_token: str = Field(..., min_length=1, description="SSO JWT 토큰 (RS256 서명)")

class SSOTokenPayload(BaseModel):
    """메인 시스템이 발급한 SSO JWT의 payload"""
    sub: str                                    # 사용자 식별자 → login_id 매핑
    name: str                                   # 이름
    email: Optional[str] = None                 # 이메일 (JIT 자동 생성 시 필수)
    tenant_code: Optional[str] = None           # 테넌트 코드 (JIT 자동 생성 시 필수)
    dept_code: Optional[str] = None             # 부서 코드 (JIT 시 부서 매핑, 없으면 NULL)
    dept_name: Optional[str] = None             # 부서명 (JIT 시 부서 자동 생성에 사용)
    iss: str                                    # 발급 시스템 식별자
    exp: int                                    # 만료 시간 (Unix timestamp)
```

> **기존 사용자 로그인**: `sub`, `name`, `iss`, `exp`만 필수. login_id로 매칭.
> **JIT 자동 생성**: `email`, `tenant_code`가 추가 필수. 없으면 자동 생성 불가 → 에러.
> **POST /sso-redirect는 `Form(token=...)`**: `SSOLoginRequest` 모델이 아닌 FastAPI `Form` 파라미터로 수신.

### 6.10 변경 감지 항목

SSO 로그인 시 기존 사용자의 정보 변경을 자동 감지하여 업데이트한다.

| 항목 | SSO 필드 | tb_user 컬럼 | 변경 시 동작 |
|------|----------|-------------|------------|
| 이름 | name | display_name | UPDATE |
| 이메일 | email | email | UPDATE (email이 있을 때만) |

> **역할/부서 변경**: SSO에서 자동 변경하지 않음. 관리자가 Admin UI에서 직접 변경한다.
> **이유**: 역할 변경은 권한 상승 위험이 있고, 부서 이동은 관리자 확인이 필요하므로 자동화하지 않는다.

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
메인 시스템 API → win-AI 배치 스크립트

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

### 9.2 백엔드 — Phase 4 (SSO) 구현 완료

```
app/config.py                          # 변경: SSO 설정 8개 추가 (sso_enabled ~ sso_frontend_url)  ✅

app/core/security/
  └── sso.py                           # ★ 신규: RS256 공개키 로드 + SSO 토큰 검증 (PyJWT)  ✅
                                       #   load_sso_public_key()  — 앱 시작 시 공개키 캐시
                                       #   verify_sso_token()     — 서명+발급자+최대수명 검증

app/api/routes/
  └── auth.py                          # 변경: SSO 엔드포인트 2개 추가  ✅
                                       #   POST /sso         — JSON API (토큰 교환 → JWT 응답)
                                       #   POST /sso-redirect — Form POST → Cookie Base64URL → 302

app/api/services/
  └── auth_service.py                  # 변경: SSO 메서드 2개 추가  ✅
                                       #   sso_authenticate()  — SSO 인증 (기존 사용자 매칭)
                                       #   _find_sso_user()    — 1순위 sso_external_id, 2순위 login_id

app/models/
  └── auth.py                          # 변경: SSOLoginRequest, SSOTokenPayload 모델 추가  ✅

app/main.py                            # 변경: lifespan에 load_sso_public_key() 호출 추가  ✅

keys/                                  # ★ 신규 디렉토리 (.gitignore 등록)  ✅
  ├── sso_public.pem                   # RS256 공개키 (win-AI 보유)
  └── sso_private.pem                  # RS256 개인키 (테스트용)

scripts/
  ├── generate_sso_keys.py             # ★ 신규: RS256 키 쌍 생성 도구  ✅
  └── sso_test_server/                 # ★ 신규: 독립 SSO 테스트 도구  ✅
      ├── sso_test.html                # SSO 시뮬레이터 (jose CDN, Hidden Form POST)
      └── run.py                       # HTTP 서버 래퍼 (포트 19081)
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

### 9.4 프론트엔드 — Phase 4 (SSO) 구현 완료

```
frontend/src/
  ├── api/auth.js              # 변경: getMe() 활용 (ssoLogin 함수 불필요 → 제거)  ✅
  ├── store/modules/auth.js    # 변경: ssoLogin 액션 불필요 → 제거 (쿠키에서 직접 처리)  ✅
  ├── router/index.js          # 변경: /sso 경로 추가 (meta: { public: true })  ✅
  └── views/
      ├── SSOCallbackView.vue  # ★ 신규: SSO 콜백 화면  ✅
      │                        #   쿠키 sso_auth 읽기 → Base64URL 디코딩
      │                        #   → 쿠키 삭제 → localStorage 토큰 저장
      │                        #   → GET /me → Vuex 저장 → landing_page 이동
      └── LoginView.vue        # 변경: SSO 테스트 버튼 추가 (dev 환경)  ✅
                               #   window.open('http://localhost:19081/sso_test.html')
```

> **설계 변경**: API 직접 호출(ssoLogin action) 대신 쿠키 기반으로 변경.
> `SSOCallbackView`가 쿠키를 읽고 `/me` API만 호출하므로 auth.js/store에 SSO 전용 함수 불필요.

### 9.5 테스트

```
tests/
  ├── test_04_roles.py         # 변경: TestRoleScopeLevel 클래스 추가 (7개 테스트)  ✅
  ├── test_11_departments.py   # ★ 신규: 부서 CRUD 통합 테스트  ✅
  └── test_12_sso.py           # ★ 신규: SSO 통합 테스트 (9개)
                               #   test_sso_login_existing_user  — 기존 사용자 SSO 로그인
                               #   test_sso_login_new_user       — 신규 사용자 JIT 자동 생성 (USER 역할)
                               #   test_sso_auto_create_default_menus — 자동 생성 시 기본 메뉴 할당
                               #   test_sso_change_detection     — 기존 사용자 정보 변경 감지
                               #   test_sso_missing_email        — email 누락 → 자동 생성 실패
                               #   test_sso_missing_tenant_code  — tenant_code 누락 → 자동 생성 실패
                               #   test_sso_invalid_token        — 잘못된 토큰 → 401
                               #   test_sso_dept_auto_create     — 부서 자동 생성
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

### Phase 4 (SSO — RS256 + Cookie Base64URL + Hidden Form POST)

| 순서 | 작업 | 의존성 | 상태 |
|:---:|------|--------|:---:|
| 8-1 | RS256 키 쌍 생성 스크립트 (`scripts/generate_sso_keys.py`) | 없음 | **완료** |
| 8-2 | SSO 설정 추가 (`app/config.py` — 8개 설정) | 없음 | **완료** |
| 8-3 | Pydantic 모델 추가 (`SSOLoginRequest`, `SSOTokenPayload`) | 없음 | **완료** |
| 8-4 | RS256 토큰 검증 모듈 (`app/core/security/sso.py`) | 8-1, 8-2 | **완료** |
| 8-5 | SSO 서비스 로직 (`auth_service.py` — 기존 사용자 매칭) | 8-3, 8-4 | **완료** |
| 8-6 | SSO 라우트 (`POST /sso` + `POST /sso-redirect`) | 8-5 | **완료** |
| 8-7 | Vue Router (`/sso` 경로, `public: true`) | 없음 | **완료** |
| 8-8 | SSO 콜백 화면 (`SSOCallbackView.vue` — Cookie Base64URL) | 8-6, 8-7 | **완료** |
| 8-9 | 앱 시작 시 공개키 로드 (`main.py` lifespan) | 8-4 | **완료** |
| 8-10 | SSO 테스트 시뮬레이터 (`scripts/sso_test_server/`) | 8-6 | **완료** |
| 8-11 | 설계서 최종 업데이트 | 전체 | **완료** |
| 8-12 | SSO 통합 테스트 (`test_12_sso.py` — 8개) | 8-6 | 미구현 |

> **설계 변경 사항 (v3.0 → v4.0)**:
> - 8-7, 8-8: `ssoLogin` 액션/API 함수 불필요 → 제거. 쿠키 기반이므로 프론트엔드에서 직접 처리.
> - 8-6: `POST /sso-redirect` 추가 (Hidden Form → Cookie → 302). 기존 `POST /sso`는 API 직접 호출용으로 유지.
> - 8-10: 독립 HTML SSO 테스트 시뮬레이터 추가 (jose CDN, HTTP 전문 미리보기).

### Phase 5 (SSO JIT 사용자 자동 생성 — 설계 완료)

| 순서 | 작업 | 의존성 | 상태 |
|:---:|------|--------|:---:|
| 9-1 | `sso_auto_create_user` 기본값 True로 변경 (`app/config.py`) | 없음 | - |
| 9-2 | `auth_service.py`에 `find_or_create_sso_user()` 구현 | 9-1 | - |
| 9-3 | `auth_service.py`에 `_resolve_tenant()`, `_resolve_or_create_dept()`, `_get_default_role_id()` 구현 | 9-2 | - |
| 9-4 | `auth_service.py`에 `_create_sso_user()`, `_assign_default_menus()` 구현 | 9-3 | - |
| 9-5 | `auth_service.py`에 `_detect_sso_changes()`, `_update_sso_fields()` 구현 | 9-2 | - |
| 9-6 | SSO 라우트(`auth.py`)에서 `find_or_create_sso_user()` 호출로 변경 | 9-4 | - |
| 9-7 | SSO 테스트 시뮬레이터에 email/tenant_code 필드 추가 | 9-6 | - |
| 9-8 | SSO 통합 테스트 (`test_12_sso.py`) | 9-6 | - |

> **정책**: 모든 SSO 자동 생성 사용자는 USER 역할 고정. 관리자는 시스템에서 직접 등록.
> **SSO_ROLE_MAP**: 현재 미사용 (향후 확장 대비로 유지).

### Phase 6 (배치 동기화 — 미착수)

| 순서 | 작업 | 의존성 | 상태 |
|:---:|------|--------|:---:|
| 10 | 배치 동기화 스크립트 (부서/사용자/퇴직자) | Phase 5 | - |

---

## 11. 결정 사항 및 미결정 사항

### 11.1 결정 완료 (v4.0)

| 항목 | 결정 | 근거 |
|------|------|------|
| SSO 서명 방식 | **RS256 (비대칭키)** | win-AI는 공개키만 보유 → 키 유출 시에도 토큰 위조 불가, 1:N 확장 용이 |
| SSO 토큰 전달 방식 | **Hidden Form POST + Cookie Base64URL** | URL에 토큰 미노출, OAuth 2.1 Implicit Flow 폐지 방향 부합, 엔터프라이즈 표준 패턴 |
| Cookie 인코딩 | **Base64URL (RFC 4648 §5)** | `A-Za-z0-9-_` 문자만 사용 → Starlette 쿠키 자동 인용 회피, 패딩(`=`) 제거 |
| 사용자 정보 전달 | **/me API 패턴** | 쿠키에는 토큰만(at+rt), 사용자 정보는 `/me` API로 별도 조회 → 쿠키 크기 제한 회피 |
| SSO 사용자 역할 | **USER 고정** | 모든 SSO 자동 생성 사용자는 일반사용자(USER). 관리자는 시스템에서 직접 등록 |
| position 매핑 | **미사용 (향후 확장 대비)** | SSO_ROLE_MAP 데이터는 유지하나 현재 역할 매핑에 사용하지 않음 |
| 부서 계층 동기화 | **JIT flat 생성 + Admin UI 정리** | JIT 시 depth=0으로 생성, 계층은 Admin UI에서 정리 |
| 자체 계정 + SSO 병행 | **병행 (SSO_ENABLED 플래그)** | 개발/테스트 환경은 자체 로그인, 운영은 SSO 활성화 |
| SSO 테스트 도구 | **독립 HTML 페이지** | Vue 앱과 완전 분리, 별도 포트(19081)에서 jose CDN 사용, HTTP 전문 미리보기 제공 |

### 11.2 미결정 사항

| 항목 | 설명 | 비고 |
|------|------|------|
| 퇴직자 처리 주기 | 일 1회 배치 vs 메인 시스템 이벤트 수신 | Phase 5에서 결정 |
| 다중 issuer 키 관리 | issuer별 공개키 분리 vs 단일 공개키 | 현재는 단일 공개키, 추후 확장 시 검토 |
| SSO 로그아웃 연동 (SLO) | 메인 시스템 로그아웃 시 win-AI 세션 만료 | 필요 시 Phase 5+ |

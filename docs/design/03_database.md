# 데이터베이스 설계

> 최종 수정: 2026-02-15

---

## 1. 데이터베이스 구성

| DB | 용도 | 드라이버 |
|----|------|---------|
| **PostgreSQL (서비스 DB)** | 사용자, 문서, 설정, 이력 등 전체 서비스 데이터 | psycopg3 + pgvector |
| **PostgreSQL/Oracle (외부 비즈니스 DB)** | NL2SQL 질의 대상 (employee, department 등) | psycopg3 / oracledb |

---

## 2. ERD

```
                    ┌──────────────────────┐
                    │     tb_tenant        │
                    ├──────────────────────┤
                    │ tenant_id (PK)       │
                    │ tenant_code (UK)     │
                    │ tenant_name          │
                    │ is_active            │
                    │ is_system            │
                    └──────────┬───────────┘
                               │ 1:N
┌───────────────┐    ┌────────┴───────────┐ N:1  ┌────────────────────┐
│   tb_menu     │◄───│      tb_user       │─────►│     tb_role        │
├───────────────┤    ├────────────────────┤      ├────────────────────┤
│ menu_id (PK)  │    │ user_id (PK)       │      │ role_id (PK)       │
│ parent_menu_id│    │ login_id (UK)      │      │ role_code (UK)     │
│ menu_code (UK)│    │ email (UK)         │      │ role_name          │
│ menu_name     │    │ password_hash      │      │ landing_page       │
│ menu_type     │    │ display_name       │      │ is_system          │
│ menu_path     │    │ tenant_id (FK)     │      │ sort_order         │
│ depth         │    │ role_id (FK)       │      └────────────────────┘
│ sort_order    │    │ is_superuser       │
└───────┬───────┘    │ is_active          │
        │            └────────┬───────────┘
        │ N              1   │
        │     ┌──────────────┴────────┐     ┌────────────────────┐
        └────►│    tb_user_menu       │     │  tb_user_session   │
              │  (핵심 권한 테이블)     │     ├────────────────────┤
              ├───────────────────────┤     │ session_id (PK)    │
              │ user_id (PK, FK)      │     │ user_id (FK)       │
              │ menu_id (PK, FK)      │     │ refresh_token      │
              │ can_create            │     │ expires_at         │
              │ can_read              │     └────────────────────┘
              │ can_update            │
              │ can_delete            │
              │ can_export            │
              │ granted_by (FK)       │
              └───────────────────────┘

┌──────────────────────┐     ┌──────────────────────┐
│     tb_docs          │     │   tb_app_settings    │
├──────────────────────┤     ├──────────────────────┤
│ doc_id (PK)          │     │ id (PK)              │
│ title                │     │ tenant_id            │
│ doc_type             │     │ category             │
│ content              │     │ key                  │
│ embedding (vector)   │     │ value                │
│ indexed              │     │ value_type           │
│ embedding_model      │     │ description          │
│ usage_type           │     └──────────────────────┘
│ tenant_id            │
│ parent_doc_id        │     ┌──────────────────────┐
└──────────────────────┘     │   tb_api_history     │
                             ├──────────────────────┤
┌──────────────────────┐     │ id (PK)              │
│     tb_code          │     │ request_id           │
├──────────────────────┤     │ session_id           │
│ code_id (PK)         │     │ tenant_id, user_id   │
│ code_group           │     │ request_type         │
│ code_value           │     │ question, answer     │
│ code_name            │     │ trace_data (JSONB)   │
│ sort_order           │     │ response_time_ms     │
│ is_active            │     │ created_at           │
└──────────────────────┘     └──────────────────────┘
```

---

## 3. 핵심 테이블 명세

### 3.1 tb_tenant

| 컬럼 | 타입 | 설명 |
|------|------|------|
| tenant_id | BIGSERIAL PK | 테넌트 ID |
| tenant_code | VARCHAR(50) UK | 코드 |
| tenant_name | VARCHAR(200) | 테넌트명 |
| is_active | BOOLEAN (true) | 활성화 |
| **is_system** | **BOOLEAN (false)** | **시스템 테넌트 — 삭제/비활성화 불가** |
| metadata | JSONB | 추가 정보 |

### 3.2 tb_role

| 컬럼 | 타입 | 설명 |
|------|------|------|
| role_id | BIGSERIAL PK | 역할 ID |
| role_code | VARCHAR(50) UK | GLOBAL / TENANT / USER |
| role_name | VARCHAR(100) | 역할명 |
| landing_page | VARCHAR(200) | 로그인 후 경로 |
| is_system | BOOLEAN (false) | 시스템 역할 (삭제 불가) |
| **sort_order** | **INT (0)** | **역할 계층 (1=GLOBAL, 2=TENANT, 3=USER)** |

### 3.3 tb_user

| 컬럼 | 타입 | 설명 |
|------|------|------|
| user_id | BIGSERIAL PK | 사용자 ID |
| login_id | VARCHAR(100) UK | 로그인 ID |
| email | VARCHAR(255) UK | 이메일 |
| password_hash | VARCHAR(255) | bcrypt 해시 |
| display_name | VARCHAR(100) | 표시 이름 |
| tenant_id | BIGINT FK | 소속 테넌트 |
| role_id | BIGINT FK NOT NULL | 역할 |
| is_superuser | BOOLEAN (false) | RBAC 비상 우회 |
| is_active | BOOLEAN (true) | 활성화 |
| login_fail_count | INT (0) | 로그인 실패 횟수 |
| locked_until | TIMESTAMPTZ | 잠금 해제 시각 |

### 3.4 tb_user_menu (핵심 권한 테이블)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| user_id | BIGINT PK, FK CASCADE | 사용자 삭제 시 자동 삭제 |
| menu_id | BIGINT PK, FK | 메뉴 ID |
| can_create | BOOLEAN (false) | 등록 권한 |
| can_read | BOOLEAN (true) | 조회 권한 |
| can_update | BOOLEAN (false) | 수정 권한 |
| can_delete | BOOLEAN (false) | 삭제 권한 |
| can_export | BOOLEAN (false) | 내보내기 권한 |
| granted_by | BIGINT FK SET NULL | 권한 부여자 |

### 3.5 tb_menu

| 컬럼 | 타입 | 설명 |
|------|------|------|
| menu_id | BIGSERIAL PK | 메뉴 ID |
| parent_menu_id | BIGINT FK(self) | 상위 메뉴 (NULL=루트) |
| menu_code | VARCHAR(50) UK | 코드 (예: USER_MGMT) |
| menu_name | VARCHAR(100) | 표시명 |
| menu_type | VARCHAR(20) | DIRECTORY / PAGE / API |
| menu_path | VARCHAR(200) | 프론트 경로 |
| api_pattern | VARCHAR(200) | API 패턴 |
| depth | INT (0) | 트리 깊이 |
| sort_order | INT | 정렬 |
| is_active | BOOLEAN (true) | 활성 여부 |

### 3.6 tb_docs

| 컬럼 | 타입 | 설명 |
|------|------|------|
| doc_id | BIGSERIAL PK | 문서 ID |
| title | VARCHAR(500) | 제목 |
| doc_type | VARCHAR(50) | 문서 유형 |
| content | TEXT | 본문 |
| embedding | VECTOR(1536) | 벡터 임베딩 |
| indexed | BOOLEAN (false) | 임베딩 완료 여부 |
| embedding_model | VARCHAR(100) | 사용 모델명 |
| usage_type | VARCHAR(20) | rag / cortex |
| tenant_id | BIGINT | 소속 테넌트 |
| parent_doc_id | BIGINT | 청크 원본 문서 ID |

### 3.7 tb_api_history

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL PK | ID |
| request_id | VARCHAR(20) | 요청 추적 ID (8자 UUID) |
| session_id | VARCHAR | 세션 ID |
| tenant_id, user_id | BIGINT | 사용자/테넌트 |
| request_type | VARCHAR | agent / nl2sql / rag |
| question | TEXT | 원본 질문 |
| answer | TEXT | 최종 답변 |
| **trace_data** | **JSONB** | **실행 추적 (도구, SQL, 소스 등)** |
| response_time_ms | INT | 응답 시간 |
| success | BOOLEAN | 성공 여부 |

### 3.8 tb_app_settings

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL PK | ID |
| tenant_id | BIGINT | 테넌트별 설정 (NULL=글로벌) |
| category | VARCHAR(50) | 카테고리 (llm, rag, nl2sql 등) |
| key | VARCHAR(100) | 설정 키 |
| value | TEXT | 설정 값 |
| value_type | VARCHAR(20) | string / integer / boolean / json |
| description | TEXT | 설명 |

---

## 4. FK CASCADE 동작

사용자 삭제 시:

| 테이블 | FK 동작 | 결과 |
|--------|---------|------|
| tb_user_menu (user_id) | CASCADE | 메뉴 권한 자동 삭제 |
| tb_user_menu (granted_by) | SET NULL | 부여자 정보 NULL |
| tb_user_session | CASCADE | 세션 자동 삭제 |
| tb_api_history | FK 없음 | 이력 보존 |

---

## 5. 커넥션 관리

### 5.1 서비스 DB

```python
from app.core.database.connection import db_manager

# 조회 (자동 커밋 없음)
with db_manager.get_cursor() as cur:
    cur.execute("SELECT ...")
    rows = cur.fetchall()

# 변경 (자동 커밋)
with db_manager.get_cursor(commit=True) as cur:
    cur.execute("INSERT ...")
```

- psycopg3 커넥션 풀: `DB_POOL_SIZE=20`, `DB_MAX_OVERFLOW=10`

### 5.2 외부 비즈니스 DB

```python
from app.core.database.external import external_db_manager
# NL2SQL 대상 DB (PostgreSQL 또는 Oracle)
```

### 5.3 DB 어댑터 패턴

```python
from app.core.database.adapters.factory import get_adapter

adapter = get_adapter("postgresql")  # 또는 "oracle"
```

| 어댑터 | 행 제한 | 스키마 조회 |
|--------|---------|-----------|
| PostgreSQL | `LIMIT N` | `information_schema` |
| Oracle | `FETCH FIRST N ROWS ONLY` | `ALL_TABLES` |

새 DB 추가 시: `adapters/` 하위에 `DatabaseAdapter` 구현 → `factory.py`에 등록

---

## 6. Dynamic Settings 체계

설정값 우선순위:

```
1. PostgreSQL tb_app_settings (최우선 — Admin UI에서 변경 가능)
2. 환경변수 (.env)
3. config.py 기본값 (최하위)
```

사용 패턴:

```python
from app.api.services.settings_service import settings_service
value = settings_service.get_value("llm", "model", settings.llm_model)
```

---

## 7. SQL DDL 참조

| 파일 | 설명 |
|------|------|
| `docs/sql/psql-hermes_db.sql` | 전체 스키마 + 초기 데이터 |
| `docs/sql/psql-hermes_db_no_data.sql` | 스키마만 (데이터 없음) |
| `docs/sql/tb_user_permission.sql` | 사용자 권한 테이블 DDL |
| `docs/sql/tb_api_history.sql` | API 이력 테이블 DDL |
| `docs/sql/migration_role_scope.sql` | v2→v3 마이그레이션 |
| `docs/sql/orcl-business_db.sql` | Oracle 외부 DB 뷰 |

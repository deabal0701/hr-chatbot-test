# 데이터베이스 설계

> 최종 수정: 2026-03-09

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
                    │ is_active, is_system │
                    └──────────┬───────────┘
                               │ 1:N
                    ┌──────────┴───────────┐
                    │   tb_department      │
                    ├──────────────────────┤
                    │ dept_id (PK)         │
                    │ parent_dept_id (FK)  │
                    │ tenant_id (FK)       │
                    │ dept_code (UK)       │
                    │ dept_name            │
                    │ depth, sort_order    │
                    └──────────┬───────────┘
                               │ 1:N
┌───────────────┐    ┌────────┴───────────┐ N:1  ┌────────────────────┐
│   tb_menu     │◄───│      tb_user       │─────►│     tb_role        │
├───────────────┤    ├────────────────────┤      ├────────────────────┤
│ menu_id (PK)  │    │ user_id (PK)       │      │ role_id (PK)       │
│ parent_menu_id│    │ login_id (UK)      │      │ role_code (UK)     │
│ menu_code (UK)│    │ email (UK)         │      │ role_name          │
│ menu_name     │    │ password_hash      │      │ scope_level        │
│ menu_type     │    │ display_name       │      │ landing_page       │
│ menu_path     │    │ tenant_id (FK)     │      │ is_system          │
│ depth         │    │ dept_id (FK)       │      │ sort_order         │
│ sort_order    │    │ role_id (FK)       │      └────────────────────┘
└───────┬───────┘    │ is_superuser       │
        │            │ is_active          │
        │ N     1    │ login_fail_count   │
        │  ┌─────────┤ locked_until       │
        └─►│ tb_user_menu   │      ┌────────────────────┐
           │ (핵심 권한)     │      │  tb_user_session   │
           ├────────────────┤      ├────────────────────┤
           │ user_id (PK,FK)│      │ session_id (PK)    │
           │ menu_id (PK,FK)│      │ user_id (FK)       │
           │ can_create     │      │ refresh_token      │
           │ can_read       │      │ expires_at         │
           │ can_update     │      └────────────────────┘
           │ can_delete     │
           │ can_export     │
           │ granted_by (FK)│
           └────────────────┘

┌──────────────────────┐     ┌──────────────────────┐     ┌──────────────────────┐
│     tb_docs          │     │   tb_app_settings    │     │  tb_prompt_history   │
├──────────────────────┤     ├──────────────────────┤     ├──────────────────────┤
│ id (PK)              │     │ id (PK)              │     │ id (PK)              │
│ title                │     │ tenant_id            │     │ category, key        │
│ doc_type             │     │ category, key (UK)   │     │ old_value, new_value │
│ content              │     │ value, value_type    │     │ changed_by           │
│ embedding (vector)   │     │ is_secret            │     │ changed_at           │
│ indexed              │     │ description          │     └──────────────────────┘
│ usage_type           │     └──────────────────────┘
│ tenant_id            │                                  ┌──────────────────────┐
│ chunk_index          │     ┌──────────────────────┐     │   tb_api_history     │
│ total_chunks         │     │     tb_code          │     ├──────────────────────┤
│ content_hash         │     ├──────────────────────┤     │ id (PK)              │
│ context_data (JSONB) │     │ code_id (PK)         │     │ request_id           │
└──────────────────────┘     │ tenant_id            │     │ session_id           │
                             │ code_group           │     │ tenant_id, user_id   │
                             │ code_value, code_name│     │ request_type         │
                             │ sort_order           │     │ question, answer     │
                             │ is_active, is_system │     │ trace_data (JSONB)   │
                             │ metadata (JSONB)     │     │ response_time_ms     │
                             └──────────────────────┘     │ llm_calls_count      │
                                                          │ success              │
                                                          └──────────────────────┘
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

### 3.2 tb_department

| 컬럼 | 타입 | 설명 |
|------|------|------|
| dept_id | BIGSERIAL PK | 부서 ID |
| parent_dept_id | BIGINT FK(self) | 상위 부서 (NULL=루트) |
| tenant_id | BIGINT FK | 소속 테넌트 |
| dept_code | VARCHAR(50) | 부서 코드 (테넌트 내 유니크) |
| dept_name | VARCHAR(200) | 부서명 |
| depth | INT (0) | 트리 깊이 |
| sort_order | INT (0) | 정렬 순서 |
| is_active | BOOLEAN (true) | 활성 여부 |

### 3.3 tb_role

| 컬럼 | 타입 | 설명 |
|------|------|------|
| role_id | BIGSERIAL PK | 역할 ID |
| role_code | VARCHAR(50) UK | GLOBAL / TENANT / DEPT / USER |
| role_name | VARCHAR(100) | 역할명 |
| **scope_level** | **INT (3)** | **데이터 범위 (0=전체, 1=테넌트, 2=부서, 3=본인)** |
| landing_page | VARCHAR(200) | 로그인 후 경로 |
| is_system | BOOLEAN (false) | 시스템 역할 (삭제 불가) |
| **sort_order** | **INT (0)** | **역할 계층 (1=GLOBAL, 2=TENANT, 3=DEPT, 4=USER)** |

### 3.4 tb_user

| 컬럼 | 타입 | 설명 |
|------|------|------|
| user_id | BIGSERIAL PK | 사용자 ID |
| login_id | VARCHAR(100) UK | 로그인 ID |
| email | VARCHAR(255) UK | 이메일 |
| password_hash | VARCHAR(255) | bcrypt 해시 |
| display_name | VARCHAR(100) | 표시 이름 |
| tenant_id | BIGINT FK | 소속 테넌트 |
| **dept_id** | **BIGINT FK** | **소속 부서** |
| role_id | BIGINT FK NOT NULL | 역할 |
| is_superuser | BOOLEAN (false) | RBAC 비상 우회 |
| is_active | BOOLEAN (true) | 활성화 |
| login_fail_count | INT (0) | 로그인 실패 횟수 |
| locked_until | TIMESTAMPTZ | 잠금 해제 시각 |
| landing_page | VARCHAR(200) | 사용자별 랜딩 페이지 (NULL이면 역할 기본값) |
| last_login_at | TIMESTAMPTZ | 최근 로그인 시각 |

### 3.5 tb_user_menu (핵심 권한 테이블)

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

### 3.6 tb_menu

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
| icon | VARCHAR(100) | 아이콘 클래스 |
| is_active | BOOLEAN (true) | 활성 여부 |

### 3.7 tb_docs

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL PK | 문서 ID |
| title | VARCHAR(500) | 제목 |
| doc_type | VARCHAR(50) | 문서 유형 |
| content | TEXT | 본문 |
| embedding | VECTOR(1536) | 벡터 임베딩 |
| indexed | BOOLEAN (false) | 임베딩 완료 여부 |
| embedding_model | VARCHAR(100) | 사용 모델명 |
| usage_type | VARCHAR(20) | rag_knowledge / rag_action |
| tenant_id | BIGINT | 소속 테넌트 |
| parent_doc_id | BIGINT | 청크 원본 문서 ID |
| chunk_index | INT | 청크 인덱스 |
| total_chunks | INT | 전체 청크 수 |
| content_hash | VARCHAR(64) | 중복 체크용 해시 |
| context_data | JSONB | 비임베딩 컨텍스트 (SQL, 스키마 등) |
| metadata | JSONB | 추가 메타데이터 |

> **usage_type 구분**: `rag_knowledge`=문서 Q&A용, `rag_action`=SQL 생성 예제용 (Agent/NL2SQL fewshot)

**인덱스**: IVFFlat(embedding), GIN(metadata), btree(created_at, indexed, usage_type)

### 3.8 tb_api_history

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL PK | ID |
| request_id | VARCHAR(20) | 요청 추적 ID (8자 UUID) |
| session_id | VARCHAR | 세션 ID (NULL=RAG) |
| tenant_id, user_id | BIGINT | 사용자/테넌트 |
| request_type | VARCHAR | agent / nl2sql / rag |
| question | TEXT | 원본 질문 |
| answer | TEXT | 최종 답변 |
| **trace_data** | **JSONB** | **실행 추적 (도구, SQL, 소스 등)** |
| response_time_ms | INT | 응답 시간 |
| llm_calls_count | INT | LLM API 호출 횟수 |
| success | BOOLEAN | 성공 여부 |

> **trace_data 구조**: Agent(steps, tools_used, iteration_count), NL2SQL(sql, sql_result, current_turn, validation_passed), RAG(sources, similarity_scores, chunks_count)

**인덱스**: request_id, session_id, tenant_id, user_id, created_at, request_type, GIN(trace_data)

### 3.9 tb_app_settings

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL PK | ID |
| tenant_id | BIGINT | 테넌트별 설정 (NULL=글로벌) |
| category | VARCHAR(50) | 카테고리 (llm, rag, nl2sql, agent, external_database, prompt 등) |
| key | VARCHAR(100) | 설정 키 |
| value | TEXT | 설정 값 |
| value_type | VARCHAR(20) | string / int / bool |
| is_secret | BOOLEAN (false) | UI에서 숨김 |
| description | TEXT | 설명 |

> **UNIQUE**: (category, key)

### 3.10 tb_code

| 컬럼 | 타입 | 설명 |
|------|------|------|
| code_id | BIGSERIAL PK | 코드 ID |
| tenant_id | BIGINT | 테넌트 |
| code_group | VARCHAR(50) | 코드 분류 |
| code_value | VARCHAR(100) | 코드 값 |
| code_name | VARCHAR(200) | 표시명 |
| metadata | JSONB | 추가 데이터 |
| sort_order | INT | 정렬 순서 |
| is_active | BOOLEAN (true) | 활성 여부 |
| is_system | BOOLEAN (false) | 시스템 코드 (삭제 불가) |

> **UNIQUE**: (code_group, code_value)

### 3.11 tb_prompt_history (설정 변경 감사)

| 컬럼 | 타입 | 설명 |
|------|------|------|
| id | BIGSERIAL PK | ID |
| category | VARCHAR(50) | 설정 카테고리 |
| key | VARCHAR(100) | 설정 키 |
| old_value | TEXT | 변경 전 값 |
| new_value | TEXT | 변경 후 값 |
| changed_by | BIGINT | 변경자 user_id |
| changed_at | TIMESTAMPTZ | 변경 시각 |

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

**풀 설정** (psycopg3 ConnectionPool):

| 항목 | 값 | 설명 |
|------|-----|------|
| min_size | pool_size / 2 | 최소 커넥션 (기본 10) |
| max_size | pool_size | 최대 커넥션 (기본 20) |
| max_idle | 300초 | 유휴 커넥션 타임아웃 |
| max_lifetime | 3600초 | 커넥션 최대 수명 |
| timeout | 30초 | 커넥션 획득 대기 |
| num_workers | 3 | 커넥션 생성 워커 수 |
| row_factory | dict_row | 딕셔너리 반환 |
| timezone | Asia/Seoul | 타임존 설정 |

**pgvector**: 커넥션마다 `register_vector(conn)` 자동 등록

### 5.2 외부 비즈니스 DB

```python
from app.core.database.external import external_db_manager
```

- **Lazy 초기화**: 앱 시작 시 연결 없음, 최초 NL2SQL/Agent 요청 시 커넥션 풀 생성
- **멀티테넌트**: 테넌트별 독립 커넥션 풀 또는 공유 풀(tenant_id=1)
- **Thread-safe**: 더블 체크 락킹
- **설정**: tb_app_settings (external_database 카테고리)에서 동적 로드

**외부 DB 설정 키**:

| 키 | 기본값 | 설명 |
|----|--------|------|
| enabled | true | 외부 DB 활성화 |
| db_type | postgresql | postgresql / oracle |
| host, port, database | - | 접속 정보 |
| schema | business | 스키마명 |
| allowed_tables | employee,department,... | 화이트리스트 테이블 |
| connection_pool_size | 5 | 풀 크기 |
| connection_timeout | 10 | 접속 타임아웃 (초) |

### 5.3 DB 어댑터 패턴

```python
from app.core.database.adapters.factory import get_adapter
adapter = get_adapter("postgresql")  # 또는 "oracle"
```

| 어댑터 | 행 제한 | 스키마 조회 | 타임아웃 |
|--------|---------|-----------|---------|
| PostgreSQL | `LIMIT N` | `information_schema` + `pg_description` | `SET statement_timeout = N` |
| Oracle | `FETCH FIRST N ROWS ONLY` | `ALL_TABLES` + `ALL_VIEWS` + `ALL_COL_COMMENTS` | 미지원 (Resource Manager) |

**주요 어댑터 메서드**:

| 메서드 | 역할 |
|--------|------|
| build_connection_url | 접속 URL 생성 |
| create_pool / close_pool | 풀 관리 |
| get_tables_query / get_columns_query | 스키마 조회 SQL |
| set_timeout | 쿼리 타임아웃 설정 |
| add_limit_clause | LIMIT/FETCH FIRST 자동 추가 |
| get_sql_dialect_name | "PostgreSQL" / "Oracle" |
| row_to_dict | 행 → 딕셔너리 변환 |

**Oracle 특수 처리**:
- `ALTER SESSION SET CURRENT_SCHEMA` (정규식 검증된 식별자만 허용)
- `FROM DUAL` 자동 추가 (스칼라 서브쿼리)
- 컬럼명 소문자 변환 (Oracle은 대문자 반환)

새 DB 추가 시: `adapters/` 하위에 `DatabaseAdapter` 구현 → `factory.py`에 등록

---

## 6. SQL 보안 (sql_executor.py)

| 보안 계층 | 설명 |
|----------|------|
| **키워드 블랙리스트** | DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE, GRANT, REVOKE, EXEC, DECLARE, CURSOR |
| **테이블 화이트리스트** | allowed_tables만 조회 가능, system 테이블(dual) 제외 |
| **SELECT 전용** | sqlparse로 구문 분석 (read_only_mode) |
| **CTE 처리** | WITH절 CTE 이름 추출 → 테이블 화이트리스트에서 제외 (false positive 방지) |
| **LIMIT 검증** | LIMIT/FETCH FIRST 누락 시 어댑터가 자동 추가 |
| **타임아웃** | 30초 (설정 가능) |
| **행 제한** | 1000행 (설정 가능) |

---

## 7. Table Catalog 서비스

NL2SQL schema_retrieval_node에서 LLM에 테이블 메타데이터를 제공한다.

- **파일**: `app/core/database/table_catalog.py`
- **역할**: 테이블별 설명, 컬럼 목록, 키워드, 관계 정보를 캐싱
- **자동 확장**: `get_related_tables()` - FK 관련 테이블 자동 포함

```python
table_info = {
    "description": "직원 기본정보 (메인 테이블)",
    "columns": ["EMP_ID (PK, 조인키)", "EMP_NAME (이름)", ...],
    "keywords": ["직원", "사원", "입사", ...],
    "is_primary": True,
    "join_key": "EMP_ID",
    "relation": "1 (메인)",
    "related_tables": ["v_ai_address"]
}
```

---

## 8. Dynamic Settings 체계

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

설정 변경 시 `tb_prompt_history`에 감사 로그 저장 (old_value → new_value)

---

## 9. SQL DDL 참조

| 파일 | 설명 |
|------|------|
| `docs/sql/psql-hermes_db.sql` | 전체 스키마 + 초기 데이터 |
| `docs/sql/orcl-business_db.sql` | Oracle 외부 DB 뷰 |
| `docs/sql/rag_docs_*.sql` | RAG 문서 데이터 (연차, 복지, 평가 등 10종) |

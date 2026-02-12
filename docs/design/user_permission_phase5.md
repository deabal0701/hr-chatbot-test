# Phase 5 구현 가이드: NL2SQL 권한 필터 주입 (Row-Level Security)

> **문서 버전**: 2.0 (하이브리드 방식)
> **작성일**: 2026-02-12
> **상위 문서**: `docs/design/user_permission_system.md` (섹션 4, 11.2 Phase 5)
> **선행 조건**: Phase 3 완료 (인증 미들웨어 — UserContext), Phase 4 완료 (기존 API 권한 적용)
> **목적**: NL2SQL Row-Level Security — LLM 프롬프트(SQL 품질) + App 필터 주입(보안 보장) 하이브리드 방식

---

## 목차

1. [Phase 5 개요](#1-phase-5-개요)
2. [현재 상태 분석](#2-현재-상태-분석)
3. [Step 1: 비즈니스 DB 스키마 마이그레이션](#3-step-1-비즈니스-db-스키마-마이그레이션)
4. [Step 2: tb_data_filter 초기 데이터 확인](#4-step-2-tb_data_filter-초기-데이터-확인)
5. [Step 3: sql_executor.py — 필터 주입 로직 (보안 계층)](#5-step-3-sql_executor-필터-주입-로직)
6. [Step 4: prompt_build_node — LLM Scope Awareness (품질 계층)](#6-step-4-prompt_build_node-llm-scope-awareness)
7. [Step 5: NL2SQL State + 노드 수정](#7-step-5-nl2sql-state-노드-수정)
8. [Step 6: NL2SQL 서비스/라우트 수정 — UserContext 전파](#8-step-6-nl2sql-서비스-라우트-수정)
9. [Step 7: Agent SQL Tool 수정](#9-step-7-agent-sql-tool-수정)
10. [Step 8: History 미들웨어 수정](#10-step-8-history-미들웨어-수정)
11. [검증 체크리스트](#11-검증-체크리스트)
12. [다음 단계 (Phase 6 Preview)](#12-다음-단계)

---

## 1. Phase 5 개요

### 1.1 무엇을 하는가

Phase 5는 **사용자 권한(scope_type)에 따라 NL2SQL이 생성한 SQL에 자동으로 WHERE 조건을 주입**합니다. 이를 통해 동일한 질문이라도 사용자 역할에 따라 다른 데이터 범위를 보여줍니다.

```
원본 질문: "2024년 입사자 목록 보여줘"

LLM 생성 SQL:
  SELECT e.name, e.hire_date FROM employee e WHERE e.hire_date >= '2024-01-01'

[시스템 관리자 (GLOBAL)] → 변경 없음
  SELECT e.name, e.hire_date FROM employee e WHERE e.hire_date >= '2024-01-01'

[테넌트 관리자 (TENANT, tenant_id=5)] → alias prefix로 tenant_id 조건 추가
  SELECT e.name, e.hire_date FROM employee e WHERE e.hire_date >= '2024-01-01' AND e.tenant_id = 5

[일반 사용자 (USER, tenant_id=5, user_id=123)] → alias prefix로 tenant_id + emp_id 조건 추가
  SELECT e.name, e.hire_date FROM employee e WHERE e.hire_date >= '2024-01-01' AND e.tenant_id = 5 AND e.emp_id = 123
```

### 1.2 핵심 설계 원칙 — 하이브리드 이중 방어

```
┌─────────────────────────────────────────────────────────────────────────┐
│  2-Layer Defense: LLM 프롬프트(SQL 품질) + App 필터 주입(보안 보장)     │
│                                                                         │
│  [1차: SQL 품질] prompt_build_node에 scope 정보 제공                   │
│    → LLM이 자연스럽게 WHERE tenant_id = N 포함한 SQL 생성              │
│    → 더 자연스러운 SQL, JOIN/서브쿼리에서도 적절한 필터 배치           │
│    ⚠ 프롬프트는 "보안"이 아님 — LLM이 빠뜨릴 수 있음                  │
│                                                                         │
│  [2차: 보안 보장] sql_executor에서 필터 강제 주입                      │
│    → SQL 실행 직전에 WHERE 조건 자동 주입                              │
│    → LLM이 빠뜨려도 반드시 적용 — 보안 최후 방어선                    │
│    → tb_data_filter 테이블로 규칙 관리 → 코드 변경 없이 필터 추가     │
│                                                                         │
│  [이중 보호 효과]                                                       │
│    LLM이 잘 추가하면 → AND 중복 (무해, 같은 조건 중복)                │
│    LLM이 빠뜨리면   → App이 추가 (보안 보장)                          │
│                                                                         │
│  GLOBAL scope → 프롬프트 "전체 접근", 필터 주입 없음                   │
│  TENANT scope → 프롬프트 "tenant_id=N", 필터 주입 tenant_id=N         │
│  USER scope   → 프롬프트 "tenant_id=N, emp_id=M", 필터 주입 양쪽     │
└─────────────────────────────────────────────────────────────────────────┘
```

**왜 하이브리드인가?**

| 방식 | 장점 | 한계 |
|------|------|------|
| LLM 프롬프트만 | SQL이 자연스러움, 복잡한 JOIN에서도 적절한 위치에 필터 | LLM이 빠뜨릴 수 있음 (보안 불완전) |
| App 주입만 | 보안 100% 보장, LLM 무관 | UNION/Alias/CTE 등 복잡한 SQL 처리 필요 |
| **하이브리드** | **LLM이 90%+ 자연스럽게 처리, App이 나머지 보장** | 조건 중복 가능 (무해) |

> **핵심 원칙**: 프롬프트는 **SQL 품질 향상**을 위한 것이고, 실제 **보안은 App 주입이 담당**합니다.

### 1.3 산출물

```
수정 파일:
  docs/sql/psql-business_test_db.sql    # tenant_id 컬럼 추가 ALTER
  app/core/database/sql_executor.py     # inject_permission_filter() 메서드 추가 (~100줄) [보안 계층]
  app/graphs/nl2sql/nodes.py            # ① prompt_build_node에 scope 정보 주입 [품질 계층]
                                        # ② execute_sql_node에서 필터 주입 호출 [보안 계층]
  app/graphs/nl2sql/state.py            # NL2SQLState에 user_context 필드 추가
  app/graphs/nl2sql/graph.py            # _prepare_initial_state에 user_context 전달
  app/api/services/nl2sql_service.py    # search()에 user_context 파라미터 추가
  app/api/routes/search.py              # nl2sql_service 호출 시 user_context 전달
  app/graphs/agent/tools/sql_tool.py    # SQL 실행 시 user_context 적용
  app/middleware/history.py             # 헤더 → request.state.current_user 연동
```

---

## 2. 현재 상태 분석

### 2.1 비즈니스 DB 테이블 현황

| 테이블 | tenant_id 컬럼 | 비고 |
|--------|:-:|------|
| `employee` | ❌ 없음 | **마이그레이션 필요** |
| `department` | ❌ 없음 | **마이그레이션 필요** |
| `job_history` | ❌ 없음 | emp_id 기반 간접 필터 가능 |
| `performance_review` | ❌ 없음 | emp_id 기반 간접 필터 가능 |
| `salary` | ❌ 없음 | emp_id 기반 간접 필터 가능 |

> **중요**: 설계 문서(user_permission_system.md)에서 `employee.tenant_id` 컬럼을 가정하지만, 현재 비즈니스 DB에는 존재하지 않습니다. Step 1에서 마이그레이션합니다.

### 2.2 tb_data_filter 테이블

DDL은 `docs/sql/tb_user_permission.sql`에 정의되어 있고, 초기 데이터도 INSERT되어 있습니다:
- TENANT_ADMIN → employee.tenant_id (TENANT 필터)
- USER → employee.emp_id (USER 필터)

### 2.3 sql_executor.py 현황

- `execute_sql(sql, validate=True)` — user_context 파라미터 없음
- `_extract_table_names(sql)` — 이미 테이블명 추출 기능 존재 (재활용)
- `validate_sql(sql)` — DDL/DML 차단, 테이블 화이트리스트 검증

### 2.4 NL2SQL 노드 현황

- `execute_sql_node` — `sql_executor.execute_sql(sql, validate=False)` 직접 호출
- `NL2SQLState` — `user_context` 필드 없음

### 2.5 History 미들웨어 현황

- 헤더 기반으로 tenant_id/user_id 추출 (`X-Tenant-ID`, `X-User-ID`)
- 인증 미들웨어 도입 이후 `request.state.current_user`로 변경 필요

---

## 3. Step 1: 비즈니스 DB 스키마 마이그레이션

### 3.1 employee 테이블에 tenant_id 컬럼 추가

비즈니스 DB(외부 DB)의 `employee`, `department` 테이블에 `tenant_id` 컬럼을 추가합니다.

```sql
-- docs/sql/migration_phase5_tenant_id.sql

-- ==========================================
-- Phase 5: 비즈니스 테이블에 tenant_id 추가
-- ==========================================

-- 1. employee 테이블에 tenant_id 추가
ALTER TABLE employee ADD COLUMN IF NOT EXISTS tenant_id BIGINT;
COMMENT ON COLUMN employee.tenant_id IS '소속 테넌트 ID (NL2SQL 필터용)';
CREATE INDEX IF NOT EXISTS idx_employee_tenant ON employee(tenant_id);

-- 2. department 테이블에 tenant_id 추가
ALTER TABLE department ADD COLUMN IF NOT EXISTS tenant_id BIGINT;
COMMENT ON COLUMN department.tenant_id IS '소속 테넌트 ID (NL2SQL 필터용)';
CREATE INDEX IF NOT EXISTS idx_department_tenant ON department(tenant_id);

-- 3. 기존 데이터 초기화 (기본 테넌트 = DEMO의 tenant_id)
-- ※ 실제 운영 환경에서는 각 테넌트별로 적절히 설정
UPDATE employee SET tenant_id = 2 WHERE tenant_id IS NULL;
UPDATE department SET tenant_id = 2 WHERE tenant_id IS NULL;
```

### 3.2 주의사항

- 이 마이그레이션은 **외부 비즈니스 DB**에 실행합니다 (PostgreSQL 또는 Oracle)
- Oracle의 경우 `ALTER TABLE employee ADD (tenant_id NUMBER(19))` 문법 사용
- 기존 데이터에 `tenant_id = NULL`이면 TENANT 필터 시 조회 누락되므로 초기값 설정 필수

---

## 4. Step 2: tb_data_filter 초기 데이터 확인

### 4.1 현재 INSERT된 필터 규칙 (tb_user_permission.sql)

```
tb_data_filter 초기 데이터:
┌──────────────────┬──────────────┬───────────────┬─────────────┐
│ role_code        │ target_table │ filter_column │ filter_type │
├──────────────────┼──────────────┼───────────────┼─────────────┤
│ TENANT_ADMIN     │ employee     │ tenant_id     │ TENANT      │
│ TENANT_ADMIN     │ tb_user      │ tenant_id     │ TENANT      │
│ USER             │ employee     │ emp_id        │ USER        │
│ USER             │ tb_user      │ user_id       │ USER        │
└──────────────────┴──────────────┴───────────────┴─────────────┘
※ SYSTEM_ADMIN (GLOBAL) → 필터 레코드 없음 → 전체 데이터 접근
```

### 4.2 추가 필요한 필터 규칙

USER 역할에 tenant_id 필터도 추가 (이중 필터: tenant_id + emp_id):

```sql
-- USER 역할: employee 테이블에 tenant_id 필터도 추가
INSERT INTO tb_data_filter (role_id, target_table, filter_column, filter_type)
SELECT r.role_id, 'employee', 'tenant_id', 'TENANT'
FROM tb_role r WHERE r.role_code = 'USER'
ON CONFLICT (role_id, target_table, filter_column) DO NOTHING;
```

### 4.3 필터 적용 로직

```
GLOBAL (SYSTEM_ADMIN):
  → tb_data_filter에 레코드 없음
  → SQL 변경 없음

TENANT (TENANT_ADMIN):
  → employee.tenant_id = {user_context.tenant_id}

USER:
  → employee.tenant_id = {user_context.tenant_id}
  → employee.emp_id = {user_context.user_id}
  (두 조건 모두 AND로 추가)
```

---

## 5. Step 3: sql_executor.py — 필터 주입 로직 (보안 계층)

### 5.1 수정 개요

`SQLExecutorService`에 6개 메서드를 추가합니다:

| 메서드 | 설명 |
|--------|------|
| `inject_permission_filter(sql, user_context)` | 메인 필터 주입 메서드 (UNION 분리 포함) |
| `_get_data_filters(roles)` | tb_data_filter에서 역할별 필터 규칙 조회 |
| `_build_filter_condition(rule, user_context, prefix)` | 필터 규칙 → SQL 조건식 (alias prefix 적용) |
| `_inject_where_condition(sql, conditions)` | SQL segment에 WHERE/AND 조건 추가 |
| `_extract_tables_with_aliases(sql)` | 테이블명 + 별칭(alias) 매핑 추출 |
| `_split_at_union(sql)` | UNION/UNION ALL 경계에서 SQL 분리 |

### 5.2 inject_permission_filter 구현

```python
def inject_permission_filter(self, sql: str, user_context: "UserContext") -> str:
    """
    사용자 권한(scope_type)에 따라 SQL에 WHERE 조건 자동 주입
    UNION 쿼리와 테이블 별칭(alias)을 모두 처리합니다.

    Args:
        sql: LLM이 생성한 원본 SQL
        user_context: 인증된 사용자 컨텍스트

    Returns:
        필터가 적용된 SQL (GLOBAL이면 원본 그대로)

    주입 흐름:
    1. GLOBAL → return sql (변경 없음)
    2. tb_data_filter에서 사용자 역할들의 필터 규칙 조회
    3. UNION 경계에서 SQL 분리
    4. 각 segment에서 테이블명+별칭 추출
    5. alias prefix를 적용한 조건을 WHERE/AND로 추가
    6. segment 재결합
    """
    # 1. GLOBAL scope → 필터 없음
    if user_context.scope_type == "GLOBAL":
        return sql

    # 2. 필터 규칙 조회
    filters = self._get_data_filters(user_context.roles)
    if not filters:
        logger.debug(f"필터 규칙 없음: roles={user_context.roles}")
        return sql

    # 3. UNION 경계에서 분리
    segments = self._split_at_union(sql)

    # 4. 각 segment에 필터 주입
    filtered_segments = []
    for segment_sql, separator in segments:
        filtered_sql = self._inject_filter_to_segment(
            segment_sql, filters, user_context
        )
        filtered_segments.append((filtered_sql, separator))

    # 5. 재결합
    result_parts = []
    for filtered_sql, separator in filtered_segments:
        if separator:
            result_parts.append(separator)
        result_parts.append(filtered_sql)

    return " ".join(result_parts)


def _inject_filter_to_segment(
    self,
    sql: str,
    filters: Dict[str, List[Dict]],
    user_context: "UserContext",
) -> str:
    """
    단일 SELECT segment에 필터 주입

    1. 테이블명 + 별칭 추출 (FROM employee e → {"employee": "e"})
    2. 필터 대상 테이블에 alias prefix 적용한 조건 생성
    3. WHERE/AND로 조건 삽입
    """
    # 1. 테이블명 + 별칭 추출
    table_alias_map = self._extract_tables_with_aliases(sql)

    # 2. 각 테이블에 필터 조건 생성
    all_conditions = []
    for table_name, alias in table_alias_map.items():
        table_lower = table_name.lower()
        if table_lower in filters:
            # prefix: alias가 있으면 alias, 없으면 테이블명
            prefix = alias if alias else table_name
            for filter_rule in filters[table_lower]:
                condition = self._build_filter_condition(
                    filter_rule, user_context, prefix
                )
                if condition:
                    all_conditions.append(condition)

    # 3. 조건 주입
    if all_conditions:
        sql = self._inject_where_condition(sql, all_conditions)

    return sql
```

### 5.3 _get_data_filters 구현

```python
def _get_data_filters(self, role_codes: list) -> Dict[str, List[Dict]]:
    """
    tb_data_filter에서 역할별 필터 규칙 조회

    Args:
        role_codes: 사용자의 역할 코드 목록 (예: ["TENANT_ADMIN"])

    Returns:
        {target_table: [{filter_column, filter_type, filter_sql}, ...]}
    """
    from app.core.database.connection import db_manager

    if not role_codes:
        return {}

    placeholders = ", ".join(["%s"] * len(role_codes))
    query = f"""
        SELECT df.target_table, df.filter_column, df.filter_type, df.filter_sql
        FROM tb_data_filter df
        JOIN tb_role r ON df.role_id = r.role_id
        WHERE r.role_code IN ({placeholders})
        ORDER BY df.target_table, df.filter_type
    """

    filters = {}
    with db_manager.get_cursor() as cur:
        cur.execute(query, role_codes)
        for row in cur.fetchall():
            table = row["target_table"].lower()
            if table not in filters:
                filters[table] = []
            filters[table].append({
                "filter_column": row["filter_column"],
                "filter_type": row["filter_type"],
                "filter_sql": row["filter_sql"],
            })

    return filters
```

### 5.4 _build_filter_condition 구현

```python
def _build_filter_condition(
    self,
    filter_rule: Dict,
    user_context: "UserContext",
    prefix: str,
) -> Optional[str]:
    """
    필터 규칙 + UserContext → SQL 조건식 생성 (alias prefix 적용)

    Args:
        filter_rule: 필터 규칙 딕셔너리
        user_context: 사용자 컨텍스트
        prefix: 테이블 별칭 또는 테이블명 (예: "e" 또는 "employee")

    filter_type별 처리:
    - TENANT: {prefix}.{column} = {tenant_id}
    - USER: {prefix}.{column} = {user_id}
    - CUSTOM: filter_sql에서 {prefix} 치환

    Examples:
        FROM employee e  → prefix="e"  → e.tenant_id = 5
        FROM employee    → prefix="employee" → employee.tenant_id = 5
    """
    filter_type = filter_rule["filter_type"]
    filter_column = filter_rule["filter_column"]

    if filter_type == "TENANT":
        if user_context.tenant_id is None:
            return None
        # prefix.column 형태 → alias 또는 테이블명이 항상 붙어 ambiguous 방지
        # 정수형 파라미터 → SQL Injection 불가
        return f"{prefix}.{filter_column} = {int(user_context.tenant_id)}"

    elif filter_type == "USER":
        if user_context.user_id is None:
            return None
        return f"{prefix}.{filter_column} = {int(user_context.user_id)}"

    elif filter_type == "CUSTOM":
        # filter_sql은 DB 관리자가 직접 입력한 SQL 조건
        filter_sql = filter_rule.get("filter_sql")
        if filter_sql:
            # 변수 치환: {prefix}, {tenant_id}, {user_id}
            return filter_sql.format(
                prefix=prefix,
                tenant_id=int(user_context.tenant_id) if user_context.tenant_id else 0,
                user_id=int(user_context.user_id) if user_context.user_id else 0,
            )
        return None

    return None
```

### 5.5 _inject_where_condition 구현

```python
def _inject_where_condition(
    self,
    sql: str,
    conditions: List[str],
) -> str:
    """
    단일 SELECT segment에 WHERE/AND 조건 추가

    전략:
    - WHERE 절이 있으면 → AND {condition} 추가
    - WHERE 절이 없으면 → WHERE {condition} 삽입
    - GROUP BY/ORDER BY/LIMIT 등 앞에 삽입

    Note: UNION은 이미 _split_at_union으로 분리된 후이므로 end_keywords에 포함 안 함
    """
    if not conditions:
        return sql

    condition_str = " AND ".join(conditions)

    sql_upper = sql.upper()

    # GROUP BY, ORDER BY, LIMIT, HAVING 등 키워드 위치 찾기
    # UNION은 이미 분리 완료 → 여기서는 제외
    end_keywords = ['GROUP BY', 'ORDER BY', 'LIMIT', 'HAVING', 'FETCH FIRST']
    insert_pos = len(sql)

    for kw in end_keywords:
        pos = self._find_keyword_at_depth_zero(sql_upper, kw)
        if pos != -1 and pos < insert_pos:
            insert_pos = pos

    # WHERE 존재 여부 확인 (depth 0)
    where_pos = self._find_keyword_at_depth_zero(sql_upper, 'WHERE')

    if where_pos != -1:
        # WHERE가 있으면: end_keyword 앞에 AND 추가
        sql = sql[:insert_pos].rstrip() + f" AND {condition_str} " + sql[insert_pos:]
    else:
        # WHERE가 없으면: end_keyword 앞에 WHERE 삽입
        sql = sql[:insert_pos].rstrip() + f" WHERE {condition_str} " + sql[insert_pos:]

    return sql
```

### 5.6 _extract_tables_with_aliases 구현

```python
def _extract_tables_with_aliases(self, sql: str) -> Dict[str, Optional[str]]:
    """
    SQL에서 테이블명과 별칭(alias) 매핑 추출

    Returns:
        {table_name_lower: alias_or_none}

    Examples:
        FROM employee             → {"employee": None}
        FROM employee e           → {"employee": "e"}
        FROM employee e JOIN department d ON ...
                                  → {"employee": "e", "department": "d"}
        FROM employee AS emp      → {"employee": "emp"}

    CTE 이름은 제외됩니다 (기존 _extract_cte_names 활용).
    """
    cte_names = self._extract_cte_names(sql)

    parsed = sqlparse.parse(sql)
    if not parsed:
        return {}

    stmt = parsed[0]
    table_alias_map = {}
    from_seen = False
    last_table = None        # 직전에 감지한 테이블명
    as_seen = False          # AS 키워드 감지
    parenthesis_depth = 0
    just_closed_paren = False

    for token in stmt.flatten():
        if token.ttype is sqlparse.tokens.Whitespace:
            continue

        if token.value == '(':
            parenthesis_depth += 1
            just_closed_paren = False
            from_seen = False
            last_table = None
            continue
        elif token.value == ')':
            parenthesis_depth -= 1
            just_closed_paren = True
            continue
        elif just_closed_paren and token.ttype in (sqlparse.tokens.Name, None):
            just_closed_paren = False
            from_seen = False
            last_table = None
            continue

        # FROM/JOIN 키워드 감지
        if token.ttype is sqlparse.tokens.Keyword and token.value.upper() in (
            'FROM', 'JOIN', 'INNER', 'LEFT', 'RIGHT', 'FULL', 'CROSS'
        ):
            from_seen = True
            just_closed_paren = False
            last_table = None
            as_seen = False
            continue

        # AS 키워드 감지
        if token.ttype is sqlparse.tokens.Keyword and token.value.upper() == 'AS':
            if last_table:
                as_seen = True
            continue

        # 테이블명 또는 별칭 감지
        if from_seen and token.ttype in (sqlparse.tokens.Name, None):
            value = token.value.strip()
            if not self._is_valid_table_identifier(value):
                just_closed_paren = False
                continue

            if last_table is None:
                # 첫 번째 식별자 = 테이블명
                last_table = value.lower()
                as_seen = False
            else:
                # 두 번째 식별자 = 별칭 (AS 여부 무관)
                # last_table에 alias 기록
                if last_table not in cte_names:
                    table_alias_map[last_table] = value
                last_table = None
                from_seen = False
                as_seen = False

            just_closed_paren = False
            continue

        # WHERE, GROUP BY 등 → FROM 절 종료
        if token.ttype is sqlparse.tokens.Keyword and token.value.upper() in (
            'WHERE', 'GROUP', 'ORDER', 'LIMIT', 'HAVING', 'ON', 'SET'
        ):
            # 마지막 테이블에 별칭이 없었던 경우 기록
            if last_table and last_table not in cte_names:
                table_alias_map[last_table] = None
            from_seen = False
            last_table = None
            as_seen = False
            just_closed_paren = False
            continue

        # 콤마 → 다중 테이블 (FROM a, b)
        if token.ttype is sqlparse.tokens.Punctuation and token.value == ',':
            if last_table and last_table not in cte_names:
                table_alias_map[last_table] = None
            last_table = None
            as_seen = False
            # from_seen은 유지
            continue

        just_closed_paren = False

    # 루프 종료 후 마지막 테이블 처리
    if last_table and last_table not in cte_names:
        table_alias_map[last_table] = None

    return table_alias_map
```

### 5.7 _split_at_union 구현

```python
def _split_at_union(self, sql: str) -> List[Tuple[str, str]]:
    """
    UNION/UNION ALL 경계에서 SQL 분리 (괄호 깊이 0에서만)

    Args:
        sql: 전체 SQL 문자열

    Returns:
        [(segment, separator), ...]
        첫 번째 segment의 separator는 빈 문자열

    Examples:
        "SELECT ... UNION ALL SELECT ..."
        → [("SELECT ...", ""), ("SELECT ...", "UNION ALL")]

        "SELECT ... UNION SELECT ..."
        → [("SELECT ...", ""), ("SELECT ...", "UNION")]

        "SELECT ..."  (UNION 없음)
        → [("SELECT ...", "")]
    """
    sql_upper = sql.upper()
    segments = []
    depth = 0
    last_cut = 0

    i = 0
    while i < len(sql_upper):
        if sql_upper[i] == '(':
            depth += 1
            i += 1
        elif sql_upper[i] == ')':
            depth -= 1
            i += 1
        elif depth == 0 and sql_upper[i:i + 9] == 'UNION ALL':
            # 단어 경계 확인
            before_ok = (i == 0 or not sql_upper[i - 1].isalnum())
            after_ok = (i + 9 >= len(sql_upper) or not sql_upper[i + 9].isalnum())
            if before_ok and after_ok:
                segment = sql[last_cut:i].strip()
                separator = "" if not segments else segments[-1][1]
                if not segments:
                    segments.append((segment, ""))
                else:
                    segments.append((segment, segments_separator))
                segments_separator = "UNION ALL"
                last_cut = i + 9
                i += 9
                continue
            i += 1
        elif depth == 0 and sql_upper[i:i + 5] == 'UNION':
            # UNION (not UNION ALL) — UNION ALL을 먼저 체크했으므로 여기는 순수 UNION
            before_ok = (i == 0 or not sql_upper[i - 1].isalnum())
            after_ok = (i + 5 >= len(sql_upper) or not sql_upper[i + 5].isalnum())
            if before_ok and after_ok:
                segment = sql[last_cut:i].strip()
                if not segments:
                    segments.append((segment, ""))
                    segments_separator = "UNION"
                else:
                    segments.append((segment, segments_separator))
                    segments_separator = "UNION"
                last_cut = i + 5
                i += 5
                continue
            i += 1
        else:
            i += 1

    # 마지막 segment
    last_segment = sql[last_cut:].strip()
    if segments:
        segments.append((last_segment, segments_separator))
    else:
        segments.append((last_segment, ""))

    return segments
```

### 5.8 _find_keyword_at_depth_zero 구현

```python
def _find_keyword_at_depth_zero(self, sql_upper: str, keyword: str) -> int:
    """괄호 깊이 0에서 키워드 위치 찾기 (서브쿼리 내부 제외)"""
    depth = 0
    kw_len = len(keyword)

    for i in range(len(sql_upper)):
        if sql_upper[i] == '(':
            depth += 1
        elif sql_upper[i] == ')':
            depth -= 1
        elif depth == 0 and sql_upper[i:i + kw_len] == keyword:
            # 단어 경계 확인
            before_ok = (i == 0 or not sql_upper[i - 1].isalnum())
            after_ok = (i + kw_len >= len(sql_upper) or not sql_upper[i + kw_len].isalnum())
            if before_ok and after_ok:
                return i

    return -1
```

### 5.9 보안 고려사항

| 항목 | 대응 |
|------|------|
| SQL Injection | `tenant_id`와 `user_id`는 `int()` 캐스팅으로 숫자만 허용 |
| CUSTOM 필터 | DB 관리자만 입력 가능 (tb_data_filter), 사용자 입력 아님 |
| 테이블 미존재 | `_extract_tables_with_aliases()`로 추출된 테이블만 필터 적용 |
| CTE 쿼리 | CTE 정의부는 무시, 메인 SELECT에만 필터 적용 (기존 `_extract_cte_names` 활용) |
| Alias ambiguity | `{prefix}.{column}` 형태로 항상 prefix 사용 → JOIN 시 컬럼 모호성 방지 |
| UNION 보안 | `_split_at_union`으로 각 SELECT에 개별 필터 적용 → 데이터 노출 방지 |

---

## 6. Step 4: prompt_build_node — LLM Scope Awareness (품질 계층)

### 6.1 목적

LLM이 SQL 생성 시 사용자의 데이터 접근 범위를 인지하도록 **프롬프트에 scope 정보를 주입**합니다. 이를 통해:
- LLM이 `WHERE tenant_id = N` 등을 **자연스럽게** 포함한 SQL을 생성
- JOIN, 서브쿼리 등 복잡한 쿼리에서도 **적절한 위치**에 필터 배치
- App 주입(Step 3)과 겹쳐도 `AND` 중복일 뿐 무해

> **주의**: 이 계층은 보안을 **보장하지 않습니다**. LLM이 프롬프트를 무시할 수 있으므로, Step 3의 App 주입이 반드시 필요합니다.

### 6.2 프롬프트 조립 순서 (변경 후)

```
prompt_parts 조립 순서:
  1. base_prompt         ← 기존 (DB 전문가 역할, 스키마 정보)
  2. permission_context  ← ★ 신규 (데이터 접근 권한 정보)
  3. fewshot_context     ← 기존 (유사 쿼리 예제)
  4. history_context     ← 기존 (멀티턴 대화 이력)
  5. error_context       ← 기존 (재시도 오류 컨텍스트)
```

### 6.3 permission_context 템플릿

```python
def _build_permission_context(self, user_context) -> str:
    """
    사용자 권한 정보를 프롬프트 컨텍스트로 변환

    scope별 프롬프트:
    - GLOBAL: 전체 데이터 접근 (필터 불필요)
    - TENANT: tenant_id 필터 필수
    - USER: tenant_id + emp_id 필터 필수
    """
    if not user_context or not hasattr(user_context, 'scope_type'):
        return ""

    scope = user_context.scope_type

    if scope == "GLOBAL":
        return """
---
## 데이터 접근 권한
현재 사용자는 **시스템 관리자**입니다. 전체 데이터에 접근 가능합니다.
별도의 필터 조건을 추가하지 마세요.
"""

    if scope == "TENANT":
        tenant_id = int(user_context.tenant_id)
        return f"""
---
## 데이터 접근 권한 (중요: 반드시 적용)
현재 사용자는 **테넌트 관리자**입니다.
- tenant_id = {tenant_id} 에 해당하는 데이터만 조회해야 합니다.
- employee, department 등 tenant_id 컬럼이 있는 테이블에는 반드시 `WHERE tenant_id = {tenant_id}` 조건을 포함하세요.
- JOIN 쿼리에서는 각 테이블에 개별적으로 tenant_id 조건을 적용하세요.
"""

    if scope == "USER":
        tenant_id = int(user_context.tenant_id)
        user_id = int(user_context.user_id)
        return f"""
---
## 데이터 접근 권한 (중요: 반드시 적용)
현재 사용자는 **일반 사용자**입니다.
- tenant_id = {tenant_id} 에 해당하는 데이터만 조회해야 합니다.
- employee 테이블 조회 시 반드시 `WHERE emp_id = {user_id}` 조건을 포함하세요.
- JOIN 쿼리에서는 employee.emp_id = {user_id} AND employee.tenant_id = {tenant_id} 조건을 적용하세요.
"""

    return ""
```

### 6.4 prompt_build_node 수정 (`app/graphs/nl2sql/nodes.py`)

```python
def prompt_build_node(state: Dict[str, Any]) -> Dict[str, Any]:
    # ... 기존 코드 ...

    # Base 프롬프트 로드
    base_prompt = prompt_service.get_nl2sql_generation_prompt(schema_description, db_type)

    # 프롬프트 조립
    prompt_parts = [base_prompt]

    # ★ Phase 5: 권한 컨텍스트 추가 (base_prompt 직후, fewshot 이전)
    user_context = state.get("user_context")
    if user_context:
        permission_context = _build_permission_context(user_context)
        if permission_context:
            prompt_parts.append(permission_context)

    # Few-shot 예제 추가 (기존)
    if fewshot_context:
        prompt_parts.append("\n---\n")
        prompt_parts.append(fewshot_context)

    # 이전 대화 이력 컨텍스트 추가 (기존)
    # ... 기존 코드 유지 ...

    # 재시도 시 이전 오류 컨텍스트 추가 (기존)
    # ... 기존 코드 유지 ...

    # prompt_metadata에 scope 정보 추가
    prompt_metadata = {
        # ... 기존 필드 유지 ...
        "scope_type": user_context.scope_type if user_context else None,  # ← Phase 5 추가
        "has_permission_context": bool(user_context),                     # ← Phase 5 추가
    }
```

### 6.5 하이브리드 이중 방어 동작 예시

```
질문: "2024년 입사자 목록 보여줘"
사용자: TENANT scope (tenant_id=5)

[1차: LLM 프롬프트]
  프롬프트에 "tenant_id = 5 데이터만 조회" 포함
  → LLM 생성 SQL:
    SELECT e.name, e.hire_date
    FROM employee e
    WHERE e.hire_date >= '2024-01-01' AND e.tenant_id = 5
    ↑ LLM이 프롬프트 보고 자연스럽게 추가

[2차: App 주입] (execute_sql_node → inject_permission_filter)
  → tb_data_filter 조회: employee.tenant_id = TENANT
  → 조건 추가 시도: e.tenant_id = 5
  → 결과 SQL:
    SELECT e.name, e.hire_date
    FROM employee e
    WHERE e.hire_date >= '2024-01-01' AND e.tenant_id = 5 AND e.tenant_id = 5
    ↑ 중복이지만 무해 (DB 옵티마이저가 자동 제거)

만약 LLM이 프롬프트를 무시했다면:
  LLM 생성 SQL:
    SELECT e.name, e.hire_date
    FROM employee e
    WHERE e.hire_date >= '2024-01-01'
  → App 주입 결과:
    SELECT e.name, e.hire_date
    FROM employee e
    WHERE e.hire_date >= '2024-01-01' AND e.tenant_id = 5
    ↑ App 주입이 보안 보장
```

---

## 7. Step 5: NL2SQL State + 노드 수정

### 7.1 NL2SQLState 필드 추가 (`app/graphs/nl2sql/state.py`)

```python
# ===== Phase 5: 사용자 권한 필드 =====
user_context: Optional[Any]           # UserContext (인증된 사용자, None=미인증)
```

`create_initial_state()`에도 `user_context` 파라미터 추가:
```python
def create_initial_state(
    question: str,
    request_id: str = "unknown",
    max_retries: int = 2,
    session_id: str = "",
    max_turns: int = 5,
    user_context: Any = None,       # ← 추가
) -> NL2SQLState:
    return NL2SQLState(
        # ... 기존 필드 ...
        user_context=user_context,   # ← 추가
    )
```

> **Type 설명**: `Optional[Any]`를 사용하는 이유 — TypedDict에서 `UserContext` 직접 import 시 순환 참조 가능성. 런타임에서는 실제 `UserContext` 인스턴스가 전달됩니다.

### 7.2 execute_sql_node 수정 (`app/graphs/nl2sql/nodes.py`)

```python
def execute_sql_node(state: Dict[str, Any]) -> Dict[str, Any]:
    sql = state["generated_sql"]
    request_id = state.get("request_id", "unknown")
    user_context = state.get("user_context")  # ← Phase 5 추가

    log_step(logger, request_id, "NL2SQL", "3", "EXECUTE", "SQL 실행 시작")

    try:
        # Phase 5: 권한 필터 주입
        original_sql = sql
        if user_context and hasattr(user_context, 'scope_type'):
            sql = sql_executor.inject_permission_filter(sql, user_context)
            if sql != original_sql:
                log_step(logger, request_id, "NL2SQL", "3", "FILTER", "권한 필터 적용", scope=user_context.scope_type)

        result = sql_executor.execute_sql(sql, validate=False)
        state["sql_result"] = result
        state["metadata"]["execution_time_ms"] = result.execution_time_ms
        state["metadata"]["row_count"] = result.row_count
        state["metadata"]["filtered_sql"] = sql if sql != original_sql else None  # 디버깅용

        log_step(logger, request_id, "NL2SQL", "3", "EXECUTE", "SQL 실행 완료", row_count=result.row_count, execution_time_ms=result.execution_time_ms)

    except (SQLExecutionError, SQLValidationError) as e:
        log_step(logger, request_id, "NL2SQL", "3", "ERROR", f"SQL 실행 실패: {e}", level="ERROR")
        state["validation_error"] = str(e)
        state["validated"] = False

    return state
```

---

## 8. Step 6: NL2SQL 서비스/라우트 수정 — UserContext 전파

### 8.1 전파 경로

```
search.py (라우트)
  → current_user (Depends(get_optional_user))
  → nl2sql_service.search(query, session_id, request_id, user_context=current_user)
    → _prepare_inputs(query, session_id, request_id, user_context)
      → {"question": ..., "user_context": current_user}
        → nl2sql_graph.ainvoke(inputs)
          → _prepare_initial_state(inputs, session_id)
            → create_initial_state(..., user_context=inputs.get("user_context"))
              → execute_sql_node(state) ← state["user_context"] 사용
```

### 8.2 nl2sql_service.py 수정

```python
async def search(
    self,
    query: str,
    session_id: Optional[str] = None,
    request_id: str = "unknown",
    user_context: Any = None,          # ← Phase 5 추가
) -> SearchResponse:
    inputs = self._prepare_inputs(query, session_id, request_id, user_context)
    response = await nl2sql_graph.ainvoke(inputs)
    return response


async def search_stream(
    self,
    query: str,
    session_id: Optional[str] = None,
    request_id: str = "unknown",
    user_context: Any = None,          # ← Phase 5 추가
) -> AsyncGenerator[str, None]:
    inputs = self._prepare_inputs(query, session_id, request_id, user_context)
    async for event in nl2sql_graph.astream_events(inputs):
        yield event


def _prepare_inputs(
    self,
    query: str,
    session_id: Optional[str],
    request_id: str,
    user_context: Any = None,          # ← Phase 5 추가
) -> Dict[str, Any]:
    return {
        "question": query,
        "session_id": session_id,
        "request_id": request_id,
        "user_context": user_context,  # ← Phase 5 추가
    }
```

### 8.3 search.py (라우트) 수정

```python
# search() 함수 내 NL2SQL 서비스 호출 부분
if query_type == "nl2sql":
    response = await nl2sql_service.search(
        query=search_request.query,
        session_id=search_request.session_id,
        request_id=request_id,
        user_context=current_user,  # ← Phase 5 추가
    )

# search_stream() 함수도 동일 패턴
async for event in nl2sql_service.search_stream(
    query=search_request.query,
    session_id=search_request.session_id,
    request_id=request_id,
    user_context=current_user,  # ← Phase 5 추가
):
    yield event
```

### 8.4 graph.py (_prepare_initial_state) 수정

```python
def _prepare_initial_state(self, inputs: Dict[str, Any], session_id: str) -> NL2SQLState:
    # ... 기존 코드 ...

    initial_state = create_initial_state(
        question=inputs["question"],
        request_id=inputs.get("request_id", "unknown"),
        max_retries=inputs.get("max_retries", 2),
        session_id=session_id,
        max_turns=max_turns,
        user_context=inputs.get("user_context"),  # ← Phase 5 추가
    )

    # 기존 conversation_history 복원
    initial_state["conversation_history"] = existing_history

    return initial_state
```

---

## 9. Step 7: Agent SQL Tool 수정

### 9.1 수정 개요

Agent의 SQL Tool(`query_database_tool`)도 SQL 실행 시 UserContext를 적용해야 합니다.

**문제**: LangChain `@tool` 데코레이터는 함수 시그니처가 고정됨 → `user_context`를 직접 파라미터로 받기 어려움

**해결**: Agent 상태(`AgentState`)에 `user_context`를 저장하고, SQL Tool이 실행될 때 전역/스레드-로컬에서 읽어오는 방식

### 9.2 AgentState에 user_context 추가 (`app/graphs/agent/state.py`)

```python
# ===== Phase 5: 사용자 권한 =====
user_context: Optional[Any]           # UserContext (인증된 사용자)
```

### 9.3 sql_tool.py 수정

`_execute_enhanced()` 메서드에서 SQL 실행 전 필터 주입:

```python
# 5. SQL 실행 (Phase 5: 필터 주입)
try:
    # user_context가 있으면 필터 주입
    user_context = kwargs.get("user_context")
    if user_context:
        sql = sql_executor.inject_permission_filter(sql, user_context)

    result = sql_executor.execute_sql(sql, validate=True)
```

### 9.4 agent_service.py에서 user_context 전달

```python
# agent_service.search() 메서드
initial_state = create_initial_state(
    question=question,
    session_id=session_id,
    request_id=request_id,
    user_context=user_context,  # ← Phase 5 추가
)
```

> **Note**: Agent의 `@tool` 함수에서 user_context를 직접 접근하기 어려운 경우, `tools_node`에서 state의 user_context를 추출하여 tool 호출 시 전달하는 방식을 사용합니다. 이 부분은 구현 시 Agent 아키텍처에 맞게 조정합니다.

---

## 10. Step 8: History 미들웨어 수정

### 10.1 변경 내용 (`app/middleware/history.py`)

```python
# 변경 전 (헤더에서 직접 읽기 — 위변조 가능)
tenant_id = request.headers.get("X-Tenant-ID")
user_id = request.headers.get("X-User-ID")
user_name = request.headers.get("X-User-Name")

# 변경 후 (인증된 UserContext에서 읽기, 미인증 시 헤더 fallback)
current_user = getattr(request.state, "current_user", None)
if current_user:
    tenant_id = str(current_user.tenant_id) if current_user.tenant_id else None
    user_id = str(current_user.user_id)
    user_name = current_user.display_name or current_user.login_id
else:
    # Phase 3a: 미인증 호환 — 기존 헤더 방식 유지
    tenant_id = request.headers.get("X-Tenant-ID")
    user_id = request.headers.get("X-User-ID")
    user_name = request.headers.get("X-User-Name")
```

### 10.2 변경 의도

- 인증된 사용자: `request.state.current_user`에서 **검증된** 정보 사용 (위변조 불가)
- 미인증 사용자 (Phase 3a): 기존 헤더 방식 유지 (하위호환)
- Phase 3b(필수 인증) 전환 시 헤더 fallback 제거

---

## 11. 검증 체크리스트

### 11.1 단위 테스트 (`tests/test_phase5.py`)

| 테스트 | 설명 |
|--------|------|
| `test_inject_filter_global` | GLOBAL scope → SQL 변경 없음 |
| `test_inject_filter_tenant` | TENANT scope → `AND e.tenant_id = N` 추가 |
| `test_inject_filter_user` | USER scope → `AND e.tenant_id = N AND e.emp_id = M` 추가 |
| `test_inject_filter_no_where` | WHERE 절 없는 SQL → `WHERE employee.tenant_id = N` 삽입 |
| `test_inject_filter_with_where` | WHERE 절 있는 SQL → `AND e.tenant_id = N` 추가 |
| `test_inject_filter_alias` | `FROM employee e` → `e.tenant_id = N` (alias prefix 사용) |
| `test_inject_filter_alias_as` | `FROM employee AS e` → `e.tenant_id = N` |
| `test_inject_filter_no_alias` | `FROM employee` → `employee.tenant_id = N` (테이블명 prefix) |
| `test_inject_filter_join_alias` | JOIN + alias → 양쪽 테이블에 alias prefix 필터 |
| `test_inject_filter_union` | UNION 쿼리 → 각 SELECT segment에 개별 필터 적용 |
| `test_inject_filter_union_all` | UNION ALL → 각 SELECT segment에 개별 필터 적용 |
| `test_inject_filter_subquery` | 서브쿼리 → 메인 쿼리에만 필터 적용 |
| `test_inject_filter_group_by` | GROUP BY 앞에 필터 조건 삽입 |
| `test_inject_filter_cte` | CTE 쿼리 → 메인 SELECT에만 필터 적용 |
| `test_inject_filter_no_match` | 필터 대상 테이블 없는 SQL → 변경 없음 |
| `test_inject_filter_unauthenticated` | user_context=None → SQL 변경 없음 |

### 11.2 통합 테스트

| 테스트 | 설명 |
|--------|------|
| NL2SQL + GLOBAL | 관리자로 NL2SQL 검색 → 전체 데이터 반환 |
| NL2SQL + TENANT | 테넌트 관리자로 검색 → 해당 테넌트 데이터만 |
| NL2SQL + USER | 일반 사용자로 검색 → 본인 데이터만 |
| NL2SQL + TENANT (프롬프트) | 프롬프트에 "tenant_id = N" 포함 확인 (로그 검증) |
| NL2SQL 이중 방어 | LLM이 필터 포함/미포함 양쪽 모두 올바른 결과 |
| Agent SQL Tool + TENANT | Agent 검색 → SQL Tool이 필터 적용 |
| History 저장 | 인증 사용자 → tenant_id/user_id 올바르게 저장 |

### 11.3 프롬프트 품질 테스트 (LLM Scope Awareness)

| 테스트 | 설명 |
|--------|------|
| `test_prompt_global_scope` | GLOBAL → "전체 데이터 접근" 문구 포함, 필터 조건 없음 |
| `test_prompt_tenant_scope` | TENANT → "tenant_id = N" 문구 포함 |
| `test_prompt_user_scope` | USER → "tenant_id = N" + "emp_id = M" 문구 포함 |
| `test_prompt_no_context` | user_context=None → permission_context 없음 (기존 동작) |
| `test_prompt_position` | permission_context가 base_prompt 뒤, fewshot 앞에 위치 |
| `test_prompt_metadata` | prompt_metadata에 scope_type, has_permission_context 포함 |

### 11.4 엣지 케이스

| 케이스 | 기대 동작 | Phase 5 지원 |
|--------|----------|:-:|
| CTE(WITH) 쿼리 | CTE 정의부 무시, 메인 SELECT에 필터 | ✅ |
| UNION/UNION ALL | 각 SELECT segment에 개별 필터 적용 | ✅ |
| 테이블 별칭 사용 | `FROM employee e` → `e.tenant_id = N` (alias prefix) | ✅ |
| AS 키워드 별칭 | `FROM employee AS e` → `e.tenant_id = N` | ✅ |
| 별칭 없는 단일 테이블 | `FROM employee` → `employee.tenant_id = N` | ✅ |
| JOIN + 별칭 | `employee e JOIN department d` → `e.tenant_id=N AND d.tenant_id=N` | ✅ |
| 필터 대상 없는 테이블 | department만 조회 + tb_data_filter에 규칙 없음 → 무필터 | ✅ |
| 서브쿼리 내 테이블 | 서브쿼리 내부 테이블은 depth>0이므로 메인 필터 미적용 | ✅ |

**예시: JOIN + Alias**
```sql
-- 원본 (LLM 생성)
SELECT e.name, d.dept_name
FROM employee e
JOIN department d ON e.dept_id = d.dept_id
WHERE e.hire_date >= '2024-01-01'

-- TENANT 필터 적용 후 (tenant_id=5)
SELECT e.name, d.dept_name
FROM employee e
JOIN department d ON e.dept_id = d.dept_id
WHERE e.hire_date >= '2024-01-01' AND e.tenant_id = 5 AND d.tenant_id = 5
```

**예시: UNION ALL**
```sql
-- 원본 (LLM 생성)
SELECT name FROM employee WHERE dept_id = 10
UNION ALL
SELECT name FROM employee WHERE dept_id = 20

-- TENANT 필터 적용 후 (tenant_id=5)
SELECT name FROM employee WHERE dept_id = 10 AND employee.tenant_id = 5
UNION ALL
SELECT name FROM employee WHERE dept_id = 20 AND employee.tenant_id = 5
```

---

## 12. 다음 단계 (Phase 6 Preview)

Phase 5 완료 후 **Phase 6: 프론트엔드 인증 통합**을 진행합니다.

| 작업 | 설명 |
|------|------|
| `LoginView.vue` | 로그인 화면 구현 |
| `auth.js` (API) | 인증 API 클라이언트 |
| `auth.js` (Store) | Vuex 인증 상태 관리 |
| `index.js` (Router) | 라우터 가드 활성화 (미인증 → /login) |
| `index.js` (Axios) | Authorization 헤더 자동 추가, 401 시 토큰 갱신 |
| `UsersView.vue` | 사용자 관리 화면 |
| `RolesView.vue` | 역할 관리 화면 |
| `TenantsView.vue` | 테넌트 관리 화면 |
| Phase 3a → 3b 전환 | `get_optional_user` → `get_current_active_user`로 변경 |

---

## 부록: 파일 수정 의존 관계

```
순서 제약:
  Step 1 (DB 마이그레이션)    → Step 2 (데이터 확인) → Step 3 (sql_executor 보안계층)
  Step 3 (sql_executor)       → Step 5 (NL2SQL State+노드) → Step 6 (서비스/라우트)
  Step 4 (prompt_build 품질계층) → Step 5 (NL2SQL State+노드) — Step 3과 병렬 가능
  Step 3 (sql_executor)       → Step 7 (Agent SQL Tool) — Step 6과 병렬 가능
  Step 8 (History 미들웨어)   → 독립 (병렬 가능)

병렬 가능 작업:
  [Step 3 + Step 4] — 독립적으로 병렬 진행 가능 (보안계층 + 품질계층)
  [Step 6 + Step 7 + Step 8] — 모두 Step 5 완료 후 병렬 진행 가능
```

```
파일별 import 의존 (순환 없음):
  sql_executor.py     → db_manager, UserContext (타입만)
  state.py            → (추가 의존 없음)
  nodes.py            → sql_executor, prompt_service, UserContext (타입만)
  graph.py            → state, nodes
  nl2sql_service.py   → graph
  search.py           → nl2sql_service, dependencies
  sql_tool.py         → sql_executor
  history.py          → (추가 의존 없음)
```

```
하이브리드 이중 방어 흐름 (전체):

  사용자 질문
    → search.py (UserContext 추출)
      → nl2sql_service (user_context 전달)
        → NL2SQLState (user_context 저장)
          → prompt_build_node [1차: 품질계층]
            → LLM에 scope 정보 제공 → SQL에 필터 자연스럽게 포함
          → sql_generate_node → validate_sql_node
          → execute_sql_node [2차: 보안계층]
            → inject_permission_filter() → 필터 강제 주입
          → sql_executor.execute_sql()
```

# Phase 5 구현 가이드: NL2SQL 권한 필터 주입 (Row-Level Security)

> **문서 버전**: 3.0 (v2.0 메뉴 기반 체계 반영)
> **작성일**: 2026-02-13
> **상위 문서**: `docs/design/user_permission_system.md` (v2.0)
> **선행 조건**: Phase 3 완료 (인증 미들웨어 — UserContext), Phase 4 완료 (관리 API)
> **목적**: NL2SQL Row-Level Security — LLM 프롬프트(SQL 품질) + App 필터 주입(보안 보장) 하이브리드 방식

---

## 목차

1. [Phase 5 개요](#1-phase-5-개요)
2. [현재 상태 분석](#2-현재-상태-분석)
3. [Step 1: 비즈니스 DB 스키마 마이그레이션](#3-step-1-비즈니스-db-스키마-마이그레이션)
4. [Step 2: sql_executor.py — 필터 주입 로직 (보안 계층)](#4-step-2-sql_executor-필터-주입-로직)
5. [Step 3: prompt_build_node — LLM Scope Awareness (품질 계층)](#5-step-3-prompt_build_node-llm-scope-awareness)
6. [Step 4: NL2SQL State + 노드 수정](#6-step-4-nl2sql-state-노드-수정)
7. [Step 5: NL2SQL 서비스/라우트 수정 — UserContext 전파](#7-step-5-nl2sql-서비스-라우트-수정)
8. [Step 6: Agent SQL Tool 수정](#8-step-6-agent-sql-tool-수정)
9. [Step 7: History 미들웨어 수정](#9-step-7-history-미들웨어-수정)
10. [검증 체크리스트](#10-검증-체크리스트)
11. [다음 단계 (Phase 6 Preview)](#11-다음-단계)

---

## 1. Phase 5 개요

### 1.1 무엇을 하는가

Phase 5는 **사용자의 역할(scope_type)에 따라 NL2SQL이 생성한 SQL에 자동으로 WHERE 조건을 주입**합니다. 동일한 질문이라도 사용자 역할에 따라 보이는 데이터 범위가 달라집니다.

```
원본 질문: "2024년 입사자 목록 보여줘"

LLM 생성 SQL:
  SELECT e.name, e.hire_date FROM employee e WHERE e.hire_date >= '2024-01-01'

[시스템 관리자 (GLOBAL)] → 변경 없음
  SELECT e.name, e.hire_date FROM employee e WHERE e.hire_date >= '2024-01-01'

[테넌트 관리자 (TENANT, tenant_id=5)] → tenant_id 조건 추가
  SELECT e.name, e.hire_date FROM employee e WHERE e.hire_date >= '2024-01-01' AND e.tenant_id = 5

[일반 사용자 (USER, tenant_id=5, user_id=123)] → tenant_id + emp_id 조건 추가
  SELECT e.name, e.hire_date FROM employee e WHERE e.hire_date >= '2024-01-01' AND e.tenant_id = 5 AND e.emp_id = 123
```

### 1.2 v2.0 설계 핵심 — scope_type 코드 기반 필터

> **v2.0 변경**: `tb_data_filter` 테이블 삭제.
> `tb_role.scope_type` 값만으로 서비스 레이어에서 WHERE 조건을 코드로 유도합니다.

```
┌─────────────────────────────────────────────────────────────────────────┐
│  v2.0 필터 결정 체계                                                      │
│                                                                           │
│  tb_user.role_id (FK, 1:N)                                               │
│    → tb_role.scope_type (GLOBAL / TENANT / USER)                         │
│      → 서비스 레이어에서 scope_type 읽어 WHERE 조건 코드로 유도            │
│                                                                           │
│  GLOBAL → 필터 없음                                                       │
│  TENANT → WHERE tenant_id = {user_context.tenant_id}                     │
│  USER   → WHERE tenant_id = {user_context.tenant_id}                     │
│              AND emp_id = {user_context.user_id}                         │
│                                                                           │
│  ※ tb_data_filter 테이블 없음 — 필터 규칙은 코드에서 scope_type으로 유도  │
│  ※ 사용자 1명 = 역할 1개 (tb_user.role_id FK) → scope_type 결정이 단순   │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.3 하이브리드 이중 방어

```
┌─────────────────────────────────────────────────────────────────────────┐
│  2-Layer Defense: LLM 프롬프트(SQL 품질) + App 필터 주입(보안 보장)       │
│                                                                           │
│  [1차: SQL 품질] prompt_build_node에 scope 정보 제공                     │
│    → LLM이 자연스럽게 WHERE tenant_id = N 포함한 SQL 생성                │
│    → JOIN/서브쿼리에서도 적절한 필터 배치                                │
│    ⚠ 프롬프트는 "보안"이 아님 — LLM이 빠뜨릴 수 있음                    │
│                                                                           │
│  [2차: 보안 보장] sql_executor에서 필터 강제 주입                        │
│    → SQL 실행 직전에 WHERE 조건 자동 주입                                │
│    → LLM이 빠뜨려도 반드시 적용 — 보안 최후 방어선                      │
│    → scope_type으로 규칙 결정 → 코드 변경 없이 역할만 설정하면 적용      │
│                                                                           │
│  [이중 보호 효과]                                                         │
│    LLM이 잘 추가하면 → AND 중복 (무해, DB 옵티마이저가 자동 처리)       │
│    LLM이 빠뜨리면   → App이 추가 (보안 보장)                            │
│                                                                           │
│  GLOBAL scope → 프롬프트 "전체 접근", 필터 주입 없음                     │
│  TENANT scope → 프롬프트 "tenant_id=N", 필터 주입 tenant_id=N           │
│  USER scope   → 프롬프트 "tenant_id=N, emp_id=M", 필터 주입 양쪽       │
└─────────────────────────────────────────────────────────────────────────┘
```

**왜 하이브리드인가?**

| 방식 | 장점 | 한계 |
|------|------|------|
| LLM 프롬프트만 | SQL이 자연스러움, 복잡한 JOIN에서도 적절한 위치에 필터 | LLM이 빠뜨릴 수 있음 (보안 불완전) |
| App 주입만 | 보안 100% 보장, LLM 무관 | UNION/Alias/CTE 등 복잡한 SQL 처리 필요 |
| **하이브리드** | **LLM이 90%+ 자연스럽게 처리, App이 나머지 보장** | 조건 중복 가능 (무해) |

### 1.4 산출물

```
수정 파일:
  docs/sql/migration_phase5_tenant_id.sql     # tenant_id 컬럼 추가 ALTER
  app/core/database/sql_executor.py           # inject_permission_filter() 추가 [보안 계층]
  app/graphs/nl2sql/nodes.py                  # ① prompt_build_node에 scope 주입 [품질 계층]
                                              # ② execute_sql_node에서 필터 주입 [보안 계층]
  app/graphs/nl2sql/state.py                  # NL2SQLState에 user_context 필드 추가
  app/graphs/nl2sql/graph.py                  # _prepare_initial_state에 user_context 전달
  app/api/services/nl2sql_service.py          # search()에 user_context 파라미터 추가
  app/api/routes/search.py                    # nl2sql_service 호출 시 user_context 전달
  app/graphs/agent/tools/sql_tool.py          # SQL 실행 시 user_context 적용
  app/graphs/agent/state.py                   # AgentState에 user_context 필드 추가
  app/middleware/history.py                   # request.state.current_user 연동
```

---

## 2. 현재 상태 분석

### 2.1 v2.0 인증/권한 체계 (Phase 1~4 완료 가정)

| 항목 | v2.0 상태 |
|------|-----------|
| 사용자-역할 | `tb_user.role_id` FK (1:N, 사용자 1명 = 역할 1개) |
| 역할 | `tb_role.scope_type` (GLOBAL / TENANT / USER) |
| 권한 체크 | `tb_user_menu` (사용자별 메뉴 CRUD 권한) |
| JWT 페이로드 | `role_code`, `scope_type`, `tenant_id` 포함 |
| UserContext | `scope_type`, `tenant_id`, `role_code` 필드 보유 |

> **Phase 5에서 사용하는 UserContext 필드**:
> - `scope_type`: 데이터 범위 결정 (GLOBAL / TENANT / USER)
> - `tenant_id`: 테넌트 필터 값 (TENANT, USER scope에서 사용)
> - `user_id`: 사용자 필터 값 (USER scope에서 사용)

### 2.2 비즈니스 DB 테이블 현황

| 테이블 | tenant_id 컬럼 | 비고 |
|--------|:-:|------|
| `employee` | ❌ 없음 | **마이그레이션 필요** |
| `department` | ❌ 없음 | **마이그레이션 필요** |
| `job_history` | ❌ 없음 | emp_id 기반 간접 필터 가능 |
| `performance_review` | ❌ 없음 | emp_id 기반 간접 필터 가능 |
| `salary` | ❌ 없음 | emp_id 기반 간접 필터 가능 |

### 2.3 sql_executor.py 현황

- `execute_sql(sql, validate=True)` — user_context 파라미터 없음
- `_extract_table_names(sql)` — 테이블명 추출 기능 존재 (재활용)
- `validate_sql(sql)` — DDL/DML 차단, 테이블 화이트리스트 검증

### 2.4 NL2SQL 노드/상태 현황

- `execute_sql_node` — `sql_executor.execute_sql(sql, validate=False)` 직접 호출
- `NL2SQLState` — `user_context` 필드 없음
- `AgentState` — `user_context` 필드 없음

---

## 3. Step 1: 비즈니스 DB 스키마 마이그레이션

### 3.1 employee/department 테이블에 tenant_id 추가

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

- 이 마이그레이션은 **외부 비즈니스 DB**에 실행 (PostgreSQL 또는 Oracle)
- Oracle의 경우 `ALTER TABLE employee ADD (tenant_id NUMBER(19))` 문법 사용
- 기존 데이터에 `tenant_id = NULL`이면 TENANT 필터 시 조회 누락 → 초기값 설정 필수

### 3.3 필터 대상 테이블 매핑

v2.0에서는 `tb_data_filter` 테이블 대신 **코드에서 직접 필터 대상을 정의**합니다.

```python
# sql_executor.py 내부 상수
# scope_type별 필터 대상 테이블과 컬럼 매핑
SCOPE_FILTER_RULES = {
    "TENANT": [
        {"table": "employee",   "column": "tenant_id", "value_field": "tenant_id"},
        {"table": "department", "column": "tenant_id", "value_field": "tenant_id"},
    ],
    "USER": [
        {"table": "employee",   "column": "tenant_id", "value_field": "tenant_id"},
        {"table": "employee",   "column": "emp_id",    "value_field": "user_id"},
        {"table": "department", "column": "tenant_id", "value_field": "tenant_id"},
    ],
    # GLOBAL: 필터 없음 → 여기에 정의하지 않음
}
```

> **v1.0 vs v2.0 차이**:
> - v1.0: `tb_data_filter` 테이블에서 역할별 필터 규칙 조회 (런타임 DB 쿼리)
> - v2.0: `SCOPE_FILTER_RULES` 상수에서 scope_type별 규칙 결정 (DB 조회 없음)
> - 장점: DB 조회 1회 감소, 로직 단순화, 필터 규칙이 코드에 명시적으로 존재

---

## 4. Step 2: sql_executor.py — 필터 주입 로직 (보안 계층)

### 4.1 수정 개요

`SQLExecutorService`에 필터 주입 관련 메서드를 추가합니다.

| 메서드 | 설명 |
|--------|------|
| `inject_permission_filter(sql, user_context)` | 메인 필터 주입 (UNION 분리 포함) |
| `_get_scope_filter_conditions(sql_segment, user_context)` | scope_type → SQL 조건식 목록 생성 |
| `_inject_where_condition(sql, conditions)` | SQL segment에 WHERE/AND 조건 추가 |
| `_extract_tables_with_aliases(sql)` | 테이블명 + 별칭(alias) 매핑 추출 |
| `_split_at_union(sql)` | UNION/UNION ALL 경계에서 SQL 분리 |
| `_find_keyword_at_depth_zero(sql, keyword)` | 괄호 깊이 0에서 키워드 위치 탐색 |

### 4.2 SCOPE_FILTER_RULES 상수 + inject_permission_filter 구현

```python
from typing import Dict, List, Optional, Tuple

# ===== Phase 5: scope_type별 필터 규칙 (코드 기반) =====
# tb_data_filter 테이블 대신 코드에서 직접 정의
# value_field: UserContext의 어떤 필드 값을 사용할지
SCOPE_FILTER_RULES: Dict[str, List[Dict[str, str]]] = {
    "TENANT": [
        {"table": "employee",   "column": "tenant_id", "value_field": "tenant_id"},
        {"table": "department", "column": "tenant_id", "value_field": "tenant_id"},
    ],
    "USER": [
        {"table": "employee",   "column": "tenant_id", "value_field": "tenant_id"},
        {"table": "employee",   "column": "emp_id",    "value_field": "user_id"},
        {"table": "department", "column": "tenant_id", "value_field": "tenant_id"},
    ],
}


def inject_permission_filter(self, sql: str, user_context) -> str:
    """
    사용자 scope_type에 따라 SQL에 WHERE 조건 자동 주입.
    UNION 쿼리와 테이블 별칭(alias)을 모두 처리합니다.

    Args:
        sql: LLM이 생성한 원본 SQL
        user_context: 인증된 UserContext (scope_type, tenant_id, user_id)

    Returns:
        필터가 적용된 SQL (GLOBAL이면 원본 그대로)
    """
    # 1. user_context 없거나 GLOBAL → 필터 없음
    if not user_context or not hasattr(user_context, 'scope_type'):
        return sql
    if user_context.scope_type == "GLOBAL":
        return sql

    # 2. scope_type에 해당하는 필터 규칙 조회
    filter_rules = SCOPE_FILTER_RULES.get(user_context.scope_type, [])
    if not filter_rules:
        return sql

    # 3. UNION 경계에서 분리
    segments = self._split_at_union(sql)

    # 4. 각 segment에 필터 주입
    result_parts = []
    for segment_sql, separator in segments:
        if separator:
            result_parts.append(separator)
        filtered = self._inject_filter_to_segment(segment_sql, filter_rules, user_context)
        result_parts.append(filtered)

    return " ".join(result_parts)


def _inject_filter_to_segment(
    self,
    sql: str,
    filter_rules: List[Dict[str, str]],
    user_context,
) -> str:
    """
    단일 SELECT segment에 필터 주입.

    1. 테이블명 + 별칭 추출 (FROM employee e → {"employee": "e"})
    2. 필터 대상 테이블에 alias prefix 적용한 조건 생성
    3. WHERE/AND로 조건 삽입
    """
    table_alias_map = self._extract_tables_with_aliases(sql)
    conditions = self._get_scope_filter_conditions(table_alias_map, filter_rules, user_context)

    if conditions:
        sql = self._inject_where_condition(sql, conditions)

    return sql
```

### 4.3 _get_scope_filter_conditions 구현

```python
def _get_scope_filter_conditions(
    self,
    table_alias_map: Dict[str, Optional[str]],
    filter_rules: List[Dict[str, str]],
    user_context,
) -> List[str]:
    """
    scope_type 필터 규칙 + 테이블 별칭 → SQL 조건식 목록 생성.

    Args:
        table_alias_map: {테이블명(lower): alias 또는 None}
        filter_rules: SCOPE_FILTER_RULES[scope_type]
        user_context: 인증된 UserContext

    Returns:
        ["e.tenant_id = 5", "e.emp_id = 123"] 형태의 조건 목록

    Examples:
        FROM employee e  → prefix="e"  → e.tenant_id = 5
        FROM employee    → prefix="employee" → employee.tenant_id = 5
    """
    conditions = []

    for rule in filter_rules:
        target_table = rule["table"].lower()

        # SQL에 해당 테이블이 있는지 확인
        if target_table not in table_alias_map:
            continue

        # alias가 있으면 alias, 없으면 테이블명을 prefix로 사용
        alias = table_alias_map[target_table]
        prefix = alias if alias else target_table

        # UserContext에서 필터 값 추출
        value_field = rule["value_field"]
        value = getattr(user_context, value_field, None)
        if value is None:
            continue

        # 정수형 캐스팅 → SQL Injection 방지
        condition = f"{prefix}.{rule['column']} = {int(value)}"
        conditions.append(condition)

    return conditions
```

### 4.4 _inject_where_condition 구현

```python
def _inject_where_condition(self, sql: str, conditions: List[str]) -> str:
    """
    단일 SELECT segment에 WHERE/AND 조건 추가.

    전략:
    - WHERE 절이 있으면 → AND {condition} 추가
    - WHERE 절이 없으면 → WHERE {condition} 삽입
    - GROUP BY/ORDER BY/LIMIT 등 앞에 삽입
    """
    if not conditions:
        return sql

    condition_str = " AND ".join(conditions)
    sql_upper = sql.upper()

    # GROUP BY, ORDER BY, LIMIT, HAVING 등 키워드 위치 찾기
    end_keywords = ['GROUP BY', 'ORDER BY', 'LIMIT', 'HAVING', 'FETCH FIRST']
    insert_pos = len(sql)

    for kw in end_keywords:
        pos = self._find_keyword_at_depth_zero(sql_upper, kw)
        if pos != -1 and pos < insert_pos:
            insert_pos = pos

    # WHERE 존재 여부 확인 (depth 0에서만)
    where_pos = self._find_keyword_at_depth_zero(sql_upper, 'WHERE')

    if where_pos != -1:
        sql = sql[:insert_pos].rstrip() + f" AND {condition_str} " + sql[insert_pos:]
    else:
        sql = sql[:insert_pos].rstrip() + f" WHERE {condition_str} " + sql[insert_pos:]

    return sql
```

### 4.5 _extract_tables_with_aliases 구현

```python
def _extract_tables_with_aliases(self, sql: str) -> Dict[str, Optional[str]]:
    """
    SQL에서 테이블명과 별칭(alias) 매핑 추출.

    Returns:
        {table_name_lower: alias_or_none}

    Examples:
        FROM employee             → {"employee": None}
        FROM employee e           → {"employee": "e"}
        FROM employee AS emp      → {"employee": "emp"}
        FROM employee e JOIN department d ON ...
                                  → {"employee": "e", "department": "d"}

    CTE 이름은 제외 (기존 _extract_cte_names 활용).
    """
    cte_names = self._extract_cte_names(sql)

    parsed = sqlparse.parse(sql)
    if not parsed:
        return {}

    stmt = parsed[0]
    table_alias_map = {}
    from_seen = False
    last_table = None
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
            continue

        # AS 키워드 감지
        if token.ttype is sqlparse.tokens.Keyword and token.value.upper() == 'AS':
            continue

        # 테이블명 또는 별칭 감지
        if from_seen and token.ttype in (sqlparse.tokens.Name, None):
            value = token.value.strip()
            if not self._is_valid_table_identifier(value):
                just_closed_paren = False
                continue

            if last_table is None:
                last_table = value.lower()
            else:
                if last_table not in cte_names:
                    table_alias_map[last_table] = value
                last_table = None
                from_seen = False

            just_closed_paren = False
            continue

        # WHERE, GROUP BY 등 → FROM 절 종료
        if token.ttype is sqlparse.tokens.Keyword and token.value.upper() in (
            'WHERE', 'GROUP', 'ORDER', 'LIMIT', 'HAVING', 'ON', 'SET'
        ):
            if last_table and last_table not in cte_names:
                table_alias_map[last_table] = None
            from_seen = False
            last_table = None
            just_closed_paren = False
            continue

        # 콤마 → 다중 테이블 (FROM a, b)
        if token.ttype is sqlparse.tokens.Punctuation and token.value == ',':
            if last_table and last_table not in cte_names:
                table_alias_map[last_table] = None
            last_table = None
            continue

        just_closed_paren = False

    # 루프 종료 후 마지막 테이블 처리
    if last_table and last_table not in cte_names:
        table_alias_map[last_table] = None

    return table_alias_map
```

### 4.6 _split_at_union 구현

```python
def _split_at_union(self, sql: str) -> List[Tuple[str, str]]:
    """
    UNION/UNION ALL 경계에서 SQL 분리 (괄호 깊이 0에서만).

    Returns:
        [(segment, separator), ...]  첫 번째 segment의 separator는 빈 문자열

    Examples:
        "SELECT ... UNION ALL SELECT ..."
        → [("SELECT ...", ""), ("SELECT ...", "UNION ALL")]
    """
    sql_upper = sql.upper()
    segments = []
    depth = 0
    last_cut = 0
    pending_separator = ""

    i = 0
    while i < len(sql_upper):
        if sql_upper[i] == '(':
            depth += 1
            i += 1
        elif sql_upper[i] == ')':
            depth -= 1
            i += 1
        elif depth == 0 and sql_upper[i:i + 9] == 'UNION ALL':
            before_ok = (i == 0 or not sql_upper[i - 1].isalnum())
            after_ok = (i + 9 >= len(sql_upper) or not sql_upper[i + 9].isalnum())
            if before_ok and after_ok:
                segment = sql[last_cut:i].strip()
                segments.append((segment, pending_separator))
                pending_separator = "UNION ALL"
                last_cut = i + 9
                i += 9
                continue
            i += 1
        elif depth == 0 and sql_upper[i:i + 5] == 'UNION':
            before_ok = (i == 0 or not sql_upper[i - 1].isalnum())
            after_ok = (i + 5 >= len(sql_upper) or not sql_upper[i + 5].isalnum())
            if before_ok and after_ok:
                segment = sql[last_cut:i].strip()
                segments.append((segment, pending_separator))
                pending_separator = "UNION"
                last_cut = i + 5
                i += 5
                continue
            i += 1
        else:
            i += 1

    # 마지막 segment
    last_segment = sql[last_cut:].strip()
    segments.append((last_segment, pending_separator))

    return segments
```

### 4.7 _find_keyword_at_depth_zero 구현

```python
def _find_keyword_at_depth_zero(self, sql_upper: str, keyword: str) -> int:
    """괄호 깊이 0에서 키워드 위치 찾기 (서브쿼리 내부 제외)."""
    depth = 0
    kw_len = len(keyword)

    for i in range(len(sql_upper)):
        if sql_upper[i] == '(':
            depth += 1
        elif sql_upper[i] == ')':
            depth -= 1
        elif depth == 0 and sql_upper[i:i + kw_len] == keyword:
            before_ok = (i == 0 or not sql_upper[i - 1].isalnum())
            after_ok = (i + kw_len >= len(sql_upper) or not sql_upper[i + kw_len].isalnum())
            if before_ok and after_ok:
                return i

    return -1
```

### 4.8 보안 고려사항

| 항목 | 대응 |
|------|------|
| SQL Injection | `tenant_id`와 `user_id`를 `int()` 캐스팅으로 숫자만 허용 |
| 필터 대상 관리 | `SCOPE_FILTER_RULES` 상수에 명시적 정의 → 코드 리뷰 대상 |
| 테이블 미존재 | `_extract_tables_with_aliases()`로 추출된 테이블만 필터 적용 |
| CTE 쿼리 | CTE 정의부는 무시, 메인 SELECT에만 필터 적용 |
| Alias ambiguity | `{prefix}.{column}` 형태로 항상 prefix 사용 → JOIN 시 컬럼 모호성 방지 |
| UNION 보안 | `_split_at_union`으로 각 SELECT에 개별 필터 적용 |

---

## 5. Step 3: prompt_build_node — LLM Scope Awareness (품질 계층)

### 5.1 목적

LLM이 SQL 생성 시 사용자의 데이터 접근 범위를 인지하도록 **프롬프트에 scope 정보를 주입**합니다.

> **주의**: 이 계층은 보안을 **보장하지 않습니다**. LLM이 프롬프트를 무시할 수 있으므로, Step 2의 App 주입이 반드시 필요합니다.

### 5.2 프롬프트 조립 순서 (변경 후)

```
prompt_parts 조립 순서:
  1. base_prompt         ← 기존 (DB 전문가 역할, 스키마 정보)
  2. permission_context  ← ★ 신규 (데이터 접근 권한 정보)
  3. fewshot_context     ← 기존 (유사 쿼리 예제)
  4. history_context     ← 기존 (멀티턴 대화 이력)
  5. error_context       ← 기존 (재시도 오류 컨텍스트)
```

### 5.3 permission_context 생성 함수

```python
def _build_permission_context(user_context) -> str:
    """
    사용자 scope_type → 프롬프트 컨텍스트 문자열 변환.

    v2.0: tb_user.role_id → tb_role.scope_type으로 직접 결정
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

### 5.4 prompt_build_node 수정 (`app/graphs/nl2sql/nodes.py`)

```python
def prompt_build_node(state: Dict[str, Any]) -> Dict[str, Any]:
    # ... 기존 코드 ...

    base_prompt = prompt_service.get_nl2sql_generation_prompt(schema_description, db_type)

    prompt_parts = [base_prompt]

    # ★ Phase 5: 권한 컨텍스트 추가
    user_context = state.get("user_context")
    if user_context:
        permission_context = _build_permission_context(user_context)
        if permission_context:
            prompt_parts.append(permission_context)

    # Few-shot, history, error context (기존 유지)
    # ...

    prompt_metadata = {
        # ... 기존 필드 유지 ...
        "scope_type": user_context.scope_type if user_context else None,
        "has_permission_context": bool(user_context),
    }
```

### 5.5 하이브리드 이중 방어 동작 예시

```
질문: "2024년 입사자 목록 보여줘"
사용자: TENANT scope (tenant_id=5)

[1차: LLM 프롬프트]
  프롬프트에 "tenant_id = 5 데이터만 조회" 포함
  → LLM 생성 SQL:
    SELECT e.name, e.hire_date
    FROM employee e
    WHERE e.hire_date >= '2024-01-01' AND e.tenant_id = 5

[2차: App 주입] (execute_sql_node → inject_permission_filter)
  → SCOPE_FILTER_RULES["TENANT"] → employee.tenant_id
  → 조건 추가: e.tenant_id = 5
  → 결과 SQL:
    SELECT e.name, e.hire_date
    FROM employee e
    WHERE e.hire_date >= '2024-01-01' AND e.tenant_id = 5 AND e.tenant_id = 5
    ↑ 중복이지만 무해 (DB 옵티마이저가 자동 제거)

만약 LLM이 프롬프트를 무시했다면:
  LLM 생성:
    SELECT e.name, e.hire_date FROM employee e WHERE e.hire_date >= '2024-01-01'
  App 주입 결과:
    SELECT e.name, e.hire_date FROM employee e WHERE e.hire_date >= '2024-01-01' AND e.tenant_id = 5
    ↑ App 주입이 보안 보장
```

---

## 6. Step 4: NL2SQL State + 노드 수정

### 6.1 NL2SQLState에 user_context 필드 추가 (`app/graphs/nl2sql/state.py`)

```python
class NL2SQLState(TypedDict):
    # ... 기존 필드 ...

    # ===== Phase 5: 사용자 권한 =====
    user_context: Optional[Any]       # UserContext (인증된 사용자, None=미인증)
```

`create_initial_state()`에도 파라미터 추가:

```python
def create_initial_state(
    question: str,
    request_id: str = "unknown",
    max_retries: int = 2,
    session_id: str = "",
    max_turns: int = 5,
    user_context: Any = None,       # ← Phase 5 추가
) -> NL2SQLState:
    return NL2SQLState(
        # ... 기존 필드 ...
        user_context=user_context,
    )
```

> **`Optional[Any]` 사용 이유**: TypedDict에서 `UserContext` 직접 import 시 순환 참조 가능성. 런타임에서는 실제 UserContext 인스턴스가 전달됩니다.

### 6.2 execute_sql_node 수정 (`app/graphs/nl2sql/nodes.py`)

```python
def execute_sql_node(state: Dict[str, Any]) -> Dict[str, Any]:
    sql = state["generated_sql"]
    request_id = state.get("request_id", "unknown")
    user_context = state.get("user_context")

    log_step(logger, request_id, "NL2SQL", "3", "EXECUTE", "SQL 실행 시작")

    try:
        # Phase 5: scope_type 기반 권한 필터 주입
        original_sql = sql
        if user_context and hasattr(user_context, 'scope_type'):
            sql = sql_executor.inject_permission_filter(sql, user_context)
            if sql != original_sql:
                log_step(logger, request_id, "NL2SQL", "3", "FILTER", "권한 필터 적용", scope=user_context.scope_type)

        result = sql_executor.execute_sql(sql, validate=False)
        state["sql_result"] = result
        state["metadata"]["execution_time_ms"] = result.execution_time_ms
        state["metadata"]["row_count"] = result.row_count
        state["metadata"]["filtered_sql"] = sql if sql != original_sql else None

        log_step(logger, request_id, "NL2SQL", "3", "EXECUTE", "SQL 실행 완료", row_count=result.row_count)

    except (SQLExecutionError, SQLValidationError) as e:
        log_step(logger, request_id, "NL2SQL", "3", "ERROR", f"SQL 실행 실패: {e}", level="ERROR")
        state["validation_error"] = str(e)
        state["validated"] = False

    return state
```

---

## 7. Step 5: NL2SQL 서비스/라우트 수정 — UserContext 전파

### 7.1 전파 경로

```
search.py (라우트)
  → current_user = Depends(get_optional_user)
  → nl2sql_service.search(query, session_id, request_id, user_context=current_user)
    → _prepare_inputs(query, session_id, request_id, user_context)
      → {"question": ..., "user_context": current_user}
        → nl2sql_graph.ainvoke(inputs)
          → _prepare_initial_state(inputs, session_id)
            → create_initial_state(..., user_context=inputs.get("user_context"))
              → prompt_build_node(state)  ← state["user_context"] 사용 [품질 계층]
              → execute_sql_node(state)   ← state["user_context"] 사용 [보안 계층]
```

### 7.2 nl2sql_service.py 수정

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
        "user_context": user_context,
    }
```

### 7.3 search.py (라우트) 수정

```python
from app.core.security.dependencies import get_optional_user

@router.post("/search")
async def search(
    search_request: SearchRequest,
    request: Request,
    current_user = Depends(get_optional_user),  # ← Phase 5 추가 (Phase 3a 선택적)
):
    # ... 기존 코드 ...

    if query_type == "nl2sql":
        response = await nl2sql_service.search(
            query=search_request.query,
            session_id=search_request.session_id,
            request_id=request_id,
            user_context=current_user,  # ← Phase 5 추가
        )

# search_stream()도 동일 패턴
```

### 7.4 graph.py (_prepare_initial_state) 수정

```python
def _prepare_initial_state(self, inputs: Dict[str, Any], session_id: str) -> NL2SQLState:
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

## 8. Step 6: Agent SQL Tool 수정

### 8.1 수정 개요

Agent의 SQL Tool(`query_database_tool`)도 SQL 실행 시 UserContext를 적용해야 합니다.

### 8.2 AgentState에 user_context 추가 (`app/graphs/agent/state.py`)

```python
class AgentState(TypedDict):
    # ... 기존 필드 ...

    # ===== Phase 5: 사용자 권한 =====
    user_context: Optional[Any]       # UserContext (인증된 사용자)
```

`create_initial_state()`에도 `user_context` 파라미터 추가.

### 8.3 sql_tool.py 수정

`_execute_enhanced()` 메서드에서 SQL 실행 전 필터 주입:

```python
# 5. SQL 실행 (Phase 5: 권한 필터 주입)
try:
    user_context = kwargs.get("user_context")
    if user_context:
        sql = sql_executor.inject_permission_filter(sql, user_context)

    result = sql_executor.execute_sql(sql, validate=True)
```

### 8.4 agent_service.py에서 user_context 전달

```python
initial_state = create_initial_state(
    question=question,
    session_id=session_id,
    request_id=request_id,
    user_context=user_context,  # ← Phase 5 추가
)
```

### 8.5 tools_node에서 user_context 전달

Agent의 `tools_node`에서 state의 `user_context`를 추출하여 SQL tool 호출 시 전달:

```python
def tools_node(state: AgentState) -> Dict[str, Any]:
    user_context = state.get("user_context")
    # ... tool 실행 시 user_context를 kwargs로 전달 ...
```

---

## 9. Step 7: History 미들웨어 수정

### 9.1 변경 내용 (`app/middleware/history.py`)

인증 미들웨어(Phase 3)가 설정한 `request.state.current_user`에서 사용자 정보를 읽도록 변경합니다.

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

### 9.2 변경 의도

- 인증된 사용자: `request.state.current_user`에서 **검증된** 정보 사용 (위변조 불가)
- 미인증 사용자 (Phase 3a): 기존 헤더 방식 유지 (하위호환)
- Phase 6(필수 인증) 전환 시 헤더 fallback 제거

---

## 10. 검증 체크리스트

### 10.1 단위 테스트 (`tests/test_phase5_filter.py`)

| 테스트 | 설명 |
|--------|------|
| `test_inject_filter_global` | GLOBAL scope → SQL 변경 없음 |
| `test_inject_filter_tenant` | TENANT scope → `AND e.tenant_id = N` 추가 |
| `test_inject_filter_user` | USER scope → `AND e.tenant_id = N AND e.emp_id = M` 추가 |
| `test_inject_filter_no_where` | WHERE 절 없는 SQL → `WHERE tenant_id = N` 삽입 |
| `test_inject_filter_with_where` | WHERE 절 있는 SQL → `AND tenant_id = N` 추가 |
| `test_inject_filter_alias` | `FROM employee e` → `e.tenant_id = N` (alias prefix) |
| `test_inject_filter_alias_as` | `FROM employee AS e` → `e.tenant_id = N` |
| `test_inject_filter_no_alias` | `FROM employee` → `employee.tenant_id = N` |
| `test_inject_filter_join_alias` | JOIN + alias → 양쪽 테이블에 alias prefix 필터 |
| `test_inject_filter_union` | UNION → 각 SELECT에 개별 필터 |
| `test_inject_filter_union_all` | UNION ALL → 각 SELECT에 개별 필터 |
| `test_inject_filter_subquery` | 서브쿼리 → 메인 쿼리에만 필터 |
| `test_inject_filter_group_by` | GROUP BY 앞에 필터 삽입 |
| `test_inject_filter_cte` | CTE → 메인 SELECT에만 필터 |
| `test_inject_filter_no_match` | 필터 대상 테이블 없는 SQL → 변경 없음 |
| `test_inject_filter_no_context` | user_context=None → SQL 변경 없음 |

### 10.2 통합 테스트

| 테스트 | 설명 |
|--------|------|
| NL2SQL + GLOBAL | 관리자(scope_type=GLOBAL)로 검색 → 전체 데이터 |
| NL2SQL + TENANT | 테넌트 관리자로 검색 → 해당 테넌트 데이터만 |
| NL2SQL + USER | 일반 사용자로 검색 → 본인 데이터만 |
| NL2SQL 프롬프트 | 프롬프트에 scope 정보 포함 확인 (로그 검증) |
| NL2SQL 이중 방어 | LLM 필터 포함/미포함 양쪽 모두 올바른 결과 |
| Agent SQL Tool + TENANT | Agent 검색 → SQL Tool이 필터 적용 |
| History 저장 | 인증 사용자 → tenant_id/user_id 올바르게 저장 |

### 10.3 프롬프트 품질 테스트

| 테스트 | 설명 |
|--------|------|
| `test_prompt_global_scope` | GLOBAL → "전체 데이터 접근" 문구, 필터 없음 |
| `test_prompt_tenant_scope` | TENANT → "tenant_id = N" 문구 포함 |
| `test_prompt_user_scope` | USER → "tenant_id = N" + "emp_id = M" 문구 포함 |
| `test_prompt_no_context` | user_context=None → permission_context 없음 |
| `test_prompt_position` | permission_context가 base_prompt 뒤, fewshot 앞에 위치 |

### 10.4 엣지 케이스

| 케이스 | 기대 동작 |
|--------|----------|
| CTE(WITH) 쿼리 | CTE 정의부 무시, 메인 SELECT에 필터 |
| UNION/UNION ALL | 각 SELECT segment에 개별 필터 |
| 테이블 별칭 `FROM employee e` | `e.tenant_id = N` (alias prefix) |
| AS 키워드 별칭 `FROM employee AS e` | `e.tenant_id = N` |
| 별칭 없는 단일 테이블 | `employee.tenant_id = N` |
| JOIN + 별칭 | `e.tenant_id=N AND d.tenant_id=N` |
| 필터 대상 없는 테이블 | SCOPE_FILTER_RULES에 없으면 무필터 |
| 서브쿼리 내 테이블 | depth>0 → 메인 필터 미적용 |

**예시: JOIN + Alias (TENANT scope, tenant_id=5)**

```sql
-- 원본 (LLM 생성)
SELECT e.name, d.dept_name
FROM employee e
JOIN department d ON e.dept_id = d.dept_id
WHERE e.hire_date >= '2024-01-01'

-- 필터 적용 후
SELECT e.name, d.dept_name
FROM employee e
JOIN department d ON e.dept_id = d.dept_id
WHERE e.hire_date >= '2024-01-01' AND e.tenant_id = 5 AND d.tenant_id = 5
```

**예시: UNION ALL (TENANT scope, tenant_id=5)**

```sql
-- 원본
SELECT name FROM employee WHERE dept_id = 10
UNION ALL
SELECT name FROM employee WHERE dept_id = 20

-- 필터 적용 후
SELECT name FROM employee WHERE dept_id = 10 AND employee.tenant_id = 5
UNION ALL
SELECT name FROM employee WHERE dept_id = 20 AND employee.tenant_id = 5
```

---

## 11. 다음 단계 (Phase 6 Preview)

Phase 5 완료 후 **Phase 6: 프론트엔드 인증 통합**을 진행합니다.

| 작업 | 설명 |
|------|------|
| `LoginView.vue` | 로그인 화면 구현 |
| `auth.js` (API) | 인증 API 클라이언트 |
| `auth.js` (Store) | Vuex 인증 상태 관리 |
| `router/index.js` | 라우터 가드 (미인증 → /login) |
| `api/index.js` | Authorization 헤더 자동 추가, 401 시 토큰 갱신 |
| `AppSidebar.vue` | 메뉴 목록을 DB에서 받아 동적 생성 (tb_user_menu 기반) |
| `AppHeader.vue` | 로그인 사용자 표시 + 로그아웃 |
| 관리 화면 | UsersView, MenusView, RolesView, TenantsView |
| Phase 3a → 3b 전환 | `get_optional_user` → `get_current_active_user`로 변경 |

> **상세**: `docs/design/user_permission_phase6.md` 참조

---

## 부록 A: 파일 수정 의존 관계

```
순서 제약:
  Step 1 (DB 마이그레이션)         → Step 2 (sql_executor)
  Step 2 (sql_executor 보안계층)   → Step 4 (NL2SQL State+노드) → Step 5 (서비스/라우트)
  Step 3 (prompt_build 품질계층)   → Step 4 (NL2SQL State+노드) — Step 2와 병렬 가능
  Step 2 (sql_executor)           → Step 6 (Agent SQL Tool) — Step 5와 병렬 가능
  Step 7 (History 미들웨어)       → 독립 (병렬 가능)

병렬 가능 작업:
  [Step 2 + Step 3] — 보안계층 + 품질계층 독립 진행
  [Step 5 + Step 6 + Step 7] — 모두 Step 4 완료 후 병렬 진행
```

## 부록 B: v1.0 → v2.0 주요 변경 비교

| 항목 | v1.0 (이전 Phase 5) | v2.0 (현재 Phase 5) |
|------|------|------|
| 필터 규칙 소스 | `tb_data_filter` 테이블 (DB 조회) | `SCOPE_FILTER_RULES` 상수 (코드 기반) |
| 사용자-역할 | M:N (`tb_user_role`, `roles[]` 배열) | 1:N (`tb_user.role_id` FK, 단일 역할) |
| scope 결정 | 다중 역할 중 최상위 scope 계산 | 단일 역할의 `scope_type` 직접 사용 |
| 필터 대상 조회 | `_get_data_filters(roles)` DB 쿼리 | `SCOPE_FILTER_RULES[scope_type]` 딕셔너리 조회 |
| 권한 체크 | `permission_code` 기반 | `tb_user_menu` 메뉴 기반 CRUD |
| 제거된 테이블 | - | `tb_data_filter`, `tb_permission`, `tb_role_permission`, `tb_user_role` |
| UserContext 필드 | `roles[]`, `permissions[]` | `role_code`, `scope_type` (단일) |

## 부록 C: 전체 흐름 다이어그램

```
하이브리드 이중 방어 흐름 (v2.0):

  사용자 질문
    → search.py (Depends(get_optional_user) → UserContext)
      → nl2sql_service (user_context 전달)
        → NL2SQLState (user_context 저장)
          → prompt_build_node [1차: 품질계층]
            → scope_type → permission_context 프롬프트 주입
            → LLM에 scope 정보 제공 → SQL에 필터 자연스럽게 포함
          → sql_generate_node → validate_sql_node
          → execute_sql_node [2차: 보안계층]
            → inject_permission_filter(sql, user_context)
              → SCOPE_FILTER_RULES[scope_type] → 필터 규칙 결정
              → _extract_tables_with_aliases() → 테이블+별칭 추출
              → _get_scope_filter_conditions() → SQL 조건식 생성
              → _inject_where_condition() → WHERE/AND 주입
            → sql_executor.execute_sql(filtered_sql)
          → pii_filter → generate_answer → save_history → END
```

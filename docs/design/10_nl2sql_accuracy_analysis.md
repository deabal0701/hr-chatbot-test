# NL2SQL 정확도 분석 보고서

> **작성일**: 2026-02-21
> **분석 범위**: Business DB 스키마, Graph 설계, 스키마 검색, Few-shot, Intent Rewrite, SQL 생성 프롬프트, SQL 검증/실행
> **대상 DB**: Oracle (ORCLCDB, 115.68.223.220:1521, MUSER 스키마)

---

## 목차

1. [Business DB 스키마 분석](#1-business-db-스키마-분석)
2. [Graph 설계 분석](#2-graph-설계-분석)
3. [스키마 검색 단계 분석](#3-스키마-검색-단계-분석)
4. [Few-shot 검색 분석](#4-few-shot-검색-분석)
5. [Intent Rewrite 분석](#5-intent-rewrite-분석)
6. [SQL 생성 프롬프트 분석](#6-sql-생성-프롬프트-분석)
7. [SQL 검증/실행 단계 분석](#7-sql-검증실행-단계-분석)
8. [종합 개선 로드맵](#8-종합-개선-로드맵)

---

## 1. Business DB 스키마 분석

### 1.1 뷰 구조 개요

NL2SQL 대상은 **Oracle DB**의 `MUSER` 스키마에 있는 14개 시노님(→ H552_RND 스키마의 VIEW)입니다.

| 뷰 | 행 수 | 조인 키 | 관계 | 설명 |
|----|-------|---------|------|------|
| **v_ai_employee** | 2,437 | EMP_ID (PK) | 1 (메인) | 직원 기본정보 (23 컬럼) |
| v_ai_address | 2,365 | EMP_ID | 1:N | 주소/거주지 |
| v_ai_career | 1,464 | EMP_ID | 1:N | 이전 직장 경력 |
| v_ai_scholar | 35 | EMP_ID | 1:N | 학력사항 |
| v_ai_family | 4 | EMP_ID | 1:N | 가족관계 |
| v_ai_language | 1,358 | EMP_ID | 1:N | 어학성적 |
| v_ai_license | 7 | EMP_ID | 1:N | 자격증 |
| v_ai_military | 5 | EMP_ID | 1:1 | 병역 |
| v_ai_reward | 265 | EMP_ID | 1:N | 상벌 |
| v_ai_training | 4,088 | EMP_ID | 1:N | 교육/훈련 |
| v_ai_feedback | 103 | EMP_ID | 1:N | 인사평가 (26 컬럼, 복잡 뷰) |
| **v_ai_pay_report** | 69,360 | **EMPLOYEE_ID** | 1:N | 급여 (25 컬럼) |
| **v_ai_dtm_yy_rest** | 6,625 | **EMPLOYEE_ID** | 1:N | 연차관리 (21 컬럼) |
| v_ai_phm_education | ERROR | - | - | 시노님 깨짐 (ORA-00980) |

### 1.2 발견된 이슈

#### [이슈 1-1] V_AI_EMPLOYEE 중복 행 (심각도: 높음)

동일 `EMP_ID`가 부서이동/코드조인(`FRM_CODE`의 `CPE_GROUP_CD`)으로 여러 행 생성됩니다.

```
EMP_ID=2282 → Row1: DEPARTMENT=SIU파트
EMP_ID=2282 → Row2: DEPARTMENT=2사업그룹
```

**영향**: `SELECT COUNT(*) FROM v_ai_employee WHERE work_status='재직'`이 실제 재직자 수보다 많은 값을 반환합니다.
`COUNT(DISTINCT emp_id)` 사용이 필수적이나, LLM은 이를 인지하지 못합니다.

#### [이슈 1-2] V_AI_EDUCATION vs V_AI_SCHOLAR 이름 불일치 (심각도: 높음)

| 위치 | 사용하는 이름 |
|------|-------------|
| `nl2sql_generation_prompt` (DB 프롬프트) | `V_AI_EDUCATION` |
| Few-shot 예제 id=947, id=973 | `v_ai_education` |
| `table_catalog` (DB 설정) | `v_ai_scholar` |
| Oracle DB `allowed_tables` | `V_AI_SCHOLAR` |
| 실제 Oracle 뷰 | `V_AI_SCHOLAR` (존재), `V_AI_EDUCATION` (**미존재**) |

**영향**: LLM이 `V_AI_EDUCATION`으로 SQL 생성 시 테이블 검증 실패 또는 ORA-00942 에러 발생.

#### [이슈 1-3] EMP_ID vs EMPLOYEE_ID 조인키 불일치 (심각도: 중간)

- `EMP_ID` 사용: v_ai_employee 외 11개 뷰
- `EMPLOYEE_ID` 사용: **v_ai_pay_report**, **v_ai_dtm_yy_rest**

조인 시 `V_AI_EMPLOYEE.EMP_ID = V_AI_PAY_REPORT.EMPLOYEE_ID`로 작성해야 하나, LLM이 동일 컬럼명으로 간주하여 `EMP_ID = EMP_ID`로 생성할 가능성이 있습니다.

#### [이슈 1-4] 희소 데이터 테이블 (심각도: 낮음)

`v_ai_family(4건)`, `v_ai_license(7건)`, `v_ai_military(5건)`은 데이터가 극히 적어 조인 시 결과 없음이 빈번합니다.

#### [이슈 1-5] 컬럼 코멘트 부재 (심각도: 중간)

Oracle 뷰의 `ALL_COL_COMMENTS`가 대부분 비어 있어, `generate_schema_description()`이 컬럼명+타입만 출력합니다. `CAREER_MONTHS`, `DUTY_DATE` 등 비직관적 컬럼의 의미를 LLM이 스키마만으로 파악할 수 없습니다.

---

## 2. Graph 설계 분석

### 2.1 그래프 흐름

```
load_history → intent_rewrite → should_route_after_intent
                                 ├─ sql_needed → schema_retrieval → fewshot_retrieval → prompt_build
                                 │               → sql_generate → validate_sql
                                 │                                  ├─ execute → execute_sql → should_continue_after_execute
                                 │                                  │              ├─ answer → pii_filter → generate_answer → save_history → END
                                 │                                  │              ├─ retry → prepare_retry → fewshot_retrieval (루프)
                                 │                                  │              └─ error → handle_error → END
                                 │                                  ├─ retry → prepare_retry → fewshot_retrieval (루프)
                                 │                                  └─ error → handle_error → END
                                 └─ sql_not_needed → answer_from_history → save_history → END
```

### 2.2 발견된 이슈

#### [이슈 2-1] multiturn_max_turns=1 설정 (심각도: 높음)

**현재 DB 설정**: `multiturn_enabled=true`, `multiturn_max_turns=1`

`load_history_node`(`app/graphs/nl2sql/nodes.py:1032`)에서:

```python
if len(conversation_history) >= max_turns:  # max_turns=1
    keep_count = max(0, max_turns - 1)      # keep_count=0
    conversation_history = []                 # 모든 이력 삭제!
```

**영향**: 멀티턴이 활성화되어 있으나, max_turns=1로 이전 이력이 매번 삭제됩니다. `intent_rewrite_node`에 빈 이력이 전달되어 "첫 번째 질문이므로 SQL 실행 필요"로 항상 통과 → **멀티턴 기능 완전 비활성화 상태**.

#### [이슈 2-2] schema_retrieval → fewshot 간 의존성 부재 (심각도: 중간)

`schema_retrieval_node`에서 선택한 테이블 정보가 `fewshot_retrieval_node`의 검색 필터에 활용되지 않습니다. 예: "급여 관련 질문"에서 `v_ai_pay_report`가 선택되었어도, few-shot 검색은 순수 벡터 유사도만으로 수행하여 무관한 예제가 반환될 수 있습니다.

#### [이슈 2-3] validate_sql_node state 직접 mutation (심각도: 낮음)

`validate_sql_node`(`app/graphs/nl2sql/nodes.py:598`)에서 `state["validated"] = False`와 같이 state를 직접 변경합니다. LangGraph의 권장 패턴은 변경할 필드만 dict로 반환하는 것이므로, 일관성을 위해 수정이 바람직합니다.

---

## 3. 스키마 검색 단계 분석

### 3.1 동작 방식

1. `table_catalog_service.get_table_summary_for_llm()` → 13개 테이블 요약
2. 경량 LLM(`gpt-4.1-nano`)으로 관련 테이블 JSON 선택
3. FK 관계 테이블 자동 포함
4. `schema_loader.generate_schema_description(tables=...)` → 선택된 테이블 스키마 로드

### 3.2 발견된 이슈

#### [이슈 3-1] table_catalog 메타데이터가 SQL 생성 프롬프트에 미전달 (심각도: 높음)

`table_catalog`에는 풍부한 비즈니스 정보가 있습니다:

```python
"POSITION (직위: 사원,대리,과장,차장,부장)"
"HIRE_DATE ★입사일 (입사자 집계: TO_CHAR(HIRE_DATE,'YYYY')=':YYYY')"
"WORK_STATUS ★재직상태 (재직/퇴직)"
```

그러나 `generate_schema_description()`은 Oracle 카탈로그에서 가져온 **컬럼명+타입만** 출력합니다:

```
- position: VARCHAR2 (NULL 가능)     ← "직위: 사원,대리,..." 정보 없음!
- hire_date: DATE (NOT NULL)          ← 사용 패턴 정보 없음!
```

`table_catalog`의 설명은 `schema_retrieval_node`(테이블 선택)에서만 사용되고, `prompt_build_node`(SQL 생성 프롬프트)에는 전달되지 않습니다.

#### [이슈 3-2] 컬럼 값 예시 미포함 (심각도: 중간)

LLM이 `WHERE POSITION = '부장'`을 올바르게 생성하려면 POSITION 컬럼의 실제 값 목록("사원,대리,과장,차장,부장")이 필요합니다. 현재 스키마 설명에는 이 정보가 포함되지 않습니다.

특히 `HIRE_TYPE` 컬럼은:
- catalog 설명: "채용유형: 신입,경력"
- **실제 DB 값**: "입사(경력)", "입사(신입)"

이 불일치로 LLM이 `WHERE HIRE_TYPE = '신입'` (실패) 대신 `WHERE HIRE_TYPE = '입사(신입)'` (성공)을 생성해야 합니다.

---

## 4. Few-shot 검색 분석

### 4.1 현황

- **총 33개** Few-shot 예제 (`tb_docs` 테이블, `usage_type='rag_action'`, `doc_type='query_example'`)
- **fewshot_top_k=1** (DB 설정) → 1개 예제만 검색
- **fewshot_similarity_threshold=0.3** → 임계값 낮음
- 벡터 유사도(코사인) 기반 검색 (`text-embedding-3-small`)

### 4.2 예제 커버리지

| 카테고리 | 예제 수 | 대표 예제 |
|----------|---------|----------|
| 직원 기본 집계 (연도별/부서별/성별) | 10 | 연도별 입사자, 부서별 직원수 |
| 1:N 조인 패턴 | 8 | 자격증 보유자, 어학성적 기준 |
| 급여/평가 | 4 | 부서별 평균급여, 평가등급 분포 |
| 복합 조건 | 3 | 지역+어학+직급 복합 |
| 상세 조회 (명단/비교표) | 8 | 입사자 자격증 상세, 전체 정보 비교 |

### 4.3 발견된 이슈

#### [이슈 4-1] fewshot_top_k=1 (심각도: 높음)

1개 예제만으로는 복잡한 질문의 SQL 패턴을 충분히 참고할 수 없습니다. 특히 다중 테이블 조인, EXISTS 패턴, 서브쿼리 패턴을 동시에 보여주려면 최소 3개가 필요합니다.

#### [이슈 4-2] V_AI_EDUCATION 사용 예제 (심각도: 높음)

| id | title | 문제 |
|----|-------|------|
| 947 | 학력 기준 직원 수 조회 | SQL에 `v_ai_education` 참조 → 실제 뷰명 `v_ai_scholar` |
| 973 | 입사자 현황 + 학력 정보 | SQL에 `v_ai_education` 참조 → 실제 뷰명 `v_ai_scholar` |

이 예제가 검색되면 LLM이 잘못된 테이블명으로 SQL을 생성합니다.

#### [이슈 4-3] context_data 형식 비일관 (심각도: 중간)

```
# 형식 A (대부분): 마크다운 구조화
## SQL
```sql
SELECT ...
```
## 핵심 패턴
- EXISTS 사용

# 형식 B (일부): plain text
SQL: SELECT ... 핵심: 부서별 GROUP BY

# 형식 C (id=979): 주석 포함 raw SQL
-- 다건 직원 전체 정보 비교 표 조회
SELECT ...
```

LLM이 예제를 파싱할 때 형식이 다르면 SQL 추출 정확도가 떨어질 수 있습니다.

#### [이슈 4-4] 벡터 유사도 기반 검색만 사용 (심각도: 중간)

의미적 유사성만으로 검색하므로, "연도별 입사자"와 "연도별 퇴사자"가 매우 높은 유사도를 가져 잘못된 예제가 1등으로 검색될 수 있습니다. 테이블 필터링이나 키워드 보조 검색이 없습니다.

---

## 5. Intent Rewrite 분석

### 5.1 동작 방식

1. 대화 이력 확인 (없으면 바로 `sql_needed` 반환)
2. LLM 호출하여 의도 분석 + 질문 재작성
3. `query_type` 결정: `sql_needed` 또는 `sql_not_needed`

### 5.2 발견된 이슈

#### [이슈 5-1] multiturn_max_turns=1로 사실상 비활성 (심각도: 높음)

이슈 2-1과 동일. `conversation_history`가 항상 빈 배열이므로 `intent_rewrite_node`의 첫 번째 조건분기에서 바로 반환됩니다:

```python
# app/graphs/nl2sql/nodes.py:1141
if not conversation_history:
    return {
        "query_type": "sql_needed",
        "rewritten_question": question,  # 원본 질문 그대로
    }
```

질문 재작성, 이전 컨텍스트 활용, `sql_not_needed` 판단이 모두 불가합니다.

#### [이슈 5-2] intent_analysis_system_prompt 빈 값 (심각도: 낮음)

DB(`tb_app_settings`)에 `intent_analysis_system_prompt` 키가 빈 문자열로 저장되어 있습니다. 현재 코드에서 이 키를 직접 참조하지 않으므로 영향은 없으나, 향후 사용 시 주의가 필요합니다.

---

## 6. SQL 생성 프롬프트 분석

### 6.1 프롬프트 구조 (prompt_build_node)

```
[System Prompt]
├── base_prompt (nl2sql_generation_prompt from DB)
│   ├── Oracle 전문가 페르소나
│   ├── {schema_description} → 런타임 치환
│   ├── 필수 규칙 (SELECT only, 세미콜론 금지 등)
│   ├── 날짜 규칙
│   ├── 재직 조건 규칙
│   ├── 1:N 관계 조인 규칙
│   ├── 서브쿼리 규칙
│   ├── 급여/평가/연차 규칙
│   └── (행 수 제한 규칙)
├── Few-shot 예제 (fewshot_context)
├── 이전 대화 이력 (conversation_history) ← multiturn_max_turns=1로 항상 비어 있음
└── 재시도 에러 컨텍스트 (retry_count > 0일 때)

[User Prompt]
└── "질문: {question}\n위 질문에 대한 Oracle SELECT 쿼리를 생성해주세요."
```

### 6.2 발견된 이슈

#### [이슈 6-1] 날짜 하드코딩 "2026년00월00일" (심각도: 높음)

DB에 저장된 프롬프트:

```
올해는 2026년, 오늘 = 2026년00월00일임(LLM기준 날짜 추측 절대 금지)
```

"00월00일"이 동적으로 치환되지 않고 **그대로** LLM에 전달됩니다. LLM이 "이번 달 입사자", "최근 3개월" 등의 시간 기반 질문에 정확한 SQL을 생성할 수 없습니다.

**수정 방안**: `prompt_build_node`에서 `datetime.now()` 값을 프롬프트에 주입하거나, DB 프롬프트 자체에 `{current_date}` 플레이스홀더를 사용.

#### [이슈 6-2] V_AI_EDUCATION 참조 (심각도: 높음)

프롬프트의 1:N 뷰 목록에 `V_AI_EDUCATION`이 명시되어 있으나, 실제 뷰명은 `V_AI_SCHOLAR`입니다.

```
1:N 뷰: V_AI_ADDRESS, V_AI_CAREER, V_AI_EDUCATION, ...
                                     ^^^^^^^^^^^^^^^^ → V_AI_SCHOLAR 이어야 함
```

#### [이슈 6-3] COUNT 시 DISTINCT 미안내 (심각도: 높음)

V_AI_EMPLOYEE 중복 행 문제(이슈 1-1)에도 불구하고, 프롬프트에 `COUNT(DISTINCT emp_id)` 사용 가이드가 없습니다.

**추가 필요 규칙**:

```
# V_AI_EMPLOYEE 주의사항
- V_AI_EMPLOYEE는 1인 다행 가능 (부서이동 이력)
- 인원수 집계 시 반드시 COUNT(DISTINCT EMP_ID) 사용
- SELECT DISTINCT emp_id, emp_name, ... 으로 중복 제거
```

#### [이슈 6-4] table_catalog 메타데이터 미주입 (심각도: 중간)

이슈 3-1과 관련. `table_catalog`에 있는 컬럼별 비즈니스 설명, 키워드, 값 예시가 SQL 생성 프롬프트에 포함되지 않습니다.

| 정보 | schema_description (현재) | table_catalog (미사용) |
|------|--------------------------|----------------------|
| 컬럼 타입 | `position: VARCHAR2` | `POSITION (직위: 사원,대리,과장,차장,부장)` |
| 사용 패턴 | 없음 | `★입사일 (TO_CHAR(HIRE_DATE,'YYYY')=':YYYY')` |
| 조인 키 | 없음 | `EMP_ID (PK, 조인키)` / `EMPLOYEE_ID (FK, ★주의: EMP_ID 아님)` |

#### [이슈 6-5] 컬럼 값 열거 부족 (심각도: 중간)

LLM이 WHERE 조건을 정확히 생성하려면 Enum 성격 컬럼의 실제 값이 필요합니다.

| 컬럼 | 프롬프트 정보 | 실제 DB 값 | 차이 |
|------|-------------|-----------|------|
| WORK_STATUS | '재직'/'퇴직' | 재직, 퇴직 | 일치 |
| POSITION | 없음 | 사원,대리,과장,차장,부장 | **누락** |
| EMP_TYPE | 없음 | 정규직,계약직 | **누락** |
| HIRE_TYPE | catalog에 "신입,경력" | **입사(경력), 입사(신입)** | **불일치** |
| GENDER | 없음 | 남, 여 | **누락** |

특히 `HIRE_TYPE`은 catalog 설명("신입,경력")과 실제 값("입사(경력)","입사(신입)")이 달라, LLM이 `WHERE HIRE_TYPE = '신입'`으로 잘못 생성할 가능성이 높습니다.

#### [이슈 6-6] 답변 생성 프롬프트 간소 (심각도: 낮음)

`nl2sql_answer_prompt`는 15개 규칙이 잘 정의되어 있으나, 결과가 0건일 때의 안내 메시지가 코드 하드코딩(`"조회된 결과가 없습니다."`)으로 처리됩니다. 프롬프트에서 "왜 결과가 없을 수 있는지" 안내하는 규칙을 추가하면 사용자 경험이 개선됩니다.

---

## 7. SQL 검증/실행 단계 분석

### 7.1 검증 체계

| 단계 | 항목 | 구현 상태 |
|------|------|----------|
| 키워드 차단 | DROP/DELETE/UPDATE/INSERT 등 | 구현됨 (정규식 단어경계) |
| SELECT 전용 | sqlparse로 statement type 확인 | 구현됨 |
| 테이블 화이트리스트 | allowed_tables 비교 | 구현됨 (CTE 이름 제외 포함) |
| LIMIT/FETCH 자동 추가 | Oracle: FETCH FIRST N ROWS ONLY | 구현됨 (GROUP BY 예외 처리) |
| 타임아웃 | Oracle: 미구현 / PostgreSQL: statement_timeout | Oracle 미구현 |

### 7.2 발견된 이슈

#### [이슈 7-1] Oracle 타임아웃 미지원 (심각도: 중간)

`app/core/database/adapters/oracle.py:219`:

```python
def set_timeout(self, cursor, timeout_seconds):
    # Oracle에서는 세션 레벨 타임아웃이 직접 지원되지 않음
    logger.debug(f"Oracle 타임아웃 설정 요청: {timeout_seconds}초 (직접 지원 안 함)")
```

무한 실행 쿼리(예: 대형 CROSS JOIN)가 서버를 점유할 수 있습니다.

**수정 방안**: Python 측에서 `asyncio.wait_for()` 또는 `concurrent.futures.ThreadPoolExecutor`로 타임아웃 구현, 또는 Oracle `DBMS_RESOURCE_MANAGER` 활용.

#### [이슈 7-2] 재시도 시 구체적 수정 가이드 부재 (심각도: 중간)

`prepare_retry_node`에서 `previous_error`만 전달합니다:

```python
return {
    "retry_count": new_retry_count,
    "previous_sql": generated_sql,
    "previous_error": validation_error,  # "허용되지 않은 테이블: v_ai_education"
    "enhanced_fewshot": True,
}
```

에러 메시지를 파싱하여 구체적인 수정 힌트를 제공하면 재시도 성공률이 향상됩니다:
- `"허용되지 않은 테이블: v_ai_education"` → `"v_ai_education 대신 v_ai_scholar를 사용하세요"`
- `"ORA-00904: EMP_ID invalid"` → `"v_ai_pay_report에서는 EMPLOYEE_ID를 사용하세요"`

#### [이슈 7-3] LIMIT 자동 추가의 부작용 (심각도: 낮음)

`add_limit_clause()`가 모든 쿼리에 `FETCH FIRST 1000 ROWS ONLY`를 추가합니다 (GROUP BY 제외). 사용자가 "전직원 목록"을 요청했을 때도 1000건으로 제한됩니다. 프롬프트에 "전직원이라는 단어 → 행 수 제한 금지" 규칙이 있으나, 코드 레벨에서 이를 반영하는 로직은 없습니다.

---

## 8. 종합 개선 로드맵

### 8.1 CRITICAL (즉시 수정 필요)

| ID | 이슈 | 영향 | 수정 방안 | 수정 위치 |
|----|------|------|----------|----------|
| **C1** | V_AI_EDUCATION → V_AI_SCHOLAR 통일 | SQL 실행 실패 | 프롬프트/Few-shot에서 `v_ai_education` → `v_ai_scholar` 변경 | DB: `tb_app_settings`(prompt.nl2sql_generation_prompt), `tb_docs`(id=947,973) |
| **C2** | 날짜 동적 주입 | 시간 기반 질문 오류 | `prompt_build_node`에서 `datetime.now()` 주입 또는 프롬프트에 `{current_date}` 플레이스홀더 | `app/graphs/nl2sql/nodes.py` + DB 프롬프트 |
| **C3** | COUNT(DISTINCT EMP_ID) 가이드 | 집계 수치 부정확 | 프롬프트에 V_AI_EMPLOYEE 중복 행 주의 규칙 추가 | DB: `tb_app_settings`(prompt.nl2sql_generation_prompt) |

### 8.2 HIGH (정확도 직접 영향)

| ID | 이슈 | 수정 방안 | 수정 위치 |
|----|------|----------|----------|
| **H1** | fewshot_top_k=1 | 3으로 증가 | DB: `tb_app_settings`(nl2sql.fewshot_top_k) |
| **H2** | table_catalog → SQL 프롬프트 주입 | `prompt_build_node`에서 selected_tables의 catalog 정보를 프롬프트에 추가 | `app/graphs/nl2sql/nodes.py:prompt_build_node()` |
| **H3** | 컬럼 값 열거(ENUM) 추가 | catalog 또는 프롬프트에 주요 컬럼의 실제 값 목록 추가 | DB: `tb_app_settings`(nl2sql.table_catalog) + 프롬프트 |
| **H4** | multiturn_max_turns=1 → 5 | DB 설정 변경 (의도적 비활성화라면 문서화) | DB: `tb_app_settings`(nl2sql.multiturn_max_turns) |

### 8.3 MEDIUM (품질 개선)

| ID | 이슈 | 수정 방안 |
|----|------|----------|
| **M1** | Few-shot context_data 형식 통일 | 33개 예제를 표준 마크다운 형식(`## SQL\n```sql...\n## 핵심 패턴`)으로 정규화 |
| **M2** | schema_description에 catalog 정보 병합 | `generate_schema_description()`에서 Oracle 코멘트 대신 catalog 컬럼 설명 사용 |
| **M3** | 재시도 시 구체적 수정 가이드 | `prepare_retry_node`에서 에러 파싱 → catalog 기반 수정 힌트 제공 |
| **M4** | schema_retrieval → fewshot 필터링 | 선택된 테이블과 관련된 few-shot만 우선 검색하도록 필터 추가 |
| **M5** | Oracle 타임아웃 구현 | Python `asyncio.wait_for()` 또는 `ThreadPoolExecutor` 타임아웃 적용 |

### 8.4 LOW (장기 개선)

| ID | 이슈 | 수정 방안 |
|----|------|----------|
| **L1** | V_AI_EMPLOYEE 뷰 1인 1행 보장 | DBA 협의하여 DISTINCT 또는 ROW_NUMBER 적용 |
| **L2** | Few-shot 예제 카테고리화 | 질문 유형별 태그 추가 → 유형별 우선 검색 |
| **L3** | SQL 실행 결과 자동 검증 | 결과 0건/이상 수치일 때 자동 재생성 |
| **L4** | validate_sql_node state mutation 수정 | dict return 패턴으로 LangGraph 표준 준수 |

### 8.5 Quick Win (즉시 적용 가능)

**DB 설정 변경만으로 가능** (코드 수정 불필요):

```sql
-- 1. fewshot_top_k: 1 → 3
UPDATE tb_app_settings SET value = '3' WHERE category = 'nl2sql' AND key = 'fewshot_top_k';

-- 2. multiturn_max_turns: 1 → 5
UPDATE tb_app_settings SET value = '5' WHERE category = 'nl2sql' AND key = 'multiturn_max_turns';

-- 3. Few-shot 예제 수정 (v_ai_education → v_ai_scholar)
UPDATE tb_docs SET context_data = REPLACE(context_data, 'v_ai_education', 'v_ai_scholar')
WHERE id IN (947, 973);

-- 4. nl2sql_generation_prompt에서 V_AI_EDUCATION → V_AI_SCHOLAR 변경
UPDATE tb_app_settings
SET value = REPLACE(value, 'V_AI_EDUCATION', 'V_AI_SCHOLAR')
WHERE category = 'prompt' AND key = 'nl2sql_generation_prompt';
```

**코드 수정이 필요한 항목**:

| 파일 | 수정 내용 |
|------|----------|
| `app/graphs/nl2sql/nodes.py` (prompt_build_node) | 날짜 동적 주입, table_catalog 메타데이터 주입 |
| `app/core/database/schema_loader.py` | catalog 컬럼 설명 병합 옵션 |

---

## 부록: 관련 소스 파일

| 파일 | 역할 |
|------|------|
| `app/graphs/nl2sql/graph.py` | NL2SQL 그래프 정의 (노드 등록, 엣지 연결) |
| `app/graphs/nl2sql/nodes.py` | 14개 노드 함수 (핵심 로직) |
| `app/graphs/nl2sql/state.py` | NL2SQLState TypedDict 정의 |
| `app/core/database/schema_loader.py` | DB 스키마 메타데이터 로드 + LLM용 설명 생성 |
| `app/core/database/table_catalog.py` | 테이블 카탈로그 (비즈니스 메타데이터) |
| `app/core/database/sql_executor.py` | SQL 검증 + 실행 |
| `app/core/database/external.py` | 외부 DB 연결 관리 (Oracle/PostgreSQL) |
| `app/core/database/adapters/oracle.py` | Oracle 어댑터 |
| `app/core/llm/prompt_service.py` | 프롬프트 관리 (DB 조회) |
| `app/core/vector/vector_store.py` | 벡터 검색 (Few-shot 예제 검색) |

# NL2SQL 아키텍처 정의서

## 승인 및 개정이력

| 날짜 | 버전 | 변경내용 | 작성자 |
|------|------|----------|--------|
| 2025.12.03 | 1.0 | 최초 작성 | |

---

## 1. 시스템 아키텍처 개요

### RAG 및 NL2SQL 기술을 통합한 차세대 엔터프라이즈 검색 솔루션

본 시스템은 사내 문서(HR 등) 및 데이터베이스를 자연어로 검색할 수 있는 **AI 기반 챗봇**입니다.

### 주요 특징

- **RAG(Retrieval Augmented Generation)와 NL2SQL(Natural Language to SQL) 기술 결합**
  - 사용자 질의에 최적화된 답변 제공
  
- **AI Agent(ReAct 패턴) 기반 자율적 도구 선택**
  - 복잡한 멀티스텝 질문을 단일 요청으로 처리
  
- **세션 기반 멀티턴 대화 지원**
  - 이전 맥락을 유지하며 연속적인 질의응답 가능

---

## 2. 시스템 아키텍처 구성

### 2.1 하드웨어 아키텍처

#### WEB 서버
| 항목 | 사양 |
|------|------|
| CPU | 4 Core |
| Memory | 4GB |
| HDD | 30GB |
| OS | Linux(64bit) / Windows |

#### APPLICATION 서버
| 항목 | 사양 |
|------|------|
| CPU | 4 Core |
| Memory | 4GB |
| HDD | 30GB |
| OS | Linux(64bit) / Windows |

#### DATABASE 서버
| 항목 | 사양 |
|------|------|
| CPU | 4 Core |
| Memory | 4GB |
| HDD | 50GB |
| OS | Linux(64bit) / Windows |

> **Note:** 최초 개발 시는 1PC에 통합 개발/테스트

---

### 2.2 소프트웨어 구성

#### Frontend
- **Framework:** Vue.js v3.3.13
- **UI Library:** Element Plus 2.2.4
- **State Management:** Vuex 4.10
- **Web Technologies:** HTML5.0 / CSS
- **Web Server:** Nginx 1.3

#### Backend
- **Language:** Python 3.12+
- **API Framework:** FastAPI 0.109.0+
- **ASGI Server:** UVICORN 0.27.0+
- **AI Framework:** LangChain 1.2+ / LangGraph
- **Runtime:** OpenJDK 17+
- **OS:** Windows / Linux
- **기타 라이브러리:** pydantic 등

#### Database
- **RDBMS Options:**
  - PostgreSQL 16+
  - Oracle 21+
  
- **Vector Database:**
  - PGVector (PostgreSQL Extension)
  - Qdrant
  - 기타 VectorDB

#### LLM
- **Model:** ChatGPT-4
- **Embedding:** Text-Embedding-large

---

## 3. 검색 플로우(Flow)

### 3.1 기본 Flow

```
┌─────────────┐      ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
│  CHAT UI    │      │   APP서버   │      │  DATABASE   │      │     LLM     │
│  (Vue.js)   │      │ (LangGraph) │      │  (업무DB)   │      │  (ChatGPT)  │
└─────────────┘      └─────────────┘      └─────────────┘      └─────────────┘
       │                     │                     │                     │
       │  ① User Question    │                     │                     │
       │─────────────────────>                     │                     │
       │                     │                     │                     │
       │  ② 질문/세션 정보   │                     │                     │
       │─────────────────────>                     │                     │
       │                     │                     │                     │
       │                     │  ③ Schema 조회      │                     │
       │                     │────────────────────>│                     │
       │                     │     (메타데이터)    │                     │
       │                     │                     │                     │
       │                     │  ④ SQL 생성 요청    │                     │
       │                     │────────────────────────────────────────>│
       │                     │    (질문 + 스키마)  │                     │
       │                     │                     │                     │
       │                     │  ⑤ SQL 실행         │                     │
       │                     │────────────────────>│                     │
       │                     │<────────────────────│                     │
       │                     │    (실행 결과)      │                     │
       │                     │                     │                     │
       │                     │  ⑥ 답변 생성 요청   │                     │
       │                     │────────────────────────────────────────>│
       │                     │    (질문+SQL+결과)  │                     │
       │                     │                     │                     │
       │  ⑦ 응답 전송        │                     │                     │
       │<─────────────────────                     │                     │
       │  (답변+SQL+데이터)  │                     │                     │
```

#### 상세 프로세스

**① User Question → CHAT UI**
- 사용자가 브라우저(Vue.js 채팅 화면)에 자연어 질문 입력

**② CHAT UI → APP서버**
- 질문/세션 정보를 FastAPI(LangGraph) 백엔드로 전송

**③ APP서버 → TABLE Schema**
- 테이블/컬럼 구조 및 메타데이터 조회
- SQL 생성에 필요한 스키마 정보 수집

**④ APP서버 → LLM (SQL생성) [첫 번째 LLM 호출]**
- 질문 + 스키마를 프롬프트로 전송
- SELECT SQL 생성

**⑤ APP서버 ↔ DATABASE**
- 생성된 SQL 검증 후 DB에서 실행
- 결과 데이터 조회

**⑥ APP서버 → LLM (답변생성) [두 번째 LLM 호출]**
- 질문 + SQL + 실행 결과를 전송
- 자연어 답변 생성

**⑦ APP서버 → CHAT UI**
- 자연어 답변 + SQL + 결과 데이터를 프론트엔드로 전송
- 화면에 출력

---

## 4. NL2SQL Graph 상세 설계

### 4.1 Graph 상태(State) 정의

| 필드명 | 타입 | 설명 |
|--------|------|------|
| question | str | 사용자 자연어 질문 |
| schema_description | str | DB 스키마 설명 (LLM 제공용) |
| generated_sql | str | 생성된 SQL 쿼리 |
| validated | bool | SQL 검증 통과 여부 |
| validation_error | str | 검증 실패 시 오류 메시지 |
| sql_result | SQLResult | SQL 실행 결과 (columns, rows, row_count) |
| answer | str | 최종 자연어 답변 |
| metadata | Dict | 메타데이터 (llm_model, execution_time_ms 등) |
| request_id | str | 요청 추적용 ID (8자리) |

---

### 4.2 노드 구성 및 역할

| 노드명 | 역할 | LLM 호출 | 입력 | 출력 |
|--------|------|:--------:|------|------|
| **generate_sql** | 자연어 → SQL 변환 | ✅ (1차) | question, schema | generated_sql |
| **validate_sql** | SQL 보안 검증 | ❌ | generated_sql | validated, validation_error |
| **execute_sql** | SQL 실행 | ❌ | generated_sql | sql_result |
| **generate_answer** | 결과 → 자연어 요약 | ✅ (2차) | question, sql, result | answer |
| **handle_error** | 에러 메시지 생성 | ❌ | validation_error | answer |

---

### 4.3 Graph 실행 흐름도ㅂ

```
┌─────────────────┐
│  generate_sql   │ ← LLM 호출 (1차): 질문 + 스키마 → SQL 생성
└────────┬────────┘
         ↓
┌─────────────────┐
│  validate_sql   │ ← 보안 검증: 금지 키워드, 테이블 화이트리스트
└────────┬────────┘
         ↓
    ┌────┴────┐
    │ 검증    │
    │ 성공?   │
    └────┬────┘
    Yes ↓    ↘ No
┌─────────────────┐    ┌─────────────────┐
│  execute_sql    │    │  handle_error   │
└────────┬────────┘    └────────┬────────┘
         ↓                      ↓
┌─────────────────┐            │
│ generate_answer │ ← LLM (2차)│
└────────┬────────┘            │
         ↓                      ↓
      [ END ] ←────────────────┘
```

---

### 4.4 조건부 분기 로직

```python
def _should_execute(state) -> str:
    if state["validated"]:
        return "execute"   # → execute_sql 노드로 이동
    else:
        return "error"     # → handle_error 노드로 이동
```

| 조건 | 분기 | 다음 노드 |
|------|------|-----------|
| validated = True | execute | execute_sql |
| validated = False | error | handle_error |

---

## 5. Input Guardrails (입력 보안)

### 5.1 개요

> **"LLM에 전송되는 사용자 입력에서 민감정보(PII)를 사전 차단하여 정보 유출 방지"**

```
┌──────────┐     ┌─────────────────┐     ┌─────────┐     ┌───────────┐
│  User    │────→│  Input Guard    │────→│   LLM   │────→│ SQL Guard │
│  Input   │     │  (PII 마스킹)   │     │         │     │           │
└──────────┘     └─────────────────┘     └─────────┘     └───────────┘
                        │
                        ├─ 주민번호 마스킹
                        ├─ 카드번호 마스킹
                        ├─ 금지 키워드 탐지
                        └─ 악성 프롬프트 차단
```

### 5.2 처리 방식: Redact vs Mask

민감정보 유형과 상황에 따라 두 가지 처리 방식을 구분하여 적용:

| 방식 | 설명 | 적용 대상 | 처리 결과 |
|------|------|----------|-----------|
| **Redact (삭제)** | 민감정보를 완전히 제거하고 요청 차단 | 비밀번호, PIN, 보안코드 | 요청 거부 + 경고 메시지 |
| **Mask (마스킹)** | 민감정보를 대체 문자열로 치환 후 처리 계속 | 주민번호, 카드번호, 연락처 | [MASKED] 처리 후 LLM 전송 |

**적용 기준:**
- **Redact**: 해당 정보가 질문에 포함되면 안 되는 경우 (보안 키워드)
- **Mask**: 정보 자체는 질문 맥락에 필요하나 원본 노출이 불필요한 경우

### 5.3 마스킹 대상 (PII 패턴)

| 유형 | 패턴 예시 | 처리 방식 | 결과 |
|------|----------|:---------:|------|
| 주민번호 | 900101-1234567 | Mask | [주민번호_MASKED] |
| 카드번호 | 1234-5678-9012-3456 | Mask | [카드번호_MASKED] |
| 계좌번호 | 110-123-456789 | Mask | [계좌번호_MASKED] |
| 휴대폰 | 010-1234-5678 | Mask | [휴대폰_MASKED] |
| 이메일 | user@example.com | Mask | [이메일_MASKED] |

### 5.4 금지 키워드 (Redact 대상)

```
password, 패스워드, 비밀번호, 비번, PIN, secret
```
- 해당 키워드 포함 시 경고 로그 기록 및 질문 거부

### 5.5 설정 위치

| 항목 | 위치 |
|------|------|
| PII 패턴 (Mask) | `app_settings` 테이블 (category='input_guard') |
| 금지 키워드 (Redact) | `app_settings` 테이블 (category='input_guard') |
| 구현 파일 | `app/services/input_guard.py` |

---

## 6. SQL 보안 설계

### 6.1 검증 프로세스

```
① 빈 SQL 확인 → ② 금지 키워드 검사 → ③ SQL 파싱 → ④ SELECT만 허용 → ⑤ 테이블 화이트리스트 → ⑥ LIMIT 권장
```

### 6.2 금지 키워드 목록 (12개)

| 카테고리 | 키워드 |
|----------|--------|
| DDL | DROP, ALTER, CREATE, TRUNCATE |
| DML | DELETE, UPDATE, INSERT |
| 권한 | GRANT, REVOKE |
| 실행 | EXEC, EXECUTE, DECLARE, CURSOR |

### 6.3 테이블 화이트리스트

```
허용 테이블: employee, department, job_history, performance_review, salary
```
- 설정 위치: `app_settings` 테이블 (external_database.allowed_tables)
- 미등록 테이블 접근 시 검증 실패

### 6.4 보안 계층화 (Defense in Depth)

| 계층 | 방어 수단 | 설명 |
|:----:|-----------|------|
| 1 | 키워드 필터링 | 정규식 기반 금지 키워드 검사 |
| 2 | SQL 파싱 | sqlparse로 문법 검증 |
| 3 | SELECT 강제 | read_only_mode로 SELECT만 허용 |
| 4 | 테이블 제한 | 화이트리스트 기반 접근 제어 |
| 5 | 타임아웃 | 30초 statement_timeout |
| 6 | 행 제한 | LIMIT 1000 자동 추가 |

---

## 7. 스키마 관리

### 7.1 핵심 메시지

> **"LLM은 DB 구조를 모른다. 스키마 정보 없이는 정확한 SQL 생성이 불가능하다."**

**왜 스키마 관리가 필요한가?**

| 문제 | 스키마 정보 없을 때 | 스키마 정보 제공 시 |
|------|---------------------|---------------------|
| 테이블명 | LLM이 추측 → 오류 발생 | 정확한 테이블명 사용 |
| 컬럼명/타입 | 잘못된 컬럼 참조 | 올바른 컬럼 및 타입 사용 |
| 테이블 관계 | JOIN 조건 누락/오류 | FK 기반 정확한 JOIN |
| 데이터 형식 | 날짜/숫자 포맷 오류 | 샘플 데이터로 형식 학습 |

---

### 7.2 스키마 관리 아키텍처 (PPT 1장)

```
┌─────────────────────────────────────────────────────────────────────┐
│                        스키마 관리 흐름                              │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   PostgreSQL    │────→│  Schema Loader  │────→│   LLM Prompt    │
│ information_    │     │  (메타데이터    │     │  (스키마 설명   │
│    schema       │     │   JSON 변환)    │     │   마크다운)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   DB 스키마 조회         메모리 캐싱              프롬프트에 포함
   (테이블/컬럼/관계)     (성능 최적화)           (SQL 생성 컨텍스트)


┌─────────────────────────────────────────────────────────────────────┐
│  수집 정보: 테이블명, 컬럼(타입/nullable), PK, FK, 인덱스, 샘플     │
└─────────────────────────────────────────────────────────────────────┘
```

**관리 방식 요약**

| 항목 | 설명 |
|------|------|
| **데이터 소스** | PostgreSQL `information_schema` 실시간 조회 |
| **저장 위치** | 메모리 캐시 (성능 최적화) |
| **테이블 필터링** | `allowed_tables` 화이트리스트 (보안) |
| **민감정보 처리** | salary.base_salary → `'***'` 마스킹 |

---

### 7.3 메타데이터 구조 및 활용 (PPT 2장)

**수집 메타데이터 항목**

| 항목 | 설명 | SQL 생성 시 활용 |
|------|------|------------------|
| **columns** | 컬럼명, 타입, nullable | SELECT/WHERE 절 작성 |
| **primary_key** | 기본 키 컬럼 | 고유 식별자 조건 |
| **foreign_keys** | 외래 키 관계 | 테이블 JOIN 조건 |
| **indexes** | 인덱스 목록 | 성능 최적화 힌트 |
| **sample_data** | 샘플 데이터 (3행) | 데이터 형식 예시 |

**LLM 프롬프트 변환 예시**

```
## 테이블: employee
컬럼:
  - emp_id: integer (NOT NULL) ← PK
  - name: character varying (NOT NULL)
  - hire_date: date (NULL 가능)
  - dept_id: integer (NULL 가능) ← FK → department.dept_id
샘플 데이터:
  1. {'emp_id': 1, 'name': '김철수', 'hire_date': '2020-03-15'}
```

**캐싱 전략**

| 항목 | 값 |
|------|-----|
| 초기 로드 | NL2SQL Graph 초기화 시 1회 |
| 수동 갱신 | `refresh=True` 파라미터 또는 서버 재시작 |

---

### 7.4 상세 내용 (참고용)

<details>
<summary>메타데이터 JSON 구조 전체 예시 (클릭하여 펼치기)</summary>

```json
{
  "database": "business_data",
  "schema": "business",
  "tables": [
    {
      "name": "employee",
      "columns": [
        {"name": "emp_id", "type": "integer", "nullable": false},
        {"name": "emp_no", "type": "character varying", "nullable": false, "max_length": 20},
        {"name": "name", "type": "character varying", "nullable": false, "max_length": 100},
        {"name": "hire_date", "type": "date", "nullable": true},
        {"name": "dept_id", "type": "integer", "nullable": true}
      ],
      "primary_key": ["emp_id"],
      "foreign_keys": [
        {"column": "dept_id", "references_table": "department", "references_column": "dept_id"}
      ],
      "indexes": ["employee_pkey", "idx_employee_emp_no"],
      "sample_data": [
        {"emp_id": 1, "emp_no": "E001", "name": "김철수", "hire_date": "2020-03-15", "dept_id": 1}
      ]
    },
    {
      "name": "department",
      "columns": [
        {"name": "dept_id", "type": "integer", "nullable": false},
        {"name": "dept_name", "type": "character varying", "nullable": false, "max_length": 100}
      ],
      "primary_key": ["dept_id"],
      "foreign_keys": [],
      "sample_data": [{"dept_id": 1, "dept_name": "개발팀"}]
    },
    {
      "name": "salary",
      "columns": [
        {"name": "emp_id", "type": "integer", "nullable": false},
        {"name": "base_salary", "type": "numeric", "nullable": true}
      ],
      "sample_data": [{"emp_id": 1, "base_salary": "***"}]
    }
  ]
}
```

</details>

---

## 8. 프롬프트 설계

### 8.1 SQL 생성 프롬프트

| 구분 | 내용 |
|------|------|
| **역할** | PostgreSQL 전문가 |
| **System** | "사용자의 자연어 질문을 PostgreSQL SQL 쿼리로 변환해주세요." + {스키마 정보} |
| **User** | "질문: {question}\n\nSQL만 출력하세요 (설명 없이)." |
| **Temperature** | 0 (결정적 생성) |

### 8.2 답변 생성 프롬프트

| 구분 | 내용 |
|------|------|
| **역할** | 데이터 분석 전문가 |
| **System** | "SQL 쿼리 결과를 사용자가 이해하기 쉽게 자연어로 요약해주세요." |
| **User** | "질문: {question}\n실행된 SQL: {sql}\n조회 결과: {rows}" |
| **Temperature** | 0 (일관성 있는 답변) |

### 8.3 프롬프트 관리

- **저장 위치**: `app_settings` 테이블 (category='prompt')
- **캐시**: 5분 TTL
- **우선순위**: DB → 코드 기본값

---

## 9. 에러 처리

### 9.1 예외 클래스 구조

```
Exception
├── SQLValidationError    # 검증 실패
│   - 금지 키워드 사용
│   - 테이블 화이트리스트 위반
│   - 문법 오류
│
└── SQLExecutionError     # 실행 실패
    - DB 연결 오류
    - 타임아웃 (30초 초과)
    - 런타임 에러
```

### 9.2 에러 응답 형식

**사용자 응답 메시지**:
```
SQL 생성 또는 실행 중 오류가 발생했습니다.

오류 내용: {error_msg}

다음 사항을 확인해주세요:
1. 질문이 데이터베이스 스키마에 맞는지 확인
2. 테이블명과 컬럼명이 정확한지 확인
3. 질문을 더 구체적으로 작성
```

**API 응답 구조**:
```json
{
  "answer": "SQL 생성 또는 실행 중 오류가 발생했습니다...",
  "sql": "",
  "result": null,
  "query_type": "nl2sql",
  "metadata": {}
}
```

---

## 10. 설정값 정의

### 10.1 NL2SQL 관련 설정

| 설정명 | 기본값 | 설명 |
|--------|:------:|------|
| sql_timeout_seconds | 30 | SQL 실행 타임아웃 (초) |
| sql_max_rows | 1000 | 최대 반환 행 수 |
| read_only_mode | True | SELECT만 허용 |
| allow_ddl | False | DDL 허용 여부 |
| llm_model | gpt-4o | LLM 모델명 |
| llm_temperature | 0 | SQL 생성 온도 |

### 10.2 설정 우선순위

```
① DB (app_settings 테이블)  ← 최우선 (Admin UI에서 변경 가능)
        ↓
② 환경변수 (.env 파일)
        ↓
③ 코드 기본값 (config.py)   ← 최하위
```

**실시간 반영**: DB 설정 변경 시 서버 재시작 없이 즉시 적용

# 테넌트 관리 설계서

> **문서 버전**: 2.0
> **작성일**: 2026-02-14
> **상태**: Draft
> **관련 문서**: `docs/design/user_permission_system.md`

---

## 1. 개요

### 1.1 목적

MUREUM 시스템의 멀티테넌트 데이터 격리 체계를 정의합니다.
총괄관리자(System)는 모든 테넌트의 데이터를 관리하고, 테넌트관리자는 자기 테넌트의 데이터만 접근할 수 있도록 합니다.

### 1.2 테넌트 구조

```
┌──────────────────────────────────────────────────────────────────┐
│  [Tenant 1] System (예약 - 총괄관리 전용)                        │
│    └── admin        (SYSTEM_ADMIN, GLOBAL, is_superuser=true)   │
│                                                                  │
│  [Tenant 2~N] 업무 테넌트                                        │
│    ├── tenant_admin (TENANT_ADMIN, TENANT)                      │
│    └── user01      (USER, USER)                                 │
└──────────────────────────────────────────────────────────────────┘
```

### 1.3 역할-스코프 매핑

| 역할 | role_code | scope_type | tenant_id | 데이터 접근 범위 |
|------|-----------|-----------|:---------:|-----------------|
| 총괄관리자 | SYSTEM_ADMIN | GLOBAL | 1 (System) | **전체 테넌트** |
| 테넌트관리자 | TENANT_ADMIN | TENANT | 2~N | **자기 테넌트만** |
| 일반사용자 | USER | USER | 2~N | **본인 데이터만** |

### 1.4 전역 tenant_id 규칙

```
tenant_id = '0'   → 전역 (모든 테넌트에 적용되는 기본값/공용 데이터)
tenant_id = '1'   → System 테넌트 (총괄관리자 소속)
tenant_id = '2'   → DEMO 테넌트
tenant_id = '5'   → 현대A
tenant_id = '6'   → 현대B
```

**'0'을 전역으로 사용하는 이유**:
- `UNIQUE (category, key, tenant_id)` 제약조건에서 UPSERT가 정상 작동
- NULL은 PostgreSQL에서 `NULL != NULL`이므로 `ON CONFLICT`가 작동하지 않음
- `IN ('0', '2')` 등 단순 비교 가능 (`IS NULL` 별도 처리 불필요)
- `tb_tenant` 테이블에 실제 tenant_id=0 레코드는 존재하지 않음 (가상 ID)

---

## 2. 현재 상태 분석

### 2.1 DB 스키마 - tenant_id 컬럼 현황

| 테이블 | tenant_id 존재 | 타입 | 현재 활용 |
|--------|:---:|------|:---:|
| `tb_tenant` | O | `integer` (PK) | O |
| `tb_user` | O | `integer` (FK) | O |
| `tb_docs` | O | `varchar` | **X** (항상 NULL → '0'으로 마이그레이션 필요) |
| `tb_app_settings` | O | `varchar` | **O** ('0' = 전역, 마이그레이션 완료) |
| `tb_api_history` | O | `varchar` | O (middleware에서 저장) |
| `tb_code` | O | `varchar` | 전역 관리 (테넌트 격리 불필요) |
| `tb_user_menu` | - | - | user_id 기반 |

### 2.2 애플리케이션 코드 - 테넌트 필터링 현황

| 기능 | 서비스 파일 | 필터링 적용 | 비고 |
|------|-----------|:---:|------|
| 사용자 관리 | `user_service.py` | **O** | `_check_scope_access()` |
| API 이력 | `history.py` | **O** | `_apply_scope_filter()` |
| 지식문서 관리 | `document_service.py` | **X** | 전체 문서 노출 |
| RAG 검색 | `vector_store.py` | **X** | 전체 문서 검색 |
| 시스템 설정 | `settings_service.py` | **X** | 전체 설정 노출 |
| 코드 관리 | `code_service.py` | - | 전역 관리 (격리 불필요) |
| NL2SQL | `nl2sql_service.py` | **X** | 비즈니스 DB에 테넌트 조건 없음 |

### 2.3 현재 데이터

```
tb_tenant:
  1 - SYSTEM    (시스템)        ← 총괄관리 전용
  2 - DEMO      (데모 테넌트)
  5 - HYNDAI_A  (현대A)
  6 - HUNDAI_B  (현대B)

tb_user:
  admin        → tenant_id=1, SYSTEM_ADMIN, GLOBAL, is_superuser=true
  tenant_admin → tenant_id=2, TENANT_ADMIN, TENANT
  user01       → tenant_id=2, USER, USER
```

---

## 3. 테넌트 격리 설계

### 3.1 데이터 접근 원칙

```
┌─────────────────────────────────────────────────────────────────┐
│                     데이터 접근 결정 흐름                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 메뉴 권한 체크 (tb_user_menu)                               │
│     └── "이 메뉴에 접근할 수 있는가?" (CRUD)                     │
│                                                                 │
│  2. 스코프 기반 데이터 필터 (tb_role.scope_type)                 │
│     ├── GLOBAL  → 관리화면: 필터 없음 (전체), 채팅검색: 공용('0') 기본│
│     ├── TENANT  → WHERE tenant_id IN ('N', '0')                │
│     └── USER    → WHERE tenant_id IN ('N', '0')                │
│                                                                 │
│  '0' = 전역 데이터 (모든 테넌트에 적용)                          │
│  같은 메뉴 권한이라도 scope_type에 따라 데이터 범위가 다름       │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 테이블별 필터링 전략

#### 3.2.1 지식문서 (tb_docs)

**현재**: `tenant_id` 컬럼 존재하나 모두 NULL, 필터링 미적용

**목표**:
- 기존 NULL 데이터를 `'0'`으로 마이그레이션 (공용 문서)
- 총괄관리자: 전체 문서 관리
- 테넌트관리자: 자기 테넌트 문서 + 공용 문서(tenant_id='0') 조회
- RAG 검색 시 테넌트 필터 자동 적용

```sql
-- 마이그레이션: 기존 NULL → '0'
UPDATE tb_docs SET tenant_id = '0' WHERE tenant_id IS NULL;

-- 테넌트 관리자가 문서 목록 조회 시
SELECT * FROM tb_docs
WHERE tenant_id IN ('2', '0')   -- 자기 테넌트 + 공용
  AND usage_type = 'rag_knowledge';

-- 테넌트 관리자가 문서 생성 시
INSERT INTO tb_docs (tenant_id, ...) VALUES ('2', ...);  -- 자동으로 자기 tenant_id 부여

-- 총괄관리자가 공용 문서 생성 시
INSERT INTO tb_docs (tenant_id, ...) VALUES ('0', ...);  -- tenant_id = '0' → 전체 공용
```

**공용 문서 개념**:
- `tenant_id = '0'` → 모든 테넌트에서 접근 가능한 공용 문서
- `tenant_id = '2'` → 테넌트 2 전용 문서
- 총괄관리자만 공용 문서(tenant_id='0') 생성 가능

#### 3.2.2 시스템 설정 (tb_app_settings)

**현재**: `tenant_id` 컬럼에 '0' 설정 완료 (전역 설정)

**목표**:
- 전역 설정 (tenant_id='0'): 총괄관리자만 수정
- 테넌트 설정 (tenant_id='N'): 해당 테넌트 관리자가 수정
- 설정 조회 우선순위: 테넌트 설정 > 전역 설정 > 기본값

```
설정 조회 우선순위 (Fallback Chain):
  1. tb_app_settings WHERE tenant_id = '현재_tenant_id'  (테넌트별 오버라이드)
  2. tb_app_settings WHERE tenant_id = '0'               (전역 설정)
  3. .env 환경변수                                         (환경 설정)
  4. app/config.py 기본값                                   (코드 기본값)
```

**DB 제약조건 변경** (UPSERT 지원):
```sql
-- 기존 제약조건 변경 (테넌트별 설정 지원)
ALTER TABLE tb_app_settings DROP CONSTRAINT app_settings_category_key_key;
ALTER TABLE tb_app_settings ADD CONSTRAINT app_settings_category_key_tenant_key
    UNIQUE (category, key, tenant_id);

-- UPSERT 정상 작동 ('0'은 NULL과 달리 ON CONFLICT에서 동작)
INSERT INTO tb_app_settings (category, key, value, tenant_id, ...)
VALUES ('llm', 'model', 'gpt-4o-mini', '2')
ON CONFLICT (category, key, tenant_id)
DO UPDATE SET value = EXCLUDED.value, updated_at = NOW();
```

**설정 조회 SQL**:
```sql
-- 테넌트 2의 llm.model 조회 (fallback 포함)
SELECT value, tenant_id FROM tb_app_settings
WHERE category = 'llm' AND key = 'model'
  AND tenant_id IN ('2', '0')
ORDER BY CASE WHEN tenant_id = '0' THEN 1 ELSE 0 END  -- 테넌트 설정 우선
LIMIT 1;
```

#### 3.2.3 API 이력 (tb_api_history)

**현재**: 이미 `tenant_id`, `user_id` 필터링 적용됨 (정상 동작)

#### 3.2.4 코드 관리 (tb_code)

**현재**: 테넌트 필터링 없음

**목표**: **전역 관리 유지 (테넌트 격리 불필요)**
- 코드는 선택지 목록 정의 (LLM 모델, 문서 유형 등) → 시스템 마스터 데이터
- "무엇이 선택 가능한가" = 코드(전역), "무엇을 선택했는가" = 설정(테넌트별)
- 총괄관리자만 CODE_MGMT 메뉴 부여, 테넌트관리자에게는 미부여

---

## 4. 구현 계획

### Phase 0: 데이터 마이그레이션 (선행 작업)

```sql
-- tb_app_settings: NULL → '0' (완료)
UPDATE tb_app_settings SET tenant_id = '0' WHERE tenant_id IS NULL;

-- tb_docs: NULL → '0' (TODO)
UPDATE tb_docs SET tenant_id = '0' WHERE tenant_id IS NULL;

-- tb_app_settings: UNIQUE 제약조건 변경 (TODO)
ALTER TABLE tb_app_settings DROP CONSTRAINT app_settings_category_key_key;
ALTER TABLE tb_app_settings ADD CONSTRAINT app_settings_category_key_tenant_key
    UNIQUE (category, key, tenant_id);
```

### Phase 1: 지식문서 테넌트 격리 (핵심)

**영향 범위**: 문서 CRUD + RAG 검색

#### 백엔드 수정

| 파일 | 수정 내용 |
|------|----------|
| `app/api/services/document_service.py` | `list_documents()`, `create_document()` 등에 tenant_id 필터 추가 |
| `app/api/routes/documents.py` | `current_user`에서 tenant_id 추출하여 서비스에 전달 |
| `app/core/vector/vector_store.py` | `search_similar_documents()`에 tenant_id 필터 조건 추가 |
| `app/graphs/rag/nodes.py` | `retrieve_documents_node()`에서 request의 tenant_id를 벡터 검색에 전달 |
| `app/api/services/rag_service.py` | 검색 시 current_user의 tenant_id 전달 |

#### 핵심 변경 패턴

```python
# document_service.py - list_documents()
def list_documents(self, current_user: Optional[UserContext] = None, ...):
    conditions = [...]

    # 테넌트 필터링
    if current_user and current_user.scope_type == "TENANT":
        # 자기 테넌트 + 공용 문서
        conditions.append("tenant_id IN (%s, '0')")
        params.append(str(current_user.tenant_id))
    elif current_user and current_user.scope_type == "USER":
        conditions.append("tenant_id IN (%s, '0')")
        params.append(str(current_user.tenant_id))
    # GLOBAL: 필터 없음

# document_service.py - create_document()
def create_document(self, data, current_user: Optional[UserContext] = None, ...):
    # 테넌트관리자 → 자동으로 자기 tenant_id 부여
    if current_user and current_user.scope_type == "TENANT":
        data["tenant_id"] = str(current_user.tenant_id)
    # GLOBAL → tenant_id는 요청 데이터에서 선택 ('0'=공용)

# vector_store.py - search_similar_documents()
def search_similar_documents(self, query, ..., tenant_id=None):
    if tenant_id:
        filter_conditions.append("tenant_id IN (%s, '0')")
        filter_params.append(tenant_id)
```

#### 프론트엔드 수정

| 파일 | 수정 내용 |
|------|----------|
| `frontend/src/views/admin/DocumentsView.vue` | 총괄관리자: 테넌트 필터 드롭다운 추가 |
| `frontend/src/api/documents.js` | API 호출 시 tenant_id 파라미터 없음 (백엔드에서 자동 처리) |

### Phase 2: 시스템 설정 테넌트 격리

#### 백엔드 수정

| 파일 | 수정 내용 |
|------|----------|
| `app/api/services/settings_service.py` | `get_value()` fallback에 tenant_id 우선순위 적용 |
| `app/api/routes/settings.py` | 테넌트관리자는 자기 테넌트 설정만 조회/수정 |
| `app/core/config/settings_config.py` | 테넌트별 설정 캐시 분리 |

#### 설정 조회 로직 변경

```python
# settings_service.py
def get_value(self, category, key, default, tenant_id='0'):
    """설정 조회: 테넌트 설정 → 전역 설정 → 기본값"""
    db_manager = _get_db_manager()
    with db_manager.get_cursor() as cur:
        # 테넌트 설정 + 전역 설정 한 번에 조회
        cur.execute("""
            SELECT value, tenant_id FROM tb_app_settings
            WHERE category = %s AND key = %s AND tenant_id IN (%s, '0')
            ORDER BY CASE WHEN tenant_id = '0' THEN 1 ELSE 0 END
            LIMIT 1
        """, (category, key, str(tenant_id)))
        row = cur.fetchone()
        return row['value'] if row else default
```

### Phase 3: RAG 검색 + Agent 테넌트 격리

| 파일 | 수정 내용 |
|------|----------|
| `app/api/routes/search.py` | `get_optional_user()` → 인증 사용자의 tenant_id 전달 |
| `app/graphs/agent/tools/rag_tool.py` | Agent의 RAG tool에 tenant_id 전달 |
| `app/graphs/agent/tools/sql_tool.py` | NL2SQL tool에 tenant_id 조건 자동 주입 (비즈니스 DB) |

### Phase 4: 검색이력 테넌트 격리 보완

**현재 상태**: `list_history()`, `statistics()`, `user_*()` 엔드포인트는 이미 scope 필터 적용됨

**보완 대상**: 세션 관련 엔드포인트 + 프론트엔드 테넌트 필터

#### 백엔드

| 파일 | 수정 내용 |
|------|----------|
| `app/api/routes/history.py` | `list_sessions()`에 tenant_id/user_id 추가 + `_apply_scope_filter()` 적용 |
| `app/api/routes/history.py` | `get_session_history()`에 scope 기반 접근 검증 추가 |
| `app/api/routes/history.py` | `delete_session_history()`에 scope 기반 접근 검증 추가 |
| `app/api/services/history_service.py` | `get_session_list()`, `get_session_list_count()`에 tenant_id/user_id 필터 파라미터 추가 |

#### 프론트엔드

| 파일 | 수정 내용 |
|------|----------|
| `frontend/src/views/admin/HistoryView.vue` | GLOBAL scope 사용자에게 테넌트 필터 드롭다운 추가 |
| `frontend/src/views/admin/HistoryView.vue` | GLOBAL scope일 때 테넌트 컬럼 표시 |
| `frontend/src/api/history.js` | `list()` 호출 시 tenant_id 파라미터 전달 |

---

## 5. 화면별 동작 정의

### 5.1 지식문서 관리 화면

| 역할 | 문서 목록 | 문서 생성 | 문서 수정/삭제 |
|------|----------|----------|--------------|
| 총괄관리자 | 전체 문서 (테넌트 필터 드롭다운) | 공용('0') 또는 특정 테넌트 문서 생성 | 모든 문서 |
| 테넌트관리자 | 자기 테넌트 + 공용 문서 | 자기 테넌트 문서만 생성 | 자기 테넌트 문서만 |
| 일반사용자 | (메뉴 접근 불가) | - | - |

### 5.2 시스템 설정 화면

| 역할 | 설정 조회 | 설정 수정 |
|------|----------|----------|
| 총괄관리자 | 전역 설정 + 테넌트별 설정 (드롭다운 전환) | 전역 설정 수정, 테넌트별 설정 수정 |
| 테넌트관리자 | 자기 테넌트 설정 (전역 설정은 읽기 전용) | 자기 테넌트 설정만 수정 |

#### 5.2.1 총괄관리자 설정 화면 UX

```
┌──────────────────────────────────────────────────────────────────┐
│  시스템 설정                                                      │
│  ┌──────────────────────────┐                                    │
│  │ 테넌트: [전역 (기본값) ▼] │  ← 테넌트 선택 드롭다운            │
│  │   ├ 전역 (기본값)  [0]    │                                    │
│  │   ├ DEMO (테넌트 2)       │                                    │
│  │   ├ 현대A (테넌트 5)      │                                    │
│  │   └ 현대B (테넌트 6)      │                                    │
│  └──────────────────────────┘                                    │
│                                                                  │
│  [전역 (기본값) 선택 시 → tenant_id = '0']                       │
│  ┌────────────┬───────────────────────────────────┐              │
│  │ 카테고리     │ 설정값                             │              │
│  ├────────────┼───────────────────────────────────┤              │
│  │ LLM 모델    │ gpt-4o                [수정]      │              │
│  │ Temperature │ 0.1                   [수정]      │              │
│  │ RAG top_k   │ 5                     [수정]      │              │
│  └────────────┴───────────────────────────────────┘              │
│                                                                  │
│  [DEMO (테넌트 2) 선택 시 → tenant_id = '2']                     │
│  ┌────────────┬──────────┬──────────┬─────────┐                  │
│  │ 카테고리     │ 전역 기본값 │ 테넌트 설정 │ 상태     │                  │
│  ├────────────┼──────────┼──────────┼─────────┤                  │
│  │ LLM 모델    │ gpt-4o   │ gpt-4o-mini [수정]│ 오버라이드│                  │
│  │ Temperature │ 0.1      │ -        [설정]  │ 전역 사용│                  │
│  │ RAG top_k   │ 5        │ 3        [수정]  │ 오버라이드│                  │
│  └────────────┴──────────┴──────────┴─────────┘                  │
│                                                                  │
│  * 오버라이드: 테넌트별 설정이 전역 기본값을 덮어씀               │
│  * 전역 사용: 테넌트별 설정 없음 → 전역 기본값 자동 적용          │
│  * [설정] 클릭 → 테넌트별 오버라이드 값 생성                      │
│  * [삭제] 클릭 → 테넌트별 오버라이드 제거 → 전역 기본값으로 복원  │
└──────────────────────────────────────────────────────────────────┘
```

**동작 규칙**:
1. **드롭다운 선택지**: `전역 (기본값)` [value='0'] + `tb_tenant`에서 활성화된 테넌트 목록
2. **전역 선택 시**: 기존 설정 화면과 동일 (category/key/value CRUD, tenant_id='0')
3. **테넌트 선택 시**: 전역 기본값(tenant_id='0') + 테넌트 오버라이드를 나란히 표시
4. **오버라이드 생성**: 테넌트 설정이 없는 항목에서 [설정] 클릭 → `tenant_id = 'N'`으로 INSERT
5. **오버라이드 삭제**: 테넌트 설정이 있는 항목에서 [삭제] 클릭 → 해당 row DELETE → 전역 기본값 복원

#### 5.2.2 테넌트관리자 설정 화면 UX

```
┌──────────────────────────────────────────────────────────────────┐
│  시스템 설정  (DEMO 테넌트)                                       │
│                                                                  │
│  ┌────────────┬──────────┬──────────┬─────────┐                  │
│  │ 카테고리     │ 전역 기본값 │ 내 설정    │ 상태     │                  │
│  ├────────────┼──────────┼──────────┼─────────┤                  │
│  │ LLM 모델    │ gpt-4o   │ gpt-4o-mini [수정]│ 오버라이드│                  │
│  │ Temperature │ 0.1      │ -              │ 전역 사용│                  │
│  │ RAG top_k   │ 5        │ 3        [수정]│ 오버라이드│                  │
│  └────────────┴──────────┴──────────┴─────────┘                  │
│                                                                  │
│  * 전역 기본값은 읽기 전용 (회색 표시)                             │
│  * 내 설정만 수정 가능                                            │
└──────────────────────────────────────────────────────────────────┘
```

**테넌트관리자 제약**:
- 테넌트 선택 드롭다운 없음 (자기 테넌트 고정)
- 전역 기본값 컬럼은 읽기 전용 (수정 불가, 회색 텍스트)
- 자기 테넌트 설정만 생성/수정/삭제 가능

#### 5.2.3 설정 API 변경

```
현재 API:
  GET  /api/admin/v1/settings                    → 전체 설정 조회 (tenant_id='0')
  PUT  /api/admin/v1/settings/{category}/{key}   → 설정 수정 (tenant_id='0')

변경 후 API:
  GET  /api/admin/v1/settings?tenant_id=0         → 전역 설정 (tenant_id='0')
  GET  /api/admin/v1/settings?tenant_id=2         → 테넌트 2 설정 (오버라이드 + 전역 기본값)
  PUT  /api/admin/v1/settings/{category}/{key}?tenant_id=0  → 전역 설정 수정
  PUT  /api/admin/v1/settings/{category}/{key}?tenant_id=2  → 테넌트 2 설정 수정
  DELETE /api/admin/v1/settings/{category}/{key}?tenant_id=2 → 테넌트 2 오버라이드 삭제
```

**응답 형식 (테넌트 선택 시)**:
```json
{
  "items": [
    {
      "category": "llm",
      "key": "model",
      "global_value": "gpt-4o",
      "tenant_value": "gpt-4o-mini",
      "effective_value": "gpt-4o-mini",
      "is_overridden": true
    },
    {
      "category": "llm",
      "key": "temperature",
      "global_value": "0.1",
      "tenant_value": null,
      "effective_value": "0.1",
      "is_overridden": false
    }
  ]
}
```

### 5.3 코드 관리 화면

| 역할 | 접근 |
|------|------|
| 총괄관리자 | CODE_MGMT 메뉴 부여 → 전체 코드 CRUD |
| 테넌트관리자 | CODE_MGMT 메뉴 **미부여** → 접근 불가 |
| 일반사용자 | 접근 불가 |

**사유**: 코드는 "선택 가능한 목록"을 정의하는 시스템 마스터 데이터이므로 전역 관리

### 5.4 검색이력 관리 화면

#### 5.4.1 현재 상태

| 엔드포인트 | scope 필터 | 비고 |
|-----------|:---:|------|
| `GET /history` (목록) | **O** | `_apply_scope_filter()` 적용 |
| `GET /history/statistics` (통계) | **O** | `_apply_scope_filter()` 적용 |
| `GET /history/users/{id}` (사용자 요약) | **O** | USER scope → 본인만 |
| `GET /history/users/{id}/history` (사용자 이력) | **O** | USER scope → 본인만 |
| `GET /history/sessions` (세션 목록) | **X** | tenant_id/user_id 미전달 |
| `GET /history/sessions/{key}` (세션 상세) | **X** | scope 필터 없음 |
| `DELETE /history/sessions/{key}` (세션 삭제) | **X** | scope 필터 없음 |
| `DELETE /history/cleanup` (정리) | O | 메뉴 권한 (SEARCH_HIST, delete) |

**문제점**:
1. `list_sessions()`: tenant_id/user_id를 서비스에 전달하지 않아 전체 세션 노출
2. `get_session_history()`, `delete_session_history()`: scope 필터 미적용
3. 프론트엔드: 총괄관리자용 **테넌트 필터 드롭다운** 없음

#### 5.4.2 백엔드 수정 사항

| 파일 | 수정 내용 |
|------|----------|
| `app/api/routes/history.py` | `list_sessions()`에 tenant_id/user_id 파라미터 추가 + `_apply_scope_filter()` 적용 |
| `app/api/routes/history.py` | `get_session_history()`에 scope 필터 추가 (세션의 tenant_id 검증) |
| `app/api/routes/history.py` | `delete_session_history()`에 scope 필터 추가 |
| `app/api/services/history_service.py` | `get_session_list()`에 tenant_id/user_id 파라미터 추가 |

**핵심 수정: `list_sessions()`**
```python
# 변경 전
@router.get("/sessions")
async def list_sessions(search, request_type, limit, offset, current_user):
    items = history_service.get_session_list(
        search_query=search, request_type=request_type, ...
    )

# 변경 후
@router.get("/sessions")
async def list_sessions(
    tenant_id: Optional[str] = Query(None),
    user_id: Optional[str] = Query(None),
    search, request_type, limit, offset, current_user
):
    tenant_id, user_id = _apply_scope_filter(current_user, tenant_id, user_id)
    items = history_service.get_session_list(
        tenant_id=tenant_id, user_id=user_id,
        search_query=search, request_type=request_type, ...
    )
```

#### 5.4.3 프론트엔드 수정 사항

| 파일 | 수정 내용 |
|------|----------|
| `frontend/src/views/admin/HistoryView.vue` | 총괄관리자(GLOBAL)인 경우 테넌트 필터 드롭다운 추가 |

```
┌──────────────────────────────────────────────────────────────────┐
│  검색 이력                                            [이력 정리] │
│                                                                  │
│  필터:                                                           │
│  ┌──────────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────────┐│
│  │ 테넌트: 전체 ▼│ │ 타입: 전체│ │ 성공/실패 │ │ 날짜범위         ││
│  │  ├ 전체       │ └──────────┘ └──────────┘ └──────────────────┘│
│  │  ├ DEMO       │                                               │
│  │  ├ 현대A      │   ← GLOBAL scope일 때만 표시                  │
│  │  └ 현대B      │                                               │
│  └──────────────┘                                               │
│                                                                  │
│  [테이블: ID | 질문 | 요청ID | 타입 | 사용자 | 테넌트 | 성공 | 시간]│
│  ※ 테넌트 컬럼도 GLOBAL scope일 때만 표시                         │
└──────────────────────────────────────────────────────────────────┘
```

**표시 규칙**:
- 총괄관리자(GLOBAL): 테넌트 필터 드롭다운 + 테넌트 컬럼 표시
- 테넌트관리자(TENANT): 테넌트 필터 없음 (자기 테넌트 고정), 테넌트 컬럼 숨김
- 일반사용자(USER): 본인 이력만 표시

#### 5.4.4 역할별 동작 정의

| 역할 | 이력 목록 | 통계 | 세션 조회 | 이력 삭제 |
|------|----------|------|----------|----------|
| 총괄관리자 | 전체 이력 (테넌트 필터 드롭다운) | 전체 통계 | 전체 세션 | 모든 이력 |
| 테넌트관리자 | 자기 테넌트 이력만 | 자기 테넌트 통계 | 자기 테넌트 세션만 | 자기 테넌트 이력만 |
| 일반사용자 | 본인 이력만 | 본인 통계 | 본인 세션만 | 본인 이력만 |

### 5.5 채팅 검색 (RAG / NL2SQL / Agent)

#### 5.5.1 검색 컨텍스트 원칙

검색 시 **테넌트 컨텍스트**가 다음 두 가지에 영향을 줍니다:

1. **데이터 범위** (RAG): 어떤 테넌트의 문서에서 검색하는가
2. **설정 값** (NL2SQL/Agent): 어떤 테넌트의 LLM 모델, temperature 등을 사용하는가

**"전체 검색" 옵션을 제공하지 않는 이유**:
- RAG: 서로 다른 테넌트의 문서가 섞여서 LLM 답변이 혼란스러움 (현대A 정책 + 현대B 정책 혼합)
- NL2SQL: 어떤 테넌트의 설정(모델, 프롬프트, few-shot)을 적용할지 모호
- Agent: RAG + NL2SQL 혼합 사용 시 동일한 문제 발생

#### 5.5.2 역할별 검색 컨텍스트

| 역할 | 기본 컨텍스트 | 테넌트 선택 | RAG 검색 범위 | NL2SQL 설정 |
|------|:---:|:---:|------------|-----------|
| 총괄관리자 | **공용('0')** | O (드롭다운) | 공용 문서만 | 전역 설정('0') |
| 총괄관리자 (테넌트 선택 시) | 선택된 테넌트 | O | 선택 테넌트 + 공용('0') | 테넌트 설정 → 전역 fallback |
| 테넌트관리자 | 자기 테넌트 | X (고정) | 자기 테넌트 + 공용('0') | 테넌트 설정 → 전역 fallback |
| 일반사용자 | 자기 테넌트 | X (고정) | 자기 테넌트 + 공용('0') | 테넌트 설정 → 전역 fallback |

#### 5.5.3 관리자 채팅 UI

```
┌──────────────────────────────────────────────────────────┐
│  관리자 채팅                                              │
│                                                          │
│  검색 컨텍스트: [공용 (기본) ▼]    ← 총괄관리자만 표시    │
│                  ├ 공용 (기본)      → tenant_id = '0'     │
│                  ├ DEMO             → tenant_id IN ('2','0') │
│                  ├ 현대A            → tenant_id IN ('5','0') │
│                  └ 현대B            → tenant_id IN ('6','0') │
│                                                          │
│  ┌──────────────────────────────────────────────────┐    │
│  │ 재택근무 정책 알려줘                    [전송]    │    │
│  └──────────────────────────────────────────────────┘    │
└──────────────────────────────────────────────────────────┘

* 테넌트관리자: 드롭다운 없음 (자기 테넌트 고정, 라벨만 표시)
* 일반사용자: 드롭다운 없음 (자기 테넌트 고정)
```

#### 5.5.4 검색 흐름별 tenant_id 전달

```
[채팅 입력] → 검색 컨텍스트의 tenant_id 결정
  │
  ├─ RAG 검색:
  │    tenant_id='0' → WHERE tenant_id = '0'           (공용 문서만)
  │    tenant_id='2' → WHERE tenant_id IN ('2', '0')   (DEMO + 공용)
  │
  ├─ NL2SQL 검색:
  │    tenant_id='0' → 전역 설정으로 LLM 호출 (model, temperature, prompt)
  │    tenant_id='2' → DEMO 설정 → 없으면 전역 fallback
  │
  └─ Agent 검색:
       RAG tool → 위 RAG 규칙 적용
       SQL tool → 위 NL2SQL 규칙 적용
       설정 → 위 NL2SQL 규칙 적용
```

### 5.6 사용자 관리 화면

| 역할 | 사용자 목록 | 사용자 생성 | 역할/테넌트 선택 |
|------|-----------|-----------|---------------|
| 총괄관리자 | 전체 사용자 (테넌트 필터) | 모든 역할/테넌트 선택 가능 | 모든 옵션 표시 |
| 테넌트관리자 | 자기 테넌트 사용자만 | TENANT_ADMIN, USER만 | 자기 테넌트 고정 |

---

## 6. DB 스키마 참고

### 6.1 tenant_id 타입 불일치 이슈

현재 `tb_tenant.tenant_id`는 `integer`이지만, `tb_docs`, `tb_app_settings`, `tb_api_history`의 `tenant_id`는 `varchar`입니다.

**대응 방안**: 현 상태 유지 (varchar로 통일 사용)
- 비교 시 `str(current_user.tenant_id)` 변환하여 사용
- 전역 = `'0'` (varchar), 테넌트 = `'1'`, `'2'`, ...
- 향후 필요 시 integer FK로 마이그레이션

### 6.2 주요 테이블 관계

```
tb_tenant (1) ──┬── (N) tb_user
                │          ├── tb_user.role_id → tb_role (1:N)
                │          └── tb_user_menu (사용자별 메뉴 CRUD)
                │
                ├── (N) tb_docs          (tenant_id: varchar, '0'=공용)
                ├── (N) tb_app_settings  (tenant_id: varchar, '0'=전역)
                └── (N) tb_api_history   (tenant_id: varchar)
```

### 6.3 tb_app_settings 제약조건 변경

```sql
-- 변경 전: UNIQUE (category, key) → 설정당 1행만 가능
-- 변경 후: UNIQUE (category, key, tenant_id) → 설정당 테넌트별 1행

-- 마이그레이션 SQL
ALTER TABLE tb_app_settings DROP CONSTRAINT app_settings_category_key_key;
ALTER TABLE tb_app_settings ADD CONSTRAINT app_settings_category_key_tenant_key
    UNIQUE (category, key, tenant_id);
```

---

## 7. 구현 우선순위

| 순서 | Phase | 난이도 | 영향도 | 비고 |
|:---:|-------|:---:|:---:|------|
| 0 | 데이터 마이그레이션 | 낮음 | - | NULL → '0' 변환, UNIQUE 변경 |
| 1 | 지식문서 테넌트 격리 | 중 | **높음** | 문서 CRUD + RAG 검색 |
| 2 | 시스템 설정 테넌트 격리 | 중 | 중 | fallback chain 변경 |
| 3 | RAG/Agent 검색 격리 | 중 | **높음** | 벡터 검색 + Agent tool |
| 4 | 검색이력 테넌트 격리 보완 | **낮음** | 중 | 세션 엔드포인트 scope 보완 + 프론트 필터 |

---

## 8. 검증 시나리오

### 8.1 지식문서 격리 검증

```
1. 총괄관리자(admin) 로그인
   → 문서 목록: 전체 문서 표시
   → 공용 문서 생성 (tenant_id='0')
   → 테넌트 A 전용 문서 생성 (tenant_id='2')

2. 테넌트관리자(tenant_admin, tenant_id=2) 로그인
   → 문서 목록: 공용('0') + 자기 테넌트('2') 문서만 표시
   → 문서 생성: tenant_id='2' 자동 부여
   → 다른 테넌트 문서: 보이지 않음

3. RAG 검색
   → 테넌트관리자가 검색: 공용('0') + 자기 테넌트('2') 문서에서만 검색
   → 총괄관리자가 검색: 전체 문서에서 검색
```

### 8.2 설정 격리 검증

```
1. 총괄관리자가 전역(tenant_id='0') LLM 모델 설정: gpt-4o
2. 테넌트 A 관리자가 테넌트 설정(tenant_id='2') 추가: gpt-4o-mini
3. 테넌트 A 사용자가 검색 → gpt-4o-mini 사용 (테넌트 설정 우선)
4. 테넌트 B 사용자가 검색 → gpt-4o 사용 (전역 설정 '0' fallback)
5. 테넌트 A 관리자가 오버라이드 삭제 → gpt-4o 사용 (전역 복원)
```

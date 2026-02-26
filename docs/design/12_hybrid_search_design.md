# 하이브리드 검색 설계 (Hybrid Search + Reranking)

> 최종 수정: 2026-02-26
> 상태: 설계 완료 / 구현 예정
> 버전: v2.1 (keyword_extraction llm 모드 제거, rule 모드 suffix 제거 강화)

---

## 1. 개요

### 1.1 목적

현재 MUREUM RAG 시스템은 pgvector 코사인 유사도 기반의 **순수 벡터 검색**만 수행한다.
벡터 검색은 의미적 유사성에 강하지만 아래 케이스에서 한계가 있다.

| 케이스 | 현재 문제 |
|--------|---------|
| `"법인카드 사용 규정"` | 임베딩이 "법인카드"를 의미적으로 일반화 → 관련 없는 문서 혼입 |
| `"ISO 27001 인증"` | 고유 약어는 임베딩 공간에서 분산 → 결과 없음 |
| `"재택"` → `"재택근무 정책"` | 부분 단어 매칭 불가 → 낮은 유사도 점수 |
| `"재턱근무"` (오타) | 벡터 공간에서 이탈 → 결과 없음 |
| `"문서 HR-001을 찾아줘"` | 식별자 직접 조회가 필요하지만 의미 검색 시도 |
| `"연차휴가 처리 방법 알려줘"` | pg_trgm에 긴 자연어 그대로 넣으면 조사·어미 노이즈 |

### 1.2 해결 방향

```
[벡터 검색]  원본 전체 쿼리 → 의미적 유사도 기반 후보군
     +
[키워드 검색] 추출 키워드만 → pg_trgm word_similarity 기반 후보군
     ↓
[RRF 융합]  두 순위를 합산 → 최종 순위 결정
     ↓
[리랭킹]    LLM 또는 Cross-Encoder로 최종 정밀 정렬 (선택적)
```

### 1.3 쿼리 종류별 처리 전략

벡터 검색과 키워드 검색은 **최적 입력이 다르다**.

| 검색 유형 | 최적 입력 | 이유 |
|----------|---------|------|
| 벡터 검색 | 원본 전체 자연어 | 문장 전체가 의미적 맥락 포함 |
| pg_trgm 검색 | 핵심 키워드만 | 조사·어미가 trigram pool 오염 → 점수 희석 |
| 직접 조회 | 패턴 매칭 (regex) | `"HR-001"` 같은 식별자는 의미 검색 불필요 |

이를 처리하기 위해 **`query_analysis_node`** 를 파이프라인 맨 앞에 추가한다.

---

## 2. RAG 그래프 흐름 (최종)

### 2.1 그래프 구조

```
현재:
  START → retrieve → generate_answer → END

변경 후:
  START → query_analysis → retrieve → rerank → generate_answer → END
```

조건부 분기(`add_conditional_edges`) 없이 **단순 순차 엣지**만 사용한다.
`retrieve_node`가 `query_analysis_node`의 출력(`search_type`)을 읽어 내부에서 처리 방식을 결정한다.

### 2.2 노드별 역할

| 노드 | 입력 | 출력 | 비고 |
|------|------|------|------|
| `query_analysis_node` | `question` (원본) | `search_type`, `vector_query`, `keyword_query` | 신규 |
| `retrieve_node` | 위 3개 필드 + `filters`, `top_k` | `retrieved_docs` | 기존 retrieve 대체 |
| `rerank_node` | `retrieved_docs`, `question` | `retrieved_docs` (재정렬) | 신규 |
| `generate_answer_node` | `retrieved_docs`, `question` | `answer` | 변경 없음 |

### 2.3 전체 데이터 흐름

```
사용자 질의: "우리회사의 연차휴가 처리 방법 알려줘"
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  query_analysis_node                                    │
│                                                         │
│  ① Doc ID 패턴 감지                                      │
│     regex: [A-Z]{2,}-\d+  → 없음                        │
│     → search_type = "normal"                            │
│                                                         │
│  ② 키워드 추출 (keyword_extraction 설정에 따라)           │
│     none: 원본 그대로 (테스트용)                          │
│     rule: "연차휴가 처리" (불용어+조사 suffix 제거) ★기본  │
│                                                         │
│  출력:                                                   │
│    vector_query  = "우리회사의 연차휴가 처리 방법 알려줘"  │
│    keyword_query = "연차휴가 처리"   (rule 모드 기준)     │
│    search_type   = "normal"                             │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  retrieve_node                                          │
│                                                         │
│  if search_type == "direct_lookup":                     │
│      → title ILIKE '%HR-001%' 직접 조회                  │
│                                                         │
│  else (normal):                                         │
│      ┌──────────────────┐  ┌──────────────────────────┐ │
│      │  Vector Search   │  │  Keyword Search (trgm)   │ │
│      │  vector_query    │  │  keyword_query           │ │
│      │  (원본 전체)      │  │  (추출 키워드)            │ │
│      │  top_k × 2 후보  │  │  top_k × 2 후보          │ │
│      └────────┬─────────┘  └────────────┬─────────────┘ │
│               └──────── RRF Fusion ──────┘              │
│                          top_k 결과                      │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  rerank_node                                            │
│                                                         │
│  reranker_mode 설정에 따라:                              │
│    none          → PassthroughReranker (순서 유지)       │
│    llm           → LLMReranker (gpt-4.1-mini 평가)      │
│    cross_encoder → CrossEncoderReranker (로컬 모델)      │
│                                                         │
│  출력: 상위 reranker_top_n 문서                          │
└─────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────┐
│  generate_answer_node                                   │
│  (기존과 동일)                                           │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 현재 검색 구조 분석

### 3.1 현재 검색 코드 (`app/core/vector/vector_store.py`)

```python
# 현재: 벡터 검색만 수행, 원본 쿼리 임베딩
query_sql = """
    SELECT id, title, doc_type, content, context_data, metadata, language, distance
    FROM (
        SELECT id, title, doc_type, content, context_data, metadata, language,
               embedding <=> %s AS distance   -- pgvector 코사인 거리
        FROM tb_docs
        {where_clause}
    ) subq
    ORDER BY distance
    LIMIT %s
"""
```

키워드 검색, 쿼리 분석, 리랭킹 없음.

### 3.2 tb_docs 테이블 현황 분석

#### 3.2.1 테이블 정의

```sql
CREATE TABLE tb_docs (
    id              int8        NOT NULL DEFAULT nextval('hr_docs_id_seq'),
    tenant_id       varchar(50) NULL,          -- 테넌트 식별자 (NULL=공용)
    usage_type      varchar(20) NULL DEFAULT 'rag',  -- rag | cortex(SQL few-shot)
    title           text        NOT NULL,      -- ★ 직접 조회 및 trgm 검색 대상
    doc_type        text        NOT NULL,      -- policy, guide, faq, notice 등
    language        text        NULL DEFAULT 'ko',
    content         text        NOT NULL,      -- ★ 벡터 임베딩 및 trgm 검색 주요 대상
    original_content text       NULL,          -- 청킹 전 원본 (재청킹용)
    metadata        jsonb       NULL,          -- ★ doc_id, code 등 식별자 저장 가능
    embedding       vector(1536) NULL,         -- pgvector (text-embedding-3-small)
    embedding_model text        NULL DEFAULT 'text-embedding-3-small',
    indexed         bool        NULL DEFAULT false,
    embedded_at     timestamptz NULL,
    chunk_index     int4        NULL DEFAULT 0,
    total_chunks    int4        NULL DEFAULT 1,
    parent_doc_id   int8        NULL,          -- 자기 참조 FK (청크 계층)
    source_type     text        NULL DEFAULT 'ui_input',
    source_file     text        NULL,
    content_hash    text        NULL,
    context_data    text        NULL,          -- 비임베딩 컨텍스트 (SQL/스키마)
    created_at      timestamptz NULL DEFAULT now(),
    updated_at      timestamptz NULL DEFAULT now(),
    CONSTRAINT hr_docs_pkey PRIMARY KEY (id),
    CONSTRAINT hr_docs_parent_doc_id_fkey
        FOREIGN KEY (parent_doc_id) REFERENCES tb_docs(id) ON DELETE CASCADE
);
```

#### 3.2.2 현재 인덱스 현황 (13개)

| 인덱스명 | 타입 | 컬럼 | 용도 |
|---------|------|------|------|
| `idx_hr_docs_embedding` | **IVFFlat** | `embedding` | ★ 벡터 유사도 검색 |
| `idx_hr_docs_metadata` | **GIN** | `metadata` | JSONB 필드 검색 |
| `idx_hr_docs_doc_type` | B-Tree | `doc_type` | 유형별 필터 |
| `idx_hr_docs_language` | B-Tree | `language` | 언어별 필터 |
| `idx_hr_docs_indexed` | B-Tree | `indexed` | 임베딩 완료 필터 |
| `idx_tb_docs_usage_type` | B-Tree | `usage_type` | 용도별 필터 |
| `idx_tb_docs_usage_doc_type` | B-Tree | `usage_type, doc_type` | 복합 필터 |
| `idx_docs_tenant` | B-Tree | `tenant_id` | 테넌트 격리 |
| `idx_docs_tenant_type` | B-Tree | `tenant_id, doc_type` | 테넌트+유형 복합 |
| `idx_docs_tenant_usage` | B-Tree | `tenant_id, usage_type` | 테넌트+용도 복합 |
| `idx_hr_docs_content_hash` | B-Tree | `content_hash` | 중복 방지 |
| `idx_hr_docs_created_at` | B-Tree | `created_at DESC` | 최신 순 정렬 |
| `idx_hr_docs_parent_doc` | B-Tree | `parent_doc_id` | 청크 계층 |

**누락**: `content`, `title` 텍스트 검색 인덱스 없음 → GIN Trigram 인덱스 추가 필요.

#### 3.2.3 데이터 특성 및 검색 전략 매핑

| 특성 | 내용 | 검색 전략 |
|------|------|---------|
| 주요 언어 | 한국어 (`language = 'ko'`) | pg_trgm (언어 독립적) |
| content 길이 | 청크 기준 ~500~1,000자 | `word_similarity` (부분 매칭) |
| title 특성 | 문서명 또는 `"제목 (n/total)"` | `word_similarity` + 직접 조회 |
| 복합어 | 재택근무, 법인카드, 출장비 | pg_trgm trigram 분해로 매칭 |
| 고유 식별자 | HR-001 등 (`metadata` 또는 `title`) | regex 패턴 → 직접 조회 |

---

## 4. query_analysis_node 설계

### 4.1 출력 필드

```python
# 분석 결과를 RAGState에 추가
{
    "search_type":   "normal" | "direct_lookup",
    "vector_query":  str,   # 벡터 검색용 (= 원본 question 그대로)
    "keyword_query": str,   # pg_trgm 검색용 (추출된 키워드 또는 원본)
    "doc_pattern":   str,   # direct_lookup 시 식별자 패턴 (예: "HR-001")
}
```

### 4.2 Doc ID 직접 조회 패턴 감지

```python
DIRECT_LOOKUP_PATTERNS = [
    r'\b[A-Z]{2,}-\d+\b',        # "HR-001", "POL-023", "ISO-27001"
    r'문서\s*번호\s*[A-Z\d\-]+',  # "문서 번호 HR-001"
    r'#\d{3,}',                   # "#1234" (3자리 이상 번호)
]
```

패턴 감지 시 `search_type = "direct_lookup"`, `doc_pattern = "HR-001"` 설정.
이후 `retrieve_node`에서 벡터/키워드 검색을 건너뛰고 `title ILIKE '%HR-001%'` 또는
`metadata->>'doc_id' = 'HR-001'` 직접 조회.

### 4.3 키워드 추출 (pg_trgm용)

#### 4.3.1 문제: 긴 자연어 쿼리의 trigram 노이즈

```
원본 쿼리: "우리회사의 연차휴가를 처리하는 방법에 대해 설명을 해줘"

생성 trigram 예시:
  유효: "연차휴가", "처리하"  ← 실제 매칭에 기여
  노이즈: "우리회", "리회사", "회사의", "하는방", "방법에", "에대해", "해줘" ...

결과: 유효 trigram이 노이즈에 희석 → word_similarity 점수 저하
```

벡터 검색은 반대다. 전체 자연어 문장이 의미적 맥락을 포함하므로 **원본 쿼리 그대로** 사용한다.

#### 4.3.2 키워드 추출 모드 비교

pg_trgm은 **문자(character) 기반 trigram 매칭**이므로 의미적 키워드 재해석이 불필요하다.
LLM이 더 정확한 키워드를 만들어도 trigram 점수 개선 효과는 미미하다.
불용어·조사 제거만으로 trigram 노이즈를 충분히 줄일 수 있다.

| 모드 | 방식 | 추가 지연 | pg_trgm 개선 효과 | 권장 상황 |
|------|------|----------|-----------------|---------|
| `none` | 원본 쿼리 그대로 trgm에 사용 | 0ms | 없음 | 테스트·검증 시 |
| `rule` | 불용어 제거 + 조사 suffix 제거 | ~1ms | 충분 | **기본값 (권장)** |

#### 4.3.3 rule 모드: 규칙 기반 키워드 추출 설계

**처리 2단계**:

```
단계 1: 공백 단위 불용어 제거
  → 독립된 토큰("해줘", "알려줘", "우리회사" 등) 제거

단계 2: 토큰별 조사 suffix 제거
  → 토큰 끝의 조사/어미 패턴 제거 ("연차휴가를" → "연차휴가")
```

```python
# app/core/vector/keyword_extractor.py

# 1단계: 독립 불용어 (공백으로 분리된 토큰 전체가 불용어인 경우)
KO_STOPWORDS = {
    # 요청/의문 표현
    '해줘', '알려줘', '알려', '대해', '대해서',
    '어떻게', '무엇', '무슨', '뭐', '어떤', '어디', '언제', '누가',
    '주세요', '하세요', '궁금', '찾아줘', '찾아', '보여줘', '해주세요',
    # 관계어
    '우리', '우리회사', '회사', '관련', '관한', '위한', '따른',
    # 기타
    '것', '수', '등', '및', '또는', '그리고', '하지만', '있어', '있나요',
}

# 2단계: 토큰 끝에서 제거할 조사/어미 suffix (긴 것 먼저 체크)
KO_PARTICLE_SUFFIXES = [
    '에서', '에게', '으로', '까지', '부터', '한테', '이랑', '하고',
    '는', '은', '를', '을', '가', '이', '의', '에', '로', '도', '만',
]

def extract_keywords_rule(query: str) -> str:
    """
    규칙 기반 한글 키워드 추출 (2단계)

    예시:
      입력:  "우리회사의 연차휴가를 처리하는 방법에 대해 알려줘"
      1단계: ["우리회사의", "연차휴가를", "처리하는", "방법에"]  ← 불용어 제거
      2단계: ["우리회사", "연차휴가", "처리하는", "방법"]       ← suffix 제거
      출력:  "우리회사 연차휴가 처리하는 방법"

      입력:  "연차 휴가는 몇 일 까지 사용할 수 있어"
      1단계: ["연차", "휴가는", "몇", "일"]                    ← 불용어(까지,수,있어) 제거
      2단계: ["연차", "휴가"]                                  ← suffix 제거, 2글자미만 제거
      출력:  "연차 휴가"
    """
```

**처리 결과 예시 모음**:

| 입력 질의 | keyword_query 출력 |
|---------|-----------------|
| `"연차 휴가는 몇 일 까지 사용할 수 있어"` | `"연차 휴가"` |
| `"법인카드 사용 규정은 어떻게 되나요"` | `"법인카드 사용 규정"` |
| `"재택근무 정책이 뭐야"` | `"재택근무 정책"` |
| `"ISO 27001 인증 절차를 알려줘"` | `"ISO 27001 인증 절차"` ← 영문숫자 보존 |
| `"우리회사의 연차휴가를 처리하는 방법"` | `"우리회사 연차휴가 처리하는 방법"` |

**영문·숫자 패턴 보존**: 영문+숫자 토큰은 2글자 미만이어도 제거하지 않음.
suffix 제거 시 결과가 2글자 미만이 되면 원본 토큰 유지.

---

## 5. retrieve_node 설계 (하이브리드)

### 5.1 내부 분기 로직

```python
def retrieve_documents_node(state):
    search_type   = state.get("search_type", "normal")
    vector_query  = state.get("vector_query", state["question"])
    keyword_query = state.get("keyword_query", state["question"])

    if search_type == "direct_lookup":
        # 식별자 직접 조회 (벡터·키워드 검색 생략)
        docs = vector_store.search_by_pattern(
            pattern=state.get("doc_pattern", ""),
            filters=filters,
            tenant_id=tenant_id,
        )
    else:
        # 하이브리드 검색 (search_mode 설정 따름)
        docs = hybrid_search.search(
            vector_query=vector_query,    # 원본 전체 쿼리
            keyword_query=keyword_query,  # 추출된 키워드
            top_k=top_k,
            filters=filters,
            tenant_id=tenant_id,
        )

    state["retrieved_docs"] = docs
    return state
```

### 5.2 직접 조회 SQL (direct_lookup)

```sql
-- title 또는 metadata->>'doc_id' 매칭
SELECT id, title, doc_type, content, context_data, metadata, 1.0 AS similarity_score
FROM tb_docs
WHERE (
    title ILIKE %s                        -- '%HR-001%'
    OR metadata->>'doc_id' = %s           -- 'HR-001' 정확 매칭
    OR metadata->>'code'   = %s           -- 코드 필드
)
AND usage_type = 'rag_knowledge'
{tenant_filter}
ORDER BY
    CASE WHEN title ILIKE %s THEN 0 ELSE 1 END,  -- title 완전 매칭 우선
    created_at DESC
LIMIT %s;
```

### 5.3 하이브리드 검색 (HybridSearchEngine)

#### 5.3.1 search_mode 설정

| 모드 | 동작 |
|------|------|
| `vector` | 기존 벡터 검색만 (하위 호환, 회귀 방지용) |
| `hybrid` | 벡터 + pg_trgm → RRF 융합 **(기본값)** |

#### 5.3.2 pg_trgm word_similarity SQL

```sql
-- pg_trgm 키워드 검색 쿼리
SELECT
    id, title, doc_type, content, context_data, metadata, language,
    GREATEST(
        word_similarity(%s, title),     -- 제목 매칭
        word_similarity(%s, content)    -- 본문 매칭 (긴 텍스트 → word_similarity 필수)
    ) AS keyword_score
FROM tb_docs
{where_clause}
  AND (
    title   %> %s          -- %> 연산자: word_similarity >= threshold (GIN 인덱스 활용)
    OR content %> %s
  )
ORDER BY keyword_score DESC
LIMIT %s;
-- 파라미터: (kw, kw) + filter_params + (kw, kw, fetch_k)
```

**`word_similarity` vs `similarity` 선택 이유**:

```
content = "재택근무 정책은 다음과 같습니다. 주 2회 이내로 재택근무가 가능합니다."

similarity("재택", content)       = 0.03   ← 전체 문자열 대비 너무 낮음 → 사용 불가
word_similarity("재택", content)  = 0.67   ← 텍스트 내 최대 매칭 구간 기준 → 사용
```

긴 content 컬럼은 **반드시 `word_similarity`** 사용.

#### 5.3.3 RRF (Reciprocal Rank Fusion) 융합

```
RRF_score(d) = 1 / (k + rank_vector(d))  +  1 / (k + rank_keyword(d))

k = 60  (상수. 변경 불필요. 논문·산업 표준값)
```

**계산 예시**:

| 문서 | 벡터 순위 | 키워드 순위 | RRF 점수 | 최종 순위 |
|------|----------|-----------|---------|---------|
| A | 1 | 3 | 1/61 + 1/63 = 0.0323 | 2위 |
| B | 2 | 1 | 1/62 + 1/61 = 0.0325 | **1위** |
| C | 3 | - (미등장) | 1/63 = 0.0159 | 4위 |
| D | - (미등장) | 2 | 1/62 = 0.0161 | 3위 |

- B가 키워드에서 1위이므로 최종 1위 → 키워드가 강한 문서가 보완됨
- 한쪽 검색에만 등장한 문서(C, D)도 결과에 포함됨 (union merge)
- 스케일 차이 무관: 벡터 거리(0~1)와 trgm 유사도(0~1) 정규화 불필요

---

## 6. rerank_node 설계

### 6.1 아키텍처 원칙

- `BaseReranker` ABC로 구현체 교체 용이 (팩토리 패턴)
- 모드 변경: Admin UI → Settings에서 실시간 변경 (재시작 불필요)
- `PassthroughReranker`(none)가 기본 → 기존 동작과 완전 동일

### 6.2 디렉토리 구조

```
app/core/reranker/
├── __init__.py              # 패키지 (내용 없음)
├── base.py                  # BaseReranker ABC
├── passthrough.py           # PassthroughReranker (none, no-op)
├── llm_reranker.py          # LLMReranker
├── cross_encoder.py         # CrossEncoderReranker
└── factory.py               # RerankerFactory
```

### 6.3 BaseReranker 인터페이스

```python
# app/core/reranker/base.py
class BaseReranker(ABC):
    @abstractmethod
    async def rerank(
        self,
        query: str,
        documents: List[DocumentSource],
        top_n: int
    ) -> List[DocumentSource]:
        """
        query 기준으로 documents를 재정렬하여 상위 top_n 반환.
        구현체가 어떤 방식이든 동일한 인터페이스를 제공.
        """
        ...
```

### 6.4 LLMReranker

```
전략: 모든 문서를 하나의 LLM 호출로 일괄 평가 (배치 처리, 토큰 절약)
모델: settings_service.get_value("rag", "reranker_llm_model", "gpt-4.1-mini")

[시스템 프롬프트]
문서 관련성 평가 전문가입니다.
주어진 질문에 각 문서의 관련도를 0~10으로 평가합니다.
반드시 JSON 배열로만 답하세요: [점수1, 점수2, ...]

[사용자 프롬프트]
질문: {query}

[문서 1] {title}
{content_snippet_300자}

[문서 2] {title}
{content_snippet_300자}
...

JSON 배열만:
```

**비용 예측**:
- 문서 5개 × 평균 350 토큰 = 약 1,750 토큰/요청
- gpt-4.1-mini: $0.40/M input → 1만 요청 기준 약 $0.007

### 6.5 CrossEncoderReranker

```
권장 모델 (한국어 지원):
┌─────────────────────────────────┬────────┬──────────────┬──────────┐
│ 모델명                           │ 크기   │ 한국어 품질  │ 메모리   │
├─────────────────────────────────┼────────┼──────────────┼──────────┤
│ BAAI/bge-reranker-v2-m3         │ 568MB  │ ★★★★★ 다국어 │ ~1.1GB  │
│ Dongjin-kr/ko-reranker          │ 280MB  │ ★★★★★ 한국어 │ ~550MB  │
│ cross-encoder/ms-marco-MiniLM-L6│ 80MB   │ ★★☆☆☆ 영어   │ ~160MB  │
└─────────────────────────────────┴────────┴──────────────┴──────────┘

기본값: BAAI/bge-reranker-v2-m3 (다국어, 한국어 포함)

구현 주의:
- sentence-transformers CrossEncoder는 동기(sync) API
- asyncio.to_thread()로 래핑 → FastAPI async 환경 블록 방지
- CrossEncoderReranker 싱글톤 유지 (모델 로드 비용 큼)
- Docker: HuggingFace 캐시 볼륨 마운트 권장 (~/.cache/huggingface)
```

### 6.6 RerankerFactory

```python
# app/core/reranker/factory.py
class RerankerFactory:
    _cross_encoder_instance = None  # 싱글톤 (모델 로드 1회)

    @classmethod
    def get(cls, mode: str) -> BaseReranker:
        if mode == "llm":
            return LLMReranker()           # 매번 생성 (설정 동적 반영)
        elif mode == "cross_encoder":
            if cls._cross_encoder_instance is None:
                model = settings_service.get_value(
                    "rag", "reranker_ce_model", "BAAI/bge-reranker-v2-m3"
                )
                cls._cross_encoder_instance = CrossEncoderReranker(model)
            return cls._cross_encoder_instance
        else:  # "none"
            return PassthroughReranker()   # 매번 생성 (무상태)
```

---

## 7. Docker PostgreSQL 환경 및 pg_trgm 활성화

### 7.1 현재 인프라 구성

```
[원격 서버: 115.68.223.220]
│
├── Docker Network: mureum-network
│   ├── mureum-backend (python:3.13-slim)  :19090  컨테이너명: mureum-backend
│   └── PostgreSQL 컨테이너                :5432   컨테이너명: pgvector-db  ★확인됨
│       ├── 데이터베이스: hermesdb
│       ├── 관리 계정:   postgres  (superuser, extension 설치 전용)
│       ├── 앱 계정:     hermesuser (일반 권한, 앱 접속용)
│       └── pg_trgm: contrib 포함 → CREATE EXTENSION 한 줄로 활성화 가능
│
└── /data/files/mureum/ (볼륨)
```

**확인된 접속 명령**:
```bash
# PostgreSQL 컨테이너에 postgres(관리자)로 접속
docker exec -it pgvector-db psql -U postgres -d hermesdb

# hermesuser(앱 계정)로 접속
docker exec -it pgvector-db psql -U hermesuser -d hermesdb
```

**권한 분리 원칙**:
- `CREATE EXTENSION`: postgres(superuser) 전용
- `CREATE INDEX`, `INSERT INTO tb_app_settings`: hermesuser 가능

### 7.2 pg_trgm 활성화 완료 현황 (2026-02-26)

| 단계 | 명령 | 상태 |
|------|------|------|
| STEP 1 | `CREATE EXTENSION IF NOT EXISTS pg_trgm` (postgres 계정으로 실행) | ✅ 완료 |
| STEP 2 | `ALTER DATABASE hermesdb SET pg_trgm.word_similarity_threshold = 0.1` | ✅ 완료 |
| STEP 3 | `CREATE INDEX CONCURRENTLY` — content, title GIN 인덱스 생성 | ✅ 완료 |
| STEP 4 | `tb_app_settings` 설정 추가 | 백엔드 코드 배포 후 실행 |

**STEP 2 — `ALTER DATABASE` vs `SET` 차이**:

```sql
-- ❌ 세션 레벨: 재접속 시 초기화됨
SET pg_trgm.word_similarity_threshold = 0.1;

-- ✅ DB 레벨 영구 적용: 재접속 후에도 유지 — 실제 실행 방법
ALTER DATABASE hermesdb SET pg_trgm.word_similarity_threshold = 0.1;
```

`ALTER DATABASE`는 DB 수준 파라미터로 저장되어 이후 모든 새 접속 세션에 자동 적용된다.
`postgresql.conf` 수정 없이 가능하며, 컨테이너 재시작 후에도 유지된다.

롤백 시: `ALTER DATABASE hermesdb RESET pg_trgm.word_similarity_threshold;` (postgres 계정 필요)

### 7.3 pg_trgm 이란

PostgreSQL **contrib 모듈**. 텍스트를 3글자(trigram) 단위로 분해하여 유사도 검색.

```
"재택근무" → {" 재", " 재택", "재택근", "택근무", "근무 "}
"재택"     → {" 재", " 재택", "재택 "}
```

`word_similarity("재택", "재택근무 정책은 ...")`:
쿼리의 trigram이 긴 텍스트 내에서 **최대로 겹치는 구간**을 기준으로 점수 계산.
→ 긴 문서에서 짧은 키워드 검색에 최적. 언어 독립적(한글 유니코드 그대로 처리).

### 7.4 Docker 이미지별 pg_trgm 가용성

| Docker 이미지 | pg_trgm 포함 | 활성화 방법 |
|--------------|-------------|------------|
| `pgvector/pgvector:pg16` | ✅ | `CREATE EXTENSION IF NOT EXISTS pg_trgm;` |
| `ankane/pgvector` | ✅ | 동일 |
| `postgres:16` (공식) | ✅ | 동일 |
| 커스텀 slim 빌드 | ❌ 가능 | `postgresql-contrib` 패키지 설치 후 활성화 |

### 7.5 활성화 전 확인 방법 (참고)

```bash
# PostgreSQL 컨테이너 이름 확인
docker ps --filter "network=mureum-network" --format "table {{.Names}}\t{{.Image}}\t{{.Status}}"

# pg_trgm 설치 가능 여부 확인
docker exec -it <postgres_container> \
    psql -U hermesuser -d hermesdb \
    -c "SELECT name, default_version, installed_version FROM pg_available_extensions WHERE name = 'pg_trgm';"

# 예상 결과 (활성화 가능한 경우):
#  name    | default_version | installed_version
# ---------+-----------------+-------------------
#  pg_trgm | 1.6             |                    ← installed_version 비어있음 = 비활성

# 이미 활성화된 경우:
docker exec -it <postgres_container> \
    psql -U hermesuser -d hermesdb \
    -c "SELECT extname, extversion FROM pg_extension WHERE extname = 'pg_trgm';"
```

### 7.6 마이그레이션 SQL 요약

전체 스크립트: `docs/sql/migrate_hybrid_search.sql` (별도 파일)

**실행 완료 현황 (2026-02-26 수동 실행)**:

```bash
# 컨테이너명 확인 → pgvector-db
docker ps | grep pgvector

# postgres 계정으로 접속 (STEP 1~2: superuser 필요)
docker exec -it pgvector-db psql -U postgres -d hermesdb
```

```sql
-- [완료] STEP 1: Extension 설치
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- [완료] STEP 2: 임계값 영구 설정 (DB 레벨, 재시작 후에도 유지)
ALTER DATABASE hermesdb SET pg_trgm.word_similarity_threshold = 0.1;

-- [완료] STEP 3: GIN 인덱스 생성 (한 줄씩 실행)
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tb_docs_content_trgm ON tb_docs USING gin (content gin_trgm_ops);
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_tb_docs_title_trgm   ON tb_docs USING gin (title gin_trgm_ops);

-- 확인
SELECT extname, extversion FROM pg_extension WHERE extname = 'pg_trgm';
SELECT indexname, pg_size_pretty(pg_relation_size(indexname::regclass)) AS size
FROM pg_indexes WHERE tablename = 'tb_docs' AND indexname LIKE '%trgm%';
```

**잔여 작업 — STEP 4 설정 추가 (백엔드 코드 배포 후 hermesuser로 실행)**:

```bash
docker cp docs/sql/migrate_hybrid_search.sql pgvector-db:/tmp/
docker exec -it pgvector-db psql -U hermesuser -d hermesdb \
    -f /tmp/migrate_hybrid_search.sql
```

### 7.7 계정별 실행 권한 정리

| 작업 | 필요 계정 | 이유 |
|------|----------|------|
| `CREATE EXTENSION pg_trgm` | **postgres** | superuser 전용 |
| `ALTER DATABASE ... SET` | **postgres** | superuser 전용 |
| `CREATE INDEX CONCURRENTLY` | hermesuser | 일반 DDL 권한 |
| `INSERT INTO tb_app_settings` | hermesuser | 일반 DML 권한 |

### 7.8 롤백 방법

```sql
-- 인덱스만 제거 (extension은 유지)
DROP INDEX CONCURRENTLY IF EXISTS idx_tb_docs_content_trgm;
DROP INDEX CONCURRENTLY IF EXISTS idx_tb_docs_title_trgm;

-- 검색 모드를 벡터 전용으로 되돌리기
UPDATE tb_app_settings SET value = 'vector'
WHERE category = 'rag' AND key = 'search_mode';
```

---

## 8. 설정 (tb_app_settings)

### 8.1 추가할 설정 전체

```sql
INSERT INTO tb_app_settings (category, key, value, value_type, description, is_active, tenant_id)
VALUES
    -- Query Analysis
    ('rag', 'keyword_extraction',     'rule',                    'string',  '키워드 추출 방식: none | rule', true, NULL),
    ('rag', 'direct_lookup_enabled',  'true',                    'boolean', 'Doc ID 패턴 직접 조회 활성화', true, NULL),

    -- Hybrid Search
    ('rag', 'search_mode',            'hybrid',                  'string',  '검색 모드: vector | hybrid', true, NULL),
    ('rag', 'hybrid_rrf_k',           '60',                      'integer', 'RRF 상수 k (기본값 60, 변경 불필요)', true, NULL),
    ('rag', 'hybrid_fetch_k_factor',  '2',                       'integer', '각 검색 후보 수 = top_k × factor', true, NULL),
    ('rag', 'trgm_word_sim_threshold','0.1',                     'float',   'pg_trgm word_similarity 최소 임계값', true, NULL),

    -- Reranker
    ('rag', 'reranker_mode',          'none',                    'string',  '리랭커: none | llm | cross_encoder', true, NULL),
    ('rag', 'reranker_top_n',         '5',                       'integer', '리랭킹 후 최종 반환 문서 수', true, NULL),
    ('rag', 'reranker_llm_model',     'gpt-4.1-mini',            'string',  'LLM 리랭커 모델명', true, NULL),
    ('rag', 'reranker_ce_model',      'BAAI/bge-reranker-v2-m3', 'string',  'Cross-Encoder 모델명 (HuggingFace)', true, NULL)
ON CONFLICT (category, key)
    DO UPDATE SET value = EXCLUDED.value, description = EXCLUDED.description;
```

### 8.2 설정 조합별 동작

keyword_extraction은 `rule`이 기본값이며 `none`은 테스트 목적으로만 사용한다.
정밀도 향상은 reranker_mode로 제어한다.

| keyword_extraction | search_mode | reranker_mode | 특징 |
|-------------------|-------------|--------------|------|
| `none` | `vector` | `none` | 기존과 동일 (회귀 방지·테스트용) |
| `rule` | `hybrid` | `none` | **기본값** (권장 시작점, 추가 비용 없음) |
| `rule` | `hybrid` | `llm` | 정밀도 향상, +0.5~1s (저가 LLM) |
| `rule` | `hybrid` | `cross_encoder` | 최고 품질, 로컬 모델 (+100~300ms) |

---

## 9. 구현 계획

### 9.1 파일 변경 목록

#### 신규 생성

| 파일 | 설명 |
|------|------|
| `app/core/vector/hybrid_search.py` | HybridSearchEngine (RRF 융합 엔진) |
| `app/core/vector/keyword_extractor.py` | KeywordExtractor (rule/llm 모드) |
| `app/core/reranker/__init__.py` | 패키지 (내용 없음) |
| `app/core/reranker/base.py` | BaseReranker ABC |
| `app/core/reranker/passthrough.py` | PassthroughReranker |
| `app/core/reranker/llm_reranker.py` | LLMReranker |
| `app/core/reranker/cross_encoder.py` | CrossEncoderReranker |
| `app/core/reranker/factory.py` | RerankerFactory |
| `docs/sql/migrate_hybrid_search.sql` | pg_trgm + 인덱스 + 설정 마이그레이션 |

#### 수정

| 파일 | 변경 내용 |
|------|---------|
| `app/core/vector/vector_store.py` | `search_by_keyword()`, `search_by_pattern()` 메서드 추가 |
| `app/graphs/rag/state.py` | `vector_query`, `keyword_query`, `search_type`, `doc_pattern` 필드 추가 |
| `app/graphs/rag/nodes.py` | `query_analysis_node` 추가, `retrieve_documents_node` 하이브리드 처리, `rerank_documents_node` 추가 |
| `app/graphs/rag/graph.py` | `query_analysis`, `rerank` 노드 연결 (순차 엣지) |
| `app/graphs/agent/tools/rag_tool.py` | `hybrid_search` 사용으로 교체 |
| `requirements.txt` | `sentence-transformers` 추가 (cross_encoder 활성화 시) |

#### 변경 없음

`rag_service.py`, `search.py`(routes), 모든 models, 프론트엔드, `main.py`

### 9.2 단계별 구현 순서

| 단계 | 작업 | 검증 방법 |
|------|------|----------|
| **1** | `migrate_hybrid_search.sql` 실행 (pg_trgm + GIN 인덱스) | `SELECT extname FROM pg_extension WHERE extname='pg_trgm'` |
| **2** | `vector_store.py`에 `search_by_keyword()`, `search_by_pattern()` 추가 | 단위 테스트 |
| **3** | `keyword_extractor.py` 구현 (none/rule 모드, 불용어+suffix 제거) | "연차 휴가는 몇 일 까지 사용할 수 있어" → "연차 휴가" 검증 |
| **4** | `hybrid_search.py` HybridSearchEngine + RRF 구현 | `search_mode = "hybrid"` 테스트 |
| **5** | `state.py` 필드 추가, `query_analysis_node` 구현 | Doc ID 패턴 감지 테스트 |
| **6** | `nodes.py` + `graph.py` 수정 (4노드 순차 그래프) | 기존 pytest 통과 확인 |
| **7** | Reranker 인터페이스 + PassthroughReranker | `reranker_mode = "none"` 동작 동일 확인 |
| **8** | LLMReranker 구현 | `reranker_mode = "llm"` 설정 후 테스트 |
| **9** | CrossEncoderReranker 구현 | Docker 메모리 확인, `reranker_mode = "cross_encoder"` 테스트 |

---

## 10. 성능 및 운영 고려사항

### 10.1 응답 시간 예측

| 구성 | 추가 지연 | 비고 |
|------|---------|------|
| 기존 (vector only) | 기준 | - |
| + query_analysis (rule) | +1ms | 거의 무시 가능 |
| + hybrid search | +20~50ms | pg_trgm 키워드 검색 |
| + reranker (none) | 0ms | Passthrough |
| + reranker (llm) | +500~1,500ms | gpt-4.1-mini, 문서 5개 기준 |
| + reranker (cross_encoder) | +100~300ms | CPU 추론, GPU 시 더 빠름 |

### 10.2 메모리 요구사항 (Docker)

| 구성 | 추가 메모리 |
|------|-----------|
| hybrid search만 | 0 MB (DB 연산) |
| LLM 리랭킹 | 0 MB (외부 API) |
| CrossEncoder (bge-v2-m3) | +1,100 MB |
| CrossEncoder (ko-reranker) | +550 MB |

CrossEncoder 사용 시 Docker 메모리 제한 확인 필요.
HuggingFace 모델 캐시 볼륨 마운트 권장:

```bash
# deploy-docker.sh docker run에 추가
-v /data/files/mureum/hf_cache:/root/.cache/huggingface
```

### 10.3 폴백(Fallback) 처리

```python
# pg_trgm 미활성화 또는 오류 시 벡터 검색으로 자동 폴백
try:
    keyword_docs = vector_store.search_by_keyword(keyword_query, ...)
    return self._rrf_merge(vector_docs, keyword_docs, top_k)
except Exception as e:
    logger.warning(f"키워드 검색 실패, 벡터 검색 폴백: {e}")
    return vector_docs[:top_k]
```

### 10.4 GIN 인덱스 크기 예측

| 인덱스 | 예상 크기 (1만 문서 기준) | 빌드 시간 |
|--------|------------------------|---------|
| `idx_tb_docs_content_trgm` | content 크기의 약 2~3배 | 2~5분 (CONCURRENTLY) |
| `idx_tb_docs_title_trgm` | title 크기의 약 2~3배 | < 1분 (CONCURRENTLY) |

GIN 인덱스는 삽입 속도가 B-Tree보다 느리지만, 검색 성능은 선형 스캔 대비 10~100배 향상.

---

## 11. 관련 문서

| 문서 | 연관 내용 |
|------|---------|
| [01_ai_workflows.md](01_ai_workflows.md) | RAG 그래프 기본 흐름 |
| [03_database.md](03_database.md) | tb_docs 테이블 구조, pgvector 설정 |
| [06_deployment.md](06_deployment.md) | Docker 배포 환경 |
| [docs/sql/migrate_hybrid_search.sql](../sql/migrate_hybrid_search.sql) | 마이그레이션 SQL 전체 |

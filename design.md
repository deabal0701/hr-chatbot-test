1. 전체 목표 정리

HR 시스템 특성상 크게 두 가지 검색 니즈가 있을 거예요.

자연어 문서 검색 (RAG)

예: “2024년에 입사한 데이터 엔지니어 채용 공고 보여줘”

대상: 채용공고, JD, 인사 규정, 평가 가이드, 교육자료, FAQ 등 “텍스트 문서”

자연어 → 구조화 질의 (NL2SQL)

예: “2023년에 서울 근무이면서 데이터 분석 직군으로 입사한 인원 수를 월별로 집계해줘”

대상: Postgres HR 스키마 (EMPLOYEE, DEPARTMENT, HIRE, PAYROLL 등) 에 대한 통계·조회

요구사항:

상용수준(운영/모니터링/권한 고려)

Python, LangGraph, pgvector, OpenAI 모델 기반

개발 초기엔 text-embedding-3-small 사용, 추후 필요시 -large 업그레이드 여지 확보

2. 전체 아키텍처 개요
2.1 논리 아키텍처 레이어

데이터 레이어 (Postgres + pgvector)

HR 도메인 RDB 스키마

문서용 테이블 (예: hr_docs) + 벡터 컬럼 (embedding vector(1536) 등)

인사 데이터 테이블들 (employee, job_history, salary, department 등)

AI/검색 레이어 (Python 서비스)

FastAPI(or equivalent) + LangGraph 기반 애플리케이션

주요 graph:

RAGGraph: 자연어 문서 검색용

NL2SQLGraph: 자연어 → SQL → 실행 → 결과 정리

pgvector 연동 DAO/Repository 모듈

API/Gateway 레이어

HR 포털 / 사내 시스템이 호출하는 REST API

인증/인가(JWT, SSO 등) + Rate limiting (사내 API Gateway와 연동 가능)

운영/관측 레이어

로깅(요청/응답, 프롬프트, SQL, latency)

메트릭(Prometheus 등)

Trace (OpenTelemetry 등 선택)

3. 데이터 설계 (Postgres + pgvector)
3.1 문서(텍스트)용 테이블 예시
CREATE TABLE hr_docs (
  id              BIGSERIAL PRIMARY KEY,
  title           TEXT,
  doc_type        TEXT,           -- 'policy', 'job_posting', 'faq', …
  language        TEXT,           -- 'ko', 'en'
  content         TEXT,
  metadata        JSONB,          -- {"year":2024,"department":"HR","region":"Seoul"}
  embedding       VECTOR(1536),   -- text-embedding-3-small 차원수에 맞추기
  created_at      TIMESTAMPTZ DEFAULT now(),
  updated_at      TIMESTAMPTZ DEFAULT now()
);

-- pgvector index (검색 스케일 고려)
CREATE INDEX idx_hr_docs_embedding
  ON hr_docs USING ivfflat (embedding vector_l2_ops)
  WITH (lists = 100); -- 데이터량에 따라 튜닝


차원 수는 실제 사용하는 embedding 모델 스펙에 맞춰야 합니다. (OpenAI text-embedding-3-small 은 1536차원)

3.2 HR 구조화 데이터 (예시)
CREATE TABLE employee (
  emp_id        BIGSERIAL PRIMARY KEY,
  emp_no        TEXT UNIQUE,
  name          TEXT,
  gender        TEXT,
  birth_date    DATE,
  hire_date     DATE,
  position      TEXT,
  job_family    TEXT,
  department_id BIGINT,
  work_location TEXT,
  employment_type TEXT, -- 정규직, 계약직 등
  status        TEXT,   -- 재직, 퇴사, 휴직 등
  created_at    TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE department (
  dept_id       BIGSERIAL PRIMARY KEY,
  dept_name     TEXT,
  parent_dept_id BIGINT,
  region        TEXT
);

CREATE TABLE job_history (
  id            BIGSERIAL PRIMARY KEY,
  emp_id        BIGINT REFERENCES employee(emp_id),
  from_date     DATE,
  to_date       DATE,
  department_id BIGINT,
  position      TEXT,
  job_family    TEXT
);

-- 필요에 따라 salary/payroll, performance_review 등 추가

4. 임베딩 파이프라인 설계
4.1 배치/ETL 스타일 임베딩 파이프라인

소스 수집

HR 관련 문서 (PDF/Word/HTML/Markdown)

채용공고/FAQ 등 DB/파일에서 읽기

Chunking

langchain-text-splitter 비슷한 로직 직접 or LangChain/기타 사용

문서 1개 → 여러 chunk (chunk_id, parent_doc_id, offset 등)

길이 기준 토큰 300~800 선

임베딩 생성 (OpenAI text-embedding-3-small)

Python 스크립트 or 별도 embedding-worker 서비스

content → embedding → hr_docs insert/update

재임베딩 전략

모델 교체 시 (small → large)

문서 수정 시

컬럼 분리도 가능: embedding_small, embedding_large

4.2 ETL 코드 뼈대 (아주 간단 예시 느낌)
from openai import OpenAI
import psycopg
from my_chunker import chunk_text

client = OpenAI(api_key="...")

def embed_text(text: str) -> list[float]:
    resp = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return resp.data[0].embedding

def index_documents():
    with psycopg.connect("postgresql://...") as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, title, content, metadata FROM raw_hr_docs WHERE indexed = false")
            rows = cur.fetchall()

            for doc_id, title, content, metadata in rows:
                chunks = chunk_text(content)
                for chunk in chunks:
                    vec = embed_text(chunk)
                    cur.execute("""
                        INSERT INTO hr_docs (title, doc_type, content, metadata, embedding)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (title, metadata.get("doc_type"), chunk, json.dumps(metadata), vec))
                cur.execute("UPDATE raw_hr_docs SET indexed = true WHERE id = %s", (doc_id,))
        conn.commit()

5. 검색 서비스 설계 (LangGraph 중심)
5.1 RAG Graph 개념

입력: 사용자 질문 (자연어)
출력: 답변 텍스트 + 근거 문서(타이틀/링크/스니펫 등)

노드 구성 (LangGraph):

UserInputNode

질문 text 수신

EmbedQueryNode

질문을 같은 embedding 모델로 벡터화

VectorSearchNode

pgvector 쿼리:

SELECT id, title, content, metadata
FROM hr_docs
ORDER BY embedding <-> :query_vec
LIMIT 10;


AnswerLLMNode

LLM (gpt-4.1 등) 호출

retrieved docs를 context로 RAG 프롬프트 구성

“출처 문서를 반드시 인용해라” 등 지시 포함

OutputNode

JSON 응답 구조화:

answer

sources: [ {id, title, metadata, snippet} ]

이걸 LangGraph로 정의해두면, 추후 tool 호출 구조나 **스텝 추가(예: 질문 의도 분류)**를 쉽게 변경 가능.

5.2 NL2SQL Graph 개념

입력: “2023년에 서울에서 근무하는 데이터 엔지니어 입사자 수 월별 통계”
중간:

스키마 메타데이터 적재:

테이블/컬럼 이름, foreign key, 예제 값 등

hr_schema 라는 JSON/문서로 LLM에 제공

IntentClassifierNode

이 질의가 문서 RAG인지, NL2SQL인지, 혼합인지 분류

예: “정책 문서가 궁금하다” → RAG

“입사자 수 통계” → NL2SQL

SQLGeneratorNode

LLM에 아래 정보를 제공:

자연어 질의

스키마 설명(JSON)

“Postgres SQL로만 작성, LIMIT 반드시 추가, 위험한 DDL 금지” 등 제약

LLM이 SQL을 생성

예:

SELECT date_trunc('month', hire_date) AS month,
       COUNT(*) AS hire_count
FROM employee
WHERE hire_date BETWEEN '2023-01-01' AND '2023-12-31'
  AND job_family = '데이터 엔지니어'
  AND work_location LIKE '%서울%'
GROUP BY 1
ORDER BY 1;


SQLValidatorNode (선택적이지만 상용수준에서는 강력 추천)

SQL 파서로 단순 검증 (예: sqlparse, sqlglot 등)

허용되지 않은 키워드(DROP, DELETE, UPDATE, INSERT, ALTER 등)가 있으면 거절

허용된 테이블/뷰만 사용했는지 체크

WHERE/LIMIT 없는 대규모 SELECT 방지 (행 제한)

SQLExecutorNode

psycopg로 Postgres 실행

결과를 Python dict(list[dict])로 변환

ResultToAnswerLLMNode

LLM에 질문 + SQL + 실행 결과 전달

“테이블 형태 결과를 사람이 이해하기 쉬운 자연어 요약 + 간단한 통계/해석” 생성

필요시 “표 데이터를 그대로 JSON으로도 반환”

OutputNode

JSON 구조:

answer: 자연어 요약

sql: 실제 실행된 SQL

rows: 결과 테이블 일부

metadata: 쿼리 시간, row 수 등

6. FastAPI + LangGraph 통합 구조
6.1 디렉터리 구조 예시
app/
  main.py              # FastAPI entry
  graphs/
    rag_graph.py
    nl2sql_graph.py
  services/
    vector_store.py    # pgvector 조회
    sql_executor.py
    schema_loader.py
  models/
    hr_schema_def.py   # Pydantic models
  config.py

6.2 FastAPI 엔드포인트 뼈대
from fastapi import FastAPI, Depends
from app.graphs.rag_graph import rag_app
from app.graphs.nl2sql_graph import nl2sql_app

app = FastAPI()

@app.post("/search")
async def search(query: str):
    # Intent 분석 후 RAG or NL2SQL graph 실행
    # 여기선 단순 예시로 RAG만 호출한다고 가정
    result = await rag_app.ainvoke({"question": query})
    return result

@app.post("/nl2sql")
async def search_nl2sql(query: str):
    result = await nl2sql_app.ainvoke({"question": query})
    return result


LangGraph 쪽에서는 rag_app, nl2sql_app 각각 Graph를 정의하고, ainvoke로 실행.

7. 운영/상용 수준 고려사항

권한/보안

HR 데이터는 민감:

API 호출자에 따라 row-level security 또는 필터링

예: HR 담당자만 전체 조회, 일반 관리자는 자신의 부서만 검색

Postgres RLS(row level security) 사용 가능

LLM 프롬프트에 민감한 식별자(주민번호 등)가 직접 노출되지 않도록 마스킹

프롬프트/응답 로깅

질문, 생성된 SQL, 실행 결과, LLM 응답 로그를 audit 테이블에 기록

다만 PII/민감 정보는 마스킹 후 저장

쿼리 가드레일

NL2SQL가 만든 SQL 항상 재검증

read-only 전용 DB 계정 사용

timeout, row limit 설정

성능/캐시

자주 사용하는 통계 질의는 materialized view + 정기 refresh

RAG 검색도 자주 쓰는 질문은 결과 캐싱 (Redis 등) → LLM 호출 비용 절약

테스트/평가 체계

대표적인 HR 질의 셋(예: 100개)을 만들어:

기대 SQL, 기대 결과 샘플 정의

주기적으로 NL2SQL/검색 품질 regression test 수행

8. “더 좋은 방안” / 추가 제안

임베딩 모델 업그레이드 전략

개발/테스트: text-embedding-3-small

운영: 품질 측정 후 필요시 -large or 다른 고성능 모델로 재임베딩

테이블에 embedding_model 컬럼 넣어서 어떤 모델로 계산했는지 구분

LLM 모델 전략

ChatGPT-4 계열 LLM을 기본으로 하되:

NL2SQL: context+tool 사용 전용 system prompt 최적화

문서 RAG: context length 긴 모델 선택 (보고서/규정이 길기 때문)

스키마 메타데이터 자동 생성

Postgres information_schema / pg_catalog 를 기반으로 스키마 메타정보 자동 생성/갱신

컬럼 설명(코멘트)도 LLM을 이용해 자동 보강 가능 (내부 사용용)

NL2SQL + RAG 하이브리드

하나의 질의가 둘 다 필요할 수 있음

예: “2023년 입사자 수 통계를 보여주고, 관련 인사 정책 요약도 같이 알려줘”

LangGraph에서 분기:

NL2SQL Graph → 통계

RAG Graph → 정책 문서 요약

마지막 Node에서 둘을 합쳐 응답

도메인 커스터마이징

HR 도메인 용어 사전 (job family, 직무명, 부서명, 평가 등)

NL2SQL 프롬프트에 “직급/직책/직무” 같이 헷갈리는 용어에 대한 매핑 규칙 포함

장기적으로: 사내 전용 모델 or 파인튜닝

HR 텍스트, 사내 정책/용어로 사내 전용 LLM/파인튜닝을 도입하면:

NL2SQL 정확도 + 문서 요약 품질 향상

초기에는 OpenAI만 써도 충분히 상용구현 가능하니, 2단계 과제로 둬도 됨.

9. 요약 로드맵

1단계 – PoC

Postgres + pgvector 셋업

hr_docs + RAG Graph (LangGraph) 구현

간단한 NL2SQL Graph (몇 개 대표 테이블 기준) 구현

FastAPI API /search, /nl2sql 제공

2단계 – 상용화

HR 전체 스키마 반영, NL2SQL 가드레일 강화

권한/보안/RLS 적용, 로깅/모니터링 도입

캐싱/성능 튜닝 (index, mv, pgvector list 튜닝)

3단계 – 고도화

하이브리드 질의 (RAG + NL2SQL 혼합)

도메인 사전/용어집 적용

재임베딩/모델 업그레이드 전략 실행

사용자 피드백 기반 질의/응답 품질 개선 루프 구축

원하시면 다음 단계로는:

실제 pgvector 쿼리 코드 (Python + psycopg) 예제

LangGraph로 RAG / NL2SQL workflow를 정의한 구체적인 코드 뼈대

HR 대표 질의 20~30개를 정의해서 “테스트 벤치”로 쓸 수 있는 JSON 스펙

까지 바로 같이 짜볼게요.


# UI 기획
1. UX 컨셉 먼저 정리

이 시스템은 기본적으로 “검색 한 줄 + 결과” 구조인데, 실제로는:

자연어 문서 검색 (RAG)

자연어 → 통계/리포트 (NL2SQL)

두 가지를 동시에 다뤄야 합니다.
그래서 UX는:

”검색창은 하나”

결과는 탭으로 분리 (예: 요약, 표/그래프, SQL, 근거 문서)

사용자는 “모드 선택”을 하거나, “자동 판별”에 맡길 수 있게

이 느낌으로 가져가면, 사용자가 “복잡한 AI 구조”를 의식하지 않고, 그냥 “검색 시스템”처럼 쓸 수 있습니다.

2. 전체 화면 구성 (페이지 플로우)
2.1 주요 페이지

검색 화면 (핵심) – /search

상단: 검색 바 + 모드 선택 + 필터

중단: 결과 영역 (NL2SQL / RAG)

하단/우측: 최근 검색, 추천 질의

내 검색 히스토리 / 리포트 – /history

내가 했던 질의 목록

특정 질의를 눌러 다시 실행 / 수정

“리포트로 저장” 기능

저장된 리포트 / 대시보드 – /reports

자주 쓰는 통계 질의를 저장 (예: “월별 입사자 수”, “부서별 퇴사율”)

카드 형태 대시보드

관리자 / 어드민 화면 – /admin/*

/admin/schema : 스키마 설명, 테이블/컬럼 구조 표시

/admin/logs : NL2SQL 생성 SQL, 실행 로그, 에러 모니터링

/admin/settings : 모델 설정, 임베딩 설정, RLS 정책 설명 등

3. 검색 화면 상세 설계 (/search)
3.1 레이아웃

대략 이런 레이아웃을 생각해볼 수 있습니다:

상단 고정 헤더:

로고 / 시스템 이름

환경(운영/개발), 사용자 이름, 프로필, 로그아웃

중앙 메인 영역:

상단: 검색 Bar + 모드 / 필터

하단: 결과 탭

3.1.1 상단 검색 영역

구성 요소:

검색 입력창

플레이스홀더 예:

“예: 2023년에 서울 근무 데이터 엔지니어 입사자 수 알려줘”

“예: 최근 3년간 퇴사율이 가장 높은 부서와 이유 설명해줘”

Enter 입력 시 검색 실행

검색 모드 토글

옵션:

자동(Auto) – 백엔드에서 Intent 분류 (RAG vs NL2SQL)

통계/데이터 (NL2SQL)

문서/정책 검색 (RAG)

Segmented Control 형태의 버튼 3개

필터 영역(옵션, 접을 수 있게)

기간 선택 (연도/월, DateRangePicker)

조직/부서 (Select)

근무지 (Select)

언어 (ko/en)

이 필터 값들은 NL2SQL 프롬프트에도 반영, RAG 시에도 metadata filter로 사용 가능

3.1.2 결과 영역 – 탭 구조

검색이 실행되면, 아래 영역에 탭을 사용:

요약 (Summary) – 공통

LLM이 생성한 최종 자연어 답변

통계 질의의 경우: 핵심 숫자, 포인트, 간단 해석

문서 질의의 경우: 정책 요약, 주요 조항 등

표/그래프 (Data View) – 주로 NL2SQL

Table + Chart 두 개를 같이 보여주는 레이아웃

Table:

Vue + 어떤 그리드(예: AG Grid, Element Plus Table)

정렬, 필터, 컬럼 숨기기

Chart:

ECharts로 라인/바/파이 등 자동 선택

“CSV 다운로드”, “엑셀 다운로드” 버튼

SQL 보기 (SQL View) – NL2SQL 전용

실제 실행된 SQL을 readonly code block으로 표시

DB 반응 시간, row 수, 실행 시간 표시

“SQL 복사” 버튼

근거 문서 (Sources) – RAG 전용

RAG에 사용된 문서 리스트

각 문서 카드:

Title

Doc type (policy / job posting / FAQ 등)

Metadata(연도, 부서 등)

하이라이트된 스니펫

클릭 시 오른쪽에 상세보기 / 사이드패널 열기 (drawer 형태)

4. Vue 컴포넌트 구조 제안
4.1 라우터 구조
// src/router/index.ts
const routes = [
  { path: '/search', component: () => import('@/pages/SearchPage.vue') },
  { path: '/history', component: () => import('@/pages/HistoryPage.vue') },
  { path: '/reports', component: () => import('@/pages/ReportsPage.vue') },
  {
    path: '/admin',
    children: [
      { path: 'schema', component: () => import('@/pages/admin/SchemaPage.vue') },
      { path: 'logs', component: () => import('@/pages/admin/LogsPage.vue') },
      { path: 'settings', component: () => import('@/pages/admin/SettingsPage.vue') },
    ]
  },
  { path: '/', redirect: '/search' }
];

4.2 기본 컴포넌트 트리 (SearchPage)
SearchPage.vue
 ├─ SearchHeader (검색창 + 모드 + 필터 toggle)
 │   ├─ SearchInput
 │   ├─ ModeSelector
 │   └─ FilterPanel (collapsible)
 └─ SearchResultPanel
     ├─ ResultTabs
     │   ├─ SummaryTab
     │   ├─ DataTab
     │   │    ├─ ResultTable
     │   │    └─ ResultChart
     │   ├─ SqlTab
     │   └─ SourcesTab
     └─ SidePanel (선택된 문서 상세보기 등)

4.3 Pinia 상태 설계

store/searchStore.ts (예시)

state:

query: string

mode: 'auto' | 'nl2sql' | 'rag'

filters: { fromDate, toDate, department, location, lang }

loading: boolean

result: { summary, dataRows, columns, sql, sources, meta }

actions:

search() – FastAPI /search 혹은 /nl2sql 호출

setMode(), setFilters(), setQuery()

이렇게 하면 SearchPage는 대부분 store에만 의존하고, UI 로직이 깔끔해집니다.

5. UI/UX 디테일 포인트 (HR 시스템 특화)

예시 질의(Placeholder/추천)

사용자에게 “어떻게 질문해야 하는지”를 보여주는 게 중요:

예:

“2023년 서울 근무 개발 직군 입사자 수를 월별로 보여줘”

“퇴사율이 가장 높은 부서를 최근 2년 기준으로 보여줘”

“재택근무 관련 인사 정책을 요약해줘”

검색창 아래에 “추천 질의”를 Chips처럼 노출 → 클릭 시 자동 입력

현실적인 응답 시간 UX

LLM 응답이 1~3초 이상 걸릴 수 있으므로:

검색 결과 영역에서 skeleton loading / spinner

“질문 이해 중…”, “DB 통계 조회 중…”, “정책 문서 요약 중…” 같이 단계별 안내 문구

에러 표시 방식

SQL 오류, 권한 오류, timeout 등:

상단에 alert 형태로 노출

관리자에게 넘길 수 있는 “에러 상세 보기” 버튼

“민감한 데이터라 답변할 수 없음” 같은 메시지도 UX적으로 부드럽게 처리

SQL 신뢰도 표시 (선택사항이지만 좋음)

NL2SQL 경우:

“AI가 생성한 SQL입니다. 결과를 검토해주세요.” 라는 배지

SQL 탭에 “신뢰도”, “검증 여부” 표시

향후 사람 검증을 거친 “공식 리포트 SQL”은 다른 표시로 구분

디자인 톤

HR 시스템이라 너무 게임/스타트업 느낌보다는:

심플한 블루/그레이 톤

카드 + 탭 구조 위주

Vue + Tailwind라면:

상단 h-screen flex flex-col, 내부 container mx-auto, rounded-xl shadow 정도

6. 간단한 Vue 코드 스케치 (느낌용)
<!-- src/pages/SearchPage.vue -->
<template>
  <div class="h-screen flex flex-col">
    <AppHeader />

    <main class="flex-1 container mx-auto px-4 py-4 flex flex-col gap-4">
      <SearchHeader
        :query="searchStore.query"
        :mode="searchStore.mode"
        :filters="searchStore.filters"
        :loading="searchStore.loading"
        @search="searchStore.search"
        @update:query="searchStore.query = $event"
        @update:mode="searchStore.mode = $event"
        @update:filters="searchStore.filters = $event"
      />

      <SearchResultPanel :result="searchStore.result" :loading="searchStore.loading" />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useSearchStore } from '@/stores/searchStore';
import AppHeader from '@/components/layout/AppHeader.vue';
import SearchHeader from '@/components/search/SearchHeader.vue';
import SearchResultPanel from '@/components/search/SearchResultPanel.vue';

const searchStore = useSearchStore();
</script>


이 정도 구조만 잡아두면, 뒤에 컴포넌트 세분화/디자인 시스템(예: Tailwind + 내부 컴포넌트 라이브러리) 붙이기가 편합니다.

7. 요약

Vue 3 SPA로 구성:

/search (핵심), /history, /reports, /admin/*

검색 화면은:

상단 검색 Bar + 모드 토글(Auto/NL2SQL/RAG) + 필터

하단 결과 탭 (요약 / 표·그래프 / SQL / 근거 문서)

NL2SQL 결과는 자연어 요약 + 표 + 그래프 + SQL 보기로 구성

RAG 결과는 요약 + 근거 문서 카드/사이드 패널 형식

Pinia로 검색 상태를 중앙 관리해서, 나중에 “한 질의를 다른 페이지에서 재사용”하는 것도 쉽게

원하시면 다음 단계로:

실제 컴포넌트 설계서(테이블) 형태로 각각의 컴포넌트 props / events 정리

Element Plus 또는 Tailwind 기준의 구체적인 UI 예시(코드)
까지도 바로 이어서 정리해줄게요.de
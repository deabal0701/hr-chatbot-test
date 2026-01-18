# MUREUM 기능명세서 (NL2SQL 중심)

> 본 문서는 MUREUM 프로젝트의 전체 기능명세서입니다. (NL2SQL 중심)
> 작성일: 2026-01-12 | 버전: v1.1

---

## 1. 기능 영역 개요

| # | Screen ID | 영역명 | 설명 |
|---|-----------|--------|------|
| 1 | NL2SQL-CORE | NL2SQL 핵심 기능 | 자연어→SQL 변환, 실행, 답변 생성 |
| 2 | NL2SQL-SEC | SQL 보안 | SQL Injection 방지, 접근 제어 |
| 3 | NL2SQL-SCHEMA | 스키마 관리 | DB 메타데이터 로드, 캐싱 |
| 4 | NL2SQL-PROMPT | 프롬프트 관리 | SQL/답변 생성 프롬프트, 이력 관리 |
| 5 | NL2SQL-LOG | 로깅/모니터링 | 쿼리 로그, SQL 실행 로그 |
| 6 | NL2SQL-EXT | 외부 DB 연동 | 비즈니스 DB 연결, 설정 |
| 7 | RAG-CORE | RAG 검색 | 문서 벡터 검색, 답변 생성 |
| 8 | DOC-MGMT | 문서 관리 | 문서 CRUD, 임베딩 |
| 9 | CHAT-UI | 채팅 인터페이스 | 사용자 채팅 UI, 모드 선택 |
| 10 | ADMIN-SET | 시스템 설정 | API 키, LLM, RAG, NL2SQL 설정 |
| 11 | ADMIN-CODE | 코드 관리 | 공통코드, 동적 옵션 관리 |
| 12 | ADMIN-DASH | 대시보드 | 통계, 시스템 상태 모니터링 |

---

## 2. 기능 명세 상세

### 2.1 NL2SQL-CORE (NL2SQL 핵심 기능)

| Screen ID | 1 depth | 2 depth | 기능명세 |
|-----------|---------|---------|----------|
| NL2SQL-CORE | 자연어 질의 처리 | 질의 입력 | - 사용자 자연어 질문을 텍스트로 입력 받음 |
| | | 질의 분석 | - 질의 의도(Intent) 분석 및 데이터 요청 유형 판별 |
| | | 컨텍스트 관리 | - 세션 기반 대화 맥락 유지 (멀티턴 지원) |
| | SQL 생성 | LLM 기반 SQL 변환 | - GPT-4o/Claude 활용 자연어→SQL 변환 |
| | | 스키마 컨텍스트 주입 | - DB 스키마 메타데이터를 프롬프트에 포함 |
| | | SQL 문법 검증 | - sqlparse 라이브러리로 SQL 구문 유효성 검사 |
| | SQL 실행 | 쿼리 실행 | - PostgreSQL 비즈니스 DB에 SQL 실행 |
| | | 결과 반환 | - 쿼리 결과를 JSON 형태로 반환 |
| | | 결과 요약 | - LLM이 쿼리 결과를 자연어로 요약 |

---

### 2.2 NL2SQL-SEC (SQL 보안)

| Screen ID | 1 depth | 2 depth | 기능명세 |
|-----------|---------|---------|----------|
| NL2SQL-SEC | SQL Injection 방지 | 키워드 블랙리스트 | - DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE, GRANT, REVOKE 차단 |
| | | SELECT 전용 검증 | - sqlparse로 SELECT 문만 허용, DML/DDL 차단 |
| | | 파라미터화 쿼리 | - psycopg3 자동 이스케이핑으로 인젝션 방지 |
| | 접근 제어 | 테이블 화이트리스트 | - allowed_tables 설정으로 접근 가능 테이블 제한 |
| | | 스키마 제한 | - 지정된 스키마(business)만 접근 허용 |
| | | 읽기 전용 모드 | - read_only_mode 설정으로 SELECT만 허용 |
| | 실행 제한 | 타임아웃 제어 | - statement_timeout 30초 설정 |
| | | 행 수 제한 | - LIMIT 미지정 시 자동으로 LIMIT 1000 추가 |
| | | 결과 크기 제한 | - max_rows 설정으로 최대 반환 행 수 제어 |
| | 민감정보 보호 | 데이터 마스킹 | - salary.base_salary 등 민감 컬럼 '***' 처리 |

---

### 2.3 NL2SQL-SCHEMA (스키마 관리)

| Screen ID | 1 depth | 2 depth | 기능명세 |
|-----------|---------|---------|----------|
| NL2SQL-SCHEMA | 메타데이터 로드 | 테이블 정보 조회 | - information_schema에서 테이블 목록 조회 |
| | | 컬럼 정보 조회 | - 컬럼명, 데이터타입, nullable, 기본값 수집 |
| | | 관계 정보 조회 | - Primary Key, Foreign Key, 인덱스 정보 수집 |
| | | 샘플 데이터 조회 | - 테이블별 상위 3행 샘플 데이터 수집 |
| | 캐싱 | 메모리 캐시 | - 스키마 정보를 메모리에 캐싱하여 성능 최적화 |
| | | 캐시 갱신 | - refresh=True 파라미터로 수동 갱신 지원 |
| | LLM 변환 | 마크다운 변환 | - 스키마 정보를 LLM 이해 가능한 마크다운 형식으로 변환 |
| | | 프롬프트 주입 | - SQL 생성 시 스키마 설명을 프롬프트에 포함 |

---

### 2.4 NL2SQL-PROMPT (프롬프트 관리)

| Screen ID | 1 depth | 2 depth | 기능명세 |
|-----------|---------|---------|----------|
| NL2SQL-PROMPT | SQL 생성 프롬프트 | 시스템 프롬프트 | - PostgreSQL 전문가 페르소나 설정 |
| | | 규칙 주입 | - SELECT 전용, 보안 규칙, 형식 지정 |
| | | Few-shot 예시 | - SQL 생성 예시를 프롬프트에 포함 |
| | 답변 생성 프롬프트 | 결과 요약 프롬프트 | - 데이터 분석 전문가 페르소나로 결과 요약 |
| | | 형식 지정 | - 불릿포인트, 핵심 수치 강조 등 형식 가이드 |
| | 프롬프트 설정 | DB 저장 | - tb_app_settings 테이블에 프롬프트 저장 |
| | | 실시간 변경 | - Admin UI에서 프롬프트 수정 시 즉시 반영 |
| | | 이력 관리 | - tb_prompt_history 테이블에 변경 이력 저장 |
| | | 원복 기능 | - 이전 버전 프롬프트로 복원 가능 |

---

### 2.5 NL2SQL-LOG (로깅 및 모니터링)

| Screen ID | 1 depth | 2 depth | 기능명세 |
|-----------|---------|---------|----------|
| NL2SQL-LOG | 쿼리 로깅 | 기본 로그 | - query_log 테이블에 사용자 질의, 유형, 응답시간 저장 |
| | | SQL 실행 로그 | - sql_execution_log에 생성 SQL, 실행 SQL, 행 수, 실행시간 저장 |
| | | 에러 로그 | - 실패 시 에러 메시지 및 원인 저장 |
| | 요청 추적 | Request ID | - 8자리 UUID로 요청별 고유 ID 부여 |
| | | 단계별 로깅 | - INIT → GENERATE → VALIDATE → EXECUTE → ANSWER → COMPLETE |
| | | 처리 시간 측정 | - 각 단계별 소요 시간 측정 및 기록 |
| | 성능 분석 | 응답 시간 통계 | - 평균/최대/최소 응답 시간 집계 |
| | | 성공률 분석 | - 질의 성공/실패 비율 통계 |

---

### 2.6 NL2SQL-EXT (외부 DB 연동)

| Screen ID | 1 depth | 2 depth | 기능명세 |
|-----------|---------|---------|----------|
| NL2SQL-EXT | DB 연결 관리 | 연결 풀 | - psycopg3 커넥션 풀 (기본 5개) |
| | | 연결 타임아웃 | - 연결 타임아웃 10초 설정 |
| | | 자동 재연결 | - 연결 끊김 시 자동 재연결 |
| | DB 유형 지원 | PostgreSQL | - PostgreSQL 데이터베이스 지원 (현재 구현) |
| | | 확장성 | - Oracle, MySQL 등 추후 확장 가능 구조 |
| | 설정 관리 | 동적 설정 | - DB 연결 정보를 tb_app_settings에서 관리 |
| | | 환경 분리 | - 개발/운영 환경별 별도 설정 지원 |
| | | 연결 테스트 | - 설정 변경 시 연결 유효성 테스트 |

---

### 2.7 RAG-CORE (RAG 검색)

| Screen ID | 1 depth | 2 depth | 기능명세 |
|-----------|---------|---------|----------|
| RAG-CORE | 벡터 검색 | 임베딩 생성 | - OpenAI text-embedding-3-small (1536차원) |
| | | 유사도 검색 | - pgvector 코사인 유사도 기반 검색 |
| | | Top-K 반환 | - 설정된 top_k 개수만큼 문서 반환 (기본 5개) |
| | | 유사도 임계값 | - similarity_threshold 이상만 반환 (기본 0.3) |
| | 검색 필터 | 문서 유형 필터 | - doc_type별 필터링 (policy, faq, guide 등) |
| | | 언어 필터 | - language별 필터링 (ko, en) |
| | | 메타데이터 필터 | - jsonb 메타데이터 기반 필터링 |
| | 답변 생성 | 컨텍스트 구성 | - 검색된 문서를 프롬프트 컨텍스트로 구성 |
| | | LLM 답변 생성 | - 문서 기반 자연어 답변 생성 |
| | | 출처 명시 | - 답변에 참조 문서 출처 표시 |

---

### 2.8 DOC-MGMT (문서 관리)

| Screen ID | 1 depth | 2 depth | 기능명세 |
|-----------|---------|---------|----------|
| DOC-MGMT | 문서 CRUD | 문서 등록 | - 제목, 유형, 내용, 메타데이터 입력 |
| | | 문서 조회 | - 목록 조회, 상세 조회, 필터링 |
| | | 문서 수정 | - 제목, 내용, 메타데이터 수정 |
| | | 문서 삭제 | - 단건/다건 삭제, 청크 문서 연쇄 삭제 |
| | 임베딩 관리 | 임베딩 미리보기 | - 청킹 결과 미리보기 (청크 수, 크기) |
| | | 임베딩 실행 | - 선택 문서 일괄 임베딩 실행 |
| | | 임베딩 상태 | - indexed 여부 표시 (완료/대기) |
| | 문서 필터링 | 유형별 필터 | - policy, faq, guide, job_posting 필터 |
| | | 상태별 필터 | - 임베딩 완료/대기 필터 |
| | | 다중 선택 | - 체크박스로 다중 문서 선택 |
| | 청킹 설정 | 청크 크기 | - 기본 1000자, 설정 가능 |
| | | 오버랩 크기 | - 기본 100자, 설정 가능 |

---

### 2.9 CHAT-UI (채팅 인터페이스)

| Screen ID | 1 depth | 2 depth | 기능명세 |
|-----------|---------|---------|----------|
| CHAT-UI | 메시지 입력 | 텍스트 입력 | - 자연어 질문 텍스트 입력창 |
| | | 예시 질문 | - 클릭 시 예시 질문 자동 입력 |
| | | Enter 전송 | - Enter 키로 메시지 전송 |
| | 검색 모드 선택 | Auto 모드 | - 시스템이 RAG/NL2SQL 자동 판별 |
| | | RAG 모드 | - 문서 검색 전용 모드 |
| | | NL2SQL 모드 | - 데이터베이스 조회 전용 모드 |
| | 메시지 표시 | 사용자 메시지 | - 오른쪽 정렬, 사용자 아이콘 |
| | | AI 응답 | - 왼쪽 정렬, AI 아이콘, 마크다운 렌더링 |
| | | 로딩 표시 | - 타이핑 애니메이션, 로딩 텍스트 |
| | | 에러 표시 | - 에러 발생 시 사용자 친화적 메시지 |
| | 응답 상세 | SQL 표시 | - NL2SQL 응답 시 생성된 SQL 코드 블록 |
| | | 데이터 테이블 | - 쿼리 결과 테이블 형식 표시 |
| | | 참조 문서 | - RAG 응답 시 참조 문서 링크 |

---

### 2.10 ADMIN-SET (시스템 설정)

| Screen ID | 1 depth | 2 depth | 기능명세 |
|-----------|---------|---------|----------|
| ADMIN-SET | API 키 관리 | OpenAI API Key | - GPT 모델 및 임베딩용 API 키 설정 |
| | | Organization ID | - OpenAI Organization ID 설정 (선택) |
| | | Anthropic API Key | - Claude 모델용 API 키 설정 (선택) |
| | | 비밀번호 마스킹 | - API 키 표시/숨김 토글 |
| | LLM 설정 | Provider 선택 | - openai / anthropic 선택 |
| | | 모델 선택 | - gpt-4o, gpt-4o-mini, claude-3-5-sonnet 등 |
| | | Temperature | - 생성 온도 설정 (0.0-2.0) |
| | | Max Tokens | - 최대 토큰 수 설정 |
| | RAG 설정 | Top-K | - 검색 문서 수 설정 |
| | | 유사도 임계값 | - similarity_threshold 설정 (0.0-1.0) |
| | | 최대 컨텍스트 길이 | - max_context_length 설정 |
| | NL2SQL 설정 | 타임아웃 | - SQL 실행 타임아웃 (초) |
| | | 최대 행 수 | - max_rows 설정 |
| | | 읽기 전용 모드 | - read_only_mode 토글 |
| | 외부 DB 설정 | DB 유형 | - postgresql, oracle, mysql |
| | | 연결 정보 | - host, port, database, schema 설정 |
| | | 인증 정보 | - username, password 설정 |
| | | 허용 테이블 | - allowed_tables 설정 |
| | 임베딩 설정 | 모델 선택 | - text-embedding-3-small 등 |
| | | 벡터 차원 | - 1536 등 |
| | 청킹 설정 | 청크 크기 | - default_chunk_size 설정 |
| | | 오버랩 크기 | - default_overlap 설정 |
| | 프롬프트 설정 | RAG 프롬프트 | - RAG 시스템 프롬프트, 페르소나 |
| | | NL2SQL 프롬프트 | - SQL 생성, 답변 생성 프롬프트 |
| | | Agent 프롬프트 | - Agent 페르소나, Tool 설명 |

---

### 2.11 ADMIN-CODE (코드 관리)

| Screen ID | 1 depth | 2 depth | 기능명세 |
|-----------|---------|---------|----------|
| ADMIN-CODE | 코드 그룹 관리 | 그룹 조회 | - LLM_PROVIDER, LLM_MODEL, EMBEDDING_MODEL 등 |
| | | 그룹 선택 | - 드롭다운으로 코드 그룹 선택 |
| | 코드 CRUD | 코드 등록 | - code_value, code_name, description, metadata |
| | | 코드 조회 | - 그룹별 코드 목록 테이블 표시 |
| | | 코드 수정 | - 표시명, 설명, 메타데이터, 정렬순서 수정 |
| | | 코드 삭제 | - 시스템 코드 외 삭제 가능 |
| | 코드 속성 | 정렬 순서 | - sort_order로 표시 순서 지정 |
| | | 활성화 상태 | - is_active 토글 (비활성 코드는 선택 불가) |
| | | 시스템 코드 | - is_system=true 코드는 삭제/수정 제한 |
| | | 메타데이터 | - JSON 형식 추가 정보 저장 |

---

### 2.12 ADMIN-DASH (대시보드)

| Screen ID | 1 depth | 2 depth | 기능명세 |
|-----------|---------|---------|----------|
| ADMIN-DASH | 통계 카드 | 전체 문서 수 | - tb_docs 테이블 총 문서 수 표시 |
| | | 임베딩 완료 | - indexed=true 문서 수 표시 |
| | | 임베딩 대기 | - indexed=false 문서 수 표시 |
| | | 오늘 대화 | - 당일 query_log 수 표시 |
| | 빠른 시작 | HR 챗봇 | - 채팅 화면으로 바로가기 |
| | | 문서 등록 | - 문서 관리 화면으로 바로가기 |
| | | 임베딩 실행 | - 대기 문서 임베딩 화면으로 바로가기 |
| | 시스템 정보 | API 상태 | - 백엔드 API 헬스체크 상태 표시 |
| | | API 서버 | - 연결된 API 서버 URL 표시 |
| | | 검색 모드 | - 지원 검색 모드 표시 (Auto/RAG/NL2SQL) |

---

## 3. 비기능 요구사항

### 3.1 성능 (Performance)

| 구분 | 항목 | 목표치 | 비고 |
|------|------|--------|------|
| 응답시간 | SQL 생성 | < 2초 | LLM API 호출 포함 |
| | SQL 실행 | < 1초 | 단순 쿼리 기준 |
| | RAG 검색 | < 3초 | 벡터 검색 + LLM 응답 |
| | 전체 응답 | < 5초 | 생성 + 실행 + 요약 |
| 처리량 | 동시 요청 | 50 req/s | 커넥션 풀 기반 |
| | 일일 처리량 | 10,000건 | 예상 사용량 |
| 가용성 | 서비스 가용률 | 99.5% | 연간 기준 |

---

### 3.2 보안 (Security)

| 구분 | 항목 | 요구사항 | 구현 방법 |
|------|------|----------|-----------|
| 인증 | API 인증 | API Key 기반 인증 | 향후 OAuth 2.0 확장 예정 |
| 권한 | 테이블 접근 | 화이트리스트 기반 | allowed_tables 설정 |
| | 스키마 접근 | 지정 스키마만 허용 | schema 설정 |
| 데이터 보호 | 민감정보 | 마스킹 처리 | salary 등 민감 컬럼 |
| | API 키 | 암호화 저장 | is_secret=true 마스킹 |
| SQL 보안 | Injection 방지 | 다중 검증 레이어 | 블랙리스트 + 파라미터화 |
| | DDL/DML 차단 | SELECT 전용 | sqlparse 검증 |

---

### 3.3 확장성 (Scalability)

| 구분 | 항목 | 요구사항 | 구현 방법 |
|------|------|----------|-----------|
| 수평 확장 | 서버 확장 | Stateless 설계 | 세션 정보 분리 |
| | 로드 밸런싱 | 다중 인스턴스 지원 | Docker/K8s 배포 |
| DB 확장 | 연결 풀 | 동적 풀 크기 조정 | connection_pool_size 설정 |
| | 다중 DB | 여러 외부 DB 지원 | 향후 확장 예정 |
| LLM 확장 | 다중 Provider | OpenAI + Anthropic | init_chat_model 통합 |
| | 모델 전환 | 설정 기반 모델 변경 | DB 설정 실시간 반영 |

---

### 3.4 유지보수성 (Maintainability)

| 구분 | 항목 | 요구사항 | 구현 방법 |
|------|------|----------|-----------|
| 설정 관리 | 동적 설정 | 재시작 없이 변경 | tb_app_settings DB 저장 |
| | 환경 분리 | 개발/운영 설정 분리 | .env + DB 설정 |
| 모니터링 | 로그 추적 | Request ID 기반 추적 | 8자리 UUID |
| | 단계별 로그 | 처리 단계별 로깅 | INIT~COMPLETE |
| 프롬프트 관리 | 버전 관리 | 변경 이력 추적 | tb_prompt_history 테이블 |
| | 원복 기능 | 이전 버전 복원 | old_value 저장 |
| 문서화 | API 문서 | OpenAPI 스펙 | FastAPI 자동 생성 |

---

### 3.5 신뢰성 (Reliability)

| 구분 | 항목 | 요구사항 | 구현 방법 |
|------|------|----------|-----------|
| 에러 처리 | SQL 에러 | 친절한 에러 메시지 | 한글 에러 변환 |
| | 타임아웃 | 30초 타임아웃 | statement_timeout |
| | 재시도 | LLM 호출 재시도 | LangChain 내장 |
| 폴백 | LLM 폴백 | 대체 모델 사용 | OpenAI → Anthropic |
| | DB 폴백 | 연결 실패 시 재연결 | 자동 재연결 |
| 검증 | SQL 검증 | 실행 전 문법 검사 | sqlparse |
| | 결과 검증 | 빈 결과 처리 | 안내 메시지 |

---

## 4. Excel 붙여넣기용 탭 구분 형식

### 4.1 기능 영역 요약 (Excel 복사용)

```
#	Screen ID	영역명	설명
1	NL2SQL-CORE	NL2SQL 핵심 기능	자연어→SQL 변환, 실행, 답변 생성
2	NL2SQL-SEC	SQL 보안	SQL Injection 방지, 접근 제어
3	NL2SQL-SCHEMA	스키마 관리	DB 메타데이터 로드, 캐싱
4	NL2SQL-PROMPT	프롬프트 관리	SQL/답변 생성 프롬프트, 이력 관리
5	NL2SQL-LOG	로깅/모니터링	쿼리 로그, SQL 실행 로그
6	NL2SQL-EXT	외부 DB 연동	비즈니스 DB 연결, 설정
7	RAG-CORE	RAG 검색	문서 벡터 검색, 답변 생성
8	DOC-MGMT	문서 관리	문서 CRUD, 임베딩
9	CHAT-UI	채팅 인터페이스	사용자 채팅 UI, 모드 선택
10	ADMIN-SET	시스템 설정	API 키, LLM, RAG, NL2SQL 설정
11	ADMIN-CODE	코드 관리	공통코드, 동적 옵션 관리
12	ADMIN-DASH	대시보드	통계, 시스템 상태 모니터링
```

### 4.2 전체 기능 명세 (Excel 복사용)

```
Screen ID	1 depth	2 depth	기능명세
NL2SQL-CORE	자연어 질의 처리	질의 입력	사용자 자연어 질문을 텍스트로 입력 받음
NL2SQL-CORE	자연어 질의 처리	질의 분석	질의 의도(Intent) 분석 및 데이터 요청 유형 판별
NL2SQL-CORE	자연어 질의 처리	컨텍스트 관리	세션 기반 대화 맥락 유지 (멀티턴 지원)
NL2SQL-CORE	SQL 생성	LLM 기반 SQL 변환	GPT-4o/Claude 활용 자연어→SQL 변환
NL2SQL-CORE	SQL 생성	스키마 컨텍스트 주입	DB 스키마 메타데이터를 프롬프트에 포함
NL2SQL-CORE	SQL 생성	SQL 문법 검증	sqlparse 라이브러리로 SQL 구문 유효성 검사
NL2SQL-CORE	SQL 실행	쿼리 실행	PostgreSQL 비즈니스 DB에 SQL 실행
NL2SQL-CORE	SQL 실행	결과 반환	쿼리 결과를 JSON 형태로 반환
NL2SQL-CORE	SQL 실행	결과 요약	LLM이 쿼리 결과를 자연어로 요약
NL2SQL-SEC	SQL Injection 방지	키워드 블랙리스트	DROP, DELETE, UPDATE, INSERT, ALTER, CREATE, TRUNCATE, GRANT, REVOKE 차단
NL2SQL-SEC	SQL Injection 방지	SELECT 전용 검증	sqlparse로 SELECT 문만 허용, DML/DDL 차단
NL2SQL-SEC	SQL Injection 방지	파라미터화 쿼리	psycopg3 자동 이스케이핑으로 인젝션 방지
NL2SQL-SEC	접근 제어	테이블 화이트리스트	allowed_tables 설정으로 접근 가능 테이블 제한
NL2SQL-SEC	접근 제어	스키마 제한	지정된 스키마(business)만 접근 허용
NL2SQL-SEC	접근 제어	읽기 전용 모드	read_only_mode 설정으로 SELECT만 허용
NL2SQL-SEC	실행 제한	타임아웃 제어	statement_timeout 30초 설정
NL2SQL-SEC	실행 제한	행 수 제한	LIMIT 미지정 시 자동으로 LIMIT 1000 추가
NL2SQL-SEC	실행 제한	결과 크기 제한	max_rows 설정으로 최대 반환 행 수 제어
NL2SQL-SEC	민감정보 보호	데이터 마스킹	salary.base_salary 등 민감 컬럼 '***' 처리
NL2SQL-SCHEMA	메타데이터 로드	테이블 정보 조회	information_schema에서 테이블 목록 조회
NL2SQL-SCHEMA	메타데이터 로드	컬럼 정보 조회	컬럼명, 데이터타입, nullable, 기본값 수집
NL2SQL-SCHEMA	메타데이터 로드	관계 정보 조회	Primary Key, Foreign Key, 인덱스 정보 수집
NL2SQL-SCHEMA	메타데이터 로드	샘플 데이터 조회	테이블별 상위 3행 샘플 데이터 수집
NL2SQL-SCHEMA	캐싱	메모리 캐시	스키마 정보를 메모리에 캐싱하여 성능 최적화
NL2SQL-SCHEMA	캐싱	캐시 갱신	refresh=True 파라미터로 수동 갱신 지원
NL2SQL-SCHEMA	LLM 변환	마크다운 변환	스키마 정보를 LLM 이해 가능한 마크다운 형식으로 변환
NL2SQL-SCHEMA	LLM 변환	프롬프트 주입	SQL 생성 시 스키마 설명을 프롬프트에 포함
NL2SQL-PROMPT	SQL 생성 프롬프트	시스템 프롬프트	PostgreSQL 전문가 페르소나 설정
NL2SQL-PROMPT	SQL 생성 프롬프트	규칙 주입	SELECT 전용, 보안 규칙, 형식 지정
NL2SQL-PROMPT	SQL 생성 프롬프트	Few-shot 예시	SQL 생성 예시를 프롬프트에 포함
NL2SQL-PROMPT	답변 생성 프롬프트	결과 요약 프롬프트	데이터 분석 전문가 페르소나로 결과 요약
NL2SQL-PROMPT	답변 생성 프롬프트	형식 지정	불릿포인트, 핵심 수치 강조 등 형식 가이드
NL2SQL-PROMPT	프롬프트 설정	DB 저장	tb_app_settings 테이블에 프롬프트 저장
NL2SQL-PROMPT	프롬프트 설정	실시간 변경	Admin UI에서 프롬프트 수정 시 즉시 반영
NL2SQL-PROMPT	프롬프트 설정	이력 관리	tb_prompt_history 테이블에 변경 이력 저장
NL2SQL-PROMPT	프롬프트 설정	원복 기능	이전 버전 프롬프트로 복원 가능
NL2SQL-LOG	쿼리 로깅	기본 로그	query_log 테이블에 사용자 질의, 유형, 응답시간 저장
NL2SQL-LOG	쿼리 로깅	SQL 실행 로그	sql_execution_log에 생성 SQL, 실행 SQL, 행 수, 실행시간 저장
NL2SQL-LOG	쿼리 로깅	에러 로그	실패 시 에러 메시지 및 원인 저장
NL2SQL-LOG	요청 추적	Request ID	8자리 UUID로 요청별 고유 ID 부여
NL2SQL-LOG	요청 추적	단계별 로깅	INIT → GENERATE → VALIDATE → EXECUTE → ANSWER → COMPLETE
NL2SQL-LOG	요청 추적	처리 시간 측정	각 단계별 소요 시간 측정 및 기록
NL2SQL-LOG	성능 분석	응답 시간 통계	평균/최대/최소 응답 시간 집계
NL2SQL-LOG	성능 분석	성공률 분석	질의 성공/실패 비율 통계
NL2SQL-EXT	DB 연결 관리	연결 풀	psycopg3 커넥션 풀 (기본 5개)
NL2SQL-EXT	DB 연결 관리	연결 타임아웃	연결 타임아웃 10초 설정
NL2SQL-EXT	DB 연결 관리	자동 재연결	연결 끊김 시 자동 재연결
NL2SQL-EXT	DB 유형 지원	PostgreSQL	PostgreSQL 데이터베이스 지원 (현재 구현)
NL2SQL-EXT	DB 유형 지원	확장성	Oracle, MySQL 등 추후 확장 가능 구조
NL2SQL-EXT	설정 관리	동적 설정	DB 연결 정보를 tb_app_settings에서 관리
NL2SQL-EXT	설정 관리	환경 분리	개발/운영 환경별 별도 설정 지원
NL2SQL-EXT	설정 관리	연결 테스트	설정 변경 시 연결 유효성 테스트
RAG-CORE	벡터 검색	임베딩 생성	OpenAI text-embedding-3-small (1536차원)
RAG-CORE	벡터 검색	유사도 검색	pgvector 코사인 유사도 기반 검색
RAG-CORE	벡터 검색	Top-K 반환	설정된 top_k 개수만큼 문서 반환 (기본 5개)
RAG-CORE	벡터 검색	유사도 임계값	similarity_threshold 이상만 반환 (기본 0.3)
RAG-CORE	검색 필터	문서 유형 필터	doc_type별 필터링 (policy, faq, guide 등)
RAG-CORE	검색 필터	언어 필터	language별 필터링 (ko, en)
RAG-CORE	검색 필터	메타데이터 필터	jsonb 메타데이터 기반 필터링
RAG-CORE	답변 생성	컨텍스트 구성	검색된 문서를 프롬프트 컨텍스트로 구성
RAG-CORE	답변 생성	LLM 답변 생성	문서 기반 자연어 답변 생성
RAG-CORE	답변 생성	출처 명시	답변에 참조 문서 출처 표시
DOC-MGMT	문서 CRUD	문서 등록	제목, 유형, 내용, 메타데이터 입력
DOC-MGMT	문서 CRUD	문서 조회	목록 조회, 상세 조회, 필터링
DOC-MGMT	문서 CRUD	문서 수정	제목, 내용, 메타데이터 수정
DOC-MGMT	문서 CRUD	문서 삭제	단건/다건 삭제, 청크 문서 연쇄 삭제
DOC-MGMT	임베딩 관리	임베딩 미리보기	청킹 결과 미리보기 (청크 수, 크기)
DOC-MGMT	임베딩 관리	임베딩 실행	선택 문서 일괄 임베딩 실행
DOC-MGMT	임베딩 관리	임베딩 상태	indexed 여부 표시 (완료/대기)
DOC-MGMT	문서 필터링	유형별 필터	policy, faq, guide, job_posting 필터
DOC-MGMT	문서 필터링	상태별 필터	임베딩 완료/대기 필터
DOC-MGMT	문서 필터링	다중 선택	체크박스로 다중 문서 선택
DOC-MGMT	청킹 설정	청크 크기	기본 1000자, 설정 가능
DOC-MGMT	청킹 설정	오버랩 크기	기본 100자, 설정 가능
CHAT-UI	메시지 입력	텍스트 입력	자연어 질문 텍스트 입력창
CHAT-UI	메시지 입력	예시 질문	클릭 시 예시 질문 자동 입력
CHAT-UI	메시지 입력	Enter 전송	Enter 키로 메시지 전송
CHAT-UI	검색 모드 선택	Auto 모드	시스템이 RAG/NL2SQL 자동 판별
CHAT-UI	검색 모드 선택	RAG 모드	문서 검색 전용 모드
CHAT-UI	검색 모드 선택	NL2SQL 모드	데이터베이스 조회 전용 모드
CHAT-UI	메시지 표시	사용자 메시지	오른쪽 정렬, 사용자 아이콘
CHAT-UI	메시지 표시	AI 응답	왼쪽 정렬, AI 아이콘, 마크다운 렌더링
CHAT-UI	메시지 표시	로딩 표시	타이핑 애니메이션, 로딩 텍스트
CHAT-UI	메시지 표시	에러 표시	에러 발생 시 사용자 친화적 메시지
CHAT-UI	응답 상세	SQL 표시	NL2SQL 응답 시 생성된 SQL 코드 블록
CHAT-UI	응답 상세	데이터 테이블	쿼리 결과 테이블 형식 표시
CHAT-UI	응답 상세	참조 문서	RAG 응답 시 참조 문서 링크
ADMIN-SET	API 키 관리	OpenAI API Key	GPT 모델 및 임베딩용 API 키 설정
ADMIN-SET	API 키 관리	Organization ID	OpenAI Organization ID 설정 (선택)
ADMIN-SET	API 키 관리	Anthropic API Key	Claude 모델용 API 키 설정 (선택)
ADMIN-SET	API 키 관리	비밀번호 마스킹	API 키 표시/숨김 토글
ADMIN-SET	LLM 설정	Provider 선택	openai / anthropic 선택
ADMIN-SET	LLM 설정	모델 선택	gpt-4o, gpt-4o-mini, claude-3-5-sonnet 등
ADMIN-SET	LLM 설정	Temperature	생성 온도 설정 (0.0-2.0)
ADMIN-SET	LLM 설정	Max Tokens	최대 토큰 수 설정
ADMIN-SET	RAG 설정	Top-K	검색 문서 수 설정
ADMIN-SET	RAG 설정	유사도 임계값	similarity_threshold 설정 (0.0-1.0)
ADMIN-SET	RAG 설정	최대 컨텍스트 길이	max_context_length 설정
ADMIN-SET	NL2SQL 설정	타임아웃	SQL 실행 타임아웃 (초)
ADMIN-SET	NL2SQL 설정	최대 행 수	max_rows 설정
ADMIN-SET	NL2SQL 설정	읽기 전용 모드	read_only_mode 토글
ADMIN-SET	외부 DB 설정	DB 유형	postgresql, oracle, mysql
ADMIN-SET	외부 DB 설정	연결 정보	host, port, database, schema 설정
ADMIN-SET	외부 DB 설정	인증 정보	username, password 설정
ADMIN-SET	외부 DB 설정	허용 테이블	allowed_tables 설정
ADMIN-SET	임베딩 설정	모델 선택	text-embedding-3-small 등
ADMIN-SET	임베딩 설정	벡터 차원	1536 등
ADMIN-SET	청킹 설정	청크 크기	default_chunk_size 설정
ADMIN-SET	청킹 설정	오버랩 크기	default_overlap 설정
ADMIN-SET	프롬프트 설정	RAG 프롬프트	RAG 시스템 프롬프트, 페르소나
ADMIN-SET	프롬프트 설정	NL2SQL 프롬프트	SQL 생성, 답변 생성 프롬프트
ADMIN-SET	프롬프트 설정	Agent 프롬프트	Agent 페르소나, Tool 설명
ADMIN-CODE	코드 그룹 관리	그룹 조회	LLM_PROVIDER, LLM_MODEL, EMBEDDING_MODEL 등
ADMIN-CODE	코드 그룹 관리	그룹 선택	드롭다운으로 코드 그룹 선택
ADMIN-CODE	코드 CRUD	코드 등록	code_value, code_name, description, metadata
ADMIN-CODE	코드 CRUD	코드 조회	그룹별 코드 목록 테이블 표시
ADMIN-CODE	코드 CRUD	코드 수정	표시명, 설명, 메타데이터, 정렬순서 수정
ADMIN-CODE	코드 CRUD	코드 삭제	시스템 코드 외 삭제 가능
ADMIN-CODE	코드 속성	정렬 순서	sort_order로 표시 순서 지정
ADMIN-CODE	코드 속성	활성화 상태	is_active 토글 (비활성 코드는 선택 불가)
ADMIN-CODE	코드 속성	시스템 코드	is_system=true 코드는 삭제/수정 제한
ADMIN-CODE	코드 속성	메타데이터	JSON 형식 추가 정보 저장
ADMIN-DASH	통계 카드	전체 문서 수	tb_docs 테이블 총 문서 수 표시
ADMIN-DASH	통계 카드	임베딩 완료	indexed=true 문서 수 표시
ADMIN-DASH	통계 카드	임베딩 대기	indexed=false 문서 수 표시
ADMIN-DASH	통계 카드	오늘 대화	당일 query_log 수 표시
ADMIN-DASH	빠른 시작	HR 챗봇	채팅 화면으로 바로가기
ADMIN-DASH	빠른 시작	문서 등록	문서 관리 화면으로 바로가기
ADMIN-DASH	빠른 시작	임베딩 실행	대기 문서 임베딩 화면으로 바로가기
ADMIN-DASH	시스템 정보	API 상태	백엔드 API 헬스체크 상태 표시
ADMIN-DASH	시스템 정보	API 서버	연결된 API 서버 URL 표시
ADMIN-DASH	시스템 정보	검색 모드	지원 검색 모드 표시 (Auto/RAG/NL2SQL)
```

### 4.3 비기능 요구사항 (Excel 복사용)

```
구분	항목	요구사항/목표치	구현 방법/비고
성능	SQL 생성 응답시간	< 2초	LLM API 호출 포함
성능	SQL 실행 응답시간	< 1초	단순 쿼리 기준
성능	RAG 검색 응답시간	< 3초	벡터 검색 + LLM 응답
성능	전체 응답시간	< 5초	생성 + 실행 + 요약
성능	동시 요청 처리	50 req/s	커넥션 풀 기반
성능	일일 처리량	10,000건	예상 사용량
성능	서비스 가용률	99.5%	연간 기준
보안	API 인증	API Key 기반	향후 OAuth 2.0 확장 예정
보안	테이블 접근 권한	화이트리스트 기반	allowed_tables 설정
보안	스키마 접근 권한	지정 스키마만 허용	schema 설정
보안	민감정보 보호	마스킹 처리	salary 등 민감 컬럼
보안	API 키 보호	암호화 저장	is_secret=true 마스킹
보안	SQL Injection 방지	다중 검증 레이어	블랙리스트 + 파라미터화
보안	DDL/DML 차단	SELECT 전용	sqlparse 검증
확장성	서버 확장	Stateless 설계	Docker/K8s 배포
확장성	DB 연결 풀	동적 풀 크기 조정	connection_pool_size 설정
확장성	LLM Provider	OpenAI + Anthropic	init_chat_model 통합
확장성	모델 전환	설정 기반 모델 변경	DB 설정 실시간 반영
유지보수성	동적 설정	재시작 없이 변경	tb_app_settings DB 저장
유지보수성	로그 추적	Request ID 기반 추적	8자리 UUID
유지보수성	프롬프트 버전관리	변경 이력 추적	tb_prompt_history 테이블
유지보수성	API 문서	OpenAPI 스펙	FastAPI 자동 생성
신뢰성	SQL 에러 처리	친절한 에러 메시지	한글 에러 변환
신뢰성	타임아웃	30초 타임아웃	statement_timeout
신뢰성	LLM 폴백	대체 모델 사용	OpenAI → Anthropic
신뢰성	SQL 검증	실행 전 문법 검사	sqlparse
```

---

## 5. API 명세

### 5.1 NL2SQL API

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | /api/v1/nl2sql | NL2SQL 질의 실행 |
| POST | /api/v1/search | 통합 검색 (mode=nl2sql) |

### 5.2 RAG API

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | /api/v1/rag | RAG 검색 |
| POST | /api/v1/search | 통합 검색 (mode=rag) |

### 5.3 문서 관리 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/admin/v1/documents | 문서 목록 조회 |
| POST | /api/admin/v1/documents | 문서 등록 |
| GET | /api/admin/v1/documents/{id} | 문서 상세 조회 |
| PUT | /api/admin/v1/documents/{id} | 문서 수정 |
| DELETE | /api/admin/v1/documents/{id} | 문서 삭제 |
| POST | /api/admin/v1/documents/embedding/preview | 임베딩 미리보기 |
| POST | /api/admin/v1/documents/embedding/execute | 임베딩 실행 |

### 5.4 설정 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/admin/v1/settings | 전체 설정 조회 |
| PUT | /api/admin/v1/settings | 설정 저장 |
| GET | /api/admin/v1/settings/{category} | 카테고리별 설정 조회 |

### 5.5 코드 관리 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | /api/admin/v1/codes | 코드 목록 조회 |
| POST | /api/admin/v1/codes | 코드 등록 |
| PUT | /api/admin/v1/codes/{id} | 코드 수정 |
| DELETE | /api/admin/v1/codes/{id} | 코드 삭제 |

---

*작성일: 2026-01-12*
*버전: v1.1*

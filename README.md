# MUREUM - 기업용 AI 지식 베이스 어시스턴트

자연어 기반 기업 지식 검색 및 통계 조회를 위한 AI 어시스턴트 시스템

## 주요 기능

### 1. AI Agent (ReAct 패턴)
- **자율적 도구 선택**: 질문에 따라 자동으로 적절한 도구(SQL, 문서검색, 계산기) 선택
- **멀티스텝 질의**: 복잡한 질문을 단계별로 분해하여 처리
- **멀티턴 대화**: 세션 기반 대화 히스토리 관리 (InMemorySaver)
- **실행 과정 추적**: Thought → Action → Observation 패턴으로 추론 과정 확인

### 2. RAG (Retrieval Augmented Generation)
- **벡터 검색**: pgvector 기반 시맨틱 검색
- **문서 청킹**: 효율적인 검색을 위한 스마트 문서 분할
- **동적 필터링**: 문서 유형, 카테고리 기반 필터링

### 3. NL2SQL
- **자연어 → SQL 변환**: LLM 기반 SQL 자동 생성
- **SQL 보안 검증**: SQL Injection 방지, 읽기 전용 강제
- **다중 DB 지원**: 서비스 DB + 외부 비즈니스 DB 연결

### 4. 동적 설정 관리
- **DB 기반 설정**: 코드 배포 없이 실시간 설정 변경
- **Admin UI**: 웹 기반 설정 관리 인터페이스
- **Fallback 체계**: DB → 환경변수 → 기본값 순서로 설정 로드

### 5. 다중 LLM 제공자 지원
- **OpenAI**: GPT-4o, GPT-4o-mini 등
- **Anthropic**: Claude 3.5 Sonnet 등
- **통합 인터페이스**: `init_chat_model` 사용으로 제공자 독립적 코드

## 기술 스택

### Backend
- **Language**: Python 3.11+ (3.10 이상 필수)
- **Framework**: FastAPI 0.115+
- **Database**: PostgreSQL + pgvector
- **AI Framework**:
  - LangChain 1.2+ (Production-ready v1.0 series)
  - LangGraph 1.0+ (AI workflow orchestration)
  - LangChain-OpenAI 1.1.6+
  - LangChain-Anthropic 0.2.4+

### LLM Providers
- **OpenAI**: gpt-4o, gpt-4o-mini, gpt-4-turbo-preview
- **Anthropic**: claude-3-5-sonnet-20241022
- **Embeddings**: text-embedding-3-small (1536 dimensions)

### Frontend
- **Framework**: Vue 3 + Composition API
- **State Management**: Vuex
- **UI Components**: Element Plus

### Infrastructure
- **ASGI Server**: Uvicorn (development) / Gunicorn (production)
- **Database**: PostgreSQL 15+ with pgvector extension
- **Monitoring**: Prometheus (optional)

## 설치

### 1. 필수 요구사항
```bash
# Python 3.11 이상 (3.10 최소)
python --version  # Python 3.11.x 확인

# PostgreSQL 15+ with pgvector extension
psql --version
```

### 2. 가상환경 생성 (Conda 권장)
```bash
# Conda 환경 생성
conda create -n my-env3.11_chat2 python=3.11
conda activate my-env3.11_chat2

# 또는 venv 사용
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. 의존성 설치
```bash
pip install -r requirements.txt
```

### 4. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력
```

**필수 환경 변수**:
```ini
# Database (PostgreSQL with pgvector)
DATABASE_URL=postgresql://user:password@host:port/dbname

# OpenAI API
OPENAI_API_KEY=sk-proj-...

# Anthropic API (선택)
ANTHROPIC_API_KEY=sk-ant-...

# Application
APP_ENV=development
LOG_LEVEL=INFO
```

### 5. 데이터베이스 초기화
```bash
# pgvector 확장 설치 (DB에서 수동 실행)
# CREATE EXTENSION IF NOT EXISTS vector;

# 테이블 생성
python scripts/init_db.py
```

### 6. 문서 임베딩 (선택)
```bash
# 샘플 문서 임베딩
python scripts/embed_documents.py --sample

# 특정 파일 임베딩
python scripts/embed_documents.py --file data/documents.json
```

## 실행

### Backend 서버
```bash
# 개발 서버 (자동 재시작)
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 또는
python app/main.py

# 프로덕션 서버
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Frontend 서버
```bash
cd frontend
npm install
npm run dev      # 개발 서버 (http://localhost:5173)
npm run build    # 프로덕션 빌드
npm run preview  # 빌드 미리보기
```

## API 문서

서버 실행 후 다음 URL에서 API 문서 확인:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 주요 엔드포인트

#### 1. AI Agent 검색 (멀티스텝, 멀티턴)
```bash
POST /api/v1/agent/search
```
**예시**:
```json
{
  "question": "2024년 입사자 중 재택근무 정책을 준수하는 사람은 몇 명이고 평균 급여는?",
  "session_id": "user123-session456",
  "config": {
    "max_iterations": 10,
    "enable_memory": true,
    "llm_model": "gpt-4o",
    "llm_temperature": 0.0
  }
}
```

#### 2. RAG 문서 검색
```bash
POST /api/v1/rag
```
**예시**:
```json
{
  "query": "재택근무 정책이 뭐야?",
  "mode": "rag"
}
```

#### 3. NL2SQL 데이터베이스 조회
```bash
POST /api/v1/nl2sql
```
**예시**:
```json
{
  "query": "2024년 입사자 수는?",
  "mode": "nl2sql"
}
```

#### 4. 자동 모드 (의도 분류)
```bash
POST /api/v1/search
```
**예시**:
```json
{
  "query": "2024년 입사자는 몇 명이고 재택근무 정책은 뭐야?",
  "mode": "auto"
}
```

## 프로젝트 구조

```
.
├── app/
│   ├── main.py                 # FastAPI 엔트리포인트
│   ├── config.py               # 설정 (Pydantic Settings)
│   ├── api/
│   │   └── routes/
│   │       ├── agent.py        # AI Agent 엔드포인트
│   │       ├── search.py       # RAG/NL2SQL/Auto 검색
│   │       ├── documents.py    # 문서 관리
│   │       ├── settings.py     # 설정 관리
│   │       └── codes.py        # 코드 관리
│   ├── graphs/                 # LangGraph 워크플로우
│   │   ├── agent_graph.py      # AI Agent (ReAct 패턴)
│   │   ├── rag_graph.py        # RAG 워크플로우
│   │   └── nl2sql_graph.py     # NL2SQL 워크플로우
│   ├── tools/                  # AI Agent 도구
│   │   ├── base.py             # 도구 베이스 클래스
│   │   ├── sql_tool.py         # SQL 쿼리 도구
│   │   ├── rag_tool.py         # 문서 검색 도구
│   │   └── calc_tool.py        # 계산기 도구
│   ├── services/               # 비즈니스 로직
│   │   ├── vector_store.py     # 벡터 검색
│   │   ├── sql_executor.py     # SQL 실행 및 검증
│   │   ├── schema_loader.py    # DB 스키마 로딩
│   │   └── settings_service.py # 동적 설정 관리
│   ├── models/                 # 데이터 모델
│   │   ├── schemas.py          # 공통 스키마
│   │   ├── agent_schemas.py    # Agent 전용 스키마
│   │   └── hr_schema_def.py    # HR 스키마 정의
│   └── utils/                  # 유틸리티
│       ├── database.py         # DB 연결 풀
│       ├── external_database.py # 외부 DB 연결
│       ├── llm_config.py       # 통합 LLM 설정
│       ├── logger.py           # 로깅
│       ├── text_chunker.py     # 문서 청킹
│       └── common.py           # 공통 유틸
├── scripts/                    # 스크립트
│   ├── init_db.py              # DB 초기화
│   ├── embed_documents.py      # 문서 임베딩
│   └── hermes_db.sql           # DB 스키마 DDL
├── frontend/                   # Vue 3 프론트엔드
│   ├── src/
│   │   ├── views/              # 페이지 컴포넌트
│   │   ├── components/         # 재사용 컴포넌트
│   │   ├── store/              # Vuex 스토어
│   │   └── api/                # API 클라이언트
│   └── package.json
├── tests/                      # 테스트
├── requirements.txt            # Python 의존성
└── README.md
```

## 주요 특징

### 1. AI Agent (ReAct 패턴)
- **자율적 도구 선택**: LLM이 질문을 분석하여 필요한 도구를 자동 선택
- **반복적 추론**: Thought → Action → Observation 사이클 반복
- **멀티스텝 처리**: 복잡한 질문을 여러 단계로 분해하여 처리
- **실행 과정 추적**: 각 단계별 추론 과정 및 도구 호출 결과 확인

### 2. 동적 설정 시스템
- **DB 기반 설정**: `tb_app_settings` 테이블에서 설정 로드
- **실시간 변경**: Admin UI에서 설정 변경 즉시 반영
- **Fallback 체계**: DB → .env → 코드 기본값 순서로 로드
- **설정 항목**: LLM 모델, 제공자, 온도, RAG 파라미터, NL2SQL 설정 등

### 3. 다중 LLM 제공자 지원
- **init_chat_model**: LangChain의 통합 LLM 인터페이스 사용
- **제공자 독립적**: 코드 변경 없이 제공자 전환 가능
- **Fallback**: 메인 제공자 실패 시 OpenAI로 자동 전환

### 4. 보안
- **SQL Injection 방지**: 키워드 블랙리스트, 테이블 화이트리스트, SELECT-only 강제
- **파라미터화된 쿼리**: psycopg3 자동 이스케이핑
- **타임아웃**: SQL 실행 시간 제한 (30초)
- **Row 제한**: 최대 1000개 결과 제한

### 5. 성능 최적화
- **연결 풀링**: psycopg3 connection pool
- **스키마 캐싱**: DB 스키마 메모리 캐싱
- **벡터 인덱스**: pgvector HNSW/IVFFlat 인덱스
- **비동기 처리**: FastAPI async/await 패턴

## 테스트

### 헬스 체크
```bash
curl http://localhost:8000/health
```

### RAG 검색 테스트
```bash
curl -X POST "http://localhost:8000/api/v1/rag" \
  -H "Content-Type: application/json" \
  -d '{"query": "재택근무 정책이 뭐야?", "mode": "rag"}'
```

### NL2SQL 검색 테스트
```bash
curl -X POST "http://localhost:8000/api/v1/nl2sql" \
  -H "Content-Type: application/json" \
  -d '{"query": "2024년 입사자 수는?", "mode": "nl2sql"}'
```

### AI Agent 검색 테스트
```bash
curl -X POST "http://localhost:8000/api/v1/agent/search" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "2024년 입사자는 몇 명이고 재택근무 정책은 뭐야?",
    "config": {
      "max_iterations": 10,
      "enable_memory": true
    }
  }'
```

### 단위 테스트 실행
```bash
# 가상환경 활성화
conda activate my-env3.11_chat2

# 테스트 실행
pytest tests/
```

## 환경 변수 상세

| 변수명 | 설명 | 기본값 | 필수 |
|--------|------|--------|------|
| `DATABASE_URL` | PostgreSQL 연결 URL | - | ✅ |
| `OPENAI_API_KEY` | OpenAI API 키 | - | ✅ |
| `ANTHROPIC_API_KEY` | Anthropic API 키 | - | ❌ |
| `APP_ENV` | 환경 (development/production) | development | ❌ |
| `APP_HOST` | 서버 호스트 | 0.0.0.0 | ❌ |
| `APP_PORT` | 서버 포트 | 8000 | ❌ |
| `LOG_LEVEL` | 로그 레벨 | INFO | ❌ |
| `LLM_MODEL` | 기본 LLM 모델 | gpt-4o | ❌ |
| `LLM_PROVIDER` | LLM 제공자 | openai | ❌ |
| `EMBEDDING_MODEL` | 임베딩 모델 | text-embedding-3-small | ❌ |

## 트러블슈팅

### 1. Python 버전 오류
**증상**: `langchain-core requires Python 3.10+`
**해결**: Python 3.11 이상 사용 (`python --version` 확인)

### 2. pgvector 확장 없음
**증상**: `extension "vector" does not exist`
**해결**: PostgreSQL에서 수동 설치
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

### 3. OpenAI API 키 오류
**증상**: `Error code: 401 - Incorrect API key`
**해결**: `.env` 파일의 `OPENAI_API_KEY` 확인

### 4. 임베딩 검색 결과 없음
**증상**: RAG 검색 시 "관련 문서를 찾을 수 없습니다"
**해결**:
```bash
# 문서 임베딩 상태 확인
psql $DATABASE_URL -c "SELECT id, title, indexed FROM tb_docs;"

# 임베딩 실행
python scripts/embed_documents.py --sample
```

### 5. LLM 모델 404 오류
**증상**: `Error code: 404 - The model 'xxx' does not exist`
**해결**: Admin UI에서 유효한 모델명으로 변경 (gpt-4o, claude-3-5-sonnet-20241022 등)

## 추가 문서

- [CLAUDE.md](CLAUDE.md) - Claude Code 작업 가이드 (코드베이스 상세 설명)
- [ARCHITECTURE.md](ARCHITECTURE.md) - 시스템 아키텍처 및 데이터 플로우
- [PYTHON_CODE_GUIDE.md](PYTHON_CODE_GUIDE.md) - 파일별 상세 코드 가이드
- [SETUP.md](SETUP.md) - 설치 및 배포 가이드

## 라이선스

MIT License

## 기여

이슈 및 풀 리퀘스트 환영합니다.

## 연락처

프로젝트 관련 문의: [이메일 주소]

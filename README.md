# HR Chatbot with Claude AI

HR 시스템을 위한 AI 기반 자연어 검색 챗봇 시스템

## 주요 기능

- **RAG (Retrieval Augmented Generation)**: 자연어 문서 검색
- **NL2SQL**: 자연어를 SQL로 변환하여 통계 조회
- **pgvector**: 벡터 검색을 위한 PostgreSQL 확장
- **LangGraph**: AI 워크플로우 관리

## 기술 스택

- Python 3.11+ (3.11.14)
- FastAPI
- PostgreSQL + pgvector
- OpenAI API
- LangGraph
- Pydantic

## 설치

1. 가상환경 생성 및 활성화
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

2. 의존성 설치
```bash
pip install -r requirements.txt
```

3. 환경 변수 설정
```bash
cp .env.example .env
# .env 파일을 편집하여 실제 값 입력
```

4. 데이터베이스 초기화
 -  vector extension : CREATE EXTENSION IF NOT EXISTS vector; 사전설치 필요
```bash
python scripts/init_db.py
```

## 실행

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## API 문서

서버 실행 후 다음 URL에서 확인:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 프로젝트 구조

```
app/
  ├── main.py              # FastAPI 엔트리포인트
  ├── config.py            # 설정
  ├── graphs/              # LangGraph 워크플로우
  │   ├── rag_graph.py
  │   └── nl2sql_graph.py
  ├── services/            # 비즈니스 로직
  │   ├── vector_store.py
  │   ├── sql_executor.py
  │   └── schema_loader.py
  ├── models/              # 데이터 모델
  │   ├── schemas.py
  │   └── hr_schema_def.py
  ├── api/                 # API 엔드포인트
  │   └── routes/
  └── utils/               # 유틸리티
scripts/                   # 스크립트
  ├── init_db.py
  └── embed_documents.py
```

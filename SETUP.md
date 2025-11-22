# HR Chatbot 설치 및 실행 가이드

## 목차
1. [사전 요구사항](#사전-요구사항)
2. [설치](#설치)
3. [데이터베이스 설정](#데이터베이스-설정)
4. [환경 변수 설정](#환경-변수-설정)
5. [실행](#실행)
6. [API 테스트](#api-테스트)

## 사전 요구사항

- Python 3.11 이상
- PostgreSQL 14 이상
- OpenAI API 키

## 설치

### 1. 저장소 클론 및 가상환경 생성

```bash
cd 12.hr-chatbot-claude
python -m venv venv
```

### 2. 가상환경 활성화

Windows:
```bash
venv\Scripts\activate
```

macOS/Linux:
```bash
source venv/bin/activate
```

### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

## 데이터베이스 설정

### 1. PostgreSQL 설치

PostgreSQL을 설치하고 실행합니다.

### 2. pgvector 확장 설치

```bash
# Ubuntu/Debian
sudo apt-get install postgresql-14-pgvector

# macOS (Homebrew)
brew install pgvector

# Windows
# https://github.com/pgvector/pgvector 참고
```

### 3. 데이터베이스 생성

```bash
# PostgreSQL 접속
psql -U postgres

# 데이터베이스 생성
CREATE DATABASE hr_chatbot;

# 사용자 생성 (선택사항)
CREATE USER hr_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE hr_chatbot TO hr_user;
```

### 4. 데이터베이스 초기화

```bash
python scripts/init_db.py
```

이 스크립트는:
- pgvector 확장 활성화
- 모든 테이블 생성 (hr_docs, employee, department 등)
- 샘플 데이터 삽입

## 환경 변수 설정

### 1. .env 파일 생성

```bash
cp .env.example .env
```

### 2. .env 파일 편집

```env
# Database
DATABASE_URL=postgresql://postgres:your_password@localhost:5432/hr_chatbot

# OpenAI
OPENAI_API_KEY=sk-your-openai-api-key-here

# Application
APP_ENV=development
LOG_LEVEL=INFO

# Security
SECRET_KEY=your-secret-key-change-this-in-production
```

**주의**: 프로덕션 환경에서는 반드시 강력한 SECRET_KEY를 사용하세요.

## 실행

### 1. 문서 임베딩 (최초 1회)

샘플 문서를 임베딩합니다:

```bash
python scripts/embed_documents.py --sample
```

출력 예시:
```
문서 임베딩 시작...
[1/4] 임베딩 완료: 2024년 재택근무 정책 (ID: 5)
[2/4] 임베딩 완료: 연차 휴가 사용 가이드 (ID: 6)
...
```

### 2. API 서버 실행

```bash
# 방법 1: uvicorn 직접 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# 방법 2: Python 스크립트로 실행
python app/main.py
```

서버가 시작되면:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

### 3. API 문서 확인

브라우저에서 다음 URL을 열어 API 문서를 확인:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## API 테스트

### 1. 헬스 체크

```bash
curl http://localhost:8000/health
```

응답:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

### 2. RAG 검색 테스트

```bash
curl -X POST "http://localhost:8000/api/v1/rag" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "재택근무 정책이 뭐야?",
    "mode": "rag",
    "top_k": 5
  }'
```

### 3. NL2SQL 검색 테스트

```bash
curl -X POST "http://localhost:8000/api/v1/nl2sql" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "2024년에 입사한 직원 수를 부서별로 알려줘",
    "mode": "nl2sql"
  }'
```

### 4. 통합 검색 테스트 (자동 의도 분류)

```bash
curl -X POST "http://localhost:8000/api/v1/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "개발 직군 직원이 몇 명이야?",
    "mode": "auto"
  }'
```

## 문서 추가

### JSON 파일로 문서 추가

1. `data/documents.json` 파일 생성:

```json
[
  {
    "title": "문서 제목",
    "doc_type": "policy",
    "language": "ko",
    "content": "문서 내용...",
    "metadata": {
      "year": 2024,
      "department": "HR"
    }
  }
]
```

2. 임베딩 실행:

```bash
python scripts/embed_documents.py --file data/documents.json
```

### API로 문서 추가

```bash
curl -X POST "http://localhost:8000/api/v1/documents/" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "신규 정책",
    "doc_type": "policy",
    "language": "ko",
    "content": "정책 내용...",
    "metadata": {"year": 2024}
  }'
```

## 문제 해결

### 데이터베이스 연결 오류

```
ERROR: 데이터베이스 연결 실패
```

해결:
1. PostgreSQL이 실행 중인지 확인
2. DATABASE_URL이 올바른지 확인
3. 방화벽 설정 확인

### pgvector 확장 오류

```
ERROR: extension "vector" is not available
```

해결:
1. pgvector 확장 설치 확인
2. PostgreSQL 재시작

### OpenAI API 오류

```
ERROR: 임베딩 생성 실패
```

해결:
1. OPENAI_API_KEY가 올바른지 확인
2. API 키 잔액 확인
3. 네트워크 연결 확인

## 다음 단계

1. [design.md](design.md)에서 전체 아키텍처 확인
2. 프론트엔드 개발 (Vue 3)
3. 권한/인증 시스템 추가
4. 모니터링 및 로깅 강화
5. 프로덕션 배포

## 프로덕션 배포 체크리스트

- [ ] 환경 변수를 프로덕션 값으로 변경
- [ ] SECRET_KEY 변경
- [ ] CORS 설정 업데이트
- [ ] HTTPS 설정
- [ ] 데이터베이스 백업 설정
- [ ] 로그 수집 시스템 구성
- [ ] 모니터링 설정 (Prometheus, Grafana 등)
- [ ] Rate Limiting 설정
- [ ] 보안 검토

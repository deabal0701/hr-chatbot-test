# 배포/인프라 설계

> 최종 수정: 2026-02-15

---

## 1. 배포 아키텍처

```
┌─────────────────────────────────────────────────┐
│              배포 서버 (115.68.223.220)           │
│                                                   │
│  ┌─────────────────┐    ┌─────────────────────┐  │
│  │ mureum-frontend  │    │ mureum-backend       │  │
│  │ (Nginx, :19080)  │───►│ (Uvicorn, :19090)    │  │
│  │                  │    │                       │  │
│  │ 정적파일 서빙    │    │ FastAPI + LangGraph   │  │
│  │ /api/* 프록시    │    │                       │  │
│  └─────────────────┘    └──────────┬────────────┘  │
│                                     │               │
│           mureum-network (Docker)    │               │
└─────────────────────────────────────┼───────────────┘
                                      │
                          ┌───────────┴───────────┐
                          │  PostgreSQL (pgvector) │
                          │  115.68.223.220:5432   │
                          └───────────────────────┘
```

---

## 2. Docker 구성

### 2.1 Backend Dockerfile

```dockerfile
FROM python:3.13-slim
WORKDIR /app
# 시스템 의존성: curl, tzdata, gcc, libpq-dev
# 타임존: Asia/Seoul
COPY requirements.txt → pip install
COPY app/ scripts/ .env.docker
RUN mkdir -p logs
EXPOSE 19090
HEALTHCHECK --interval=30s curl /health
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "19090"]
```

### 2.2 Frontend Dockerfile (멀티스테이지)

```dockerfile
# 1단계: 빌드
FROM node:20.18-alpine AS builder
COPY package*.json → npm ci
ARG ENV_FILE=.env.docker
RUN cp ${ENV_FILE} .env.production && npm run build

# 2단계: 서빙
FROM nginx:alpine
COPY nginx.conf → /etc/nginx/conf.d/default.conf
COPY --from=builder /app/dist → /usr/share/nginx/html
EXPOSE 19080
```

### 2.3 Nginx 설정 핵심

```nginx
server {
    listen 19080;

    # SPA 라우팅
    location / {
        root /usr/share/nginx/html;
        try_files $uri $uri/ /index.html;
    }

    # API 프록시 → 백엔드
    location /api/ {
        proxy_pass http://mureum-backend:19090/api/;
        proxy_connect_timeout 60s;
        proxy_read_timeout 120s;    # Agent/NL2SQL 긴 처리
    }

    # 정적 파일 캐싱 (1년)
    location ~* \.(css|js|svg|woff|ttf)$ {
        expires 1y;
    }
}
```

---

## 3. 배포 스크립트

### 3.1 Backend (`deploy-docker.sh`)

```
로컬 빌드 → SSH로 이미지/파일 전송 → 원격 Docker 실행
```

| 설정 | 값 |
|------|---|
| REMOTE_HOST | 115.68.223.220 |
| REMOTE_DIR | /home/deabal/mureum/backend |
| CONTAINER | mureum-backend |
| PORT | 19090 |
| NETWORK | mureum-network |
| LOGS | /data/files/mureum/logs |

### 3.2 Frontend (`frontend/deploy-docker.sh`)

| 설정 | 값 |
|------|---|
| REMOTE_DIR | /home/deabal/mureum/frontend |
| CONTAINER | mureum-frontend |
| PORT | 19080 |

---

## 4. 환경변수

### 4.1 Backend (.env)

| 카테고리 | 변수 | 기본값 | 설명 |
|----------|------|--------|------|
| **DB** | DATABASE_URL | - | PostgreSQL 연결 문자열 |
| | DB_POOL_SIZE | 20 | 커넥션 풀 크기 |
| | DB_MAX_OVERFLOW | 10 | 최대 초과 커넥션 |
| **LLM** | OPENAI_API_KEY | - | OpenAI API 키 |
| | ANTHROPIC_API_KEY | - | Anthropic API 키 (선택) |
| | LLM_PROVIDER | openai | openai / anthropic |
| | LLM_MODEL | gpt-4.1-mini | 기본 LLM 모델 |
| | EMBEDDING_MODEL | text-embedding-3-small | 임베딩 모델 |
| **앱** | APP_ENV | development | 환경 (dev/staging/prod) |
| | APP_PORT | 19090 | 서버 포트 |
| | CORS_ORIGINS | * | CORS 허용 도메인 |
| **보안** | SECRET_KEY | - | JWT 서명 키 |
| | ACCESS_TOKEN_EXPIRE_MINUTES | 30 | 액세스 토큰 만료 |
| | JWT_REFRESH_TOKEN_EXPIRE_DAYS | 7 | 리프레시 토큰 만료 |
| | PASSWORD_MIN_LENGTH | 8 | 최소 비밀번호 길이 |
| | LOGIN_MAX_FAIL_COUNT | 5 | 로그인 실패 한도 |
| | LOGIN_LOCK_MINUTES | 30 | 계정 잠금 시간 |
| **RAG** | RAG_TOP_K | 10 | 검색 결과 수 |
| | RAG_SIMILARITY_THRESHOLD | 0.4 | 유사도 임계값 |
| **NL2SQL** | SQL_TIMEOUT_SECONDS | 30 | SQL 실행 타임아웃 |
| | SQL_MAX_ROWS | 1000 | 최대 반환 행 |
| **로그** | LOG_LEVEL | DEBUG | 로그 레벨 |
| | LOG_FORMAT | text | text / json |
| | LOG_FILE | ./logs/app.log | 로그 파일 경로 |

> **설정 우선순위**: Admin UI (DB tb_app_settings) > .env 환경변수 > config.py 기본값

### 4.2 Frontend (.env)

| 변수 | 개발 | Docker | 운영 |
|------|------|--------|------|
| VITE_API_URL | `http://localhost:19090` | (빈값) | `https://api.company.com` |
| VITE_APP_TITLE | Chatbot - MUREUM | Chatbot - MUREUM | Chatbot - MUREUM |

---

## 5. 헬스체크

### Backend

```bash
GET /health → {"status": "healthy", "database": "connected"}
```

- Docker HEALTHCHECK: 30초 간격, 10초 타임아웃, 30초 시작 대기, 3회 재시도

### Frontend

```bash
GET /health → Nginx 200 OK
```

---

## 6. 로깅

### 6.1 구조화 로깅

```python
log_step(logger, request_id, "MODULE", "STEP", "ACTION", "Message", key=value)
```

- request_id: 8자 UUID (LoggingMiddleware에서 생성)
- 포맷: text (개발) / json (운영)
- 파일: `./logs/app.log` (30일 보관, 일별 로테이션)

### 6.2 API 이력

- HistoryMiddleware → 비동기 워커 큐 → `tb_api_history` DB 저장
- JSONB trace_data에 실행 추적 정보 저장 (도구, SQL, 소스 등)

---

## 7. 운영 명령어

```bash
# 백엔드 개발 서버
conda activate penv3.13-nlq
uvicorn app.main:app --reload --host 0.0.0.0 --port 19090

# 프론트엔드 개발 서버
cd frontend && npm run dev

# Docker 빌드 & 실행
docker build -t mureum-backend .
docker run -p 19090:19090 --network mureum-network mureum-backend

cd frontend
docker build -t mureum-frontend .
docker run -p 19080:19080 --network mureum-network mureum-frontend

# 원격 배포
bash deploy-docker.sh
bash frontend/deploy-docker.sh
```

---

## 8. 스크립트 목록

| 파일 | 용도 |
|------|------|
| `scripts/add_multiturn_settings.py` | NL2SQL 멀티턴 설정 초기화 |
| `scripts/check_oracle_schema.py` | Oracle 외부 DB 스키마 검증 |
| `scripts/check_tools_config.py` | Agent 도구 설정 확인 |
| `scripts/check_admin.py` | 관리자 계정 상태 확인 |
| `scripts/reset_admin_password.py` | 관리자 비밀번호 초기화 |
| `deploy-docker.sh` | 백엔드 원격 Docker 배포 |
| `frontend/deploy-docker.sh` | 프론트엔드 원격 Docker 배포 |
| `deploy-gen-ssh-key.sh` | SSH 키 쌍 생성 |

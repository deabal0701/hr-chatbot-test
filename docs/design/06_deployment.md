# 배포/인프라 설계

> 최종 수정: 2026-03-09

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
RUN mkdir -p logs keys
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

## 3. 애플리케이션 시작 (Lifespan)

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. 서비스 DB 초기화 (PostgreSQL 커넥션 풀)
    db_manager.initialize()

    # 2. 외부 비즈니스 DB: lazy 초기화 (최초 요청 시 테넌트별 연결)
    external_db_manager.initialize()

    # 3. SSO 공개키 로드 (SSO 활성화 시)
    from app.core.security.sso import load_sso_public_key
    load_sso_public_key()

    # 4. LangSmith 초기화 (옵션)
    init_langsmith()

    yield  # 앱 실행

    # 종료: 워커 정리 + DB 커넥션 풀 종료
    history_service.stop_worker()
    db_manager.close()
    external_db_manager.close()
```

---

## 4. 미들웨어 스택

```
등록 순서 (역순 실행):
  app.add_middleware(HistoryMiddleware)      # 5. 이력 저장
  app.add_middleware(RateLimitMiddleware)    # 4. 요청 속도 제한
  app.add_middleware(AuthMiddleware)         # 3. 인증 검증
  app.add_middleware(LoggingMiddleware)      # 2. 요청/응답 로깅 + request_id
  app.add_middleware(CORSMiddleware, ...)    # 1. CORS

요청 실행 순서:
  CORS → Logging → Auth → RateLimit → History → Handler

응답 실행 순서:
  Handler → History → RateLimit → Auth → Logging → CORS
```

---

## 5. 배포 스크립트

### 5.1 Backend (`deploy-docker.sh`)

```
로컬 빌드 → SSH로 이미지/파일 전송 → 원격 Docker 실행
```

| 설정 | 값 |
|------|---|
| REMOTE_HOST | 115.68.223.220 |
| REMOTE_USER | deabal |
| REMOTE_DIR | /home/deabal/mureum/backend |
| CONTAINER | mureum-backend |
| PORT | 19090 |
| NETWORK | mureum-network |
| LOGS | /data/files/mureum/logs |
| ENV_FILE | .env.docker |

**배포 단계**:
1. SSH 연결 확인 (키 기반 인증)
2. 환경 검증 (.env.docker, requirements.txt, Dockerfile, app/ 확인)
3. 파일 전송 (Dockerfile, .env.docker, requirements.txt, app/, scripts/)
4. Docker 이미지 빌드 (기존 이미지 백업 → 신규 빌드)
5. 컨테이너 배포 (기존 중지 → 네트워크 생성 → 신규 실행)
6. 검증 (health check, Swagger UI, 컨테이너 로그)
7. 정리 (이전 이미지 prune)

### 5.2 Frontend (`frontend/deploy-docker.sh`)

| 설정 | 값 |
|------|---|
| REMOTE_DIR | /home/deabal/mureum/frontend |
| CONTAINER | mureum-frontend |
| PORT | 19080 |
| ENV_FILE | .env.docker |

---

## 6. 환경변수

### 6.1 Backend (.env)

| 카테고리 | 변수 | 기본값 | 설명 |
|----------|------|--------|------|
| **DB** | DATABASE_URL | - | PostgreSQL 연결 문자열 |
| | DB_POOL_SIZE | 20 | 커넥션 풀 크기 |
| | DB_MAX_OVERFLOW | 10 | 최대 초과 커넥션 |
| **LLM** | OPENAI_API_KEY | - | OpenAI API 키 |
| | ANTHROPIC_API_KEY | - | Anthropic API 키 (선택) |
| | GOOGLE_API_KEY | - | Google Gemini API 키 (선택) |
| | LLM_PROVIDER | openai | openai / anthropic / google |
| | LLM_MODEL | gpt-4-turbo-preview | 기본 LLM 모델 |
| | EMBEDDING_MODEL | text-embedding-3-small | 임베딩 모델 |
| | EMBEDDING_DIMENSION | 1536 | 임베딩 차원 |
| **앱** | APP_ENV | development | 환경 (development/staging/production) |
| | APP_HOST | 0.0.0.0 | 서버 호스트 |
| | APP_PORT | 19090 | 서버 포트 |
| | CONTEXT_PATH | (빈값) | FastAPI root_path (리버스 프록시용) |
| | CORS_ORIGINS | * | CORS 허용 도메인 |
| **보안 (JWT)** | SECRET_KEY | - | JWT 서명 키 |
| | ALGORITHM | HS256 | JWT 알고리즘 |
| | ACCESS_TOKEN_EXPIRE_MINUTES | 30 | 액세스 토큰 만료 |
| | JWT_REFRESH_TOKEN_EXPIRE_DAYS | 7 | 리프레시 토큰 만료 |
| | PASSWORD_MIN_LENGTH | 8 | 최소 비밀번호 길이 |
| | LOGIN_MAX_FAIL_COUNT | 5 | 로그인 실패 한도 |
| | LOGIN_LOCK_MINUTES | 30 | 계정 잠금 시간 |
| **SSO** | SSO_ENABLED | false | SSO 활성화 여부 |
| | SSO_PUBLIC_KEY_PATH | keys/sso_public.pem | RS256 공개키 경로 |
| | SSO_ALGORITHM | RS256 | SSO JWT 알고리즘 (고정) |
| | SSO_ALLOWED_ISSUERS | hr-system | 허용 발급자 (쉼표 구분) |
| | SSO_TOKEN_MAX_AGE | 300 | SSO 토큰 최대 유효시간 (초) |
| | SSO_DEFAULT_ROLE | USER | 자동 생성 시 기본 역할 (Phase 5) |
| | SSO_AUTO_CREATE_USER | false | 사용자 자동 생성 (Phase 5) |
| **Rate Limit** | RATE_LIMIT_ENABLED | true | 속도 제한 활성화 |
| | RATE_LIMIT_DEFAULT_RPM | 120 | 기본 RPM |
| | RATE_LIMIT_LOGIN_RPM | 5 | 로그인 RPM |
| | RATE_LIMIT_AI_RPM | 20 | AI 검색 RPM |
| | RATE_LIMIT_ADMIN_RPM | 60 | 관리 API RPM |
| **RAG** | RAG_TOP_K | 10 | 검색 결과 수 |
| | RAG_SIMILARITY_THRESHOLD | 0.7 | 유사도 임계값 |
| **NL2SQL** | SQL_TIMEOUT_SECONDS | 30 | SQL 실행 타임아웃 |
| | SQL_MAX_ROWS | 1000 | 최대 반환 행 |
| **로그** | LOG_LEVEL | INFO | 로그 레벨 |
| | LOG_FORMAT | text | text / json |
| | LOG_FILE | ./logs/app.log | 로그 파일 경로 |
| | LOG_BACKUP_COUNT | 30 | 로그 보관 일수 |
| **LangSmith** | LANGCHAIN_TRACING_V2 | - | LangSmith 트레이싱 활성화 |
| | LANGCHAIN_API_KEY | - | LangSmith API 키 |
| | LANGCHAIN_PROJECT | - | LangSmith 프로젝트명 |

> **설정 우선순위**: Admin UI (DB tb_app_settings) > .env 환경변수 > config.py 기본값

### 6.2 Frontend (.env)

| 변수 | 개발 | Docker | 운영 |
|------|------|--------|------|
| VITE_API_URL | `http://localhost:19090` | (빈값) | `https://api.company.com` |
| VITE_APP_TITLE | Chatbot - MUREUM | Chatbot - MUREUM | Chatbot - MUREUM |

---

## 7. 헬스체크

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

## 8. 로깅

### 8.1 구조화 로깅

```python
log_step(logger, request_id, "MODULE", "STEP", "ACTION", "Message", key=value)
```

- request_id: 8자 UUID (LoggingMiddleware에서 생성)
- 포맷: text (개발) / json (운영)
- 파일: `./logs/app.log` (30일 보관, 일별 로테이션)

### 8.2 API 이력

- HistoryMiddleware → 비동기 워커 큐 → `tb_api_history` DB 저장
- JSONB trace_data에 실행 추적 정보 저장 (도구, SQL, 소스 등)

---

## 9. Rate Limiting

### 9.1 구현 방식

- **알고리즘**: In-memory 슬라이딩 윈도우 (60초)
- **식별**: 인증 사용자 → user_id, 미인증 → IP 주소
- **정리 주기**: 5분 간격으로 만료 레코드 정리
- **스레드 안전**: `threading.Lock` 사용

### 9.2 엔드포인트 그룹별 RPM

| 그룹 | 대상 경로 | 기본 RPM | 설명 |
|------|----------|---------|------|
| Auth | `/api/v1/auth/login`, `/api/v1/auth/refresh` | 10 | 인증 보호 |
| AI Search | `/api/v1/agent/search`, `/api/v1/search/*` | 20 | LLM 비용 보호 |
| Admin | `/api/admin/v1/*` | 60 | 관리 API |
| Default | 기타 | 120 | 일반 API |

### 9.3 응답 (HTTP 429)

```json
{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "요청이 너무 많습니다. 잠시 후 다시 시도해주세요",
    "detail": "분당 120회 제한 초과. 45초 후 재시도"
  }
}
```

**응답 헤더**: `Retry-After`, `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`

---

## 10. 운영 명령어

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

# SSO 키 생성
python scripts/generate_sso_keys.py
python scripts/generate_sso_keys.py --key-size 4096 --output-dir /custom/path
```

---

## 11. 스크립트 목록

| 파일 | 용도 |
|------|------|
| `scripts/generate_sso_keys.py` | SSO RS256 키 쌍 생성 |
| `scripts/add_multiturn_settings.py` | NL2SQL 멀티턴 설정 초기화 |
| `scripts/add_skip_answer_settings.py` | skip_answer 설정 초기화 |
| `scripts/check_oracle_schema.py` | Oracle 외부 DB 스키마 검증 |
| `scripts/check_tools_config.py` | Agent 도구 설정 확인 |
| `scripts/check_admin.py` | 관리자 계정 상태 확인 |
| `scripts/check_depts.py` | 부서 데이터 검증 |
| `scripts/reset_admin_password.py` | 관리자 비밀번호 초기화 |
| `deploy-docker.sh` | 백엔드 원격 Docker 배포 |
| `frontend/deploy-docker.sh` | 프론트엔드 원격 Docker 배포 |
| `deploy-gen-ssh-key.sh` | SSH 키 쌍 생성 |

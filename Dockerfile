# ============================================
# MUREUM Backend Dockerfile
# Python FastAPI + LangChain Application
# ============================================

FROM python:3.13-slim

# 작업 디렉토리 설정
WORKDIR /app

# 시스템 패키지 설치 및 시간대 설정
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    tzdata \
    gcc \
    libpq-dev \
    && ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime \
    && echo "Asia/Seoul" > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Python 환경 설정
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Seoul

# 의존성 파일 복사 및 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 애플리케이션 소스 복사
COPY app/ ./app/
COPY scripts/ ./scripts/

# SSO 공개키 복사
COPY keys/sso_public.pem ./keys/sso_public.pem

# 로그 디렉토리 생성
RUN mkdir -p logs

# 환경 변수 파일 복사 (Docker용)
# 실제 환경변수는 docker run 시 -e 또는 --env-file로 전달
COPY .env.docker .env

# 포트 노출
EXPOSE 19090

# 헬스체크 설정
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:19090/health || exit 1

# 애플리케이션 실행
# uvicorn으로 FastAPI 앱 실행
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "19090"]

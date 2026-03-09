from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """애플리케이션 설정"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Database
    database_url: str = Field(..., description="PostgreSQL 연결 URL")
    db_pool_size: int = Field(default=20, description="DB 커넥션 풀 크기")
    db_max_overflow: int = Field(default=10, description="DB 커넥션 풀 최대 초과")

    # OpenAI
    openai_api_key: str = Field(default="", description="OpenAI API 키 (DB tb_app_settings에서 관리, fallback 용도)")
    embedding_model: str = Field(default="text-embedding-3-small", description="임베딩 모델")
    embedding_dimension: int = Field(default=1536, description="임베딩 차원 수")
    llm_model: str = Field(default="gpt-4-turbo-preview", description="LLM 모델")

    # Anthropic (Phase 2)
    anthropic_api_key: Optional[str] = Field(default=None, description="Anthropic API 키 (선택)")

    # Google Gemini (Phase 3)
    google_api_key: Optional[str] = Field(default=None, description="Google Gemini API 키 (선택)")

    # LLM Provider (Phase 3: OpenAI + Anthropic + Google 지원)
    llm_provider: str = Field(default="openai", description="LLM 제공자 (openai, anthropic, google)")
    embedding_provider: str = Field(default="openai", description="임베딩 제공자 (openai)")

    # Application
    app_env: str = Field(default="development", description="애플리케이션 환경")
    app_host: str = Field(default="0.0.0.0", description="애플리케이션 호스트")
    app_port: int = Field(default=19090, description="애플리케이션 포트")
    context_path: str = Field(default="", description="API Context Path (예: /mureum)")
    log_level: str = Field(default="INFO", description="로그 레벨")
    log_format: str = Field(default="text", description="로그 포맷 (text: 텍스트, json: JSON)")
    log_file: Optional[str] = Field(default=None, description="로그 파일 경로 (None이면 파일 출력 안함)")
    log_backup_count: int = Field(default=30, description="로그 파일 보관 일수")

    # CORS
    cors_origins: str = Field(
        default="*",
        description="CORS 허용 도메인 (쉼표로 구분, '*'는 전체 허용)"
    )

    # Security
    secret_key: str = Field(..., description="JWT 시크릿 키")
    algorithm: str = Field(default="HS256", description="JWT 알고리즘")
    access_token_expire_minutes: int = Field(default=30, description="액세스 토큰 만료 시간(분)")
    jwt_refresh_token_expire_days: int = Field(default=7, description="Refresh Token 만료 시간(일)")
    password_min_length: int = Field(default=8, description="최소 비밀번호 길이")
    login_max_fail_count: int = Field(default=5, description="로그인 실패 허용 횟수")
    login_lock_minutes: int = Field(default=30, description="계정 잠금 시간(분)")

    # Rate Limiting
    rate_limit_enabled: bool = Field(default=True, description="Rate Limiting 활성화 여부")
    rate_limit_default_rpm: int = Field(default=120, description="기본 분당 요청 수")
    rate_limit_login_rpm: int = Field(default=5, description="로그인 분당 요청 수")
    rate_limit_ai_rpm: int = Field(default=20, description="AI 검색 분당 요청 수")
    rate_limit_admin_rpm: int = Field(default=60, description="관리자 API 분당 요청 수")

    # RAG Settings
    rag_top_k: int = Field(default=10, description="RAG 검색 시 상위 K개 문서")
    rag_distance_metric: str = Field(default="cosine", description="거리 측정 방식 (cosine, l2)")
    rag_similarity_threshold: float = Field(default=0.7, description="RAG 유사도 임계값")
    max_context_length: int = Field(default=4000, description="최대 컨텍스트 길이")

    # NL2SQL Settings (DB에서 동적 관리, fallback 용도)
    sql_timeout_seconds: int = Field(default=30, description="SQL 실행 타임아웃(초)")
    sql_max_rows: int = Field(default=1000, description="SQL 최대 반환 행 수")
    read_only_mode: bool = Field(default=True, description="읽기 전용 모드")

    # LangSmith (Optional)
    langchain_tracing_v2: Optional[bool] = Field(default=None, description="LangSmith 트레이싱 활성화")
    langchain_endpoint: Optional[str] = Field(default=None, description="LangSmith API 엔드포인트")
    langchain_api_key: Optional[str] = Field(default=None, description="LangSmith API 키")
    langchain_project: Optional[str] = Field(default=None, description="LangSmith 프로젝트 이름")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        v = v.upper()
        if v not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v

    @field_validator("log_format")
    @classmethod
    def validate_log_format(cls, v: str) -> str:
        valid_formats = ["text", "json"]
        v = v.lower()
        if v not in valid_formats:
            raise ValueError(f"log_format must be one of {valid_formats}")
        return v

    @field_validator("app_env")
    @classmethod
    def validate_app_env(cls, v: str) -> str:
        valid_envs = ["development", "staging", "production"]
        v = v.lower()
        if v not in valid_envs:
            raise ValueError(f"app_env must be one of {valid_envs}")
        return v

    @field_validator("llm_provider")
    @classmethod
    def validate_llm_provider(cls, v: str) -> str:
        # Phase 3: OpenAI + Anthropic + Google (genai) / Google Vertex
        valid_providers = ["openai", "anthropic", "google", "google_vertex"]
        v = v.lower()
        if v not in valid_providers:
            raise ValueError(f"llm_provider must be one of {valid_providers}")
        return v

    @field_validator("embedding_provider")
    @classmethod
    def validate_embedding_provider(cls, v: str) -> str:
        # Phase 2: Embedding은 OpenAI만 (Anthropic은 임베딩 미제공)
        valid_providers = ["openai"]
        v = v.lower()
        if v not in valid_providers:
            raise ValueError(f"embedding_provider must be one of {valid_providers}")
        return v

    @property
    def is_production(self) -> bool:
        """프로덕션 환경 여부"""
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        """개발 환경 여부"""
        return self.app_env == "development"

    @property
    def langsmith_enabled(self) -> bool:
        """LangSmith 활성화 여부"""
        return (
            self.langchain_tracing_v2 is True
            and self.langchain_api_key is not None
        )


# 캐싱 : 한번만 로드
@lru_cache    
def get_settings() -> Settings:
    """설정 인스턴스 반환 (캐싱됨)"""
    return Settings()


# 글로벌 설정 인스턴스
settings = get_settings()

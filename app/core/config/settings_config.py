"""시스템 설정 Core 서비스 (읽기 전용)

런타임에 설정을 조회할 수 있는 Core 서비스.
DB 설정 → 환경변수 → 기본값 순서로 fallback.

위치: app/core/config/settings_config.py
- 설정 스키마 정의 (DEFAULTS, ENV_MAPPING)
- 설정 읽기 및 캐싱
- 마스킹 유틸리티
- 모든 서비스, 그래프, 도구에서 사용

Note: CRUD 작업은 app/api/services/settings_service.py에서 처리
"""
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from unittest import result

from app.config import settings as env_settings
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 순환 import 방지를 위해 지연 import
_db_manager = None


def _get_db_manager():
    """DB 매니저 지연 로딩"""
    global _db_manager
    if _db_manager is None:
        from app.core.database.connection import db_manager
        _db_manager = db_manager
    return _db_manager


class SettingsConfig:
    """시스템 설정 Core 서비스 (읽기 전용 + 캐싱)"""

    # 카테고리별 기본값 정의: (default_value, value_type, description, is_secret)
    DEFAULTS = {
        "openai": {
            "api_key": ("", "string", "OpenAI API Key", True),
            "organization_id": ("", "string", "OpenAI Organization ID (선택)", False),
        },
        "anthropic": {
            "api_key": ("", "string", "Anthropic API Key (Phase 2)", True),
        },
        "embedding": {
            "model": ("text-embedding-3-small", "string", "임베딩 모델명", False),
            "provider": ("openai", "string", "임베딩 제공자 (현재 openai만 지원)", False),
            "dimension": ("1536", "int", "벡터 차원 수", False),
        },
        "llm": {
            "model": ("gpt-4.1-mini", "string", "LLM 모델명", False),
            "provider": ("openai", "string", "LLM 제공자 (openai, anthropic)", False),
            "temperature": ("0.1", "float", "생성 온도 (0.0-2.0)", False),
            "max_tokens": ("2000", "int", "최대 토큰 수", False),
        },
        "rag": {
            "top_k": ("5", "int", "검색 문서 수", False),
            "distance_metric": ("cosine", "string", "거리 측정 방식 (cosine, l2)", False),
            "similarity_threshold": ("0.7", "float", "유사도 임계값 (0.0-1.0)", False),
            "max_context_length": ("4000", "int", "최대 컨텍스트 길이", False),
        },
        "nl2sql": {
            "timeout_seconds": ("30", "int", "SQL 실행 타임아웃 (초)", False),
            "max_rows": ("1000", "int", "최대 반환 행 수", False),
            "read_only_mode": ("true", "bool", "읽기 전용 모드", False),
        },
        "chunking": {
            "default_chunk_size": ("1000", "int", "기본 청크 크기 (문자)", False),
            "default_overlap": ("100", "int", "기본 오버랩 크기 (문자)", False),
        },
        "agent": {
            "max_iterations": ("10", "int", "최대 반복 횟수 (1-20)", False),
            "timeout_seconds": ("60", "int", "전체 타임아웃 (초, 10-300)", False),
            "llm_provider": ("openai", "string", "Agent용 LLM 제공자 (openai, anthropic)", False),
            "llm_temperature": ("0.0", "float", "Agent LLM 온도 (0.0-2.0)", False),
            "enable_memory": ("true", "bool", "대화 메모리 활성화", False),
            "enable_streaming": ("false", "bool", "스트리밍 응답 (확장)", False),
            "enabled_tools": ("context_search_tool,query_database_tool,search_documents_tool,calculate_tool", "string", "사용 가능한 도구 (쉼표 구분)", False),
        },
        "external_database": {
            "enabled": ("false", "bool", "외부 비즈니스 DB 사용 여부", False),
            "db_type": ("postgresql", "string", "DB 타입 (postgresql, oracle, mysql)", False),
            "host": ("localhost", "string", "DB 호스트", False),
            "port": ("5432", "int", "DB 포트", False),
            "database": ("chatbot_system", "string", "데이터베이스 이름", False),
            "username": ("postgres", "string", "DB 사용자명", False),
            "password": ("", "string", "DB 비밀번호", True),
            "schema": ("business", "string", "비즈니스 데이터 스키마", False),
            "allowed_tables": ("employee,department,job_history,performance_review,salary", "string", "NL2SQL 쿼리 허용 테이블", False),
            "connection_pool_size": ("5", "int", "연결 풀 크기", False),
            "connection_timeout": ("10", "int", "연결 타임아웃 (초)", False),
        },
        "prompt": {
            "rag_system_prompt": ("", "text", "RAG 답변 생성용 시스템 프롬프트", False),
            "rag_persona": ("기업용 지식 베이스 전문가", "string", "RAG 시스템의 페르소나", False),
            "nl2sql_generation_prompt": ("", "text", "NL2SQL SQL 생성용 프롬프트", False),
            "nl2sql_answer_prompt": ("", "text", "NL2SQL 답변 생성용 프롬프트", False),
            "nl2sql_sql_persona": ("PostgreSQL 전문가", "string", "NL2SQL SQL 생성 시 페르소나", False),
            "nl2sql_answer_persona": ("데이터 분석 전문가", "string", "NL2SQL 답변 생성 시 페르소나", False),
            "agent_system_prompt": ("", "text", "Agent 시스템 프롬프트 (ReAct 패턴)", False),
            "agent_persona": ("AI assistant for corporate knowledge base", "string", "Agent 페르소나", False),
            "tool_sql_description": ("", "text", "SQL Tool 설명 (Agent용)", False),
            "tool_rag_description": ("", "text", "RAG Tool 설명 (Agent용)", False),
            "tool_calculator_description": ("", "text", "Calculator Tool 설명 (Agent용)", False),
        },
    }

    # 환경변수 매핑 (category.key -> env_settings attribute)
    ENV_MAPPING = {
        "openai.api_key": "openai_api_key",
        "embedding.model": "embedding_model",
        "embedding.dimension": "embedding_dimension",
        "llm.model": "llm_model",
        "rag.top_k": "rag_top_k",
        "rag.distance_metric": "rag_distance_metric",
        "rag.similarity_threshold": "rag_similarity_threshold",
        "rag.max_context_length": "max_context_length",
        "nl2sql.timeout_seconds": "sql_timeout_seconds",
        "nl2sql.max_rows": "sql_max_rows",
        "nl2sql.read_only_mode": "read_only_mode",
    }

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_loaded = False

    # ============================================================================
    # 내부 유틸리티
    # ============================================================================

    def _ensure_table_exists(self) -> bool:
        """설정 테이블 존재 여부 확인"""
        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'tb_app_settings')")
                return cur.fetchone()['exists']
        except Exception as e:
            logger.warning(f"설정 테이블 확인 실패: {e}")
            return False

    def _load_cache(self, force: bool = False) -> None:
        """DB에서 캐시 로드"""
        if self._cache_loaded and not force:
            return

        if not self._ensure_table_exists():
            logger.warning("tb_app_settings 테이블이 없습니다. 기본값 사용.")
            self._cache_loaded = True
            return

        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT category, key, value, value_type, description, is_secret, updated_at FROM tb_app_settings ORDER BY category, key")
                rows = cur.fetchall()

                self._cache = {}
                for row in rows:
                    category = row['category']
                    if category not in self._cache:
                        self._cache[category] = {}
                    self._cache[category][row['key']] = {
                        'value': row['value'],
                        'value_type': row['value_type'],
                        'description': row['description'],
                        'is_secret': row['is_secret'],
                        'updated_at': row['updated_at']
                    }
                self._cache_loaded = True
                logger.debug(f"설정 캐시 로드 완료: {len(rows)}개 항목")

        except Exception as e:
            logger.error(f"설정 캐시 로드 실패: {e}")
            self._cache_loaded = True

    def _get_env_value(self, category: str, key: str) -> Optional[str]:
        """환경변수에서 값 조회"""
        env_key = f"{category}.{key}"
        if env_key in self.ENV_MAPPING:
            attr_name = self.ENV_MAPPING[env_key]
            if hasattr(env_settings, attr_name):
                value = getattr(env_settings, attr_name)
                if value is not None:
                    return str(value)
        return None

    def _get_default_value(self, category: str, key: str) -> Optional[Tuple[str, str, str, bool]]:
        """기본값 조회 (value, value_type, description, is_secret)"""
        if category in self.DEFAULTS and key in self.DEFAULTS[category]:
            return self.DEFAULTS[category][key]
        return None

    def _query_setting_from_db(self, category: str, key: str) -> Optional[Dict[str, Any]]:
        """DB에서 직접 설정 조회 (캐시 우회)"""
        if not self._ensure_table_exists():
            return None

        try:
            db_manager = _get_db_manager()
            with db_manager.get_cursor() as cur:
                cur.execute("SELECT value, value_type, description, is_secret, updated_at FROM tb_app_settings WHERE category = %s AND key = %s", (category, key))
                row = cur.fetchone()
                if row:
                    return {'value': row['value'], 'value_type': row['value_type'], 'description': row['description'], 'is_secret': row['is_secret'], 'updated_at': row['updated_at'], 'source': 'db'}
        except Exception as e:
            logger.error(f"DB 설정 조회 실패: {category}.{key} - {e}")
        return None

    def _update_cache(self, category: str, key: str, value: str, value_type: str, description: str, is_secret: bool, updated_at: datetime) -> None:
        """캐시 갱신 (API 서비스에서 호출)"""
        if category not in self._cache:
            self._cache[category] = {}
        self._cache[category][key] = {'value': value, 'value_type': value_type, 'description': description, 'is_secret': is_secret, 'updated_at': updated_at}

    # ============================================================================
    # 설정 조회 (읽기 전용)
    # ============================================================================

    def get_setting(self, category: str, key: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        단일 설정 조회 (우선순위: DB → 환경변수 → 기본값)

        Args:
            category: 설정 카테고리
            key: 설정 키
            use_cache: 캐시 사용 여부
        """
        # 1. DB에서 조회
        if use_cache:
            self._load_cache()
            if category in self._cache and key in self._cache[category]:
                cached = self._cache[category][key]
                if cached['value']:
                    return cached
        else:
            db_value = self._query_setting_from_db(category, key)
            if db_value and db_value['value']:
                return db_value

        # 2. 환경변수에서 조회
        env_value = self._get_env_value(category, key)
        if env_value:
            default = self._get_default_value(category, key)
            return {'value': env_value, 'value_type': default[1] if default else 'string', 'description': default[2] if default else None, 'is_secret': default[3] if default else False, 'updated_at': None, 'source': 'env'}

        # 3. 기본값 반환
        default = self._get_default_value(category, key)
        if default:
            return {'value': default[0], 'value_type': default[1], 'description': default[2], 'is_secret': default[3], 'updated_at': None, 'source': 'default'}

        return None

    def get_value(self, category: str, key: str, default: Any = None, use_cache: bool = True) -> Any:
        """
        설정 값만 조회 (타입 변환 포함)

        다른 서비스/그래프에서 설정 값을 가져올 때 사용하는 주요 메서드

        Args:
            category: 설정 카테고리
            key: 설정 키
            default: 기본값 (설정이 없을 때)
            use_cache: 캐시 사용 여부
        """
        setting = self.get_setting(category, key, use_cache=use_cache)
        if not setting:
            return default

        value = setting['value']
        value_type = setting.get('value_type', 'string')

        try:
            if value_type == 'int':
                return int(value)
            elif value_type == 'float':
                return float(value)
            elif value_type == 'bool':
                return value.lower() in ('true', '1', 'yes')
            else:
                return value
        except (ValueError, AttributeError):
            return default

    def get_category_settings(self, category: str) -> List[Dict[str, Any]]:
        """카테고리별 설정 전체 조회"""
        self._load_cache()
        result = []
        if category in self.DEFAULTS:
            for key in self.DEFAULTS[category]:
                setting = self.get_setting(category, key)
                if setting:
                    result.append({'category': category, 'key': key, **setting})
        return result

    def get_all_settings(self) -> Dict[str, List[Dict[str, Any]]]:
        """전체 설정 조회"""
        self._load_cache()
        return {category: self.get_category_settings(category) for category in self.DEFAULTS}

    # ============================================================================
    # 마스킹 유틸리티
    # ============================================================================

    def mask_secret_value(self, value: str) -> str:
        """비밀 값 마스킹"""
        if not value or len(value) < 8:
            return "****"
        return value[:4] + "*" * (len(value) - 8) + value[-4:]

    def get_masked_settings(self, category: str) -> List[Dict[str, Any]]:
        """마스킹된 카테고리 설정 조회"""
        settings = self.get_category_settings(category)
        for setting in settings:
            if setting.get('is_secret') and setting.get('value'):
                setting['value'] = self.mask_secret_value(setting['value'])
        return settings

    def get_all_masked_settings(self) -> Dict[str, List[Dict[str, Any]]]:
        """마스킹된 전체 설정 조회"""
        result = {}
        for category in self.DEFAULTS:
            result[category] = self.get_masked_settings(category)
        return result
    #   return {category: self.get_masked_settings(category) for category in self.DEFAULTS}

    # ============================================================================
    # 캐시 관리
    # ============================================================================

    def refresh_cache(self) -> None:
        """캐시 강제 새로고침"""
        self._cache = {}
        self._cache_loaded = False
        self._load_cache(force=True)


# 싱글톤 인스턴스
settings_config = SettingsConfig()

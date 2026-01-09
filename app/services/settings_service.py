"""시스템 설정 관리 서비스

런타임에 설정을 조회/수정할 수 있는 서비스.
DB 설정 → 환경변수 → 기본값 순서로 fallback.
"""
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime

from app.config import settings as env_settings
from app.utils.database import db_manager
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class SettingsService:
    """시스템 설정 관리 서비스"""

    # 카테고리별 기본값 정의
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
            "model": ("gpt-4-turbo-preview", "string", "LLM 모델명", False),
            "provider": ("openai", "string", "LLM 제공자 (openai, anthropic)", False),
            "temperature": ("0.1", "float", "생성 온도 (0.0-2.0)", False),
            "max_tokens": ("2000", "int", "최대 토큰 수", False),
        },
        "rag": {
            "top_k": ("10", "int", "검색 문서 수", False),
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
            "llm_model": ("gpt-4o", "string", "Agent용 LLM 모델", False),
            "llm_provider": ("openai", "string", "Agent용 LLM 제공자 (openai, anthropic)", False),
            "llm_temperature": ("0.0", "float", "Agent LLM 온도 (0.0-2.0)", False),
            "enable_memory": ("true", "bool", "대화 메모리 활성화", False),
            "enable_streaming": ("false", "bool", "스트리밍 응답 (확장)", False),
            "enabled_tools": ("query_database,search_documents,calculate", "string", "사용 가능한 도구 (쉼표 구분)", False),
        },
        "external_database": {
            "enabled": ("false", "bool", "외부 비즈니스 DB 사용 여부 (비활성화 시 로컬 business 스키마 사용)", False),
            "db_type": ("postgresql", "string", "DB 타입 (postgresql, oracle, mysql)", False),
            "host": ("localhost", "string", "DB 호스트", False),
            "port": ("5432", "int", "DB 포트", False),
            "database": ("chatbot_system", "string", "데이터베이스 이름", False),
            "username": ("postgres", "string", "DB 사용자명", False),
            "password": ("", "string", "DB 비밀번호", True),
            "schema": ("business", "string", "비즈니스 데이터 스키마", False),
            "allowed_tables": ("employee,department,job_history,performance_review,salary", "string", "NL2SQL 쿼리 허용 테이블 (쉼표 구분)", False),
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
        "rag.similarity_threshold": "rag_similarity_threshold",
        "rag.max_context_length": "max_context_length",
        "nl2sql.timeout_seconds": "sql_timeout_seconds",
        "nl2sql.max_rows": "sql_max_rows",
        "nl2sql.read_only_mode": "read_only_mode",
    }

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._cache_loaded = False

    def _ensure_table_exists(self) -> bool:
        """설정 테이블 존재 여부 확인"""
        try:
            with db_manager.get_cursor() as cur:
                cur.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_name = 'app_settings'
                    )
                """)
                return cur.fetchone()['exists']
        except Exception as e:
            logger.warning(f"설정 테이블 확인 실패: {e}")
            return False

    def _load_cache(self, force: bool = False) -> None:
        """DB에서 캐시 로드"""
        if self._cache_loaded and not force:
            return

        if not self._ensure_table_exists():
            logger.warning("app_settings 테이블이 없습니다. 기본값 사용.")
            self._cache_loaded = True
            return

        try:
            with db_manager.get_cursor() as cur:
                cur.execute("""
                    SELECT category, key, value, value_type, description, is_secret, updated_at
                    FROM app_settings
                    ORDER BY category, key
                """)
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
            with db_manager.get_cursor() as cur:
                cur.execute("""
                    SELECT value, value_type, description, is_secret, updated_at
                    FROM app_settings
                    WHERE category = %s AND key = %s
                """, (category, key))
                row = cur.fetchone()

                if row:
                    return {
                        'value': row['value'],
                        'value_type': row['value_type'],
                        'description': row['description'],
                        'is_secret': row['is_secret'],
                        'updated_at': row['updated_at'],
                        'source': 'db'
                    }
        except Exception as e:
            logger.error(f"DB 설정 조회 실패: {category}.{key} - {e}")

        return None

    def get_setting(self, category: str, key: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
        """
        단일 설정 조회

        우선순위: DB → 환경변수 → 기본값
        """
        # 1. DB에서 조회
        if use_cache:
            self._load_cache()
            # 캐시에서 조회
            if category in self._cache and key in self._cache[category]:
                cached = self._cache[category][key]
                logger.debug(f"[GET DEBUG] {category}.{key} from cache, value length={len(cached.get('value', ''))}")
                if cached['value']:  # 빈 문자열이 아닌 경우
                    return cached
                else:
                    logger.warning(f"[GET DEBUG] {category}.{key} cached but value is empty!")
        else:
            # 캐시 사용 안 함 - DB에서 직접 조회
            db_value = self._query_setting_from_db(category, key)
            logger.debug(f"[GET DEBUG] {category}.{key} from DB (no cache), value length={len(db_value.get('value', '')) if db_value else 0}")
            if db_value and db_value['value']:
                return db_value

        # 2. 환경변수에서 조회
        env_value = self._get_env_value(category, key)
        if env_value:
            default = self._get_default_value(category, key)
            return {
                'value': env_value,
                'value_type': default[1] if default else 'string',
                'description': default[2] if default else None,
                'is_secret': default[3] if default else False,
                'updated_at': None,
                'source': 'env'
            }

        # 3. 기본값 반환
        default = self._get_default_value(category, key)
        if default:
            return {
                'value': default[0],
                'value_type': default[1],
                'description': default[2],
                'is_secret': default[3],
                'updated_at': None,
                'source': 'default'
            }

        return None

    def get_value(self, category: str, key: str, default: Any = None, use_cache: bool = True) -> Any:
        """설정 값만 조회 (타입 변환 포함)

        Args:
            category: 설정 카테고리
            key: 설정 키
            default: 기본값
            use_cache: 캐시 사용 여부 (기본 True - 성능 최적화)
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

        # DEFAULTS에서 해당 카테고리의 모든 키 가져오기
        if category in self.DEFAULTS:
            for key in self.DEFAULTS[category]:
                setting = self.get_setting(category, key)
                if setting:
                    result.append({
                        'category': category,
                        'key': key,
                        **setting
                    })

        return result

    def get_all_settings(self) -> Dict[str, List[Dict[str, Any]]]:
        """전체 설정 조회"""
        self._load_cache()

        result = {}
        for category in self.DEFAULTS:
            result[category] = self.get_category_settings(category)

        return result

    def set_setting(self, category: str, key: str, value: str, changed_by: str = 'system', change_reason: str = None) -> bool:
        """
        단일 설정 저장

        DB에 upsert하고 캐시 갱신
        프롬프트 카테고리의 경우 변경 이력 자동 저장

        Args:
            category: 설정 카테고리
            key: 설정 키
            value: 새로운 값
            changed_by: 변경자 (기본값: 'system')
            change_reason: 변경 사유 (선택)
        """
        if not self._ensure_table_exists():
            logger.error("app_settings 테이블이 없습니다.")
            return False

        default = self._get_default_value(category, key)
        if not default:
            logger.warning(f"알 수 없는 설정: {category}.{key}")
            return False

        try:
            with db_manager.get_cursor(commit=True) as cur:
                # 프롬프트 카테고리인 경우 기존 값 조회 (이력 저장용)
                old_value = None
                if category == 'prompt':
                    cur.execute("""
                        SELECT value FROM app_settings
                        WHERE category = %s AND key = %s
                    """, (category, key))
                    row = cur.fetchone()
                    if row:
                        old_value = row['value']

                # 설정 저장 (UPSERT)
                cur.execute("""
                    INSERT INTO app_settings (category, key, value, value_type, description, is_secret, updated_at)
                    VALUES (%s, %s, %s, %s, %s, %s, NOW())
                    ON CONFLICT (category, key)
                    DO UPDATE SET value = EXCLUDED.value, updated_at = NOW()
                    RETURNING updated_at
                """, (category, key, value, default[1], default[2], default[3]))

                row = cur.fetchone()
                updated_at = row['updated_at'] if row else datetime.now()

                # 프롬프트 카테고리인 경우 이력 저장
                if category == 'prompt' and old_value != value:
                    try:
                        cur.execute("""
                            INSERT INTO prompt_history (category, key, old_value, new_value, changed_by, change_reason)
                            VALUES (%s, %s, %s, %s, %s, %s)
                        """, (category, key, old_value, value, changed_by, change_reason or 'Manual update'))
                        logger.info(f"프롬프트 이력 저장: {category}.{key}")
                    except Exception as hist_err:
                        # 이력 저장 실패해도 설정 저장은 유지
                        logger.error(f"프롬프트 이력 저장 실패 (무시): {hist_err}")

                # 캐시 갱신
                if category not in self._cache:
                    self._cache[category] = {}
                self._cache[category][key] = {
                    'value': value,
                    'value_type': default[1],
                    'description': default[2],
                    'is_secret': default[3],
                    'updated_at': updated_at
                }

                logger.info(f"설정 저장: {category}.{key}")
                return True

        except Exception as e:
            logger.error(f"설정 저장 실패: {category}.{key} - {e}")
            return False

    def set_category_settings(self, category: str, settings: Dict[str, str]) -> Tuple[int, List[str]]:
        """
        카테고리별 설정 일괄 저장

        Returns:
            (성공 개수, 실패한 키 목록)
        """
        success_count = 0
        failed_keys = []

        for key, value in settings.items():
            if self.set_setting(category, key, value):
                success_count += 1
            else:
                failed_keys.append(key)

        return success_count, failed_keys

    def reset_category(self, category: str) -> bool:
        """카테고리 설정을 기본값으로 초기화"""
        if category not in self.DEFAULTS:
            return False

        if not self._ensure_table_exists():
            return False

        try:
            with db_manager.get_cursor(commit=True) as cur:
                # 해당 카테고리의 모든 설정을 기본값으로 업데이트
                for key, (value, value_type, desc, is_secret) in self.DEFAULTS[category].items():
                    cur.execute("""
                        UPDATE app_settings
                        SET value = %s, updated_at = NOW()
                        WHERE category = %s AND key = %s
                    """, (value, category, key))

                # 캐시 초기화
                if category in self._cache:
                    del self._cache[category]

                logger.info(f"카테고리 초기화: {category}")
                return True

        except Exception as e:
            logger.error(f"카테고리 초기화 실패: {category} - {e}")
            return False

    def refresh_cache(self) -> None:
        """캐시 강제 새로고침"""
        self._cache = {}
        self._cache_loaded = False
        self._load_cache(force=True)

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

    # ============================================================================
    # 프롬프트 이력 관리
    # ============================================================================

    def get_prompt_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        프롬프트 변경 이력 조회

        Args:
            limit: 조회할 최대 개수 (기본: 100, 최대: 1000)

        Returns:
            이력 목록 (최신순)
        """
        # 최대 제한 적용
        limit = min(limit, 1000)

        try:
            with db_manager.get_cursor() as cur:
                cur.execute("""
                    SELECT
                        id,
                        category,
                        key,
                        old_value,
                        new_value,
                        changed_by,
                        changed_at,
                        change_reason
                    FROM prompt_history
                    ORDER BY changed_at DESC
                    LIMIT %s
                """, (limit,))

                rows = cur.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"프롬프트 이력 조회 실패: {e}")
            return []

    def get_prompt_history_by_key(self, category: str, key: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        특정 프롬프트의 변경 이력 조회

        Args:
            category: 카테고리 (일반적으로 'prompt')
            key: 프롬프트 키
            limit: 조회할 최대 개수 (기본: 50, 최대: 500)

        Returns:
            해당 프롬프트의 이력 목록 (최신순)
        """
        # 최대 제한 적용
        limit = min(limit, 500)

        try:
            with db_manager.get_cursor() as cur:
                cur.execute("""
                    SELECT
                        id,
                        category,
                        key,
                        old_value,
                        new_value,
                        changed_by,
                        changed_at,
                        change_reason
                    FROM prompt_history
                    WHERE category = %s AND key = %s
                    ORDER BY changed_at DESC
                    LIMIT %s
                """, (category, key, limit))

                rows = cur.fetchall()
                return [dict(row) for row in rows]

        except Exception as e:
            logger.error(f"프롬프트 이력 조회 실패 ({category}.{key}): {e}")
            return []

    def restore_prompt_from_history(self, history_id: int, changed_by: str = 'system') -> bool:
        """
        특정 이력으로 프롬프트 복원

        Args:
            history_id: 복원할 이력 ID
            changed_by: 복원 작업자 (기본값: 'system')

        Returns:
            성공 여부
        """
        try:
            with db_manager.get_cursor(commit=True) as cur:
                # 이력에서 이전 값 조회
                cur.execute("""
                    SELECT category, key, old_value, new_value, changed_at
                    FROM prompt_history
                    WHERE id = %s
                """, (history_id,))

                history = cur.fetchone()
                if not history:
                    logger.error(f"이력을 찾을 수 없습니다: {history_id}")
                    return False

                category = history['category']
                key = history['key']
                restore_value = history['old_value']  # 이전 값으로 복원

                logger.info(f"[RESTORE DEBUG] history_id={history_id}, category={category}, key={key}")
                logger.info(f"[RESTORE DEBUG] old_value length={len(restore_value) if restore_value else 0}")
                logger.info(f"[RESTORE DEBUG] old_value preview={restore_value[:100] if restore_value else 'None'}")

                if restore_value is None:
                    logger.error(f"복원할 값이 없습니다 (최초 생성 이력): {history_id}")
                    return False

                # 현재 값 조회 (새로운 이력 저장용)
                cur.execute("""
                    SELECT value FROM app_settings
                    WHERE category = %s AND key = %s
                """, (category, key))

                current_row = cur.fetchone()
                current_value = current_row['value'] if current_row else None
                logger.info(f"[RESTORE DEBUG] current_value length={len(current_value) if current_value else 0}")

                # 프롬프트 값 업데이트
                logger.info(f"[RESTORE DEBUG] Updating app_settings with restore_value")
                cur.execute("""
                    UPDATE app_settings
                    SET value = %s, updated_at = NOW()
                    WHERE category = %s AND key = %s
                """, (restore_value, category, key))

                affected_rows = cur.rowcount
                logger.info(f"[RESTORE DEBUG] UPDATE affected {affected_rows} rows")

                # 복원 작업도 이력에 기록
                cur.execute("""
                    INSERT INTO prompt_history (category, key, old_value, new_value, changed_by, change_reason)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    category,
                    key,
                    current_value,
                    restore_value,
                    changed_by,
                    f'Restored from history #{history_id} ({history["changed_at"]})'
                ))

                # 캐시 무효화 - 전체 캐시 재로드하도록 플래그 초기화
                self._cache_loaded = False
                logger.info(f"[RESTORE DEBUG] Cache invalidated, will reload on next access")

                logger.info(f"프롬프트 복원 완료: {category}.{key} (history_id={history_id})")
                return True

        except Exception as e:
            logger.error(f"프롬프트 복원 실패: {e}")
            return False


# 싱글톤 인스턴스
settings_service = SettingsService()

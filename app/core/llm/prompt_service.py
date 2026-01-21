"""프롬프트 관리 서비스

위치: app/core/llm/prompt_service.py
- DB에 저장된 프롬프트를 조회하고 캐싱하여 성능을 최적화합니다.
"""
import time
from typing import Dict

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 순환 import 방지를 위해 지연 import
_settings_service = None


def _get_settings_service():
    global _settings_service
    if _settings_service is None:
        from app.core.config.settings_config import settings_config
        _settings_service = settings_config
    return _settings_service


class PromptService:
    """프롬프트 관리 서비스

    DB에서 프롬프트를 조회하고 캐싱하여 LLM 호출 시 사용합니다.
    """

    def __init__(self):
        """초기화"""
        self.cache: Dict[str, tuple[float, str]] = {}
        self.cache_ttl = 300  # 5분 (프롬프트는 자주 변경되지 않으므로 캐시 유지)

    def get_prompt(self, prompt_key: str, default: str = "") -> str:
        """프롬프트 조회

        캐시에서 먼저 조회하고, 없으면 DB에서 조회합니다.

        Args:
            prompt_key: 프롬프트 키 (예: 'rag_system_prompt')
            default: 기본값 (DB에 없을 경우 반환)

        Returns:
            프롬프트 문자열
        """
        # 캐시 확인
        if prompt_key in self.cache:
            cached_time, value = self.cache[prompt_key]
            if time.time() - cached_time < self.cache_ttl:
                logger.debug(f"프롬프트 캐시 히트: {prompt_key}")
                return value

        # DB에서 조회
        try:
            settings_service = _get_settings_service()
            value = settings_service.get_value('prompt', prompt_key, default)

            # 캐시 저장
            self.cache[prompt_key] = (time.time(), value)
            logger.debug(f"프롬프트 DB 조회: {prompt_key}")

            return value
        except Exception as e:
            logger.error(f"프롬프트 조회 실패: {prompt_key}, {e}")
            return default

    def update_prompt(self, prompt_key: str, value: str) -> bool:
        """프롬프트 업데이트

        Args:
            prompt_key: 프롬프트 키
            value: 새로운 프롬프트 값

        Returns:
            성공 여부
        """
        try:
            settings_service = _get_settings_service()
            success = settings_service.set_setting('prompt', prompt_key, value)
            if success:
                # 캐시 무효화
                self.cache.pop(prompt_key, None)
                logger.info(f"프롬프트 업데이트 성공: {prompt_key}")
            return success
        except Exception as e:
            logger.error(f"프롬프트 업데이트 실패: {prompt_key}, {e}")
            return False

    def refresh_cache(self):
        """캐시 전체 무효화"""
        self.cache.clear()
        logger.info("프롬프트 캐시 전체 무효화")

    # =============================================================================
    # RAG 프롬프트
    # =============================================================================

    def get_rag_system_prompt(self) -> str:
        """RAG 시스템 프롬프트 조회

        Returns:
            RAG 답변 생성용 시스템 프롬프트
        """
        default = """당신은 기업용 지식 베이스 전문가입니다.
제공된 문서를 기반으로 사용자의 질문에 정확하고 친절하게 답변해주세요."""

        return self.get_prompt('rag_system_prompt', default)

    def get_rag_persona(self) -> str:
        """RAG 페르소나 조회

        Returns:
            RAG 시스템의 페르소나
        """
        return self.get_prompt('rag_persona', '기업용 지식 베이스 전문가')

    # =============================================================================
    # NL2SQL 프롬프트
    # =============================================================================

    def get_nl2sql_generation_prompt(self, schema_description: str = "", db_type: str = "postgresql") -> str:
        """NL2SQL SQL 생성 프롬프트 조회

        Args:
            schema_description: DB 스키마 설명 (프롬프트에 주입됨)
            db_type: 데이터베이스 타입 (postgresql, oracle)

        Returns:
            SQL 생성용 프롬프트 (스키마 정보 포함)
        """
        # DB 타입에 따른 기본 프롬프트
        if db_type == "oracle":
            default = """당신은 Oracle 전문가입니다.
사용자의 자연어 질문을 Oracle SQL 쿼리로 변환해주세요.

주의사항:
- LIMIT 대신 FETCH FIRST N ROWS ONLY 사용 (Oracle 12c+)
- 문자열 비교 시 대소문자 주의 (Oracle은 대소문자 구분)
- 날짜 형식: TO_DATE('YYYY-MM-DD', 'YYYY-MM-DD')
- NVL 함수 사용 (COALESCE 대신)

# 데이터베이스 스키마
{schema_description}"""
        else:
            default = """당신은 PostgreSQL 전문가입니다.
사용자의 자연어 질문을 PostgreSQL SQL 쿼리로 변환해주세요.

# 데이터베이스 스키마
{schema_description}"""

        template = self.get_prompt('nl2sql_generation_prompt', default)

        # 스키마 정보 주입
        return template.format(schema_description=schema_description)

    def get_nl2sql_answer_prompt(self) -> str:
        """NL2SQL 답변 생성 프롬프트 조회

        Returns:
            SQL 결과를 자연어로 변환하는 프롬프트
        """
        default = """당신은 데이터 분석 전문가입니다.
SQL 쿼리 결과를 사용자가 이해하기 쉽게 자연어로 요약해주세요."""

        return self.get_prompt('nl2sql_answer_prompt', default)

    def get_nl2sql_sql_persona(self, db_type: str = "postgresql") -> str:
        """NL2SQL SQL 생성 페르소나 조회

        Args:
            db_type: 데이터베이스 타입 (postgresql, oracle)

        Returns:
            SQL 생성 시 페르소나
        """
        default_persona = "Oracle 전문가" if db_type == "oracle" else "PostgreSQL 전문가"
        return self.get_prompt('nl2sql_sql_persona', default_persona)

    def get_nl2sql_answer_persona(self) -> str:
        """NL2SQL 답변 생성 페르소나 조회

        Returns:
            답변 생성 시 페르소나
        """
        return self.get_prompt('nl2sql_answer_persona', '데이터 분석 전문가')

    # =============================================================================
    # Agent 프롬프트
    # =============================================================================

    def get_agent_system_prompt(self) -> str:
        """Agent 시스템 프롬프트 조회

        Returns:
            Agent 기본 시스템 프롬프트 (ReAct 패턴)
        """
        default = """당신은 기업용 지식베이스와 데이터베이스 시스템을 위한 AI 어시스턴트입니다.
사용 가능한 도구를 활용하여 사용자의 질문에 정확하게 답변해주세요."""

        return self.get_prompt('agent_system_prompt', default)

    def get_agent_persona(self) -> str:
        """Agent 페르소나 조회

        Returns:
            Agent 페르소나
        """
        return self.get_prompt('agent_persona', 'AI assistant for corporate knowledge base')

    # =============================================================================
    # Tool 설명
    # =============================================================================

    def get_tool_sql_description(self) -> str:
        """SQL Tool 설명 조회

        Returns:
            SQL Tool 설명 (Agent에서 도구 선택 시 참조)
        """
        default = """Query the database using natural language.

Use this tool when you need to:
- Get counts, statistics, aggregations from structured tables
- Find specific record information"""

        return self.get_prompt('tool_sql_description', default)

    def get_tool_rag_description(self) -> str:
        """RAG Tool 설명 조회

        Returns:
            RAG Tool 설명 (Agent에서 도구 선택 시 참조)
        """
        default = """Search corporate documents and regulations.

Use this tool when you need to:
- Find company policies
- Look up company regulations and guidelines"""

        return self.get_prompt('tool_rag_description', default)

    def get_tool_calculator_description(self) -> str:
        """Calculator Tool 설명 조회

        Returns:
            Calculator Tool 설명 (Agent에서 도구 선택 시 참조)
        """
        default = """Perform mathematical calculations.

Use this tool when you need to:
- Calculate percentages, averages, sums
- Perform arithmetic operations"""

        return self.get_prompt('tool_calculator_description', default)


# 싱글톤 인스턴스
prompt_service = PromptService()

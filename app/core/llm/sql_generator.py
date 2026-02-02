"""SQL 생성 공통 서비스

위치: app/core/llm/sql_generator.py
- 자연어 → SQL 변환 통합 로직
- Agent SQL Tool과 NL2SQL Graph에서 공통 사용
- 프롬프트 서비스 연동 (DB 동적 로드)
- 다중 DB 지원 (PostgreSQL, Oracle)
"""
from typing import Dict, Tuple, Any
import logging

from langchain_core.messages import HumanMessage, SystemMessage

from app.utils.logger import setup_logger, log_step
from app.utils.common import strip_markdown_code_block

logger = setup_logger(__name__)

# 순환 import 방지를 위해 지연 import
_schema_loader = None
_external_db_manager = None
_prompt_service = None
_llm_config_manager = None
_settings_config = None


def _get_schema_loader():
    global _schema_loader
    if _schema_loader is None:
        from app.core.database.schema_loader import schema_loader
        _schema_loader = schema_loader
    return _schema_loader


def _get_external_db_manager():
    global _external_db_manager
    if _external_db_manager is None:
        from app.core.database.external import external_db_manager
        _external_db_manager = external_db_manager
    return _external_db_manager


def _get_prompt_service():
    global _prompt_service
    if _prompt_service is None:
        from app.core.llm.prompt_service import prompt_service
        _prompt_service = prompt_service
    return _prompt_service


def _get_llm_config_manager():
    global _llm_config_manager
    if _llm_config_manager is None:
        from app.core.llm.llm_config import LLMConfigManager
        _llm_config_manager = LLMConfigManager
    return _llm_config_manager


def _get_settings_config():
    global _settings_config
    if _settings_config is None:
        from app.core.config.settings_config import settings_config
        _settings_config = settings_config
    return _settings_config


class SQLGeneratorService:
    """SQL 생성 공통 서비스

    Agent SQL Tool과 NL2SQL Graph에서 공통으로 사용하는 SQL 생성 로직을 제공합니다.

    주요 기능:
    - 스키마 로드 및 캐싱
    - DB 타입 자동 감지 (PostgreSQL, Oracle)
    - 프롬프트 서비스 연동 (Admin UI 설정 반영)
    - LLM 호출 및 마크다운 제거
    """

    def __init__(self):
        self._schema_cache: str = None

    def get_schema_description(self, refresh: bool = False) -> str:
        """
        스키마 설명 조회 (캐싱 지원)

        Args:
            refresh: 캐시 무시하고 새로 로드

        Returns:
            LLM용 스키마 설명 문자열
        """
        if refresh or self._schema_cache is None:
            schema_loader = _get_schema_loader()
            self._schema_cache = schema_loader.generate_schema_description()
            log_step("SYSTEM", "SQL-GEN", "SCHEMA", "CACHE", "스키마 캐시 갱신 완료")

        return self._schema_cache

    def get_db_type(self) -> str:
        """
        현재 DB 타입 조회

        Returns:
            'postgresql' 또는 'oracle'
        """
        external_db_manager = _get_external_db_manager()
        return external_db_manager.get_db_type()

    def get_sql_dialect(self) -> str:
        """
        SQL 방언 이름 조회

        Returns:
            'PostgreSQL' 또는 'Oracle'
        """
        external_db_manager = _get_external_db_manager()
        adapter = external_db_manager.get_adapter()
        return adapter.get_sql_dialect_name()

    def generate_sql(
        self,
        question: str,
        request_id: str = "unknown",
        temperature: float = 0,
        schema_description: str = None
    ) -> Tuple[str, Dict[str, Any]]:
        """
        자연어 → SQL 변환 (공통 로직)

        Args:
            question: 사용자 자연어 질문
            request_id: 요청 추적 ID
            temperature: LLM 온도 (기본값 0, deterministic)
            schema_description: 미리 생성된 스키마 설명 (None이면 전체 로드)

        Returns:
            (sql, metadata) 튜플
            - sql: 생성된 SQL 문자열 (빈 문자열이면 실패)
            - metadata: {
                "db_type": str,
                "sql_dialect": str,
                "llm_model": str,
                "schema_length": int,
                "error": str (실패 시)
              }
        """
        metadata: Dict[str, Any] = {}

        try:
            # 1. 스키마 로드 (전달받은 스키마 우선 사용)
            if schema_description:
                # schema_retrieval_node에서 전달받은 스키마 사용
                log_step(request_id, "SQL-GEN", "0", "SCHEMA", "선택적 스키마 사용", schema_length=len(schema_description))
            else:
                # 전체 스키마 로드 (기존 동작)
                schema_description = self.get_schema_description()
            metadata["schema_length"] = len(schema_description)

            # 2. DB 타입 감지
            db_type = self.get_db_type()
            sql_dialect = self.get_sql_dialect()
            metadata["db_type"] = db_type
            metadata["sql_dialect"] = sql_dialect

            log_step(request_id, "SQL-GEN", "1", "INIT", f"SQL 생성 시작", db_type=db_type, sql_dialect=sql_dialect)

            # 3. 프롬프트 구성 (DB에서 동적 로드)
            prompt_service = _get_prompt_service()
            system_prompt = prompt_service.get_nl2sql_generation_prompt(schema_description, db_type)

            user_prompt = f"""질문: {question}

위 질문에 대한 {sql_dialect} SELECT 쿼리를 생성해주세요.
SQL만 출력하세요 (설명 없이)."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]

            # 4. LLM 호출
            LLMConfigManager = _get_llm_config_manager()
            settings_config = _get_settings_config()
            from app.config import settings

            llm = LLMConfigManager.create_llm(temperature=temperature)
            llm_model = settings_config.get_value("llm", "model", settings.llm_model)
            metadata["llm_model"] = llm_model

            # LLM 입력 로그
            log_step(request_id, "SQL-GEN", "2a", "LLM-INPUT", "LLM 호출 시작", model=llm_model, system_len=len(system_prompt), user_len=len(user_prompt))
            # DEBUG: 상세 로깅 (전문 출력)
            if logger.isEnabledFor(logging.DEBUG):
                llm_model_name = getattr(llm, 'model_name', getattr(llm, 'model', 'unknown'))
                llm_temp = getattr(llm, 'temperature', 'unknown')
                log_step(request_id, "SQL-GEN", "2a", "LLM-INFO", f"{type(llm).__name__}(model={llm_model_name}, temp={llm_temp})", level="DEBUG")
                log_step(request_id, "SQL-GEN", "2a", "LLM-INPUT", "SYSTEM_PROMPT", level="DEBUG", content=system_prompt)
                log_step(request_id, "SQL-GEN", "2a", "LLM-INPUT", "USER_PROMPT", level="DEBUG", content=user_prompt)

            # LLM 호출
            response = llm.invoke(messages)

            # LLM 출력 로그 (DEBUG 레벨, 전문 출력)
            if logger.isEnabledFor(logging.DEBUG):
                log_step(request_id, "SQL-GEN", "2b", "LLM-OUTPUT", "LLM_RESPONSE", level="DEBUG", content=response.content)

            # 5. 마크다운 제거
            sql = strip_markdown_code_block(response.content, language="sql")

            log_step(request_id, "SQL-GEN", "3", "COMPLETE", "SQL 생성 완료", sql_length=len(sql))
            if logger.isEnabledFor(logging.DEBUG):
                log_step(request_id, "SQL-GEN", "3", "SQL", "생성된 SQL", level="DEBUG", content=sql)

            return sql, metadata

        except Exception as e:
            log_step(request_id, "SQL-GEN", "ERR", "ERROR", f"SQL 생성 실패: {e}", level="ERROR")
            metadata["error"] = str(e)
            return "", metadata

    def refresh_schema_cache(self) -> str:
        """
        스키마 캐시 강제 갱신

        Returns:
            갱신된 스키마 설명
        """
        return self.get_schema_description(refresh=True)


# 싱글톤 인스턴스
sql_generator = SQLGeneratorService()

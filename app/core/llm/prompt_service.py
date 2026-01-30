"""프롬프트 관리 서비스

위치: app/core/llm/prompt_service.py
- DB에 저장된 프롬프트를 조회합니다.
- 캐싱은 settings_config에서 통합 관리합니다.
"""
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 순환 import 방지를 위해 지연 import
_settings_config = None


def _get_settings_config():
    global _settings_config
    if _settings_config is None:
        from app.core.config.settings_config import settings_config
        _settings_config = settings_config
    return _settings_config


class PromptService:
    """프롬프트 관리 서비스

    settings_config를 통해 프롬프트를 조회합니다.
    캐싱은 settings_config에서 통합 관리되므로 별도 캐시를 두지 않습니다.
    """

    def get_prompt(self, prompt_key: str, default: str = "") -> str:
        """프롬프트 조회

        Args:
            prompt_key: 프롬프트 키 (예: 'rag_system_prompt')
            default: 기본값 (DB에 없을 경우 반환)

        Returns:
            프롬프트 문자열
        """
        try:
            settings_config = _get_settings_config()
            value = settings_config.get_value('prompt', prompt_key, default)
            logger.debug(f"프롬프트 조회: {prompt_key}")
            return value
        except Exception as e:
            logger.error(f"프롬프트 조회 실패: {prompt_key}, {e}")
            return default

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
            Agent 기본 시스템 프롬프트 (ReAct 패턴, context_search_tool 포함)
        """
        default = """당신은 기업용 지식베이스와 데이터베이스 시스템을 위한 AI 어시스턴트입니다.

**사용 가능한 도구:**
1. context_search_tool: SQL 컨텍스트 검색 (스키마, 쿼리 예제, 용어집)
2. query_database_tool: 데이터베이스 조회 (실제 SQL 실행)
3. search_documents_tool: 문서 검색 (정책, 규정, 가이드라인)
4. calculate_tool: 수학 계산

**도구 선택 가이드:**
- 데이터/통계 질문 → context_search_tool로 스키마/예제 확인 후 query_database_tool 실행
- 정책/규정 질문 → search_documents_tool
- 계산 → calculate_tool

**실행 규칙:**
- 데이터 조회 전에 context_search_tool로 스키마와 쿼리 예제를 먼저 확인하세요
- SQL 예제만 보여주지 말고, 반드시 query_database_tool로 실행하여 결과를 얻으세요
- 복잡한 질문은 여러 도구를 순차적으로 사용할 수 있습니다
- 충분한 정보를 얻었으면 최종 답변을 작성하세요

**답변 작성 규칙:**
- 핵심 통계나 수치를 강조하세요 (예: **27명**, **5,400만원**)
- 결과를 명확하고 간결하게 설명하세요
- 필요시 불릿 포인트를 사용하세요
- 리스트 형태의 데이터는 표 또는 CSV 형식으로 보여주세요

**중요:**
- 도구 결과를 받으면 반드시 사용자에게 답변하세요
- 추측하지 말고 도구로 확인하세요
- 최종 답변은 한국어로 작성하세요"""

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

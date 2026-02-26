"""프롬프트 관리 서비스

위치: app/core/llm/prompt_service.py
- DB에 저장된 프롬프트를 조회합니다.
- 캐싱은 settings_config에서 통합 관리합니다.
"""
from datetime import date

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
제공된 문서를 기반으로 사용자의 질문에 정확하고 친절하게 답변해주세요.

**답변 원칙:**
1. 반드시 제공된 문서의 내용만을 기반으로 답변하세요.
2. 문서에 정보가 없으면 "제공된 문서에서 해당 정보를 찾을 수 없습니다"라고 명확히 안내하세요.

**답변 포맷팅 규칙:**
1. 답변 첫 줄에 핵심 요약을 1~2문장으로 작성하세요.
2. 내용이 여러 주제를 포함하면 **## 소제목**으로 구분하세요.
3. 절차나 단계가 있으면 **번호 목록(1. 2. 3.)**을 사용하세요.
4. 항목 나열은 **불릿 포인트(- )**를 사용하세요.
5. 비교 데이터나 항목별 정보는 **마크다운 표(| 헤더 | 헤더 |)**로 정리하세요.
6. 중요한 단어, 수치, 기간은 **굵게** 표시하세요.
7. 답변 마지막에 반드시 참고 문서를 표기하세요:
   **[참고 문서]** 《문서제목1》, 《문서제목2》"""

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

오늘 날짜: {current_date}
현재 연도: {current_year}

주의사항:
- LIMIT 대신 FETCH FIRST N ROWS ONLY 사용 (Oracle 12c+)
- 문자열 비교 시 대소문자 주의 (Oracle은 대소문자 구분)
- 날짜 형식: TO_DATE('YYYY-MM-DD', 'YYYY-MM-DD')
- NVL 함수 사용 (COALESCE 대신)
- 인원수/사람 수를 셀 때는 반드시 COUNT(DISTINCT EMP_ID)를 사용하세요 (V_AI_EMPLOYEE 등 뷰에 1인당 여러 행이 존재할 수 있음)

# 데이터베이스 스키마
{schema_description}"""
        else:
            default = """당신은 PostgreSQL 전문가입니다.
사용자의 자연어 질문을 PostgreSQL SQL 쿼리로 변환해주세요.

# 데이터베이스 스키마
{schema_description}"""

        template = self.get_prompt('nl2sql_generation_prompt', default)

        # 날짜 변수 + 스키마 정보 주입 (SafeDict로 누락 키 안전 처리)
        today = date.today()

        class _SafeDict(dict):
            def __missing__(self, key):
                return '{' + key + '}'

        variables = _SafeDict({
            "schema_description": schema_description,
            "current_date": today.strftime("%Y년 %m월 %d일"),
            "current_year": str(today.year),
        })
        return template.format_map(variables)

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

        Note:
            SQL 컨텍스트(스키마, Few-shot, 용어집)는 context_retrieval_node에서
            자동으로 System Prompt에 주입됩니다.
        """
        default = """당신은 기업용 지식베이스와 데이터베이스 시스템을 위한 AI 어시스턴트입니다.

**사용 가능한 도구:**
1. query_database_tool: 데이터베이스 조회 (SQL 실행)
2. search_documents_tool: 문서 검색 (정책, 규정, 가이드라인)
3. calculate_tool: 수학 계산

**도구 선택 가이드:**
- 데이터/통계 질문 → query_database_tool 실행
- 정책/규정 질문 → search_documents_tool
- 계산 → calculate_tool

**실행 규칙:**
- SQL 쿼리 작성 시 아래 "SQL 컨텍스트" 섹션의 스키마와 예제를 참고하세요
- SQL 예제만 보여주지 말고, 반드시 query_database_tool로 실행하여 결과를 얻으세요
- 복잡한 질문은 여러 도구를 순차적으로 사용할 수 있습니다
- 충분한 정보를 얻었으면 최종 답변을 작성하세요

**답변 작성 규칙:**
- 핵심 통계나 수치를 강조하세요 (예: **27명**, **5,400만원**)
- 결과를 명확하고 간결하게 설명하세요
- 필요시 불릿 포인트를 사용하세요
- 리스트 형태의 데이터는 표 또는 CSV 형식으로 보여주세요

**도구 결과 처리 규칙:**
- search_documents_tool 결과가 있으면 **문서의 핵심 내용을 직접 인용**하여 답변에 포함하세요
- query_database_tool 결과가 0행이면 "해당 조건의 데이터가 DB에 존재하지 않습니다"라고 명확히 안내하세요
- 여러 도구를 사용한 경우, **각 도구의 결과를 모두 종합**하여 답변하세요
- 도구에서 정보를 얻었다면 "확인되었습니다"만 쓰지 말고 **실제 내용을 보여주세요**

**중요:**
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

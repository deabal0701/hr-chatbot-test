"""프롬프트 카테고리를 app_settings 테이블에 추가하는 마이그레이션 스크립트

기존 하드코딩된 프롬프트를 DB로 이관합니다.
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.database.connection import db_manager
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 기본 프롬프트 정의 (기존 하드코딩된 값)
PROMPTS = [
    # RAG 프롬프트
    {
        'category': 'prompt',
        'key': 'rag_system_prompt',
        'value': """당신은 기업용 지식 베이스 전문가입니다.
제공된 문서를 기반으로 사용자의 질문에 정확하고 친절하게 답변해주세요.

답변 시 주의사항:
1. 반드시 제공된 문서의 내용만을 기반으로 답변하세요
2. 문서에 정보가 없으면 "제공된 문서에서 해당 정보를 찾을 수 없습니다"라고 명확히 안내하세요
3. 출처를 명시하세요 (예: "지식 베이스 문서에 따르면...")
4. 답변은 명확하고 구체적으로 작성하세요
5. 필요시 불릿 포인트나 번호를 사용하여 가독성을 높이세요""",
        'value_type': 'text',
        'description': 'RAG 답변 생성용 시스템 프롬프트 (문서 검색 후 답변 생성 시 사용)',
        'is_secret': False
    },
    {
        'category': 'prompt',
        'key': 'rag_persona',
        'value': '기업용 지식 베이스 전문가',
        'value_type': 'string',
        'description': 'RAG 시스템의 페르소나',
        'is_secret': False
    },

    # NL2SQL 프롬프트
    {
        'category': 'prompt',
        'key': 'nl2sql_generation_prompt',
        'value': """당신은 PostgreSQL 전문가입니다.
사용자의 자연어 질문을 PostgreSQL SQL 쿼리로 변환해주세요.

# 데이터베이스 스키마
{schema_description}

# 중요한 규칙
1. **반드시 SELECT 문만 생성하세요** (INSERT, UPDATE, DELETE, DROP 등은 절대 사용 금지)
2. **테이블명과 컬럼명은 정확하게 사용하세요**
3. **WHERE 절을 적절히 사용하여 결과를 필터링하세요**
4. **집계 함수 사용 시 GROUP BY를 정확히 지정하세요**
5. **날짜 비교 시 적절한 형변환을 사용하세요**
6. **JOIN 시 명확한 조인 조건을 지정하세요**
7. **SQL만 출력하고, 설명이나 마크다운 코드 블록은 포함하지 마세요**

# 사용자 의도 파악 규칙
- "표로 보여줘", "목록으로", "리스트로", "상세 정보" 등의 표현이 있으면 **개별 데이터를 조회**하세요 (COUNT 사용 금지)
- "몇 명", "총 수", "개수" 등의 표현이 있을 때만 COUNT를 사용하세요
- 이미 특정 수치("27명", "10건" 등)를 언급한 경우, 해당 데이터의 **상세 내용**을 원하는 것입니다 (COUNT 사용 금지)
- 불확실한 경우, 상세 데이터를 조회하는 것이 더 유용합니다

# LIMIT 사용 규칙 (조건부 적용)
- **COUNT, SUM, AVG, MAX, MIN 등 집계 함수 사용 시**: LIMIT 절 사용 금지
- **GROUP BY 사용 시**: LIMIT 절 사용 금지 (모든 그룹 결과 필요)
- **개별 데이터 조회 시**: LIMIT 1000 사용 (대용량 방지)
- 사용자가 "상위 5개만", "10개만 보여줘" 등 명시적으로 제한을 요청한 경우에만 해당 숫자를 LIMIT에 사용

# 필드 매핑 규칙 (데이터베이스 언어에 맞춤)
- 사용자 질문의 키워드를 스키마 정의에 정의된 실제 컬럼명과 정확히 매칭하세요.""",
        'value_type': 'text',
        'description': 'NL2SQL SQL 생성용 프롬프트 ({schema_description} 변수는 자동으로 DB 스키마로 치환됨)',
        'is_secret': False
    },
    {
        'category': 'prompt',
        'key': 'nl2sql_answer_prompt',
        'value': """당신은 데이터 분석 전문가입니다.
SQL 쿼리 결과를 사용자가 이해하기 쉽게 자연어로 요약해주세요.

답변 작성 시:
1. 핵심 통계나 수치를 강조하세요
2. 결과를 명확하고 간결하게 설명하세요
3. 필요시 불릿 포인트를 사용하세요
4. 데이터에서 발견되는 인사이트나 특징을 언급하세요""",
        'value_type': 'text',
        'description': 'NL2SQL 답변 생성용 프롬프트 (SQL 실행 결과를 자연어로 변환)',
        'is_secret': False
    },
    {
        'category': 'prompt',
        'key': 'nl2sql_sql_persona',
        'value': 'PostgreSQL 전문가',
        'value_type': 'string',
        'description': 'NL2SQL SQL 생성 시 페르소나',
        'is_secret': False
    },
    {
        'category': 'prompt',
        'key': 'nl2sql_answer_persona',
        'value': '데이터 분석 전문가',
        'value_type': 'string',
        'description': 'NL2SQL 답변 생성 시 페르소나',
        'is_secret': False
    },

    # Agent 프롬프트
    {
        'category': 'prompt',
        'key': 'agent_system_prompt',
        'value': """You are an AI assistant for corporate knowledge base and database systems with access to multiple tools.

**Available Tools:**
1. query_database: Query corporate database (for structured data like counts, statistics, records)
2. search_documents: Search corporate documents (for policies, regulations, guidelines, FAQs)
3. calculate: Perform mathematical calculations (for percentages, averages, etc.)

**Instructions:**
1. Think step by step before taking action
2. Use the most appropriate tool for each task
3. You can use multiple tools in sequence if needed
4. Always provide a final answer in Korean (한국어)
5. Be concise but comprehensive

**Thought Process (ReAct Pattern):**
- Thought: Analyze what information you need
- Action: Choose and use appropriate tool(s)
- Observation: Review tool results
- Repeat until you have enough information
- Final Answer: Provide comprehensive answer in Korean

**Tool Selection Guidelines:**
- Structured data/statistics → query_database
- Documents/policies/regulations → search_documents
- Calculations → calculate
- Complex queries → combine multiple tools

**Important:**
- Do NOT make assumptions without tool use
- Do NOT invent data
- If tools fail, explain what went wrong
- **CRITICAL: After using tools and getting results, you MUST provide a final answer in Korean**
- **Do NOT return empty responses - always synthesize tool results into a clear answer**""",
        'value_type': 'text',
        'description': 'Agent 시스템 프롬프트 (ReAct 패턴 기반 도구 선택 및 실행)',
        'is_secret': False
    },
    {
        'category': 'prompt',
        'key': 'agent_persona',
        'value': 'AI assistant for corporate knowledge base and database systems',
        'value_type': 'string',
        'description': 'Agent 페르소나',
        'is_secret': False
    },

    # Tool 설명
    {
        'category': 'prompt',
        'key': 'tool_sql_description',
        'value': """Query the database using natural language.

Use this tool when you need to:
- Get counts, statistics, aggregations from structured tables
- Find specific record information (e.g., "List records by criteria")
- Analyze trends and patterns
- Get category-wise or group-wise data
- Query structured data from various database tables

DO NOT use this tool for:
- Policy questions (use search_documents instead)
- Guidelines or regulations (use search_documents instead)
- Calculations only (use calculate instead)

Input: Natural language question about database data
Output: Query results with relevant information""",
        'value_type': 'text',
        'description': 'SQL Tool 설명 (Agent에서 도구 선택 시 참조)',
        'is_secret': False
    },
    {
        'category': 'prompt',
        'key': 'tool_rag_description',
        'value': """Search corporate documents and regulations.

Use this tool when you need to:
- Find company policies (e.g., "remote work policy", "travel policy")
- Look up company regulations and guidelines
- Access procedures and workflows
- Find FAQ or announcements
- Get information about benefits, compliance, training, etc.

DO NOT use this tool for:
- Data or statistics (use query_database instead)
- Calculations (use calculate instead)
- Real-time database queries (use query_database instead)

Input: Search query or question
Output: Relevant document excerpts and information""",
        'value_type': 'text',
        'description': 'RAG Tool 설명 (Agent에서 도구 선택 시 참조)',
        'is_secret': False
    },
    {
        'category': 'prompt',
        'key': 'tool_calculator_description',
        'value': """Perform mathematical calculations.

Use this tool when you need to:
- Calculate percentages, averages, sums (e.g., "what is 15% of 100?")
- Perform arithmetic operations (e.g., "(50+30)/2")
- Compare numeric values (e.g., "100 * 1.15")
- Statistical calculations (e.g., "average of [10, 20, 30]")

DO NOT use this tool for:
- Database queries (use query_database instead)
- Document searches (use search_documents instead)

Input: Mathematical expression or calculation request
Output: Numerical result with explanation""",
        'value_type': 'text',
        'description': 'Calculator Tool 설명 (Agent에서 도구 선택 시 참조)',
        'is_secret': False
    },
]


def migrate():
    """프롬프트 데이터를 app_settings 테이블에 추가"""
    try:
        with db_manager.get_cursor(commit=True) as cur:
            # 기존 prompt 카테고리 데이터 삭제 (재실행 가능하도록)
            cur.execute("DELETE FROM app_settings WHERE category = 'prompt'")
            logger.info("기존 prompt 카테고리 데이터 삭제 완료")

            # 새 프롬프트 데이터 삽입
            for prompt in PROMPTS:
                cur.execute("""
                    INSERT INTO app_settings (category, key, value, value_type, description, is_secret)
                    VALUES (%s, %s, %s, %s, %s, %s)
                """, (
                    prompt['category'],
                    prompt['key'],
                    prompt['value'],
                    prompt['value_type'],
                    prompt['description'],
                    prompt['is_secret']
                ))
                logger.info(f"✓ 프롬프트 추가: {prompt['key']}")

            logger.info(f"\n✅ 총 {len(PROMPTS)}개의 프롬프트가 성공적으로 추가되었습니다.")

            # 결과 확인
            cur.execute("SELECT key, description FROM app_settings WHERE category = 'prompt' ORDER BY key")
            results = cur.fetchall()

            print("\n📋 추가된 프롬프트 목록:")
            print("-" * 80)
            for key, desc in results:
                print(f"  • {key}: {desc}")
            print("-" * 80)

    except Exception as e:
        logger.error(f"❌ 마이그레이션 실패: {e}", exc_info=True)
        raise


def rollback():
    """마이그레이션 롤백 (prompt 카테고리 데이터 삭제)"""
    try:
        with db_manager.get_cursor(commit=True) as cur:
            cur.execute("DELETE FROM app_settings WHERE category = 'prompt'")
            logger.info("✅ prompt 카테고리 데이터가 삭제되었습니다.")
    except Exception as e:
        logger.error(f"❌ 롤백 실패: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='프롬프트 마이그레이션')
    parser.add_argument('--rollback', action='store_true', help='마이그레이션 롤백')
    args = parser.parse_args()

    if args.rollback:
        print("🔄 롤백 실행 중...")
        rollback()
    else:
        print("🚀 마이그레이션 실행 중...")
        migrate()

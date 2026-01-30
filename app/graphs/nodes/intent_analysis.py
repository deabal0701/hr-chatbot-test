"""
의도 분석 노드 (Intent Analysis Node)

기능:
- 질문 유형 분류 (SQL 질의 / 단순 질문 / 복합 질문)
- 쿼리 의도 분석 (select, aggregate, compare, trend, join 등)
- 모호성 감지 및 명확화 선택지 생성
- 신뢰도 점수 산출

사용:
- Agent 그래프의 진입점 노드로 사용
- 모호성 감지 시 human_clarification 노드로 분기 가능
"""

from typing import Dict, Any, Literal
import json
import re

from langchain_core.messages import SystemMessage, HumanMessage

from app.core.llm.llm_config import LLMConfigManager
from app.core.database.schema_loader import schema_loader
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)

# 스키마 캐시 (서버 시작 시 한 번만 로드)
_schema_cache: str = ""


# 의도 분석 결과 타입 정의
QUERY_TYPES = ["sql_query", "document_search", "hybrid", "calculation", "general"]
INTENT_TYPES = ["select", "aggregate", "compare", "trend", "join", "search", "calculate"]
AMBIGUITY_TYPES = ["period", "quantity", "criteria", "table", "column", "none"]


def intent_analysis_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    의도 분석 노드

    기존 agent 노드 전에 실행되어 질문을 분석합니다.
    모호성이 감지되면 human_clarification으로 분기합니다.

    Args:
        state: ExtendedAgentState (Dict 형태로 전달)

    Returns:
        업데이트된 state (intent_analysis 관련 필드 채움)
    """
    request_id = state.get("request_id", "unknown")
    question = state.get("question", "")

    log_step(request_id, "AGENT", "INTENT", "START", f"의도 분석 시작 | question={question[:50]}...")

    try:
        # LLM 호출하여 의도 분석
        result = _analyze_intent(question, request_id)

        # 상태 업데이트
        state["intent_analysis"] = result
        state["intent_confidence"] = result.get("confidence", 1.0)
        state["is_ambiguous"] = result.get("is_ambiguous", False)
        state["ambiguity_options"] = result.get("clarification_options", [])
        state["extracted_entities"] = result.get("extracted_entities", {})

        # 로깅
        if state["is_ambiguous"]:
            log_step(
                request_id, "AGENT", "INTENT", "AMBIGUOUS",
                f"모호성 감지 | type={result.get('ambiguity_type')}, confidence={state['intent_confidence']:.2f}, options={len(state['ambiguity_options'])}"
            )
        else:
            log_step(
                request_id, "AGENT", "INTENT", "COMPLETE",
                f"의도 분석 완료 | query_type={result.get('query_type')}, intent={result.get('intent')}, confidence={state['intent_confidence']:.2f}"
            )

        return state

    except Exception as e:
        log_step(request_id, "AGENT", "INTENT", "ERROR", f"의도 분석 실패: {e}", level="ERROR")

        # 실패 시 기본값으로 설정 (기존 플로우 계속 진행)
        state["intent_analysis"] = {"error": str(e)}
        state["intent_confidence"] = 1.0  # 실패 시 모호성 없음으로 처리
        state["is_ambiguous"] = False
        state["ambiguity_options"] = []
        state["extracted_entities"] = {}

        return state


def _get_schema_description() -> str:
    """
    스키마 설명 가져오기 (캐시 사용)

    Returns:
        DB 스키마 설명 문자열
    """
    global _schema_cache
    if not _schema_cache:
        try:
            _schema_cache = schema_loader.generate_schema_description()
            logger.debug(f"스키마 로드 완료: {len(_schema_cache)} chars")
        except Exception as e:
            logger.warning(f"스키마 로드 실패, 기본값 사용: {e}")
            _schema_cache = "스키마 정보를 로드할 수 없습니다."
    return _schema_cache


def _get_business_glossary() -> str:
    """
    비즈니스 용어집 반환

    Returns:
        비즈니스 용어 → SQL 조건 매핑 문자열
    """
    return """## 비즈니스 용어집 (SQL 조건 변환)

### 재직 상태 관련
- 재직자/현직자/현재 직원: WORK_STATUS = '재직' (v_ai_employee 테이블)
- 퇴직자/퇴사자: WORK_STATUS = '퇴직'
- 전체 직원: WORK_STATUS 조건 없이 조회

### 입사/퇴사 관련
- N년 입사자: TO_CHAR(HIRE_DATE, 'YYYY') = 'N' (재직 조건 불필요)
- N년 퇴사자: TO_CHAR(RETIRE_DATE, 'YYYY') = 'N' (재직 조건 불필요)
- 신입사원: 입사 1년 미만 (HIRE_DATE > SYSDATE - INTERVAL '1' YEAR)

### 경력/근속 관련
- 경력연수/근속연수: CAREER_YEARS 컬럼 (v_ai_employee)
- 경력개월수: CAREER_MONTHS 컬럼

### 조직 관련
- 부서별: DEPARTMENT 컬럼 또는 v_ai_employee 테이블
- 직위별: POSITION 컬럼 (사원, 대리, 과장, 차장, 부장 등)
- 직급별: GRADE 컬럼 (직위와 다름)

### 집계 키워드
- "몇 명", "수", "인원": COUNT(*) 집계
- "평균": AVG() 집계
- "합계", "총": SUM() 집계
- "목록", "명단", "리스트": 개별 데이터 조회 (COUNT 사용 금지)

### 1:N 관계 테이블 (EXISTS 패턴 사용)
- 학력: v_ai_education (학교명, 전공 등)
- 경력: v_ai_career (이전 회사, 근무 기간 등)
- 자격증: v_ai_license (자격증명, 발급기관 등)
- 어학: v_ai_language (TOEIC 점수 등)
- 주소: v_ai_address (거주 지역 등)
- 교육: v_ai_training (교육 과정 등)
- 가족: v_ai_family (가족 관계 등)
- 포상/징계: v_ai_reward
- 급여: v_ai_pay_report
- 평가: v_ai_feedback"""


def _analyze_intent(question: str, request_id: str) -> Dict[str, Any]:
    """
    LLM을 사용하여 의도 분석 수행

    Args:
        question: 분석할 질문
        request_id: 요청 ID (로깅용)

    Returns:
        의도 분석 결과 딕셔너리
    """
    llm = LLMConfigManager.create_llm(temperature=0)

    # 스키마 및 용어집 로드
    schema_desc = _get_schema_description()
    glossary = _get_business_glossary()

    system_prompt = f"""당신은 HR(인사) 시스템의 자연어 질문을 분석하는 전문가입니다.
사용자 질문을 분석하여 반드시 다음 JSON 형식으로만 응답하세요. 다른 텍스트 없이 JSON만 출력하세요.

{schema_desc}

{glossary}

## JSON 응답 형식
{{
    "query_type": "sql_query | document_search | hybrid | calculation | general",
    "intent": "select | aggregate | compare | trend | join | search | calculate",
    "confidence": 0.0~1.0,
    "is_ambiguous": true 또는 false,
    "ambiguity_type": "period | quantity | criteria | table | column | none",
    "ambiguity_reason": "모호한 이유 (모호하지 않으면 빈 문자열)",
    "clarification_options": ["선택지1", "선택지2", "선택지3"],
    "extracted_entities": {{
        "tables": ["테이블명"],
        "columns": ["컬럼명"],
        "conditions": [{{"column": "컬럼", "operator": "=", "value": "값"}}],
        "time_range": "기간",
        "aggregation": "집계 유형 (count, sum, avg 등)"
    }},
    "requires_document": false,
    "document_keywords": []
}}

## query_type 분류 기준
- sql_query: 데이터베이스 조회만 필요 (직원 수, 급여, 입사자 수 등 숫자/목록)
- document_search: 정책/규정 문서 검색만 필요 (재택근무 정책이 뭐야?, 휴가 규정 알려줘)
- hybrid: DB 조회 + 문서 검색 둘 다 필요 (예: "재택근무 정책을 준수하는 직원은?")
- calculation: 수학적 계산 (X의 Y% 등)
- general: 일반적인 질문, 인사말

## intent 분류 기준
- select: 단순 조회 (목록, 상세 정보)
- aggregate: 집계 (개수, 합계, 평균) - "몇 명", "총", "평균" 키워드
- compare: 비교 (A vs B, 증감)
- trend: 추세 (기간별 변화, 월별, 연도별)
- join: 여러 테이블 조인 필요 (부서별 직원 수 등)
- search: 문서 검색
- calculate: 계산

## 모호성 판단 기준 (is_ambiguous=true)
- period: 기간이 불명확 ("최근", "올해" 등 - 단, "2024년"처럼 명시되면 명확함)
- quantity: 수량 기준 불명확 ("많은", "상위", "일부" 등)
- criteria: 평가/필터 기준 불명확 ("좋은", "우수한" 등)
- table: 여러 테이블이 해당 가능
- column: 어떤 컬럼을 원하는지 불명확

## confidence 기준
- 0.9~1.0: 질문이 명확하고 해석이 분명함
- 0.7~0.9: 대체로 명확하지만 약간의 가정 필요
- 0.5~0.7: 모호한 부분이 있어 확인 필요 (is_ambiguous=true)
- 0.5 미만: 매우 모호하여 명확화 필수 (is_ambiguous=true)

## 예시

### 명확한 질문 (is_ambiguous: false)
질문: "2024년 입사자는 몇 명이야?"
→ query_type: "sql_query", intent: "aggregate", confidence: 0.95, is_ambiguous: false, ambiguity_type: "none"

질문: "재택근무 정책이 뭐야?"
→ query_type: "document_search", intent: "search", confidence: 0.95, is_ambiguous: false, ambiguity_type: "none"

질문: "재직자 중 경력연수 10년 이상인 사람은?"
→ query_type: "sql_query", intent: "aggregate", confidence: 0.9, is_ambiguous: false, ambiguity_type: "none"

### 모호한 질문 (is_ambiguous: true) - 반드시 모호성 감지!
질문: "최근 입사자는 몇 명이야?"
→ query_type: "sql_query", intent: "aggregate", confidence: 0.5, is_ambiguous: true, ambiguity_type: "period"
→ ambiguity_reason: "'최근'의 기간이 불명확 (1개월? 3개월? 6개월? 1년?)"
→ clarification_options: ["최근 1개월", "최근 3개월", "최근 6개월", "올해"]

질문: "경력 많은 직원 보여줘"
→ query_type: "sql_query", intent: "select", confidence: 0.5, is_ambiguous: true, ambiguity_type: "quantity"
→ ambiguity_reason: "'많은'의 기준이 불명확 (5년 이상? 10년 이상?)"
→ clarification_options: ["5년 이상", "10년 이상", "15년 이상", "상위 10%"]

질문: "우수한 직원 명단"
→ query_type: "sql_query", intent: "select", confidence: 0.4, is_ambiguous: true, ambiguity_type: "criteria"
→ ambiguity_reason: "'우수한'의 평가 기준이 불명확"
→ clarification_options: ["평가 등급 A 이상", "성과급 상위 10%", "포상 이력 있음"]
"""

    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=f"질문: {question}")
    ]

    log_step(request_id, "AGENT", "INTENT", "LLM", "의도 분석 LLM 호출", level="DEBUG")

    response = llm.invoke(messages)
    response_text = response.content if hasattr(response, 'content') else str(response)

    # response_text가 리스트인 경우 문자열로 변환
    if isinstance(response_text, list):
        response_text = str(response_text)

    log_step(request_id, "AGENT", "INTENT", "LLM", "LLM 응답 수신", level="DEBUG", response_length=len(response_text))

    # JSON 파싱
    result = _parse_json_response(response_text, request_id)

    return result


def _parse_json_response(response_text: str, request_id: str) -> Dict[str, Any]:
    """
    LLM 응답에서 JSON 파싱

    Args:
        response_text: LLM 응답 텍스트
        request_id: 요청 ID

    Returns:
        파싱된 딕셔너리
    """
    # 기본값
    default_result = {
        "query_type": "general",
        "intent": "select",
        "confidence": 1.0,
        "is_ambiguous": False,
        "ambiguity_type": "none",
        "ambiguity_reason": "",
        "clarification_options": [],
        "extracted_entities": {},
        "requires_document": False,
        "document_keywords": []
    }

    try:
        # JSON 블록 추출 (```json ... ``` 또는 순수 JSON)
        json_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', response_text)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 순수 JSON 시도
            json_str = response_text.strip()

        result = json.loads(json_str)

        # 필수 필드 검증 및 기본값 보완
        for key, default_value in default_result.items():
            if key not in result:
                result[key] = default_value

        # 타입 검증
        if result.get("query_type") not in QUERY_TYPES:
            result["query_type"] = "general"

        if result.get("intent") not in INTENT_TYPES:
            result["intent"] = "select"

        if result.get("ambiguity_type") not in AMBIGUITY_TYPES:
            result["ambiguity_type"] = "none"

        # confidence 범위 검증
        confidence = result.get("confidence", 1.0)
        result["confidence"] = max(0.0, min(1.0, float(confidence)))

        # is_ambiguous 타입 검증
        result["is_ambiguous"] = bool(result.get("is_ambiguous", False))

        return result

    except json.JSONDecodeError as e:
        log_step(request_id, "AGENT", "INTENT", "PARSE", f"JSON 파싱 실패: {e}", level="WARNING")
        return default_result
    except Exception as e:
        log_step(request_id, "AGENT", "INTENT", "PARSE", f"응답 처리 실패: {e}", level="WARNING")
        return default_result


def should_clarify(state: Dict[str, Any]) -> Literal["need_clarification", "proceed"]:
    """
    의도 분석 후 라우팅 결정

    모호성이 감지되고 신뢰도가 낮으면 human_clarification으로 분기

    Args:
        state: ExtendedAgentState

    Returns:
        "need_clarification": human_clarification 노드로 분기
        "proceed": 다음 노드 (context_retrieval 또는 agent)로 진행
    """
    is_ambiguous = state.get("is_ambiguous", False)
    confidence = state.get("intent_confidence", 1.0)

    # 모호하고 신뢰도가 0.7 미만이면 명확화 필요
    if is_ambiguous and confidence < 0.7:
        return "need_clarification"

    return "proceed"

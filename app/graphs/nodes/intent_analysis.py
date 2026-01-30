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
from app.utils.logger import setup_logger, log_step

logger = setup_logger(__name__)

# 의도 파악 컨텍스트 캐시 (서버 시작 시 한 번만 로드)
_intent_context_cache: str = ""


# 순환 import 방지를 위해 지연 import
_settings_config = None


def _get_settings_config():
    """settings_config 지연 로드"""
    global _settings_config
    if _settings_config is None:
        from app.core.config.settings_config import settings_config
        _settings_config = settings_config
    return _settings_config


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


def _get_intent_context() -> str:
    """
    의도 파악용 경량화된 컨텍스트 가져오기

    DB(tb_app_settings)에서 조회하고, 없으면 하드코딩된 기본값 사용.
    전체 스키마 대신 테이블 개요와 질문 유형 패턴만 제공.

    Returns:
        경량화된 컨텍스트 문자열
    """
    global _intent_context_cache
    if _intent_context_cache:
        return _intent_context_cache

    # 1. DB에서 조회 시도 (추후 tb_app_settings에 저장)
    try:
        settings_config = _get_settings_config()
        db_context = settings_config.get_value("agent", "intent_context", "")
        if db_context:
            _intent_context_cache = db_context
            logger.debug(f"의도 파악 컨텍스트 DB 로드 완료: {len(db_context)} chars")
            return _intent_context_cache
    except Exception as e:
        logger.debug(f"DB 조회 실패, 기본값 사용: {e}")

    # 2. 하드코딩된 경량 컨텍스트 (기본값)
    _intent_context_cache = _get_default_intent_context()
    logger.debug(f"의도 파악 컨텍스트 기본값 사용: {len(_intent_context_cache)} chars")
    return _intent_context_cache


def _get_default_intent_context() -> str:
    """
    하드코딩된 경량화된 의도 파악 컨텍스트

    Returns:
        기본 컨텍스트 문자열
    """
    return """## 데이터 소스 개요 (HR 인사 시스템)

### 주요 테이블
| 테이블명 | 설명 | 주요 조회 내용 |
|---------|------|--------------|
| v_ai_employee | 직원 마스터 | 입사일, 부서, 직위, 재직상태, 경력연수 |
| v_ai_address | 주소 정보 | 거주 지역 (서울, 경기, 경북 등) |
| v_ai_education | 학력 정보 | 학교명, 전공, 졸업연도 |
| v_ai_career | 경력 정보 | 이전 회사, 근무 기간 |
| v_ai_license | 자격증 | 자격증명, 발급기관, 취득일 |
| v_ai_language | 어학 | TOEIC 점수, 어학 등급 |
| v_ai_family | 가족 정보 | 가족 관계, 장애 여부 |
| v_ai_training | 교육 이력 | 교육 과정, 수료 여부 |
| v_ai_reward | 포상/징계 | 포상 종류, 포상금 |
| v_ai_feedback | 인사평가 | 평가 점수, 평가 등급 |
| v_ai_pay_report | 급여 | 급여액, 지급 내역 |
| v_ai_military | 병역 | 군종, 계급, 전역일 |

### 테이블 관계
- 모든 테이블은 EMP_ID로 v_ai_employee와 조인
- 1:N 관계: address, education, career, license, language, family, training, reward, feedback, pay_report
- 1:1 관계: military

## 질문 유형 패턴

### SQL 조회 (sql_query)
- "몇 명", "몇 건", "총 수" → 집계(aggregate) 의도
- "목록", "명단", "리스트", "보여줘" → 조회(select) 의도
- "부서별", "연도별", "직위별" → 그룹화(join) 의도
- "추이", "변화", "기간별" → 추세(trend) 의도
- "비교", "차이", "vs" → 비교(compare) 의도

### 문서 검색 (document_search)
- "정책", "규정", "지침", "가이드라인"
- "절차", "방법", "어떻게"
- "재택근무", "휴가", "복지"

### 복합 질문 (hybrid)
- "~정책을 따르는 직원 수" (문서 + SQL)
- "~규정에 해당하는 사람 명단"

### 계산 (calculation)
- "퍼센트", "비율", "계산"
- "X의 Y%"

## 모호성 키워드 (명확화 필요)

### 기간 모호 (period)
- "최근", "요즘", "얼마 전" → 1개월? 3개월? 6개월?
- "올해" → 현재 연도 (명확)
- "2024년" → 명확 (모호하지 않음)

### 수량 모호 (quantity)
- "많은", "적은", "일부" → 기준 불명확
- "상위", "하위" → 몇 %? 몇 명?

### 기준 모호 (criteria)
- "우수한", "좋은", "뛰어난" → 평가 기준 불명확
- "경력 있는" → 몇 년 이상?"""


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

    # 경량화된 의도 파악 컨텍스트 로드 (스키마 대신)
    intent_context = _get_intent_context()
    glossary = _get_business_glossary()

    system_prompt = f"""당신은 HR(인사) 시스템의 자연어 질문을 분석하는 전문가입니다.
사용자 질문을 분석하여 반드시 다음 JSON 형식으로만 응답하세요. 다른 텍스트 없이 JSON만 출력하세요.

{intent_context}

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

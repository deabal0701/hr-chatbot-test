"""테이블 카탈로그 서비스

위치: app/core/database/table_catalog.py

schema_retrieval_node에서 경량 LLM에게 제공할 테이블 요약 정보
- 출처: docs/NL2SQL 시스템 프롬프트.md
- 추후 DB 설정화 예정 (현재 하드코딩)

주요 기능:
- 테이블 카탈로그 조회 (이름 + 설명 + 컬럼)
- LLM용 테이블 요약 문자열 생성
- FK 관계 테이블 조회
"""
from typing import Dict, List, Any, Set

from app.utils.logger import setup_logger

logger = setup_logger(__name__)


# =============================================================================
# 테이블 카탈로그 (하드코딩)
# 출처: docs/NL2SQL 시스템 프롬프트.md
# =============================================================================

TABLE_CATALOG: Dict[str, Dict[str, Any]] = {
    "v_ai_employee": {
        "description": "직원 기본정보 (메인 테이블)",
        "columns": [
            "EMP_ID (PK, 조인키)",
            "EMP_NAME (이름)",
            "DEPARTMENT (부서)",
            "POSITION (직위: 사원,대리,과장,차장,부장)",
            "HIRE_DATE ★입사일 (입사자 집계: TO_CHAR(HIRE_DATE,'YYYY')='2024')",
            "RETIRE_DATE ★퇴직일 (퇴사자 집계)",
            "WORK_STATUS ★재직상태 (재직/퇴직)",
            "GRADE (직급/등급)",
            "EMP_TYPE (고용형태: 정규직,계약직)",
            "GENDER (성별)",
            "HIRE_TYPE (채용유형: 신입,경력)",
        ],
        "keywords": ["직원", "사원", "입사", "퇴사", "부서", "직급", "재직", "퇴직"],
        "is_primary": True,
        "join_key": "EMP_ID",
        "relation": "1 (메인)",
    },
    "v_ai_address": {
        "description": "직원 주소/거주지 정보",
        "columns": [
            "EMP_ID (FK)",
            "ADDRESS (기본주소)",
            "REGION ★거주 시/도 (서울,경기,부산 등)",
            "ZIP_CODE (우편번호)",
        ],
        "keywords": ["주소", "거주지", "서울", "경기", "지역", "시도"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    "v_ai_career": {
        "description": "이전 직장 경력 정보",
        "columns": [
            "EMP_ID (FK)",
            "PREV_COMPANY (전 직장명)",
            "PREV_POSITION (전 직장 직위)",
            "WORK_MONTHS (근무 개월수)",
            "WORK_YEARS (근무 연수)",
        ],
        "keywords": ["경력", "전직장", "이전회사", "근무경력"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    "v_ai_education": {
        "description": "학력 정보",
        "columns": [
            "EMP_ID (FK)",
            "SCHOOL_NAME (학교명)",
            "MAJOR (전공)",
            "DOUBLE_MAJOR (복수전공)",
            "GRADUATION_YEAR (졸업연도)",
        ],
        "keywords": ["학력", "학교", "대학", "전공", "졸업"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    "v_ai_family": {
        "description": "가족 관계 정보",
        "columns": [
            "EMP_ID (FK)",
            "RELATION (가족관계: 배우자,자녀,부모)",
            "FAMILY_NAME (가족 이름)",
            "FAMILY_GENDER (가족 성별)",
            "DISABILITY_STATUS (장애여부)",
        ],
        "keywords": ["가족", "배우자", "자녀", "부모", "부양"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    "v_ai_language": {
        "description": "어학 성적 정보 (TOEIC, TOEFL, JLPT 등)",
        "columns": [
            "EMP_ID (FK)",
            "LANGUAGE_TYPE (어학종류: 영어,일본어,중국어)",
            "EXAM_TYPE ★시험종류 (TOEIC,TOEFL,JLPT)",
            "SCORE ★시험점수",
            "LANGUAGE_GRADE (등급)",
            "EXAM_DATE (응시일)",
        ],
        "keywords": ["어학", "토익", "TOEIC", "토플", "JLPT", "영어", "점수"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    "v_ai_license": {
        "description": "자격증 정보",
        "columns": [
            "EMP_ID (FK)",
            "LICENSE_TYPE (자격구분: 국가자격,민간자격)",
            "LICENSE_NAME ★자격증명",
            "ISSUING_ORG (발급기관)",
            "ISSUE_DATE (취득일)",
            "VALIDITY_STATUS (유효상태: 유효,만료,영구)",
        ],
        "keywords": ["자격증", "자격", "면허", "취득", "보유"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    "v_ai_military": {
        "description": "병역 정보",
        "columns": [
            "EMP_ID (FK)",
            "MILITARY_TYPE (군종류: 육군,해군,공군)",
            "MILITARY_RANK (최종계급)",
            "SERVICE_STATUS (군필여부: 군필,미필,면제)",
            "DISCHARGE_DATE (전역일)",
        ],
        "keywords": ["병역", "군대", "군필", "전역", "군복무"],
        "join_key": "EMP_ID",
        "relation": "1:1",
        "related_tables": ["v_ai_employee"],
    },
    "v_ai_reward": {
        "description": "상벌 정보",
        "columns": [
            "EMP_ID (FK)",
            "REWARD_TYPE ★상벌구분 (포상,징계)",
            "REWARD_KIND (상벌종류)",
            "REWARD_REASON (사유)",
            "REWARD_DATE (일자)",
            "REWARD_AMOUNT (포상금액)",
        ],
        "keywords": ["상벌", "포상", "징계", "표창", "상금"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    "v_ai_training": {
        "description": "교육/훈련 이력",
        "columns": [
            "EMP_ID (FK)",
            "TRAINING_YEAR (교육연도)",
            "COURSE_NAME ★과정명",
            "INSTITUTION_NAME (교육기관)",
            "START_DATE (시작일)",
            "END_DATE (종료일)",
            "TRAINING_COST (교육비용)",
            "COMPLETION_STATUS (수료여부: 수료,미수료)",
        ],
        "keywords": ["교육", "훈련", "연수", "수료", "과정"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    "v_ai_feedback": {
        "description": "인사평가/직원평가 정보",
        "columns": [
            "EMP_ID (FK)",
            "APPR_NM ★평가명",
            "PEE_TYPE_NM (평가종류)",
            "EMP_ORG_NM (소속부서)",
            "APPR_SCORE ★평가점수",
            "APPR_GRADE ★평가등급 (A,B,C,D)",
            "PEE_OPINION (평가의견)",
            "APPR_YMD (평가일자)",
        ],
        "keywords": ["평가", "인사평가", "고과", "등급", "점수"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    "v_ai_pay_report": {
        "description": "급여 정보",
        "columns": [
            "EMPLOYEE_ID (FK, ★주의: EMP_ID 아님)",
            "EMPLOYEE_NAME (성명)",
            "PAY_YEAR (급여연도)",
            "PAY_YEAR_MONTH (급여년월)",
            "PAYMENT_TYPE_NAME (지급구분: 정기급여,상여)",
            "ORGANIZATION_NAME (소속)",
            "FIXED_PAY_AMOUNT (고정비)",
            "VARIABLE_PAY_AMOUNT (변동비)",
            "GROSS_PAY_AMOUNT ★지급합계",
            "DEDUCTION_AMOUNT (공제합계)",
            "NET_PAY_AMOUNT ★실지급액",
        ],
        "keywords": ["급여", "월급", "연봉", "지급", "실수령", "공제"],
        "join_key": "EMPLOYEE_ID",  # 주의: EMP_ID가 아님
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
}

# 테이블 관계 정보
TABLE_RELATIONS = {
    "1:N": [
        "v_ai_address", "v_ai_career", "v_ai_education", "v_ai_family",
        "v_ai_language", "v_ai_license", "v_ai_reward", "v_ai_training",
        "v_ai_feedback", "v_ai_pay_report"
    ],
    "1:1": ["v_ai_military"],
}


class TableCatalogService:
    """테이블 카탈로그 서비스

    schema_retrieval_node에서 사용하는 테이블 메타데이터 제공
    """

    def __init__(self):
        self._catalog = TABLE_CATALOG
        self._relations = TABLE_RELATIONS

    def get_catalog(self) -> Dict[str, Dict[str, Any]]:
        """전체 테이블 카탈로그 조회"""
        return self._catalog

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """특정 테이블 정보 조회"""
        return self._catalog.get(table_name.lower(), {})

    def get_all_table_names(self) -> List[str]:
        """전체 테이블 이름 목록"""
        return list(self._catalog.keys())

    def get_table_summary_for_llm(self) -> str:
        """
        schema_retrieval_node에서 경량 LLM에게 전달할 테이블 요약

        Returns:
            테이블 요약 문자열 (LLM 프롬프트용)
        """
        lines = ["## 테이블 목록 (질문에 필요한 테이블을 선택하세요)\n"]

        for name, info in self._catalog.items():
            lines.append(f"### {name}")
            lines.append(f"- 설명: {info['description']}")
            lines.append(f"- 관계: {info['relation']}")
            lines.append(f"- 주요 컬럼: {', '.join(info['columns'][:6])}...")  # 상위 6개만
            lines.append("")

        lines.append("## 조인 규칙")
        lines.append("- 모든 테이블은 EMP_ID로 v_ai_employee와 조인 (v_ai_pay_report만 EMPLOYEE_ID)")
        lines.append("- 1:N 관계 테이블과 직원 수 집계 시 EXISTS 사용 필수")

        return "\n".join(lines)

    def get_related_tables(self, tables: List[str]) -> Set[str]:
        """
        FK 관계 테이블 조회

        선택된 테이블에 연결된 관련 테이블을 자동으로 추가합니다.

        Args:
            tables: 선택된 테이블 목록

        Returns:
            관련 테이블이 포함된 테이블 집합
        """
        result = set(t.lower() for t in tables)

        for table in list(result):
            info = self._catalog.get(table, {})
            related = info.get("related_tables", [])
            for rel_table in related:
                result.add(rel_table.lower())

        # v_ai_employee는 메인 테이블이므로 항상 포함 (다른 테이블이 있을 경우)
        if result and "v_ai_employee" not in result:
            # v_ai_employee 외의 다른 테이블이 있으면 v_ai_employee 추가
            non_employee_tables = result - {"v_ai_employee"}
            if non_employee_tables:
                result.add("v_ai_employee")

        return result

    def is_1n_relation(self, table_name: str) -> bool:
        """테이블이 1:N 관계인지 확인"""
        return table_name.lower() in self._relations.get("1:N", [])

    def get_join_key(self, table_name: str) -> str:
        """테이블의 조인 키 조회"""
        info = self._catalog.get(table_name.lower(), {})
        return info.get("join_key", "EMP_ID")


# 싱글톤 인스턴스
table_catalog_service = TableCatalogService()

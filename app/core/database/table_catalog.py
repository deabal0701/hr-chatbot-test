"""테이블 카탈로그 서비스

위치: app/core/database/table_catalog.py

schema_retrieval_node에서 경량 LLM에게 제공할 테이블 요약 정보
- DB 설정(tb_app_settings)에서 로드, 없으면 기본값 폴백

주요 기능:
- 테이블 카탈로그 조회 (이름 + 설명 + 컬럼)
- LLM용 테이블 요약 문자열 생성
- FK 관계 테이블 조회
"""
import json
from typing import Dict, List, Any, Set

from app.utils.logger import setup_logger

logger = setup_logger(__name__)

# 순환 import 방지를 위해 지연 import
_settings_config = None


def _get_settings_config():
    """settings_config 지연 로딩"""
    global _settings_config
    if _settings_config is None:
        from app.core.config.settings_config import settings_config
        _settings_config = settings_config
    return _settings_config


# =============================================================================
# 기본 테이블 카탈로그 (DB에 설정이 없을 때 폴백용)
# =============================================================================

_DEFAULT_CATALOG: Dict[str, Dict[str, Any]] = {
    # ── 01. 메인 테이블 ──
    "v_ai_employee": {
        "description": "직원 기본정보 (메인 테이블, 모든 V_AI_* 뷰와 EMP_ID로 JOIN)",
        "columns": [
            "EMP_ID (PK, 조인키)",
            "EMP_NAME (이름)",
            "DEPARTMENT (부서)",
            "POSITION (직위: 회장,부사장,전무이사,상무이사,이사,부장,차장,과장,대리,주임,사원)",
            "DUTY (직책: 대표이사,사업부장,본부장,팀장,팀원 등)",
            "GRADE (직급: 1급~9급)",
            "EMP_TYPE (고용형태: 정규직,기간제)",
            "GENDER (성별: 남,여)",
            "BIRTH_DATE (생년월일)",
            "HIRE_TYPE (입사구분: 입사(신입), 입사(경력), 입사(기간제), 입사(재입사) 등)",
            "HIRE_DATE ★입사일 (입사자 집계: TO_CHAR(HIRE_DATE,'YYYY')=':YYYY')",
            "RETIRE_DATE ★퇴직일 (퇴사자 집계, 재직자는 NULL)",
            "WORK_STATUS ★재직상태 (재직/퇴직)",
            "CAREER_MONTHS (재직 개월수, HIRE_DATE 기반 자동계산)",
            "CAREER_YEARS ★재직 연수 (근속연수 질의 시 사용: CAREER_YEARS >= N)",
            "RETIRE_REASON (퇴직사유: 퇴직,정년,사망 등)",
        ],
        "keywords": ["직원", "사원", "입사", "퇴사", "부서", "직급", "재직", "퇴직", "근속", "재직연수", "성별", "직위", "직책"],
        "is_primary": True,
        "join_key": "EMP_ID",
        "relation": "1 (메인)",
    },
    # ── 02. 주소 (1:1, LEFT JOIN 필수) ──
    "v_ai_address": {
        "description": "직원 현재 거주지 정보 (현주소 + 현재 유효 기간만 필터, 주소 미등록 직원 미포함 → LEFT JOIN 필수)",
        "columns": [
            "EMP_ID (FK → V_AI_EMPLOYEE)",
            "REGION ★현재 거주 시/도 (서울,부산,대구,인천,광주,대전,울산,세종,경기,강원,충북,충남,전북,전남,경북,경남,제주,기타)",
            "ZIP_CODE (우편번호)",
        ],
        "keywords": ["주소", "거주지", "서울", "경기", "부산", "대구", "인천", "광주", "대전", "울산", "세종", "강원", "충북", "충남", "전북", "전남", "경북", "경남", "제주", "지역", "시도", "거주"],
        "join_key": "EMP_ID",
        "relation": "1:1",
        "related_tables": ["v_ai_employee"],
    },
    # ── 03. 경력 (1:N) ──
    "v_ai_career": {
        "description": "이전 직장 경력 정보 (1:N — 1인 다건, EMP_ID로 V_AI_EMPLOYEE와 JOIN)",
        "columns": [
            "EMP_ID (FK → V_AI_EMPLOYEE)",
            "PREV_COMPANY ★전 직장명",
            "PREV_POSITION (전 직장 직위)",
            "CAREER_START_DATE (전 직장 입사일)",
            "CAREER_END_DATE (전 직장 퇴사일)",
            "WORK_MONTHS (전 직장 근무 개월수, NULL 가능)",
            "WORK_YEARS (전 직장 근무 연수, NULL 가능)",
            "LEAVE_REASON (퇴직사유)",
        ],
        "keywords": ["경력", "전직장", "이전회사", "근무경력", "경력직", "이직", "전직", "퇴직사유", "출신회사", "경력사항"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    # ── 04. 학력 (1:N, LEFT JOIN 필수) ──
    "v_ai_scholar": {
        "description": "학력 정보 (1:N, 학력 미등록 직원 미포함 → V_AI_EMPLOYEE 기준 LEFT JOIN 필수)",
        "columns": [
            "EMP_ID (FK → V_AI_EMPLOYEE)",
            "EDUCATION_LEVEL ★학력수준 (고졸,전문대졸,대졸,석사,박사 등)",
            "GRADUATION_STATUS (졸업구분: 졸업,재학,중퇴 등)",
            "SCHOOL_NAME ★학교명",
            "MAJOR_NAME ★전공학과명 (LIKE '%경영%' 등으로 검색)",
            "DOUBLE_MAJOR_NAME (복수전공명)",
            "SUB_MAJOR_NM (부전공명)",
            "ADMISSION_DATE (입학년월, YYYYMM)",
            "GRADUATION_DATE (졸업년월, YYYYMM)",
            "SCHOOL_LOCATION_NAME (학교 소재지)",
        ],
        "keywords": ["학력", "학교", "대학", "전공", "졸업", "경영학", "공학", "이학", "학과", "학부", "출신학교", "석사", "박사", "대졸", "고졸", "학위", "학력수준", "부전공", "복수전공"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    # ── 05. 가족 (1:N, LEFT JOIN 필수) ──
    "v_ai_family": {
        "description": "사원 가족 구성원 정보 (1:N, 가족 미등록 직원 미포함 → V_AI_EMPLOYEE 기준 LEFT JOIN 필수)",
        "columns": [
            "EMP_ID (FK → V_AI_EMPLOYEE)",
            "RELATION ★가족관계 (배우자,자녀,부모,형제자매 등)",
            "FAMILY_NAME (가족 이름, PII)",
            "FAMILY_GENDER (가족 성별: 남,여)",
            "DISABILITY_STATUS (장애여부: 장애있음,장애없음)",
            "DISABILITY_GRADE (장애등급)",
        ],
        "keywords": ["가족", "배우자", "자녀", "부모", "부양", "가족수", "자녀수", "장애", "부양가족"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    # ── 06. 어학 (1:N) ──
    "v_ai_language": {
        "description": "어학 시험 성적 (1:N, TOEIC/TOEFL/JLPT 등)",
        "columns": [
            "EMP_ID (FK → V_AI_EMPLOYEE)",
            "LANGUAGE_TYPE (어학종류: 영어,일본어,중국어 등)",
            "EXAM_TYPE ★시험종류 (TOEIC,TOEFL,JLPT 등)",
            "SCORE ★시험점수",
            "EVAL_METHOD (평가유형: 점수,등급 — 어학 실력 비교는 SCORE 사용)",
            "EXAM_DATE (응시일)",
            "EXAM_YEAR (응시연도, YYYY)",
        ],
        "keywords": ["어학", "토익", "TOEIC", "토플", "JLPT", "영어", "점수", "어학성적"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    # ── 07. 자격증 (1:N) ──
    "v_ai_license": {
        "description": "자격증/면허 보유 현황 (1:N)",
        "columns": [
            "EMP_ID (FK → V_AI_EMPLOYEE)",
            "LICENSE_TYPE (자격구분: 국가자격,민간자격,사내자격 등)",
            "LICENSE_NAME ★자격증명",
            "ISSUING_ORG (발급기관)",
            "ISSUE_DATE (취득일)",
            "EXPIRY_DATE (만료일)",
            "VALIDITY_STATUS (유효상태: 유효,만료,영구)",
        ],
        "keywords": ["자격증", "자격", "면허", "취득", "보유", "국가자격"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    # ── 08. 병역 (1:1) ──
    "v_ai_military": {
        "description": "병역 정보 (1:1)",
        "columns": [
            "EMP_ID (FK → V_AI_EMPLOYEE)",
            "MILITARY_TYPE (군종류: 육군,해군,공군,해병대 등)",
            "MILITARY_RANK (최종계급: 병장,상병 등)",
            "SERVICE_STATUS (군필여부: 군필,미필,면제 등)",
            "DISCHARGE_TYPE (전역사유)",
            "ENLIST_DATE (입대일)",
            "DISCHARGE_DATE (전역일)",
            "DISCHARGE_YEAR (전역연도, YYYY)",
        ],
        "keywords": ["병역", "군대", "군필", "전역", "군복무", "입대"],
        "join_key": "EMP_ID",
        "relation": "1:1",
        "related_tables": ["v_ai_employee"],
    },
    # ── 09. 상벌 (1:N) ──
    "v_ai_reward": {
        "description": "상벌 내역 (1:N)",
        "columns": [
            "EMP_ID (FK → V_AI_EMPLOYEE)",
            "REWARD_TYPE ★상벌구분 (포상,징계)",
            "REWARD_KIND (상벌종류)",
            "REWARD_REASON (사유)",
            "REWARD_DATE (일자)",
            "REWARD_YEAR (발생연도, YYYY)",
            "REWARD_AMOUNT (포상금액)",
        ],
        "keywords": ["상벌", "포상", "징계", "표창", "상금", "상벌이력"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    # ── 10. 교육 (1:N) ──
    "v_ai_training": {
        "description": "교육/연수 이수 내역 (1:N)",
        "columns": [
            "EMP_ID (FK → V_AI_EMPLOYEE)",
            "TRAINING_YEAR (교육연도)",
            "COURSE_NAME ★교육과정명",
            "COURSE_FIELD (교육분야)",
            "TRAINING_TYPE (교육유형: 집합교육,사이버교육,필수교육,선택교육 등)",
            "INSTITUTION_NAME (교육기관)",
            "START_DATE (교육시작일)",
            "END_DATE (교육종료일)",
            "TRAINING_COST (교육비용, 원)",
            "COMPLETION_HOURS (총 이수 시간)",
            "COMPLETION_STATUS (수료여부: 수료,미수료)",
        ],
        "keywords": ["교육", "훈련", "연수", "수료", "과정", "이수", "교육비", "교육시간", "연수원", "필수교육", "선택교육"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    # ── 11. 인사평가 (1:N) ──
    "v_ai_feedback": {
        "description": "인사평가 결과 (1:N — 평가 횟수만큼 행 존재)",
        "columns": [
            "EMP_ID (FK → V_AI_EMPLOYEE)",
            "APPR_NM ★평가명 (인사평가,역량평가,종합평가,업적평가,다면평가 등)",
            "PEE_TYPE_NM (평가종류명)",
            "EMP_ORG_NM (평가 시점 소속부서명)",
            "APPR_SCORE ★평가점수 (숫자, 0 초과 시만 유효)",
            "APPR_GRADE ★평가등급 (S,A,B,C,D 등)",
            "RK (등급 내 순위)",
            "PEE_OPINION (평가자 의견)",
            "APPR_YMD ★평가일자 (DATE)",
            "END_YMD (평가종료일)",
        ],
        "keywords": ["평가", "인사평가", "고과", "등급", "점수", "S등급", "A등급", "평가결과", "인사고과", "역량평가", "업적평가", "종합평가", "다면평가"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    # ── 12. 인사발령 (1:N, 신규 등재) ──
    "v_ai_history": {
        "description": "인사발령 이력 (1:N — 발령 건수만큼 행 존재)",
        "columns": [
            "EMP_ID (FK → V_AI_EMPLOYEE)",
            "ASSIGNMENT_TYPE_CODE ★발령유형 (승진,전보,이동,휴직,복직,퇴직,파견 등)",
            "ASSIGNMENT_REASON_CODE (발령사유)",
            "ASSIGNMENT_DATE ★발령일자 (DATE)",
            "ASSIGNMENT_START_DATE (발령 시작일)",
            "ASSIGNMENT_END_DATE (발령 종료일)",
            "ASSIGNMENT_GRADE_CODE (발령 직급, 1급~9급)",
            "ASSIGNMENT_TITLE_NAME (발령 직책명, 팀장/팀원 등)",
            "LEAVE_OF_ABSENCE_YN ★휴직 여부 (Y/N)",
        ],
        "keywords": ["발령", "인사이동", "이동", "승진", "승격", "직급변경", "전출", "휴직", "복직", "부서이동", "인사발령", "발령이력", "조직개편", "파견", "겸직"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    # ── 13. 급여 (1:N) ──
    "v_ai_pay_report": {
        "description": "급여 지급 내역 (1:N — 급여월+지급구분별 행 존재). 금액 단위: 원",
        "columns": [
            "EMP_ID (FK → V_AI_EMPLOYEE)",
            "EMP_NAME (급여 시점 성명)",
            "PAY_YEAR ★급여연도 (YYYY)",
            "PAY_YEAR_MONTH ★급여년월 (YYYYMM)",
            "PAYMENT_TYPE_NAME ★지급구분 (정기급여,연차수당,격려금,상여 등)",
            "ORGANIZATION_NAME (소속부서명)",
            "FIXED_PAY_AMOUNT (고정비, 원)",
            "VARIABLE_PAY_AMOUNT (변동비, 원)",
            "GROSS_PAY_AMOUNT ★지급합계 (원, = 고정비 + 변동비)",
            "DEDUCTION_AMOUNT (공제합계, 원)",
            "TAX_AMOUNT (세금합계, 원)",
            "TOTAL_DEDUCTION_AMOUNT (총공제액, 원, = 공제 + 세금)",
            "NET_PAY_AMOUNT ★실지급액 (원, = 지급합계 - 총공제액)",
        ],
        "keywords": ["급여", "월급", "연봉", "지급", "실수령", "공제", "세금", "상여", "보너스", "급여명세", "고정비", "변동비", "급여구조", "인건비", "급여비용", "지급합계"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
    # ── 14. 연차 (1:N) ──
    "v_ai_dtm_yy_rest": {
        "description": "연차 발생/사용/잔여 관리 (1:N — 기준년도별 행 존재). 일수 단위: 일",
        "columns": [
            "EMP_ID (FK → V_AI_EMPLOYEE)",
            "REFERENCE_YEAR ★기준년도 (YYYY, 올해: TO_CHAR(SYSDATE,'YYYY'))",
            "LEAVE_TYPE_NAME (연차구분명)",
            "ACCRUED_LEAVE_DAYS ★발생연차일수",
            "ADDITIONAL_LEAVE_DAYS (추가연차일수)",
            "USED_LEAVE_DAYS_PAST ★사용연차일수",
            "TOTAL_LEAVE_DAYS ★총 년월차일수 (= 발생+추가+보상+보상2+퇴직연차)",
            "REMAINING_LEAVE_DAYS ★잔여연차일수 (= 총 년월차 - 사용)",
            "CARRIED_OVER_LEAVE_DAYS (이월연차, 차년추가연차)",
            "COMPENSATED_LEAVE_DAYS (보상연차일수)",
        ],
        "keywords": ["연차", "휴가", "발생연차", "사용연차", "잔여연차", "남은연차", "추가연차", "이월", "보상연차", "연차현황", "휴가일수"],
        "join_key": "EMP_ID",
        "relation": "1:N",
        "related_tables": ["v_ai_employee"],
    },
}

class TableCatalogService:
    """테이블 카탈로그 서비스

    schema_retrieval_node에서 사용하는 테이블 메타데이터 제공
    - DB 설정(tb_app_settings.nl2sql.table_catalog)에서 JSON으로 로드
    - DB에 없으면 _DEFAULT_CATALOG 폴백
    """

    def __init__(self):
        self._catalog: Dict[str, Dict[str, Any]] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        """카탈로그 로드 (DB → 기본값 폴백)"""
        if self._loaded:
            return

        try:
            sc = _get_settings_config()
            db_value = sc.get_value("nl2sql", "table_catalog", default=None)

            if db_value and isinstance(db_value, dict):
                self._catalog = db_value
                logger.info(f"[TABLE_CATALOG] DB 설정에서 로드 완료 | tables={len(db_value)}")
            elif db_value and isinstance(db_value, str):
                self._catalog = json.loads(db_value)
                logger.info(f"[TABLE_CATALOG] DB 설정(JSON 문자열)에서 로드 완료 | tables={len(self._catalog)}")
            else:
                self._catalog = _DEFAULT_CATALOG
                logger.info(f"[TABLE_CATALOG] DB 설정 없음 → 기본값 사용 | tables={len(self._catalog)}")
        except Exception as e:
            self._catalog = _DEFAULT_CATALOG
            logger.warning(f"[TABLE_CATALOG] DB 로드 실패 → 기본값 사용 | error={e}")

        self._loaded = True

    def refresh(self) -> None:
        """캐시 갱신 (Admin에서 수정 후 호출)"""
        self._loaded = False
        self._catalog = {}
        self._ensure_loaded()

    def get_catalog(self) -> Dict[str, Dict[str, Any]]:
        """전체 테이블 카탈로그 조회"""
        self._ensure_loaded()
        return self._catalog

    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """특정 테이블 정보 조회"""
        self._ensure_loaded()
        return self._catalog.get(table_name.lower(), {})

    def get_all_table_names(self) -> List[str]:
        """전체 테이블 이름 목록"""
        self._ensure_loaded()
        return list(self._catalog.keys())

    def get_table_summary_for_llm(self) -> str:
        """
        schema_retrieval_node에서 경량 LLM에게 전달할 테이블 요약

        Returns:
            테이블 요약 문자열 (LLM 프롬프트용)
        """
        self._ensure_loaded()
        lines = ["## 테이블 목록 (질문에 필요한 테이블을 선택하세요)\n"]

        for name, info in self._catalog.items():
            lines.append(f"### {name}")
            lines.append(f"- 설명: {info.get('description', name)}")
            lines.append(f"- 관계: {info.get('relation', 'N/A')}")
            lines.append(f"- 주요 컬럼: {', '.join(info.get('columns', []))}")
            keywords = info.get('keywords', [])
            if keywords:
                lines.append(f"- 키워드: {', '.join(keywords)}")
            lines.append("")

        lines.append("## 조인 규칙")
        lines.append("- 모든 테이블은 EMP_ID로 v_ai_employee와 조인")
        lines.append("- 1:N 관계 테이블과 직원 수 집계 시 EXISTS 사용 필수")

        return "\n".join(lines)

    def get_related_tables(self, tables: List[str]) -> Set[str]:
        """
        FK 관계 테이블 조회

        선택된 테이블에 연결된 관련 테이블을 자동으로 추가합니다.
        """
        self._ensure_loaded()
        result = set(t.lower() for t in tables)

        for table in list(result):
            info = self._catalog.get(table, {})
            related = info.get("related_tables", [])
            for rel_table in related:
                result.add(rel_table.lower())

        if result and "v_ai_employee" not in result:
            non_employee_tables = result - {"v_ai_employee"}
            if non_employee_tables:
                result.add("v_ai_employee")

        return result

    def get_join_key(self, table_name: str) -> str:
        """테이블의 조인 키 조회"""
        self._ensure_loaded()
        info = self._catalog.get(table_name.lower(), {})
        return info.get("join_key", "EMP_ID")


# 싱글톤 인스턴스
table_catalog_service = TableCatalogService()

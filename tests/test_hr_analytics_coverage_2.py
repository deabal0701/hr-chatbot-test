"""HR 분석 쿼리 커버리지 테스트 v2 (100개 질의, 난이도별 5단계)

위치: tests/test_hr_analytics_coverage_2.py

목적:
  - 14개 뷰 × 다양한 SQL 패턴 조합으로 100개 NL2SQL 질의 검증
  - 동일 session_id로 2회 실행하여 SQL 일관성 비교
  - 난이도별(★~★★★★★) SQL 생성률, 실행률, 일관성 통계
  - 결과를 docs/sql/fewshot/coverage2_report_YYYYMMDD.md + JSON 저장

실행:
  pytest tests/test_hr_analytics_coverage_2.py -v -s
  pytest tests/test_hr_analytics_coverage_2.py -v -s -k "test_hr"
"""
import json
import re
import time
import httpx
import pytest
from datetime import datetime
from pathlib import Path
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

# ─────────────────────────────────────────
# 상수
# ─────────────────────────────────────────
BASE_URL = "http://localhost:19090"
LONG_TIMEOUT = 90.0
SEARCH_PREFIX = "/api/v1/search"
ADMIN_ID = "admin"
ADMIN_PW = "Win1234!"

PASS_RATE_THRESHOLD = 0.55   # 100개 중 SQL 생성률 55% 이상이면 PASS
QUERY_DELAY = 0.0            # 쿼리 간 대기(초)
REPEAT_COUNT = 2             # 동일 질의 반복 횟수

REPORT_DIR = Path(__file__).parent.parent / "docs" / "sql" / "fewshot"

# ─────────────────────────────────────────
# 100개 HR 분석 질의 (난이도별 5단계)
# (id, category, difficulty, question, expected_tables, sql_keywords, purpose)
#
# difficulty: 1~5 (★ 수)
# expected_tables: 기대 사용 뷰 목록 (검증용)
# sql_keywords: SQL에 포함되어야 할 키워드 (검증용, 대소문자 무관)
# ─────────────────────────────────────────
HR_QUERIES_V2 = [
    # ═══════════════════════════════════════
    # ★ 난이도 1: 단일 테이블, 단순 집계/조건 (20건)
    # ═══════════════════════════════════════

    # v_ai_employee 기본 조회
    ("S01", "인력기본", 1, "현재 재직 중인 전체 직원 수는 몇 명이야?",
     ["v_ai_employee"], ["COUNT", "WORK_STATUS"],
     "단순 COUNT + 재직 조건"),
    ("S02", "인력기본", 1, "퇴직한 직원은 총 몇 명이야?",
     ["v_ai_employee"], ["COUNT", "RETIRE_DATE"],
     "퇴직자 COUNT (WORK_STATUS 조건 불필요)"),
    ("S03", "인력기본", 1, "남자 직원과 여자 직원 수를 각각 알려줘",
     ["v_ai_employee"], ["COUNT", "GENDER", "GROUP BY"],
     "성별 GROUP BY"),
    ("S04", "인력기본", 1, "2017년에 입사한 직원 수는?",
     ["v_ai_employee"], ["COUNT", "HIRE_DATE"],
     "연도 조건 COUNT"),
    ("S05", "인력기본", 1, "부서별 직원 수를 알려줘",
     ["v_ai_employee"], ["COUNT", "DEPARTMENT", "GROUP BY"],
     "부서 GROUP BY"),
    ("S06", "인력기본", 1, "직급별 재직자 수는?",
     ["v_ai_employee"], ["COUNT", "POSITION", "GROUP BY"],
     "직급 GROUP BY"),
    ("S07", "인력기본", 1, "정규직 직원은 몇 명이야?",
     ["v_ai_employee"], ["COUNT", "EMP_TYPE"],
     "고용유형 조건 COUNT"),
    ("S08", "인력기본", 1, "계약직 직원 명단을 보여줘",
     ["v_ai_employee"], ["EMP_TYPE"],
     "조건 필터 목록 (EMP_TYPE: 정규직,계약직 등)"),
    ("S09", "인력기본", 1, "2020년에 입사한 직원 이름과 부서를 알려줘",
     ["v_ai_employee"], ["HIRE_DATE", "EMP_NAME", "DEPARTMENT"],
     "연도 필터 + 컬럼 지정"),
    ("S10", "인력기본", 1, "경영지원부 재직자 수는?",
     ["v_ai_employee"], ["COUNT", "DEPARTMENT", "WORK_STATUS"],
     "특정 부서 COUNT"),

    # v_ai_employee 날짜/수치 조건
    ("S11", "인력기본", 1, "근속연수가 10년 이상인 직원 수는?",
     ["v_ai_employee"], ["COUNT", "CAREER_YEARS"],
     "수치 조건 COUNT"),
    ("S12", "인력기본", 1, "40대 직원은 몇 명이야?",
     ["v_ai_employee"], ["COUNT", "BIRTH_DATE"],
     "연령 조건 COUNT"),
    ("S13", "인력기본", 1, "직책별 재직자 수를 알려줘",
     ["v_ai_employee"], ["COUNT", "DUTY", "GROUP BY"],
     "직책 GROUP BY (DUTY=직책: 대표이사,팀장,팀원 등)"),
    ("S14", "인력기본", 1, "2018년에 퇴직한 직원 수는?",
     ["v_ai_employee"], ["COUNT", "RETIRE_DATE"],
     "퇴직연도 COUNT"),
    ("S15", "인력기본", 1, "경력사원으로 입사한 직원 수는?",
     ["v_ai_employee"], ["COUNT", "HIRE_TYPE"],
     "입사구분 COUNT (HIRE_TYPE: 신입,경력 등)"),

    # 다른 단일 뷰 단순 조회
    ("S16", "병역", 1, "군필자 수는 몇 명이야?",
     ["v_ai_military"], ["COUNT", "SERVICE_STATUS"],
     "병역 단순 COUNT"),
    ("S17", "포상", 1, "2017년 포상을 받은 직원 수는?",
     ["v_ai_reward"], ["COUNT", "REWARD_TYPE", "REWARD_YEAR"],
     "포상 조건 COUNT"),
    ("S18", "연차", 1, "2018년 기준 잔여연차가 0인 직원 수는?",
     ["v_ai_dtm_yy_rest"], ["COUNT", "REMAINING_LEAVE_DAYS", "REFERENCE_YEAR"],
     "연차 조건 COUNT"),
    ("S19", "교육", 1, "2017년 교육을 수료한 건수는?",
     ["v_ai_training"], ["COUNT", "COMPLETION_STATUS", "TRAINING_YEAR"],
     "교육 수료 COUNT"),
    ("S20", "평가", 1, "S등급을 받은 건수는 총 몇 건이야?",
     ["v_ai_feedback"], ["COUNT", "APPR_GRADE"],
     "평가등급 COUNT"),

    # ═══════════════════════════════════════
    # ★★ 난이도 2: 단일 테이블, GROUP BY/HAVING/CASE WHEN (15건)
    # ═══════════════════════════════════════

    ("S21", "인력현황", 2, "부서별 평균 근속연수를 알려줘",
     ["v_ai_employee"], ["AVG", "CAREER_YEARS", "GROUP BY", "DEPARTMENT"],
     "AVG + GROUP BY"),
    ("S22", "인력현황", 2, "연도별 입사자 수 추이를 보여줘",
     ["v_ai_employee"], ["COUNT", "HIRE_DATE", "GROUP BY"],
     "연도 추출 + GROUP BY"),
    ("S23", "인력현황", 2, "연도별 퇴사자 수 추이를 보여줘",
     ["v_ai_employee"], ["COUNT", "RETIRE_DATE", "GROUP BY"],
     "퇴직 연도 추출 GROUP BY"),
    ("S24", "인력현황", 2, "직급별 남녀 비율을 보여줘",
     ["v_ai_employee"], ["COUNT", "POSITION", "GENDER", "GROUP BY"],
     "2차원 GROUP BY"),
    ("S25", "인력현황", 2, "연령대별 직원 분포를 알려줘",
     ["v_ai_employee"], ["CASE", "BIRTH_DATE", "GROUP BY"],
     "CASE WHEN 연령 구간"),
    ("S26", "인력현황", 2, "근속연수 구간별 인원 분포를 보여줘",
     ["v_ai_employee"], ["CASE", "CAREER_YEARS", "GROUP BY"],
     "CASE WHEN 근속 구간"),
    ("S27", "인력현황", 2, "10명 이상인 부서만 보여줘",
     ["v_ai_employee"], ["COUNT", "HAVING"],
     "GROUP BY + HAVING"),
    ("S28", "인력현황", 2, "입사구분별 직원 수를 보여줘",
     ["v_ai_employee"], ["COUNT", "HIRE_TYPE", "GROUP BY"],
     "입사구분 GROUP BY"),
    ("S29", "인력현황", 2, "부서별 최근 입사자 입사일을 알려줘",
     ["v_ai_employee"], ["MAX", "HIRE_DATE", "GROUP BY"],
     "MAX + GROUP BY"),
    ("S30", "급여분석", 2, "지급유형별 총 지급액을 보여줘",
     ["v_ai_pay_report"], ["SUM", "PAYMENT_TYPE_NAME", "GROUP BY"],
     "급여 유형 SUM"),
    ("S31", "평가분석", 2, "평가등급별 인원 수를 보여줘",
     ["v_ai_feedback"], ["COUNT", "APPR_GRADE", "GROUP BY"],
     "평가등급 GROUP BY"),
    ("S32", "교육분석", 2, "교육 유형별 수료 건수를 알려줘",
     ["v_ai_training"], ["COUNT", "TRAINING_TYPE", "COMPLETION_STATUS", "GROUP BY"],
     "교육유형 GROUP BY + 조건"),
    ("S33", "인사이동", 2, "발령유형별 건수를 보여줘",
     ["v_ai_history"], ["COUNT", "ASSIGNMENT_TYPE_CODE", "GROUP BY"],
     "발령유형 GROUP BY"),
    ("S34", "연차분석", 2, "2018년 기준 직원별 잔여연차 상위 10명을 알려줘",
     ["v_ai_dtm_yy_rest"], ["REMAINING_LEAVE_DAYS", "REFERENCE_YEAR", "ORDER BY", "FETCH"],
     "TOP-N 조회"),
    ("S35", "포상", 2, "연도별 포상 건수 추이를 보여줘",
     ["v_ai_reward"], ["COUNT", "REWARD_YEAR", "GROUP BY"],
     "포상 연도 GROUP BY"),

    # ═══════════════════════════════════════
    # ★★★ 난이도 3: 2테이블 JOIN + 필터/집계 (30건)
    # ═══════════════════════════════════════

    # employee + address
    ("M01", "주소분석", 3, "서울 거주 재직자 수는 몇 명이야?",
     ["v_ai_employee", "v_ai_address"], ["JOIN", "REGION"],
     "JOIN + 지역 필터"),
    ("M02", "주소분석", 3, "지역별 재직자 분포를 알려줘",
     ["v_ai_employee", "v_ai_address"], ["LEFT JOIN", "GROUP BY", "NVL"],
     "LEFT JOIN + 전체 분포 (미등록 포함)"),

    # employee + career
    ("M03", "경력분석", 3, "이전 직장 경력이 있는 재직자 수는?",
     ["v_ai_employee", "v_ai_career"], ["EXISTS"],
     "EXISTS 서브쿼리"),
    ("M04", "경력분석", 3, "전직장 경력이 3건 이상인 직원 목록을 알려줘",
     ["v_ai_employee", "v_ai_career"], ["HAVING", "COUNT"],
     "GROUP BY + HAVING"),

    # employee + scholar
    ("M05", "학력분석", 3, "석사 이상 학력의 재직자 수는?",
     ["v_ai_employee", "v_ai_scholar"], ["EXISTS", "EDUCATION_LEVEL"],
     "학력 EXISTS"),
    ("M06", "학력분석", 3, "컴퓨터공학 전공자 명단을 보여줘",
     ["v_ai_employee", "v_ai_scholar"], ["MAJOR_NAME", "LIKE"],
     "전공 LIKE 검색"),

    # employee + family
    ("M07", "가족분석", 3, "배우자가 있는 재직자 수는?",
     ["v_ai_employee", "v_ai_family"], ["EXISTS", "RELATION"],
     "배우자 → LLM이 RELATION='처'로 매핑해야 함"),
    ("M08", "가족분석", 3, "자녀가 2명 이상인 직원 목록을 알려줘",
     ["v_ai_employee", "v_ai_family"], ["HAVING", "COUNT", "RELATION"],
     "자녀수 HAVING"),

    # employee + language
    ("M09", "어학분석", 3, "토익 800점 이상 재직자 수는?",
     ["v_ai_employee", "v_ai_language"], ["EXISTS", "EXAM_TYPE", "SCORE"],
     "어학 조건 EXISTS"),
    ("M10", "어학분석", 3, "시험종류별 평균 점수를 알려줘",
     ["v_ai_employee", "v_ai_language"], ["JOIN", "AVG", "EXAM_TYPE", "GROUP BY"],
     "JOIN + 평균 (재직자만)"),

    # employee + license
    ("M11", "자격증분석", 3, "자격증 보유 재직자 수는?",
     ["v_ai_employee", "v_ai_license"], ["EXISTS"],
     "자격증 보유 여부 EXISTS"),
    ("M12", "자격증분석", 3, "자격증 3개 이상 보유한 직원 목록을 알려줘",
     ["v_ai_employee", "v_ai_license"], ["HAVING", "COUNT"],
     "자격증 수 HAVING"),

    # employee + reward
    ("M13", "포상분석", 3, "포상을 받은 재직자 부서별 수는?",
     ["v_ai_employee", "v_ai_reward"], ["JOIN", "REWARD_TYPE", "GROUP BY"],
     "포상 JOIN + 부서 GROUP BY"),
    ("M14", "포상분석", 3, "징계를 받은 직원 명단을 알려줘",
     ["v_ai_employee", "v_ai_reward"], ["REWARD_TYPE"],
     "징계 조건 JOIN"),

    # employee + training
    ("M15", "교육분석", 3, "2017년 교육을 수료한 재직자 수는?",
     ["v_ai_employee", "v_ai_training"], ["JOIN", "COMPLETION_STATUS", "TRAINING_YEAR"],
     "교육수료 JOIN"),
    ("M16", "교육분석", 3, "부서별 1인당 평균 교육시간을 알려줘",
     ["v_ai_employee", "v_ai_training"], ["LEFT JOIN", "AVG", "GROUP BY"],
     "LEFT JOIN 분포 통계 (미이수 직원 포함)"),

    # employee + feedback
    ("M17", "평가분석", 3, "최근 평가에서 S등급을 받은 재직자 명단을 알려줘",
     ["v_ai_employee", "v_ai_feedback"], ["JOIN", "APPR_GRADE"],
     "평가등급 JOIN"),
    ("M18", "평가분석", 3, "부서별 평균 평가점수를 보여줘",
     ["v_ai_employee", "v_ai_feedback"], ["JOIN", "AVG", "APPR_SCORE", "GROUP BY"],
     "부서별 평가 평균"),

    # employee + history
    ("M19", "인사이동", 3, "최근 10년간 승진한 직원 수는?",
     ["v_ai_employee", "v_ai_history"], ["COUNT", "ASSIGNMENT_TYPE_CODE"],
     "승진 → LLM이 직급변경으로 매핑해야 함"),
    ("M20", "인사이동", 3, "현재 휴직 중인 직원 목록을 보여줘",
     ["v_ai_employee", "v_ai_history"], ["LEAVE_OF_ABSENCE_YN"],
     "휴직 상태 조회"),

    # employee + pay_report
    ("M21", "급여분석", 3, "부서별 월평균 실수령액을 보여줘",
     ["v_ai_employee", "v_ai_pay_report"], ["JOIN", "AVG", "NET_PAY_AMOUNT", "GROUP BY"],
     "급여 JOIN + 부서 AVG"),
    ("M22", "급여분석", 3, "직급별 평균 총지급액을 알려줘",
     ["v_ai_employee", "v_ai_pay_report"], ["JOIN", "AVG", "GROSS_PAY_AMOUNT", "GROUP BY"],
     "직급별 급여 AVG"),

    # employee + dtm_yy_rest
    ("M23", "연차분석", 3, "부서별 평균 연차 사용률을 알려줘",
     ["v_ai_employee", "v_ai_dtm_yy_rest"], ["JOIN", "AVG", "GROUP BY"],
     "연차 사용률 부서별"),
    ("M24", "연차분석", 3, "잔여연차가 10일 이상인 재직자 명단을 알려줘",
     ["v_ai_employee", "v_ai_dtm_yy_rest"], ["JOIN", "REMAINING_LEAVE_DAYS"],
     "잔여연차 조건"),

    # employee + military
    ("M25", "병역분석", 3, "병역유형별 재직자 수를 보여줘",
     ["v_ai_employee", "v_ai_military"], ["JOIN", "MILITARY_TYPE", "GROUP BY"],
     "병역유형 GROUP BY"),

    # 복합 조건 (2테이블이지만 조건이 여러 개)
    ("M26", "급여분석", 3, "상여금 지급 총액 부서별 비교를 해줘",
     ["v_ai_employee", "v_ai_pay_report"], ["JOIN", "SUM", "PAYMENT_TYPE_NAME", "GROUP BY"],
     "급여유형 필터 + 부서 SUM"),
    ("M27", "교육분석", 3, "교육 유형별 수료 건수 부서별 분포를 보여줘",
     ["v_ai_employee", "v_ai_training"], ["JOIN", "TRAINING_TYPE", "GROUP BY"],
     "교육유형(선택/필수) + 부서 GROUP BY"),
    ("M28", "평가분석", 3, "평가등급이 C 또는 D인 재직자 명단과 부서를 알려줘",
     ["v_ai_employee", "v_ai_feedback"], ["JOIN", "APPR_GRADE"],
     "평가 저성과 필터"),
    ("M29", "인사이동", 3, "부서별 인사이동 건수를 보여줘",
     ["v_ai_employee", "v_ai_history"], ["COUNT", "ASSIGNMENT_TYPE_CODE", "GROUP BY"],
     "인사이동 → LLM이 이동으로 매핑해야 함"),
    ("M30", "학력분석", 3, "부서별 학력 분포를 알려줘",
     ["v_ai_employee", "v_ai_scholar"], ["LEFT JOIN", "EDUCATION_LEVEL", "GROUP BY"],
     "LEFT JOIN 학력 분포 (미등록 포함)"),

    # ═══════════════════════════════════════
    # ★★★★ 난이도 4: 다중 테이블 JOIN + 복합 조건 (20건)
    # ═══════════════════════════════════════

    ("H01", "종합분석", 4, "서울 거주 토익 800점 이상 재직자 명단을 알려줘",
     ["v_ai_employee", "v_ai_address", "v_ai_language"], ["JOIN", "REGION", "SCORE"],
     "3테이블 다중 조건"),
    ("H02", "종합분석", 4, "석사 이상 학력이면서 자격증 보유한 재직자 수는?",
     ["v_ai_employee", "v_ai_scholar", "v_ai_license"], ["EXISTS"],
     "다중 EXISTS"),
    ("H03", "보상분석", 4, "평가등급별 평균 급여를 보여줘",
     ["v_ai_employee", "v_ai_feedback", "v_ai_pay_report"], ["JOIN", "AVG", "APPR_GRADE"],
     "평가+급여 3테이블 조인"),
    ("H04", "보상분석", 4, "동일 직급 내 남녀 평균 급여 차이를 보여줘",
     ["v_ai_employee", "v_ai_pay_report"], ["JOIN", "AVG", "GENDER", "POSITION", "GROUP BY"],
     "성별 급여 격차 2차원"),
    ("H05", "교육분석", 4, "교육 미이수 재직자 목록을 알려줘",
     ["v_ai_employee", "v_ai_training"], ["NOT EXISTS"],
     "NOT EXISTS 패턴"),
    ("H06", "인사이동", 4, "근속 10년 이상인데 승진 이력이 없는 재직자 목록을 알려줘",
     ["v_ai_employee", "v_ai_history"], ["CAREER_YEARS", "ASSIGNMENT_TYPE_CODE"],
     "승진 → LLM이 직급변경으로 매핑해야 함"),
    ("H07", "종합분석", 4, "부서별 평균 교육비용과 평균 평가점수를 비교해줘",
     ["v_ai_employee", "v_ai_training", "v_ai_feedback"], ["AVG", "GROUP BY"],
     "교육+평가 부서별 비교"),
    ("H08", "급여분석", 4, "직급별 평균 실수령액과 최대 최소 급여를 알려줘",
     ["v_ai_employee", "v_ai_pay_report"], ["AVG", "MAX", "MIN", "NET_PAY_AMOUNT", "POSITION"],
     "통계함수 복합 (AVG/MAX/MIN)"),
    ("H09", "인력현황", 4, "부서별 퇴직률을 계산해줘",
     ["v_ai_employee"], ["COUNT", "CASE", "RETIRE_DATE", "GROUP BY"],
     "퇴직률 비율 계산"),
    ("H10", "급여분석", 4, "고정비 대비 변동비 비율을 부서별로 분석해줘",
     ["v_ai_employee", "v_ai_pay_report"], ["SUM", "FIXED_PAY", "VARIABLE_PAY", "GROUP BY"],
     "급여 구조 비율"),
    ("H11", "종합분석", 4, "포상을 받은 직원의 평균 평가점수는?",
     ["v_ai_employee", "v_ai_reward", "v_ai_feedback"], ["JOIN", "AVG", "REWARD_TYPE"],
     "포상자 평가점수 3테이블"),
    ("H12", "인사이동", 4, "부서별 승진자 수와 승진률을 보여줘",
     ["v_ai_employee", "v_ai_history"], ["COUNT", "ASSIGNMENT_TYPE_CODE", "GROUP BY"],
     "승진 → LLM이 직급변경으로 매핑해야 함"),
    ("H13", "교육분석", 4, "부서별 1인당 교육비용을 보여줘",
     ["v_ai_employee", "v_ai_training"], ["LEFT JOIN", "SUM", "GROUP BY", "NVL"],
     "LEFT JOIN 교육비 분포"),
    ("H14", "연차분석", 4, "직급별 평균 연차 사용률을 보여줘",
     ["v_ai_employee", "v_ai_dtm_yy_rest"], ["JOIN", "AVG", "POSITION", "GROUP BY"],
     "직급별 연차 사용률"),
    ("H15", "평가분석", 4, "부서별 평가점수 표준편차를 계산해줘",
     ["v_ai_employee", "v_ai_feedback"], ["STDDEV", "GROUP BY"],
     "표준편차 분석"),
    ("H16", "급여분석", 4, "최근 10년간 연도별 급여 총지급액 추이를 보여줘",
     ["v_ai_pay_report"], ["SUM", "PAY_YEAR_MONTH", "GROUP BY", "ORDER BY"],
     "월별 추이"),
    ("H17", "인력현황", 4, "정규직과 기간제 비율 및 부서별 분포를 보여줘",
     ["v_ai_employee"], ["COUNT", "EMP_TYPE", "DEPARTMENT", "GROUP BY"],
     "고용유형 2차원 분포"),
    ("H18", "인사이동", 4, "휴직 유형별 현황을 알려줘",
     ["v_ai_employee", "v_ai_history"], ["COUNT", "ASSIGNMENT_REASON_CODE", "GROUP BY"],
     "휴직 유형 분석"),
    ("H19", "평가분석", 4, "평가등급이 C나 D인 직원의 근속연수 분포를 보여줘",
     ["v_ai_employee", "v_ai_feedback"], ["JOIN", "APPR_GRADE", "CAREER_YEARS", "CASE"],
     "저성과자 근속 분포"),
    ("H20", "급여분석", 4, "공제와 세금 비율을 직급별로 분석해줘",
     ["v_ai_employee", "v_ai_pay_report"], ["SUM", "DEDUCTION", "TAX", "POSITION"],
     "공제/세금 비율 분석"),

    # ═══════════════════════════════════════
    # ★★★★★ 난이도 5: 서브쿼리, 분석함수, 비율 계산, PIVOT (15건)
    # ═══════════════════════════════════════

    ("X01", "고급분석", 5, "부서별 최고 급여자 이름과 급여를 알려줘",
     ["v_ai_employee", "v_ai_pay_report"], ["ROW_NUMBER", "OVER"],
     "ROW_NUMBER 윈도우 함수"),
    ("X02", "고급분석", 5, "최근 10년간 S등급을 2회 이상 받은 직원 목록을 알려줘",
     ["v_ai_employee", "v_ai_feedback"], ["HAVING", "COUNT", "APPR_GRADE"],
     "HAVING + 등급 조건"),
    ("X03", "고급분석", 5, "최근 10년간 연도별 입사 퇴사 추이를 보여줘",
     ["v_ai_employee"], ["UNION", "HIRE_DATE", "RETIRE_DATE"],
     "UNION ALL 입사/퇴사 비교"),
    ("X04", "고급분석", 5, "승진 이력이 없는 근속 5년 이상 재직자 명단을 알려줘",
     ["v_ai_employee", "v_ai_history"], ["LEFT JOIN", "IS NULL"],
     "승진 → LLM이 직급변경으로 매핑해야 함"),
    ("X05", "고급분석", 5, "부서별 교육 수료율을 계산해줘",
     ["v_ai_employee", "v_ai_training"], ["LEFT JOIN", "COUNT", "CASE", "GROUP BY"],
     "수료율 비율 계산 + LEFT JOIN"),
    ("X06", "고급분석", 5, "직급별 평균 승진 소요연수를 알려줘",
     ["v_ai_employee", "v_ai_history"], ["AVG", "ASSIGNMENT_TYPE_CODE"],
     "승진 → LLM이 직급변경으로 매핑해야 함"),
    ("X07", "고급분석", 5, "부서별 여성 비율을 알려줘",
     ["v_ai_employee"], ["COUNT", "CASE", "GENDER", "GROUP BY"],
     "비율 계산 (CASE WHEN)"),
    ("X08", "고급분석", 5, "과장 이상 관리직의 여성 비율은?",
     ["v_ai_employee"], ["COUNT", "CASE", "GENDER", "POSITION"],
     "직급 조건 + 비율"),
    ("X09", "고급분석", 5, "입사 5년차 이내 직원 중 S등급을 받은 비율은?",
     ["v_ai_employee", "v_ai_feedback"], ["JOIN", "CAREER_YEARS", "APPR_GRADE"],
     "복합 조건 비율"),
    ("X10", "고급분석", 5, "부서별 평가등급 분포를 보여줘",
     ["v_ai_employee", "v_ai_feedback"], ["JOIN", "COUNT", "APPR_GRADE", "DEPARTMENT", "GROUP BY"],
     "2차원 분포 (부서×등급)"),
    ("X11", "고급분석", 5, "최근 입사자 5명의 이름 부서 직급을 알려줘",
     ["v_ai_employee"], ["ORDER BY", "HIRE_DATE", "FETCH"],
     "TOP-N FETCH FIRST"),
    ("X12", "고급분석", 5, "50대 이상 재직자의 부서별 분포를 알려줘",
     ["v_ai_employee"], ["BIRTH_DATE", "DEPARTMENT", "GROUP BY"],
     "연령 조건 + 부서 분포"),
    ("X13", "고급분석", 5, "부서별 자격증 보유율을 계산해줘",
     ["v_ai_employee", "v_ai_license"], ["LEFT JOIN", "COUNT", "GROUP BY"],
     "LEFT JOIN 보유율 계산"),
    ("X14", "고급분석", 5, "연도별 부서별 승진자 수 추이를 보여줘",
     ["v_ai_employee", "v_ai_history"], ["COUNT", "ASSIGNMENT_TYPE_CODE", "GROUP BY"],
     "승진 → LLM이 직급변경으로 매핑해야 함"),
    ("X15", "고급분석", 5, "장애인 가족이 있는 재직자의 부서별 분포를 알려줘",
     ["v_ai_employee", "v_ai_family"], ["JOIN", "DISABILITY_STATUS", "GROUP BY"],
     "가족 장애 조건 + 분포"),
]


# ─────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────
@pytest.fixture(scope="module")
def long_client():
    with httpx.Client(base_url=BASE_URL, timeout=LONG_TIMEOUT) as c:
        yield c


class _AutoRefreshHeaders(dict):
    """Access Token 만료 시 refresh token으로 자동 갱신하는 헤더 dict"""

    def __init__(self, client, login_id, password):
        super().__init__()
        self._client = client
        self._login_id = login_id
        self._password = password
        self._refresh_token = None
        self._login()

    def _login(self):
        resp = self._client.post("/api/v1/auth/login", json={
            "login_id": self._login_id, "password": self._password,
        })
        assert resp.status_code == 200, f"로그인 실패: {resp.text}"
        data = resp.json()["data"]
        self["Authorization"] = f"Bearer {data['access_token']}"
        self._refresh_token = data.get("refresh_token")
        self._token_time = time.time()

    def _refresh(self):
        if not self._refresh_token:
            self._login()
            return
        resp = self._client.post("/api/v1/auth/refresh", json={
            "refresh_token": self._refresh_token,
        })
        if resp.status_code == 200 and resp.json().get("success"):
            data = resp.json()["data"]
            self["Authorization"] = f"Bearer {data['access_token']}"
            if data.get("refresh_token"):
                self._refresh_token = data["refresh_token"]
            self._token_time = time.time()
        else:
            self._login()

    def ensure_valid(self):
        if time.time() - self._token_time > 1200:
            self._refresh()
            print("       [TOKEN] 자동 갱신 완료")


@pytest.fixture(scope="module")
def admin_headers(long_client):
    return _AutoRefreshHeaders(long_client, ADMIN_ID, ADMIN_PW)


# ─────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────
def _call_nl2sql(client: httpx.Client, headers, question: str, session_id: str) -> dict:
    """NL2SQL 호출 — session_id를 외부에서 받아 동일 세션으로 재실행 가능"""
    if hasattr(headers, "ensure_valid"):
        headers.ensure_valid()
    try:
        resp = client.post(
            SEARCH_PREFIX,
            headers=headers,
            json={"query": question, "mode": "nl2sql", "session_id": session_id},
        )
        http_ok = resp.status_code == 200
        body = resp.json() if http_ok else {}
        api_success = body.get("success", False)
        data = body.get("data", {}) if api_success else {}
        error_msg = body.get("error", {}).get("message", "") if not api_success else ""
    except Exception as exc:
        http_ok = False
        api_success = False
        data = {}
        error_msg = str(exc)

    sql = data.get("sql") or ""
    sql_result = data.get("sql_result") or {}
    answer = data.get("answer") or ""
    row_count = sql_result.get("row_count", -1) if sql_result else -1
    exec_ms = sql_result.get("execution_time_ms", -1) if sql_result else -1
    columns = sql_result.get("columns", []) if sql_result else []
    rows_data = sql_result.get("rows", []) if sql_result else []
    sample_rows = rows_data[:5] if rows_data else []

    return {
        "http_ok":      http_ok,
        "api_success":  api_success,
        "has_sql":      bool(sql),
        "sql_short":    sql[:120].replace("\n", " ") if sql else "",
        "sql_full":     sql,
        "has_result":   bool(sql_result) and row_count >= 0,
        "row_count":    row_count,
        "exec_ms":      exec_ms,
        "columns":      columns,
        "sample_rows":  sample_rows,
        "has_answer":   bool(answer.strip()),
        "answer_len":   len(answer),
        "answer":       answer,
        "error":        error_msg[:80] if error_msg else "",
    }


def _normalize_sql(sql: str) -> str:
    """SQL 비교용 정규화"""
    if not sql:
        return ""
    s = sql.upper().strip()
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'\s*,\s*', ', ', s)
    s = re.sub(r'\s*\(\s*', '(', s)
    s = re.sub(r'\s*\)\s*', ')', s)
    return s


def _check_sql_keywords(sql: str, keywords: list[str]) -> tuple[list[str], list[str]]:
    """SQL에 기대 키워드 포함 여부 체크 → (found, missing)"""
    sql_upper = sql.upper()
    found, missing = [], []
    for kw in keywords:
        if kw.upper() in sql_upper:
            found.append(kw)
        else:
            missing.append(kw)
    return found, missing


def _check_expected_tables(sql: str, expected_tables: list[str]) -> tuple[list[str], list[str]]:
    """SQL에 기대 테이블 사용 여부 체크 → (found, missing)"""
    sql_upper = sql.upper()
    found, missing = [], []
    for tbl in expected_tables:
        if tbl.upper() in sql_upper:
            found.append(tbl)
        else:
            missing.append(tbl)
    return found, missing


def _grade(r: dict) -> str:
    """결과 단계 판정"""
    if not r["http_ok"] or not r["api_success"]:
        return "FAIL-API"
    if not r["has_sql"]:
        return "FAIL-SQL"
    if not r["has_result"]:
        return "FAIL-EXEC"
    if r["row_count"] == 0:
        return "WARN-EMPTY"
    if not r["has_answer"]:
        return "WARN-NOANSWER"
    if not r.get("consistent", True):
        return "PASS-INCONSISTENT"
    return "PASS"


def _build_report(rows: list, repeat: int) -> str:
    """마크다운 보고서 생성 (난이도별 통계 포함)"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(rows)
    passed   = sum(1 for r in rows if r["grade"] == "PASS")
    incon    = sum(1 for r in rows if r["grade"] == "PASS-INCONSISTENT")
    fail_sql = sum(1 for r in rows if "FAIL-SQL" in r["grade"])
    fail_exec = sum(1 for r in rows if "FAIL-EXEC" in r["grade"])
    warn     = sum(1 for r in rows if "WARN" in r["grade"])
    fail_api = sum(1 for r in rows if "FAIL-API" in r["grade"])
    has_sql  = sum(1 for r in rows if r["has_sql"])

    lines = [
        f"# HR 분석 쿼리 커버리지 테스트 v2 보고서",
        f"",
        f"> 생성일시: {now}  ",
        f"> 반복횟수: {repeat}회 (동일 session_id)  ",
        f"> 총 질의수: {total}건",
        f"",
        f"## 전체 요약",
        f"",
        f"| 항목 | 건수 | 비율 |",
        f"|------|------|------|",
        f"| 전체 질의 | {total} | 100% |",
        f"| **PASS** | **{passed}** | **{passed/total:.0%}** |",
        f"| PASS-INCONSISTENT | {incon} | {incon/total:.0%} |",
        f"| FAIL-SQL | {fail_sql} | {fail_sql/total:.0%} |",
        f"| FAIL-EXEC | {fail_exec} | {fail_exec/total:.0%} |",
        f"| WARN | {warn} | {warn/total:.0%} |",
        f"| FAIL-API | {fail_api} | {fail_api/total:.0%} |",
        f"| SQL 생성률 | {has_sql}/{total} | {has_sql/total:.0%} |",
        f"",
    ]

    # 난이도별 통계
    lines += [f"## 난이도별 통계", f"",
              f"| 난이도 | 총건 | PASS | INCON | F-SQL | F-EXEC | WARN | F-API | SQL생성률 |",
              f"|--------|------|------|-------|-------|--------|------|-------|----------|"]
    for diff in range(1, 6):
        dr = [r for r in rows if r["difficulty"] == diff]
        if not dr:
            continue
        dt = len(dr)
        dp = sum(1 for r in dr if r["grade"] == "PASS")
        di = sum(1 for r in dr if r["grade"] == "PASS-INCONSISTENT")
        dfs = sum(1 for r in dr if "FAIL-SQL" in r["grade"])
        dfe = sum(1 for r in dr if "FAIL-EXEC" in r["grade"])
        dw = sum(1 for r in dr if "WARN" in r["grade"])
        dfa = sum(1 for r in dr if "FAIL-API" in r["grade"])
        dsql = sum(1 for r in dr if r["has_sql"])
        stars = "★" * diff
        lines.append(f"| {stars} | {dt} | {dp} | {di} | {dfs} | {dfe} | {dw} | {dfa} | {dsql}/{dt} ({dsql/dt:.0%}) |")

    # 카테고리별 통계
    lines += [f"", f"## 카테고리별 통계", f"",
              f"| 카테고리 | 총건 | PASS | SQL생성률 |",
              f"|----------|------|------|----------|"]
    cats = sorted(set(r["category"] for r in rows))
    for cat in cats:
        cr = [r for r in rows if r["category"] == cat]
        ct = len(cr)
        cp = sum(1 for r in cr if r["grade"] in ("PASS", "PASS-INCONSISTENT"))
        csql = sum(1 for r in cr if r["has_sql"])
        lines.append(f"| {cat} | {ct} | {cp} | {csql}/{ct} ({csql/ct:.0%}) |")

    # 상세 결과 테이블
    lines += [
        f"", f"## 상세 결과", f"",
        f"| ID | ★ | 카테고리 | 질의 | 판정 | rows | ms | 일관 | SQL키워드 | 오류 |",
        f"|----|---|---------|------|------|------|----|------|----------|------|",
    ]
    for r in rows:
        q_short = r["question"][:28] + ("…" if len(r["question"]) > 28 else "")
        con_mark = "O" if r.get("consistent", True) else "X"
        kw_mark = f"{r.get('kw_found', 0)}/{r.get('kw_total', 0)}"
        lines.append(
            f"| {r['id']} | {'★'*r['difficulty']} | {r['category']} | {q_short} "
            f"| `{r['grade']}` | {r['row_count']} | {r['exec_ms']} | {con_mark} | {kw_mark} | {r['error']} |"
        )

    # 판정 기준
    lines += [
        f"", f"## 판정 기준", f"",
        f"| 판정 | 의미 |",
        f"|------|------|",
        f"| `PASS` | SQL 생성 + 실행 성공 + 1행 이상 + 답변 생성 + 일관성 O |",
        f"| `PASS-INCONSISTENT` | PASS이나 2회 실행 SQL 불일치 |",
        f"| `WARN-EMPTY` | SQL 실행 성공이나 결과 0행 |",
        f"| `WARN-NOANSWER` | 결과는 있으나 답변 없음 |",
        f"| `FAIL-SQL` | SQL 미생성 |",
        f"| `FAIL-EXEC` | SQL 생성됐으나 실행 실패 |",
        f"| `FAIL-API` | HTTP/서버 오류 |",
    ]
    return "\n".join(lines)


def _save_report(content: str) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    fname = REPORT_DIR / f"coverage2_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    fname.write_text(content, encoding="utf-8")
    return fname


def _save_detail_json(rows: list) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    fname = REPORT_DIR / f"coverage2_detail_{datetime.now().strftime('%Y%m%d_%H%M')}.json"

    output = {
        "generated_at": datetime.now().isoformat(),
        "repeat_count": REPEAT_COUNT,
        "total": len(rows),
        "summary": {
            "PASS": sum(1 for r in rows if r["grade"] == "PASS"),
            "PASS_INCONSISTENT": sum(1 for r in rows if r["grade"] == "PASS-INCONSISTENT"),
            "WARN": sum(1 for r in rows if "WARN" in r["grade"]),
            "FAIL_SQL": sum(1 for r in rows if "FAIL-SQL" in r["grade"]),
            "FAIL_EXEC": sum(1 for r in rows if "FAIL-EXEC" in r["grade"]),
            "FAIL_API": sum(1 for r in rows if "FAIL-API" in r["grade"]),
        },
        "by_difficulty": {},
        "results": [],
    }

    # 난이도별 통계
    for diff in range(1, 6):
        dr = [r for r in rows if r["difficulty"] == diff]
        if dr:
            output["by_difficulty"][f"level_{diff}"] = {
                "total": len(dr),
                "pass": sum(1 for r in dr if r["grade"] == "PASS"),
                "sql_generated": sum(1 for r in dr if r["has_sql"]),
            }

    # 상세 결과
    for r in rows:
        output["results"].append({
            "id":                r["id"],
            "category":          r["category"],
            "difficulty":        r["difficulty"],
            "question":          r["question"],
            "purpose":           r["purpose"],
            "expected_tables":   r["expected_tables"],
            "sql_keywords":      r["sql_keywords"],
            "grade":             r["grade"],
            "session_id":        r["session_id"],
            "consistent":        r.get("consistent", True),
            "sql_consistent":    r.get("sql_consistent", True),
            "col_consistent":    r.get("col_consistent", True),
            "row_consistent":    r.get("row_consistent", True),
            "sql_runs":          r.get("sql_runs", []),
            "columns_runs":      r.get("columns_runs", []),
            "row_count_runs":    r.get("row_count_runs", []),
            "sample_runs":       r.get("sample_runs", []),
            "sql":               r["sql_full"],
            "columns":           r["columns"],
            "row_count":         r["row_count"],
            "sample_rows":       r["sample_rows"],
            "exec_ms":           r["exec_ms"],
            "answer":            r["answer"],
            "kw_found":          r.get("kw_found_list", []),
            "kw_missing":        r.get("kw_missing_list", []),
            "tbl_found":         r.get("tbl_found_list", []),
            "tbl_missing":       r.get("tbl_missing_list", []),
            "error":             r["error"],
        })

    fname.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    return fname


def _save_excel_report(rows: list) -> Path:
    """엑셀 보고서 생성 — 질의, SQL 1/2회차, 결과, 일관성 비교"""
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    fname = REPORT_DIR / f"coverage2_excel_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx"

    wb = Workbook()

    # ── Sheet 1: 요약 ──
    ws_summary = wb.active
    ws_summary.title = "요약"

    header_font = Font(bold=True, size=11)
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")
    header_font_white = Font(bold=True, size=11, color="FFFFFF")
    wrap_align = Alignment(wrap_text=True, vertical="top")
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )
    pass_fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
    incon_fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
    fail_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
    warn_fill = PatternFill(start_color="FFD966", end_color="FFD966", fill_type="solid")

    # 헤더
    headers = ["ID", "난이도", "카테고리", "질의", "판정", "일관성", "rows", "ms",
               "SQL #1", "SQL #2", "rows#1", "rows#2", "SQL키워드 매칭", "누락 키워드", "오류"]
    for col_idx, h in enumerate(headers, 1):
        cell = ws_summary.cell(row=1, column=col_idx, value=h)
        cell.font = header_font_white
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = thin_border

    # 데이터
    for row_idx, r in enumerate(rows, 2):
        sql_runs = r.get("sql_runs", [])
        row_count_runs = r.get("row_count_runs", [])

        values = [
            r["id"],
            "★" * r["difficulty"],
            r["category"],
            r["question"],
            r["grade"],
            "O" if r.get("consistent", True) else "X",
            r["row_count"],
            r["exec_ms"],
            sql_runs[0] if len(sql_runs) > 0 else "",
            sql_runs[1] if len(sql_runs) > 1 else "",
            row_count_runs[0] if len(row_count_runs) > 0 else "",
            row_count_runs[1] if len(row_count_runs) > 1 else "",
            f"{r.get('kw_found', 0)}/{r.get('kw_total', 0)}",
            ", ".join(r.get("kw_missing_list", [])),
            r.get("error", ""),
        ]
        for col_idx, val in enumerate(values, 1):
            cell = ws_summary.cell(row=row_idx, column=col_idx, value=val)
            cell.alignment = wrap_align
            cell.border = thin_border

        # 판정별 셀 색상
        grade_cell = ws_summary.cell(row=row_idx, column=5)
        grade = r["grade"]
        if grade == "PASS":
            grade_cell.fill = pass_fill
        elif "INCONSISTENT" in grade:
            grade_cell.fill = incon_fill
        elif "FAIL" in grade:
            grade_cell.fill = fail_fill
        elif "WARN" in grade:
            grade_cell.fill = warn_fill

        # 일관성 X 강조
        con_cell = ws_summary.cell(row=row_idx, column=6)
        if not r.get("consistent", True):
            con_cell.fill = incon_fill

    # 열 너비
    col_widths = [6, 8, 10, 40, 18, 6, 7, 7, 60, 60, 8, 8, 12, 20, 20]
    for col_idx, width in enumerate(col_widths, 1):
        ws_summary.column_dimensions[chr(64 + col_idx) if col_idx <= 26 else "A"].width = width
    # openpyxl 열 너비 (A~O)
    col_letters = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J", "K", "L", "M", "N", "O"]
    for letter, width in zip(col_letters, col_widths):
        ws_summary.column_dimensions[letter].width = width

    # 자동 필터
    ws_summary.auto_filter.ref = f"A1:O{len(rows) + 1}"
    # 첫 행 고정
    ws_summary.freeze_panes = "A2"

    # ── Sheet 2: 통계 ──
    ws_stats = wb.create_sheet("통계")
    ws_stats.cell(row=1, column=1, value="항목").font = header_font
    ws_stats.cell(row=1, column=2, value="건수").font = header_font
    ws_stats.cell(row=1, column=3, value="비율").font = header_font

    total = len(rows)
    stats = [
        ("전체", total),
        ("PASS", sum(1 for r in rows if r["grade"] == "PASS")),
        ("PASS-INCONSISTENT", sum(1 for r in rows if r["grade"] == "PASS-INCONSISTENT")),
        ("WARN-EMPTY", sum(1 for r in rows if "WARN" in r["grade"])),
        ("FAIL-SQL", sum(1 for r in rows if "FAIL-SQL" in r["grade"])),
        ("FAIL-EXEC", sum(1 for r in rows if "FAIL-EXEC" in r["grade"])),
        ("FAIL-API", sum(1 for r in rows if "FAIL-API" in r["grade"])),
        ("SQL 생성 성공", sum(1 for r in rows if r["has_sql"])),
    ]
    for i, (label, cnt) in enumerate(stats, 2):
        ws_stats.cell(row=i, column=1, value=label)
        ws_stats.cell(row=i, column=2, value=cnt)
        ws_stats.cell(row=i, column=3, value=f"{cnt/total:.0%}" if total > 0 else "0%")

    # 난이도별 통계
    ws_stats.cell(row=12, column=1, value="난이도별").font = header_font
    ws_stats.cell(row=12, column=2, value="총건").font = header_font
    ws_stats.cell(row=12, column=3, value="PASS").font = header_font
    ws_stats.cell(row=12, column=4, value="SQL생성률").font = header_font
    for diff in range(1, 6):
        dr = [r for r in rows if r["difficulty"] == diff]
        if dr:
            ri = 12 + diff
            ws_stats.cell(row=ri, column=1, value="★" * diff)
            ws_stats.cell(row=ri, column=2, value=len(dr))
            ws_stats.cell(row=ri, column=3, value=sum(1 for r in dr if r["grade"] in ("PASS", "PASS-INCONSISTENT")))
            ds = sum(1 for r in dr if r["has_sql"])
            ws_stats.cell(row=ri, column=4, value=f"{ds}/{len(dr)} ({ds/len(dr):.0%})")

    wb.save(fname)
    return fname


# ─────────────────────────────────────────
# 테스트
# ─────────────────────────────────────────
class TestHRAnalyticsCoverageV2:
    """HR 분석 쿼리 커버리지 검증 v2 (100개 질의, 동일 session_id 2회 실행)"""

    def test_hr_analytics_full_coverage_v2(self, long_client, admin_headers):
        """
        100개 HR 분석 질의를 난이도별로 실행.
        각 질의마다 고정 session_id로 2회 실행하여 일관성 비교.
        """
        rows = []
        repeat = max(REPEAT_COUNT, 1)
        total_queries = len(HR_QUERIES_V2)

        # SQL 비교 로그 파일 — 실행 중 실시간 쓰기
        REPORT_DIR.mkdir(parents=True, exist_ok=True)
        sql_log_file = REPORT_DIR / f"coverage2_sql_log_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        with open(sql_log_file, "w", encoding="utf-8") as f:
            f.write(f"# SQL 비교 로그 (실시간)\n\n")
            f.write(f"> 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"> 반복횟수: {repeat}회\n\n")

        print(f"\n{'='*100}")
        print(f"{'HR 분석 쿼리 커버리지 테스트 v2 (100건, 반복 ' + str(repeat) + '회)':^100}")
        print(f"{'='*100}")
        print(f"  SQL 비교 로그: {sql_log_file}")
        print(f"{'ID':<5} {'★':>2} {'카테고리':<10} {'질의(앞28자)':<30} {'판정':<18} {'rows':>5} {'ms':>6} {'일관':>4} {'SQL키워드':>10}")
        print(f"{'-'*100}")

        for idx, (query_id, category, difficulty, question, exp_tables, sql_kws, purpose) in enumerate(HR_QUERIES_V2):
            # 고정 session_id: 질의 ID 기반 (2회 실행 동일 세션)
            session_id = f"cov2-{query_id.lower()}"

            # 1회차 실행
            result1 = _call_nl2sql(long_client, admin_headers, question, session_id)

            # 2회차 이상 실행
            sql_runs = [result1["sql_full"]]
            col_runs = [result1["columns"]]
            row_runs = [result1["row_count"]]
            all_results = [result1]

            for _ in range(1, repeat):
                if QUERY_DELAY > 0:
                    time.sleep(QUERY_DELAY)
                result_n = _call_nl2sql(long_client, admin_headers, question, session_id)
                sql_runs.append(result_n["sql_full"])
                col_runs.append(result_n["columns"])
                row_runs.append(result_n["row_count"])
                all_results.append(result_n)

            # 일관성 판정
            normalized = [_normalize_sql(s) for s in sql_runs]
            sql_consistent = len(set(normalized)) <= 1
            col_consistent = all(c == col_runs[0] for c in col_runs)
            row_consistent = all(r == row_runs[0] for r in row_runs)
            consistent = sql_consistent and col_consistent

            result1["consistent"] = consistent
            grade = _grade(result1)

            # SQL 키워드/테이블 체크
            kw_found, kw_missing = _check_sql_keywords(result1["sql_full"], sql_kws) if result1["has_sql"] else ([], sql_kws)
            tbl_found, tbl_missing = _check_expected_tables(result1["sql_full"], exp_tables) if result1["has_sql"] else ([], exp_tables)

            sample_runs = [r["sample_rows"] for r in all_results]
            columns_runs = [r["columns"] for r in all_results]

            row = {
                "id":              query_id,
                "category":        category,
                "difficulty":      difficulty,
                "question":        question,
                "purpose":         purpose,
                "expected_tables": exp_tables,
                "sql_keywords":    sql_kws,
                "session_id":      session_id,
                "grade":           grade,
                "consistent":      consistent,
                "sql_consistent":  sql_consistent,
                "col_consistent":  col_consistent,
                "row_consistent":  row_consistent,
                "sql_runs":        sql_runs,
                "row_count_runs":  row_runs,
                "sample_runs":     sample_runs,
                "columns_runs":    columns_runs,
                "kw_found":        len(kw_found),
                "kw_total":        len(sql_kws),
                "kw_found_list":   kw_found,
                "kw_missing_list": kw_missing,
                "tbl_found_list":  tbl_found,
                "tbl_missing_list": tbl_missing,
                **result1,
            }
            rows.append(row)

            # 콘솔 출력
            q_short = question[:28] + ("…" if len(question) > 28 else "")
            con_mark = "O" if consistent else "X"
            kw_mark = f"{len(kw_found)}/{len(sql_kws)}"
            stars = "★" * difficulty
            print(f"{query_id:<5} {stars:>5} {category:<10} {q_short:<30} {grade:<18} {result1['row_count']:>5} {result1['exec_ms']:>6} {con_mark:>4} {kw_mark:>10}")

            if result1["error"]:
                print(f"       ⚠ {result1['error']}")
            if kw_missing and result1["has_sql"]:
                print(f"       ⚠ SQL 키워드 누락: {kw_missing}")
            if tbl_missing and result1["has_sql"]:
                print(f"       ⚠ 테이블 누락: {tbl_missing}")
            if not sql_consistent and repeat > 1:
                print(f"       ⚠ SQL 불일치!")

            # SQL 비교 로그 — 즉시 파일에 append (질의 + SQL만)
            with open(sql_log_file, "a", encoding="utf-8") as f:
                f.write(f"## {query_id} [{grade}] {'일치' if consistent else '**불일치**'}\n")
                f.write(f"**{question}**\n\n")
                for run_idx, run_sql in enumerate(sql_runs, 1):
                    f.write(f"**Run #{run_idx}**\n")
                    if run_sql:
                        f.write(f"```sql\n{run_sql}\n```\n\n")
                    else:
                        f.write(f"(SQL 없음)\n\n")
                f.write(f"---\n\n")

            if QUERY_DELAY > 0 and idx < total_queries - 1:
                time.sleep(QUERY_DELAY)

        # ── 보고서 생성 ──
        report = _build_report(rows, repeat)
        report_path = _save_report(report)
        detail_path = _save_detail_json(rows)
        excel_path = _save_excel_report(rows)

        # ── 최종 통계 출력 ──
        print(f"\n{'='*100}")
        total        = len(rows)
        passed       = sum(1 for r in rows if r["grade"] == "PASS")
        inconsistent = sum(1 for r in rows if r["grade"] == "PASS-INCONSISTENT")
        has_sql      = sum(1 for r in rows if r["has_sql"])
        warn         = sum(1 for r in rows if "WARN" in r["grade"])
        fail         = sum(1 for r in rows if "FAIL" in r["grade"])

        print(f"  총 {total}건 | PASS {passed} | INCONSISTENT {inconsistent} | WARN {warn} | FAIL {fail}")
        print(f"  SQL 생성률: {has_sql}/{total} ({has_sql/total:.0%})")

        if repeat > 1:
            con_count = sum(1 for r in rows if r["consistent"] and r["has_sql"])
            print(f"  SQL 일관성: {con_count}/{has_sql} ({con_count/max(has_sql,1):.0%})")

        # 난이도별 요약
        print(f"\n  [난이도별 SQL 생성률]")
        for diff in range(1, 6):
            dr = [r for r in rows if r["difficulty"] == diff]
            if dr:
                ds = sum(1 for r in dr if r["has_sql"])
                dp = sum(1 for r in dr if r["grade"] in ("PASS", "PASS-INCONSISTENT"))
                stars = "★" * diff
                print(f"    {stars:<6} {ds}/{len(dr)} ({ds/len(dr):.0%}) SQL생성, {dp}/{len(dr)} ({dp/len(dr):.0%}) PASS")

        # SQL 키워드 매칭 통계
        kw_queries = [r for r in rows if r["has_sql"]]
        if kw_queries:
            full_match = sum(1 for r in kw_queries if r["kw_found"] == r["kw_total"])
            print(f"\n  [SQL 키워드 매칭]")
            print(f"    전체 매칭: {full_match}/{len(kw_queries)} ({full_match/len(kw_queries):.0%})")

        print(f"\n  보고서: {report_path}")
        print(f"  상세 JSON: {detail_path}")
        print(f"  SQL 비교: {sql_log_file}")
        print(f"  엑셀: {excel_path}")
        print(f"{'='*100}")

        # FAIL 목록
        for fail_type in ("FAIL-API", "FAIL-SQL", "FAIL-EXEC"):
            fail_list = [r for r in rows if fail_type in r["grade"]]
            if fail_list:
                print(f"\n[{fail_type} 목록]")
                for r in fail_list:
                    print(f"  {r['id']} {'★'*r['difficulty']} {r['category']} | {r['question']} | {r['error']}")

        # 일관성 불일치 목록
        incon_rows = [r for r in rows if r["grade"] == "PASS-INCONSISTENT"]
        if incon_rows:
            print(f"\n[SQL 일관성 불일치 — session_id 확인 필요]")
            for r in incon_rows:
                print(f"  {r['id']} {r['category']} | session: {r['session_id']} | {r['question']}")

        # 키워드 누락 목록 (SQL 생성됐으나 기대 키워드 미포함)
        kw_miss_rows = [r for r in rows if r["has_sql"] and r.get("kw_missing_list")]
        if kw_miss_rows:
            print(f"\n[SQL 키워드 누락 목록 — SQL 품질 검토 필요]")
            for r in kw_miss_rows:
                print(f"  {r['id']} {r['category']} | 누락: {r['kw_missing_list']} | {r['question'][:40]}")

        # 통과 기준 검증
        non_api_fail = [r for r in rows if "FAIL-API" not in r["grade"]]
        effective_total = len(non_api_fail) if non_api_fail else total
        effective_sql = sum(1 for r in non_api_fail if r["has_sql"])
        sql_rate = effective_sql / effective_total if effective_total > 0 else 0

        if len(non_api_fail) < total:
            api_fail_count = total - len(non_api_fail)
            print(f"\n  [!] FAIL-API {api_fail_count}건 제외 후 SQL 생성률: {effective_sql}/{effective_total} ({sql_rate:.0%})")

        assert sql_rate >= PASS_RATE_THRESHOLD, (
            f"SQL 생성률 {sql_rate:.0%} < 기준 {PASS_RATE_THRESHOLD:.0%}\n"
            f"FAIL-SQL: {[r['id'] for r in rows if 'FAIL-SQL' in r['grade']]}\n"
            f"FAIL-EXEC: {[r['id'] for r in rows if 'FAIL-EXEC' in r['grade']]}\n"
            f"FAIL-API: {[r['id'] for r in rows if 'FAIL-API' in r['grade']]}"
        )

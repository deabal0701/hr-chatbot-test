# 기존 Few-shot 예제 AS-IS (tb_docs, doc_type=query_example)

> 조회 시점: 2026-03-17, 총 34건
> DB: hermesdb.tb_docs

---

## id=935: 연도별 입사자 수 조회

### content
```
2024년 입사자 수를 알려줘
올해 입사한 직원 몇 명
작년 신규 입사자 수
특정 연도 입사 인원
- 입사일(HIRE_DATE) 기준 연도별 집계
- 입사자 집계 시 재직 조건 불필요
- TO_CHAR로 연도 추출
```

### context_data
```
## SQL
```sql
SELECT COUNT(*) AS hire_count
FROM v_ai_employee
WHERE TO_CHAR(HIRE_DATE, 'YYYY') = ':년도'
```

## 핵심 패턴
- 연도 추출: TO_CHAR(HIRE_DATE, 'YYYY')
- 입사자 집계 시 WORK_STATUS 조건 불필요 (입사 시점 기준)
- HIRE_DATE 컬럼 사용 (NOT NULL)
```

---

## id=936: 연도별 퇴사자 수 조회

### content
```
2024년 퇴사자 수를 알려줘
올해 퇴직한 직원 몇 명
작년 퇴사 인원
특정 연도 퇴직자
- 퇴직일(RETIRE_DATE) 기준 연도별 집계
- 퇴사자 집계 시 재직 조건 불필요
- RETIRE_DATE IS NOT NULL 필수
```

### context_data
```
## SQL
```sql
SELECT COUNT(*) AS retire_count
FROM v_ai_employee
WHERE RETIRE_DATE IS NOT NULL
  AND TO_CHAR(RETIRE_DATE, 'YYYY') = '2024'
```

## 핵심 패턴
- 연도 추출: TO_CHAR(RETIRE_DATE, 'YYYY')
- RETIRE_DATE IS NOT NULL 조건 필수
- 퇴사자 집계 시 WORK_STATUS 조건 불필요
```

---

## id=937: 현재 재직자 수 조회

### content
```
현재 재직 중인 직원 수
전체 재직자 몇 명
현재 근무 중인 사원 수
회사 전체 인원
- 현재 재직 상태인 직원만 집계
- WORK_STATUS = 재직 조건 필수
- 특별한 언급 없으면 재직자만 대상
```

### context_data
```
## SQL
```sql
SELECT COUNT(*) AS active_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
```

## 핵심 패턴
- 재직자 기본 조건: WORK_STATUS = '재직'
- 특별한 언급이 없으면 재직자만 대상
- "퇴직자", "전체 직원" 등 명시적 언급 시에만 조건 변경
```

---

## id=938: 부서별 직원 수 조회

### content
```
부서별 직원 수를 알려줘
팀별 인원 현황
각 부서에 몇 명이 있어
조직별 재직자 수
부서 인원 분포
- 재직자만 대상
- DEPARTMENT 컬럼 기준 그룹화
- 인원 순 내림차순 정렬
```

### context_data
```
## SQL
```sql
SELECT DEPARTMENT, COUNT(*) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY DEPARTMENT
ORDER BY emp_count DESC
```

## 핵심 패턴
- 재직자 조건: WORK_STATUS = '재직'
- GROUP BY DEPARTMENT로 부서별 그룹화
- ORDER BY로 인원 순 정렬
```

---

## id=939: 직위별 직원 수 조회

### content
```
직위별 사원 수를 알려줘
직급별 직원 수 현황
사원 대리 과장 차장 부장 인원
직위 분포
- 재직자만 대상
- POSITION 컬럼 기준 그룹화
- 직위 순서대로 정렬 (사원→대리→과장→차장→부장)
```

### context_data
```
## SQL
```sql
SELECT POSITION, COUNT(*) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY POSITION
ORDER BY
    CASE POSITION
        WHEN '사원' THEN 1
        WHEN '대리' THEN 2
        WHEN '과장' THEN 3
        WHEN '차장' THEN 4
        WHEN '부장' THEN 5
        WHEN '이사' THEN 6
        WHEN '전무이사' THEN 7
        WHEN '사장' THEN 8
        WHEN '회장' THEN 9
        ELSE 10
    END
```

## 핵심 패턴
- 재직자 조건: WORK_STATUS = '재직'
- GROUP BY POSITION
- CASE WHEN으로 직위 순서 정렬
- 주의: GRADE(직급)와 POSITION(직위)은 다름
```

---

## id=940: 성별 직원 수 조회

### content
```
성별 직원 수를 알려줘
남녀 비율
남자 여자 직원 몇 명
성별 인원 현황
- 재직자만 대상
- GENDER 컬럼 기준 그룹화
- 비율 계산 포함 가능
```

### context_data
```
## SQL
```sql
SELECT
    GENDER,
    COUNT(*) AS emp_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS percentage
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY GENDER
ORDER BY GENDER
```

## 핵심 패턴
- GENDER 컬럼: 남, 여
- 비율 계산: 윈도우 함수 SUM() OVER()
- ROUND로 소수점 처리
```

---

## id=941: 고용형태별 직원 수 조회

### content
```
고용형태별 직원 수
정규직 계약직 인턴 몇 명
고용 유형별 인원
비정규직 현황
- 재직자만 대상
- EMP_TYPE 컬럼 기준 그룹화
- 정규직, 계약직, 인턴 등
```

### context_data
```
## SQL
```sql
SELECT EMP_TYPE, COUNT(*) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY EMP_TYPE
ORDER BY emp_count DESC
```

## 핵심 패턴
- EMP_TYPE 컬럼: 정규직, 계약직, 인턴 등
- 비정규직 조건: EMP_TYPE != '정규직'
```

---

## id=942: 채용유형별 직원 수 조회

### content
```
채용유형별 직원 수
신입 경력 입사자 현황
신입사원 몇 명
경력직 인원
- 재직자만 대상
- HIRE_TYPE 컬럼 기준 그룹화
- 신입, 경력, 입사(신입), 입사(경력) 등
```

### context_data
```
## SQL
```sql
SELECT HIRE_TYPE, COUNT(*) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
GROUP BY HIRE_TYPE
ORDER BY emp_count DESC
```

## 핵심 패턴
- HIRE_TYPE 컬럼: 신입, 경력, 입사(신입), 입사(경력) 등
- 신입: HIRE_TYPE LIKE '%신입%'
- 경력: HIRE_TYPE LIKE '%경력%'
```

---

## id=943: 연도별 입사 퇴사 추이 조회

### content
```
연도별 입사자 퇴사자 추이
2010년부터 2020년까지 입사 퇴사 현황
연도별 채용 이직 트렌드
기간별 인력 변동
- 입사와 퇴사 동시 집계
- UNION ALL로 데이터 통합
- 재직 조건 제외 (시점 기준)
```

### context_data
```
## SQL
```sql
SELECT
    year,
    SUM(hire_count) AS hire_count,
    SUM(retire_count) AS retire_count
FROM (
    SELECT TO_CHAR(HIRE_DATE, 'YYYY') AS year, 1 AS hire_count, 0 AS retire_count
    FROM v_ai_employee
    WHERE TO_CHAR(HIRE_DATE, 'YYYY') BETWEEN ':년도' AND ':년도'
    UNION ALL
    SELECT TO_CHAR(RETIRE_DATE, 'YYYY') AS year, 0 AS hire_count, 1 AS retire_count
    FROM v_ai_employee
    WHERE RETIRE_DATE IS NOT NULL
      AND TO_CHAR(RETIRE_DATE, 'YYYY') BETWEEN ':년도' AND ':년도'
)
GROUP BY year
ORDER BY year
```

## 핵심 패턴
- UNION ALL로 입사/퇴사 데이터 통합
- TO_CHAR(날짜, 'YYYY') BETWEEN으로 기간 조건
- 추이 분석 시 WORK_STATUS 조건 제외
```

---

## id=944: 지역별 거주 직원 수 조회

### content
```
서울에 사는 직원 몇 명
경기도 거주자 수
부산 지역 직원 현황
특정 시도 거주 재직자
지역별 인원
- 1:N 관계(v_ai_address) 조인 시 EXISTS 사용
- REGION 컬럼으로 지역 필터
- 중복 방지를 위해 JOIN 대신 EXISTS
```

### context_data
```
## SQL
```sql
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1 FROM v_ai_address a
    WHERE a.EMP_ID = e.EMP_ID
      AND a.REGION = '서울'
  )
```

## 핵심 패턴
- 1:N 관계 뷰 조건 시 EXISTS 서브쿼리 사용 (중복 방지)
- JOIN 대신 EXISTS 사용
- REGION 값: 서울, 경기, 경북, 경남, 전북, 전남, 충북, 충남, 강원, 제주 등
```

---

## id=945: 자격증 보유자 수 조회

### content
```
정보처리기사 자격증 보유자 수
특정 자격증 보유 직원 몇 명
자격증 있는 사원
국가자격 보유자
- 1:N 관계(v_ai_license) 조인 시 EXISTS 사용
- LICENSE_NAME으로 자격증명 검색
- LIKE로 부분 일치 검색
```

### context_data
```
## SQL
```sql
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1 FROM v_ai_license l
    WHERE l.EMP_ID = e.EMP_ID
      AND l.LICENSE_NAME LIKE '%정보처리기사%'
  )
```

## 핵심 패턴
- LIKE '%키워드%'로 자격증명 검색
- 1:N 관계 뷰에서 중복 방지를 위한 EXISTS
- LICENSE_TYPE: 국가자격, 민간자격, 사내자격
```

---

## id=946: 어학 점수 조건 직원 수 조회

### content
```
TOEIC 800점 이상인 직원 수
영어 점수 높은 사원
토익 점수 조건
어학 성적 우수자
- 1:N 관계(v_ai_language) 조인 시 EXISTS 사용
- EXAM_TYPE으로 시험 종류 필터
- SCORE로 점수 조건
```

### context_data
```
## SQL
```sql
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1 FROM v_ai_language l
    WHERE l.EMP_ID = e.EMP_ID
      AND l.EXAM_TYPE = 'TOEIC'
      AND l.SCORE >= 800
  )
```

## 핵심 패턴
- EXAM_TYPE: TOEIC, TOEFL, JLPT, BCT 등
- SCORE 컬럼으로 점수 조건
- LANGUAGE_TYPE: 영어, 일본어, 중국어 등
```

---

## id=947: 학력 조건 직원 수 조회

### content
```
서울대 출신 직원 몇 명
특정 학교 졸업자
컴퓨터공학 전공자 수
특정 전공 직원
- 1:N 관계(v_ai_scholar) 조인 시 EXISTS 사용
- SCHOOL_NAME으로 학교 검색
- MAJOR_NAME으로 전공 검색
```

### context_data
```
## SQL
```sql
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1 FROM v_ai_scholar ed
    WHERE ed.EMP_ID = e.EMP_ID
      AND ed.SCHOOL_NAME LIKE 'OO대학교%'
  )
```

## 핵심 패턴
- SCHOOL_NAME: 학교명 (LIKE 검색)
- MAJOR_NAME: 전공 학과명
- GRADUATION_DATE: 졸업 연도
```

---

## id=948: 가족 조건 직원 수 조회

### content
```
배우자가 있는 직원 수
기혼자 몇 명
자녀가 있는 사원
부양가족 있는 직원
- 1:N 관계(v_ai_family) 조인 시 EXISTS 사용
- RELATION으로 가족 관계 필터
- 배우자: 처, 남편, 배우자
```

### context_data
```
## SQL
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1 FROM v_ai_family f
    WHERE f.EMP_ID = e.EMP_ID
      AND f.RELATION IN ('배우자', '처', '남편')
  )
```

## 핵심 패턴
- RELATION: 배우자, 처, 남편, 자녀, 부, 모 등
- 자녀 조건: RELATION = '자녀'
- DISABILITY_STATUS: 장애있음, 장애없음
```

---

## id=949: 교육 이수 직원 수 조회

### content
```
특정 교육 이수자 수
2024년 교육 수료자
교육 과정 완료한 직원
연수 이수 현황
- 1:N 관계(v_ai_training) 조인 시 EXISTS 사용
- COMPLETION_STATUS로 수료 여부 확인
- TRAINING_YEAR로 연도 필터
```

### context_data
```
## SQL
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1 FROM v_ai_training t
    WHERE t.EMP_ID = e.EMP_ID
      AND t.TRAINING_YEAR = '2024'
      AND t.COMPLETION_STATUS = '수료'
  )
```

## 핵심 패턴
- TRAINING_YEAR: 교육 연도
- COMPLETION_STATUS: 수료, 미수료
- COURSE_NAME: 교육 과정명
```

---

## id=950: 포상 이력 직원 수 조회

### content
```
포상 받은 직원 수
우수사원 몇 명
상 받은 사람
징계 이력 있는 직원
- 1:N 관계(v_ai_reward) 조인 시 EXISTS 사용
- REWARD_TYPE으로 포상/징계 구분
- REWARD_KIND로 상 종류 확인
```

### context_data
```
## SQL
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1 FROM v_ai_reward r
    WHERE r.EMP_ID = e.EMP_ID
      AND r.REWARD_TYPE = '포상'
  )
```

## 핵심 패턴
- REWARD_TYPE: 포상, 징계
- REWARD_KIND: 우수상, 우수상-혁신 등
- REWARD_AMOUNT: 포상금 금액
```

---

## id=951: 이전 경력 조건 직원 수 조회

### content
```
경력직 출신 직원 수
이전 회사 경력 있는 사원
전직장 경험자
특정 회사 출신
- 1:N 관계(v_ai_career) 조인 시 EXISTS 사용
- PREV_COMPANY로 이전 회사 검색
- WORK_YEARS로 경력 연수 확인
```

### context_data
```
## SQL
```sql
SELECT COUNT(DISTINCT e.EMP_ID) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1 FROM v_ai_career c
    WHERE c.EMP_ID = e.EMP_ID
  )
```

## 핵심 패턴
- PREV_COMPANY: 이전 회사명
- WORK_YEARS: 해당 직장 근무 연수
- WORK_MONTHS: 해당 직장 근무 개월수
```

---

## id=952: 평가 등급 분포 조회

### content
```
2024년 평가 등급 분포
인사평가 등급별 인원
S A B C D 등급 분포
성과평가 결과 현황
- v_ai_feedback 테이블 사용
- APPR_GRADE로 등급 그룹화
- 연도는 END_YMD 기준
```

### context_data
```
## SQL
```sql
SELECT
    APPR_GRADE,
    COUNT(*) AS cnt,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER(), 1) AS percentage
FROM v_ai_feedback
WHERE TO_CHAR(END_YMD, 'YYYY') = ':년도'
GROUP BY APPR_GRADE
ORDER BY
    CASE APPR_GRADE
        WHEN 'S' THEN 1
        WHEN 'A' THEN 2
        WHEN 'B' THEN 3
        WHEN 'C' THEN 4
        WHEN 'D' THEN 5
    END
```

## 핵심 패턴
- v_ai_feedback 테이블: 인사평가/성과평가 정보
- APPR_GRADE: S, A, B, C, D 등급
- END_YMD: 평가 종료일 (연도 기준)
- APPR_SCORE: 평가 점수
```

---

## id=953: 평가 등급 별 인원수/직원수 조회 (S/A/B/C/D 등급 필터링)|

### content
```
제목 : 평가 등급 별 인원수/직원수 조회 (S/A/B/C/D 등급 필터링)|

OOO가 평가에서 S등급을 몇 번 받았나요?
OOO의  A등급 이상 평가 건수는?
S의 평가 등급 받은 직원이 몇 명인가요?
우수 평가(S, A등급)를 받은 인원수를 알려줘.
최우수 등급(S등급) 받은 사람 수는?
2026년에 S등급 받은 직원은 몇 명이야?
A등급 이상 우수자가 몇 명인지 조회해줘
특정 직원의 평가 등급별 건수를 보여줘
저성과(D등급) 평가 받은 직원 수는?
등급별 평가 인원 현황을 조회하고 싶어
OOO가 지금까지 받은 S등급 개수
우수 이상 등급 받은 횟수 알려줘
```

### context_data
```
SQL 예제:

-- 예제 1: 특정 직원의 S등급 평가 건수
SELECT COUNT(DISTINCT f.APPR_ID) AS s_grade_count
FROM v_ai_feedback f
JOIN v_ai_employee e ON f.EMP_ID = e.EMP_ID
WHERE e.EMP_NAME = ':직원명'
  AND e.WORK_STATUS = '재직'
  AND f.END_YMD <= SYSDATE
  AND f.APPR_GRADE = 'S'

-- 예제 2: 우수 이상(S, A등급) 평가 건수
SELECT COUNT(DISTINCT f.APPR_ID) AS excellent_count
FROM v_ai_feedback f
JOIN v_ai_employee e ON f.EMP_ID = e.EMP_ID
WHERE e.EMP_NAME = ':직원명'
  AND e.WORK_STATUS = '재직'
  AND f.END_YMD <= SYSDATE
  AND f.APPR_GRADE IN ('S', 'A')

-- 예제 3: 특정 년도 S등급 받은 직원 수
SELECT COUNT(DISTINCT e.EMP_ID) AS s_grade_employee_count
FROM v_ai_feedback f
JOIN v_ai_employee e ON f.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND TO_CHAR(f.END_YMD, 'YYYY') = ':년도'
  AND f.APPR_GRADE = 'S'

-- 예제 4: 등급별 인원 현황 (그룹핑)
SELECT f.APPR_GRADE, COUNT(DISTINCT e.EMP_ID) AS employee_count
FROM v_ai_feedback f
JOIN v_ai_employee e ON f.EMP_ID = e.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND f.END_YMD <= SYSDATE
GROUP BY f.APPR_GRADE
ORDER BY f.APPR_GRADE

핵심 패턴:
- 최우수: APPR_GRADE = 'S'
- 우수 이상: APPR_GRADE IN ('S', 'A')
- 보통 이상: APPR_GRADE IN ('S', 'A', 'B')
- 저성과: APPR_GRADE = 'D'
- 특정 년도: TO_CHAR(f.END_YMD, 'YYYY') = ':년도'
- 기간 범위: TO_CHAR(f.END_YMD, 'YYYY') BETWEEN ':시작년도' AND ':종료년도'
- 완료된 평가만: f.END_YMD <= SYSDATE
- 중복 제거 카운트: COUNT(DISTINCT APPR_ID) 또는 COUNT(DISTINCT EMP_ID)
- 날짜가 지금까지, 현재까지, 재직기간중 : END_YMD <= SYSDATE
```

---

## id=954: 부서별 평균 급여 조회

### content
```
부서별 평균 급여
팀별 연봉 현황
조직별 급여 통계
부서 평균 월급
- v_ai_pay_report 테이블 사용
- NET_PAY_AMOUNT: 실지급액
- 정기급여만 필터
```

### context_data
```
## SQL
```sql
SELECT
    ORGANIZATION_NAME,
    ROUND(AVG(NET_PAY_AMOUNT), 0) AS avg_pay,
    MIN(NET_PAY_AMOUNT) AS min_pay,
    MAX(NET_PAY_AMOUNT) AS max_pay,
    COUNT(DISTINCT EMPLOYEE_ID) AS emp_count
FROM v_ai_pay_report
WHERE PAY_YEAR = '2024'
  AND PAYMENT_TYPE_NAME = '정기급여'
GROUP BY ORGANIZATION_NAME
ORDER BY avg_pay DESC
```

## 핵심 패턴
- v_ai_pay_report 테이블: 급여 정보
- NET_PAY_AMOUNT: 실지급액
- PAYMENT_TYPE_NAME: 정기급여, 연차수당, 격려금, 상여
- 주의: EMPLOYEE_ID로 조인 (EMP_ID 아님)
```

---

## id=955: 특정 연월 급여 현황 조회

### content
```
2024년 1월 급여 현황
특정 월 급여 지급 내역
연월별 급여 조회
이번 달 급여 통계
- PAY_YEAR_MONTH로 연월 필터
- 급여 유형별 조회 가능
- 지급합계, 공제합계 확인
```

### context_data
```
## SQL
```sql
SELECT
    PAYMENT_TYPE_NAME,
    COUNT(DISTINCT EMPLOYEE_ID) AS emp_count,
    SUM(GROSS_PAY_AMOUNT) AS total_gross,
    SUM(NET_PAY_AMOUNT) AS total_net
FROM v_ai_pay_report
WHERE PAY_YEAR_MONTH = ':년월(YYYYMM)'
GROUP BY PAYMENT_TYPE_NAME
ORDER BY total_net DESC
```

## 핵심 패턴
- PAY_YEAR_MONTH: YYYYMM 형식
- GROSS_PAY_AMOUNT: 지급합계
- NET_PAY_AMOUNT: 실지급액
- DEDUCTION_AMOUNT: 공제합계
```

---

## id=956: 조건별 직원 명단 조회

### content
```
서울 거주 직원 명단
특정 조건 사원 목록
직원 리스트
명단 보여줘
- COUNT 대신 실제 데이터 조회
- 필요한 컬럼만 SELECT
- ORDER BY로 정렬
```

### context_data
```
## SQL
```sql
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1 FROM v_ai_address a
    WHERE a.EMP_ID = e.EMP_ID
      AND a.REGION = '서울'
  )
ORDER BY e.EMP_NAME
```

## 핵심 패턴
- 명단 조회: COUNT 대신 컬럼 SELECT
- 명단에도 EXISTS 또는 IN 사용 (중복 방지)
- ORDER BY로 이름순 정렬
```

---

## id=957: 개인 상세 정보 조회

### content
```
홍길동의 자격증 목록
특정 직원 학력 정보
개인 상세 데이터 조회
직원 정보 보여줘
- 상세 데이터 필요 시 JOIN 사용
- 특정 직원 조건
- 1:N 데이터 전체 조회
```

### context_data
```
## SQL
```sql
SELECT e.EMP_NAME, l.LICENSE_NAME, l.ISSUING_ORG, l.ISSUE_DATE
FROM v_ai_employee e
JOIN v_ai_license l ON e.EMP_ID = l.EMP_ID
WHERE e.EMP_NAME = '홍길동'
ORDER BY l.ISSUE_DATE DESC
```

## 핵심 패턴
- 상세 데이터 필요 시에만 JOIN 사용
- 집계가 아닌 개별 데이터 조회
- ORDER BY로 최신순 정렬
```

---

## id=958: 군종별 직원 수 조회

### content
```
육군 출신 직원 몇 명
군종별 인원 현황
해군 공군 육군 직원
병역 이행 현황
- v_ai_military 테이블 (1:1 관계)
- MILITARY_TYPE으로 군종 필터
- JOIN 사용 가능 (1:1 관계)
```

### context_data
```
## SQL
```sql
SELECT m.MILITARY_TYPE, COUNT(*) AS emp_count
FROM v_ai_employee e
JOIN v_ai_military m ON e.EMP_ID = m.EMP_ID
WHERE e.WORK_STATUS = '재직'
  AND m.MILITARY_TYPE IS NOT NULL
GROUP BY m.MILITARY_TYPE
ORDER BY emp_count DESC
```

## 핵심 패턴
- v_ai_military: 1:1 관계 (JOIN 가능)
- MILITARY_TYPE: 육군, 해군, 공군, 해병대, 의무경찰 등
- MILITARY_RANK: 병장, 상병 등 최종 계급
```

---

## id=959: 복합 조건 직원 수 조회

### content
```
서울 거주하면서 TOEIC 800점 이상인 직원
여러 조건 동시 만족
복합 조건 검색
다중 조건 직원 수
- 여러 EXISTS 조건 조합
- AND로 조건 연결
- 각 조건별 EXISTS 사용
```

### context_data
```
## SQL
```sql
SELECT COUNT(*) AS emp_count
FROM v_ai_employee e
WHERE e.WORK_STATUS = '재직'
  AND EXISTS (
    SELECT 1 FROM v_ai_address a
    WHERE a.EMP_ID = e.EMP_ID AND a.REGION = '서울'
  )
  AND EXISTS (
    SELECT 1 FROM v_ai_language l
    WHERE l.EMP_ID = e.EMP_ID
      AND l.EXAM_TYPE = 'TOEIC'
      AND l.SCORE >= 800
  )
```

## 핵심 패턴
- 여러 1:N 조건: 각각 EXISTS 사용
- AND로 조건 연결
- 모든 조건을 만족하는 직원만 집계
```

---

## id=960: 경력연수 조건 직원 수 조회

### content
```
경력 OO년 이상 직원 수
근속연수 O년 이상
장기 근속자
경력 많은 직원
- v_ai_employee의 CAREER_YEARS 사용
- 근속연수 = 현재 회사 경력
- 경력연수 = 총 경력
```

### context_data
```
## SQL
```sql
SELECT COUNT(*) AS emp_count
FROM v_ai_employee
WHERE WORK_STATUS = '재직'
  AND CAREER_YEARS >= ":경력년수"
```

## 핵심 패턴
- CAREER_YEARS: 총 경력 연수
- CAREER_MONTHS: 총 경력 개월수
- 근속연수: MONTHS_BETWEEN(SYSDATE, HIRE_DATE) / 12
```

---

## id=969: 입사자 현황 + 자격증 보유 개수 (요약 리스트)

### content
```
입사자 현황과 자격증 보유 사항을 알려줘
입사자별 자격증 개수
직원 목록과 보유 자격증 수
연도별 입사자와 자격증 현황
- 1:N 관계에서 1행/인 유지 필요
- 서브쿼리로 N테이블 COUNT
- 자격증 없는 사람도 0으로 표시
```

### context_data
```
## SQL
```sql
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION, e.HIRE_DATE,
       (SELECT COUNT(*) FROM v_ai_license l WHERE l.EMP_ID = e.EMP_ID) AS license_count
FROM v_ai_employee e
WHERE TO_CHAR(e.HIRE_DATE, 'YYYY') = ':년도'
  AND e.WORK_STATUS = '재직'
ORDER BY e.EMP_NAME
```

## 핵심 패턴
- **1:N 요약 리스트**: 서브쿼리로 COUNT하여 1행/인 유지
- 자격증 없는 사람도 license_count = 0으로 표시됨
- JOIN 사용 시 자격증 여러개면 행이 늘어나는 문제 방지
```

---

## id=970: 사원(직원) 현황 + 자격증 보유 개수 (요약 리스트)

### content
```
입사자(사원 또는 직원)의 현황과 자격증 보유 사항을 알려줘
입사자별 자격증 개수
직원 목록과 보유 자격증 수
연도별 입사자와 자격증 현황
- 1:N 관계에서 1행/인 유지 필요
- 서브쿼리로 N테이블 COUNT
- 자격증 없는 사람도 0으로 표시
```

### context_data
```
## SQL
```sql
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION, e.HIRE_DATE,
       (SELECT COUNT(*) FROM v_ai_license l WHERE l.EMP_ID = e.EMP_ID) AS license_count
FROM v_ai_employee e
WHERE TO_CHAR(e.HIRE_DATE, 'YYYY') = ':년도'
  AND e.WORK_STATUS = '재직'
ORDER BY e.EMP_NAME
```

## 핵심 패턴
- **1:N 요약 리스트**: 서브쿼리로 COUNT하여 1행/인 유지
- 자격증 없는 사람도 license_count = 0으로 표시됨
- JOIN 사용 시 자격증 여러개면 행이 늘어나는 문제 방지
```

---

## id=971: 사원(직원) 현황 + 자격증 보유 개수 (요약 리스트)

### content
```
입사자(사원 또는 직원)의 현황과 자격증 보유 사항을 알려줘
입사자별 자격증 개수
직원 목록과 보유 자격증 수
연도별 입사자와 자격증 현황
- 1:N 관계에서 1행/인 유지 필요
- 서브쿼리로 N테이블 COUNT
- 자격증 없는 사람도 0으로 표시
```

### context_data
```
## SQL
```sql
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION, e.HIRE_DATE,
       (SELECT COUNT(*) FROM v_ai_license l WHERE l.EMP_ID = e.EMP_ID) AS license_count
FROM v_ai_employee e
WHERE TO_CHAR(e.HIRE_DATE, 'YYYY') = ':년도'
  AND e.WORK_STATUS = '재직'
ORDER BY e.EMP_NAME
```

## 핵심 패턴
- **1:N 요약 리스트**: 서브쿼리로 COUNT하여 1행/인 유지
- 자격증 없는 사람도 license_count = 0으로 표시됨
- JOIN 사용 시 자격증 여러개면 행이 늘어나는 문제 방지
```

---

## id=972: 입사자 자격증 상세 목록 (상세 리스트)

### content
```
입사자들의 자격증 상세 정보
자격증 목록 전체 보여줘
어떤 자격증을 가지고 있는지 상세히
자격증 발급일, 발급기관 포함
- 자격증별로 행 표시 (1인 여러 행 가능)
- LEFT JOIN으로 자격증 없는 사람도 포함
```

### context_data
```
## SQL
```sql
SELECT e.EMP_NAME, e.DEPARTMENT,
       l.LICENSE_NAME, l.ISSUING_ORG, l.ISSUE_DATE
FROM v_ai_employee e
LEFT JOIN v_ai_license l ON e.EMP_ID = l.EMP_ID
WHERE TO_CHAR(e.HIRE_DATE, 'YYYY') = ':년도'
  AND e.WORK_STATUS = '재직'
ORDER BY e.EMP_NAME, l.ISSUE_DATE
```

## 핵심 패턴
- **1:N 상세 리스트**: LEFT JOIN으로 모든 자격증 표시
- 자격증 여러개면 여러 행 (정상)
- 자격증 없으면 LICENSE 컬럼이 NULL로 표시
- INNER JOIN 사용 시 자격증 없는 사람 누락됨
```

---

## id=973: 입사자 현황 + 학력 정보 (요약)

### content
```
입사자 현황과 학력 사항
직원 학력 정보
최종 학력 조회
출신 학교 정보
- 1:N 관계 (직원:학력)
- 최종학력만 필요시 서브쿼리
```

### context_data
```
## SQL
```sql
SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION,
       (SELECT MAX(ed.SCHOOL_NAME) FROM v_ai_scholar ed WHERE ed.EMP_ID = e.EMP_ID) AS school_name,
       (SELECT COUNT(*) FROM v_ai_scholar ed WHERE ed.EMP_ID = e.EMP_ID) AS education_count
FROM v_ai_employee e
WHERE TO_CHAR(e.HIRE_DATE, 'YYYY') between ':년도' and ':년도'
  AND e.WORK_STATUS = '재직'
ORDER BY e.EMP_NAME
```

## 핵심 패턴
- **1:N 요약 (학력)**: 서브쿼리로 최종학력 또는 학력 수 조회
- MAX(SCHOOL_NAME)은 예시, 실제로는 졸업연도 기준 최신 학력 조회 필요
```

---

## id=974: 입사자 현황 + 어학 점수

### content
```
입사자 현황과 어학 성적
토익 점수 조회
어학 점수 보유 현황
영어 점수 확인
- 1:N 관계 (직원:어학)
- 어학별로 여러 건 가능
```

### context_data
```
## SQL
```sql
SELECT e.EMP_NAME, e.DEPARTMENT,
       (SELECT MAX(lg.SCORE) FROM v_ai_language lg
        WHERE lg.EMP_ID = e.EMP_ID AND lg.LANGUAGE_TYPE = 'TOEIC') AS toeic_score
FROM v_ai_employee e
WHERE TO_CHAR(e.HIRE_DATE, 'YYYY') = ':년도'
  AND e.WORK_STATUS = '재직'
ORDER BY toeic_score DESC NULLS LAST
```

## 핵심 패턴
- **1:N 요약 (어학)**: 특정 어학(TOEIC)의 최고 점수 조회
- NULLS LAST: 점수 없는 사람 맨 뒤로
```

---

## id=979: 두 사원 전체 데이터 종합 비교 조회

### content
```
- 사원번호 000 번과 000 번의 모든 데이터를 서로 비교해서 한번에 보기 쉽도록 표로 만들어줘
- 두 직원(혹은 그 이상) 전체 정보 비교 표로 보여줘
- 사원 A와 사원 B 모든 데이터 나란히 비교
- 두 (혹은 그 이상)사람 인사 정보 전부 비교해줘
- 특정 사원끼리 종합 비교 분석해줘
- 두 명 비교 표 만들어줘
- 사원들 간의 비교 표 만들어줘
- 두(혹은 3) 사원 학력 경력 자격증 전부 비교
- 사원번호 000 번과 000 번 비교해줘
- 직원 두 명 데이터 대조
- 두 사원의 전체 인사정보를 행/열 전환(피벗) 형태의 비교표로 생성
```

### context_data
```
- ★ 패턴1: VARCHAR2 컬럼 비교 (CROSS JOIN, 타입변환 불필요)
-- 적용: 성명, 영문명, 성별, 부서, 직위, 직급, 보직, 고용형태, 입사유형, 재직상태
SELECT '성명' AS 구분, e1.EMP_NAME AS "사원 241", e2.EMP_NAME AS "사원 242"
FROM v_ai_employee e1, v_ai_employee e2
WHERE e1.EMP_ID = 241 AND e2.EMP_ID = 242

-- ★ 패턴2: DATE 컬럼 비교 (TO_CHAR로 VARCHAR2 변환 필수)
-- 적용: 생년월일, 입사일, 퇴직일
UNION ALL
SELECT '입사일', TO_CHAR(e1.HIRE_DATE, 'YYYY-MM-DD'), TO_CHAR(e2.HIRE_DATE, 'YYYY-MM-DD')
FROM v_ai_employee e1, v_ai_employee e2
WHERE e1.EMP_ID = 241 AND e2.EMP_ID = 242

-- ★ 패턴3: NUMBER 컬럼 비교 (TO_CHAR + NVL로 NULL 방어)
-- 적용: 사원번호, 경력연수
UNION ALL
SELECT '경력연수', NVL(TO_CHAR(e1.CAREER_YEARS), '-') || '년', NVL(TO_CHAR(e2.CAREER_YEARS), '-') || '년'
FROM v_ai_employee e1, v_ai_employee e2
WHERE e1.EMP_ID = 241 AND e2.EMP_ID = 242

-- ★ 패턴4: 1:N 테이블에서 최신 1건 조회 (서브쿼리 ORDER BY + ROWNUM)
-- 적용: 주소(MOD_DATE), 거주지역(MOD_DATE)
-- 주의: ROWNUM은 ORDER BY 전에 적용되므로 반드시 서브쿼리로 감싸야 함
UNION ALL
SELECT '주소',
  (SELECT ADDRESS || ' ' || ADDRESS_DETAIL
   FROM (SELECT ADDRESS, ADDRESS_DETAIL FROM v_ai_address WHERE EMP_ID = 241 ORDER BY MOD_DATE DESC)
   WHERE ROWNUM = 1),
  (SELECT ADDRESS || ' ' || ADDRESS_DETAIL
   FROM (SELECT ADDRESS, ADDRESS_DETAIL FROM v_ai_address WHERE EMP_ID = 242 ORDER BY MOD_DATE DESC)
   WHERE ROWNUM = 1)
FROM DUAL

-- ★ 패턴5: 1:N 테이블 전체 데이터 집약 (LISTAGG + CHR(10) 줄바꿈)
-- 적용: 학력(GRADUATION_DATE↑), 경력(WORK_YEARS↓), 자격증(ISSUE_DATE↑),
--       어학(SCORE↓), 가족(RELATION↑), 교육(START_DATE↓), 상벌(REWARD_DATE↓), 평가(END_YMD↓)
UNION ALL
SELECT '학력',
  (SELECT LISTAGG(SCHOOL_NAME || '(' || NVL(MAJOR_NAME, '-') || ', ' || NVL(TO_CHAR(GRADUATION_DATE), '-') || '졸)', CHR(10))
   WITHIN GROUP (ORDER BY GRADUATION_DATE)
   FROM v_ai_scholar WHERE EMP_ID = 241),
  (SELECT LISTAGG(SCHOOL_NAME || '(' || NVL(MAJOR_NAME, '-') || ', ' || NVL(TO_CHAR(GRADUATION_DATE), '-') || '졸)', CHR(10))
   WITHIN GROUP (ORDER BY GRADUATION_DATE)
   FROM v_ai_scholar WHERE EMP_ID = 242)
FROM DUAL

-- ★ 패턴6: 1:1 테이블 최신 1건 (ORDER BY NULLS LAST로 NULL 후순위)
-- 적용: 병역(DISCHARGE_DATE), 전역일(DISCHARGE_DATE)
UNION ALL
SELECT '병역',
  (SELECT NVL(MILITARY_TYPE, '-') || ' ' || NVL(MILITARY_RANK, '-') || ' ' || NVL(SPECIALTY, '-')
   FROM (SELECT MILITARY_TYPE, MILITARY_RANK, SPECIALTY FROM v_ai_military WHERE EMP_ID = 241 ORDER BY DISCHARGE_DATE DESC NULLS LAST)
   WHERE ROWNUM = 1),
  (SELECT NVL(MILITARY_TYPE, '-') || ' ' || NVL(MILITARY_RANK, '-') || ' ' || NVL(SPECIALTY, '-')
   FROM (SELECT MILITARY_TYPE, MILITARY_RANK, SPECIALTY FROM v_ai_military WHERE EMP_ID = 242 ORDER BY DISCHARGE_DATE DESC NULLS LAST)
   WHERE ROWNUM = 1)
FROM DUAL


SELECT '경력연수', NVL(TO_CHAR(e1.CAREER_YEARS), '-') || '년', NVL(TO_CHAR(e2.CAREER_YEARS), '-') || '년'
FROM v_ai_employee e1, v_ai_employee e2
WHERE e1.EMP_ID = 241 AND e2.EMP_ID = 242

-- ★ 패턴7: PK가 다른 테이블에서 최신 1건 (EMPLOYEE_ID 사용, 금액 포맷팅)
-- 적용: 최근급여 (v_ai_pay_report는 EMP_ID가 아닌 EMPLOYEE_ID)
UNION ALL
SELECT '최근급여(실지급액)',
  (SELECT TO_CHAR(NET_PAY_AMOUNT, 'FM999,999,999') || '원(' || PAY_YEAR_MONTH || ')'
   FROM (SELECT NET_PAY_AMOUNT, PAY_YEAR_MONTH FROM v_ai_pay_report WHERE EMPLOYEE_ID = 241 ORDER BY PAY_YEAR_MONTH DESC)
   WHERE ROWNUM = 1),
  (SELECT TO_CHAR(NET_PAY_AMOUNT, 'FM999,999,999') || '원(' || PAY_YEAR_MONTH || ')'
   FROM (SELECT NET_PAY_AMOUNT, PAY_YEAR_MONTH FROM v_ai_pay_report WHERE EMPLOYEE_ID = 242 ORDER BY PAY_YEAR_MONTH DESC)
   WHERE ROWNUM = 1)
FROM DUAL
```

---

## id=1393: 연령대별 직원수

### content
```
#	질의
1	연령대별 직원 수를 알려줘
2	나이대별로 사원이 몇 명인지 보여줘
3	10대부터 60대까지 연령 구간별 인원 현황 알려줘
4	직원들의 연령대 분포를 알고 싶어
5	20대, 30대, 40대 각각 몇 명이야?
6	우리 회사 연령대별 인원 통계 보여줘
7	세대별 직원 수 분포 현황을 알려줘
8	나이 구간별로 직원 몇 명인지 알려줘
9	전체 직원의 연령대별 인원 분포를 조회해줘
10	50대 이상 직원이 몇 명인지 연령대별로 보여
```

### context_data
```
SELECT
  CASE
    WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 10 AND 19 THEN '10대'
    WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 20 AND 29 THEN '20대'
    WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 30 AND 39 THEN '30대'
    WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 40 AND 49 THEN '40대'
    WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 50 AND 59 THEN '50대'
    WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) >= 60 THEN '60대 이상'
    ELSE '미상' 
  END AS age_group,
  COUNT(DISTINCT EMP_ID) AS employee_count
FROM v_ai_employee
WHERE BIRTH_DATE IS NOT NULL
GROUP BY
  CASE
    WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 10 AND 19 THEN '10대'
    WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 20 AND 29 THEN '20대'
    WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 30 AND 39 THEN '30대'
    WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 40 AND 49 THEN '40대'
    WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) BETWEEN 50 AND 59 THEN '50대'
    WHEN TRUNC(MONTHS_BETWEEN(SYSDATE, BIRTH_DATE) / 12) >= 60 THEN '60대 이상'
    ELSE '미상' 
  END
ORDER BY
  CASE
    WHEN age_group = '10대' THEN 1
    WHEN age_group = '20대' THEN 2
    WHEN age_group = '30대' THEN 3
    WHEN age_group = '40대' THEN 4
    WHEN age_group = '50대' THEN 5
    WHEN age_group = '60대 이상' THEN 6
    ELSE 7
  END
```

---

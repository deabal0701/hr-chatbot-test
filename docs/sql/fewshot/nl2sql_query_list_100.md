# NL2SQL 질의 목록 (100개)

> 대상: V_AI_* 뷰 14개 기준
> 목적: NL2SQL 테스트, Few-shot 예제 후보, 정확도 측정용
> 난이도: ★(단순) ~ ★★★★★(복합)

---

## Level 1 — 단일 테이블, 단순 조회/집계 ★

### v_ai_employee 단독

| # | 질의 | 사용 테이블 | 핵심 패턴 |
|---|------|-----------|----------|
| 1 | 전체 직원 수는? | employee | COUNT(*) |
| 2 | 현재 재직자 수는? | employee | WHERE WORK_STATUS='재직' |
| 3 | 퇴직자 수는? | employee | WHERE WORK_STATUS='퇴직' |
| 4 | 남자 직원 수는? | employee | WHERE GENDER='남' |
| 5 | 여자 재직자 수는? | employee | WHERE GENDER='여' AND WORK_STATUS='재직' |
| 6 | 과장 몇 명이야? | employee | WHERE POSITION='과장' |
| 7 | 정규직 직원 수는? | employee | WHERE EMP_TYPE='정규직' |
| 8 | 기간제 직원 목록 | employee | WHERE EMP_TYPE='기간제', SELECT 목록 |
| 9 | 2024년 입사자 수는? | employee | TO_CHAR(HIRE_DATE,'YYYY')='2024' |
| 10 | 2023년 퇴사자 수는? | employee | TO_CHAR(RETIRE_DATE,'YYYY')='2023' |
| 11 | 개발팀 직원 목록 | employee | WHERE DEPARTMENT LIKE '%개발%' |
| 12 | 팀장인 직원 목록 | employee | WHERE DUTY='팀장' |
| 13 | 경력직 입사자 수는? | employee | WHERE HIRE_TYPE LIKE '%경력%' |
| 14 | 5급 직원 수는? | employee | WHERE GRADE='5급' |
| 15 | 근속 10년 이상 재직자 수는? | employee | WHERE CAREER_YEARS>=10 AND WORK_STATUS='재직' |

### 기타 단일 테이블

| # | 질의 | 사용 테이블 | 핵심 패턴 |
|---|------|-----------|----------|
| 16 | 서울 거주 직원 수는? | address | WHERE REGION='서울', COUNT |
| 17 | 토익 성적 등록된 건수는? | language | WHERE EXAM_TYPE='TOEIC', COUNT |
| 18 | 포상 받은 건수는? | reward | WHERE REWARD_TYPE='포상', COUNT |
| 19 | 징계 받은 건수는? | reward | WHERE REWARD_TYPE='징계', COUNT |
| 20 | 올해 발생연차 총 일수는? | dtm_yy_rest | WHERE REFERENCE_YEAR=올해, SUM |

---

## Level 2 — 단일 테이블, GROUP BY / 집계 ★★

| # | 질의 | 사용 테이블 | 핵심 패턴 |
|---|------|-----------|----------|
| 21 | 부서별 재직자 수는? | employee | GROUP BY DEPARTMENT |
| 22 | 직위별 직원 수는? | employee | GROUP BY POSITION |
| 23 | 성별 직원 수는? | employee | GROUP BY GENDER |
| 24 | 직급별 직원 수는? | employee | GROUP BY GRADE |
| 25 | 연도별 입사자 수는? | employee | GROUP BY TO_CHAR(HIRE_DATE,'YYYY') |
| 26 | 연도별 퇴사자 수는? | employee | GROUP BY TO_CHAR(RETIRE_DATE,'YYYY') |
| 27 | 고용형태별 직원 수는? | employee | GROUP BY EMP_TYPE |
| 28 | 입사구분별 직원 수는? | employee | GROUP BY HIRE_TYPE |
| 29 | 부서별 평균 근속연수는? | employee | GROUP BY DEPARTMENT, AVG(CAREER_YEARS) |
| 30 | 지역별 직원 분포는? | address | GROUP BY REGION |
| 31 | 시험종류별 평균 점수는? | language | GROUP BY EXAM_TYPE, AVG(SCORE) |
| 32 | 교육연도별 수료 건수는? | training | GROUP BY TRAINING_YEAR, WHERE 수료 |
| 33 | 평가등급별 인원 수는? | feedback | GROUP BY APPR_GRADE |
| 34 | 발령유형별 건수는? | history | GROUP BY ASSIGNMENT_TYPE_CODE |
| 35 | 근속연수 구간별 직원 분포는? | employee | CASE WHEN 구간, GROUP BY |

---

## Level 3 — 2테이블 JOIN, 단순 필터 ★★★

| # | 질의 | 사용 테이블 | 핵심 패턴 |
|---|------|-----------|----------|
| 36 | 서울 거주 과장 목록 | employee + address | JOIN + WHERE REGION, POSITION |
| 37 | 경기도 거주 재직자 수는? | employee + address | JOIN + WHERE REGION='경기' |
| 38 | 토익 800점 이상 직원 목록 | employee + language | JOIN + WHERE SCORE>=800 |
| 39 | 대졸 이상 직원 수는? | employee + scholar | JOIN + WHERE EDUCATION_LEVEL |
| 40 | 자녀가 있는 직원 수는? | employee + family | JOIN + WHERE RELATION='자녀' |
| 41 | 군필인 재직자 수는? | employee + military | JOIN + WHERE SERVICE_STATUS='군필' |
| 42 | 국가자격증 보유 직원 목록 | employee + license | JOIN + WHERE LICENSE_TYPE='국가자격' |
| 43 | 포상 받은 직원 목록 | employee + reward | JOIN + WHERE REWARD_TYPE='포상' |
| 44 | 올해 교육 수료한 직원 목록 | employee + training | JOIN + WHERE TRAINING_YEAR, 수료 |
| 45 | S등급 받은 직원 목록 | employee + feedback | JOIN + WHERE APPR_GRADE='S' |
| 46 | 휴직 중인 직원 목록 | employee + history | JOIN + WHERE LEAVE_OF_ABSENCE_YN='Y' |
| 47 | 전직장이 삼성인 직원 목록 | employee + career | JOIN + WHERE PREV_COMPANY LIKE '%삼성%' |
| 48 | 잔여연차 5일 미만 직원 목록 | employee + dtm_yy_rest | JOIN + WHERE REMAINING < 5 |
| 49 | 2024년 정기급여 실수령액 목록 | employee + pay_report | JOIN + WHERE PAY_YEAR, PAYMENT_TYPE |
| 50 | 승진 발령 받은 직원 목록 | employee + history | JOIN + WHERE ASSIGNMENT_TYPE='승진' |

---

## Level 4 — 2테이블 JOIN + GROUP BY / 집계 ★★★

| # | 질의 | 사용 테이블 | 핵심 패턴 |
|---|------|-----------|----------|
| 51 | 부서별 서울 거주 직원 수는? | employee + address | JOIN + GROUP BY DEPARTMENT |
| 52 | 부서별 토익 평균 점수는? | employee + language | JOIN + GROUP BY, AVG(SCORE) |
| 53 | 부서별 자격증 보유 건수는? | employee + license | JOIN + GROUP BY, COUNT |
| 54 | 부서별 평균 급여는? | employee + pay_report | JOIN + GROUP BY, AVG(NET_PAY) |
| 55 | 부서별 잔여연차 평균은? | employee + dtm_yy_rest | JOIN + GROUP BY, AVG |
| 56 | 부서별 포상 건수는? | employee + reward | JOIN + GROUP BY, COUNT |
| 57 | 부서별 교육 이수시간 합계는? | employee + training | JOIN + GROUP BY, SUM(HOURS) |
| 58 | 직급별 평균 급여는? | employee + pay_report | JOIN + GROUP BY GRADE |
| 59 | 지역별 직급 분포는? | employee + address | JOIN + GROUP BY REGION, POSITION |
| 60 | 전직장 3곳 이상 경력자 목록 | employee + career | JOIN + GROUP BY HAVING COUNT>=3 |
| 61 | 자녀 2명 이상 직원 목록 | employee + family | JOIN + GROUP BY HAVING COUNT>=2 |
| 62 | 직원별 교육 이수 횟수 순위 | employee + training | JOIN + GROUP BY, ORDER BY COUNT DESC |
| 63 | 평가등급별 평균 급여는? | feedback + pay_report | 2테이블 + GROUP BY APPR_GRADE |
| 64 | 연도별 승진자 수는? | employee + history | JOIN + GROUP BY 연도 |
| 65 | 가장 많이 거친 전직장 TOP 10 | employee + career | JOIN + GROUP BY PREV_COMPANY, FETCH 10 |

---

## Level 5 — 3+ 테이블 JOIN / 복합 조건 ★★★★

| # | 질의 | 사용 테이블 | 핵심 패턴 |
|---|------|-----------|----------|
| 66 | 서울 거주 대졸 이상 재직자 수는? | employee + address + scholar | 3테이블 JOIN |
| 67 | 토익 800점 이상이고 자격증 보유한 직원 목록 | employee + language + license | 3테이블 JOIN |
| 68 | 경기도 거주 과장 중 S등급 받은 직원 | employee + address + feedback | 3테이블 JOIN + 복합 WHERE |
| 69 | 서울 거주 직원 중 전직장이 3곳 이상인 사람 | employee + address + career | 3테이블 + HAVING |
| 70 | 자녀 있는 직원 중 잔여연차 5일 미만인 목록 | employee + family + dtm_yy_rest | 3테이블 JOIN |
| 71 | 군필인 남자 직원 중 토익 점수 상위 10명 | employee + military + language | 3테이블 + ORDER BY + FETCH |
| 72 | 포상 받은 직원의 평가등급 분포 | employee + reward + feedback | 3테이블 + GROUP BY |
| 73 | 교육 10회 이상 이수한 직원의 평균 급여 | employee + training + pay_report | 3테이블 + HAVING + AVG |
| 74 | 부서별 대졸 비율은? | employee + scholar | JOIN + COUNT 비율 계산 |
| 75 | 2024년 입사자 중 경기도 거주자 목록 | employee + address | JOIN + 복합 WHERE |

---

## Level 6 — 서브쿼리 / 분석함수 / 복합 집계 ★★★★★

| # | 질의 | 사용 테이블 | 핵심 패턴 |
|---|------|-----------|----------|
| 76 | 부서별 최고 급여자는? | employee + pay_report | ROW_NUMBER() / 서브쿼리 |
| 77 | 평균 근속연수보다 오래 근무한 직원 목록 | employee | 서브쿼리 AVG 비교 |
| 78 | 토익 점수가 부서 평균보다 높은 직원 | employee + language | 상관 서브쿼리 |
| 79 | 부서별 남녀 비율은? | employee | CASE WHEN + GROUP BY + 비율 계산 |
| 80 | 직급별 재직/퇴직 비율은? | employee | CASE WHEN + GROUP BY + 비율 |
| 81 | 부서별 연차 사용률은? | employee + dtm_yy_rest | SUM(사용)/SUM(발생)*100 |
| 82 | 전년 대비 입사자 증감은? | employee | LAG/서브쿼리 + 연도별 비교 |
| 83 | 급여 상위 10% 직원 목록 | employee + pay_report | PERCENTILE / ROW_NUMBER |
| 84 | 부서별 평균 급여 순위 | employee + pay_report | RANK() OVER + GROUP BY |
| 85 | 교육비 합계 상위 5개 부서 | employee + training | GROUP BY + SUM + FETCH 5 |
| 86 | 자격증 3개 이상 보유한 대졸 이상 직원 | employee + license + scholar | 3테이블 + HAVING + EXISTS |
| 87 | 최근 3년간 승진한 직원 중 평가 S등급 비율 | employee + history + feedback | 3테이블 + 기간 필터 + 비율 |
| 88 | 부서별 근속연수 5년 구간별 인원 분포 | employee | CASE WHEN 구간 + PIVOT형 GROUP BY |
| 89 | 전직장 평균 근무기간이 2년 미만인 직원 | employee + career | JOIN + GROUP BY + HAVING AVG |
| 90 | 연차 사용률 하위 10명 | employee + dtm_yy_rest | 사용/발생 비율 + ORDER BY + FETCH |

---

## Level 7 — 실무 복합 시나리오 ★★★★★

| # | 질의 | 사용 테이블 | 핵심 패턴 |
|---|------|-----------|----------|
| 91 | 올해 잔여연차가 많은 부서 TOP 5 | employee + dtm_yy_rest | GROUP BY DEPT + AVG(REMAINING) + FETCH |
| 92 | 부서별 월평균 급여와 전체 평균 대비 비율 | employee + pay_report | GROUP BY + 전체 AVG 서브쿼리 + 비율 |
| 93 | 5년 이상 근속자 중 승진 이력 없는 직원 | employee + history | LEFT JOIN + IS NULL (승진 없음) |
| 94 | 교육 미이수 재직자 목록 (올해 수료 0건) | employee + training | LEFT JOIN + IS NULL / NOT EXISTS |
| 95 | 부서별 성별 평균 급여 차이 | employee + pay_report | GROUP BY DEPT, GENDER + PIVOT |
| 96 | 경력직 입사자 vs 신입 입사자 평균 급여 비교 | employee + pay_report | CASE WHEN HIRE_TYPE + GROUP BY |
| 97 | 전직장 경험 있는 직원과 없는 직원의 평가등급 분포 비교 | employee + career + feedback | LEFT JOIN + CASE WHEN + GROUP BY |
| 98 | 지역별 직급별 평균 급여 교차표 | employee + address + pay_report | 3테이블 + GROUP BY REGION, GRADE |
| 99 | 최근 1년 내 발령 받은 직원의 연차 사용률 | employee + history + dtm_yy_rest | 3테이블 + 기간 필터 + 비율 |
| 100 | 부서별 인원/평균근속/평균급여/교육이수율/연차사용률 종합 리포트 | employee + pay + training + dtm | 4테이블 JOIN + 다중 집계 |

---

## 난이도별 요약

| 난이도 | 범위 | 테이블 수 | 패턴 | 건수 |
|:---:|------|:---:|------|:---:|
| ★ | #1~#20 | 1개 | 단순 COUNT/WHERE | 20 |
| ★★ | #21~#35 | 1개 | GROUP BY, HAVING, CASE WHEN | 15 |
| ★★★ | #36~#65 | 2개 | JOIN + 필터/집계 | 30 |
| ★★★★ | #66~#75 | 3+개 | 다중 JOIN + 복합 조건 | 10 |
| ★★★★★ | #76~#100 | 2~4개 | 서브쿼리, 분석함수, 비율, PIVOT | 25 |
| | | | **합계** | **100** |

---

## 뷰별 사용 빈도 (예상)

| 뷰 | 등장 횟수 | 비고 |
|----|:---:|------|
| v_ai_employee | ~95 | 거의 모든 질의에 필요 |
| v_ai_pay_report | ~15 | 급여 관련 |
| v_ai_address | ~10 | 지역 관련 |
| v_ai_training | ~8 | 교육 관련 |
| v_ai_dtm_yy_rest | ~8 | 연차 관련 |
| v_ai_feedback | ~8 | 평가 관련 |
| v_ai_history | ~7 | 발령/승진 |
| v_ai_career | ~6 | 전직장 경력 |
| v_ai_family | ~5 | 가족 |
| v_ai_language | ~5 | 어학 |
| v_ai_license | ~5 | 자격증 |
| v_ai_scholar | ~5 | 학력 |
| v_ai_reward | ~5 | 상벌 |
| v_ai_military | ~3 | 병역 |

---

## 부록: 실무 HR 분석 쿼리 (인사담당자 관점)

> HR 부서에서 실제로 자주 요청하는 분석 질의. 경영진 보고, 인력 계획, 감사 대응 등에 활용.

### A. 인력 현황 분석

| # | 질의 | 분석 목적 |
|---|------|----------|
| A1 | 부서별 정원 대비 현원 현황 (부서별 재직자 수) | 인력 과부족 파악 |
| A2 | 최근 5년간 연도별 입사/퇴사 추이 | 이직률 트렌드 |
| A3 | 부서별 퇴직률 (퇴사자/전체 비율) | 고위험 부서 식별 |
| A4 | 정규직 vs 기간제 비율 및 부서별 분포 | 비정규직 관리 |
| A5 | 근속연수 구간별(1년미만/1~3/3~5/5~10/10+) 인원 분포 | 조직 안정성 진단 |
| A6 | 직급별 평균 근속연수 | 승진 소요 연수 분석 |
| A7 | 입사구분별(신입/경력/기간제/재입사) 연도별 추이 | 채용 전략 평가 |
| A8 | 50대 이상 재직자 부서별 분포 | 정년 대비 인력 계획 |

### B. 보상/급여 분석

| # | 질의 | 분석 목적 |
|---|------|----------|
| B1 | 부서별 월평균 실수령액 | 부서 간 급여 형평성 |
| B2 | 직급별 급여 중위값과 상/하위 25% | 급여 밴드 적정성 |
| B3 | 동일 직급 내 남녀 평균 급여 차이 | 성별 급여 격차 (감사 대응) |  
| B4 | 상여금 지급 총액 부서별 비교 | 성과급 분배 분석 |
| B5 | 최근 12개월 급여 총지급액 추이 | 인건비 트렌드 |
| B6 | 고정비 대비 변동비 비율 부서별 분석 | 급여 구조 진단 |
| B7 | 공제/세금 비율 직급별 분석 | 실수령률 파악 |

### C. 평가/성과 분석

| # | 질의 | 분석 목적 |
|---|------|----------|
| C1 | 부서별 평가등급 분포 (S/A/B/C/D 비율) | 평가 편향 진단 |
| C2 | 직급별 평균 평가점수 | 직급 간 성과 비교 |
| C3 | 최근 3년간 S등급 2회 이상 받은 직원 (고성과자 풀) | 승진 후보 식별 |
| C4 | 평가등급과 급여 상관관계 (등급별 평균 급여) | Pay-for-Performance 진단 |
| C5 | 평가등급 하위(C,D) 직원의 근속연수 분포 | 저성과자 관리 |
| C6 | 부서별 평가점수 표준편차 (관대/엄격 평가 부서 식별) | 평가 공정성 분석 |

### D. 교육/역량 분석

| # | 질의 | 분석 목적 |
|---|------|----------|
| D1 | 부서별 1인당 평균 교육시간 | 교육 투자 균형 |
| D2 | 부서별 1인당 교육비용 | 교육 예산 배분 |
| D3 | 올해 교육 미이수 재직자 목록 | 필수교육 미이수 관리 |
| D4 | 교육 유형별(집합/사이버) 참여율 추이 | 교육 방식 효과 분석 |
| D5 | 토익 800점 이상 직원의 부서별 분포 | 글로벌 인력 파악 |
| D6 | 자격증 보유 현황 부서별 분석 | 전문 역량 분포 |
| D7 | 대졸/석사/박사 학력 분포 부서별 분석 | 학력 수준 진단 |

### E. 인사이동/승진 분석

| # | 질의 | 분석 목적 |
|---|------|----------|
| E1 | 최근 3년간 부서별 승진자 수 추이 | 승진 기회 균형 |
| E2 | 직급별 평균 승진 소요연수 (해당 직급 체류기간) | 승진 적체 진단 |
| E3 | 5년 이상 동일 직급 체류 직원 목록 | 승진 누락 후보 |
| E4 | 휴직(육아/병가/개인) 유형별 현황 | 복지 정책 모니터링 |
| E5 | 부서 간 전보 빈도 (어디서 어디로 많이 이동?) | 인사이동 패턴 |

### F. 연차/근태 분석

| # | 질의 | 분석 목적 |
|---|------|----------|
| F1 | 부서별 연차 사용률 (사용/발생 비율) | 연차 촉진 대상 부서 |
| F2 | 잔여연차 10일 이상 직원 목록 | 연차 소진 독려 대상 |
| F3 | 직급별 평균 연차 사용률 | 직급 간 워라밸 비교 |
| F4 | 연차 사용률 하위 10% 직원 | 번아웃 위험군 |
| F5 | 근속연수별 발생연차 평균 | 연차 부여 기준 점검 |

### G. 다이버시티/ESG 분석

| # | 질의 | 분석 목적 |
|---|------|----------|
| G1 | 직급별 여성 비율 (유리천장 지수) | 성별 다양성 |
| G2 | 관리직(과장 이상) 여성 비율 | ESG 지표 |
| G3 | 장애 가족 보유 직원 현황 | 복지 지원 대상 |
| G4 | 지역별 거주 분포와 부서 분포 교차 분석 | 출퇴근 거리 이슈 |
| G5 | 연령대별(20대/30대/40대/50대+) 부서 분포 | 세대 다양성 |

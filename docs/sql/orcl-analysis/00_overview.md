# Oracle Business View 재설계 — NL2SQL 성능 향상 계획

## 1. 목적

Oracle HR 비즈니스 DB의 `V_AI_*` 뷰와 이를 활용하는 NL2SQL 파이프라인 전반을 개선하여, 자연어 질의 → SQL 생성의 **정확도와 신뢰성**을 높인다.

현재 NL2SQL 파이프라인의 주요 병목:

| 영역 | 문제 | 영향 |
|------|------|------|
| View 데이터 품질 | PHM_EMP 중복(COMPANY_CD 복수 소속), NULL 컬럼 | 집계 쿼리 부정확, 근속연수 계산 불가 |
| Table Catalog | 컬럼 설명 부족, 값 도메인 미기재, 조인 관계 불명확 | LLM이 잘못된 컬럼/조인 선택 |
| Few-shot 예제 | 실제 데이터 패턴과 괴리, 뷰 간 JOIN 예제 부족 | SQL 생성 실패율 증가 |
| 조직 체계 | ORG_ID ↔ 부서명 매핑이 FRM_CODE 경유, 계층 구조 미반영 | 부서별 집계 질의 오류 |

이 디렉토리의 분석 문서들은 위 문제를 **영역별로 분석하고 수정안을 도출**하기 위한 것이다.

---

## 2. 파일 넘버링 규칙

```
01~14  : 뷰 단위 분석/재설계 (V_AI_* 뷰 14개, 1:1 대응)
20~29  : NL2SQL 파이프라인 개선 (table_catalog, fewshot, prompt 등)
30~39  : 참조 데이터 / 기초 분석
```

---

## 3. 뷰 단위 분석 문서 (01~14)

| # | 파일명 | 대상 뷰 | 상태 | 주요 내용 |
|---|--------|---------|------|----------|
| 01 | `01_v_ai_employee_redesign.md` | V_AI_EMPLOYEE | **작성 완료** | PHM_EMP 중복 제거(COMPANY_CD), CAREER_MONTHS/YEARS NULL→HIRE_DATE 기반 계산, NL2SQL 연동 |
| 02 | `02_v_ai_address.md` | V_AI_ADDRESS | **작성 완료** | 주소 중복 확인 필요, REGION 값 도메인 보강, PII 관리 |
| 03 | `03_v_ai_career.md` | V_AI_CAREER | **작성 완료** | RCAREER_NUM NULL 확인 필요, CAREER vs WORK 혼동 방지, 카탈로그 보강 |
| 04 | `04_v_ai_scholar.md` | V_AI_SCHOLAR | **작성 완료** | PHM_EMP JOIN 제거(방안A) 또는 COMPANY_CD 필터(방안B), POSITION 중복 제거, 카탈로그 컬럼명 동기화 |
| 05 | `05_v_ai_family.md` | V_AI_FAMILY | **작성 완료** | DDL 변경 없음, COMMENT/카탈로그 보강, PII 주의, fewshot 3건 |
| 06 | `06_v_ai_language.md` | V_AI_LANGUAGE | **작성 완료** | dead JOIN(FC3) 제거, LANGUAGE_GRADE 코드→한글 변환, EXAM_YEAR TO_CHAR 수정 |
| 07 | `07_v_ai_license.md` | V_AI_LICENSE | **작성 완료** | VALIDITY_STATUS 타입 버그 수정(REGEXP→DATE비교), LICENSE_NO PII |
| 08 | `08_v_ai_military.md` | V_AI_MILITARY | **작성 완료** | UK(EMP_ID) 1:1 확정, SUBSTR→TO_CHAR, ENLIST_DATE 추가, FC6 CD_KIND 오타 검증 |
| 09 | `09_v_ai_reward.md` | V_AI_REWARD | **작성 완료** | SUBSTR→TO_CHAR, 카탈로그 REWARD_YEAR 추가, fewshot 3건 |
| 10 | `10_v_ai_training.md` | V_AI_TRAINING | **작성 완료** | DDL 변경 없음, 카탈로그 누락 9개→11개 보강, COMMENT 전 컬럼 추가, fewshot 3건 |
| 11 | `11_v_ai_feedback.md` | V_AI_FEEDBACK | **작성 완료** | VI_FRM_PHM_EMP COMPANY_CD 중복 파급, 컬럼 명명 불일치, Oracle 함수 의존, 카탈로그/COMMENT/fewshot 보강 |
| 12 | `12_v_ai_history.md` | V_AI_HISTORY | **작성 완료** | table_catalog 신규 등재, EMPLOYEE_ID→EMP_ID 통일, COMMENT 오류 수정, fewshot 3건 |
| 13 | `13_v_ai_pay_report.md` | V_AI_PAY_REPORT | **작성 완료** | FC5 CD_KIND 매핑 오류(검증 대기), EMPLOYEE_ID→EMP_ID 통일, 급여 계산 구조 명시, fewshot 3건 |
| 14 | `14_v_ai_dtm_yy_rest.md` | V_AI_DTM_YY_REST | **작성 완료** | dead JOIN 활용, TOTAL/REMAINING_LEAVE_DAYS 계산 컬럼 추가, NVL 누락 수정, fewshot 3건 |

---

## 4. NL2SQL 파이프라인 개선 문서 (20~29)

| # | 파일명 | 상태 | 주요 내용 |
|---|--------|------|----------|
| 20 | `20_table_catalog_update.md` | **반영 완료** | 컬럼별 값 도메인 → `table_catalog.py`에 반영 완료 |
| 21 | `21_fewshot_redesign.md` | 예정 | 빈출 질의 유형별 few-shot 예제 재설계 |
| 22 | `22_prompt_build_enhancement.md` | 예정 | prompt_build에 catalog 컨텍스트 주입 검토 |

---

## 5. 참조 데이터 (30~39)

| # | 파일명 | 상태 | 내용 |
|---|--------|------|------|
| 30 | `30_org_cd_reference.md` | **완료** | FRM_CODE 테이블의 CPE_GROUP_CD 원본 데이터 (조직코드 매핑) |
| -- | `fewshot_as-is.md` | **완료** | 기존 tb_docs fewshot 예제 34건 AS-IS 현황 (id=935~949 등) |

---

## 6. 관련 시스템 파일

| 파일 | 역할 | 변경 예상 |
|------|------|----------|
| `docs/sql/orcl-business_view_db.sql` | Oracle 뷰 DDL 원본 | 뷰 수정 시 동기화 |
| `docs/sql/orcl-business_org_db.sql` | Oracle 원본 테이블 DDL | 참조용 |
| `app/core/database/table_catalog.py` | NL2SQL용 테이블 메타데이터 | catalog 보강 |
| `app/core/llm/prompt_service.py` | NL2SQL 프롬프트 (few-shot 포함) | few-shot 재설계 |
| `app/graphs/nl2sql/nodes.py` | NL2SQL 그래프 노드 | schema/fewshot 노드 개선 |
| `app/core/config/settings_config.py` | DB 설정 스키마 | catalog 설정 구조 변경 시 |

---

## 7. 작업 순서

```
[Phase 1] 데이터 품질 — 뷰 수정 (01~14 중 이슈 있는 뷰)        ← 분석 완료, Oracle 뷰 DDL 적용 대기
    ↓
[Phase 2] 메타데이터 — Table Catalog 보강 (20)                  ← table_catalog.py 반영 완료
    ↓
[Phase 3] 프롬프트 — Few-shot 재설계 (21), Prompt 보강 (22)     ← 예정
    ↓
[Phase 4] 통합 테스트 — NL2SQL 정확도 비교 (before/after)        ← 예정
```

**현재 진행 상황**: Phase 1 분석 완료 + Phase 2 코드 반영 완료. Oracle 뷰 DDL 적용과 Phase 3~4가 남아있다.

---

## 8. 참고

- 분석 시 Oracle 접속 정보는 `app/core/database/external.py` 설정 참조
- 뷰 수정 후 반드시 `orcl-business_view_db.sql`에 DDL 동기화

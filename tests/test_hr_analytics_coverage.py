"""HR 분석 쿼리 커버리지 테스트

위치: tests/test_hr_analytics_coverage.py

목적:
  - 부록 A~G 37개 HR 분석 질의에 대해 NL2SQL 파이프라인 전체 검증
  - Few-shot 매핑, SQL 생성, SQL 실행, 답변 품질 항목별 체크
  - 결과를 docs/sql/fewshot/coverage_report_YYYYMMDD.md 로 저장

실행:
  pytest tests/test_hr_analytics_coverage.py -v -s
  pytest tests/test_hr_analytics_coverage.py -v -s -k "test_hr"
  pytest tests/test_hr_analytics_coverage.py -v -s --timeout=600
"""
import uuid
import httpx
import pytest
from datetime import datetime
from pathlib import Path

# ─────────────────────────────────────────
# 상수
# ─────────────────────────────────────────
BASE_URL = "http://localhost:19090"
LONG_TIMEOUT = 90.0          # 쿼리 1건당 최대 대기 시간
SEARCH_PREFIX = "/api/v1/search"
ADMIN_ID = "admin"
ADMIN_PW = "Win1234!"

# SQL 생성 성공 판정 기준
PASS_RATE_THRESHOLD = 0.60   # SQL 생성률 60% 이상이면 전체 PASS

# 보고서 저장 경로
REPORT_DIR = Path(__file__).parent.parent / "docs" / "sql" / "fewshot"

# ─────────────────────────────────────────
# 37개 HR 분석 질의 (부록 A~G)
# (id, category, question, purpose)
# ─────────────────────────────────────────
HR_QUERIES = [
    # A. 인력 현황 분석
    ("A1", "인력현황", "부서별 재직자 수를 알려줘",                                           "인력 과부족 파악"),
    ("A2", "인력현황", "최근 5년간 연도별 입사 퇴사 추이를 보여줘",                           "이직률 트렌드"),
    ("A3", "인력현황", "부서별 퇴직률을 계산해줘",                                            "고위험 부서 식별"),
    ("A4", "인력현황", "정규직과 기간제 비율 및 부서별 분포는?",                               "비정규직 관리"),
    ("A5", "인력현황", "근속연수 구간별 인원 분포를 알려줘 (1년미만, 1~3년, 3~5년, 5~10년, 10년이상)", "조직 안정성"),
    ("A6", "인력현황", "직급별 평균 근속연수는 얼마야?",                                       "승진 소요 연수"),
    ("A7", "인력현황", "입사구분별 연도별 추이를 보여줘",                                      "채용 전략 평가"),
    ("A8", "인력현황", "50대 이상 재직자 부서별 분포를 알려줘",                               "정년 대비 계획"),
    # B. 보상/급여 분석
    ("B1", "급여분석", "부서별 월평균 실수령액을 보여줘",                                     "급여 형평성"),
    ("B2", "급여분석", "직급별 급여 중위값과 상위 25% 하위 25%를 알려줘",                     "급여 밴드 적정성"),
    ("B3", "급여분석", "동일 직급 내 남녀 평균 급여 차이를 보여줘",                           "성별 급여 격차"),
    ("B4", "급여분석", "상여금 지급 총액 부서별 비교를 해줘",                                 "성과급 분배"),
    ("B5", "급여분석", "최근 12개월 급여 총지급액 추이를 보여줘",                             "인건비 트렌드"),
    ("B6", "급여분석", "고정비 대비 변동비 비율 부서별 분석을 해줘",                           "급여 구조"),
    ("B7", "급여분석", "공제와 세금 비율을 직급별로 분석해줘",                                 "실수령률 파악"),
    # C. 평가/성과 분석
    ("C1", "평가분석", "부서별 평가등급 분포를 알려줘",                                       "평가 편향 진단"),
    ("C2", "평가분석", "직급별 평균 평가점수를 보여줘",                                       "직급 간 성과 비교"),
    ("C3", "평가분석", "최근 3년간 S등급을 2회 이상 받은 직원 목록을 알려줘",                  "고성과자 식별"),
    ("C4", "평가분석", "평가등급별 평균 급여를 보여줘",                                       "Pay-for-Performance"),
    ("C5", "평가분석", "평가등급이 C나 D인 직원의 근속연수 분포는?",                           "저성과자 관리"),
    ("C6", "평가분석", "부서별 평가점수 표준편차를 계산해줘",                                  "평가 공정성"),
    # D. 교육/역량 분석
    ("D1", "교육분석", "부서별 1인당 평균 교육시간을 알려줘",                                  "교육 투자 균형"),
    ("D2", "교육분석", "부서별 1인당 교육비용을 보여줘",                                       "교육 예산"),
    ("D3", "교육분석", "올해 교육 미이수 재직자 목록을 알려줘",                               "필수교육 미이수"),
    ("D4", "교육분석", "교육 유형별 집합교육과 사이버교육 참여율 추이를 보여줘",               "교육 방식 효과"),
    ("D5", "교육분석", "토익 800점 이상 직원의 부서별 분포를 알려줘",                          "글로벌 인력"),
    ("D6", "교육분석", "자격증 보유 현황을 부서별로 분석해줘",                                 "전문 역량"),
    ("D7", "교육분석", "대졸 석사 박사 학력 분포를 부서별로 알려줘",                           "학력 수준"),
    # E. 인사이동/승진 분석
    ("E1", "인사이동", "최근 3년간 부서별 승진자 수 추이를 보여줘",                           "승진 기회 균형"),
    ("E2", "인사이동", "직급별 평균 승진 소요연수를 알려줘",                                   "승진 적체"),
    ("E3", "인사이동", "5년 이상 동일 직급에 있는 직원 목록을 알려줘",                        "승진 누락"),
    ("E4", "인사이동", "휴직 유형별 육아휴직 병가 개인휴직 현황을 알려줘",                    "복지 모니터링"),
    ("E5", "인사이동", "부서 간 전보 빈도를 알려줘",                                          "인사이동 패턴"),
    # F. 연차/근태 분석
    ("F1", "연차분석", "부서별 연차 사용률을 알려줘",                                         "연차 촉진"),
    ("F2", "연차분석", "잔여연차가 10일 이상인 직원 목록을 알려줘",                           "연차 소진 독려"),
    ("F3", "연차분석", "직급별 평균 연차 사용률을 보여줘",                                    "워라밸 비교"),
    # G. 다이버시티/ESG 분석
    ("G1", "ESG분석",  "직급별 여성 비율을 알려줘",                                           "성별 다양성"),
    ("G2", "ESG분석",  "과장 이상 관리직의 여성 비율은 얼마야?",                              "ESG 지표"),
    ("G3", "ESG분석",  "연령대별 부서 분포를 알려줘",                                         "세대 다양성"),
]


# ─────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────
@pytest.fixture(scope="module")
def long_client():
    with httpx.Client(base_url=BASE_URL, timeout=LONG_TIMEOUT) as c:
        yield c


@pytest.fixture(scope="module")
def admin_headers(long_client):
    resp = long_client.post("/api/v1/auth/login", json={"login_id": ADMIN_ID, "password": ADMIN_PW})
    assert resp.status_code == 200, f"로그인 실패: {resp.text}"
    token = resp.json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ─────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────
def _call_nl2sql(client: httpx.Client, headers: dict, question: str) -> dict:
    """NL2SQL 엔드포인트 호출 후 결과 dict 반환"""
    session_id = f"coverage-{uuid.uuid4().hex[:8]}"
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

    return {
        "http_ok":      http_ok,
        "api_success":  api_success,
        "has_sql":      bool(sql),
        "sql":          sql[:120].replace("\n", " ") if sql else "",   # 보고서용 앞 120자
        "has_result":   bool(sql_result) and row_count >= 0,
        "row_count":    row_count,
        "exec_ms":      exec_ms,
        "has_answer":   bool(answer.strip()),
        "answer_len":   len(answer),
        "error":        error_msg[:80] if error_msg else "",
    }


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
    return "PASS"


def _build_report(rows: list) -> str:
    """마크다운 보고서 생성"""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    total = len(rows)
    passed   = sum(1 for r in rows if r["grade"] == "PASS")
    fail_sql = sum(1 for r in rows if "FAIL-SQL" in r["grade"])
    warn     = sum(1 for r in rows if "WARN" in r["grade"])
    fail_api = sum(1 for r in rows if "FAIL-API" in r["grade"])

    lines = [
        f"# HR 분석 쿼리 커버리지 테스트 보고서",
        f"",
        f"> 생성일시: {now}",
        f"",
        f"## 요약",
        f"",
        f"| 항목 | 건수 | 비율 |",
        f"|------|------|------|",
        f"| 전체 질의 | {total} | 100% |",
        f"| **PASS** (SQL생성+실행+답변) | **{passed}** | **{passed/total:.0%}** |",
        f"| FAIL-SQL (SQL 미생성) | {fail_sql} | {fail_sql/total:.0%} |",
        f"| WARN (빈결과/답변없음) | {warn} | {warn/total:.0%} |",
        f"| FAIL-API (서버오류) | {fail_api} | {fail_api/total:.0%} |",
        f"",
        f"## 상세 결과",
        f"",
        f"| ID | 카테고리 | 질의 | 판정 | rows | ms | SQL (앞 120자) | 오류 |",
        f"|----|---------|------|------|------|----|---------------|------|",
    ]
    for r in rows:
        q_short = r["question"][:30] + ("…" if len(r["question"]) > 30 else "")
        lines.append(
            f"| {r['id']} | {r['category']} | {q_short} | `{r['grade']}` "
            f"| {r['row_count']} | {r['exec_ms']} | {r['sql']} | {r['error']} |"
        )

    lines += [
        f"",
        f"## 판정 기준",
        f"",
        f"| 판정 | 의미 |",
        f"|------|------|",
        f"| `PASS` | SQL 생성 + 실행 성공 + 1행 이상 + 답변 생성 |",
        f"| `WARN-EMPTY` | SQL 실행 성공이나 결과 0행 (데이터 없음) |",
        f"| `WARN-NOANSWER` | 결과는 있으나 LLM 답변 없음 |",
        f"| `FAIL-SQL` | SQL 미생성 (few-shot 부족 또는 intent 오류) |",
        f"| `FAIL-EXEC` | SQL 생성됐으나 실행 실패 (문법/권한 오류) |",
        f"| `FAIL-API` | HTTP 오류 또는 서버 예외 |",
    ]
    return "\n".join(lines)


def _save_report(content: str) -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    fname = REPORT_DIR / f"coverage_report_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
    fname.write_text(content, encoding="utf-8")
    return fname


# ─────────────────────────────────────────
# 테스트
# ─────────────────────────────────────────
class TestHRAnalyticsCoverage:
    """HR 분석 쿼리 커버리지 검증 (37개 질의)"""

    def test_hr_analytics_full_coverage(self, long_client, admin_headers):
        """
        37개 HR 분석 질의를 순서대로 실행하여 커버리지 보고서 생성.

        판정 기준:
          PASS       = SQL 생성 + 실행 성공 + row ≥ 1 + 답변 생성
          WARN-*     = 부분 성공 (empty result 등)
          FAIL-SQL   = SQL 미생성 → few-shot 보완 필요
          FAIL-EXEC  = 생성된 SQL 실행 오류 → SQL 패턴 수정 필요
          FAIL-API   = 서버 오류

        통과 기준: SQL 생성률 60% 이상
        """
        rows = []
        print(f"\n{'='*70}")
        print(f"{'HR 분석 쿼리 커버리지 테스트':^70}")
        print(f"{'='*70}")
        print(f"{'ID':<4} {'카테고리':<10} {'질의(앞30자)':<32} {'판정':<14} {'rows':>5} {'ms':>6}")
        print(f"{'-'*70}")

        for query_id, category, question, purpose in HR_QUERIES:
            result = _call_nl2sql(long_client, admin_headers, question)
            grade = _grade(result)

            row = {
                "id":       query_id,
                "category": category,
                "question": question,
                "purpose":  purpose,
                "grade":    grade,
                **result,
            }
            rows.append(row)

            q_short = question[:30] + ("…" if len(question) > 30 else "")
            print(f"{query_id:<4} {category:<10} {q_short:<32} {grade:<14} {result['row_count']:>5} {result['exec_ms']:>6}")
            if result["error"]:
                print(f"       ⚠ {result['error']}")

        # 보고서 생성 & 저장
        report = _build_report(rows)
        report_path = _save_report(report)

        print(f"\n{'='*70}")
        total   = len(rows)
        passed  = sum(1 for r in rows if r["grade"] == "PASS")
        has_sql = sum(1 for r in rows if r["has_sql"])
        warn    = sum(1 for r in rows if "WARN" in r["grade"])
        fail    = sum(1 for r in rows if "FAIL" in r["grade"])
        print(f"  총 {total}건 | PASS {passed} | WARN {warn} | FAIL {fail}")
        print(f"  SQL 생성률: {has_sql}/{total} ({has_sql/total:.0%})")
        print(f"  보고서 저장: {report_path}")
        print(f"{'='*70}")

        # FAIL 목록 출력
        fail_rows = [r for r in rows if "FAIL-SQL" in r["grade"]]
        if fail_rows:
            print("\n[few-shot 보완 필요 목록]")
            for r in fail_rows:
                print(f"  {r['id']} {r['category']} | {r['question']}")

        # 통과 기준 검증
        sql_rate = has_sql / total
        assert sql_rate >= PASS_RATE_THRESHOLD, (
            f"SQL 생성률 {sql_rate:.0%} < 기준 {PASS_RATE_THRESHOLD:.0%}\n"
            f"FAIL-SQL 목록: {[r['id'] for r in rows if 'FAIL-SQL' in r['grade']]}"
        )

"""Few-shot 수정/추가 적용 스크립트
실행: python scripts/apply_fewshot_fix.py
"""
import psycopg

DB_URL = "postgresql://hermesuser:hermesuser123!@115.68.223.220:5432/hermesdb"

# 수정 대상 (DELETE + RE-INSERT)
UPDATES = [
    {
        "title": "승진자 목록 조회",
        "content": (
            "올해 승진한 직원\n승진자 목록\n승진한 사람 몇 명\n승진 현황\n직급변경 직원\n"
            "- v_ai_employee JOIN v_ai_history\n"
            "- 승진 = ASSIGNMENT_TYPE_CODE = 직급변경 (실제 DB값)"
        ),
        "context_data": (
            "SQL:\n"
            "SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION, e.GRADE,\n"
            "       h.ASSIGNMENT_DATE, h.ASSIGNMENT_TYPE_CODE, h.ASSIGNMENT_REASON_CODE\n"
            "FROM v_ai_employee e\n"
            "JOIN v_ai_history h ON e.EMP_ID = h.EMP_ID\n"
            "WHERE e.WORK_STATUS = '재직'\n"
            "  AND h.ASSIGNMENT_TYPE_CODE IN ('직급변경', '직책변경')\n"
            "  AND h.ASSIGNMENT_REASON_CODE IN ('승격', '승진')\n"
            "  AND TO_CHAR(h.ASSIGNMENT_DATE, 'YYYY') = ':년도'\n"
            "ORDER BY h.ASSIGNMENT_DATE DESC\n\n"
            "패턴:\n"
            "- 승진 = ASSIGNMENT_TYPE_CODE IN ('직급변경', '직책변경') (DB 실제값)\n"
            "- 직급변경 + REASON='승격' (679건) + 직책변경 + REASON='승진' (104건)\n"
            "- LIKE '%승진%' 사용 금지\n"
            "- 승진 수: COUNT(DISTINCT h.EMP_ID)"
        ),
    },
    {
        "title": "발령유형별 통계 조회",
        "content": (
            "발령유형별 현황\n인사이동 통계\n발령 종류별 건수\n이동 승진 휴직 건수\n"
            "부서 이동 건수\n전보 현황"
        ),
        "context_data": (
            "SQL:\n"
            "SELECT ASSIGNMENT_TYPE_CODE,\n"
            "       COUNT(*) AS total_count,\n"
            "       COUNT(DISTINCT EMP_ID) AS emp_count\n"
            "FROM v_ai_history\n"
            "WHERE TO_CHAR(ASSIGNMENT_DATE, 'YYYY') = ':년도'\n"
            "GROUP BY ASSIGNMENT_TYPE_CODE\n"
            "ORDER BY total_count DESC\n\n"
            "패턴:\n"
            "- ASSIGNMENT_TYPE_CODE 실제값: 채용, 이동, 퇴직, 직책변경, 직급변경, 조직개편, 전출, 귀임, 파견, 겸직, 휴직, 복직, 직위변경\n"
            "- 자연어 매핑: 승진→직급변경, 전보/부서이동→이동, 전직→전출"
        ),
    },
    {
        "title": "승진이력 없는 장기 근속자 조회",
        "content": (
            "5년 이상 근무했는데 승진 안 한 직원\n승진 이력 없는 장기 근속자\n"
            "승진 누락 직원\n직급변경 이력 없는 재직자\n"
            "- LEFT JOIN + IS NULL 패턴"
        ),
        "context_data": (
            "SQL:\n"
            "SELECT e.EMP_NAME, e.DEPARTMENT, e.POSITION, e.GRADE,\n"
            "       e.HIRE_DATE, e.CAREER_YEARS\n"
            "FROM v_ai_employee e\n"
            "LEFT JOIN v_ai_history h\n"
            "  ON e.EMP_ID = h.EMP_ID\n"
            "  AND h.ASSIGNMENT_TYPE_CODE IN ('직급변경', '직책변경')\n"
            "  AND h.ASSIGNMENT_REASON_CODE IN ('승격', '승진')\n"
            "WHERE e.WORK_STATUS = '재직'\n"
            "  AND e.CAREER_YEARS >= 5\n"
            "  AND h.EMP_ID IS NULL\n"
            "ORDER BY e.CAREER_YEARS DESC\n\n"
            "패턴:\n"
            "- 승진 = ASSIGNMENT_TYPE_CODE IN ('직급변경', '직책변경') + REASON IN ('승격', '승진')\n"
            "- LIKE '%승진%' 사용 금지"
        ),
    },
    {
        "title": "배우자 보유 직원 수 조회",
        "content": (
            "배우자가 있는 직원 수\n기혼자 몇 명\n결혼한 사원 수\n기혼 직원 현황\n"
            "- v_ai_family (1:N) EXISTS 사용\n"
            "- RELATION 실제값: 처, 자녀, 형제자매"
        ),
        "context_data": (
            "SQL:\n"
            "SELECT COUNT(*) AS married_emp_count\n"
            "FROM v_ai_employee e\n"
            "WHERE e.WORK_STATUS = '재직'\n"
            "  AND EXISTS (\n"
            "    SELECT 1 FROM v_ai_family f\n"
            "    WHERE f.EMP_ID = e.EMP_ID\n"
            "      AND f.RELATION = '처'\n"
            "  )\n\n"
            "패턴:\n"
            "- 배우자 = RELATION = '처' (DB 실제값)\n"
            "- '배우자', '남편' 값은 DB에 없음\n"
            "- 자녀: RELATION = '자녀'"
        ),
    },
    {
        "title": "자격증 보유자 수 조회",
        "content": (
            "자격증 보유자 수\n자격증 보유한 직원\n자격증 있는 사원\n"
            "사내자격 보유 현황\n"
            "- v_ai_license (1:N) EXISTS 사용\n"
            "- LICENSE_TYPE 실제값: 사내자격, 사외자격"
        ),
        "context_data": (
            "SQL:\n"
            "SELECT COUNT(*) AS license_emp_count\n"
            "FROM v_ai_employee e\n"
            "WHERE e.WORK_STATUS = '재직'\n"
            "  AND EXISTS (\n"
            "    SELECT 1 FROM v_ai_license l\n"
            "    WHERE l.EMP_ID = e.EMP_ID\n"
            "  )\n\n"
            "패턴:\n"
            "- LICENSE_TYPE 실제값: 사내자격, 사외자격\n"
            "- '국가자격', '민간자격' 값은 DB에 없음"
        ),
    },
]

# 신규 추가
NEW_INSERTS = [
    {
        "title": "교육 유형별 통계 조회",
        "content": (
            "교육 유형별 현황\n필수교육 선택교육 통계\n교육 유형별 수료 건수\n교육유형 분포\n"
            "- v_ai_training TRAINING_TYPE GROUP BY\n- 실제값: 선택, 필수"
        ),
        "context_data": (
            "SQL:\n"
            "SELECT t.TRAINING_TYPE,\n"
            "       COUNT(*) AS total_count,\n"
            "       COUNT(DISTINCT t.EMP_ID) AS emp_count,\n"
            "       SUM(CASE WHEN t.COMPLETION_STATUS = '수료' THEN 1 ELSE 0 END) AS completed_count\n"
            "FROM v_ai_training t\n"
            "JOIN v_ai_employee e ON e.EMP_ID = t.EMP_ID\n"
            "WHERE e.WORK_STATUS = '재직'\n"
            "GROUP BY t.TRAINING_TYPE\n"
            "ORDER BY total_count DESC\n\n"
            "패턴:\n"
            "- TRAINING_TYPE 실제값: 선택, 필수\n"
            "- '집합교육', '사이버교육' 값은 DB에 없음"
        ),
    },
    {
        "title": "부서별 인사이동 건수 조회",
        "content": (
            "부서별 인사이동 건수\n부서 간 전보 빈도\n부서 이동 현황\n전보 건수\n"
            "- 인사이동/전보 = ASSIGNMENT_TYPE_CODE = 이동 (DB 실제값)"
        ),
        "context_data": (
            "SQL:\n"
            "SELECT e.DEPARTMENT,\n"
            "       COUNT(*) AS move_count,\n"
            "       COUNT(DISTINCT e.EMP_ID) AS emp_count\n"
            "FROM v_ai_employee e\n"
            "JOIN v_ai_history h ON e.EMP_ID = h.EMP_ID\n"
            "WHERE e.WORK_STATUS = '재직'\n"
            "  AND h.ASSIGNMENT_TYPE_CODE = '이동'\n"
            "GROUP BY e.DEPARTMENT\n"
            "ORDER BY move_count DESC\n\n"
            "패턴:\n"
            "- 인사이동/전보 = ASSIGNMENT_TYPE_CODE = '이동' (DB 실제값)\n"
            "- '전보' 값은 DB에 없음"
        ),
    },
    {
        "title": "평가명별 통계 조회",
        "content": (
            "평가명별 현황\n역량평가 업적평가 통계\n인사평가 종류별 결과\n평가 유형별 분포\n"
            "- v_ai_feedback APPR_NM GROUP BY"
        ),
        "context_data": (
            "SQL:\n"
            "SELECT f.APPR_NM,\n"
            "       COUNT(*) AS eval_count,\n"
            "       COUNT(DISTINCT f.EMP_ID) AS emp_count,\n"
            "       ROUND(AVG(CASE WHEN f.APPR_SCORE > 0 THEN f.APPR_SCORE END), 1) AS avg_score\n"
            "FROM v_ai_feedback f\n"
            "JOIN v_ai_employee e ON e.EMP_ID = f.EMP_ID\n"
            "WHERE e.WORK_STATUS = '재직'\n"
            "GROUP BY f.APPR_NM\n"
            "ORDER BY eval_count DESC\n\n"
            "패턴:\n"
            "- APPR_NM 실제값: 역량평가, 종합평가, 업적평가, 업적평가 상반기, 업적평가 하반기, 다면평가, 리더십평가\n"
            "- '연간인사평가', '수시평가' 값은 DB에 없음"
        ),
    },
    {
        "title": "인사발령 유형 매핑 가이드",
        "content": (
            "인사이동 유형\n발령 종류\n승진 전보 휴직\n부서이동 전출 파견\n직급변경 직책변경"
        ),
        "context_data": (
            "SQL:\n"
            "SELECT ASSIGNMENT_TYPE_CODE, ASSIGNMENT_REASON_CODE,\n"
            "       COUNT(*) AS cnt\n"
            "FROM v_ai_history\n"
            "GROUP BY ASSIGNMENT_TYPE_CODE, ASSIGNMENT_REASON_CODE\n"
            "ORDER BY cnt DESC\n\n"
            "패턴:\n"
            "- 자연어→DB값 매핑 (★ 중요):\n"
            "  승진 → ASSIGNMENT_TYPE_CODE IN ('직급변경', '직책변경') AND REASON IN ('승격', '승진')\n"
            "        직급변경(REASON='승격') 679건 + 직책변경(REASON='승진') 104건\n"
            "  전보/부서이동 → ASSIGNMENT_TYPE_CODE = '이동'\n"
            "  전직 → ASSIGNMENT_TYPE_CODE = '전출'\n"
            "  파견 → ASSIGNMENT_TYPE_CODE = '파견'\n"
            "  휴직 → ASSIGNMENT_TYPE_CODE = '휴직'\n"
            "  복직 → ASSIGNMENT_TYPE_CODE = '복직'\n"
            "  퇴직 → ASSIGNMENT_TYPE_CODE = '퇴직'\n"
            "- LIKE '%승진%' 사용 금지\n"
            "- LIKE '%전보%' 사용 금지"
        ),
    },
    {
        "title": "가족관계 조회 가이드",
        "content": (
            "배우자 있는 직원\n자녀 있는 직원\n가족 현황\n부양가족 수"
        ),
        "context_data": (
            "SQL:\n"
            "SELECT f.RELATION,\n"
            "       COUNT(*) AS family_count,\n"
            "       COUNT(DISTINCT f.EMP_ID) AS emp_count\n"
            "FROM v_ai_family f\n"
            "JOIN v_ai_employee e ON e.EMP_ID = f.EMP_ID\n"
            "WHERE e.WORK_STATUS = '재직'\n"
            "GROUP BY f.RELATION\n"
            "ORDER BY family_count DESC\n\n"
            "패턴:\n"
            "- 자연어→DB값 매핑:\n"
            "  배우자/남편/아내 → RELATION = '처'\n"
            "  자녀/아들/딸 → RELATION = '자녀'\n"
            "  형제/자매 → RELATION = '형제자매'\n"
            "- '배우자', '남편', '부', '모' 값은 DB에 없음"
        ),
    },
]


def main():
    conn = psycopg.connect(DB_URL)
    cur = conn.cursor()

    # 수정 대상 DELETE + INSERT
    for item in UPDATES:
        cur.execute(
            "DELETE FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action' AND title = %s",
            (item["title"],),
        )
        print(f"DELETE [{item['title']}] rows={cur.rowcount}")

        cur.execute(
            "INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            ("default", "rag_action", item["title"], "query_example", "ko", item["content"], item["context_data"]),
        )
        print(f"INSERT [{item['title']}] ok")

    # 신규 추가 (중복 체크)
    for item in NEW_INSERTS:
        cur.execute(
            "SELECT COUNT(*) FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action' AND title = %s",
            (item["title"],),
        )
        exists = cur.fetchone()[0]
        if exists:
            cur.execute(
                "DELETE FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action' AND title = %s",
                (item["title"],),
            )
            print(f"DELETE (기존) [{item['title']}] rows={cur.rowcount}")

        cur.execute(
            "INSERT INTO tb_docs (tenant_id, usage_type, title, doc_type, language, content, context_data) "
            "VALUES (%s, %s, %s, %s, %s, %s, %s)",
            ("default", "rag_action", item["title"], "query_example", "ko", item["content"], item["context_data"]),
        )
        print(f"INSERT [{item['title']}] ok")

    conn.commit()

    # 검증
    cur.execute("SELECT COUNT(*) FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action'")
    total = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM tb_docs WHERE doc_type = 'query_example' AND usage_type = 'rag_action' AND indexed = true")
    indexed = cur.fetchone()[0]

    print(f"\n총 few-shot: {total}건 (임베딩됨: {indexed}건)")
    print("※ 수정/추가된 few-shot은 indexed=false → 임베딩 재생성 필요")

    conn.close()


if __name__ == "__main__":
    main()

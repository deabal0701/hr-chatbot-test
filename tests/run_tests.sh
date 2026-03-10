#!/bin/bash
# ═══════════════════════════════════════════════════════
# MUREUM API 통합 테스트 실행 스크립트
#
# 사용법:
#   bash tests/run_tests.sh              # 전체 실행
#   bash tests/run_tests.sh auth         # 특정 주제만
#   bash tests/run_tests.sh health auth  # 복수 주제
#
# 환경변수:
#   TEST_BASE_URL  서버 URL (기본: http://localhost:19090)
#   TEST_ADMIN_ID  관리자 ID (기본: admin)
#   TEST_ADMIN_PW  관리자 PW (기본: Win1234!)
#
# 사전 조건:
#   1. pip install pytest httpx
#   2. 서버가 실행 중이어야 함
# ═══════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
export TEST_BASE_URL="${TEST_BASE_URL:-http://localhost:19090}"

echo "════════════════════════════════════════════"
echo "  MUREUM API Integration Tests"
echo "  Server: $TEST_BASE_URL"
echo "════════════════════════════════════════════"

# 서버 연결 확인
echo ""
echo "[1/3] 서버 연결 확인..."
if ! curl -s --max-time 5 "$TEST_BASE_URL/health" > /dev/null 2>&1; then
    echo "  ERROR: 서버에 연결할 수 없습니다 ($TEST_BASE_URL)"
    echo "  서버를 먼저 실행하세요:"
    echo "    uvicorn app.main:app --host 0.0.0.0 --port 19090"
    exit 1
fi
echo "  OK: 서버 연결 성공"

# pytest 설치 확인
echo ""
echo "[2/3] 의존성 확인..."
if ! python -c "import pytest" 2>/dev/null; then
    echo "  pytest 미설치 → 설치 중..."
    pip install pytest httpx
fi
echo "  OK: pytest, httpx 준비 완료"

# 테스트 실행
echo ""
echo "[3/3] 테스트 실행..."
echo "════════════════════════════════════════════"

# 주제 매핑
declare -A TOPIC_MAP=(
    [health]="test_01_health.py"
    [auth]="test_02_auth.py"
    [tenants]="test_03_tenants.py"
    [roles]="test_04_roles.py"
    [menus]="test_05_menus.py"
    [users]="test_06_users.py"
    [codes]="test_07_codes.py"
    [settings]="test_08_settings.py"
    [documents]="test_09_documents.py"
    [search]="test_10_search.py"
    [dashboard]="test_11_personal_dashboard.py"
    [ratelimit]="test_12_rate_limit.py"
)

cd "$PROJECT_DIR"

if [ $# -eq 0 ]; then
    # 전체 실행
    python -m pytest tests/ -v --tb=short -x 2>&1
else
    # 선택 실행
    TEST_FILES=""
    for topic in "$@"; do
        if [ -n "${TOPIC_MAP[$topic]}" ]; then
            TEST_FILES="$TEST_FILES tests/${TOPIC_MAP[$topic]}"
        else
            echo "  알 수 없는 주제: $topic"
            echo "  사용 가능: ${!TOPIC_MAP[*]}"
            exit 1
        fi
    done
    python -m pytest $TEST_FILES -v --tb=short 2>&1
fi

echo ""
echo "════════════════════════════════════════════"
echo "  테스트 완료"
echo "════════════════════════════════════════════"

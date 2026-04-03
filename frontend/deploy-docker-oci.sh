#!/usr/bin/env bash
set -euo pipefail

# ============================================================
# win-AI Frontend Docker 배포 스크립트 (OCI VM)
# ============================================================
#
# 사용법: cd frontend && bash deploy-docker-oci.sh
#
# [설정 변경 시 확인 항목]
#   - REMOTE_HOST    : OCI VM Public IP
#
# ============================================================

# -------------------------------
# OCI 배포 환경 설정
# -------------------------------
export DEPLOY_TARGET="remote"
export REMOTE_USER="winai"
export REMOTE_HOST="161.33.226.214"
export REMOTE_PORT="22"
export REMOTE_DIR="/home/winai/winai/frontend"
export DOCKER_IMAGE_NAME="winai-frontend"
export DOCKER_CONTAINER_NAME="winai-frontend"
export DOCKER_NETWORK_NAME="winai-network"
export ENV_FILE=".env.docker"
export DOCKERFILE="Dockerfile"
export NGINX_CONF="nginx.oci.conf"
export FRONTEND_PORT="19080"
export SSH_KEY="$HOME/.ssh/oci_winai.key"

# ============================================================
# 기본 설정 (환경변수가 없을 때 사용)
# ============================================================

DEPLOY_TARGET="${DEPLOY_TARGET:-remote}"
REMOTE_USER="${REMOTE_USER:-winai}"
REMOTE_HOST="${REMOTE_HOST:-<OCI_PUBLIC_IP>}"
REMOTE_PORT="${REMOTE_PORT:-22}"
REMOTE_DIR="${REMOTE_DIR:-/home/winai/winai/frontend}"
LOCAL_ROOT="${LOCAL_ROOT:-$(cd "$(dirname "$0")" && pwd)}"
DOCKER_IMAGE_NAME="${DOCKER_IMAGE_NAME:-winai-frontend}"
DOCKER_CONTAINER_NAME="${DOCKER_CONTAINER_NAME:-winai-frontend}"
DOCKER_NETWORK_NAME="${DOCKER_NETWORK_NAME:-winai-network}"
ENV_FILE="${ENV_FILE:-.env.docker}"
DOCKERFILE="${DOCKERFILE:-Dockerfile}"
NGINX_CONF="${NGINX_CONF:-nginx.oci.conf}"
FRONTEND_PORT="${FRONTEND_PORT:-19080}"
SSH_KEY="${SSH_KEY:-$HOME/.ssh/oci_winai.key}"

# ============================================================
# 이하 코드는 수정하지 마세요
# ============================================================

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}win-AI Frontend Docker 배포 시작 (OCI)${NC}"
echo -e "${GREEN}Target: ${REMOTE_HOST}${NC}"
echo -e "${GREEN}Environment: ${ENV_FILE}${NC}"
echo -e "${GREEN}========================================${NC}"

# ================= SSH 설정 =================
setup_ssh() {
    echo -e "\n${CYAN}[SSH] SSH 연결 설정 중...${NC}"

    if [ ! -f "$SSH_KEY" ]; then
        echo -e "${RED}ERROR: SSH 키가 없습니다: $SSH_KEY${NC}"
        echo "OCI SSH 키를 배치하세요: cp /path/to/oci_private_key $SSH_KEY"
        exit 1
    fi

    # SSH Agent 설정 (passphrase를 1회만 입력하도록)
    if [ -z "${SSH_AUTH_SOCK:-}" ]; then
        eval "$(ssh-agent -s)" > /dev/null 2>&1
    fi

    if ! ssh-add -l 2>/dev/null | grep -q "$(ssh-keygen -lf "$SSH_KEY" 2>/dev/null | awk '{print $2}')"; then
        ssh-add "$SSH_KEY"
    fi

    SSH_CMD="ssh -p $REMOTE_PORT -o StrictHostKeyChecking=accept-new -o LogLevel=ERROR"
    SCP_CMD="scp -P $REMOTE_PORT -o StrictHostKeyChecking=accept-new -o LogLevel=ERROR"

    echo -e "${GREEN}[OK] SSH 설정 완료${NC}"
}

# ================= 환경 검증 =================
validate_environment() {
    echo -e "\n${CYAN}[CHECK] 환경 검증 중...${NC}"

    # 디렉토리 존재 확인
    if [ ! -d "$LOCAL_ROOT" ]; then
        echo -e "${RED}ERROR: 로컬 경로가 존재하지 않습니다: $LOCAL_ROOT${NC}"
        exit 1
    fi

    cd "$LOCAL_ROOT"

    # 환경 파일 확인
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${RED}ERROR: 환경 파일이 없습니다: $ENV_FILE${NC}"
        exit 1
    fi

    # 필수 파일 확인
    if [ ! -f "package.json" ]; then
        echo -e "${RED}ERROR: package.json이 없습니다.${NC}"
        exit 1
    fi

    if [ ! -f "$DOCKERFILE" ]; then
        echo -e "${RED}ERROR: Dockerfile이 없습니다: $DOCKERFILE${NC}"
        exit 1
    fi

    if [ ! -f "$NGINX_CONF" ]; then
        echo -e "${RED}ERROR: Nginx 설정 파일이 없습니다: $NGINX_CONF${NC}"
        exit 1
    fi

    echo -e "${GREEN}[OK] 환경 검증 완료${NC}"
}

# ================= 원격 파일 전송 =================
transfer_files() {
    echo -e "\n${CYAN}[TRANSFER] 파일 전송 중...${NC}"

    # 원격 디렉토리 준비
    $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" "mkdir -p $REMOTE_DIR"

    # tar로 압축 전송 (불필요 파일 제외, 1개 스트림으로 전송)
    echo "소스 코드 압축 전송 중..."
    tar czf - \
        --exclude='node_modules' \
        --exclude='.git' \
        "$DOCKERFILE" "$NGINX_CONF" "$ENV_FILE" \
        package*.json vite.config.js index.html \
        src/ public/ \
    | $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" "cd $REMOTE_DIR && tar xzf -"

    # Dockerfile은 nginx.conf를 하드코딩하므로, nginx.oci.conf → nginx.conf로 rename
    echo "Nginx 설정 파일 rename 중..."
    $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" "cp $REMOTE_DIR/$NGINX_CONF $REMOTE_DIR/nginx.conf"

    echo -e "${GREEN}[OK] 파일 전송 완료${NC}"
}

# ================= Docker 이미지 빌드 =================
build_docker_image() {
    echo -e "\n${CYAN}[BUILD] Docker 이미지 빌드 중...${NC}"

    $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" "bash -c '
    set -e
    cd $REMOTE_DIR

    # 기존 이미지 백업
    if docker images | grep -q \"^$DOCKER_IMAGE_NAME\\\\s\"; then
        echo \"기존 이미지 백업 중...\"
        docker tag \"$DOCKER_IMAGE_NAME:latest\" \"$DOCKER_IMAGE_NAME:backup\" 2>/dev/null || true
    fi

    # 새 이미지 빌드
    echo \"Docker 이미지 빌드 시작...\"
    if docker build -f \"$DOCKERFILE\" --build-arg ENV_FILE=\"$ENV_FILE\" -t \"$DOCKER_IMAGE_NAME:latest\" .; then
        echo \"[OK] Docker 이미지 빌드 완료\"
        docker images | grep \"$DOCKER_IMAGE_NAME\"
    else
        echo \"ERROR: Docker 이미지 빌드 실패\"
        exit 1
    fi
    '"
    echo -e "${GREEN}[OK] Docker 이미지 빌드 완료${NC}"
}

# ================= 컨테이너 배포 =================
deploy_container() {
    echo -e "\n${CYAN}[DEPLOY] 컨테이너 배포 중...${NC}"

    $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" "bash -c '
    set -e

    # 기존 컨테이너 정리
    if docker ps -a | grep -q \"$DOCKER_CONTAINER_NAME\"; then
        echo \"기존 컨테이너 중단 및 제거 중...\"
        docker stop \"$DOCKER_CONTAINER_NAME\" 2>/dev/null || true
        docker rm \"$DOCKER_CONTAINER_NAME\" 2>/dev/null || true
    fi

    # 네트워크 생성 (없는 경우)
    docker network ls | grep -q \"$DOCKER_NETWORK_NAME\" || {
        echo \"Docker 네트워크 생성: $DOCKER_NETWORK_NAME\"
        docker network create \"$DOCKER_NETWORK_NAME\" || true
    }

    # 새 컨테이너 시작
    echo \"새 컨테이너 시작: $DOCKER_CONTAINER_NAME\"
    docker run -d \\
        --name \"$DOCKER_CONTAINER_NAME\" \\
        --network \"$DOCKER_NETWORK_NAME\" \\
        -p 80:80 \\
        -p 443:443 \\
        -p \"$FRONTEND_PORT:19080\" \\
        -v /etc/letsencrypt:/etc/letsencrypt:ro \\
        --restart unless-stopped \\
        \"$DOCKER_IMAGE_NAME:latest\"
    '"

    echo -e "${GREEN}[OK] 컨테이너 배포 완료${NC}"
}

# ================= 배포 검증 =================
verify_deployment() {
    echo -e "\n${CYAN}[VERIFY] 배포 검증 중...${NC}"

    # 컨테이너 기동 대기
    echo "애플리케이션 기동 대기 중..."
    sleep 5

    # 원격 컨테이너 상태 확인
    echo "컨테이너 상태:"
    $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" "docker ps --filter 'name=$DOCKER_CONTAINER_NAME'"

    # 헬스체크
    echo -e "\n애플리케이션 상태 확인:"
    if curl -sf "http://$REMOTE_HOST:$FRONTEND_PORT/health" 2>/dev/null; then
        echo -e "\n${GREEN}[OK] Health check 성공${NC}"
    else
        echo -e "${YELLOW}[WARN] Health check 실패 (서버 기동 중일 수 있음)${NC}"
    fi

    if curl -sf "http://$REMOTE_HOST:$FRONTEND_PORT/" 2>/dev/null | grep -q '<!DOCTYPE html>'; then
        echo -e "${GREEN}[OK] 웹 페이지 로딩 성공${NC}"
    else
        echo -e "${YELLOW}[WARN] 웹 페이지 로딩 실패 (서버 기동 중일 수 있음)${NC}"
    fi

    # 컨테이너 로그 확인
    echo -e "\n컨테이너 최근 로그:"
    $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" "docker logs --tail 10 '$DOCKER_CONTAINER_NAME'"
}

# ================= 정리 작업 =================
cleanup() {
    echo -e "\n${CYAN}[CLEANUP] 정리 작업 중...${NC}"

    $SSH_CMD "$REMOTE_USER@$REMOTE_HOST" "bash -c '
    docker image prune -f --filter \"until=168h\" 2>/dev/null || true
    docker rmi \"$DOCKER_IMAGE_NAME:backup\" 2>/dev/null || true
    '"

    echo -e "${GREEN}[OK] 정리 완료${NC}"
}

# ================= 메인 실행 =================
main() {
    setup_ssh
    validate_environment
    transfer_files
    build_docker_image
    deploy_container
    verify_deployment
    cleanup

    echo -e "\n${GREEN}========================================${NC}"
    echo -e "${GREEN}win-AI Frontend Docker 배포 완료! (OCI)${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}Frontend URL:  http://$REMOTE_HOST:$FRONTEND_PORT${NC}"
    echo -e "${GREEN}Health Check:  http://$REMOTE_HOST:$FRONTEND_PORT/health${NC}"
    echo ""
    echo -e "${BLUE}관리 명령어:${NC}"
    echo -e "  ${YELLOW}컨테이너 로그:${NC}     ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST 'docker logs -f $DOCKER_CONTAINER_NAME'"
    echo -e "  ${YELLOW}컨테이너 상태:${NC}     ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST 'docker ps'"
    echo -e "  ${YELLOW}컨테이너 재시작:${NC}   ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST 'docker restart $DOCKER_CONTAINER_NAME'"
    echo -e "  ${YELLOW}컨테이너 중단:${NC}     ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST 'docker stop $DOCKER_CONTAINER_NAME'"
    echo ""
    echo -e "${CYAN}배포 정보:${NC}"
    echo -e "  - 배포 대상: $REMOTE_HOST"
    echo -e "  - 환경 파일: $ENV_FILE"
    echo -e "  - Dockerfile: $DOCKERFILE"
    echo -e "  - Nginx 설정: $NGINX_CONF"
    echo -e "  - 이미지: $DOCKER_IMAGE_NAME:latest"
    echo -e "  - 컨테이너: $DOCKER_CONTAINER_NAME"
    echo -e "  - 네트워크: $DOCKER_NETWORK_NAME"
    echo -e "  - 포트: $FRONTEND_PORT"
}

# 스크립트 시작점
main "$@"

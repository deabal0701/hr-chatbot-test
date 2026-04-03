#!/usr/bin/env bash
set -euo pipefail

# ===================== 사용자 설정 =====================
REMOTE_USER="winai"
REMOTE_HOST="161.33.226.214"
REMOTE_PORT=22   # 서버 SSH 포트
# =======================================================

echo "== OCI VM SSH 키 준비 및 공개키 배포 (port ${REMOTE_PORT}) =="

# 1) 사용할 키: OCI 전용 키
KEY="${HOME}/.ssh/oci_winai.key"

# 2) 키가 없으면 생성
if [ ! -f "$KEY" ]; then
  mkdir -p "${HOME}/.ssh"
  chmod 700 "${HOME}/.ssh"
  echo "키가 없어 새로 생성합니다: $KEY (rsa 4096)"
  ssh-keygen -t rsa -b 4096 -C "${REMOTE_USER}@${REMOTE_HOST}" -f "$KEY"
fi

PUB="${KEY}.pub"
if [ ! -f "$PUB" ]; then
  echo "ERROR: 공개키 파일을 찾을 수 없습니다: $PUB" >&2
  exit 1
fi

# 3) ssh-agent 실행/등록
if [ -z "${SSH_AUTH_SOCK:-}" ]; then
  echo "ssh-agent 시작"
  eval "$(ssh-agent -s)"
fi

# fingerprint 기준으로 중복 등록 방지
if ! ssh-add -l 2>/dev/null | grep -q "$(ssh-keygen -lf "$KEY" | awk '{print $2}')" ; then
  echo "ssh-agent에 키 등록: $KEY"
  ssh-add "$KEY"
else
  echo "ssh-agent에 키가 이미 등록되어 있습니다."
fi

# 4) 원격 서버에 공개키 설치 (최초엔 패스워드 요구될 수 있음)
SSH_OPTS="-o StrictHostKeyChecking=accept-new -o LogLevel=ERROR -p ${REMOTE_PORT}"
echo "원격 서버에 공개키 설치 중 (${REMOTE_USER}@${REMOTE_HOST}:${REMOTE_PORT})..."
cat "$PUB" \
| ssh ${SSH_OPTS} "${REMOTE_USER}@${REMOTE_HOST}" \
  "mkdir -p ~/.ssh && chmod 700 ~/.ssh \
   && touch ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys \
   && cat >> ~/.ssh/authorized_keys"

# 5) 접속 테스트
echo "접속 테스트..."
ssh -i "$KEY" ${SSH_OPTS} "${REMOTE_USER}@${REMOTE_HOST}" 'echo "SSH key auth OK on $(hostname)"'

# 6) SSH config 가이드
CFG="${HOME}/.ssh/config"
echo
echo "완료! 편의를 위해 ${CFG} 에 아래 항목을 추가하면 됩니다:"
cat <<EOF
Host oci-winai
  HostName ${REMOTE_HOST}
  User ${REMOTE_USER}
  Port ${REMOTE_PORT}
  IdentityFile ${KEY}
  StrictHostKeyChecking accept-new
EOF

echo
echo "예) ssh oci-winai"
echo "예) scp file.txt oci-winai:~"
echo "끝."

#!/usr/bin/env bash
# 필수 도구 점검 — 없는 도구는 설치 방법을 한국어로 안내한다.
set -u
MISSING=0

check() {
  local cmd="$1" hint="$2"
  if command -v "$cmd" >/dev/null 2>&1; then
    echo "OK    $cmd"
  else
    echo "없음  $cmd — 설치: $hint"
    MISSING=$((MISSING + 1))
  fi
}

check git     "https://git-scm.com/downloads"
check node    "https://nodejs.org (LTS 20 이상) 또는 'curl https://get.volta.sh | bash && volta install node'"
check pnpm    "'npm install -g pnpm' 또는 'volta install pnpm'"
check python3 "Python 3.11 이상 — Mac: 'brew install python', WSL: 'sudo apt install python3'"
check uv      "'curl -LsSf https://astral.sh/uv/install.sh | sh'"
check docker  "Docker Desktop — https://www.docker.com/products/docker-desktop"

if command -v docker >/dev/null 2>&1 && ! docker info >/dev/null 2>&1; then
  echo "주의  Docker가 설치돼 있지만 실행 중이 아닙니다 — Docker Desktop을 켜 주세요."
  MISSING=$((MISSING + 1))
fi

if [ "$MISSING" -gt 0 ]; then
  echo ""
  echo "$MISSING 개 항목을 먼저 준비해야 합니다."
  exit 1
fi
echo "모든 도구 준비 완료"

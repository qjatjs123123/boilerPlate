#!/usr/bin/env bash
# 워크트리 환경 준비 — vibe-build 의 개발 서브에이전트(backend-dev·frontend-dev)가 워크트리 루트에서 실행한다.
# 워크트리에는 git 이 추적하지 않는 파일(env·가상환경·node_modules)이 없으므로 새로 만든다. DB 는 메인과 공유.
set -euo pipefail

ROOT=$(git rev-parse --show-toplevel)
cd "$ROOT"

# 메인 폴더에서 실행하면 메인 환경을 건드리게 되므로 거부
if [ "$(git rev-parse --git-dir)" = "$(git rev-parse --git-common-dir)" ]; then
  echo "워크트리가 아니다 — 메인 폴더에서는 make setup 을 쓴다." >&2
  exit 1
fi

# env 파일: 메인 폴더 것을 그대로 복사 — DB 포트·계정 등 로컬 설정을 맞춰야 메인 DB 를 공유한다.
# 메인에도 없으면 예시에서 만든다. (이미 있으면 유지)
MAIN=$(dirname "$(git rev-parse --path-format=absolute --git-common-dir)")
copy_env() { # $1=경로  $2=예시 경로
  [ -f "$1" ] && return 0
  if [ -f "$MAIN/$1" ]; then cp "$MAIN/$1" "$1"; else cp "$2" "$1"; fi
}
copy_env backend/.env backend/.env.example
copy_env frontend/.env.local frontend/.env.example

# 백엔드: editable 설치가 메인 폴더 코드를 가리키지 않도록 워크트리에서 새로 설치
(cd backend && uv venv --allow-existing -q && uv pip install -q -e ".[dev]")

# 프론트: pnpm 저장소를 재사용하므로 빠르다
(cd frontend && pnpm install --frozen-lockfile --prefer-offline --silent)

echo "✅ 워크트리 환경 준비 완료: $ROOT"

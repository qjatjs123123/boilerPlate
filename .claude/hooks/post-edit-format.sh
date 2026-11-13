#!/usr/bin/env bash
# PostToolUse(Edit|Write|MultiEdit) — 방금 수정한 파일만 자동 포맷·자동 수정한다. 실패해도 막지 않는다.
source "$(dirname "$0")/_lib.sh"
file=$(python3 -c 'import json,sys; print(json.load(sys.stdin).get("tool_input",{}).get("file_path",""))' 2>/dev/null)
[ -f "$file" ] || exit 0
# 파일이 속한 루트 — 메인 폴더 또는 워크트리(.claude/worktrees/<이름>)의 도구를 쓴다
case "$file" in
  "$ROOT"/*/backend/*.py | "$ROOT"/backend/*.py)
    base="${file%/backend/*}"
    py="$base/backend/.venv/bin"
    [ -x "$py/ruff" ] && { "$py/ruff" check --fix -q "$file"; "$py/ruff" format -q "$file"; } >/dev/null 2>&1 ;;
  "$ROOT"/*/frontend/*.ts | "$ROOT"/*/frontend/*.tsx | "$ROOT"/frontend/*.ts | "$ROOT"/frontend/*.tsx)
    base="${file%/frontend/*}"
    [ -d "$base/frontend/node_modules" ] && (cd "$base/frontend" && pnpm -s exec eslint --fix "$file") >/dev/null 2>&1 ;;
esac
exit 0

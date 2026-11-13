#!/usr/bin/env bash
# 훅 공용 함수 — 프로젝트 루트와 환경 준비 상태 판별
ROOT="${CLAUDE_PROJECT_DIR:-$(git rev-parse --show-toplevel 2>/dev/null || pwd)}"
HARNESS_DIR="$ROOT/.harness"

# 준비 안 된 항목을 공백 구분으로 출력 (모두 준비되면 빈 문자열)
missing_setup() {
  local m=""
  [ -f "$ROOT/backend/.env" ] || m="$m backend/.env"
  [ -f "$ROOT/frontend/.env.local" ] || m="$m frontend/.env.local"
  [ -x "$ROOT/backend/.venv/bin/python" ] || m="$m backend/.venv"
  [ -d "$ROOT/frontend/node_modules" ] || m="$m frontend/node_modules"
  echo "$m"
}

db_running() {
  (cd "$ROOT/backend" && docker compose ps --status running -q postgres 2>/dev/null | grep -q .)
}

# run 이 "지금 작업 중"으로 인정되는 기간 — 이보다 오래 손대지 않은 미완료 run 은 게이트를 미루거나 끄지 못한다
RUN_FRESH_MIN=${RUN_FRESH_MIN:-1440}

_fresh() { [ -n "$(find "$1" -maxdepth 0 -mmin "-$RUN_FRESH_MIN" 2>/dev/null)" ]; }

# 사용자 답을 기다리며 멈춘 run (PAUSED 파일 있음, DONE 없음, 최근) — 'slug: 사유' 한 줄씩
paused_runs() {
  [ -d "$HARNESS_DIR/runs" ] || return 0
  for d in "$HARNESS_DIR"/runs/*/; do
    [ -f "$d/PAUSED" ] || continue
    [ -f "$d/DONE" ] && continue
    _fresh "$d/PAUSED" || continue
    echo "$(basename "$d"): $(head -1 "$d/PAUSED")"
  done
}

# 진행 중(미완료) harness run 슬러그 목록 — state.md 가 최근 RUN_FRESH_MIN 분 안에 갱신된 것만
active_runs() {
  [ -d "$HARNESS_DIR/runs" ] || return 0
  for d in "$HARNESS_DIR"/runs/*/; do
    [ -f "$d/state.md" ] || continue
    [ -f "$d/DONE" ] && continue
    _fresh "$d/state.md" || continue
    basename "$d"
  done
}

# 오래 방치된 미완료 run (DONE 없음, state.md 가 RUN_FRESH_MIN 분 넘게 그대로) — 정리·재개 안내용
stale_runs() {
  [ -d "$HARNESS_DIR/runs" ] || return 0
  for d in "$HARNESS_DIR"/runs/*/; do
    [ -f "$d/state.md" ] || continue
    [ -f "$d/DONE" ] && continue
    _fresh "$d/state.md" && continue
    basename "$d"
  done
}

# 품질 게이트 지문 — 기준 커밋($1) 이후 backend·frontend 변경(커밋 + 미커밋 + 새 파일 이름·내용)
gate_fingerprint() {
  local base=$1
  {
    git diff "$base" -- backend frontend
    git ls-files --others --exclude-standard -z -- backend frontend \
      | while IFS= read -r -d '' f; do printf '%s\n' "$f"; cat "$f" 2>/dev/null; done
  } | sha1sum | cut -d' ' -f1
}

# docs/backend/DOMAIN-MAP.md 「## 개념」 표 → '개념(저장 위치), ...' 한 줄 (없으면 빈 문자열)
domain_map_summary() {
  local map="$ROOT/docs/backend/DOMAIN-MAP.md"
  [ -f "$map" ] || return 0
  awk -F'|' '
    /^## / { in_concepts = ($0 ~ /^## 개념/); next }
    in_concepts && /^\|/ && $2 !~ /^ *(개념|-+) *$/ {
      name = $2; where = $4
      gsub(/^ +| +$|`/, "", name); gsub(/^ +| +$|`/, "", where)
      out = out (out ? ", " : "") name "(" where ")"
    }
    END { print out }
  ' "$map"
}

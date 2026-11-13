#!/usr/bin/env bash
# Stop — Claude가 작업을 끝내려 할 때 정적 검증 + 테스트 누락 검사 + (화면 변경 시) e2e 를 강제한다.
# 코드가 바뀌었는데 검증을 통과하지 못하면 종료를 막고(decision: block) 에러를 돌려줘 계속 고치게 한다.
source "$(dirname "$0")/_lib.sh"
cd "$ROOT" || exit 0

MAX_BLOCKS=6
COUNT_FILE="$HARNESS_DIR/gate-count"
PASS_FILE="$HARNESS_DIR/gate-pass"
PAUSED_FP_FILE="$HARNESS_DIR/gate-paused-fp"   # PAUSED 로 한 번 넘겨 준 변경의 지문 — 같은 변경으로 두 번은 못 넘긴다
LOG_FILE="$HARNESS_DIR/gate-last.log"
mkdir -p "$HARNESS_DIR"

# python3 가 없으면 결과를 보고할 수 없고 커밋 규칙 훅도 동작하지 않는다 — 조용히 넘어가지 않고 알린다
if ! command -v python3 >/dev/null 2>&1; then
  printf '{"systemMessage": "⚠️ python3 가 없어 품질 검사·커밋 규칙 검사를 할 수 없습니다. 사용자에게 python3 설치(make doctor 안내)를 요청하라."}\n'
  exit 0
fi

emit() { # $1=json-key  $2=message → JSON 출력
  python3 -c 'import json,sys; print(json.dumps({sys.argv[1]: sys.argv[2], **({"decision": "block"} if sys.argv[1]=="reason" else {})}, ensure_ascii=False))' "$1" "$2"
}

# 1. 세션 시작 이후 바뀐 코드 파일 (커밋된 것 포함 — 커밋으로 게이트를 우회할 수 없게)
#    backend/, frontend/ 만 대상. 기준 커밋은 SessionStart 훅이 .harness/session-base 에 기록한다.
base=$(cat "$HARNESS_DIR/session-base" 2>/dev/null)
git cat-file -e "${base:-x}^{commit}" 2>/dev/null || base=HEAD
changed=$( { git diff --name-only "$base" -- backend frontend; git ls-files --others --exclude-standard -- backend frontend; } 2>/dev/null | sort -u)
[ -z "$changed" ] && exit 0

# 2. 이미 이 상태로 통과했으면 재검사하지 않음 (단순 질문 턴에서 반복 실행 방지)
fingerprint=$(gate_fingerprint "$base")
[ -f "$PASS_FILE" ] && [ "$(cat "$PASS_FILE")" = "$fingerprint" ] && exit 0

# 3. 환경 미준비면 검사 불가 — 막지 않고 안내만
if [ -n "$(missing_setup)" ]; then
  emit systemMessage "품질 검사를 건너뜀: 개발 환경이 준비되지 않았습니다 (make setup 필요)."
  exit 0
fi

# 4. 바뀐 쪽만 검사 — 실패한 쪽의 로그 끝부분만 모아 돌려준다
: > "$LOG_FILE"
fail=0
errors=""
run_side() { # $1=이름  $2=명령
  local out
  out=$(bash -c "$2" 2>&1) && return 0
  fail=1
  printf '### %s\n%s\n' "$1" "$out" >>"$LOG_FILE"
  errors+=$(printf '\n### %s 실패\n%s' "$1" "$(echo "$out" | grep -v '^\s*$' | tail -35)")
}
if echo "$changed" | grep -q '^backend/'; then
  db_running || (cd backend && docker compose up -d --wait >/dev/null 2>&1)
  run_side backend "cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check . && .venv/bin/pytest -q -x --no-header -p no:warnings && .venv/bin/alembic check"
fi
fail_with() { # $1=이름  $2=메시지 — 명령 실행 없이 실패를 기록
  fail=1
  printf '### %s\n%s\n' "$1" "$2" >>"$LOG_FILE"
  errors+=$(printf '\n### %s 실패\n%s' "$1" "$2")
}

# 진행 중 run(vibe-build 등, DONE 없음, 최근 갱신)이 있으면 e2e 와 "새 화면의 e2e 누락" 검사는 미룬다 —
# 병렬 개발 중 합친 화면은 12단계에서 e2e 를 쓰므로, 그 전 턴들이 이 검사로 막혀 차단 횟수를 다 쓰지 않게.
# 그 run 은 최종 검증 루프(vibe-build/harness.md)가 e2e 를 통과해야 DONE 을 만들고, DONE 이 생긴 뒤의 종료에서 여기서 다시 돈다.
run=$(active_runs | head -1)

# 세션 시작 이후 새로 생긴 frontend 파일 중 짝 테스트가 없는 것 (한 줄에 하나, 필요한 테스트 위치 포함)
missing_tests() {
  local added f dir name e2e_changed page
  added=$( { git diff --name-only --diff-filter=A "$base" -- frontend; git ls-files --others --exclude-standard -- frontend; } 2>/dev/null | sort -u)
  # 새 화면(page)인데 e2e 시나리오 추가·변경이 하나도 없음 (진행 중 run 이면 12단계로 미룸)
  if [ -z "$run" ]; then
    e2e_changed=$( { git diff --name-only --diff-filter=AM "$base" -- frontend/e2e; git ls-files --others --exclude-standard -- frontend/e2e; } 2>/dev/null | grep -E '\.spec\.ts$')
    echo "$added" | grep -E '^frontend/src/(features/[^/]+/pages/[^/]+Page\.tsx|app/(.*/)?page\.tsx)$' \
      | while read -r page; do
          [ -n "$e2e_changed" ] || echo "$page  → frontend/e2e/{기능}.spec.ts 필요 (frontend/browser-check 절차)"
        done
  fi
  # 새 로직·부품인데 __tests__ 짝 파일이 없음
  #   도메인(features/*) + 공용(src/{models,services,hooks,store,utils,lib}, components/shared) 모두 대상
  echo "$added" | grep -E '^frontend/src/(features/[^/]+/)?(models/[^/]+Mapper\.ts|services/[^/]+\.ts|hooks/[^/]+\.tsx?|store/[^/]+\.ts|utils/[^/]+\.ts|lib/[^/]+\.tsx?)$|^frontend/src/(features/[^/]+/components|components/shared)/[^/]+/index\.tsx$' \
    | while read -r f; do
        dir=$(dirname "$f"); name=$(basename "${f%.*}")
        [ "$name" = index ] && name=$(basename "$dir")   # components/<Name>/index.tsx → <Name>
        ls "$dir/__tests__/$name".test.ts* >/dev/null 2>&1 || echo "$f  → $dir/__tests__/$name.test.ts(x) 필요"
      done
}

if echo "$changed" | grep -q '^frontend/'; then
  run_side frontend "cd frontend && pnpm -s lint --quiet && pnpm -s type-check && pnpm -s test"
  missing=$(missing_tests)
  [ -n "$missing" ] && fail_with "테스트 누락" "새로 만든 파일에 짝 테스트가 없다. 아래 위치에 테스트를 작성하라 (빈 테스트·skip 금지):
$missing"
fi
# 정적 검사가 통과한 경우에만 실브라우저 e2e (실패 상태에서 오래 걸리는 검사를 반복하지 않음).
# 서버만 바뀌어도 기존 화면이 그 API 를 쓰므로 e2e 를 돌린다 (harness.md 와 같은 기준).
if [ "$fail" -eq 0 ] && [ -n "$run" ]; then
  deferred_e2e="e2e·새 화면 e2e 누락 검사는 진행 중 작업($run)의 최종 검증 단계로 미룸"
elif [ "$fail" -eq 0 ]; then
  db_running || (cd backend && docker compose up -d --wait >/dev/null 2>&1)
  run_side e2e "cd frontend && pnpm -s test:e2e"
fi

if [ "$fail" -eq 0 ]; then
  rm -f "$COUNT_FILE" "$PAUSED_FP_FILE"
  if [ -n "${deferred_e2e:-}" ]; then
    emit systemMessage "품질 검사 통과 (정적·테스트). $deferred_e2e."
    exit 0   # 통과 기록을 남기지 않는다 — DONE 이후 종료에서 e2e 까지 다시 검사
  fi
  echo "$fingerprint" > "$PASS_FILE"
  exit 0
fi

# 5. 실패 — 사용자 답을 기다리며 멈춘 run(PAUSED)이면 막지 않고 알리기만 한다 (질문·실패 보고가 가능하도록)
#    단 ① 사유 1줄이 있어야 하고 ② 같은 변경(지문)으로는 1회만 — "답을 기다리는 턴"은 한 번이면 충분하다.
#    사유 없는 PAUSED 나 두 번째 종료는 검사 회피로 보고 차단한다.
paused=$(paused_runs)
if [ -n "$paused" ]; then
  reason_ok=1
  for d in "$HARNESS_DIR"/runs/*/; do
    [ -f "$d/PAUSED" ] && [ ! -f "$d/DONE" ] && [ -z "$(head -1 "$d/PAUSED" | tr -d '[:space:]')" ] && reason_ok=0
  done
  if [ "$reason_ok" -eq 1 ] && [ "$(cat "$PAUSED_FP_FILE" 2>/dev/null)" != "$fingerprint" ]; then
    rm -f "$COUNT_FILE"
    echo "$fingerprint" > "$PAUSED_FP_FILE"
    emit systemMessage "검사 미통과 상태로 사용자 답을 기다리는 중 — $paused. 답을 받아 재개하면 PAUSED 를 지우고 다시 검사한다 (같은 변경으로 다시 PAUSED 로 끝낼 수는 없다)."
    exit 0
  fi
  [ "$reason_ok" -eq 0 ] && errors+=$'\n### PAUSED 사유 없음\nPAUSED 파일 첫 줄에 멈춘 사유 1줄이 필요하다. 오류를 고치기 싫어서 만든 PAUSED 는 지우고 아래 에러를 고쳐라.'
  [ "$reason_ok" -eq 1 ] && errors+=$'\n### PAUSED 재사용\n이 변경은 이미 PAUSED 로 한 번 사용자 답을 기다렸다. 답을 반영했으면 PAUSED 를 지우고 아래 에러를 고쳐라.'
fi

# 6. 실패 — 연속 차단 횟수 확인 후 block
count=$(( $(cat "$COUNT_FILE" 2>/dev/null || echo 0) + 1 ))
echo "$count" > "$COUNT_FILE"
if [ "$count" -ge "$MAX_BLOCKS" ]; then
  rm -f "$COUNT_FILE"
  emit systemMessage "⚠️ 자동으로 ${MAX_BLOCKS}번 고쳐 봤지만 마무리 검사를 통과하지 못해 여기서 멈췄습니다 (아직 저장하지 않았어요). 막힌 내용을 쉬운 말로 사용자에게 설명하고, 해결되면 '이어서 해줘'라고 말하면 멈춘 지점부터 다시 한다고 안내하라. 상세 기록: .harness/gate-last.log"
  exit 0
fi

emit reason "[품질 게이트 ${count}/${MAX_BLOCKS}] 코드 변경 후 검증에 실패해 아직 끝낼 수 없다. 아래 에러를 고친 뒤 다시 마무리하라. 경계 테스트(VIOLATION) 에러는 메시지에 적힌 rules 파일을 읽고 그 규칙대로 고친다. 테스트를 skip·삭제하거나 기대값을 바꿔 통과시키는 것은 금지.
$errors"
exit 0

#!/usr/bin/env bash
# SessionStart — 세션 시작 시 현재 상태(동적 컨텍스트)를 주입한다.
source "$(dirname "$0")/_lib.sh"
cd "$ROOT" || exit 0
mkdir -p "$HARNESS_DIR"

# 품질 게이트 기준 커밋(.harness/session-base) — 검증 안 된 커밋이 게이트 시야에서 빠지지 않게 조건부로만 앞당긴다.
#   resume·compact(작업 중 이어짐): 그대로 둔다.
#   startup·clear: 기존 기준이 HEAD 의 조상이고, 그 이후 변경이 없거나 게이트를 이미 통과한 상태면 HEAD 로 앞당긴다.
#                  통과 못 한 변경이 남아 있으면 기준을 유지해 다음 종료 때 다시 검사한다.
hook_source=$(grep -o '"source" *: *"[a-z]*"' 2>/dev/null | head -1 | sed 's/.*"\([a-z]*\)"$/\1/')
base_file="$HARNESS_DIR/session-base"
old_base=$(cat "$base_file" 2>/dev/null)
advance=1
if [ -n "$old_base" ] && git cat-file -e "${old_base}^{commit}" 2>/dev/null && git merge-base --is-ancestor "$old_base" HEAD 2>/dev/null; then
  case "$hook_source" in
    resume|compact) advance=0 ;;
    *)
      if [ -n "$( { git diff --name-only "$old_base" -- backend frontend; git ls-files --others --exclude-standard -- backend frontend; } 2>/dev/null)" ] \
         && [ "$(cat "$HARNESS_DIR/gate-pass" 2>/dev/null)" != "$(gate_fingerprint "$old_base")" ]; then
        advance=0
      fi ;;
  esac
fi
[ "$advance" = 1 ] && git rev-parse HEAD > "$base_file" 2>/dev/null

echo "## 프로젝트 현재 상태 (자동 수집)"
missing=$(missing_setup)
if [ -n "$missing" ]; then
  echo "- 개발 환경: 준비 안 됨 (없음:$missing) → 사용자의 첫 요청을 처리하기 전에 vibe-setup 스킬을 따른다."
else
  echo "- 개발 환경: 준비됨"
fi
if db_running; then echo "- DB: 실행 중"; else echo "- DB: 꺼짐 (필요하면 'make db')"; fi
branch=$(git branch --show-current 2>/dev/null)
if git show-ref -q --verify refs/heads/dev 2>/dev/null; then
  echo "- 현재 브랜치: ${branch:-(없음)} — 코드를 바꾸는 작업은 dev 에서 작업 브랜치를 만들어 하고, 검증 후 dev 에 merge 한다 (COMMON.md §3-B)"
else
  echo "- 현재 브랜치: ${branch:-(없음)} — dev 브랜치 없음 → 코드 작업 전에 vibe-setup 스킬(make setup)로 main·dev 를 만든다."
fi
echo "- 변경 중인 파일: $(git status --porcelain 2>/dev/null | wc -l | tr -d ' ')개"
echo "- 최근 커밋:"
git log --oneline -5 2>/dev/null | sed 's/^/  /'
if [ -f "$ROOT/spec/README.md" ]; then
  echo "- 개발 기록(spec/README.md 색인) — 기존 기능을 고치기 전에 관련 spec 을 읽는다. 최근 5건:"
  grep -E '^\| *[0-9]{3} ' "$ROOT/spec/README.md" | tail -5 | sed 's/^/  /'
fi
concepts=$(domain_map_summary)
[ -n "$concepts" ] && echo "- 데이터 개념 지도(docs/backend/DOMAIN-MAP.md): $concepts — 저장할 데이터를 새로 설계하기 전에 이 개념들에 먼저 매핑하고, 안 맞을 때만 새 테이블."
runs=$(active_runs)
[ -n "$runs" ] && echo "- 진행 중인 작업(.harness/runs): $runs — 관련 요청이면 그 run 의 state.md 부터 읽고 이어서 한다."
stale=$(stale_runs)
[ -n "$stale" ] && echo "- 오래 멈춰 있는 미완료 작업: $(echo $stale) — 관련 요청이면 그 run 의 state.md 를 읽고 이어서 하고, 버린 작업이면 사용자에게 확인한 뒤 DONE 을 만들어 닫는다 (닫지 않아도 품질 게이트를 미루지는 못한다)."
[ "$advance" = 0 ] && echo "- 품질 게이트 기준: 아직 검증을 통과하지 못한 이전 변경이 있어 기준 커밋(${old_base:0:7})을 유지한다 — 종료할 때 그 변경까지 검사한다."
paused=$(paused_runs)
[ -n "$paused" ] && echo "- 사용자 답을 기다리며 멈춘 작업: $paused — 사용자가 답하거나 \"이어서 해줘\"라고 하면 PAUSED 를 지우고 멈춘 단계부터 재개한다."
exit 0

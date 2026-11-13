#!/usr/bin/env bash
# 주간 엔트로피 점검 (보고 전용 — 아무것도 수정하지 않는다)
#   1. 아키텍처 경계 (래칫 포함)
#   2. API 계약 문서 drift: 백엔드 OpenAPI vs frontend/public/openapi.json
#   3. 문서 신선도: 코드가 바뀌었는데 오래 안 바뀐 문서
#   4. 데이터 구조: ERD 최신 여부, 개념 지도에 없는 테이블, 미사용 테이블, 테이블·비정규화 개수
# 종료 코드: 0 = 이상 없음, 1 = 발견
set -uo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$ROOT"
STALE_DAYS=60
ISSUES=0
fail() { echo "FAIL: $1"; ISSUES=$((ISSUES + 1)); }
ok() { echo "OK:   $1"; }

PY=backend/.venv/bin/python
[ -x "$PY" ] || PY=python3

echo "--- 1. 아키텍처 경계 ---"
if (cd backend && "$ROOT/$PY" -m pytest -q --no-header tests/architecture >/tmp/gc-arch.log 2>&1); then
  ok "백엔드 경계 테스트 통과"
else
  fail "백엔드 경계 위반 — tests/architecture 결과:"; tail -20 /tmp/gc-arch.log
fi
if (cd frontend && pnpm -s lint >/tmp/gc-lint.log 2>&1); then
  ok "프론트 계층 import 규칙 통과"
else
  fail "프론트 ESLint 위반:"; grep -E "error" /tmp/gc-lint.log | head -20
fi

echo "--- 2. API 계약 drift ---"
current=$(cd backend && "$ROOT/$PY" -c "import json; from app.main import app; print(json.dumps(app.openapi(), sort_keys=True))" 2>/dev/null)
committed=$(python3 -c "import json,sys; print(json.dumps(json.load(open('frontend/public/openapi.json')), sort_keys=True))" 2>/dev/null)
if [ -z "$current" ]; then
  fail "백엔드 OpenAPI 추출 실패 (앱 import 에러)"
elif [ "$current" != "$committed" ]; then
  fail "frontend/public/openapi.json 이 현재 백엔드와 다르다 → cd backend && .venv/bin/python scripts/export_openapi.py 로 재생성 (swagger/docs.md 는 backend/sync-api-docs 절차)"
else
  ok "API 계약 문서 최신"
fi

echo "--- 3. 문서 신선도 (${STALE_DAYS}일) ---"
now=$(date +%s)
for doc in AGENTS.md ARCHITECTURE.md docs/architecture/LAYERS.md backend/CLAUDE.md frontend/CLAUDE.md; do
  [ -f "$doc" ] || { fail "$doc 없음"; continue; }
  doc_ts=$(git log -1 --format=%ct -- "$doc" 2>/dev/null || echo "$now")
  src_ts=$(git log -1 --format=%ct -- backend/app frontend/src/features frontend/src/app 2>/dev/null || echo 0)
  if [ -n "$doc_ts" ] && [ $(( (src_ts - doc_ts) / 86400 )) -gt "$STALE_DAYS" ]; then
    fail "$doc 가 코드보다 ${STALE_DAYS}일 이상 오래됨 — 내용 점검 필요"
  fi
done
ok "문서 신선도 점검 완료"

echo "--- 4. 데이터 구조 ---"
if "$PY" backend/scripts/gen_erd.py --check >/dev/null 2>&1; then
  ok "ERD(docs/backend/ERD.md) 최신"
else
  fail "docs/backend/ERD.md 가 data-model.yaml 과 다름 → backend/scripts/gen_erd.py 실행"
fi
tables=$("$PY" -c "import yaml; print(' '.join((yaml.safe_load(open('backend/data-model.yaml')) or {}).get('tables') or {}))" 2>/dev/null)
unmapped=""
for table in $tables; do
  grep -q "\`$table[\`.]" docs/backend/DOMAIN-MAP.md 2>/dev/null || unmapped="$unmapped $table"
done
if [ -n "$unmapped" ]; then
  fail "개념 지도(docs/backend/DOMAIN-MAP.md)에 없는 테이블:$unmapped → 개념 행 추가, 필요 없는 테이블이면 schema-cleanup 제안"
else
  ok "모든 테이블이 개념 지도에 있음"
fi
unused=$(cd backend && "$ROOT/$PY" -c "from tests.architecture.test_schema import unused_table_report as r; print('\n'.join(str(v) for v in r()))" 2>/dev/null)
if [ -n "$unused" ]; then
  fail "앱 코드에서 쓰지 않는 테이블 (개발 중이 아니라면 정리 대상):"; echo "$unused"
else
  ok "미사용 테이블 없음"
fi
denormalized=$(grep -c "denormalized:" backend/data-model.yaml)
echo "INFO: 테이블 $(echo "$tables" | wc -w | tr -d ' ')개, 비정규화 컬럼 ${denormalized}개 (중복 의심 테이블은 1번 스키마 테스트가 차단)"
echo "      위반이 쌓였으면 → backend/schema-cleanup 절차로 정리안을 만들어 사용자 확인을 받는다"

echo ""
[ "$ISSUES" -eq 0 ] && { echo "이상 없음"; exit 0; }
echo "$ISSUES 건 발견"; exit 1

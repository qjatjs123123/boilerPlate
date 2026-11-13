# 최종 검증 루프 (harness)

vibe-build 13단계와 vibe-refactor 4단계가 이 파일을 읽고 따른다. **구현이 끝난 뒤** "검사 → 고침"을 통과할 때까지 반복하는 규칙만 정한다 — 설계·구현·커밋은 호출한 쪽 몫이다 (**이 루프는 커밋하지 않는다**).

입력: 호출한 쪽이 넘겨준 작업 이름 (예: "{slug} 최종 검증", "{slug} 리팩토링 검증").

## 작업 폴더 (RUN_DIR)
`.harness/runs/{slug}/` — 호출한 쪽이 이미 만들었으면 그대로 쓰고, 없으면 만든다(같은 작업의 폴더가 있으면 이어서). **다른 run 의 폴더는 읽지도 쓰지도 않는다.**
```
.harness/runs/{slug}/
├── task.md              작업 원문 (시작 시 1회)
├── state.md             호출한 쪽(vibe-build)의 진행 상태 — 브랜치명·개발 방식·배치표. **이 루프는 읽기만 하고 덮어쓰지 않는다** (덮어쓰면 재개가 불가능해진다)
├── loop.md              이 루프의 상태 — [미해결 에러] / [다음에 시도할 것] / [이미 실패해서 다시 하지 말 것]. 매 바퀴 시작 시 먼저 읽고, 끝날 때 덮어쓴다.
├── log.md               바퀴별 기록 — 뒤에 덧붙이기만 한다 (지우지 않는다)
└── console-errors.log   e2e 실행 시 브라우저 콘솔·런타임 에러가 자동 기록된다
```
- **진행 중 run** = `state.md` 가 있고 `DONE` 이 없는 폴더 (`.claude/hooks/_lib.sh` 의 `active_runs`). `state.md` 가 없으면(vibe-refactor 단독 호출) 작업 이름 한 줄로 만든다 — active_runs 판정용이며, 이미 있으면 손대지 않는다. 세션 시작·매 입력 훅이 이 목록을 알려 주고, Stop 품질 게이트는 진행 중 run 이 있으면 e2e 를 이 루프로 미룬다 — 그래서 이 루프를 통과한 뒤에만 `DONE` 을 만들고, 끝난 run 에는 반드시 `DONE` 을 만든다 (안 만들면 게이트의 e2e 가 계속 미뤄진다).

## 한 바퀴
1. `loop.md` 를 읽는다 (첫 바퀴면 만든다) — "다시 하지 말 것"에 있는 접근은 시도하지 않는다.
2. **검사 (실제로 실행)**
   - 정적: `make check` (빌드·타입·테스트·lint)
   - 동적: **먼저 `: > RUN_DIR/console-errors.log` 로 로그를 비운다** (`fixtures.ts` 가 덧붙이기만 하므로, 비우지 않으면 지난 바퀴 에러가 이번 판정에 섞인다 — 지난 기록은 `log.md` 에 남아 있다). 그다음 `make e2e HARNESS_RUN_DIR=<RUN_DIR>` — 고정 흐름 스크립트 `frontend/e2e/*.spec.ts` (`e2e/fixtures.ts` 의 `test` 사용, 콘솔 에러를 `console-errors.log` 에 자동 기록). 화면 변경이 없는 서버 전용 작업도 기존 e2e 는 돌린다.
3. **판정 — 명령 결과(exit code)와 로그 파일로만.** 스크린샷을 보고 "괜찮아 보인다"는 판정 금지.
   - 통과 = `make check` 성공 + e2e 흐름 전부 통과 + `console-errors.log` 의 에러 0건.
   - 에러 수는 `grep -cE '^\[(console\.error|pageerror)\]' <RUN_DIR>/console-errors.log` 로 센다 (`fixtures.ts` 가 에러 줄 앞에 붙이는 표시). 단순히 "error" 로 grep 하면 에러가 없을 때 쓰이는 `(no errors)` 줄까지 세어 오판한다.
4. **기록**: `log.md` 에 바퀴 번호·실행 명령·결과(실패 수/통과 수)·남은 문제를 덧붙이고, `loop.md` 를 갱신한다 (`state.md` 는 건드리지 않는다).
5. **통과면 `RUN_DIR/DONE` 을 만들고 종료.** 아니면 실패 원인을 고친다 — **먼저 `docs/TROUBLESHOOTING.md` 와 영역 문서(`docs/{backend,frontend}/TROUBLESHOOTING.md`)에서 같은 증상을 찾아** 해결법이 있으면 그대로 쓴다. rules(`.claude/rules/**`)·관련 스킬을 지키고, 테스트 약화(skip·삭제·기대값 조작)는 금지. e2e 실패 원인이 불분명하면 `frontend/browser-check` 2️⃣ 처럼 Playwright MCP 로 같은 흐름을 눌러 원인을 찾되, 판정은 e2e 로그로 한다. → 1로.

## 멈춤 조건
- **최대 6바퀴.** 도달하면 멈춘다.
- **2바퀴 연속 개선 없음**(실패 수가 줄지 않음)이면 멈춘다 — 같은 실패를 반복하지 않는다.
- 멈추면 `DONE` 을 만들지 않고 호출한 쪽에 넘긴다 (호출한 쪽은 커밋하지 않는다).

## 호출한 쪽에 넘길 결과
- 성공/미완, 몇 바퀴 돌았는지
- 통과한 검사와 남은 문제 (`loop.md` 의 미해결 에러)
- 사람이 판단해야 할 점 (있으면)

> 명령을 모르면 추측하지 말고 `Makefile`·`frontend/package.json`·`playwright.config.ts` 에서 실제 명령을 찾는다.

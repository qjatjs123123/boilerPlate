---
name: frontend-browser-check
description: 화면(UI) Task를 Playwright MCP로 실제 브라우저에서 눌러보며 콘솔·API 에러 0을 확인하고, 그 흐름을 e2e 테스트로 고정해 통과시키는 절차. UI Task 완료 전 필수.
---

# frontend/browser-check — Playwright MCP 실검증 → e2e 테스트 고정

> 절차 스킬 — 슬래시 커맨드가 아니다. 표기법·vibe-build 모드·커밋 절차·spec 번호 규칙은 **`.claude/skills/COMMON.md` 를 먼저 읽고** 따른다.

> **vibe-build 모드** — 공통 규칙은 `COMMON.md` §2. 이 스킬만의 차이: MCP 브라우저가 열리지 않을 때(`Browser is already in use` — 다른 Claude 창이 점유) 기다리거나 우회하지 않고 **같은 흐름을 e2e 로 먼저 작성·실행해 판정**하고, `RUN_DIR/mcp-check.md` 에 "MCP 불가 → e2e 판정" 과 사유를 적는다. 같은 run 안에서 MCP 가 다시 열리면 2️⃣ 실검증을 마저 한다. (단독 실행에서는 아래 금지 항목대로 둘 다 필수.)

화면을 만든 뒤 **두 겹으로** 확인한다.
1. **MCP 실검증** — Claude 가 Playwright MCP 로 진짜 브라우저를 열어 사용자처럼 눌러보고, 콘솔 에러·실패한 API 요청을 받아와 고친다.
2. **e2e 고정** — 통과한 그 흐름을 `frontend/e2e/{기능}.spec.ts` 로 저장해 언제든 다시 돌릴 수 있게 한다.

**둘 다 통과해야 UI Task 를 완료할 수 있다.** (단독 실행 시 `frontend/spec-run` 이 UI Task 마다 이 절차를 따르고, vibe-build 에서는 12단계가 UI Task 마다 따른다. 작업 종료 시 Stop 훅이 e2e 를 다시 돌린다.)

## 입력

```
frontend/browser-check <검증 URL> <핵심 사용자 흐름> [RUN_DIR]
예) frontend/browser-check /notices "목록 표시 → 작성 버튼 → 제목·내용 입력 → 저장 → 목록에 새 글 표시" .harness/runs/notice-feature
```

- 흐름은 spec 의 FR(요구사항)·Task "검증" 필드에서 가져온다.
- `RUN_DIR` 이 없으면 `.harness/runs/` 의 진행 중 run(`DONE` 없음)을 쓰고, 그것도 없으면 `.harness/runs/{기능}/` 을 만든다.

---

## 1️⃣ 서버 준비 (사용자에게 묻지 않는다)

```bash
curl -s http://localhost:3000 -o /dev/null -w '%{http_code}'            # 프론트
curl -s http://localhost:8000/api/health -o /dev/null -w '%{http_code}' # 백엔드
```

- 응답이 없으면 꺼진 쪽을 **백그라운드로** 켠다: `make dev-frontend` / `make dev-backend` (DB 가 꺼져 있으면 `make db` 먼저).
- 켜질 때까지 위 curl 로 확인한 뒤 진행한다.

## 2️⃣ MCP 실검증 루프

사용 도구 (`mcp__playwright__` 접두사 — 프로젝트 `.mcp.json` 의 Chromium 헤드리스 서버):

| 목적 | 도구 |
|---|---|
| 이동 | `browser_navigate` |
| 화면 구조 읽기 (버튼·입력칸 이름 확인) | `browser_snapshot` |
| 조작 | `browser_click`, `browser_type`, `browser_fill_form`, `browser_select_option`, `browser_press_key` |
| 대기 | `browser_wait_for` |
| **콘솔 에러 수집** | `browser_console_messages` |
| **API 요청 실패 수집** | `browser_network_requests` |
| 참고용 화면 | `browser_take_screenshot` |

절차:
1. `browser_navigate` 로 검증 URL 이동 → `browser_snapshot` 으로 화면 구조 확인.
2. 입력받은 흐름을 **한 단계씩** 수행한다. 각 단계 후 `browser_snapshot` 으로 기대한 결과(새 글이 목록에 보임 등)가 화면에 있는지 확인한다.
3. 흐름이 끝나면(또는 막히면) 에러를 수집한다:
   - `browser_console_messages` → error 레벨 메시지, 페이지 런타임 예외
   - `browser_network_requests` → `/api` 요청 중 4xx·5xx 응답 (의도한 실패 케이스를 검증하는 흐름은 제외)
4. **판정 — 모두 충족해야 통과**:
   - 콘솔 error 0, 런타임 예외 0
   - 실패한 API 요청 0
   - 흐름 마지막 단계의 기대 결과가 snapshot 에 존재
5. 미통과면: 에러 메시지·스택·요청 응답 본문으로 원인 코드를 찾아 고친다 → 페이지를 다시 열어 **같은 흐름 전체**를 재실행.
   - 같은 에러가 **3회 연속** 해결되지 않으면 중단하고 사유를 보고한다 (Task 체크·커밋 금지).
   - 백엔드 응답 문제면 백엔드 코드를 고치되, `.claude/rules/backend/` 규칙을 따른다.
6. **권한 화면 확인** — "내 글만 수정·삭제" 같은 요구가 있으면 다른 사람 데이터도 눌러 본다. 개발용 일반 사용자 `dev-user` 로 API 를 호출해 데이터를 만든다 (id 는 `make setup`·`backend/scripts/seed_dev_user.py` 출력에 나온다. DB 에 사용자를 직접 넣지 않는다):
   ```bash
   curl -s -X POST http://localhost:8000/api/{리소스} -H 'Content-Type: application/json' -H 'X-User-Id: {dev-user id}' -d '{...}'
   ```
   → 그 상세 화면에서 수정·삭제 버튼이 없는지, 수정 주소로 직접 들어가면 안내가 뜨는지 snapshot 으로 확인한다.
7. **만든 데이터는 끝나면 지운다** — 검증하려고 만든 글·임시 데이터는 흐름이 끝나면 API 로 삭제한다. 개발 DB 는 사용자가 보는 화면과 같은 DB 다.

> ❌ 스크린샷을 눈으로 보고 "괜찮아 보인다"로 통과 판정하지 않는다. 판정은 위 수집 결과와 snapshot 으로만 한다.

## 3️⃣ 증거 기록 — `RUN_DIR/mcp-check.md`

통과·실패 모두 실행할 때마다 **append** 한다. 이 기록 없이는 UI Task 를 체크할 수 없다.

```markdown
## {YYYY-MM-DD HH:MM} {검증 URL}
- 흐름: {수행한 단계 요약}
- 콘솔 error: {n}건 / 런타임 예외: {n}건
- 실패 API 요청: {n}건 ({메서드 경로 상태} 목록)
- 결과: ✅ 통과 | ❌ 미통과 — {남은 문제}
- 수정한 파일: {있으면}
```

## 4️⃣ 흐름을 e2e 테스트로 고정

MCP 로 통과한 **같은 흐름**을 `frontend/e2e/{기능}.spec.ts` 에 작성한다 (이미 있으면 테스트를 추가).

```ts
// frontend/e2e/notice.spec.ts
import { expect, test } from './fixtures'; // 콘솔 에러·런타임 예외가 있으면 자동 실패

test('공지 작성 후 목록에 새 공지가 보인다', async ({ page }) => {
  await page.goto('/notices');
  await page.getByRole('button', { name: '작성' }).click();
  await page.getByLabel('제목').fill('e2e 공지');
  await page.getByLabel('내용').fill('본문');
  await page.getByRole('button', { name: '저장' }).click();

  await expect(page.getByRole('link', { name: 'e2e 공지' })).toBeVisible();
});
```

- `@playwright/test` 가 아니라 **`./fixtures` 의 `test`** 를 import 한다 (콘솔 에러 수집 + `HARNESS_RUN_DIR` 로그 기록).
- 선택자는 2️⃣ 의 `browser_snapshot` 에서 확인한 **역할·이름**(`getByRole`, `getByLabel`, `getByText`)을 쓴다. CSS 클래스·nth 선택 금지.
- 데이터를 만드는 흐름은 매번 다른 값(예: `Date.now()` 접미사)을 써서 반복 실행에도 깨지지 않게 한다.
- **만든 데이터는 테스트가 직접 지운다** — e2e 는 개발 DB 를 그대로 쓰고, 종료 품질 게이트가 매번 e2e 를 다시 돌리므로 지우지 않으면 사용자 화면에 테스트 글이 계속 쌓인다. 흐름 자체가 삭제로 끝나지 않으면, 만든 id 를 URL 등에서 받아 두고 `test.afterEach` 에서 `request` fixture 로 API 삭제한다 (인증 헤더는 `lib/axios.ts` 와 같은 `X-User-Id`):
  ```ts
  const createdIdList: number[] = [];
  test.afterEach(async ({ request }) => {
    for (const id of createdIdList.splice(0)) {
      await request.delete(`${API_URL}/api/notices/${id}`, { headers: { 'X-User-Id': DEV_USER_ID } });
    }
  });
  ```

## 5️⃣ e2e 실행 — 통과까지

```bash
make e2e SPEC=e2e/{기능}.spec.ts HARNESS_RUN_DIR=<RUN_DIR>
```

- `playwright.config.ts` 가 프론트·백엔드 서버를 띄우거나 이미 켜진 서버를 재사용한다.
- 실패하면 원인을 고치고 재실행. 화면 코드를 고쳤다면 2️⃣ MCP 흐름도 다시 돌려 기록을 남긴다.
- 같은 실패 3회 연속이면 중단·보고.

## 6️⃣ 완료 보고 (호출한 쪽에 1회)

```
✅ browser-check 통과: {URL}
- MCP: 콘솔 error 0 · 실패 요청 0 (RUN_DIR/mcp-check.md)
- e2e: e2e/{기능}.spec.ts {n}개 통과
- 수정한 파일: {목록}
```

---

## 금지 사항

- ❌ MCP 실검증 없이 e2e 만 작성, 또는 e2e 없이 MCP 확인만으로 완료 처리 *(vibe-build 모드에서 MCP 가 열리지 않는 경우만 맨 위 「vibe-build 모드」 문단이 우선)*
- ❌ 스크린샷 육안 판단으로 통과 판정
- ❌ 테스트 약화 — `test.skip`/`test.fixme`, assertion 삭제, `fixtures` 대신 `@playwright/test` import 로 콘솔 에러 수집 회피
- ❌ 실패 API 요청·콘솔 에러를 "무관한 에러"로 판단해 무시 (원인이 이번 작업 밖이면 보고에 남기고 통과 처리하지 않는다)
- ❌ 서버를 켜 달라고 사용자에게 요청 (직접 켠다)

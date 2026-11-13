# 자주 나는 문제와 해결법 — 프론트엔드

공통 문제(환경 준비, 포트, 품질 게이트)는 [../TROUBLESHOOTING.md](../TROUBLESHOOTING.md).

## ESLint: "~ 계층은 ~ 계층을 import 할 수 없다"
- 원인: 아래 계층이 위 계층을 import (예: services → queries), 공용 계층 → features, `app/` 이 `features/*/pages` 외 import, 다른 도메인 직접 import, services 밖에서 axios 사용
- 해결: 메시지에 적힌 `.claude/rules/frontend/*.md` 를 읽고 코드를 올바른 계층으로 옮긴다. 규칙을 끄거나 `eslint-disable` 을 달지 않는다.

## 응답 형식 불일치 (`DomainLayerError`)
- 증상: 화면에 에러, 콘솔에 `DomainLayerError` / Zod 에러
- 원인: 백엔드 응답 모양이 바뀌었는데 프론트 `models/{domain}Schema.ts` 는 옛 모양
- 해결: `sync-api-docs` 로 `swagger/docs.md` 를 다시 만들고, 바뀐 필드를 `models/{domain}Schema.ts` → `models/{domain}Mapper.ts` → `types/{domain}Type.ts` 순서로 반영한다. `scripts/gc` 의 "API 계약 drift" 경고도 같은 원인.

## 서버 요청 실패 (`DataLayerError`)
- 증상: Network Error, 타임아웃(10초)
- 해결: 백엔드가 켜져 있는지 `curl -s localhost:8000/api/health`. CORS 면 [../backend/TROUBLESHOOTING.md](../backend/TROUBLESHOOTING.md).

## Next.js API 가 예상과 다름
- 증상: 학습한 방식대로 쓴 API 가 타입 에러·deprecated 경고
- 원인: Next.js 16 은 이전 버전과 API·규칙이 다르다
- 해결: `frontend/node_modules/next/dist/docs/` 의 해당 가이드를 읽고 따른다.

## "No QueryClient set" 에러
- 원인: TanStack Query 훅을 `ReactQueryProvider` 밖에서 사용 (또는 테스트에서 Provider 누락)
- 해결: 앱은 `src/app/layout.tsx` 가 이미 감싼다. 테스트는 기존 `__tests__` 처럼 QueryClientProvider 로 감싼 wrapper 를 쓴다.

## Playwright 실패
- 브라우저 미설치 → `cd frontend && pnpm exec playwright install chromium`
- 콘솔 에러로 실패 → `fixtures.ts` 가 console error·pageerror 를 자동 실패 처리한다. 테스트를 고치지 말고 콘솔 에러 원인을 고친다. `HARNESS_RUN_DIR` 지정 시 로그가 기록된다.
- 백엔드 연결 실패(`localhost:8000/api/health` 대기 시간 초과) → `playwright.config.ts` 가 백엔드도 띄우므로 `backend/.venv` 와 DB 가 준비돼 있어야 한다. `make db` 후 `curl -s localhost:8000/api/health` 로 확인. 원인이 불분명하면 `frontend/browser-check` 처럼 Playwright MCP 로 같은 흐름을 눌러 콘솔·API 에러를 직접 수집한다.

## Playwright MCP: "Browser ... is not installed" / "chrome is not found"
- 원인: MCP 는 `.mcp.json` 에 고정한 `@playwright/mcp` 버전 전용 Chromium 을 쓴다 (구글 크롬·플러그인판 MCP 는 쓰지 않음 — WSL 엔 크롬이 없다).
- 해결: `npx -y @playwright/mcp@{.mcp.json 의 버전} install-browser chrome-for-testing` (관리자 권한 불필요, `make setup` 에 포함). MCP 버전을 올리면 `Makefile` setup 줄도 같은 버전으로 맞춘다.

## 작업을 끝내려는데 "테스트 누락"으로 막힘
- 원인: 품질 게이트가 이번 세션에 새로 만든 파일의 짝 테스트를 검사한다 — 새 화면(`pages/*Page.tsx`, `app/**/page.tsx`)은 `e2e/*.spec.ts` 추가·변경, 새 `models/*Mapper.ts`·`services/*`·`hooks/*`·`store/*`·`components/<Name>/index.tsx` 는 같은 폴더 `__tests__/{이름}.test.ts(x)`.
- 해결: 메시지에 적힌 위치에 실제 동작을 검증하는 테스트를 작성한다. 빈 테스트·skip 으로 통과시키지 않는다. 화면 e2e 는 `frontend/browser-check` 절차(MCP 실검증 → e2e 고정)로 만든다.

## 코드를 고쳤는데 화면이 안 바뀜
- 개발 서버 터미널의 컴파일 에러 확인 (에러가 있으면 이전 화면이 남는다).
- 그래도 안 되면 `frontend/.next` 캐시를 지우고 `make dev-frontend` 재시작.

## 타입 검사가 `.next/dev/types/validator.ts` 에서 실패 ("Unexpected keyword or identifier")
- 증상: 소스는 안 바꿨는데 `pnpm type-check`·품질 게이트가 `.next/dev/types/validator.ts(…): error TS1434` 로 실패. 파일 앞부분 `import type` 줄이 빈 줄로 깨져 있다.
- 원인: `tsconfig.json` 이 개발 서버가 만드는 `.next/dev/types/**` 를 포함한다. e2e 도중 개발 서버가 갑자기 꺼지는 등 파일을 쓰다 끊기면 반쯤 쓴 파일이 남는다.
- 해결: 개발 서버가 꺼진 상태에서 `rm -r frontend/.next/dev` (생성물·git 미추적 — 다음 `pnpm dev` 가 다시 만든다) 후 `pnpm type-check` 재실행. 소스 코드나 tsconfig 를 고치지 않는다.
- 개발 서버가 켜져 있고 끌 수 없으면(사용자가 띄운 서버): 깨진 `frontend/.next/dev/types/validator.ts` 파일 하나만 지우고 `pnpm type-check` 를 다시 돌린다 — 서버는 그대로 두어도 된다 (spec 004 에서 확인).

## e2e 에서 링크를 눌러도 화면이 안 넘어감 (`toHaveURL` 5초 초과, 처음 실행·캐시 비운 뒤)
- 증상: 링크·메뉴 클릭 후 `expect(page).toHaveURL(...)` 가 이전 주소 그대로 시간 초과. 서버를 미리 켜 두고 다시 돌리면 통과. `.next/dev/logs` 끝이 `Compiling /board/... ...`.
- 원인: 개발 서버는 화면을 처음 열 때 만든다(1~3초). 캐시가 빈 상태에서 테스트 여러 개가 동시에 서로 다른 화면을 처음 열면 만들기가 몰려 5초를 넘긴다.
- 해결: `frontend/e2e/global-setup.ts` 가 테스트 전에 `src/app/**/page.tsx` 의 모든 화면을 한 번씩 열어 둔다 (`playwright.config.ts` `globalSetup`). 이 파일이 빠졌거나 화면 목록을 못 읽는지 확인한다. 테스트의 대기 시간을 늘리거나 기대값을 바꾸지 않는다.

## e2e 기대값이 다른 테스트의 글 때문에 어긋남 (이전 글·다음 글, 목록 순서)
- 원인: e2e 는 같은 개발 DB 에서 동시에 글을 만들고 지운다. 기대값을 API 로 먼저 읽고 화면을 열면 그 사이에 바뀔 수 있다.
- 해결: 기대값은 **화면이 실제로 받은 응답**에서 꺼낸다 — `page.waitForResponse(...)` 를 `page.goto` 전에 걸고 그 응답 JSON 과 화면을 비교한다 (예: `e2e/board-neighbor.spec.ts`).

## e2e "strict mode violation: getByRole('link', { name: '…' }) resolved to 2 elements"
- 원인: `name` 은 기본이 **부분 일치**라, 버튼·메뉴 이름("검색", "글쓰기", "게시판")이 다른 테스트가 만든 글 제목이나 새 메뉴("게시판 현황")에 포함되면 둘 다 잡힌다. 동시 실행 순서에 따라 가끔만 실패한다.
- 해결: 고정 문구 버튼·링크는 `{ name: '검색', exact: true }` 로 정확히 찾거나 `getByRole('navigation')` 처럼 영역을 좁힌다. 기대값을 바꾸거나 테스트를 건너뛰지 않는다.

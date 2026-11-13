# 코딩 규칙 — 공통

기계로 검사할 수 있는 규칙은 린터(ruff, ESLint)·타입체크·경계 테스트가 강제한다. 여기에는 **린터가 못 잡는 것**만 적는다.
영역별 규칙: 프론트 [../.claude/rules/frontend/](../.claude/rules/frontend/), 백엔드 [backend/CONVENTIONS.md](backend/CONVENTIONS.md).
계층별 상세 규칙의 단일 출처는 `.claude/rules/{backend,frontend}/*.md` 이다 — 이 문서와 다르면 rules 가 우선한다.

## 공통
- 사용자에게 보이는 문구(에러 메시지, 버튼, 안내)는 **한국어**. 백엔드 예외 message 도 한국어 문장.
- 코드 이름(변수, 함수, 파일)은 영어. DB 테이블은 복수형 snake_case (`posts`, `blog_posts`).
- 한 기능 = 한 이름. 백엔드 `post`, 프론트 `article` 처럼 다르게 부르지 않는다.
- 주석은 "왜"를 쓴다. "무엇"은 코드가 말한다.
- 함수·docstring 은 짧게: 백엔드 20줄, 프론트 15줄 이내 + 단일 책임.

## 테스트
- 모든 작업(Task)은 테스트를 포함한다. 테스트가 실패한 상태로 다음 작업으로 넘어가지 않는다.
- 테스트 약화 금지: skip·xfail·assertion 삭제·기대값을 실제값에 끼워 맞추기.
- 코드 변경 후 `make check` 통과 (종료 시 품질 게이트가 강제).

## 문서
- 모든 개발 요청은 레포 루트 `spec/backend/`·`spec/frontend/` 에 spec 을 남긴다 (색인 `spec/README.md`). 기능이 바뀌면 코드보다 spec 을 먼저 고친다.
- 새 에러를 해결하면 해당 영역의 TROUBLESHOOTING.md 에 추가한다.
- 기술 선택(라이브러리 추가, 구조 변경, 인증 방식)은 해당 spec 의 결정 사항에 이유와 함께 기록한다.
- `frontend/swagger/docs.md` 는 손으로 고치지 않는다 (sync-api-docs 생성물).

## Git (사내 컨벤션 — GitHub Flow)

### 브랜치
- `main`: 항상 배포 가능한 상태. 직접 작업하지 않는다. `dev → main` 반영은 사람이 직접 한다.
- `dev`: 개발 기준 브랜치. 직접 커밋하지 않고, 작업 브랜치는 여기서 만든다. (`make setup` 이 `main`·`dev` 를 만든다)
- 작업 브랜치: `feature/<작업>` 또는 `issue-123/<작업>` (이슈 단위), 긴급 수정 `hotfix/<작업>`.
- 흐름: dev 에서 브랜치 생성 → 커밋 → PR → 리뷰 → dev 에 merge. PR 결합은 merge, 개인 브랜치 정리는 rebase.
- 하네스(vibe-build·vibe-refactor)는 PR 대신 **모든 검증 통과 후 dev 에 `--no-ff` 자동 merge** 한다 — 이름은 `feature/{spec 번호}-{slug}`, 긴급 수정 `hotfix/{spec 번호}-{slug}`, 코드 정리 `feature/refactor-{slug}`. `main`·`dev` 위의 커밋은 `.claude/hooks/git-guard.sh` 가 막는다 (절차: `.claude/skills/COMMON.md` §3-B).

### 커밋
커밋 직전 `.claude/hooks/commit-msg-check.sh` 가 첫 줄 형식을 검사하고, 틀리면 커밋을 막는다.

**메시지 구조**
```
type: subject

body (선택)

footer (선택)
```
- `type` 은 **소문자**. 필요하면 scope 를 붙인다: `feat(post): 게시글 검색 추가`
- `subject` 는 한국어로 "무엇을 왜" 한 줄, 끝에 마침표 없음. 짧은 커밋 권장.
- 본문·푸터는 제목과 빈 줄로 구분한다.

**타입**

| type | 용도 |
|---|---|
| `feat` | 새로운 기능을 추가 |
| `fix` | 버그 수정 |
| `design` | CSS 등 사용자 UI 디자인 변경 |
| `hotfix` | 급하게 치명적인 버그를 고쳐야 하는 경우 |
| `style` | 코드 포맷 변경, 세미콜론 누락 등 코드 수정이 없는 경우 |
| `refactor` | 프로덕션 코드 리팩토링 |
| `comment` | 필요한 주석 추가 및 변경 |
| `docs` | 문서 수정 |
| `test` | 테스트 코드 추가·리팩토링 (프로덕션 코드 변경 없음) |
| `chore` | 빌드 업무, 패키지 매니저·구성 등 업데이트 (프로덕션 코드 변경 없음) |
| `rename` | 파일 혹은 폴더명을 수정하거나 옮기는 작업만인 경우 |
| `remove` | 파일을 삭제하는 작업만 수행한 경우 |
| `!BREAKING CHANGE` | 커다란 API 변경의 경우 (예: `!BREAKING CHANGE: 공지 API 응답 형식 변경`) |
| `!HOTFIX` | 치명적인 버그 긴급 수정 (예: `!HOTFIX: 로그인 불가 오류 수정`) |

**예시**
- `feat: 게시글 카테고리 필터 추가`
- `fix(post): 조회수가 두 번 증가하는 문제 수정`
- `docs: 커밋 컨벤션 정리`

- 명시적 경로로만 `git add <파일>` (`git add -A` 금지).

**민감 정보 커밋 금지** (사람·Claude 공통, 우회 금지)
- 커밋 직전 git 훅(`.githooks/pre-commit` → `scripts/check_secrets.py`)이 스테이징된 파일을 검사해 막는다. CI 도 같은 검사를 전체 파일에 돌린다.
  - 파일: `.env`·`.env.*`(`.env.example` 만 허용), 인증서·개인키(`*.pem`·`*.key`·`id_rsa*` 등), `credentials*.json`·서비스 계정 키, `*.tfstate`, 로컬 DB 파일
  - 내용: 개인키 블록, AWS·GitHub·Slack·Google·Anthropic·OpenAI·Stripe 키, npm 토큰, 외부 호스트 DB 접속 문자열의 비밀번호
- 걸리면 해당 파일을 스테이징에서 빼고(`git restore --staged`), 값은 `.env` 로 옮긴다. 오탐인 줄만 끝에 `secret-scan: allow` 주석.
- `git add -f`, `git commit --no-verify`/`-n`, `core.hooksPath` 변경은 Claude 훅(`.claude/hooks/git-guard.sh`)이 차단한다. 훅 활성화는 `make setup` 이 한다.

### PR
- 제목: `[태그] 간결한 설명` — 예: `[Fix] 채팅방 인원수 에러 해결`
- 본문 항목:
  ```markdown
  ## ✨ 변경 사항 (Changes)
  ## 🚀 구현 내용 (Implementation Details)   — 변경 이유·구현 방식·리팩토링 여부
  ## 🛠 추가 고려 사항 (Additional Context)    — 리뷰어가 알아야 할 정보, 관련 문서 링크
  ## ✅ 체크리스트 (Checklist)                 — - [ ] 코드가 정상적으로 동작하는지 확인했나요?
  ## 📢 리뷰어에게 (For Reviewers)             — 집중해서 볼 포인트, @멘션
  ```

### 금지 (이 하네스)
- Claude 는 `git push` 하지 않는다 (settings 에서 차단 — PR 생성은 사람이). `git reset --hard`, `push --force` 금지.
- `.env`, `.env.local` 읽기·출력 금지 — 설정 예시는 `.env.example` 에 추가.

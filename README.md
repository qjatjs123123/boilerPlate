# My App — 말로 만드는 웹앱 템플릿

코딩을 몰라도 Claude에게 **원하는 기능을 말로 설명**하면, 화면(Next.js)과 서버(FastAPI)·데이터베이스까지 만들어지고 자동으로 검사됩니다.

## 1. 한 번만 설치하기

| 설치할 것 | 받는 곳 |
|---|---|
| Docker Desktop | https://www.docker.com/products/docker-desktop (설치 후 실행해 두기) |
| Node.js (LTS) + pnpm | https://nodejs.org → 설치 후 터미널에 `npm install -g pnpm` |
| Python 3.11+ + uv | Mac: `brew install python` / WSL: 기본 포함 → `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Claude Code | https://claude.com/claude-code |

빠진 게 있어도 괜찮습니다. Claude가 처음에 점검하고 무엇을 설치해야 하는지 알려 줍니다.

## 2. 사용하기

```bash
git clone <이 저장소 주소> my-app
cd my-app
claude
```

처음 실행하면 "이 폴더를 신뢰하시겠습니까?"라고 묻습니다 → **Yes**를 고르세요. (그래야 자동 설정이 켜집니다)

그다음은 **그냥 말하면 됩니다.**

- "방명록 기능 만들어줘. 이름이랑 한 줄 메시지를 남길 수 있게"
- "공지사항 목록에 작성일 기준 정렬 버튼 추가해줘"
- "만든 거 보여줘"
- "이 앱 구조 설명해줘"

처음 실행하면 Claude가 개발 환경(DB, 라이브러리)을 먼저 준비합니다. 몇 분 걸릴 수 있어요.

## 3. 뒤에서 자동으로 일어나는 일 (하네스)

| 단계 | 하는 일 |
|---|---|
| 요구사항 확인 | 무엇을 만들지 쉬운 질문 몇 개로 확정 |
| 설계 문서 | 작업을 작은 단계로 쪼갠 계획서 작성 (`backend/spec`, `frontend/spec`) |
| 구현 + 테스트 | 단계마다 테스트를 통과해야 다음으로 진행 |
| 규칙 강제 | 정해진 코드 구조를 어기면 자동으로 막히고 고쳐짐 |
| 최종 검증 | 실제 브라우저로 화면을 눌러 보고 에러가 0개인지 확인 |
| 마무리 게이트 | 검사를 통과하지 못하면 "끝났다"고 하지 못하게 막음 |

## 4. 알아두면 좋은 것

- 결과 확인: http://localhost:3000 ("보여줘"라고 말하면 Claude가 켜 줍니다)
- 처음에는 홈 화면만 있습니다. 기능을 말로 요청하면 같은 구조로 하나씩 만들어집니다.
- 로그인은 아직 **개발용 임시 방식**입니다. 실제 서비스로 공개하기 전에 개발자에게 인증 교체를 요청하세요.
- 작업 내용은 자동으로 git 커밋되지만, 인터넷(GitHub)에 올리는 `push`는 하지 않습니다.

---

개발자용 문서: [AGENTS.md](AGENTS.md) · [ARCHITECTURE.md](ARCHITECTURE.md) · [docs/architecture/LAYERS.md](docs/architecture/LAYERS.md) · [CLAUDE.md](CLAUDE.md)

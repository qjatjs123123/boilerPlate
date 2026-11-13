# 코딩 규칙 — 백엔드

`ruff format` 이 편집 직후 자동 적용된다 (`.claude/hooks/post-edit-format.sh`). 포맷터와 충돌하면 포맷터가 우선이다.

## 네이밍
- 변수·함수: `snake_case` (`total_price`, `calculate_tax_amount`)
- 클래스: `PascalCase` (`User`, `UserService`)
- 상수: `UPPER_SNAKE_CASE`, 모듈 상단에 선언 (`MAX_RETRY_COUNT = 3`)
- 비공개 변수·메서드: 앞에 `_` (`self._private_data`, `def _internal_method`)
- 약어 지양 — `usr`, `cnt`, `tmp` 대신 `user`, `count`, `temp_file` 처럼 풀어 쓴다.

## 포맷팅
- 문자열은 큰따옴표(`"`) 기본.
- 들여쓰기 4칸 공백 (ruff format 기준 — 탭은 포맷터가 공백으로 바꾼다).
- 빈 줄: import 블록 뒤 2줄, 최상위 클래스·함수 사이 2줄, 클래스 안 메서드 사이 1줄.
- 연산자(`=`, `+`, `*` …) 양옆 공백. 콤마·콜론·세미콜론은 앞 공백 없이 뒤에만 (`[1, 2, 3]`, `{"key": "value"}`).
- 코드 반복 최소화 — 같은 로직이 두 번 나오면 헬퍼로 뺀다.

## import
- 파일 상단에만 둔다. 함수·코드 중간 import 지양 (순환 import 회피 등 불가피한 경우만).
- 한 줄에 모듈 하나 (`import os` / `import sys`). 한 모듈에서 여러 항목은 한 줄 가능 (`from subprocess import PIPE, Popen`).
- 절대경로 import (`from app.domains.post.models import Post`). 상대경로는 필요한 경우에만.
- 순서: 표준 라이브러리 → 서드파티 → 로컬(`app.*`), 그룹 사이 빈 줄 1줄, 그룹 안은 알파벳 순. ruff 의 isort 규칙(`I`)이 자동 정렬한다.

## 기타
- API key·비밀번호 등 민감 정보와 환경변수는 `.env` 로 관리 (`app/core/config.py` 경유). 코드에 하드코딩 금지.
- 코드만 읽어도 알 수 있는 주석은 쓰지 않는다. 한 줄 주석은 `#`, 여러 줄 설명은 `"""` docstring.
- Boolean 비교에 `==` 금지 — `if is_active:` / `if not is_active:`, None 비교는 `is None` / `is not None`.

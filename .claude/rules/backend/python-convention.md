---
description: 백엔드 Python 코드 작성 또는 수정 시 (모든 레이어 공통 — 네이밍·포맷팅·import·주석)
paths:
  - "backend/**/*.py"
---

# Python Convention — 공통 코딩 규칙

**기준 문서는 `docs/backend/CONVENTIONS.md`** 다. 이 파일은 그 내용을 모든 레이어에 적용할 수 있게 구체화한 것이고, 충돌하면 CONVENTIONS.md 가 우선한다.
`ruff format` + `ruff check`(`E`, `F`, `I`, `B`, `UP`)가 편집 직후 자동 적용된다. 포맷터 결과를 손으로 되돌리지 않는다.

---

## 1. 네이밍

| 대상 | 형식 | 예 |
|---|---|---|
| 변수·함수·메서드·모듈 | `snake_case` | `total_price`, `calculate_tax_amount`, `find_by_id` |
| 클래스 | `PascalCase` | `User`, `PostService`, `PostNotFoundException` |
| 상수 | `UPPER_SNAKE_CASE` (모듈 상단) | `MAX_RETRY_COUNT = 3`, `DEFAULT_PAGE_SIZE = 20` |
| 비공개 변수·메서드 | `_` 접두사 | `self._cache`, `def _generate_slug` |

- 함수·메서드는 **동사 + 명사** — `create_post`, `count_by_author`.
- **약어 지양** — 풀어 쓴다.

  | ❌ | ✅ |
  |---|---|
  | `repo` | `repository` |
  | `stmt` | `statement` |
  | `svc` | `service` |
  | `req` / `res` | `request` / `response` |
  | `exc`, `e` | `exception` |
  | `cnt`, `tmp`, `usr` | `count`, `temp_file`, `user` |
  | `with TestClient(app) as c` | `with TestClient(app) as test_client` |

  허용 예외(약어가 곧 일반 용어인 것): `db`(세션 — `get_db`·`self.db` 프로젝트 표준), `id`, `url`, `api`, `jwt`.

## 2. 포맷팅

- 문자열은 **큰따옴표** 기본. 따옴표를 포함한 문자열만 예외.
- 들여쓰기 **공백 4칸** (탭 금지 — 포맷터가 공백으로 바꾼다). 한 줄 최대 120자.
- 빈 줄
  - import 블록 뒤 **2줄** (바로 뒤가 상수·변수 선언이면 ruff `I` 가 1줄로 맞춘다 — 그대로 둔다)
  - 최상위 클래스·함수 사이 **2줄**
  - 클래스 안 메서드 사이 **1줄**
- 공백
  - 연산자(`=`, `+`, `*`, `==` …) 양옆에 공백 — `a = b + 1`
  - 콤마·콜론·세미콜론은 **앞 공백 없이 뒤에만** — `[1, 2, 3]`, `{"key": "value"}`
  - 키워드 인자·기본값의 `=` 는 붙여 쓴다(PEP 8) — `Field(None, max_length=500)`. 단 타입 힌트가 있는 기본값은 띄운다 — `limit: int = 20`
- **코드 반복 최소화** — 같은 로직이 두 곳 이상 나오면 `_` 헬퍼나 `app/common/` 유틸로 뺀다. 같은 문자열 메시지를 여러 곳에 쓰지 않는다(상수·예외 클래스로).

```python
import logging

from app.common.logging import log_event

MAX_RETRY_COUNT = 3


class UserService:
    """사용자 유스케이스 전담"""

    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    def _ensure_active(self, user: User) -> None:
        """비활성 사용자면 예외"""
        ...


class AnotherService:
    """다른 유스케이스 전담"""
```

## 3. import

- **파일 상단에만** 둔다. 함수·메서드 안 import 금지 (순환 import 를 피할 방법이 없을 때만 예외 — 그 경우 한 줄 주석으로 이유 기록).
- **한 줄에 모듈 하나** — `import os` / `import sys` 각각. 한 모듈에서 여러 항목은 한 줄 가능 — `from sqlalchemy import Column, Integer, String`.
- **절대경로 import** — `from app.domains.post.models import Post`. 상대경로(`from .models import Post`)는 금지에 가깝게 지양.
- 와일드카드 `from x import *` 금지.
- 순서 (ruff `I` 가 자동 정렬 — 수동으로 어기지 않는다)
  1. 표준 라이브러리 (`datetime`, `logging`, `uuid` …)
  2. 서드파티 (`fastapi`, `pydantic`, `sqlalchemy` …)
  3. 로컬 (`app.*`)
  - 그룹 사이 빈 줄 1줄, 그룹 안은 `import x` 가 `from x import y` 보다 먼저, 그 다음 알파벳 순.

```python
import logging
from collections.abc import Sequence
from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.common.response import success_response
from app.domains.post.models import Post
```

## 4. 함수

- **20줄 이내**(docstring·데코레이터 제외), 단일 책임. "무엇을 하는가"를 한 문장으로 못 말하면 분리.
- **타입 힌트 필수** — 모든 인자·반환값. `Any` 금지.
- 첫 줄 **한 줄 docstring(한국어)** — 이름을 반복하지 말고 의도·제약을 적는다.
  - ❌ `"""포스트를 생성한다"""` (`create_post` 그대로) → ✅ `"""포스트 생성 — 슬러그 자동 발급, 작성자는 현재 사용자"""`
- 인자 4개 초과 → Pydantic 모델 또는 dataclass 로 묶는다.
- **early return** — 가드를 먼저, 본문은 정상 케이스만.
- **뮤터블 기본 인자 금지** — `items: list[str] | None = None`.
- 매직 넘버·문자열은 모듈 상단 상수로.
- 문자열 조합은 **f-string** (`.format()`, `%` 금지). 단 SQL 은 f-string 금지 — ORM 파라미터 바인딩만. `logger.*` 호출은 `%s` 지연 포맷 허용.
- 숨은 부수효과 금지 — 시그니처에 드러나지 않는 전역 변경 금지.

## 5. 비교

- Boolean 비교에 `==` 금지
  - ❌ `if is_active == True:` / `if is_active == False:`
  - ✅ `if is_active:` / `if not is_active:`
- None 비교는 `is None` / `is not None` (`== None` 금지).
- 예외: SQLAlchemy 컬럼 표현식은 Python `is` 를 쓸 수 없으므로 `.is_(True)` / `.is_(None)` / `.is_not(None)` 을 쓴다 (`== True` 금지).

## 6. 주석

- **코드만 읽어도 알 수 있는 주석은 쓰지 않는다** — `# 사용자 조회` 다음 줄 `user = repository.find_by_id(...)` 같은 것.
- 쓰는 경우: 이유(왜), 제약, 우회책, 비직관적 동작.
- 한 줄 주석은 `#` (`#` 뒤 공백 1칸, 인라인은 코드 뒤 공백 2칸), 여러 줄 설명은 `"""` docstring.
- 주석 처리된 죽은 코드 금지 — 지운다(git 에 남아 있다).

## 7. 설정·민감 정보

- API key, 비밀번호, DB URL, JWT secret 등은 **`.env`** 로 관리하고 `app/core/config.py` 의 `get_settings()` 로만 읽는다.
- 코드·테스트·로그에 민감 정보 하드코딩·출력 금지. `os.environ` 직접 접근 금지(`Settings` 경유).
- 새 설정값을 추가하면 `.env.example` 에도 키를 추가한다(값은 예시만).

---

## 체크리스트

- [ ] 네이밍 형식(snake/Pascal/UPPER) + 약어 없음?
- [ ] 큰따옴표, 공백 4칸, 빈 줄 규칙(import 뒤 2·최상위 2·메서드 1)?
- [ ] import 가 파일 상단, 절대경로, 표준→서드파티→로컬 순?
- [ ] 함수 20줄 이내 + 타입 힌트 + 한 줄 docstring?
- [ ] Boolean 을 `==` 로 비교한 곳 없음?
- [ ] 뻔한 주석·주석 처리된 코드 없음?
- [ ] 민감 정보가 `.env` + `get_settings()` 경유?
- [ ] `ruff check . && ruff format --check .` 통과?

## 금지 사항

- ❌ 탭 들여쓰기, 작은따옴표 기본 사용
- ❌ 함수 중간 import, 상대경로 import, `import *`
- ❌ `repo`·`stmt`·`exc` 같은 약어 변수명
- ❌ `== True` / `== False` / `== None`
- ❌ `Any` 타입, 뮤터블 기본 인자
- ❌ 코드 반복 설명 주석, 주석 처리된 코드
- ❌ 민감 정보 하드코딩

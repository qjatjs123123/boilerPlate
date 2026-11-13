---
name: backend-refactor
description: 변경된 백엔드 파일을 .claude/rules/backend 기준(중복·재사용·가독성·구조)으로 검토하고 안전 항목만 수정하는 절차.
---

# backend/refactor — 변경된 백엔드 파일 리팩토링 검토

> 절차 스킬 — 슬래시 커맨드가 아니다. 표기법·vibe-build 모드·커밋 절차·spec 번호 규칙은 **`.claude/skills/COMMON.md` 를 먼저 읽고** 따른다.

> **vibe-build 모드** — 공통 규칙은 `COMMON.md` §2 (하위 스킬은 커밋 없음 · 워크트리는 Task별 커밋 · 중간 확인 없음). 이 스킬만의 차이: 대상은 호출자가 정한다 — 워크트리 방식은 `--spec {NNN}`(도우미 Task 커밋이 작업 브랜치에 merge 되어 남아 있다) **+ 워킹트리 미커밋 변경**을 합친 목록, 직접 방식은 **워킹트리 변경 파일**(기본 모드). 적용한 수정은 커밋하지 않는다 (vibe-build 14단계 검증 반영 커밋에 포함). 1️⃣ 의 파일 목록은 보여주지 않고 진행하며, 이번 요청과 무관해 보이는 파일은 검토에서 빼고 보고에만 남긴다.

`git`으로 식별한 **현재 변경된 파일**을 `.claude/rules/backend/` 기준으로 검토하고 개선안을 제시한다.

**우선순위 (이 순서대로 본다):**
1. **중복 최소화** — 같은 쿼리/검증/변환 로직이 두 곳 이상에서 반복되는지
2. **재사용성** — 추출하면 다른 도메인에서도 쓸 수 있는 단위인지
3. **가독성** — 위→아래 한 흐름으로 읽히는지, 매직 넘버·복잡 조건·깊은 중첩 없는지
4. **구조 개선** — 단일 책임, 레이어 경계, envelope 준수

이 4가지가 1순위. 그 외 룰(네이밍·타입 힌트 등)은 발견되면 부수적으로 보고하되 우선 다루지 않는다.

---

## 입력 형태

- `backend/refactor` — **검토만**. 위반 사항과 제안을 출력하고 끝. 자동 수정 안 함.
- `backend/refactor --apply` — 의미가 명확하고 안전한 항목만 Edit 도구로 직접 수정. 구조 변경(레이어 이동·메서드 분리 등)은 항상 제안만 하고 사용자 확인 후 진행.
- `backend/refactor --spec {NNN}` — 워킹트리 대신 **해당 spec의 커밋들이 변경한 파일**을 대상으로 검토. `--apply`와 조합 가능 (`backend/spec-run` 완료 시퀀스와 vibe-build 10단계 워크트리 방식이 `--spec {NNN} --apply` 로 호출).
- `backend/refactor {파일 경로...}` — 지정한 파일만 검토.

---

## 실행 절차

### 1️⃣ 변경 파일 수집

인자에 따라 수집 방식이 갈린다:

- **인자 없음 (기본)** — 워킹트리의 변경 파일:
  ```bash
  git status --porcelain
  git diff --name-only HEAD
  ```
- **`--spec {NNN}`** — 해당 spec의 커밋들이 변경한 파일 (Task 단위 커밋 후 워킹트리가 깨끗한 상태용):
  ```bash
  git log --grep="(spec {NNN}" --name-only --pretty=format: | sort -u
  ```
  커밋 메시지 형식 `{type}: {요약} (spec {NNN} Task {k})` 를 전제로 한다. spec 번호는 backend·frontend 가 공유하므로 아래 경로 필터(backend 코드만)로 이 영역 파일만 남긴다. 매칭 커밋이 0개면 사용자에게 알리고 종료.
- **파일 경로 인자** — 주어진 목록을 그대로 사용.

수집 방식과 무관하게 아래 필터를 동일하게 적용한다:
- modified / untracked / staged 모두 포함
- 확장자: `.py` 만 (md/toml/ini/yml 제외)
- 경로: 백엔드 코드만 — `backend/` 이하 (`backend/app/`, `backend/tests/`)
- 제외: `venv/`, `alembic/versions/`(자동 생성 마이그레이션), `__pycache__/`

결과가 **0개**면 "변경된 코드 없음"으로 정상 종료.

수집 후 사용자에게 파일 목록을 먼저 보여주고 진행한다 — 의외의 파일이 포함되면 멈출 수 있게.

### 2️⃣ 파일 경로 → 적용 룰 매핑

| 파일 경로 패턴 | 적용 룰 |
|---|---|
| `app/domains/*/router.py` | `router-layer.md` + `exception-handling.md` + `python-convention.md` |
| `app/domains/*/service.py` | `service-layer.md` + `exception-handling.md` + `python-convention.md` |
| `app/domains/*/repository.py` | `repository-layer.md` + `python-convention.md` |
| `app/domains/*/schemas.py` | `schema-layer.md` + `python-convention.md` |
| `app/domains/*/models.py` | `model-layer.md` + `db-design.md` + `python-convention.md` — `backend/data-model.yaml` 과 불일치·정규화 위반은 자동 수정하지 말고 보고 |
| `app/domains/*/exceptions.py`, `app/common/**` | `exception-handling.md` + `python-convention.md` |
| `tests/**` | `test-convention.md` + `python-convention.md` |
| 그 외 `.py` | `python-convention.md` |

룰 파일은 `.claude/rules/backend/{name}.md` 로 읽는다.

### 3️⃣ 우선순위별 검토

**변경 파일 안만 보지 말 것** — 중복·재사용성은 *다른 파일*과 비교해야 보인다. `backend/app/domains/**`, `backend/app/common/**` 를 grep으로 함께 확인.

#### 🥇 1순위: 중복 최소화
- **동일/유사 쿼리 반복** — 같은 `select` 조건·eager load 조합이 여러 repository 메서드에 있는지. 발견 방법: `selectinload`, 모델명, 필터 컬럼으로 grep.
- **동일/유사 검증·변환 반복** — 같은 존재 확인(`if x is None: raise`), 같은 slug 생성, 같은 커서 인코딩이 여러 service에 있는지.
- **단, "지금 중복" ≠ "추상화 대상"** — 도메인이 갈라질 가능성이 있으면 통합 권장하지 않는다. 진짜 항상 같이 바뀔 코드만 추출 후보.
- **상수·매직 값 중복** — 같은 숫자/문자열이 여러 파일에 박혀 있으면 모듈 상단 상수 또는 `app/core/config.py`로.

#### 🥈 2순위: 재사용성
- 도메인 무관 순수 함수(slug 생성, 커서 인코딩, 시간 계산)가 service 안에 인라인 → `app/common/` 또는 도메인 `utils.py`로.
- 페이지네이션·envelope 조립을 도메인이 직접 구현 → `app/common/pagination.py`·`response.py` 사용으로 교체.
- 여러 도메인에서 쓸 수 있는 예외 패턴 → `app/common/exceptions.py` 베이스 활용.

#### 🥉 3순위: 가독성
- **함수 길이** — 20줄 초과면 분리 검토 (`python-convention`).
- **중첩 3단계+** — early return으로 평탄화.
- **복잡 조건** — `is_owner = post.author_id == user.id` 같은 이름 있는 변수로 추출.
- **매직 넘버/문자열** — 상수로.
- **타입 힌트 누락** — 인자·반환.

#### 4순위: 구조 개선
- **레이어 경계 위반** — 라우터의 직접 쿼리(`select`/`db.query`), 서비스의 `HTTPException`, 리포지토리의 `commit()`, 스키마의 DB 접근.
- **envelope 미준수** — `success_response` 없이 dict/스키마 원본 반환, `{"detail": ...}` 형식.
- **도메인 간 직접 import** — 다른 도메인의 service 호출, 다른 도메인 repository를 deps 주입 없이 생성.
- **단일 책임 위반** — 한 service 메서드가 여러 유스케이스 처리, 한 라우터 함수에 비즈니스 분기.
- **트랜잭션 경계 위반** — repository의 commit, service 쓰기 메서드에 commit 누락.

### 4️⃣ 보고서 출력 형식

우선순위 라벨(🥇🥈🥉4)을 붙여 사용자가 한눈에 중요도를 보게 한다.

```
## app/domains/post/service.py
**적용 룰**: service-layer, exception-handling, python-convention

🥇 중복 최소화
- comment/service.py 와 동일한 "존재 확인 + 권한 확인" 5줄이 반복 (line 41-45)
  → 공통화는 보류 권장 — 도메인별 예외 클래스가 달라 갈라질 가능성 높음

🥉 가독성
- create_post 28줄 — slug 생성·태그 연결을 private 헬퍼로 분리 권장
- 매직 넘버 10 (태그 최대 개수) → MAX_TAGS 상수 (자동 수정 가능)

4️⃣ 구조 개선
- line 52: raise HTTPException(403) → PostForbiddenException 으로 교체 [service-layer §3]
```

마지막에 요약:
```
## 요약
- 검사 파일: 4개
- 🥇 중복: 2건  🥈 재사용성: 1건  🥉 가독성: 5건  4️⃣ 구조: 3건
- 자동 수정 가능: 4건 / 수동 확인 필요: 7건
- `backend/refactor --apply` 로 자동 수정 항목만 적용 가능
```

### 5️⃣ `--apply` 모드

`backend/refactor --apply` 호출 시 **안전 항목만** Edit 도구로 수정.

자동 수정 OK:
- 매직 넘버 → 상수 (같은 파일 내 상수 선언)
- early return으로 중첩 축소 (동작 불변이 명백할 때만)
- 사용 안 하는 import 제거
- 타입 힌트 보강 (기존 동작에서 타입이 명백할 때만)
- 인라인 복잡 조건 → 이름 있는 변수 추출
- f-string 아닌 포맷 → f-string (SQL 제외)

자동 수정 **금지** (제안만):
- 함수/메서드 분리, 파일 이동, 레이어 이동
- 중복 코드 통합 (갈라질 가능성 사용자 판단 필요)
- 외부 시그니처(인자·반환 타입) 변경
- 트랜잭션 경계 변경 (commit 위치 이동)
- 예외 클래스 교체 등 응답 계약에 영향 주는 변경
- 비즈니스 로직 변경

수정 후 `pytest`를 실행해 회귀가 없는지 확인하고, 다시 보고서를 출력해 어떤 항목이 적용됐는지 명시.

**완료 커밋**: 수정 항목이 1건 이상이고 `pytest`가 통과하면 수정 파일만 **명시적 경로로 `git add`** 후 `refactor: {대상 요약} (backend/refactor --apply)` 메시지로 커밋한다 (`git add -A` 금지, push 금지). 테스트 실패 시 커밋하지 않고 보고한다.
단, **커밋을 관장하는 다른 스킬이 호출한 경우**(예: `backend/spec-run` 완료 시퀀스의 `--spec {NNN}` 호출, vibe-build 10단계, vibe-refactor — `COMMON.md` §2·§2-B)에는 직접 커밋하지 않고 호출자의 커밋 규칙에 맡긴다.

---

## 안전 가드

- **변경 파일 50개 초과** 시 진행 전 사용자 확인.
- **테스트 파일**은 별도 섹션, 우선순위 1~2(중복/재사용)만 가볍게 본다.
- **자동 생성 파일**(`alembic/versions/`)은 무시.
- **중복 통합 제안은 반드시 "갈라질 가능성" 한 줄 평가를 동반.**

---

## 출력 규칙

- 위반 0건 파일은 `✅ 위반 없음`만 표시.
- 각 항목에 **룰 출처**(`[service-layer §3]` 등)를 적어 근거 추적 가능하게.
- 코드 제안은 가능하면 diff 블록으로.
- 1순위(중복)·2순위(재사용성) 항목이 가장 위, 3·4순위는 그 아래.

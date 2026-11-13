---
name: backend-spec-create
description: 백엔드 기능 요구사항을 spec/backend/NNN-*.md 작업 계획 문서로 정리하는 절차 (코드 작성 없음). vibe-build 3단계에서 읽는다.
---

# backend/spec-create — 백엔드 요구사항을 spec 문서로 정리

> 절차 스킬 — 슬래시 커맨드가 아니다. 표기법·vibe-build 모드·커밋 절차·spec 번호 규칙은 **`.claude/skills/COMMON.md` 를 먼저 읽고** 따른다.

> **vibe-build 모드** — 공통 규칙은 `COMMON.md` §2 (메인에서는 커밋 없음 · 워크트리는 Task별 커밋 · 중간 확인 없음). 이 스킬만의 차이: spec 파일과 색인은 미커밋으로 둔다 (spec-reviewer PASS 후 vibe-build 5단계가 작업 브랜치에 커밋). Task 의 "커밋" 필드는 워크트리·단독 실행용으로 그대로 적는다.

사용자가 전달한 백엔드 기능 요구사항을 분석해 **`spec/backend/` 폴더**(레포 루트의 `spec/` 아래)에 **작업 계획 문서(md)** 를 생성하고, 색인 `spec/README.md` 에 한 줄을 추가한다. 폴더가 없으면 먼저 생성한다.
**모든 개발 요청은 spec 을 남긴다** — 문구·색 하나 바꾸는 작은 수정이나 버그 수정도 예외 없음. 작은 요청은 요구사항 3줄 + Task 1개로 축약해도 된다 (버그면 원인·수정 내용을 요구사항에 적는다).
**이 스킬은 코드를 절대 작성하지 않는다** — 산출물은 spec 문서 하나뿐이다. 구현은 `backend/spec-run`이 담당.

## 입력 형태

```
backend/spec-create <기능 요구사항 설명>
```

입력: 이 스킬을 따르라고 지시한 쪽이 넘겨준 내용 (위 형태 중 하나)

---

## 실행 절차

### 1️⃣ 컨텍스트 수집

- 루트 `CLAUDE.md`, `backend/CLAUDE.md`(특히 「도메인 구성」·「응답 Envelope」 섹션)를 읽는다. 기존 엔드포인트 목록은 `frontend/swagger/docs.md` 에서 확인한다.
- 관련 rules(`.claude/rules/backend/*.md`)에서 해당 레이어의 테스트 규약을 확인한다.
- Task 의 "작업"에 클래스·함수·메서드 이름을 적을 때는 해당 레이어 rules 의 **네이밍** 절을 먼저 읽고 그 규칙대로 짓는다 (`repository-layer.md` 메서드 이름 표 — `find_by_*`·`find_all_*`·`count_*`·`save`·`delete`, `router-layer.md`·`schema-layer.md` 「네이밍」, `python-convention.md` 「1. 네이밍」). 도우미는 spec 에 적힌 이름을 그대로 쓰므로 여기서 틀리면 코드까지 틀린다.
- API 엔드포인트를 추가·변경하면 `.claude/skills/backend/api-spec/SKILL.md` 를 읽고, spec 의 「API 설계」를 그 템플릿(응답 형태·status·에러표)으로 작성한다. **이 섹션은 화면 개발의 계약이다** — vibe-build 는 서버 구현 전에 화면을 이 섹션대로 동시에 만들고, 구현 후 실제 API 와 대조한다. 엔드포인트마다 파라미터·Request/Response 필드(타입·nullable)·status·에러 message 를 빠짐없이 적고, api-spec 체크리스트를 통과시킨다. `TODO(확인 필요)` 가 남으면 열린 질문으로 올린다.
- 기존 코드 중 이번 기능과 겹치는 부분(같은 도메인의 `app/domains/{domain}/`)을 grep으로 파악한다.
- `spec/README.md` 색인에서 이번 기능과 관련된 기존 spec(같은 기능의 이전 작업, `spec/frontend/` 의 짝 문서 포함)을 찾아 **읽는다**. 이전 spec 의 요구사항·결정 사항은 이어받고, 바뀌는 점은 이번 spec 에 명시한다.

### 2️⃣ 요구사항 분석

- 요구사항을 **검증 가능한 단위**(FR-1, FR-2, ...)로 쪼갠다. "~할 수 있다" 형태로.
- 모호한 부분은 **추측으로 채우지 말고** 사용자에게 질문한다. 답을 받기 전엔 해당 부분을 "열린 질문" 섹션에 남긴다.
- 이번에 다루지 않을 것을 "범위 제외"에 명시한다.

### 2️⃣-B 데이터 모델 설계 (테이블 추가·변경이 있으면 필수)

DB 테이블을 새로 만들거나 바꿔야 하면 **Task 분해 전에** 설계를 끝낸다. 사용자는 DB 를 모르므로 설계 품질은 이 단계가 전부 책임진다.

1. `backend/db-design`(`.claude/skills/backend/db-design/SKILL.md`)을 읽고 **0단계**(개념 지도·전체 스키마·기존 FR 확인 → 기존 개념 매핑, 확장 vs 신설)부터 1~5단계(엔티티 → 관계 → 정규화 변환 → 3NF 자가 점검 → 규약)까지 **순서대로 전부** 수행한다. "이번 기능에 필요한 테이블"부터 그리지 않는다.
2. 결과를 spec 의 "데이터 모델" 섹션에 적는다 — **결정 기록**(새/변경 테이블마다 신설·확장 이유와 비교한 기존 테이블) + yaml 블록(추가·변경 테이블만). 0단계에서 기존 구조 부채를 찾았으면 「구조 부채」 메모를 덧붙인다(이번 Task 로 고치지 않음). 이 단계에서는 `backend/data-model.yaml` 을 수정하지 않는다.
3. **Agent 툴로 `db-design-reviewer` 서브에이전트를 호출**한다 — 프롬프트에 요구사항 원문, FR 목록, spec 파일 경로를 넣는다.
   - `FAIL` → 지적 항목을 전부 반영해 블록을 고치고 다시 호출. **`PASS` 가 나올 때까지 최대 3회.**
   - `QUESTIONS` 가 있으면 그 질문(화면·생활 언어)을 사용자에게 묻고, 답을 반영해 재검증한다.
   - 3회 안에 `PASS` 가 안 나오면 남은 지적을 열린 질문으로 옮기고 사용자에게 쉬운 말로 묻는다.
4. `PASS` 를 받으면 "설계 검증" 줄에 날짜와 함께 기록한다. **PASS 없는 spec 은 커밋하지 않는다.**

### 3️⃣ Task 분해

- **Task 1개 = 테스트 가능한 최소 단위 1개.** 레이어·관심사가 다르면 Task를 나눈다.
- backend는 4계층 의존성 방향을 따라 아래에서 위 순서로:
  `models → repository → service → router → 통합 테스트` (각 레이어 rules 문서의 테스트 규칙 준수)
- **models Task의 작업은 "spec 데이터 모델 블록을 `backend/data-model.yaml` 에 반영 → models.py 를 그대로 작성 → `alembic/env.py` 등록 → `docs/backend/DOMAIN-MAP.md` 개념 행 갱신 → `backend/scripts/gen_erd.py` 로 ERD 재생성"** 이다.
- **models Task의 통과 기준**: `pytest tests/architecture`(설계 일치·정규화·테이블 간 중복 검사) + `alembic revision --autogenerate` + 파일 검토 + `alembic upgrade head` + `alembic check`("No new upgrade operations") + `gen_erd.py --check`(ERD 최신). 파일 목록에 `backend/data-model.yaml`, 마이그레이션 파일, `docs/backend/DOMAIN-MAP.md`, `docs/backend/ERD.md` 를 포함한다.
- **모든 Task에 pytest 테스트 코드를 명시한다** — 테스트 파일 경로(`tests/unit/domains/{domain}/test_{layer}.py` 또는 `tests/api/test_{domain}.py`), 검증 항목, 실행 명령(`pytest <경로>`). **`make check-backend` 같은 기계적 기준은 보조 수단일 뿐, 테스트 코드를 대체할 수 없다.**
- **모든 Task에 "검증" 필드를 명시한다** — Task 성격별로:
  - router·통합 테스트 Task: `backend/verify`(서버 기동 + curl 엔드포인트 실검증) 필수 — status code·envelope 형식 확인이 통과 기준.
  - models~service Task: `make check-backend` 등 기계적 수단.
- **모든 Task에 "커밋" 필드를 명시한다** — `{type}: {요약} (spec {NNN} Task {k})` 형식(type: feat|fix|refactor|test|chore — 허용 type 전체는 `docs/CONVENTIONS.md` "### 커밋")으로 커밋 메시지를 미리 작성. `backend/spec-run`이 Task 통과 시 이 메시지로 커밋한다.
- Task 간 의존 관계가 순서에 반영되어야 한다 — 앞 Task의 산출물 없이는 뒤 Task를 시작할 수 없게.
- **Task 경계 = 커밋마다 green** — Task 하나를 끝낸 커밋에서 lint·타입·테스트가 통과해야 한다. 타입·시그니처를 바꾸는 Task 는 그 소비자(매퍼·호출부·기존 테스트 데이터)를 **같은 Task** 에서 고친다. 기존 함수를 지우는 일은 호출부를 교체하는 Task 에 둔다.
- **"커밋" type 은 `docs/CONVENTIONS.md` 표대로** — 기능·화면이 늘면 `feat`, 동작 변화 없는 구조 변경만 `refactor`. 한 Task 에 둘이 섞이면 `feat`.
- **모든 Task에 "묶음" 필드를 명시한다** — 기준은 `COMMON.md` §5. 도메인이 2개 이상이면 models Task·빈 router·`app/main.py` 등록을 `서버-기반` 으로 모으고(먼저), 나머지는 `서버-{도메인}` 으로 도메인별 연속 배치한다. 도메인이 1개면 전부 `서버-{도메인}` 하나이고, 이때는 그 묶음이 공유 파일 소유자라 models Task 를 맨 앞에 둔다. 도메인이 2개 이상일 때만 도메인 묶음 Task 의 "파일" 에 공유 파일(§5)이 들어가지 않게 한다.

### 4️⃣ spec 파일 생성

- 번호·파일명·템플릿·상단 메타·색인 갱신은 **`COMMON.md` §4** 대로 한다. 이 스킬의 영역은 `backend` → `spec/backend/{NNN}-{기능명}.md`, 색인 줄의 영역 칸에 `backend`, 상태는 `📝 계획됨`.
- **생성 후 spec 파일과 색인만 커밋** (`COMMON.md` §3): `spec/backend/{NNN}-{기능명}.md`·`spec/README.md` 를 명시적 경로로 add → `docs: spec {NNN} {기능명} 작성 (spec-create)`. 단, 열린 질문이 남아 사용자 답변으로 spec이 곧 수정될 예정이면 답변 반영 후 커밋한다.

### 5️⃣ 사용자 확인

생성 후 호출한 쪽에 다음을 넘긴다 (사용자는 비개발자 — 명령어를 안내하지 않는다):
- spec 파일 경로
- Task 목록 요약 (번호 + 제목 + 테스트 한 줄)
- 열린 질문이 있으면 강조 — 사용자에게는 화면·동작 기준의 쉬운 말로 바꿔 묻는다

---

## 금지 사항

- ❌ 코드 파일 생성·수정 (spec 문서만 산출)
- ❌ 테스트 없는 Task 작성 — 모든 Task는 기계적으로 검증 가능한 통과 기준 필수
- ❌ backend/CLAUDE.md·기존 코드 확인 없이 기억·추측으로 API 스키마나 파일 구조 서술
- ❌ 응답 envelope 포맷(`exception-handling.md` 스펙)을 임의 변형한 응답 설계
- ❌ 열린 질문이 있는데 임의로 결정하고 진행
- ❌ 테이블 추가·변경이 있는데 데이터 모델 섹션 없이, 또는 db-design-reviewer `PASS` 없이 spec 확정
- ❌ 결정 기록(신설·확장 이유) 없이 새 테이블 설계, 「구조 부채」를 이번 Task 에 슬쩍 끼워 고치기
- ❌ 사용자에게 "정규화", "1:N", "FK" 같은 DB 용어로 질문

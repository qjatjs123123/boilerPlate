# Spec: {기능명}

> **상태**: 📝 계획됨 <!-- 📝 계획됨 | 🚧 진행중 | ✅ 완료 -->
> **생성일**: {YYYY-MM-DD}
> **대상 영역**: frontend | backend | 공통
> **관련 도메인**: {domain}
> **짝 문서**: spec/{frontend|backend}/{NNN}-{기능명}.md <!-- 같은 요청의 다른 영역 spec, 없으면 — -->
> **관련 spec**: {이전 번호들} <!-- 같은 기능의 이전 작업, 없으면 — -->

---

## 1. 요구사항

### 배경 / 목적
<!-- 이 기능이 왜 필요한지 1~3문장 -->

### 기능 요구사항
<!-- 검증 가능한 단위로 나열. "~할 수 있다" 형태 -->
- **FR-1**:
- **FR-2**:

### 비기능 요구사항 / 제약
<!-- 성능, 접근성, 보안 등. 없으면 "없음" -->

### 범위 제외 (Out of Scope)
<!-- 이번 spec에서 다루지 않는 것을 명시해 스코프 확장 방지 -->

---

## 2. 설계 개요

### 영향받는 레이어 / 파일
<!-- 생성·수정할 파일 목록. frontend는 `.claude/rules/frontend/architecture.md` 「새 기능 하나가 거치는 파일 (만드는 순서)」 순서,
     backend는 models → repository → service → router → 통합 테스트 순서로 -->

### 데이터 모델 (backend — 테이블 추가·변경 시 필수, 없으면 "변경 없음")
<!-- db-design 스킬 절차로 작성. 추가·변경되는 테이블만, backend/data-model.yaml 의 `tables:` 아래 항목과 같은 형식
     (data-model.yaml 에 옮길 때는 `tables:` 아래에 2칸 들여써 붙인다).
     models Task 가 이 블록을 data-model.yaml 에 그대로 반영하고 models.py 를 똑같이 만든다. -->

- **결정 기록** (db-design 0단계 — 새/변경 테이블마다 1줄, 필수):
  - {신설|확장} `{테이블 또는 테이블.컬럼}` — 비교: `{기존 테이블 | 없음(진짜 새 개념)}`. {이유 — 규칙·화면이 어떻게 다른지/같은지}

```yaml
# 테이블명:
#   description: ...
#   columns:
#     id: {type: integer, primary_key: true}
#     ...
```

- **관계**: {예: users 1:N posts / posts N:M tags (post_tag)}
- **비정규화·시점 기록 사유**: {없으면 "없음"}
- **구조 부채** (0단계 전체 재점검에서 찾은 기존 구조 문제 — 이번에 고치지 않음, `backend/schema-cleanup` 대상. 없으면 "없음"): {예: `post_likes`·`post_bookmarks` 규칙이 같아 합칠 수 있음}
- **설계 검증**: db-design-reviewer {PASS — YYYY-MM-DD}

### API 의존성
<!-- 사용하는 엔드포인트. backend 는 엔드포인트를 추가·변경하면 이 아래에 「### API 설계」(backend/api-spec 템플릿)를 두고, 그것이 화면 개발의 계약이 된다.
     frontend 는 계약 출처를 명시 — vibe-build 병렬 개발이면 짝 서버 spec 의 「API 설계」, 서버 변경 없으면 swagger/docs.md 섹션 -->

### 열린 질문 (Open Questions)
<!-- 사용자 확인이 필요한 미결정 사항. 모두 해소돼야 작업 시작 가능 -->

---

## 3. 작업 순서 (Tasks)

> ⚠️ **게이트 규칙**: 각 Task는 명시된 **테스트와 검증이 모두 에러 0**이 될 때까지 수정 → 재실행을 반복하고,
> 전부 통과했을 때만 체크박스를 채우고 **Task 단위로 커밋**한 뒤 다음 Task로 진행할 수 있다.
> 테스트·검증이 실패한 상태로 체크하거나, 커밋하거나, 순서를 건너뛰는 것은 금지.
>
> 모든 Task는 **테스트 코드 필수** — `type-check`·`lint` 등 기계적 확인만으로 테스트를 대체할 수 없다.
> **UI Task는 Playwright E2E 테스트**(`e2e/*.spec.ts`)를 포함해야 한다.
>
> 모든 Task 완료 후 **`frontend/refactor` 적용 모드**(backend spec은 `backend/refactor` 적용 모드 — `.claude/skills/{영역}/refactor/SKILL.md`)가 **의무 실행**된다 —
> 이 단계를 건너뛰고 spec을 완료 처리할 수 없다. (vibe-build 로 진행할 때는 spec-run 대신 vibe-build 10단계가 수행한다.)
>
> **vibe-build 로 진행할 때는 `.claude/skills/COMMON.md` §2 가 위 규칙보다 우선한다** — 워크트리 도우미는 Task 구현 + 단위 테스트 + Task별 커밋까지만 하고,
> 리팩토링·서버 실검증·화면 검증(MCP·E2E)·spec 문서 갱신·메인 커밋은 메인(vibe-build 10~14단계)이 맡는다.

- [ ] **Task 1: {제목}**
  - **묶음**: {서버-기반 | 서버-{도메인} | 화면-기반 | 화면-{도메인}-데이터 | 화면-{도메인}-{화면}} <!-- 병렬 개발 단위 — 기준은 .claude/skills/COMMON.md §5. 같은 묶음 Task 는 연속으로 -->
  - **작업**: {무엇을 만드는지 구체적으로}
  - **파일**: `{경로}`
  - **테스트**: `{경로}/__tests__/{파일명}` — {무엇을 검증하는지} <!-- UI Task는 렌더링 테스트 + E2E 병기: `e2e/{기능}.spec.ts` — 핵심 사용자 흐름 -->
  - **실행**: `cd frontend && pnpm test {경로}` (backend: `cd backend && .venv/bin/pytest {경로}`) <!-- UI Task는 추가로: `make e2e SPEC=e2e/{기능}.spec.ts` -->
  - **검증**: {Task 성격별 — UI Task(components/pages): `frontend/browser-check` (검증 URL = 페이지 경로 + MCP 로 눌러볼 핵심 흐름 단계 나열. 통과 = 콘솔 error 0 + 실패 API 요청 0(`mcp-check.md` 기록) + 그 흐름을 고정한 e2e 통과. 스크린샷 육안 판정은 기준 아님) / 비UI frontend Task: `pnpm type-check` / backend router·통합 Task: `backend/verify` 스킬 / 그 외 backend: `make check-backend`}
  - **통과 기준**: {테스트·검증 외 추가 확인 사항 — 없으면 "테스트 + 검증 통과"}
  - **커밋**: `{type}: {요약} (spec {NNN} Task 1)` <!-- type: feat|fix|refactor|test|chore. 범위 = 이 Task의 파일 + 테스트 + spec 문서 갱신분 (vibe-build 워크트리에서는 spec 문서 제외 — 메인이 갱신) -->

- [ ] **Task 2: {제목}**
  - **묶음**:
  - **작업**:
  - **파일**:
  - **테스트**:
  - **실행**:
  - **검증**:
  - **통과 기준**:
  - **커밋**:

---

## 4. 진행 로그

<!-- Task 완료 시마다 한 줄 추가. 형식: 날짜 | Task | 테스트 결과 | 커밋(짧은 해시) | 비고 -->

| 날짜 | Task | 테스트 결과 | 커밋 | 비고 |
|---|---|---|---|---|

---
description: DB 테이블 설계·변경 시 (models.py, data-model.yaml, backend spec 의 데이터 모델 섹션) — 정규화 규칙
paths:
  - "backend/app/domains/*/models.py"
  - "backend/data-model.yaml"
  - "spec/backend/**/*.md"
---

# DB Design — 정규화·설계 일치 규칙

사용자는 DB 를 모른다. 설계 품질은 **절차(db-design 스킬) + 기계 검사(test_schema.py)** 가 보장한다.
상세 절차·정답 예시: `.claude/skills/backend/db-design/SKILL.md`. 모델 작성 규약: `model-layer.md`.

---

## 순서 (강제)

1. **설계 먼저, 전체부터** — `backend/spec-create` 에서 db-design 스킬로 설계한다. **0단계**(`docs/backend/DOMAIN-MAP.md`·`data-model.yaml` 전체를 보고 기존 개념에 매핑 — 확장 vs 신설)부터 시작 → spec "데이터 모델" 섹션에 결정 기록 + yaml 블록 → `db-design-reviewer` 에이전트 `PASS`.
2. **설계 반영** — models Task 에서 블록을 `backend/data-model.yaml` 에 반영하고 `DOMAIN-MAP.md` 개념 행·`docs/backend/ERD.md`(`backend/scripts/gen_erd.py`)를 같이 갱신.
3. **설계 그대로 구현** — `models.py` 를 data-model.yaml 과 **컬럼·타입·길이·nullable·unique·index·FK·ondelete·unique_constraints 까지 똑같이**.
4. **마이그레이션** — `alembic revision --autogenerate` → 검토 → `alembic upgrade head` → `alembic check` 가 "No new upgrade operations".

설계와 다르게 구현해야 할 이유가 생기면 **models.py 를 먼저 바꾸지 말고** data-model.yaml(과 spec 블록)을 고친 뒤 reviewer 를 다시 통과시킨다.

## 정규화 변환 (예외 없음)

변환 표와 허용되는 예외 2가지(사유 있는 정렬·표시용 카운터, 시점 기록 값)의 **원본은 `db-design` 스킬 3단계**다. `models.py`·`data-model.yaml`·spec 데이터 모델 블록을 고치기 전에 그 표를 읽는다. 아래 기계 검사는 그 표의 일부를 자동으로 잡을 뿐, 표 전체를 대신하지 않는다.

## 기계 검사 (`backend/tests/architecture/test_schema.py`)

| rule | 의미 | 고치는 법 |
|---|---|---|
| `schema-undesigned-table` | data-model.yaml 에 없는 테이블 | 설계부터 (db-design 스킬) |
| `schema-spec-mismatch` | 설계와 모델이 다름 | 모델을 설계에 맞추거나, 설계를 고치고 reviewer 재통과 |
| `schema-data-model-invalid` | yaml 오타 키·description 누락·빈 사유 | yaml 형식 수정 |
| `schema-list-in-column` | 목록을 한 컬럼에 | 자식/연결 테이블 |
| `schema-json-column` | JSON/ARRAY 타입 | 별도 테이블 |
| `schema-repeating-columns` | `x_1`, `x_2` | 자식 테이블 |
| `schema-copied-column` | `{fk접두사}_{대상컬럼}` 복사 | relationship 조회 |
| `schema-denormalized-unmarked` | `*_count`/`*_total`/`*_sum` 사유 없음 | 저장 안 하거나 `denormalized` 사유 |
| `schema-fk-ondelete` / `schema-integer-pk` / `schema-timestamps` / `schema-plural-table` / `schema-unnamed-unique` | 모델 규약 | `model-layer.md` |
| `schema-similar-tables` | FK 대상이 같고 컬럼 구성이 거의 같은 두 테이블 (중복 의심) | 종류 enum 으로 합치기 (db-design 패턴 카탈로그). 규칙이 달라 따로 둬야 하면 data-model.yaml 에 `distinct_from: {테이블: "사유"}` |
| `schema-unused-table` | 앱 코드 어디에서도 모델 클래스를 쓰지 않는 테이블 — **주간 점검(`make gc`) 보고만**, 커밋 차단 아님 (models Task 직후엔 정상) | 필요 없으면 `backend/schema-cleanup` 으로 정리 (사용자 확인) |
| `schema-alembic-registered` | `alembic/env.py` 미등록 | `import app.domains.{domain}.models  # noqa: F401` |

검사를 피하려고 컬럼명을 바꾸는 것(`tag_ids` → `tag_values`)은 **위반을 숨기는 것**이며 금지다. 규칙의 의도(정규화)를 따른다.

---

## 체크리스트

- [ ] 0단계(개념 지도·전체 스키마 매핑)를 하고 결정 기록을 남겼나?
- [ ] 설계(spec 블록 + reviewer PASS)가 models.py 보다 먼저?
- [ ] data-model.yaml ↔ models.py 완전 일치?
- [ ] 3NF 자가 점검 6문항 전부 "아니오"?
- [ ] 비정규화는 `denormalized` 사유가 있는 카운터뿐?
- [ ] `pytest tests/architecture` + `alembic check` 통과?
- [ ] DOMAIN-MAP.md 개념 행 갱신, `gen_erd.py --check` 통과?

## 금지 사항

- ❌ 설계 없이 models.py 부터 작성
- ❌ 기존 테이블과 비교 없이 "이번 기능용" 테이블 신설, `distinct_from` 을 사유 없이 검사 회피용으로 쓰기
- ❌ 기존 데이터를 옮기는 구조 정리를 기능 요청에 끼워 넣기 — `backend/schema-cleanup` 으로 따로, 사용자 확인 후
- ❌ data-model.yaml 과 다른 모델
- ❌ 콤마 문자열·JSON·번호 반복 컬럼·값 복사 컬럼
- ❌ 검사 회피용 이름 바꾸기, `known-violations.json` 에 항목 추가
- ❌ 사용자에게 "정규화", "1:N", "FK" 같은 용어로 질문

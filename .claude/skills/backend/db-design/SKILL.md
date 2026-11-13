---
name: db-design
description: DB 테이블을 새로 만들거나 바꿀 때 반드시 사용. 전체 스키마·개념 지도 확인 → 기존 개념 매핑(확장 vs 신설) → 엔티티·관계 추출 → 정규화 변환 → data-model.yaml 설계를 정해진 절차로 수행한다. models.py 를 쓰기 전에 이 절차가 끝나 있어야 한다.
---

# db-design — 요구사항에서 정규화된 테이블 설계까지

사용자는 DB 를 모른다. **설계 품질은 전적으로 이 절차가 보장한다.** 감으로 테이블을 만들지 말고 아래 단계를 순서대로, 빠짐없이 수행한다.

> **왜 0단계가 먼저인가** — 바이브 코딩에서 테이블 구조가 망가지는 주원인은 한 테이블 안의 실수보다 **요청마다 "이번 기능"만 보고 새 테이블을 만드는 것**이다 (비슷한 테이블 중복, 기존 테이블에 붙였어야 할 것을 따로 만들기). 그래서 설계는 항상 **전체 그림에서 시작**한다.

- 설계 결과의 단일 출처: `backend/data-model.yaml` (형식은 파일 상단 주석)
- 기계 검사: `backend/tests/architecture/test_schema.py` — yaml ↔ 모델 1:1 일치 + 정규화 규칙. 통과 못 하면 작업이 끝나지 않는다.
- 규칙 요약: `.claude/rules/backend/db-design.md`
- 개념 지도: `docs/backend/DOMAIN-MAP.md` (생활 언어로 "이 서비스에 있는 것들"), 그림: `docs/backend/ERD.md` (자동 생성)

---

## 0단계 — 전체 그림부터 (매핑 → 확장 vs 신설)

1. **읽기**: `docs/backend/DOMAIN-MAP.md` → `backend/data-model.yaml` **전체** → `spec/README.md` 색인에서 backend spec 마다 「기능 요구사항」(FR) 목록.
2. **매핑**: 이번 요청에 나온 명사마다 "이미 있는 개념인가?"를 먼저 판정한다. 아래 표를 **위에서부터** 적용한다.

   | 상황 | 결정 | 예 |
   |---|---|---|
   | 이미 있는 개념 그대로 | 재사용 (테이블 추가 없음) | "작성자" → `users` |
   | 기존 개념과 같은데 **종류만** 다름 | 기존 테이블에 enum 컬럼, 관리자가 종류를 늘리면 코드 테이블 + FK | 공지글 → `posts.post_type` (`notices` 신설 ❌) |
   | 기존 개념의 1:1 부가 정보 | 기존 테이블에 컬럼 | 게시글 고정 여부 → `posts.is_pinned` |
   | "사용자가 X 에 한 행동"이 또 생김 | 아래 「패턴 카탈로그 — 사용자 행동」의 합치기/나누기 기준 적용 | 북마크 (좋아요가 이미 있으면 비교) |
   | 카탈로그에 있는 모양 | 그 모양을 그대로 쓴다 | 첨부파일, 상태 이력, 카테고리 |
   | 어디에도 안 맞는 진짜 새 개념 | 신설 → 1단계로 | 예약, 결제 |
3. **전체 재점검**: 1~5단계를 끝낸 뒤, 결과 구조가 **지금까지의 모든 FR + 이번 요청**을 만족하는 전체 구조로 봐도 자연스러운지 다시 본다. 현재 구조와 다른 점은 두 가지로 나눈다:
   - **이번 변경** → spec 「데이터 모델」 블록 (6단계)
   - **기존 구조 부채** (이번 요청과 무관하게 합치거나 나눠야 할 것) → spec 「구조 부채」 메모. **이번 요청에선 고치지 않는다** — 기존 데이터를 옮기는 일이라 `backend/schema-cleanup` 절차로 사용자 확인을 받아 따로 한다.
4. **결정 기록** (spec 「데이터 모델」 블록 위, 필수): 새로 만들거나 바꾸는 테이블마다 한 줄.
   ```
   - 결정 기록:
     - 신설 `post_bookmarks` — 비교: `post_likes`. 좋아요는 공개 집계·인기순 정렬, 북마크는 본인만 보는 목록이라 규칙이 다름
     - 확장 `posts.post_type` — 공지는 게시글과 같은 화면·같은 규칙, 종류만 다름
   ```
   비교한 기존 테이블이 없으면 "비교: 없음(진짜 새 개념)" 이라고 적는다.

## 1단계 — 엔티티 추출

요구사항 문장에서 **"따로 목록을 보거나, 따로 추가·삭제하거나, 다른 것과 연결되는 명사"** 를 엔티티로 뽑는다.

| 요구사항 표현 | 판단 |
|---|---|
| "게시글을 쓰고 목록을 본다" | 게시글 = 엔티티 |
| "게시글에 태그를 단다" | 태그 = 엔티티 (태그로 검색·필터할 가능성) |
| "게시글에 제목·내용이 있다" | 제목·내용 = 속성 |
| "예약 상태(대기·확정·취소)" | 상태 = 속성 (enum) |

0단계에서 기존 개념에 매핑된 것은 엔티티로 다시 만들지 않는다 (사용자 = `users`).

## 2단계 — 관계 판정

엔티티 쌍마다 두 질문을 한다.
1. A 하나에 B 가 **여러 개** 붙을 수 있나?
2. B 하나에 A 가 **여러 개** 붙을 수 있나?

| 1 | 2 | 관계 | 구현 |
|---|---|---|---|
| 예 | 아니오 | 1:N | B 에 `a_id` FK |
| 예 | 예 | N:M | 연결 테이블 `a_b` — FK 2개를 복합 PK 로, `association: true` (복합 PK 가 곧 중복 방지라 별도 unique 불필요. 정답 예시 `post_tag`) |
| 아니오 | 아니오 | 1:1 | 한쪽에 `unique: true` FK (대개 같은 테이블에 합치는 게 낫다) |

판정이 요구사항으로 불확실하면 **더 유연한 쪽(N 쪽)으로 설계**한다. 1:N 을 N:M 으로 바꾸는 것보다 처음부터 N 으로 두는 게 안전하다. 그래도 결정이 불가능하면 4단계 끝의 "사용자 질문" 규칙을 따른다.

## 3단계 — 속성 나열 + 정규화 변환 (무조건 적용)

엔티티별 속성을 나열한 뒤, 아래 표의 패턴이 하나라도 보이면 **반드시** 오른쪽으로 바꾼다. 예외 없음.

| 발견한 패턴 | 예 | 바꾸는 방법 |
|---|---|---|
| 값이 여러 개 | `tags = "a,b,c"`, `image_urls`, `phones` | 자식 테이블 (1:N) 또는 연결 테이블 (N:M) |
| 번호 붙은 반복 컬럼 | `phone_1`, `phone_2`, `option1` | 자식 테이블 |
| 구조화된 값 덩어리 | `options = JSON`, `address = JSON` | 별도 테이블 또는 개별 컬럼 |
| 다른 엔티티 정보 복사 | posts 에 `author_name`, orders 에 `product_price` | FK 하나만 두고 relationship 으로 조회 |
| 정해진 선택지 | 상태: 대기/확정/취소 | `type: enum, values: [...]` |
| 관리자가 늘릴 수 있는 선택지 | 카테고리, 지역 | 코드 테이블 (`categories`) + FK |
| 계산 가능한 값 | 합계 금액, 나이, 댓글 수 | 저장하지 않는다 — 조회 시 계산 |
| 목록 화면 정렬·표시용 개수 | 좋아요 수로 정렬 | **유일한 비정규화 허용** — `denormalized: "사유"` + service 가 갱신 |

> **"복사"처럼 보이지만 복사가 아닌 것**: 그 시점의 값을 **기록으로 남겨야** 하는 경우 (주문 당시 가격 — 상품 가격이 나중에 바뀌어도 주문 금액은 그대로여야 함). 이때는 컬럼명을 `ordered_price` 처럼 **시점이 드러나게** 짓고 `description` 에 이유를 적는다. 원본 컬럼명을 그대로 붙인 `product_price` 는 금지.

## 4단계 — 3NF 자가 점검 (6문항 전부 "아니오" 여야 통과)

테이블마다 아래를 하나씩 확인한다. "예"가 하나라도 있으면 3단계로 돌아가 고친다.

1. 한 칸에 값이 **두 개 이상** 들어갈 수 있는 컬럼이 있나? (1NF)
2. 이름만 다르고 의미가 같은 컬럼이 **반복**되나? (`_1`, `_2`, `home_phone`/`work_phone`)
3. PK(`id`)가 아닌 **다른 컬럼에 의해 값이 정해지는** 컬럼이 있나? (예: `zip_code` 가 정해지면 `city` 가 정해짐 → 3NF 위반)
4. 다른 테이블에 이미 있는 값을 **그대로 들고 있는** 컬럼이 있나?
5. 다른 컬럼들로 **계산할 수 있는** 값을 저장하나? (사유 있는 `denormalized` 제외)
6. 이 테이블 하나가 **두 가지 이상의 것**을 저장하나? (예: 게시글과 댓글을 `type` 으로 구분해 한 테이블에)

**사용자 질문 규칙**: 위 단계에서 요구사항만으로 결정할 수 없는 점이 있으면, 테이블 용어 없이 **화면·생활 언어로** 하나씩 묻는다.
- ✅ "게시글 하나에 사진을 여러 장 올릴 수 있어야 하나요?"
- ✅ "한 사람이 같은 상품을 여러 번 예약할 수 있나요?"
- ❌ "1:N 관계로 할까요?" / "정규화할까요?"

## 5단계 — 규약 적용

- 테이블명 복수형 snake_case (`posts`), 연결 테이블은 단수 조합 (`post_tag`) + `association: true`
- 모든 일반 테이블: `id` integer PK, `created_at`, `updated_at`
- FK 는 `{대상 단수}_id` 또는 역할명(`author_id`) + `ondelete` 필수
  - 부모가 지워지면 같이 지워져야 함 → `CASCADE` (게시글 → 댓글)
  - 부모가 지워져도 남아야 함 → `SET NULL` + `nullable: true` (작성자 탈퇴 후에도 게시글 유지)
  - 자식이 있으면 부모 삭제를 막아야 함 → `RESTRICT` (주문이 있는 상품)
- Boolean 은 `is_`/`has_` 접두사 + `nullable: false`
- 문자열 길이는 실제 용도 기준 (`username` 50, `title` 255, 긴 본문은 `text`)
- 여러 컬럼 조합 유일성은 `unique_constraints: {uq_{테이블단수}_{컬럼}: [...]}`
- 검색·필터·정렬·FK 컬럼은 `index: true`

## 6단계 — data-model.yaml 작성

- spec-create 단계: spec 의 "데이터 모델" 섹션에 **결정 기록**(0단계) + **추가·변경할 테이블만** yaml 블록으로 적는다 (아직 `data-model.yaml` 은 건드리지 않는다). 0단계에서 부채를 찾았으면 「구조 부채」 메모도.
- spec-run 의 models Task: 그 블록을 `backend/data-model.yaml` 에 반영 → models.py 를 **똑같이** 작성 → 마이그레이션 → `docs/backend/DOMAIN-MAP.md` 개념 행 추가·수정 → `backend/scripts/gen_erd.py` 로 ERD 재생성.
- 스키마 검사 `schema-similar-tables` 가 잡았는데 정말 따로 둬야 하면 (결정 기록의 이유와 같은) 사유를 `distinct_from: {비슷한_테이블: "사유"}` 로 적는다. 사유 없이 이름만 바꿔 피하는 것은 금지.

## 7단계 — 독립 검증

spec-create 가 `db-design-reviewer` 서브에이전트에게 요구사항 + 설계 블록을 넘겨 검증받는다. `FAIL` 이면 지적대로 고치고 재검증 (최대 3회).

---

## 패턴 카탈로그 (발명하지 말고 고른다)

흔한 요구는 모양이 정해져 있다. 0단계에서 여기 해당하면 **이 모양을 그대로** 쓰고, 결정 기록에 "카탈로그: ○○" 라고 적는다.

| 요구 | 모양 | 주의 |
|---|---|---|
| **사용자 행동** (좋아요·북마크·신고·구독) | `{대상}_{행동}s` — `{대상}_id` + `user_id` FK, `unique_constraints` 로 1인 1회 | **합치기 기준**: 화면에서 같은 버튼 묶음이고 규칙(공개 여부·취소 가능·추가 정보)이 같으면 하나의 `{대상}_reactions` + `reaction_type` enum. 규칙이 하나라도 다르면 분리 + 결정 기록·`distinct_from` 에 그 차이 |
| 신고처럼 행동에 추가 정보 | 위 모양 + `reason` enum/text, `status` enum | 처리 상태가 있으면 행동 테이블과 분리 유지 |
| **첨부파일·이미지** (여러 장) | `{대상}_attachments` — `{대상}_id` FK CASCADE, `file_url`, `original_name`, `sort_order` | `image_urls` 컬럼 ❌. 여러 대상에 붙으면 대상마다 테이블 (다형 FK `target_type`+`target_id` ❌ — FK 무결성이 깨짐) |
| **상태 이력** (언제 누가 바꿨나) | 현재 상태는 원래 테이블 `status` enum, 이력은 `{대상}_status_histories` — `from_status`, `to_status`, `changed_by_id` | 이력이 필요 없으면 만들지 않는다 |
| **분류** (카테고리·지역) | 고정 선택지면 enum, 관리자가 늘리면 코드 테이블 `categories` + FK `RESTRICT` | 계층이면 `parent_id` 자기참조 FK |
| **삭제 후 보관** | 기본은 진짜 삭제. "지운 글 복구·관리자 열람" 요구가 있을 때만 `deleted_at` datetime nullable | 넣으면 모든 조회에 조건이 붙으니 요구 없으면 금지 |
| **1:1 부가 정보** (프로필) | 대개 원래 테이블에 컬럼. 크고 드물게 읽히면 `{대상}_profiles` + `unique: true` FK | |

## 정답 예시 (비슷한 요청이면 이 패턴을 재사용)

### 게시판 — 게시글·댓글·태그·좋아요

```yaml
posts:
  description: 게시글
  columns:
    id: {type: integer, primary_key: true}
    author_id: {type: integer, foreign_key: users.id, ondelete: CASCADE, nullable: false, index: true}
    title: {type: string, length: 255, nullable: false}
    content: {type: text, nullable: false}
    is_published: {type: boolean, nullable: false}
    like_count: {type: integer, nullable: false, denormalized: "목록을 좋아요 순으로 정렬 — 매번 집계하면 느림"}
    created_at: {type: datetime}
    updated_at: {type: datetime}
comments:
  description: 게시글 댓글
  columns:
    id: {type: integer, primary_key: true}
    post_id: {type: integer, foreign_key: posts.id, ondelete: CASCADE, nullable: false, index: true}
    author_id: {type: integer, foreign_key: users.id, ondelete: CASCADE, nullable: false}
    content: {type: text, nullable: false}
    created_at: {type: datetime}
    updated_at: {type: datetime}
tags:
  description: 태그 (이름 유일)
  columns:
    id: {type: integer, primary_key: true}
    name: {type: string, length: 30, nullable: false, unique: true}
    created_at: {type: datetime}
    updated_at: {type: datetime}
post_tag:
  description: 게시글-태그 연결 (N:M)
  association: true
  columns:
    post_id: {type: integer, primary_key: true, foreign_key: posts.id, ondelete: CASCADE}
    tag_id: {type: integer, primary_key: true, foreign_key: tags.id, ondelete: CASCADE}
post_likes:
  description: 게시글 좋아요 — 사용자당 1회
  columns:
    id: {type: integer, primary_key: true}
    post_id: {type: integer, foreign_key: posts.id, ondelete: CASCADE, nullable: false}
    user_id: {type: integer, foreign_key: users.id, ondelete: CASCADE, nullable: false}
    created_at: {type: datetime}
    updated_at: {type: datetime}
  unique_constraints: {uq_post_user_like: [post_id, user_id]}
```
❌ 흔한 오답: `posts.tags = "a,b"`, `posts.author_name`, `posts.comment_count` (사유 없음), `posts.liked_user_ids`

### 예약 — 상품·예약·결제

```yaml
products:
  description: 예약 가능한 상품
  columns:
    id: {type: integer, primary_key: true}
    name: {type: string, length: 100, nullable: false}
    price: {type: integer, nullable: false}
    capacity: {type: integer, nullable: false}
    created_at: {type: datetime}
    updated_at: {type: datetime}
reservations:
  description: 예약 — 예약 시점 가격을 기록으로 보존
  columns:
    id: {type: integer, primary_key: true}
    user_id: {type: integer, foreign_key: users.id, ondelete: CASCADE, nullable: false, index: true}
    product_id: {type: integer, foreign_key: products.id, ondelete: RESTRICT, nullable: false, index: true}
    reserved_date: {type: date, nullable: false}
    reserved_price: {type: integer, nullable: false}
    status: {type: enum, values: [pending, confirmed, cancelled], nullable: false}
    created_at: {type: datetime}
    updated_at: {type: datetime}
payments:
  description: 예약 결제 (예약당 여러 번 시도 가능)
  columns:
    id: {type: integer, primary_key: true}
    reservation_id: {type: integer, foreign_key: reservations.id, ondelete: CASCADE, nullable: false, index: true}
    amount: {type: integer, nullable: false}
    status: {type: enum, values: [requested, paid, failed, refunded], nullable: false}
    created_at: {type: datetime}
    updated_at: {type: datetime}
```
❌ 흔한 오답: `reservations.product_name`, `reservations.user_username`, `reservations.total_price`(수량×가격으로 계산 가능), `payments` 를 reservations 컬럼(`paid_at`, `pay_status`)으로 합치기

### 설문 — 설문·문항·선택지·응답

```yaml
surveys:
  description: 설문
  columns:
    id: {type: integer, primary_key: true}
    author_id: {type: integer, foreign_key: users.id, ondelete: CASCADE, nullable: false}
    title: {type: string, length: 255, nullable: false}
    created_at: {type: datetime}
    updated_at: {type: datetime}
questions:
  description: 설문 문항 (설문 안 순서 보유)
  columns:
    id: {type: integer, primary_key: true}
    survey_id: {type: integer, foreign_key: surveys.id, ondelete: CASCADE, nullable: false, index: true}
    content: {type: string, length: 500, nullable: false}
    question_type: {type: enum, values: [single, multiple, text], nullable: false}
    sort_order: {type: integer, nullable: false}
    created_at: {type: datetime}
    updated_at: {type: datetime}
  unique_constraints: {uq_question_survey_order: [survey_id, sort_order]}
choices:
  description: 문항 선택지
  columns:
    id: {type: integer, primary_key: true}
    question_id: {type: integer, foreign_key: questions.id, ondelete: CASCADE, nullable: false, index: true}
    content: {type: string, length: 255, nullable: false}
    sort_order: {type: integer, nullable: false}
    created_at: {type: datetime}
    updated_at: {type: datetime}
responses:
  description: 한 사용자의 설문 제출 1회
  columns:
    id: {type: integer, primary_key: true}
    survey_id: {type: integer, foreign_key: surveys.id, ondelete: CASCADE, nullable: false}
    user_id: {type: integer, foreign_key: users.id, ondelete: CASCADE, nullable: false}
    created_at: {type: datetime}
    updated_at: {type: datetime}
  unique_constraints: {uq_response_survey_user: [survey_id, user_id]}
answers:
  description: 문항별 답 (객관식은 choice_id, 주관식은 text_answer)
  columns:
    id: {type: integer, primary_key: true}
    response_id: {type: integer, foreign_key: responses.id, ondelete: CASCADE, nullable: false, index: true}
    question_id: {type: integer, foreign_key: questions.id, ondelete: CASCADE, nullable: false}
    choice_id: {type: integer, foreign_key: choices.id, ondelete: CASCADE}
    text_answer: {type: text}
    created_at: {type: datetime}
    updated_at: {type: datetime}
```
❌ 흔한 오답: `questions.choices = JSON`, `questions.choice_1..choice_5`, `responses.answers = JSON`, 복수 선택을 `choice_ids = "1,3"` 로 저장 (→ answers 행 여러 개)

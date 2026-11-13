<!-- ⚠️ 자동 생성 문서 — 직접 수정 금지. 갱신: backend/sync-api-docs {domain} -->
# API 계약 문서 (swagger/docs.md)

## 공통

- **Base URL**: `http://localhost:8000` (개발 기준)
- **인증**: 없음 — 로그인 기능을 요청하면 그때 추가된다
- **필드 네이밍**: 응답·요청 body는 **snake_case** (camelCase 변환은 프론트 Mapper 책임)
- **쿼리 파라미터**: **kebab-case** (`page-size`, `search-keyword`)
- **날짜**: UTC 기준, 타임존 표기 없는 ISO8601 (`"2026-01-01T09:30:00.123456"`)
- **응답 envelope** (원본 스펙: `.claude/rules/backend/exception-handling.md`):
  - 성공: `{ "status": "success", "data": ... }`
  - 목록(표준): `data = { "results": [...], "pagination": { "current_page", "num_pages", "page_size", "total_count", "has_previous", "has_next" } }`
  - 목록(커서, 피드 전용): `data = { "results": [...], "pagination": { "next_cursor", "has_next" } }`
  - 4xx: `{ "status": "fail", "data": { "code", "message", "fields" } }`
  - 5xx: `{ "status": "error", "data": { "code", "message" } }`
  - 422: `message` 는 "입력값이 올바르지 않습니다." 고정, `fields` 키는 body 필드명 / `query.{kebab}` / `path.{name}` — 필드별 메시지는 영어일 수 있으므로 화면에 그대로 쓰지 않는다

<!-- 도메인 섹션 없음 — 백엔드 도메인을 추가하면 sync-api-docs 가 `## {domain}` 섹션을 생성한다 -->

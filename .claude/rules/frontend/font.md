---
description: 앱 전역 글꼴(src/app/layout.tsx 의 next/font, src/app/globals.css 의 font-family) 설정·변경 시 — DesignKit 반입 후에만 적용, 그 전엔 글꼴을 건드리지 않는다
paths:
  - "**/src/app/layout.tsx"
  - "**/src/app/globals.css"
---

# Font — 글꼴 임베딩 규칙 (사내 표준)

글꼴은 **Next.js 내장 폰트 최적화(`next/font`)** 로만 임베딩한다. `<link>` 로 Google Fonts CSS 를 불러오거나 `@font-face` 를 직접 쓰지 않는다.

| 용도 | 글꼴 | 출처 | CSS 변수 |
|---|---|---|---|
| 영문 | Helvetica Neue | `next/font/local` — DesignKit 폰트 파일 | `--font-helvetica-neue` |
| 한글 | Noto Sans KR | `next/font/google` | `--font-noto-sans` |

> **적용 조건 — DesignKit 반입 후에만.** 현재 템플릿은 Next 기본값 `Geist` 를 쓰고 `src/components/DesignKit/` 은 없다 (위치 규칙은 `architecture.md` 「Shared Layer」).
> DesignKit 이 없는 상태에서 `layout.tsx`·`globals.css` 를 다른 이유(색 토큰 추가 등)로 수정할 때는 **글꼴을 건드리지 않는다**. 글꼴 교체는 사용자가 DesignKit 반입·글꼴 적용을 요청했을 때만 아래 형태로 한다.

---

## 1. `src/app/layout.tsx`

```tsx
import { Noto_Sans_KR } from "next/font/google";
import localFont from "next/font/local";

import { cn } from "@/lib/utils";

// 한글 — Google Fonts
const notoSansKr = Noto_Sans_KR({
  subsets: ["latin"],
  weight: ["300", "400", "500", "600", "700"],
  variable: "--font-noto-sans",
  display: "swap",
});

// 영문 — 로컬 파일 (경로는 layout.tsx 기준 상대경로 — DesignKit 위치 주의)
const helveticaNeue = localFont({
  src: [
    { path: "../components/DesignKit/public/fonts/HelveticaNeue/HelveticaNeueLTW15-45Light.woff2", weight: "300", style: "normal" },
    { path: "../components/DesignKit/public/fonts/HelveticaNeue/HelveticaNeueLTW15-55Roman.woff2", weight: "400", style: "normal" },
    { path: "../components/DesignKit/public/fonts/HelveticaNeue/HelveticaNeueLTW15-65Medium.woff2", weight: "500", style: "normal" },
    { path: "../components/DesignKit/public/fonts/HelveticaNeue/HelveticaNeueLTW15-65Medium.woff2", weight: "600", style: "normal" }, // 600 전용 파일 없음 → Medium 재사용
    { path: "../components/DesignKit/public/fonts/HelveticaNeue/HelveticaNeueLTW15-75Bold.woff2", weight: "700", style: "normal" },
  ],
  variable: "--font-helvetica-neue",
  display: "swap",
  adjustFontFallback: false,
});

// ...
<html lang="ko" className={cn(helveticaNeue.variable, notoSansKr.variable, "h-full antialiased")}>
```

> ⚠️ `next/font` 인자는 **빌드 시 정적 분석**된다 — 경로·옵션은 반드시 문자열 리터럴로 쓴다 (상수·템플릿 리터럴 변수 사용 시 빌드 에러). 줄이 길어도 그대로 둔다.

## 2. `src/app/globals.css`

```css
/* 영문 글꼴 먼저, 한글 글꼴 나중 — 영문 글리프는 Helvetica, 나머지(한글)는 Noto 로 폴백 */
/* !important 는 DesignKit 의 글꼴 선언을 덮어쓰기 위해 붙인다 */
html,
body {
  font-family:
    var(--font-helvetica-neue), var(--font-noto-sans), sans-serif !important;
}
```

Tailwind `font-sans` 유틸리티도 같은 글꼴을 쓰도록 `@theme inline` 의 `--font-sans` 를 함께 바꾼다:

```css
@theme inline {
  --font-sans: var(--font-helvetica-neue), var(--font-noto-sans), sans-serif;
}
```

## 핵심 원칙

1. **글꼴 선언은 `layout.tsx` 한 곳** — 페이지·컴포넌트에서 `next/font` 를 다시 호출하지 않는다.
2. **`variable` 방식으로 넘기고 CSS 에서 조합** — `className={font.className}` 을 `<html>` 에 직접 쓰지 않는다 (영문·한글 순서를 CSS 한 곳에서 관리).
3. **순서는 영문 → 한글 → `sans-serif`** — 한글을 먼저 두면 영문까지 Noto 로 렌더된다.
4. **weight 는 300·400·500·600·700 만** — 두 글꼴의 weight 집합을 맞춘다. 다른 굵기가 필요하면 이 문서를 먼저 수정한다.
5. 컴포넌트에서 `font-family` 를 개별 지정하지 않는다 (Tailwind `font-*` 임의값 포함).

## 적용 확인 방법

1. `make dev` 후 화면을 연다.
2. 개발자도구 → Elements → `<html>` 의 class 에 `__variable_...` 두 개가 붙었는지 확인.
3. 영문·한글이 섞인 텍스트 선택 → Computed 탭 하단 **Rendered Fonts** 에 `Helvetica Neue`(영문)·`Noto Sans KR`(한글)이 함께 표시되면 정상.
4. 덮어쓰기 검증: 크롬 설정에서 기본 글꼴을 임의로 바꿔도 화면 글꼴이 바뀌지 않아야 한다 — 참고: [크롬 브라우저에서 임의로 글꼴 변경하는 방법](https://blog.naver.com/myrikason/221973208064)

---

## 체크리스트

- [ ] `next/font/google` + `next/font/local` 로만 로드? (`<link>`·직접 `@font-face` 없음)
- [ ] `<html>` 에 두 글꼴의 `.variable` 이 모두 전달?
- [ ] `globals.css` 의 `font-family` 순서가 영문 → 한글 → `sans-serif`?
- [ ] `@theme inline` 의 `--font-sans` 도 같은 조합?
- [ ] 로컬 폰트 경로가 실제 파일과 일치? (`pnpm build` 성공)
- [ ] Rendered Fonts 로 영문·한글 글꼴 확인?

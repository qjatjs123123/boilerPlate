# 프론트엔드 컨벤션

> **이 문서는 사내 FE 컨벤션 원문(참고용)이다.** 이 프로젝트의 실행 기준은 `.claude/rules/frontend/` 이며, 아래처럼 다른 부분은 **rules 가 우선**한다.
>
> | 항목 | 이 문서(원문) | 이 프로젝트 (rules / 실제) | 이유 |
> |---|---|---|---|
> | 라우팅 | `src/pages/` + React Router | Next.js App Router `src/app/` (`src/pages/` 만들지 않음) | Pages Router 와 충돌 (`architecture.md`) |
> | Next / ESLint | Next v15, ESLint v8 | `frontend/package.json` 기준 (Next 16, ESLint 9 flat config) | 템플릿 최신 버전 |
> | 타입 파일명 | `buttonType.d.ts` | `{name}Type.ts` (`.d.ts` 금지) | `.d.ts` 는 `skipLibCheck` 로 오류가 검사되지 않음 (`naming-convention.md`) |
> | 컴포넌트 타입 분리 | 분리 권장 | 같은 파일 상단이 기본, 여러 파일이 공유하면 분리 | 응집도 (`naming-convention.md`) |
> | enum 값 | UPPER_SNAKE_CASE | enum 이름 UPPER, 멤버 PascalCase | `naming-convention.md` 「변수」 |
> | 공용 UI | `components/ui` 직접 작성 | shadcn/ui CLI 생성 코드 | `react-convention.md` |
> | 커밋·PR | `[Fix]` 태그 PR 제목 | `docs/CONVENTIONS.md` 「커밋」 (소문자 type, 훅이 검사) | 커밋 훅 강제 |

**Global Version: node.js (18.20.8, 20 lts)**

- ARR 유의사항
    - 해당글을 볼 수 있는 링크
    - appKit 공식 링크 (아이콘)
    - appKit 공식 일러스트레이터

# 0️⃣ Node 버전 관리

사내 보안 때문에 nvm을 사용할 수 없어요. 대신 volta를 사용해서 버전 관리하시면 됩니다.
Volta ( node version manager )

# 1️⃣ Project

프론트 엔드 컨벤션 규칙을 작성해두었습니다. 하기 내용을 확인하시고 프로젝트에 반영해주세요. (프로젝트별로 특수성에 의해 규칙이 완벽히 이행되지 않더라도, 앞으로 나아가는 방향성은 같았으면 해요 🙂)

## 🧩 Package

현재 프로젝트에서 사용하는 주요 패키지 및 라이브러리는 다음과 같습니다:

### ✅ pnpm 통일

기존의 npm 방식으로 운영되고 있는 프로젝트들의 경우 점진적으로 개선할 계획입니다. 새로 시작하는 프로젝트는 `pnpm` 사용해주세요.

### ✅ React v19

### ✅ Next v15

### Page Router vs App Router

- Page Router (기존 프로젝트 유지)
- App Router (새로운 프로젝트에 반영)

### ✅ Tanstack Query

데이터 페칭 및 캐싱을 위한 React 기반 라이브러리입니다.

### ✅ Axios

### ✅ Zustand

전역 상태 관리를 위한 경량 상태 관리 라이브러리입니다.

### ✅ DesignKit

내부 디자인시스템으로 필요시, submodule 형식으로 불러와서 사용합니다. 폰트, 컬러, 아이콘 등을 다양한 컴포넌트를 사용할 수 있습니다.

### ✅ Tailwind

최신 **v4.0** 버전을 사용합니다.

### ✅ Lucid Icon

### ✅ prettier

### ✅ eslint

eslint v9부터 flat config가 도입되면서 기존 프로젝트와의 혼선이 있었어요. 아직은 v8을 사용해야 할 것 같습니다.

- ✅ 예시

    ```json
    "dependencies": {
        "@tanstack/react-query": "^5.64.1",
        "class-variance-authority": "^0.7.1",
        "classnames": "^2.5.1",
        "clsx": "^2.1.1",
        "dotenv": "^16.4.7",
        "eslint-import-resolver-typescript": "^3.7.0",
        "lucide-react": "^0.474.0",
        "next": "15.2.3",
        "react": "^19.0.0",
        "react-dom": "^19.0.0",
        "react-dropzone": "^14.3.8",
        "react-spinners": "^0.15.0",
        "tailwind-merge": "^3.2.0",
        "zustand": "^5.0.3"
    },
    "devDependencies": {
        "@eslint/eslintrc": "^3",
        "@swc/core": "^1.11.24",
        "@tailwindcss/cli": "^4.0.0-alpha.30",
        "@tailwindcss/postcss": "^4.1.8",
        "@tanstack/react-query-devtools": "^5.64.1",
        "@types/node": "^20",
        "@types/react": "^19",
        "@types/react-dom": "^19",
        "@typescript-eslint/parser": "^8.21.0",
        "autoprefixer": "^10.4.20",
        "eslint": "^8",
        "eslint-config-next": "14.2.8",
        "eslint-config-prettier": "^9.1.0",
        "eslint-plugin-import": "^2.31.0",
        "eslint-plugin-prettier": "^5.2.1",
        "husky": "^9.1.7",
        "lint-staged": "^15.4.1",
        "postcss": "^8.5.1",
        "postcss-preset-env": "^10.1.3",
        "postcss-simple-vars": "^7.0.1",
        "tailwindcss": "^4.0.3",
        "typescript": "^5"
    },
    ```

---

## 📁 폴더 구조

참고 문서 : 폴더 구조 (아래 [폴더 구조 상세](#-폴더-구조-상세) 참고)

### src 폴더 사용 여부

- 사용

### 기준단위

- 기능

### 공용 component, hooks, utils 등의 내부 폴더 구조

- 많아지는 것만 폴더로 새로 묶고 아닌 건 넣기

### export

- index.ts 사용 여부 (베럴 X)
    - 베럴 방식 사용시 트리 쉐이킹이 되지 않아 비정상적으로 번들 사이즈가 커지는 이슈가 있었어요.

---

## 🔤 Naming

### Folder Naming Convention

- 기본적으로 `kebab-case` 입니다.
- 컴포넌트 파일만 예외적으로 `PascalCase`로 사용합니다.

### Component

- naming case : **PascalCase**
- `function` vs `const`
    - 용도에 맞게 사용하시면 됩니다. 단, const + arrow function 방식 사용시 displayName 신경 써주세요.
- props 구조분해할당 : 선호에 맞게 쓰세요.
    - case 1 : `{prop1, prop2} : IProps`
    - case 2 : `props : IProps`

### type

- naming case : `IComponentProps`, `TComponentProps`
- 파일명: buttonType.d.ts
- 컴포넌트의 type 분리 여부: 권장
- `IApprovalGetResponse`, `IApprovalCreateRequest`, ... 변환이 되는 순간 삭제

### 상수

- naming case : **UPPER_SNAKE_CASE**
- 파일명: constants

### 기타 naming case variant

| 이름 | 예시 | 설명 / 사용 예시 |
| --- | --- | --- |
| **camelCase** | `myVariableName` | JS, TS에서 변수명, 함수명 등 일반적으로 사용 |
| **PascalCase** | `MyComponentName` | 클래스명, React 컴포넌트명 등 |
| **snake_case** | `my_variable_name` | Python 변수명, 일부 설정 파일 등 |
| **UPPER_SNAKE_CASE** | `MAX_COUNT`, `API_KEY` | 상수, enum 값 등 |
| **kebab-case** | `my-variable-name` | URL, 파일 이름, CSS className 등 |
| **dot.case** | `my.variable.name` | 설정 파일 키(JSON, config 등) |
| **SCREAMING-KEBAB-CASE** | `MY-VARIABLE-NAME` | 잘 사용되진 않지만, 강조된 케밥 케이스 |
| **Train-Case** | `My-Component-Name` | kebab + Pascal 느낌. 문서화 또는 제목 등에 가끔 사용 |

### 번외1) 한글 변수 가능?

- 허용 기준 : 상수, 함수 등 영어가 품지 못하는 것들에 한해서 써주세요

### 번외2) 주석 어디까지 적어?

- 나중에 공통적으로 사용하게 될 것 같은 코드에는 필수로 적어주세요. (훅, util…등)

```jsx
// TODO: api 연동 이후 mockdata 삭제
// [테이블] ~을 위한 함수
```

---

### 추후 - 접근성(A11y)

### 마크업

- div : `aria-[name]`, `role=""`
- `시멘틱 마크업`
- 가이드라인

### eslint-plugin-jsx-a11y 도입?

- 보류

### 접근성 테스트 도구

- axe
- Lighthouse
- 그 외

---

## 🌐 API

### API URL

1. env
    1. `.env.local`, `.env.production`
    2. 되도록이면 `.env` 통일

### HTTP Client

- 되도록이면 `Axios` 사용

---

## 🛠 Code Formatter & Linter

## ESLint / Prettier / Husky / lint-staged

- 규칙 정리 및 충돌 방지 설정 (`eslint-config-prettier`)
- devkit
- Husky / lint-staged 는 추후 도입 예정

예시)

- [Project] eslint

    ```json
    {
      "extends": [
        "eslint:recommended",
        "plugin:tailwindcss/recommended",
        "plugin:react/recommended",
        "plugin:react-hooks/recommended",
        "plugin:react/jsx-runtime",
        "plugin:@typescript-eslint/recommended",
        "plugin:@tanstack/query/recommended"
      ],
      "settings": {
        "react": {
          "version": "detect"
        }
      },
      "overrides": [
        {
          "files": ["postcss.config.js"],
          "rules": {
            "no-undef": "off",
            "no-unused-vars": "off"
          }
        }
      ],
      "plugins": ["react", "react-hooks"],
      "rules": {
        "@typescript-eslint/no-unused-expressions": "off",
        "tailwindcss/no-custom-classname": "off",
        "@typescript-eslint/no-explicit-any": "off"
      }
    }
    ```

- [lease] eslint

    ```json
    {
      "env": {
        "browser": true,
        "es2021": true,
        "node": true
      },
      "extends": [
        "eslint:recommended",
        "plugin:react/recommended",
        "plugin:@typescript-eslint/recommended",
        "prettier",
        "plugin:prettier/recommended",
        "plugin:import/recommended",
        "plugin:react/jsx-runtime"
      ],
      "overrides": [],
      "parser": "@typescript-eslint/parser",
      "parserOptions": {
        "ecmaFeatures": {
          "jsx": true
        },
        "ecmaVersion": 12,
        "sourceType": "module"
      },
      "plugins": ["react", "@typescript-eslint", "react-hooks"],
      "rules": {
        "react/react-in-jsx-scope": "off",
        "react/jsx-uses-react": "off",
        "react/jsx-uses-vars": "error",
        "no-use-before-define": "off",
        "react/jsx-filename-extension": ["warn", { "extensions": [".tsx"] }],
        "import/extensions": ["error", "ignorePackages", { "ts": "never", "tsx": "never" }],
        "no-shadow": "off",
        "@typescript-eslint/explicit-function-return-type": ["error", { "allowExpressions": true }],
        "react-hooks/rules-of-hooks": "error",
        "react-hooks/exhaustive-deps": "warn",
        "import/prefer-default-export": "off",
        "react/prop-types": "off",
        "prettier/prettier": ["error", { "endOfLine": "auto" }]
      },
      "settings": {
        "import/resolver": {
          "typescript": {}
        },
        "react": {
          "version": "detect"
        }
      }
    }
    ```

---

## ⚙️ Config

### tailwindcss

- devKit config 참고

### tsconfig

- devKit config 참고

---

# 디자인시스템

### 도입 방안

1. **github sub module**

## storybook

1. 컴포넌트 문서화 방식 (MDX, Docs addon)
2. 개발 환경 공유 전략
3. 자동 배포 (GitHub Pages, Chromatic 등)
4. 버전관리

---

# Github

## Merge

- rebase
- merge: PR로 인한 코드 결합시 사용
- conflict 해결 방식

## PR template

```markdown
# 📌 제목 (PR 제목)

- `[태그] 간결한 설명` (예: `[Fix] 채팅방 인원수 에러 해결 Bugfix`)

## ✨ 변경 사항 (Changes)

- 주요 변경 사항을 리스트로 작성합니다.
- 코드 수정, 기능 추가, 버그 수정 등 내용을 간략히 설명합니다.

## 🚀 구현 내용 (Implementation Details)

- 변경 이유와 구현 방식을 설명합니다.
- 코드 개선, 리팩토링 여부도 함께 작성합니다.

## 🛠 추가 고려 사항 (Additional Context)

- 리뷰어가 알아야 할 추가적인 정보가 있다면 기재합니다.
- 관련된 문서나 레퍼런스를 링크할 수도 있습니다.

## ✅ 체크리스트 (Checklist)

- [ ] 코드가 정상적으로 동작하는지 확인했나요?

### 📢 리뷰어에게 (For Reviewers)

---

- 리뷰 시 집중해서 봐야 할 포인트가 있다면 작성해주세요.
- `@리뷰어아이디` 멘션하여 특정 리뷰어를 지정할 수도 있습니다.
```

## Commit

- 커밋 컨벤션 (Conventional Commits 등)
    - 짧은 커밋 권장
- 참고 문서 : 기본 커밋 메세지 컨벤션

## Branch

### GitHub Flow

- **✅ 특징**
    - **`dev` 브랜치를 기준**으로 작업 브랜치를 만들고 PR로 merge
    - GitHub의 PR 중심 개발 흐름에 적합
- 📌 **브랜치 전략**
    - `main`: 항상 배포 가능한 상태
    - `dev`: 개발 기준 — 작업 브랜치는 dev 에서 만들고 dev 로 merge (`dev → main` 은 배포 시점에)
    - `feature/` 또는 `issue-123/`: 이슈 단위로 브랜치 생성
    - `hotfix/` : 긴급 수정
    - PR → Review → Merge
- **🧠 장점**
    - 깔끔하고 간단한 구조
    - GitHub 기반 협업에 최적화
- ⚠️ **단점**
    - 여러 릴리즈 버전을 병렬 관리하기엔 불리
    - 복잡한 릴리즈 프로세스에는 부적합

---

# 📂 폴더 구조 상세

```
├── 📁 public                     # 정적 파일 (favicon, 이미지 등)
│   └── 📁 images
│       └── 📁 <도메인명>          # 도메인별 이미지 정리
│           └── <이미지명>.jpg
├── 📁 src
│   ├── 📁 features               # 도메인 단위 기능 모듈
│   │   └── 📁 <도메인명>
│   │       ├── 📁 pages
│   │       │   └── <컴포넌트명>.tsx
│   │       ├── 📁 components
│   │       │   └── 📁 <컴포넌트명>   # ( 도메인 전용 ) 컴포넌트
│   │       │       ├── 📁 hooks       # ( 컴포넌트 전용 ) 커스텀 훅
│   │       │       │   //...
│   │       │       └── index.tsx      # 컴포넌트 코드
│   │       ├── 📁 models         # ( 도메인 전용 ) ACL 계층 ( adapter layer )
│   │       ├── 📁 hooks          # ( 도메인 전용 ) 커스텀 훅
│   │       ├── 📁 services       # ( 도메인 전용 ) API 호출 및 비즈니스 로직
│   │       ├── 📁 store          # ( 도메인 전용 ) 전역 상태 관리
│   │       ├── 📁 queries        # ( 도메인 전용 ) React Query 관련 queryFn, queryKey
│   │       ├── 📁 utils          # ( 도메인 전용 ) 유틸리티 함수
│   │       ├── 📁 lib            # ( 도메인 전용 ) 외부 라이브러리 래퍼나 설정
│   │       ├── 📁 constants      # ( 도메인 전용 ) 상수
│   │       └── 📁 types          # ( 도메인 전용 ) 타입
│   ├── 📁 components
│   │   ├── 📁 DesignKit        # ( 공용 ) designkit
│   │   ├── 📁 ui                 # ( 공용 ) 프레젠테이션 컴포넌트
│   │   │   └── index.tsx
│   │   ├── 📁 layout             # ( 공용 ) 페이지 레이아웃, 에러 바운더리 등
│   │   └── 📁 shared             # ( 공용 ) 도메인을 넘나들며 쓰이는 컴포넌트
│   │       └── 📁 <컴포넌트명>
│   │           ├── 📁 hooks      # ( 컴포넌트 전용 ) 커스텀 훅
│   │           │   //...
│   │           └── index.tsx     # 컴포넌트 코드
│   ├── 📁 models                 # ( 공용 ) Adapter 계층 (원격 데이터 → UI-friendly 구조)
│   ├── 📁 hooks                  # ( 공용 ) 훅
│   ├── 📁 services               # ( 공용 ) 비즈니스 로직을 처리하거나 API 호출을 담당하는 계층
│   ├── 📁 store                  # ( 공용 ) 전역 상태 관리
│   ├── 📁 queries                # ( 공용 ) React Query 관련 (queryKey, queryFn 등)
│   ├── 📁 utils                  # ( 공용 ) 간단한 헬퍼 함수나 유틸리티 함수들을 모아두는 공간
│   ├── 📁 lib                    # ( 공용 ) 외부 라이브러리 래퍼나 설정
│   ├── 📁 constants              # ( 공용 ) 상수
│   ├── 📁 types                  # ( 공용 ) 타입 정의
│   ├── 📁 pages                  # ( 공용 ) 페이지 컴포넌트를 경로에 맞게 단순 import, export 하는 폴더
│   │   ├── index.tsx
│   │   └── 📁 <경로명>
│   │       ├── index.tsx
│   │       └── 📁 <하위경로>
│   │           └── index.tsx
│   ├── App.tsx                   # 앱 루트
│   ├── index.tsx                 # 진입점
│   └── route.tsx                 # React Router 설정
├── index.html                    # Vite 템플릿 HTML
├── package.json                  # 의존성 및 스크립트
├── tsconfig.json                 # TypeScript 설정
├── vite.config.mts               # Vite 설정
├── .eslintrc.cjs                 # ESLint 설정
├── .prettierrc                   # Prettier 설정
├── .gitignore                    # Git 무시 목록
└── README.md                     # 프로젝트 설명
```

## 🧱 개념

### 3️⃣ 3계층 구조 (Three-Layer Architecture)

이 프로젝트는 프론트엔드 구조를 다음과 같은 **3계층**으로 나누어 설계합니다. 각 계층은 **역할과 책임이 명확히 분리**되어 있어 유지보수성과 확장성이 뛰어납니다.

#### 1. 페이지 계층 (Page Layer)

- **역할**: 라우팅 경로에 대응되는 진입점 컴포넌트로, 도메인 계층에서 pages 컴포넌트를 가져오고 내보냅니다.
- **위치**: `src/pages/`
- **특징**:
    - 라우팅 설정과 URL 매핑을 담당
    - 실제 UI는 `features/<도메인>/pages`에서 구현하고, 이 계층에서는 import 및 조합만 담당
    - SSR/CSR 여부와 무관하게 **라우팅 중심의 역할**을 수행

#### 2. 도메인 계층 (Feature Layer)

- **역할**: 특정 기능(도메인)에 대한 모든 리소스를 포함하며, 기능 단위로 독립적인 모듈을 구성합니다.
- **위치**: `src/features/<도메인명>/`
- **포함 요소**:
    - `pages/`: 도메인 전용 페이지 컴포넌트
    - `components/`: 도메인 전용 컴포넌트
    - `services/`: API 호출 및 비즈니스 로직
    - `models/`: 데이터 가공 및 Adapter 계층
    - `queries/`, `store/`, `hooks/`, `utils/`, `types/` 등

> 도메인 단위로 캡슐화되어 있어, 기능 추가/삭제 시 다른 도메인에 영향을 주지 않으며, 테스트 및 유지보수가 용이합니다.

#### 3. 공용 계층 (Shared Layer)

- **역할**: 여러 도메인에서 재사용 가능한 리소스를 관리합니다.
- **위치**: `src/components/`, `src/hooks/`, `src/utils/`, `src/services/`, `src/types/` 등
- **포함 요소**:
    - `components/ui`: 버튼, 모달 등 순수 UI 요소
    - `components/shared`: 도메인 간 로직이 포함된 재사용 컴포넌트
    - `hooks/`: 공용 커스텀 훅
    - `services/`: 공용 API 호출 로직
    - `utils/`, `constants/`, `types/`: 공용 유틸, 상수, 타입 정의

#### ✅ 요약

| **계층** | **위치** | **책임** |
| --- | --- | --- |
| **Page Layer** | `src/pages/` | 단순 라우팅을 담당하는 계층 |
| **Feature Layer** | `src/features/<도메인>/` | 기능별 UI, 상태, API, 모델 등 |
| **Shared Layer** | `src/components/`, `src/hooks/` 등 | 공용 UI, 훅, 유틸 등 재사용 리소스 |

> 이 구조는 기능의 소유권은 도메인에, 조합의 책임은 상위 계층에 두는 것을 원칙으로 합니다.

### 🧼 삭제가 쉬운 아키텍처

- 각 도메인은 독립적으로 구성되어 있어, 특정 도메인을 제거해도 다른 도메인에 영향을 주지 않습니다.
- 공용 리소스와 도메인 전용 리소스를 명확히 분리하여, 기능 단위로 추가/삭제/교체가 용이합니다.
- 도메인 내부에 테스트, mock, 페이지까지 포함하면 전체 기능을 하나의 폴더로 관리할 수 있어 유지보수가 쉬워집니다.

### 🔗 도메인 간 의존성 관리 원칙

- 도메인 간 직접 참조는 피하고, 공용 계층 또는 상위 도메인에서만 조합합니다.
- 예: `support` 도메인이 `qna`, `faq`의 query function을 가져와 조합하는 것은 OK. 반대로 `qna`가 `support`를 참조하는 것은 ❌
- 도메인 간 의존 방향은 항상 **한 방향**으로 유지해야 순환 참조를 방지할 수 있습니다.

## ❓ Q&A

### Q1. 왜 도메인 단위로 나누나요?

- 기능별로 관심사를 분리하면 유지보수, 테스트, 협업이 쉬워집니다.
- 새로운 도메인을 추가하거나 제거할 때 다른 도메인에 영향을 주지 않습니다.

### Q2. 공용과 도메인 전용 훅은 어떻게 구분하나요?

- **공용 훅**: 여러 도메인에서 재사용 가능한 로직 (`src/hooks`)
- **도메인 훅**: 특정 도메인에만 필요한 로직 (`features/<도메인명>/hooks`)

### Q3. `components/ui`와 `components/shared`의 차이는?

- `ui`: 버튼, 모달 등 순수 UI 요소
- `shared`: 도메인 간 로직이 포함된 재사용 컴포넌트

### Q4. `models`와 `services`는 어떻게 다르나요?

- `models`: 데이터 구조 변환 (Adapter 역할)
- `services`: API 호출 및 비즈니스 로직 처리

### Q5. 여러 도메인의 데이터를 한 페이지에서 조합하려면 어떻게 해야 하나요?

- 단순히 데이터를 조회하고 조합해서 보여주는 목적이라면, `src/hooks/useQnaAndFaq.ts` 같은 공용 훅을 만들어서 처리하는 것이 적절합니다.
- 하지만 이 조합이 단순한 조회를 넘어서 **새로운 비즈니스 개념**으로 발전한다면, 예: "고객지원(Support)"이라는 도메인에서 QnA와 FAQ를 통합 관리한다면 → `features/support/` 같은 새로운 도메인을 만들어서 query function을 조합하는 것이 좋습니다.

> 핵심은 **조합의 책임은 상위 계층에서, 기능의 소유권은 각 도메인에 유지**하는 것입니다.

### Q6. 도메인 간 의존성은 어떻게 관리하나요?

- 각 도메인은 독립적으로 유지되어야 하며, 다른 도메인의 내부 로직에 직접 의존하지 않아야 합니다.
- 여러 도메인의 데이터를 조합해야 할 경우, 공용 훅 또는 상위 도메인에서 조합합니다.
- 예: `support` 도메인이 `qna`, `faq`의 query function을 가져와 조합하는 것은 OK. 반대로 `qna`가 `support`를 참조하는 것은 ❌

### Q7. `getServerSideProps`는 어디에 위치시켜야 하나요?

- `getServerSideProps`는 **Next.js의 SSR 기능**으로, 반드시 `pages/` 디렉토리 내부의 파일에 있어야 합니다.
- 데이터 로직은 도메인 서비스 계층(`features/<도메인>/services`)에 정의하고, SSR 함수에서 호출합니다.
- SSR 데이터를 도메인 컴포넌트에 props로 전달하여 렌더링을 위임합니다.
    - SSR은 페이지의 책임
    - 데이터 로직은 도메인의 책임
    - UI 렌더링은 도메인 컴포넌트의 책임

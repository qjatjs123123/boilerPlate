import fs from "node:fs";

import { defineConfig, globalIgnores } from "eslint/config";
import nextVitals from "eslint-config-next/core-web-vitals";
import nextTs from "eslint-config-next/typescript";

const RULES = ".claude/rules/frontend";

/**
 * 도메인 내부 의존 방향 (사내 FE 아키텍처 — 아래 계층은 위 계층을 import 할 수 없다)
 *   types·constants·utils·lib → models → services → queries → store → hooks → components → pages
 */
const FEATURE_LAYERS = [
  ["types", "constants", "utils", "lib"],
  ["models"],
  ["services"],
  ["queries"],
  ["store"],
  ["hooks"],
  ["components"],
  ["pages"],
];
const LAYER_DOC = {
  types: "types-layer.md",
  constants: "types-layer.md",
  utils: "architecture.md",
  lib: "architecture.md",
  models: "models-layer.md",
  services: "services-layer.md",
  queries: "queries-layer.md",
  store: "store-layer.md",
  hooks: "hooks-layer.md",
  components: "react-convention.md",
  pages: "architecture.md",
};

const layerZones = FEATURE_LAYERS.flatMap((group, rank) => {
  const upper = FEATURE_LAYERS.slice(rank + 1).flat();
  return group.flatMap((layer) =>
    upper.map((forbidden) => ({
      target: `./src/features/*/${layer}/**`,
      from: `./src/features/*/${forbidden}/**`,
      message: `${layer} 계층은 ${forbidden} 계층을 import 할 수 없다 (의존 방향: types → models → services → queries → store → hooks → components → pages). 수정 방법: ${RULES}/${LAYER_DOC[layer]} 참고`,
    })),
  );
});

/**
 * 도메인 간 의존 — 상위 도메인만 하위 도메인을 조합할 수 있다 (한 방향).
 * 예: support 가 qna·faq 의 queries 를 조합하면 { support: ["qna", "faq"] } 로 등록. 역방향(qna → support)은 등록하지 않는다.
 */
const FEATURE_DEPENDENCIES = {};

const featureNameList = fs.existsSync("./src/features")
  ? fs.readdirSync("./src/features", { withFileTypes: true }).filter((d) => d.isDirectory()).map((d) => d.name)
  : [];

const featureZones = featureNameList.map((name) => ({
  target: `./src/features/${name}/**`,
  from: "./src/features",
  except: [`./${name}`, ...(FEATURE_DEPENDENCIES[name] ?? []).map((dep) => `./${dep}/queries`)],
  message: `다른 도메인(features/*)을 직접 import 할 수 없다. 단순 조회 조합은 공용 src/hooks/(도메인 queries 만 import)에서, 새 비즈니스 개념이면 상위 도메인을 만들어 eslint.config.mjs 의 FEATURE_DEPENDENCIES 에 한 방향으로 등록한다 (하위 도메인의 queries/ 만 import 가능). 수정 방법: ${RULES}/architecture.md 참고`,
}));

/** store 는 순수 클라이언트 상태 — 의존 방향상 아래인 models·services·queries 도 금지 (store-layer.md) */
const storeZones = ["models", "services", "queries"].map((forbidden) => ({
  target: "./src/features/*/store/**",
  from: `./src/features/*/${forbidden}/**`,
  message: `store 는 서버 데이터·API 를 모르는 클라이언트 상태다 — ${forbidden} 계층을 import 할 수 없다 (types·constants·utils·lib 만). 수정 방법: ${RULES}/store-layer.md 참고`,
}));

const SHARED_DIRS = ["components", "models", "hooks", "services", "store", "queries", "utils", "lib", "constants", "types"];

/** 공용 계층 내부 의존 방향 — 도메인과 같은 순서 (pages 없음, components 가 최상단) */
const SHARED_LAYERS = [
  ["types", "constants", "utils", "lib"],
  ["models"],
  ["services"],
  ["queries"],
  ["store"],
  ["hooks"],
  ["components"],
];

const sharedLayerZones = SHARED_LAYERS.flatMap((group, rank) => {
  const upper = SHARED_LAYERS.slice(rank + 1).flat();
  return group.flatMap((layer) =>
    upper.map((forbidden) => ({
      target: `./src/${layer}/**`,
      from: `./src/${forbidden}/**`,
      message: `공용 ${layer} 는 공용 ${forbidden} 를 import 할 수 없다 (공용 계층도 types → models → services → queries → store → hooks → components 방향). 수정 방법: ${RULES}/architecture.md 참고`,
    })),
  );
});

const LAYER_ZONES = [
  ...layerZones,
  ...storeZones,
  ...featureZones,
  ...sharedLayerZones,
  {
    target: SHARED_DIRS.filter((dir) => dir !== "hooks").map((dir) => `./src/${dir}/**`),
    from: "./src/features/**",
    message: `공용 계층(components·hooks·utils 등)은 특정 도메인(features/)을 import 할 수 없다 — 공용 UI 는 props 로만 데이터를 받는다. 수정 방법: ${RULES}/architecture.md 참고`,
  },
  {
    // 예외: 공용 hooks 는 여러 도메인의 단순 조회 조합(예: useQnaAndFaq)을 위해 각 도메인 queries/ 만 import 가능
    target: "./src/hooks/**",
    from: "./src/features",
    except: featureNameList.map((name) => `./${name}/queries`),
    message: `공용 hooks 는 도메인의 queries/(queryOptions)만 import 할 수 있다 — 단순 조회 조합 전용. 그 외 도메인 파일은 import 금지. 수정 방법: ${RULES}/architecture.md 참고`,
  },
  {
    target: "./src/app/**",
    from: ["./src/features/*/!(pages)/**"],
    message: `페이지 계층(app/)은 features/<도메인>/pages 만 가져와 내보낸다. 화면 구현은 도메인 pages/ 에서. 수정 방법: ${RULES}/architecture.md 참고`,
  },
  {
    target: ["./src/features/*/!(services)/**", "./src/!(services|lib|features)/**"],
    from: "./src/lib/axios.ts",
    message: `HTTP 호출(lib/axios)은 services/ 계층에서만 한다. 화면·훅은 queries/hooks 를 사용. 수정 방법: ${RULES}/axios.md 참고`,
  },
];

const eslintConfig = defineConfig([
  ...nextVitals,
  ...nextTs,
  {
    rules: {
      "import/no-restricted-paths": ["error", { zones: LAYER_ZONES }],
      "no-restricted-imports": [
        "error",
        {
          paths: [
            {
              name: "axios",
              message: `axios 패키지 import 는 lib/axios.ts 와 services 계층(isAxiosError 타입 가드)에서만 허용. HTTP 호출은 '@/lib/axios' 의 axiosInstance 를 services 에서 사용. 수정 방법: ${RULES}/axios.md 참고`,
            },
          ],
        },
      ],
    },
  },
  {
    // axios 단일 진입점 + services 의 axios.isAxiosError 타입 가드 (axios.md 규칙 3)
    files: ["src/lib/axios.ts", "src/features/*/services/**", "src/services/**"],
    rules: { "no-restricted-imports": "off" },
  },
  {
    files: ["**/__tests__/**", "e2e/**", "tests/**"],
    rules: { "import/no-restricted-paths": "off", "no-restricted-imports": "off" },
  },
  // Override default ignores of eslint-config-next.
  globalIgnores([
    // Default ignores of eslint-config-next:
    ".next/**",
    "out/**",
    "build/**",
    "next-env.d.ts",
    "test-results/**",
    "playwright-report/**",
  ]),
]);

export default eslintConfig;

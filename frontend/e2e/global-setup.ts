// e2e 시작 전 준비 — 모든 화면을 한 번씩 열어 개발 서버가 미리 만들어 두게 한다.
// 개발 서버는 화면을 처음 열 때 그 자리에서 만든다(수 초). 캐시가 빈 상태에서 여러 테스트가 동시에
// 서로 다른 화면을 처음 열면 만들기가 몰려 toHaveURL 등의 기본 대기 시간(5초)을 넘겨 흔들린다.
// 화면 목록은 src/app/**/page.tsx 에서 읽는다 — 화면이 늘어도 이 파일은 고치지 않는다.
import { readdirSync, statSync } from 'node:fs';
import path from 'node:path';

import type { FullConfig } from '@playwright/test';

const APP_DIR = path.resolve(__dirname, '../src/app');
const DYNAMIC_SEGMENT_SAMPLE = '1'; // [postId] 같은 자리 — 없는 id 여도 화면 코드는 만들어진다
const WARM_UP_TIMEOUT_MS = 120_000;

/** src/app 아래 page.tsx 위치 → 화면 주소 목록 (route group `(x)` 는 주소에서 뺀다) */
function collectRoutePathList(dir: string, segmentList: string[] = []): string[] {
  const routePathList: string[] = [];
  for (const name of readdirSync(dir)) {
    const fullPath = path.join(dir, name);
    if (statSync(fullPath).isDirectory()) {
      const isRouteGroup = name.startsWith('(') && name.endsWith(')');
      const segment = name.startsWith('[') ? DYNAMIC_SEGMENT_SAMPLE : name;
      routePathList.push(...collectRoutePathList(fullPath, isRouteGroup ? segmentList : [...segmentList, segment]));
    } else if (name === 'page.tsx') {
      routePathList.push(`/${segmentList.join('/')}`);
    }
  }
  return routePathList;
}

export default async function globalSetup(config: FullConfig): Promise<void> {
  const baseUrl = config.projects[0]?.use.baseURL ?? process.env.E2E_BASE_URL;
  if (!baseUrl) return;
  for (const routePath of collectRoutePathList(APP_DIR)) {
    // 응답 코드는 보지 않는다 (없는 id 는 404) — 목적은 화면 코드를 미리 만들어 두는 것
    await fetch(`${baseUrl}${routePath}`, { signal: AbortSignal.timeout(WARM_UP_TIMEOUT_MS) }).catch(() => undefined);
  }
}

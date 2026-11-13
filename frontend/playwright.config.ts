import { defineConfig, devices } from '@playwright/test';

// 포트를 바꿔야 하면 E2E_PORT 지정 (기본 3000)
const PORT = process.env.E2E_PORT ?? '3000';
const BASE_URL = `http://localhost:${PORT}`;
process.env.E2E_BASE_URL = BASE_URL;

export default defineConfig({
  testDir: './e2e',
  // 서버가 뜬 뒤 모든 화면을 한 번씩 열어 미리 만들어 둔다 (차가운 개발 서버 + 동시 실행 흔들림 방지)
  globalSetup: './e2e/global-setup.ts',
  fullyParallel: true,
  reporter: 'list',
  use: {
    baseURL: BASE_URL,
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  // 프론트 + 백엔드(API 를 쓰는 화면용). 이미 켜져 있으면 재사용한다.
  webServer: [
    {
      command: `pnpm dev --port ${PORT}`,
      url: BASE_URL,
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
    {
      command: '.venv/bin/uvicorn app.main:app --port 8000',
      cwd: '../backend',
      url: 'http://localhost:8000/api/health',
      reuseExistingServer: !process.env.CI,
      timeout: 120_000,
    },
  ],
});

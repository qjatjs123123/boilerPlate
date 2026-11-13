import path from 'node:path';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    globals: true, // Testing Library auto-cleanup이 전역 afterEach를 요구
    environment: 'node', // 컴포넌트·훅 테스트는 파일별 `// @vitest-environment jsdom` 주석으로 전환
    setupFiles: ['./vitest.setup.ts'], // jsdom 미지원 API 폴리필 (Radix 부품용)
    passWithNoTests: true, // 초기 상태(기능 없음)에서는 단위 테스트가 0개다
    include: [
      'src/features/**/__tests__/**/*.test.{ts,tsx}',
      'src/components/**/__tests__/**/*.test.{ts,tsx}',
      'src/lib/**/__tests__/**/*.test.{ts,tsx}',
      'src/utils/**/__tests__/**/*.test.{ts,tsx}',
      'src/{hooks,models,services,queries,store}/**/__tests__/**/*.test.{ts,tsx}',
    ],
  },
  resolve: {
    alias: { '@': path.resolve(import.meta.dirname, 'src') },
  },
});

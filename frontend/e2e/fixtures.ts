import { appendFileSync, mkdirSync } from 'node:fs';
import path from 'node:path';

import { test as base, expect } from '@playwright/test';

/**
 * 하네스 공용 fixture — 모든 e2e 테스트는 '@playwright/test' 대신 이 파일의 test 를 import 한다.
 * 브라우저 console error·pageerror 를 수집해
 *  1) HARNESS_RUN_DIR 가 있으면 {RUN_DIR}/console-errors.log 에 기록하고
 *  2) 에러가 하나라도 있으면 테스트를 실패시킨다.
 */
export const test = base.extend<{ consoleErrors: string[] }>({
  consoleErrors: [
    async ({ page }, use, testInfo) => {
      const errors: string[] = [];
      page.on('console', (msg) => {
        if (msg.type() === 'error') errors.push(`[console.error] ${msg.text()}`);
      });
      page.on('pageerror', (err) => errors.push(`[pageerror] ${err.message}`));

      await use(errors);

      const runDir = process.env.HARNESS_RUN_DIR;
      if (runDir) {
        const logPath = path.resolve(process.cwd(), '..', runDir, 'console-errors.log');
        mkdirSync(path.dirname(logPath), { recursive: true });
        const header = `# ${new Date().toISOString()} ${testInfo.titlePath.join(' > ')}\n`;
        appendFileSync(logPath, header + (errors.length ? errors.join('\n') : '(no errors)') + '\n');
      }
      expect(errors, '브라우저 콘솔/런타임 에러가 없어야 한다').toEqual([]);
    },
    { auto: true },
  ],
});

export { expect };

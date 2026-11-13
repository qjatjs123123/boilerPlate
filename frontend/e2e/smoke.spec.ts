import { expect, test } from './fixtures';

test('홈 페이지가 로드되고 콘솔 에러가 없다', async ({ page }) => {
  const consoleErrorList: string[] = [];
  page.on('console', (message) => {
    if (message.type() === 'error') consoleErrorList.push(message.text());
  });
  page.on('pageerror', (error) => consoleErrorList.push(error.message));

  await page.goto('/');

  await expect(
    page.getByRole('heading', { name: 'To get started, edit the page.tsx file.' }),
  ).toBeVisible();
  expect(consoleErrorList).toEqual([]);
});

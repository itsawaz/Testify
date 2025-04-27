// Playwright test script
const { test, expect } = require('@playwright/test');

test('hi', async ({ page }) => {
  // Set timeout for entire test
  test.setTimeout(30000);

  // Step 3: Navigate to URL
  await page.goto('https://www.merriam-webster.com/dictionary/hi');
  console.log('Navigated to https://www.merriam-webster.com/dictionary/hi');
  await page.waitForLoadState('networkidle');

  // Take screenshot at the end
  await page.screenshot({ path: 'final-state.png' });
});

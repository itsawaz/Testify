// Playwright test script
const { test, expect } = require('@playwright/test');

test('go google.com', async ({ page }) => {
  // Set timeout for entire test
  test.setTimeout(30000);

  // Step 2: Navigate to URL
  await page.goto('https://www.google.com');
  console.log('Navigated to https://www.google.com');
  await page.waitForLoadState('networkidle');

  // Take screenshot at the end
  await page.screenshot({ path: 'final-state.png' });
});

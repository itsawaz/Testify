// Playwright test script
const { test, expect } = require('@playwright/test');

test('go to google.com', async ({ page }) => {
  // Set timeout for entire test
  test.setTimeout(30000);

  // Step 1: Navigate to URL
  await page.goto('http://www.google.com');
  console.log('Navigated to http://www.google.com');
  await page.waitForLoadState('networkidle');

  // Final step: Task completion
  console.log('Task completed successfully');

  // Take screenshot at the end
  await page.screenshot({ path: 'final-state.png' });
});

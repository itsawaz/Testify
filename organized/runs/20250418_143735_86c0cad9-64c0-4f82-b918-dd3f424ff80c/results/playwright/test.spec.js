// Playwright test script
const { test, expect } = require('@playwright/test');

test('http://aioss.in/tms/default.aspx username: admin , password admin login page', async ({ page }) => {
  // Set timeout for entire test
  test.setTimeout(30000);

  // Step 1: Navigate to URL
  await page.goto('http://aioss.in/tms/default.aspx');
  console.log('Navigated to http://aioss.in/tms/default.aspx');
  await page.waitForLoadState('networkidle');

  // Take screenshot at the end
  await page.screenshot({ path: 'final-state.png' });
});

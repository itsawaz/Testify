// Playwright test script
const { test, expect } = require('@playwright/test');

test('go to https://chatgpt.com/ and login with my email id ucontactpawan.com', async ({ page }) => {
  // Set timeout for entire test
  test.setTimeout(30000);

  // Take screenshot at the end
  await page.screenshot({ path: 'final-state.png' });
});

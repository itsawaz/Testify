const { Builder, By, Key, until } = require('selenium-webdriver');
const chrome = require('selenium-webdriver/chrome');
const assert = require('assert');

describe('Generated Selenium Test', function() {
  this.timeout(30000);
  let driver;

  beforeEach(async function() {
    driver = await new Builder()
      .forBrowser('chrome')
      .setChromeOptions(new chrome.Options().headless())
      .build();
  });

  afterEach(async function() {
    if (driver) {
      await driver.quit();
    }
  });

  it('completes the task', async function() {
    try {
      // Task: go to google.com
      // Navigate to https://google.com
      await driver.get('https://google.com');
      // Task completed
      console.log('Task completed successfully');
    } catch (error) {
      // Take screenshot on failure
      if (driver) {
        const screenshotData = await driver.takeScreenshot();
        require('fs').writeFileSync('error-screenshot.png', screenshotData, 'base64');
      }
      throw error;
    }
  });
});

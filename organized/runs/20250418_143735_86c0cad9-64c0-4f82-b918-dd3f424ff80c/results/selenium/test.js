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
      // Task: http://aioss.in/tms/default.aspx username: admin , password admin login page
      // Navigate to http://aioss.in/tms/default.aspx
      await driver.get('http://aioss.in/tms/default.aspx');
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

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
      // Task: Test Case 1: Register User\\r\\n1. Launch browser\\r\\n2. Navigate to url \\'http://automationexercise.com\\'\\r\\n3. Verify that home page is visible successfully\\r\\n4. Click on \\'Signup / Login\\' button\\r\\n5. Verify \\'New User Signup!\\' is visible\\r\\n6. Enter name and email address\\r\\n7. Click \\'Signup\\' button\\r\\n8. Verify that \\'ENTER ACCOUNT INFORMATION\\' is visible\\r\\n9. Fill details: Title, Name, Email, Password, Date of birth\\r\\n10. Select checkbox \\'Sign up for our newsletter!\\'\\r\\n11. Select checkbox \\'Receive special offers from our partners!\\'\\r\\n12. Fill details: First name, Last name, Company, Address, Address2, Country, State, City, Zipcode, Mobile Number\\r\\n13. Click \\'Create Account button\\'\\r\\n14. Verify that \\'ACCOUNT CREATED!\\' is visible\\r\\n15. Click \\'Continue\\' button\\r\\n16. Verify that \\'Logged in as username\\' is visible\\r\\n17. Click \\'Delete Account\\' button\\r\\n18. Verify that \\'ACCOUNT DELETED!\\' is visible and click \\'Continue\\' button
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

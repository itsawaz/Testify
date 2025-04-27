// WebdriverIO test script for: http://aioss.in/tms/default.aspx username: admin , password admin login page
// Generated from agent execution history

describe('http://aioss.in/tms/default.aspx username: admin , password admin login page', () => {{
    it('should automate the task', async function() {{
        // Set a reasonable timeout for the test
        this.timeout(30000);
        
        // Step 1: Navigate to URL
        await browser.url('http://aioss.in/tms/default.aspx');
        console.log('Navigated to http://aioss.in/tms/default.aspx');
        await browser.pause(1000); // Wait for page to load
        
    }});
    
    afterEach(async function() {
        // Take screenshot if test fails
        if (this.currentTest.state === 'failed') {
            await browser.saveScreenshot("./error-" + new Date().getTime() + ".png");
        }
    }});
}});

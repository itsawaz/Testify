// WebdriverIO test script for: go to https://chatgpt.com/ and login with my email id ucontactpawan.com
// Generated from agent execution history

describe('go to https://chatgpt.com/ and login with my email id ucontactpawan.com', () => {{
    it('should automate the task', async function() {{
        // Set a reasonable timeout for the test
        this.timeout(30000);
        
    }});
    
    afterEach(async function() {
        // Take screenshot if test fails
        if (this.currentTest.state === 'failed') {
            await browser.saveScreenshot("./error-" + new Date().getTime() + ".png");
        }
    }});
}});

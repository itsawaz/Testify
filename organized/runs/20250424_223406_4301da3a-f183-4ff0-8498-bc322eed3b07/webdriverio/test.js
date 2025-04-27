// WebdriverIO test script for: go google.com
// Generated from agent execution history

describe('go google.com', () => {{
    it('should automate the task', async function() {{
        // Set a reasonable timeout for the test
        this.timeout(30000);
        
        // Step 2: Navigate to URL
        await browser.url('https://www.google.com');
        console.log('Navigated to https://www.google.com');
        await browser.pause(1000); // Wait for page to load
        
    }});
    
    afterEach(async function() {
        // Take screenshot if test fails
        if (this.currentTest.state === 'failed') {
            await browser.saveScreenshot("./error-" + new Date().getTime() + ".png");
        }
    }});
}});

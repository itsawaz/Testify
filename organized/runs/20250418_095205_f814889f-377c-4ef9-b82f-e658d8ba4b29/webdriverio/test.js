// WebdriverIO test script for: hi
// Generated from agent execution history

describe('hi', () => {{
    it('should automate the task', async function() {{
        // Set a reasonable timeout for the test
        this.timeout(30000);
        
        // Step 3: Navigate to URL
        await browser.url('https://www.merriam-webster.com/dictionary/hi');
        console.log('Navigated to https://www.merriam-webster.com/dictionary/hi');
        await browser.pause(1000); // Wait for page to load
        
    }});
    
    afterEach(async function() {
        // Take screenshot if test fails
        if (this.currentTest.state === 'failed') {
            await browser.saveScreenshot("./error-" + new Date().getTime() + ".png");
        }
    }});
}});

// WebdriverIO test script for: go to google.com
// Generated from agent execution history

describe('go to google.com', () => {{
    it('should automate the task', async function() {{
        // Set a reasonable timeout for the test
        this.timeout(30000);
        
        // Step 1: Navigate to URL
        await browser.url('http://www.google.com');
        console.log('Navigated to http://www.google.com');
        await browser.pause(1000); // Wait for page to load
        
        // Final step: Task completion
        console.log('Task completed successfully');
            }});
    
    afterEach(async function() {
        // Take screenshot if test fails
        if (this.currentTest.state === 'failed') {
            await browser.saveScreenshot("./error-" + new Date().getTime() + ".png");
        }
    }});
}});

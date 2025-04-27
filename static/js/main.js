document.addEventListener('DOMContentLoaded', () => {
    const form = document.getElementById('task-form');
    const input = document.getElementById('task-input');
    const submitBtn = document.querySelector('.submit-btn');
    const stopBtn = document.getElementById('stop-button');
    const results = document.getElementById('results');
    const gherkinBtn = document.getElementById('gherkin-btn');
    const playwrightBtn = document.getElementById('playwright-btn');
    const seleniumBtn = document.getElementById('selenium-btn');
    const reportBtn = document.getElementById('report-btn');
    
    // Function to show all download buttons
    function showDownloadButtons() {
        if (gherkinBtn) gherkinBtn.style.display = 'inline-block';
        if (playwrightBtn) playwrightBtn.style.display = 'inline-block';
        if (seleniumBtn) seleniumBtn.style.display = 'inline-block';
        if (reportBtn) {
            reportBtn.style.display = 'inline-block';
            
            // Add pulsing animation to report button
            reportBtn.classList.add('pulse-animation');
            setTimeout(() => {
                reportBtn.classList.remove('pulse-animation');
            }, 2000); // Stop pulsing after 2 seconds
        }
    }
    
    // Auto-resize textarea function
    function autoResizeTextarea() {
        // Reset height to auto to accurately calculate the new height
        input.style.height = 'auto';
        
        // Get the scroll height of the content
        const scrollHeight = input.scrollHeight;
        
        if (scrollHeight > 300) {
            // If content is taller than max-height, add scrollable class
            input.classList.add('scrollable');
            input.style.height = '300px';
        } else {
            // Otherwise remove scrollable class and set height to match content
            input.classList.remove('scrollable');
            input.style.height = scrollHeight + 'px';
        }
    }
    
    // Initialize the textarea height
    autoResizeTextarea();
    
    // Auto-resize the textarea when the user types
    input.addEventListener('input', autoResizeTextarea);
    
    // Prevent Enter key from submitting the form, use Shift+Enter for newlines
    input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            // Prevent the default action (form submission)
            e.preventDefault();
            
            // Insert a newline at the current cursor position
            const start = input.selectionStart;
            const end = input.selectionEnd;
            const value = input.value;
            
            // Insert the newline
            input.value = value.substring(0, start) + '\n' + value.substring(end);
            
            // Set cursor position after the newline
            input.selectionStart = input.selectionEnd = start + 1;
            
            // Trigger resize
            autoResizeTextarea();
        }
    });
    
    // Add a subtle animation to the logo
    const logo = document.querySelector('.logo');
    setInterval(() => {
        logo.style.opacity = '0.8';
        setTimeout(() => {
            logo.style.opacity = '1';
        }, 1500);
    }, 3000);
    
    // Function to replace any waiting emojis with checkmarks throughout the document
    function replaceWaitingEmojis() {
        document.querySelectorAll('.log-item').forEach(item => {
            if (item.textContent.includes('🔄')) {
                item.textContent = item.textContent.replace(/🔄/g, '✅');
            }
        });
    }
    
    // Check for and replace waiting emojis periodically
    setInterval(replaceWaitingEmojis, 1000);
    
    // Keep track of active test
    let activeTestId = null;
    let eventSource = null;
    
    form.addEventListener('submit', (e) => {
        e.preventDefault();
        
        const task = input.value.trim();
        if (!task) return;
        
        // Disable input and button during processing
        input.disabled = true;
        submitBtn.disabled = true;
        input.classList.add('disabled');
        
        // Reset textarea height to default
        input.style.height = 'auto';
        
        // Show stop button
        stopBtn.style.display = 'inline-block';
        
        // Make sure we have the background overlay for grid effect
        const resultsContainer = document.getElementById('results');
        const existingOverlay = resultsContainer.querySelector('.background-overlay.grid-background');
        
        // Create a new test container for this run
        const testContainer = document.createElement('div');
        testContainer.className = 'test-container';
        
        // Add the task header
        const taskHeader = document.createElement('div');
        taskHeader.className = 'task-header';
        taskHeader.textContent = task;
        testContainer.appendChild(taskHeader);
        
        // Create a dedicated container for analysis panels
        const analysisContainer = document.createElement('div');
        analysisContainer.className = 'analysis-panels-container';
        analysisContainer.style.display = 'flex';
        analysisContainer.style.flexDirection = 'column';
        analysisContainer.style.gap = '10px';
        analysisContainer.style.marginBottom = '15px';
        testContainer.appendChild(analysisContainer);
        
        // Add log container
        const logContainer = document.createElement('div');
        logContainer.className = 'log-container';
        testContainer.appendChild(logContainer);
        
        // Add spinner instead of progress bar
        const spinnerDiv = document.createElement('div');
        spinnerDiv.className = 'spinner';
        spinnerDiv.id = 'loading-spinner';
        testContainer.appendChild(spinnerDiv);
        
        // Clear previous results but preserve the grid background
        if (existingOverlay) {
            // Remove only the content elements, not the background
            const children = Array.from(results.childNodes);
            children.forEach(child => {
                if (child !== existingOverlay) {
                    results.removeChild(child);
                }
            });
        } else {
            // No existing overlay, clear everything and add a new one
            results.innerHTML = '';
            const newOverlay = document.createElement('div');
            newOverlay.className = 'background-overlay grid-background';
            results.appendChild(newOverlay);
        }
        
        // Now add the test container
        results.appendChild(testContainer);
        
        // Show download buttons while processing
        if (gherkinBtn) gherkinBtn.style.display = 'none';
        if (playwrightBtn) playwrightBtn.style.display = 'none';
        if (seleniumBtn) seleniumBtn.style.display = 'none';
        if (reportBtn) reportBtn.style.display = 'none';
        
        // Send to Flask server
        const formData = new FormData();
        formData.append('task', task);
        
        fetch('/run-agent', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            // Store the test ID
            activeTestId = data.test_id;
            
            // Set the download buttons to use the specific test
            if (gherkinBtn) gherkinBtn.href = `/download-gherkin/${activeTestId}`;
            if (playwrightBtn) playwrightBtn.href = `/download-playwright/${activeTestId}`;
            if (seleniumBtn) seleniumBtn.href = `/download-selenium/${activeTestId}`;
            if (reportBtn) reportBtn.href = `/generate-playwright-report/${activeTestId}`;
            
            // Start listening for updates
            connectToEventStream(activeTestId, logContainer, testContainer);
        })
        .catch(error => {
            // Show error 
            const errorLog = document.createElement('div');
            errorLog.className = 'log-item error';
            errorLog.textContent = `Error starting test: ${error.message}`;
            logContainer.appendChild(errorLog);
            
            // Hide spinner on error
            const spinner = document.getElementById('loading-spinner');
            if (spinner) spinner.style.display = 'none';
            
            // Re-enable input and button
            input.disabled = false;
            submitBtn.disabled = false;
            input.classList.remove('disabled');
            input.focus();
            
            // Hide stop button
            stopBtn.style.display = 'none';
            
            // Scroll to the bottom of results
            results.scrollTop = results.scrollHeight;
        });
    });
    
    // Handle stop button click
    stopBtn.addEventListener('click', () => {
        if (activeTestId) {
            // Disable the stop button while processing
            stopBtn.disabled = true;
            stopBtn.textContent = 'Stopping...';
            
            // Call the API to stop the test
            fetch(`/stop-test/${activeTestId}`, {
                method: 'POST'
            })
            .then(response => response.json())
            .then(data => {
                const logContainer = document.querySelector('.log-container');
                
                if (logContainer) {
                    const stopMessage = document.createElement('div');
                    stopMessage.className = 'log-item warning';
                    stopMessage.textContent = '⚠️ Test stopped by user - Terminating browser processes';
                    logContainer.appendChild(stopMessage);
                    
                    // Add completion status to test container
                    const testContainer = logContainer.closest('.test-container');
                    if (testContainer) {
                        const completionStatus = document.createElement('div');
                        completionStatus.className = 'completion-status failure';
                        completionStatus.innerHTML = '❌ Test Terminated by User';
                        testContainer.appendChild(completionStatus);
                        
                        // Hide spinner when stopped
                        const spinner = document.getElementById('loading-spinner');
                        if (spinner) spinner.style.display = 'none';
                    }
                }
                
                // Re-enable input and button
                input.disabled = false;
                submitBtn.disabled = false;
                input.classList.remove('disabled');
                
                // Hide stop button
                stopBtn.style.display = 'none';
                stopBtn.disabled = false;
                stopBtn.textContent = 'Stop Test';
                
                // Show report buttons
                showDownloadButtons();
                
                // Close event source
                if (eventSource) {
                    eventSource.close();
                }
            })
            .catch(error => {
                console.error('Error stopping test:', error);
                stopBtn.disabled = false;
                stopBtn.textContent = 'Stop Test';
            });
        }
    });
    
    function connectToEventStream(testId, logContainer, testContainer) {
        // Check status first to handle reconnection cases
        fetch(`/test-status/${testId}`)
            .then(response => response.json())
            .then(data => {
                if (data.complete) {
                    // Test was already complete - update UI accordingly
                    const completionStatus = document.createElement('div');
                    completionStatus.className = 'completion-status ' + (data.success ? 'success' : 'failure');
                    completionStatus.innerHTML = data.success ? '✅ Test Complete' : '❌ Test Failed';
                    
                    // Hide spinner when complete
                    const spinner = document.getElementById('loading-spinner');
                    if (spinner) spinner.style.display = 'none';
                    
                    testContainer.appendChild(completionStatus);
                    
                    // Show download buttons
                    showDownloadButtons();
                    
                    // Re-enable input and button
                    input.disabled = false;
                    submitBtn.disabled = false;
                    input.classList.remove('disabled');
                    
                    // Hide stop button
                    stopBtn.style.display = 'none';
                    
                    // Trigger the test-completed event
                    const event = new CustomEvent('test-completed', {
                        detail: { testId: testId }
                    });
                    document.dispatchEvent(event);
                    
                    return;
                }
                
                // Create terminal header
                const terminalHeader = document.createElement('div');
                terminalHeader.style.backgroundColor = '#1a1a1a';
                terminalHeader.style.borderTopLeftRadius = '5px';
                terminalHeader.style.borderTopRightRadius = '5px';
                terminalHeader.style.padding = '8px 12px';
                terminalHeader.style.display = 'flex';
                terminalHeader.style.alignItems = 'center';
                terminalHeader.style.borderBottom = '1px solid #333';
                
                // Terminal buttons (macOS style)
                const terminalButtons = document.createElement('div');
                terminalButtons.style.display = 'flex';
                terminalButtons.style.gap = '6px';
                
                // Create buttons
                const buttons = ['#ff5f56', '#ffbd2e', '#27c93f'].forEach(color => {
                    const button = document.createElement('div');
                    button.style.width = '12px';
                    button.style.height = '12px';
                    button.style.borderRadius = '50%';
                    button.style.backgroundColor = color;
                    terminalButtons.appendChild(button);
                });
                
                // Terminal title
                const terminalTitle = document.createElement('div');
                terminalTitle.style.color = '#ccc';
                terminalTitle.style.fontSize = '12px';
                terminalTitle.style.marginLeft = '10px';
                terminalTitle.textContent = 'Terminal — Test Execution Logs';
                
                terminalHeader.appendChild(terminalButtons);
                terminalHeader.appendChild(terminalTitle);
                
                // Set up a terminal-style container
                const terminalContainer = document.createElement('div');
                terminalContainer.style.backgroundColor = '#000';
                terminalContainer.style.color = '#ddd';
                terminalContainer.style.fontFamily = 'Menlo, Monaco, Consolas, monospace';
                terminalContainer.style.fontSize = '13px';
                terminalContainer.style.lineHeight = '1.5';
                terminalContainer.style.padding = '10px';
                terminalContainer.style.borderBottomLeftRadius = '5px';
                terminalContainer.style.borderBottomRightRadius = '5px';
                terminalContainer.style.maxHeight = '400px';
                terminalContainer.style.overflowY = 'auto';
                terminalContainer.style.whiteSpace = 'pre-wrap';
                terminalContainer.style.boxShadow = 'inset 0 0 10px rgba(0, 0, 0, 0.5)';
                
                // Add the header and terminal container to the log container
                logContainer.appendChild(terminalHeader);
                logContainer.appendChild(terminalContainer);
                
                // Connect to the event stream for updates
                eventSource = new EventSource(`/stream-updates/${testId}`);
                
                eventSource.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    
                    // Skip initial data
                    if (data.initial) return;
                    
                    // Handle log messages
                    if (data.log) {
                        const logElement = document.createElement('div');
                        logElement.style.padding = '2px 0';
                        
                        // Styling based on content
                        if (data.log.includes('===')) {
                            // Section divider styling
                            logElement.style.color = '#8bc34a';
                            logElement.style.fontWeight = 'bold';
                            logElement.style.borderBottom = '1px dashed #333';
                            logElement.style.margin = '5px 0';
                            logElement.style.padding = '3px 0';
                        } else if (data.log.includes('ERROR') || data.log.includes('❌')) {
                            logElement.style.color = '#ff5252';
                        } else if (data.log.includes('WARNING') || data.log.includes('⚠️')) {
                            logElement.style.color = '#ffab40';
                        } else if (data.log.includes('INFO') || data.log.includes('ℹ️')) {
                            logElement.style.color = '#29b6f6';
                        } else if (data.log.includes('DEBUG')) {
                            logElement.style.color = '#b39ddb';
                        } else if (data.log.includes('✅')) {
                            logElement.style.color = '#66bb6a';
                        } else if (data.log.includes('[controller]') || data.log.includes('🔗')) {
                            logElement.style.color = '#42a5f5';
                        } else if (data.log.includes('🖱️') || data.log.includes('⌨️')) {
                            logElement.style.color = '#ec407a';
                        } else if (data.log.match(/\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}/)) {
                            logElement.style.color = '#8bc34a';
                        }
                        
                        logElement.textContent = data.log;
                        terminalContainer.appendChild(logElement);
                        
                        // Keep scrolled to bottom
                        terminalContainer.scrollTop = terminalContainer.scrollHeight;
                    }
                    
                    // Handle error messages
                    if (data.error && !data.log) {
                        const errorElement = document.createElement('div');
                        errorElement.style.color = '#ff5252';
                        errorElement.style.padding = '2px 0';
                        errorElement.textContent = `ERROR: ${data.error}`;
                        terminalContainer.appendChild(errorElement);
                        terminalContainer.scrollTop = terminalContainer.scrollHeight;
                    }
                    
                    // Handle test completion
                    if (data.complete) {
                        // Hide spinner when complete
                        const spinner = document.getElementById('loading-spinner');
                        if (spinner) spinner.style.display = 'none';
                        
                        const successClass = data.success ? 'success' : 'failure';
                        const statusIcon = data.success ? '✅' : '❌';
                        const statusText = data.success ? 'Test Complete' : 'Test Failed';
                        
                        // Add completion status if it doesn't exist
                        if (!testContainer.querySelector('.completion-status')) {
                            const completionStatus = document.createElement('div');
                            completionStatus.className = `completion-status ${successClass}`;
                            completionStatus.innerHTML = `${statusIcon} ${statusText}`;
                            
                            testContainer.appendChild(completionStatus);
                        }
                        
                        // Re-enable the form and hide the stop button
                        input.disabled = false;
                        submitBtn.disabled = false;
                        input.classList.remove('disabled');
                        stopBtn.style.display = 'none';
                        
                        // Show download buttons
                        showDownloadButtons();
                        
                        // Close the event source
                        eventSource.close();
                        
                        // Trigger the test-completed event
                        const event = new CustomEvent('test-completed', {
                            detail: { testId: testId }
                        });
                        document.dispatchEvent(event);
                    }
                    
                    // Scroll to the bottom of results
                    results.scrollTop = results.scrollHeight;
                };
                
                eventSource.onerror = (error) => {
                    console.error('EventSource failed:', error);
                    eventSource.close();
                    
                    // Add error message to log
                    const errorElement = document.createElement('div');
                    errorElement.style.color = '#ff5252';
                    errorElement.style.padding = '2px 0';
                    errorElement.textContent = 'Connection to server lost. Test status unknown.';
                    terminalContainer.appendChild(errorElement);
                    
                    // Hide spinner on error
                    const spinner = document.getElementById('loading-spinner');
                    if (spinner) spinner.style.display = 'none';
                    
                    // Re-enable form and hide stop button
                    input.disabled = false;
                    submitBtn.disabled = false;
                    input.classList.remove('disabled');
                    stopBtn.style.display = 'none';
                };
            });
    }
    
    function handleSpecialEvent(data, logContainer, testContainer) {
        if (!data.log) return;
        
        const logText = data.log;
        
        // Find or create the analysis container
        let analysisContainer = testContainer.querySelector('.analysis-panels-container');
        if (!analysisContainer) {
            analysisContainer = document.createElement('div');
            analysisContainer.className = 'analysis-panels-container';
            analysisContainer.style.display = 'flex';
            analysisContainer.style.flexDirection = 'column';
            analysisContainer.style.gap = '10px';
            analysisContainer.style.marginBottom = '15px';
            testContainer.insertBefore(analysisContainer, logContainer);
        }
        
        // Parse Planning Analysis JSON (look for lines starting with { and ending with })
        if (logText.includes('Planning Analysis:')) {
            try {
                const jsonStart = logText.indexOf('{');
                const jsonEnd = logText.lastIndexOf('}') + 1;
                
                if (jsonStart > 0 && jsonEnd > jsonStart) {
                    const jsonStr = logText.substring(jsonStart, jsonEnd);
                    const analysisData = JSON.parse(jsonStr);
                    
                    // Add state analysis panel
                    if (analysisData.state_analysis) {
                        const statePanel = window.createAnalysisPanel('state-analysis', analysisData.state_analysis);
                        // Insert at the beginning of the analysis container
                        analysisContainer.insertBefore(statePanel, analysisContainer.firstChild);
                    }
                    
                    // Add other analysis sections if available
                    if (analysisData.progress_evaluation || analysisData.challenges || 
                        analysisData.next_steps || analysisData.reasoning) {
                        const analysisObj = {
                            progress: analysisData.progress_evaluation,
                            challenges: analysisData.challenges,
                            nextSteps: analysisData.next_steps,
                            reasoning: analysisData.reasoning
                        };
                        const detailsPanel = window.createAnalysisPanel('state-analysis', analysisObj);
                        // Insert after state analysis panel
                        if (analysisContainer.firstChild) {
                            analysisContainer.insertBefore(detailsPanel, analysisContainer.firstChild.nextSibling);
                        } else {
                            analysisContainer.appendChild(detailsPanel);
                        }
                    }
                }
            } catch (e) {
                console.error('Error parsing Planning Analysis JSON:', e);
            }
        }
        
        // Look for Eval, Memory, and Goal information
        const evalMatch = logText.match(/👍 Eval: (.+)/);
        const memoryMatch = logText.match(/🧠 Memory: (.+)/);
        const goalMatch = logText.match(/🎯 Next goal: (.+)/);
        
        if (evalMatch && evalMatch[1]) {
            const evalPanel = window.createAnalysisPanel('eval', evalMatch[1]);
            analysisContainer.appendChild(evalPanel);
        }
        
        if (memoryMatch && memoryMatch[1]) {
            const memoryPanel = window.createAnalysisPanel('memory', memoryMatch[1]);
            analysisContainer.appendChild(memoryPanel);
        }
        
        if (goalMatch && goalMatch[1]) {
            const goalPanel = window.createAnalysisPanel('goal', goalMatch[1]);
            analysisContainer.appendChild(goalPanel);
        }
        
        // Add the log entry to the UI
        addLogEntryToUI(logText, logContainer);
    }
    
    function updateProgressIndicator(indicator, data) {
        const progressFill = indicator.querySelector('.progress-fill');
        const progressStatus = indicator.querySelector('.progress-status');
        
        if (!progressFill || !progressStatus) return;
        
        if (data.complete) {
            progressFill.style.width = '100%';
            progressStatus.textContent = data.success ? 'Test completed successfully!' : 'Test completed with errors';
            indicator.className = `progress-indicator ${data.success ? 'success' : 'error'}`;
        } else if (data.new_steps && data.total_steps) {
            // Calculate progress as a percentage
            const progress = Math.min(data.current_step / Math.max(data.total_steps, 5) * 100, 98);
            progressFill.style.width = `${progress}%`;
            progressStatus.textContent = `Running step ${data.current_step}/${data.total_steps}`;
        } else if (data.log_entry) {
            // Update status with current activity
            const status = extractStatusFromLog(data.log_entry);
            if (status) {
                progressStatus.textContent = status;
            }
        }
    }
    
    function extractStatusFromLog(logEntry) {
        // Extract a user-friendly status message from log entries
        if (typeof logEntry === 'object' && logEntry.log_entry) {
            logEntry = logEntry.log_entry;
        }
        
        if (typeof logEntry !== 'string') return null;
        
        // Look for key phrases that indicate status
        if (logEntry.includes('Navigating to')) {
            return 'Navigating to webpage...';
        } else if (logEntry.includes('Clicking')) {
            return 'Interacting with page elements...';
        } else if (logEntry.includes('typing') || logEntry.includes('entering')) {
            return 'Entering data...';
        } else if (logEntry.includes('Waiting')) {
            return 'Waiting for page to respond...';
        } else if (logEntry.includes('Verifying')) {
            return 'Verifying results...';
        } else if (logEntry.includes('login') || logEntry.includes('logging in')) {
            return 'Handling login process...';
        } else if (logEntry.includes('logout') || logEntry.includes('logging out')) {
            return 'Performing logout...';
        }
        
        return null;
    }
    
    function updateDownloadButtons(testId, runId) {
        if (gherkinBtn) {
            gherkinBtn.href = `/download-gherkin/${testId}`;
            gherkinBtn.style.display = 'inline-block';
        }
        
        if (playwrightBtn) {
            playwrightBtn.href = `/download-playwright/${testId}`;
            playwrightBtn.style.display = 'inline-block';
        }
        
        if (seleniumBtn) {
            seleniumBtn.href = `/download-selenium/${testId}`;
            seleniumBtn.style.display = 'inline-block';
        }
        
        if (reportBtn) {
            reportBtn.href = `/generate-playwright-report/${testId}`;
            reportBtn.style.display = 'inline-block';
            reportBtn.setAttribute('target', '_blank');
            
            // Add attention-grabbing animation
            reportBtn.classList.add('pulse-animation');
            setTimeout(() => {
                reportBtn.classList.remove('pulse-animation');
            }, 2000);
        }
    }
    
    function addFormattedLogToUI(step, container) {
        const logItem = document.createElement('div');
        logItem.className = 'log-item';
        
        if (step.success !== null) {
            logItem.classList.add(step.success ? 'success' : 'error');
        }
        
        // Format the log entry with improved descriptions
        let iconPrefix = '✅'; // Default to checkmark for executed steps
        if (step.success === false) iconPrefix = '❌';
        
        // Improve step descriptions based on step number and content
        let description = step.description;
        if (description === "Initializing test agent - Setting up browser automation") {
            description = "Initializing Browser - Setting up automation environment";
        } else if (description.match(/Step \d+\/100/)) {
            // Based on step number, provide a better description
            const stepNum = step.step_num;
            if (stepNum === 2) {
                description = "Navigating to Target Website";
            } else if (stepNum === 3) {
                description = "Interacting with Login Form";
            } else if (stepNum === 4) {
                description = "Submitting Credentials";
            } else if (stepNum === 5) {
                description = "Verifying Login Success";
            } else {
                // For other steps, use the details to create a better description
                if (step.details && step.details.includes("navigate")) {
                    description = "Navigating to New Page";
                } else if (step.details && (step.details.includes("click") || step.details.includes("select"))) {
                    description = "Interacting with Element";
                } else if (step.details && (step.details.includes("form") || step.details.includes("fill"))) {
                    description = "Filling Form Data";
                } else if (step.details && step.details.includes("submit")) {
                    description = "Submitting Data";
                } else if (step.details && (step.details.includes("verify") || step.details.includes("check"))) {
                    description = "Verifying Results";
                } else {
                    description = "Executing Action " + description;
                }
            }
        }
        
        logItem.textContent = `${iconPrefix} Step ${step.step_num}: ${description} ${step.details ? '- ' + step.details : ''}`;
        
        container.appendChild(logItem);
    }
    
    function addLogEntryToUI(logEntry, container, type = null) {
        const logItem = document.createElement('div');
        logItem.className = 'log-item';
        
        // Get the log type from data or fallback to parameter
        const logType = type || (typeof logEntry === 'object' && logEntry.type) ? logEntry.type : classifyLogEntry(logEntry);
        
        // Apply appropriate styling based on log type
        logItem.classList.add(logType);
        
        // Add appropriate icon based on log type
        let icon = '';
        switch(logType) {
            case 'error':
                icon = '❌ ';
                break;
            case 'warning':
                icon = '⚠️ ';
                break;
            case 'success':
                icon = '✅ ';
                break;
            case 'info':
                icon = 'ℹ️ ';
                break;
            case 'navigation':
                icon = '🌐 ';
                break;
            case 'interaction':
                icon = '👆 ';
                break;
            case 'input':
                icon = '⌨️ ';
                break;
            case 'wait':
                icon = '⏱️ ';
                break;
            case 'auth':
                icon = '🔐 ';
                break;
            default:
                icon = '▶️ ';
        }
        
        // Format the log entry text
        let logText = typeof logEntry === 'string' ? logEntry : logEntry.log_entry || '';
        
        // Replace 🔄 with ✅ to indicate completion
        logText = logText.replace(/🔄/g, '✅');
        
        // Enhance log entry format with highlighting and structure
        const enhancedText = formatLogText(logText);
        
        // Apply special formatting for auth events
        if (logType === 'auth') {
            logItem.classList.add('highlight-animation');
        }
        
        // Set content with icon and formatted text
        logItem.innerHTML = `${icon}${enhancedText}`;
        
        // Add timestamp if available
        if (typeof logEntry === 'object' && logEntry.timestamp) {
            const timeElement = document.createElement('span');
            timeElement.className = 'log-timestamp';
            const date = new Date(logEntry.timestamp * 1000);
            timeElement.textContent = `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}:${date.getSeconds().toString().padStart(2, '0')}`;
            logItem.appendChild(timeElement);
        }
        
        container.appendChild(logItem);
        
        // Add special animation for important events
        if ((logType === 'success' || logType === 'error' || logType === 'auth') && !logItem.classList.contains('highlight-animation')) {
            logItem.classList.add('highlight-animation');
            setTimeout(() => {
                logItem.classList.remove('highlight-animation');
            }, 2000);
        }
    }
    
    function formatLogText(text) {
        // Highlight URLs
        text = text.replace(/(https?:\/\/[^\s]+)/g, '<span class="url">$1</span>');
        
        // Highlight important terms
        const highlightTerms = {
            'success': 'success-text',
            'failed': 'error-text',
            'error': 'error-text',
            'warning': 'warning-text',
            'completed': 'success-text',
            'login': 'auth-text',
            'logout': 'auth-text',
            'authenticated': 'auth-text',
            'clicking': 'interaction-text',
            'navigating': 'navigation-text',
            'waiting': 'wait-text',
            'input': 'input-text',
            'typing': 'input-text'
        };
        
        Object.keys(highlightTerms).forEach(term => {
            const regex = new RegExp(`(${term})`, 'gi');
            text = text.replace(regex, `<span class="${highlightTerms[term]}">$1</span>`);
        });
        
        // Make step numbers bold
        text = text.replace(/(Step \d+):/g, '<strong>$1</strong>:');
        
        // Enhance element selectors
        text = text.replace(/\[(.*?)\]/g, '<code>[$1]</code>');
        
        return text;
    }
    
    function classifyLogEntry(logText) {
        // Determine log type for UI formatting
        if (typeof logText === 'string') {
            logText = logText.toLowerCase();
            
            if (logText.includes('error') || logText.includes('exception') || logText.includes('fail')) {
                return 'error';
            } else if (logText.includes('warning') || logText.includes('warn')) {
                return 'warning';
            } else if (logText.includes('success') || logText.includes('✅') || logText.includes('completed')) {
                return 'success';
            } else if (logText.includes('navigate') || logText.includes('url')) {
                return 'navigation';
            } else if (logText.includes('click') || logText.includes('select') || logText.includes('interact')) {
                return 'interaction';
            } else if (logText.includes('input') || logText.includes('type') || logText.includes('fill')) {
                return 'input';
            } else if (logText.includes('wait') || logText.includes('delay')) {
                return 'wait';
            } else if (logText.includes('login') || logText.includes('logout') || logText.includes('auth')) {
                return 'auth';
            } else if (logText.includes('info') || logText.includes('step')) {
                return 'info';
            }
        }
        return 'default';
    }
    
    // Focus the input field when the page loads
    input.focus();
    
    // Add subtle movement to grid background on mouse move
    const resultsContainer = document.getElementById('results');
    if (resultsContainer) {
        const gridBackground = resultsContainer.querySelector('.background-overlay.grid-background');
        
        resultsContainer.addEventListener('mousemove', function(e) {
            if (!gridBackground) return;
            
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left; // x position within the element
            const y = e.clientY - rect.top;  // y position within the element
            
            // Calculate percentage for movement (limited range)
            const moveX = (x / rect.width - 0.5) * 8;  // -4px to 4px movement
            const moveY = (y / rect.height - 0.5) * 8; // -4px to 4px movement
            
            // Update grid background position
            gridBackground.style.backgroundPosition = `calc(center + ${moveX}px) calc(center + ${moveY}px)`;
            
            // Add subtle glow effect where the mouse is
            gridBackground.style.background = `radial-gradient(
                circle at ${x}px ${y}px,
                rgba(0, 0, 0, 0) 0%,
                rgba(0, 0, 0, 0.4) 100%
            )`;
        });
        
        // Reset position when mouse leaves
        resultsContainer.addEventListener('mouseleave', function() {
            if (!gridBackground) return;
            
            gridBackground.style.backgroundPosition = 'center center';
            gridBackground.style.background = 'radial-gradient(circle at center, rgba(0, 0, 0, 0) 0%, rgba(0, 0, 0, 0.3) 100%)';
        });
    }
}); 
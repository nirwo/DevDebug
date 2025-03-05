document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const welcomeScreen = document.getElementById('welcome-screen');
    const stepLogSource = document.getElementById('step-log-source');
    const stepAnalyzing = document.getElementById('step-analyzing');
    const stepResults = document.getElementById('step-results');
    const stepSolutions = document.getElementById('step-solutions');
    
    // Navigation elements
    const navAnalyze = document.getElementById('nav-analyze');
    const navHistory = document.getElementById('nav-history');
    const navSettings = document.getElementById('nav-settings');
    
    // Buttons
    const startWizardBtn = document.getElementById('start-wizard');
    const backToWelcomeBtn = document.getElementById('back-to-welcome');
    const nextToAnalyzingBtn = document.getElementById('next-to-analyzing');
    const backToLogSourceBtn = document.getElementById('back-to-log-source');
    const cancelAnalysisBtn = document.getElementById('cancel-analysis');
    const backToAnalyzingBtn = document.getElementById('back-to-analyzing');
    const nextToSolutionsBtn = document.getElementById('next-to-solutions');
    const backToResultsBtn = document.getElementById('back-to-results');
    const startNewAnalysisBtn = document.getElementById('start-new-analysis');
    
    // Log source options
    const optionUrl = document.getElementById('option-url');
    const optionPaste = document.getElementById('option-paste');
    const optionUpload = document.getElementById('option-upload');
    
    // Input panels
    const urlInput = document.getElementById('url-input');
    const pasteInput = document.getElementById('paste-input');
    const uploadInput = document.getElementById('upload-input');
    
    // Form inputs
    const logUrlInput = document.getElementById('log-url');
    const logContentInput = document.getElementById('log-content');
    const logFileInput = document.getElementById('log-file');
    const selectedFileText = document.querySelector('.selected-file');
    
    // Analysis results elements
    const resultTechnology = document.getElementById('result-technology');
    const resultErrorType = document.getElementById('result-error-type');
    const resultSeverity = document.getElementById('result-severity');
    const resultErrorMessage = document.getElementById('result-error-message');
    const resultContext = document.getElementById('result-context');
    const resultRootCauses = document.getElementById('result-root-causes');
    
    // Solutions elements
    const solutionsList = document.getElementById('solutions-list');
    const solutionTemplate = document.getElementById('solution-template');
    
    // Feedback elements
    const feedbackYes = document.getElementById('feedback-yes');
    const feedbackNo = document.getElementById('feedback-no');
    const feedbackForm = document.querySelector('.feedback-form');
    const feedbackText = document.getElementById('feedback-text');
    const submitFeedback = document.getElementById('submit-feedback');
    
    // State variables
    let currentAnalysis = null;
    let selectedSolution = null;
    let fileContent = null;
    
    // Helper Functions
    function showScreen(screen) {
        // Hide all screens
        [welcomeScreen, stepLogSource, stepAnalyzing, stepResults, stepSolutions].forEach(s => {
            s.classList.remove('active');
        });
        
        // Show the selected screen
        screen.classList.add('active');
    }
    
    function selectSourceOption(option) {
        // Remove active class from all options
        [optionUrl, optionPaste, optionUpload].forEach(opt => {
            opt.classList.remove('active');
        });
        
        // Hide all input panels
        [urlInput, pasteInput, uploadInput].forEach(panel => {
            panel.classList.remove('active');
        });
        
        // Activate selected option and its input panel
        option.classList.add('active');
        
        if (option === optionUrl) {
            urlInput.classList.add('active');
        } else if (option === optionPaste) {
            pasteInput.classList.add('active');
        } else if (option === optionUpload) {
            uploadInput.classList.add('active');
        }
    }
    
    function updateAnalysisStatus(status) {
        document.getElementById('analysis-status').textContent = status;
    }
    
    function displayAnalysis(analysis, container) {
        if (!analysis) {
            container.innerHTML = '<p class="error">No analysis data available</p>';
            return;
        }
        
        let html = `
            <div class="analysis-section">
                <h3>Error Type</h3>
                <p class="error-type">${analysis.error_type || 'Unknown'}</p>
            </div>
            
            <div class="analysis-section">
                <h3>Error Message</h3>
                <p class="error-message">${analysis.error_message || 'No specific error message found'}</p>
            </div>
            
            <div class="analysis-section">
                <h3>Severity</h3>
                <div class="severity-indicator severity-${analysis.severity?.toLowerCase() || 'unknown'}">
                    ${analysis.severity || 'Unknown'}
                </div>
            </div>
        `;
        
        if (analysis.context && analysis.context.length > 0) {
            html += `
                <div class="analysis-section">
                    <h3>Context</h3>
                    <pre class="context-code">${analysis.context.join('\n')}</pre>
                </div>
            `;
        }
        
        if (analysis.tech_stack) {
            html += `
                <div class="analysis-section">
                    <h3>Technology Stack</h3>
                    <p>${analysis.tech_stack.join(', ')}</p>
                </div>
            `;
        }
        
        if (analysis.potential_causes && analysis.potential_causes.length > 0) {
            html += `
                <div class="analysis-section">
                    <h3>Potential Causes</h3>
                    <ul class="causes-list">
                        ${analysis.potential_causes.map(cause => `<li>${cause}</li>`).join('')}
                    </ul>
                </div>
            `;
        }
        
        container.innerHTML = html;
    }
    
    function displaySolutions(solutions, container) {
        if (!solutions || solutions.length === 0) {
            container.innerHTML = '<p class="no-solutions">No solution suggestions available yet. Try providing more context or refining your log data.</p>';
            return;
        }
        
        let html = '<div class="solutions-list">';
        
        solutions.forEach((solution, index) => {
            const successRatePercent = (solution.success_rate || 0) * 100;
            
            html += `
                <div class="solution-card">
                    <div class="solution-header">
                        <h3>Solution ${index + 1}</h3>
                        <div class="success-rate">
                            <div class="progress-bar">
                                <div class="progress" style="width: ${successRatePercent}%"></div>
                            </div>
                            <span>${successRatePercent.toFixed(0)}% Success Rate</span>
                        </div>
                    </div>
                    
                    <div class="solution-body">
                        <p>${solution.description || 'No description available'}</p>
                        
                        ${solution.steps && solution.steps.length > 0 ? `
                            <h4>Steps to Fix</h4>
                            <ol class="solution-steps">
                                ${solution.steps.map(step => `<li>${step}</li>`).join('')}
                            </ol>
                        ` : ''}
                        
                        ${solution.code_example ? `
                            <h4>Code Example</h4>
                            <pre class="code-example">${solution.code_example}</pre>
                        ` : ''}
                        
                        ${solution.references && solution.references.length > 0 ? `
                            <h4>References</h4>
                            <ul class="references-list">
                                ${solution.references.map(ref => `<li><a href="${ref.url}" target="_blank">${ref.title || ref.url}</a></li>`).join('')}
                            </ul>
                        ` : ''}
                    </div>
                    
                    <div class="solution-footer">
                        <button class="btn btn-outline feedback-btn" data-solution-id="${solution.id || index}">Give Feedback</button>
                    </div>
                </div>
            `;
        });
        
        html += '</div>';
        container.innerHTML = html;
        
        // Add event listeners to feedback buttons
        document.querySelectorAll('.feedback-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const solutionId = btn.getAttribute('data-solution-id');
                // Show feedback form
                console.log(`Feedback requested for solution ${solutionId}`);
                // TODO: Implement feedback submission
            });
        });
    }
    
    async function analyzeLog() {
        const logUrlInput = document.getElementById('log-url');
        const logContentInput = document.getElementById('log-content');
        const uploadedFile = document.getElementById('log-file').files[0];
        const resultContainer = document.getElementById('result-container');
        const analysisResult = document.getElementById('analysis-result');
        const solutionsResult = document.getElementById('solutions-result');
        const loadingIndicator = document.getElementById('loading');
        
        let logContent = logContentInput.value;
        let logUrl = logUrlInput.value;
        
        // Validate input
        if (!logContent && !logUrl && !uploadedFile) {
            showError('Please provide a log URL, content, or upload a file.');
            return;
        }
        
        // Show loading indicator
        loadingIndicator.style.display = 'block';
        resultContainer.style.display = 'none';
        
        try {
            // If file was uploaded, read its contents
            if (uploadedFile) {
                logContent = await readFileContent(uploadedFile);
            }
            
            // Prepare request data
            const requestData = {
                log_url: logUrl || null,
                log_content: logContent || null
            };
            
            console.log('Sending request with data:', requestData);
            
            // Send request to backend
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(requestData)
            });
            
            // Log raw response for debugging
            const rawResponse = await response.text();
            console.log('Raw response:', rawResponse);
            
            // Parse JSON
            let data;
            try {
                data = JSON.parse(rawResponse);
            } catch (e) {
                console.error('JSON parse error:', e);
                throw new Error(`Failed to parse response: ${rawResponse.substring(0, 100)}...`);
            }
            
            // Handle error response
            if (!response.ok) {
                throw new Error(data.error || `Server error: ${response.status}`);
            }
            
            // Display analysis results
            displayAnalysis(data.analysis, analysisResult);
            
            // Display solution suggestions
            displaySolutions(data.solutions, solutionsResult);
            
            // Show results container
            resultContainer.style.display = 'block';
        } catch (error) {
            console.error('Error during analysis:', error);
            showError(`Error analyzing log: ${error.message}`);
        } finally {
            // Hide loading indicator
            loadingIndicator.style.display = 'none';
        }
    }
    
    function showError(message) {
        const errorContainer = document.getElementById('error-container');
        const errorMessage = document.getElementById('error-message');
        
        errorMessage.textContent = message;
        errorContainer.style.display = 'block';
        
        // Hide loading indicator if showing
        document.getElementById('loading').style.display = 'none';
        
        // Auto-hide after 5 seconds
        setTimeout(() => {
            errorContainer.style.display = 'none';
        }, 5000);
    }
    
    async function submitFeedbackData(feedbackData) {
        try {
            const response = await fetch('/api/learn', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(feedbackData)
            });
            
            if (!response.ok) {
                throw new Error(`Error: ${response.status}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error('Feedback submission error:', error);
            return { success: false, error: error.message };
        }
    }
    
    // File upload handling
    function handleFileUpload(file) {
        if (!file) return;
        
        selectedFileText.textContent = file.name;
        
        const reader = new FileReader();
        reader.onload = function(e) {
            fileContent = e.target.result;
        };
        reader.readAsText(file);
    }
    
    // Event listeners
    
    // Navigation
    startWizardBtn.addEventListener('click', () => {
        showScreen(stepLogSource);
        selectSourceOption(optionUrl); // Default to URL option
    });
    
    backToWelcomeBtn.addEventListener('click', () => {
        showScreen(welcomeScreen);
    });
    
    nextToAnalyzingBtn.addEventListener('click', () => {
        // Get the log content based on the selected source option
        let logSource = {};
        
        if (optionUrl.classList.contains('active')) {
            const url = logUrlInput.value.trim();
            if (!url) {
                alert('Please enter a valid URL');
                return;
            }
            logSource = { log_url: url };
        } else if (optionPaste.classList.contains('active')) {
            const content = logContentInput.value.trim();
            if (!content) {
                alert('Please paste log content');
                return;
            }
            logSource = { log_content: content };
        } else if (optionUpload.classList.contains('active')) {
            if (!fileContent) {
                alert('Please upload a file');
                return;
            }
            logSource = { log_content: fileContent };
        }
        
        // Show analyzing screen
        showScreen(stepAnalyzing);
        
        // Start analysis
        analyzeLog();
    });
    
    backToLogSourceBtn.addEventListener('click', () => {
        showScreen(stepLogSource);
    });
    
    cancelAnalysisBtn.addEventListener('click', () => {
        // Cancel the analysis (in a real app, you would abort the fetch)
        showScreen(stepLogSource);
    });
    
    backToAnalyzingBtn.addEventListener('click', () => {
        showScreen(stepAnalyzing);
    });
    
    nextToSolutionsBtn.addEventListener('click', () => {
        showScreen(stepSolutions);
    });
    
    backToResultsBtn.addEventListener('click', () => {
        showScreen(stepResults);
    });
    
    startNewAnalysisBtn.addEventListener('click', () => {
        // Reset state
        currentAnalysis = null;
        selectedSolution = null;
        fileContent = null;
        
        // Clear inputs
        logUrlInput.value = '';
        logContentInput.value = '';
        logFileInput.value = '';
        selectedFileText.textContent = '';
        
        // Reset feedback form
        feedbackForm.classList.remove('active');
        feedbackText.value = '';
        
        // Show log source screen
        showScreen(stepLogSource);
        selectSourceOption(optionUrl);
    });
    
    // Source options
    optionUrl.addEventListener('click', () => {
        selectSourceOption(optionUrl);
    });
    
    optionPaste.addEventListener('click', () => {
        selectSourceOption(optionPaste);
    });
    
    optionUpload.addEventListener('click', () => {
        selectSourceOption(optionUpload);
    });
    
    // File upload
    logFileInput.addEventListener('change', (e) => {
        handleFileUpload(e.target.files[0]);
    });
    
    // Drag and drop for file upload
    const dropZone = document.querySelector('.file-upload-area');
    
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        handleFileUpload(e.dataTransfer.files[0]);
    });
    
    // Feedback
    feedbackYes.addEventListener('click', () => {
        feedbackForm.classList.add('active');
        feedbackText.placeholder = 'Great! Tell us what worked well...';
    });
    
    feedbackNo.addEventListener('click', () => {
        feedbackForm.classList.add('active');
        feedbackText.placeholder = 'Sorry to hear that. Please tell us what went wrong...';
    });
    
    submitFeedback.addEventListener('click', async () => {
        const feedbackData = {
            log_content: currentAnalysis ? currentAnalysis.error_message : '',
            analysis: currentAnalysis,
            feedback: feedbackText.value,
            solution_applied: selectedSolution ? selectedSolution.solution : null,
            solution_worked: feedbackYes.classList.contains('active')
        };
        
        const result = await submitFeedbackData(feedbackData);
        
        if (result.success) {
            alert('Thank you for your feedback!');
            feedbackForm.classList.remove('active');
            feedbackText.value = '';
        } else {
            alert('Error submitting feedback: ' + (result.error || 'Unknown error'));
        }
    });
    
    // Additional UI interactions
    feedbackYes.addEventListener('click', function() {
        this.classList.add('active');
        feedbackNo.classList.remove('active');
    });
    
    feedbackNo.addEventListener('click', function() {
        this.classList.add('active');
        feedbackYes.classList.remove('active');
    });
    
    // Navigation menu
    navAnalyze.addEventListener('click', (e) => {
        e.preventDefault();
        document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
        navAnalyze.classList.add('active');
        showScreen(welcomeScreen);
    });
    
    // Initialize file drop zone styling
    document.querySelector('.file-upload-area').addEventListener('dragover', function(e) {
        e.preventDefault();
        this.style.borderColor = 'var(--primary-color)';
        this.style.backgroundColor = 'rgba(74, 108, 247, 0.05)';
    });
    
    document.querySelector('.file-upload-area').addEventListener('dragleave', function(e) {
        e.preventDefault();
        this.style.borderColor = 'var(--border-color)';
        this.style.backgroundColor = 'transparent';
    });
    
    document.querySelector('.file-upload-area').addEventListener('drop', function(e) {
        e.preventDefault();
        this.style.borderColor = 'var(--border-color)';
        this.style.backgroundColor = 'transparent';
    });
    
    // Error handling
    document.getElementById('close-error')?.addEventListener('click', () => {
        document.getElementById('error-container').style.display = 'none';
    });
});

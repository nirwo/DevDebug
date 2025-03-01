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
    
    function displayResults(analysis) {
        // Update result elements with analysis data
        resultTechnology.textContent = analysis.technology;
        resultErrorType.textContent = analysis.error_type;
        
        // Set severity class
        resultSeverity.textContent = analysis.severity;
        resultSeverity.className = 'summary-value severity ' + analysis.severity;
        
        // Set error message
        resultErrorMessage.textContent = analysis.error_message || 'No specific error message detected';
        
        // Set context
        if (analysis.context && analysis.context.length > 0) {
            resultContext.textContent = analysis.context.join('\n');
        } else {
            resultContext.textContent = 'No context available';
        }
        
        // Set root causes
        resultRootCauses.innerHTML = '';
        if (analysis.root_causes && analysis.root_causes.length > 0) {
            analysis.root_causes.forEach(cause => {
                const li = document.createElement('li');
                li.textContent = cause;
                resultRootCauses.appendChild(li);
            });
        } else {
            const li = document.createElement('li');
            li.textContent = 'No root causes identified';
            resultRootCauses.appendChild(li);
        }
    }
    
    function displaySolutions(solutions) {
        solutionsList.innerHTML = '';
        
        if (!solutions || solutions.length === 0) {
            const noSolutions = document.createElement('div');
            noSolutions.className = 'no-solutions';
            noSolutions.innerHTML = `
                <i class="fas fa-search"></i>
                <p>No solutions found. The system is still learning about this type of error.</p>
            `;
            solutionsList.appendChild(noSolutions);
            return;
        }
        
        solutions.forEach(solution => {
            // Clone the template
            const solutionCard = document.importNode(solutionTemplate.content, true);
            
            // Update content
            solutionCard.querySelector('.solution-title').textContent = 
                `Solution for ${solution.error_type} error`;
            
            solutionCard.querySelector('.rate-value').textContent = 
                `${Math.round(solution.success_rate * 100)}%`;
            
            solutionCard.querySelector('.solution-description').textContent = solution.solution;
            
            // Add event listeners
            const copyBtn = solutionCard.querySelector('.solution-copy');
            copyBtn.addEventListener('click', () => {
                navigator.clipboard.writeText(solution.solution)
                    .then(() => {
                        copyBtn.innerHTML = '<i class="fas fa-check"></i> Copied';
                        setTimeout(() => {
                            copyBtn.innerHTML = '<i class="fas fa-copy"></i> Copy';
                        }, 2000);
                    });
            });
            
            const applyBtn = solutionCard.querySelector('.solution-apply');
            applyBtn.addEventListener('click', () => {
                // Mark this solution as selected
                selectedSolution = solution;
                
                // Update button text
                applyBtn.innerHTML = '<i class="fas fa-check-double"></i> Applied';
                applyBtn.disabled = true;
                
                // Show feedback options
                feedbackForm.classList.add('active');
            });
            
            // Add to the list
            solutionsList.appendChild(solutionCard);
        });
    }
    
    async function analyzeLog(logSource) {
        try {
            updateAnalysisStatus('Sending log for analysis...');
            
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(logSource)
            });
            
            if (!response.ok) {
                throw new Error(`Error: ${response.status}`);
            }
            
            updateAnalysisStatus('Processing results...');
            const data = await response.json();
            
            // Store the current analysis
            currentAnalysis = data.analysis;
            
            // Display results
            displayResults(data.analysis);
            
            // Prepare solutions
            displaySolutions(data.solutions);
            
            // Show results screen
            showScreen(stepResults);
            
        } catch (error) {
            console.error('Analysis error:', error);
            updateAnalysisStatus('Error analyzing log: ' + error.message);
            
            // Show a simple alert
            alert('Error analyzing log: ' + error.message);
            
            // Go back to log source screen
            showScreen(stepLogSource);
        }
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
        analyzeLog(logSource);
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
});

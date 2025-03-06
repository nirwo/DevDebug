import os
import sys

# Add the project root to Python path to make imports work
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from models.log_analyzer import LogAnalyzer
from models.web_scraper import WebScraper
from models.knowledge_base import KnowledgeBase

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Initialize components
log_analyzer = LogAnalyzer()
web_scraper = WebScraper()
knowledge_base = KnowledgeBase()

@app.route('/')
def index():
    """Render the main page with the wizard interface."""
    return render_template('index.html')

@app.route('/api/analyze', methods=['POST'])
def analyze_log():
    """Analyze log from a URL or direct input."""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
            
        log_url = data.get('log_url')
        log_content = data.get('log_content')
        
        # Set a processing timeout for long-running operations
        def process_with_timeout(timeout=15):
            """Run log processing with a timeout to prevent hanging"""
            import threading
            import time
            import ctypes
            import inspect
            
            result = {'success': False, 'error': 'Analysis timed out after {} seconds'.format(timeout)}
            
            # Function to forcibly terminate a thread
            def _terminate_thread(thread):
                """Terminates a python thread from another thread."""
                if not thread.is_alive():
                    return

                exc = ctypes.py_object(SystemExit)
                res = ctypes.pythonapi.PyThreadState_SetAsyncExc(
                    ctypes.c_long(thread.ident), exc)
                if res == 0:
                    raise ValueError("Invalid thread ID")
                elif res != 1:
                    # If more than one thread affected, undo
                    ctypes.pythonapi.PyThreadState_SetAsyncExc(
                        ctypes.c_long(thread.ident), ctypes.py_object(None))
                    raise SystemError("PyThreadState_SetAsyncExc failed")
            
            def process_log():
                nonlocal result
                try:
                    # Get log content if provided by URL
                    nonlocal log_content
                    if log_url and not log_content:
                        log_content = web_scraper.fetch_content(log_url)
                    
                    if not log_content:
                        result = {'success': False, 'error': 'No log content provided or could not fetch from URL'}
                        return
                    
                    # Check if the log content contains requests-related errors
                    if 'requests' in log_content.lower() and any(term in log_content.lower() for term in 
                                                                ['modulenotfounderror', 'importerror', 'no module named']):
                        # Return a specific solution for requests module issues
                        result = {
                            'success': True,
                            'analysis': {
                                'error_type': 'dependency',
                                'error_message': 'ModuleNotFoundError: No module named \'requests\'',
                                'technology': 'requests',
                                'severity': 'high',
                                'context': 'Missing Python requests module'
                            },
                            'solutions': [{
                                'title': 'Install the requests package',
                                'description': 'The requests package is missing. This is a popular HTTP library for Python.',
                                'steps': [
                                    'Run: pip install requests',
                                    'If using a virtual environment, make sure to activate it first: source venv/bin/activate',
                                    'If using requirements.txt, add requests to it and run: pip install -r requirements.txt'
                                ],
                                'code_snippet': '# Install the requests package\npip install requests\n\n# Or add to requirements.txt\n# requests==2.28.1',
                                'references': [
                                    {'title': 'Requests PyPI page', 'url': 'https://pypi.org/project/requests/'},
                                    {'title': 'Requests Documentation', 'url': 'https://requests.readthedocs.io/'}
                                ],
                                'success_rate': 0.98
                            }]
                        }
                        return
                    
                    # Initialize solutions array
                    solutions = []
                    
                    # Check for missing module errors - only once per session
                    if "ModuleNotFoundError: No module named" in log_content:
                        module_name = None
                        # Extract module name from error message
                        import re
                        module_match = re.search(r"No module named '([^']+)'", log_content)
                        if module_match:
                            module_name = module_match.group(1)
                            
                        if module_name:
                            # Check if we already have a solution for this module
                            solution_exists = False
                            existing_solutions = knowledge_base.get_solutions(error_type="dependency", context=[f"module {module_name}"])
                            
                            for solution in existing_solutions:
                                if module_name.lower() in solution.get('title', '').lower():
                                    solution_exists = True
                                    solutions.append(solution)
                                    break
                            
                            # Only add a new solution if one doesn't exist
                            if not solution_exists:
                                new_solution = {
                                    "title": f"Install missing module: {module_name}",
                                    "description": f"The error indicates that the Python module '{module_name}' is missing. This is a dependency that needs to be installed.",
                                    "steps": [
                                        f"Run: pip install {module_name}",
                                        f"If using a virtual environment, make sure to activate it first: source venv/bin/activate",
                                        f"If using requirements.txt, update it to include {module_name} and run: pip install -r requirements.txt"
                                    ],
                                    "code_snippet": f"# Install the missing module\npip install {module_name}\n\n# Or add to requirements.txt\n# {module_name}==latest_version",
                                    "references": [
                                        {"title": f"{module_name} PyPI page", "url": f"https://pypi.org/project/{module_name}/"},
                                        {"title": "Python dependency management", "url": "https://packaging.python.org/en/latest/tutorials/managing-dependencies/"}
                                    ]
                                }
                                solutions.append(new_solution)
                                
                                # Store this solution in the knowledge base for future use
                                knowledge_base.add_solution(
                                    error_type="dependency",
                                    context=[f"module {module_name}", "ModuleNotFoundError"],
                                    solution=new_solution
                                )
                            
                            # If we found a solution for a missing module, return early with just this solution
                            # This prevents the analysis from hanging when we already know what the problem is
                            if solutions:
                                result = {
                                    'success': True,
                                    'analysis': {
                                        'error_type': 'dependency',
                                        'error_message': f"ModuleNotFoundError: No module named '{module_name}'",
                                        'technology': 'Python',
                                        'severity': 'high',
                                        'context': f"Missing Python module: {module_name}"
                                    },
                                    'solutions': solutions
                                }
                                return
                    
                    # If we didn't return early with a module solution, do full analysis
                    # Analyze the log
                    analysis_result = log_analyzer.analyze(log_content)
                    
                    # Get solution suggestions
                    if not solutions:  # Only get more solutions if we don't already have module solutions
                        solutions.extend(knowledge_base.get_solutions(analysis_result['error_type'], analysis_result.get('context', [])))
                    
                    # Learn from this analysis
                    knowledge_base.learn(log_content, analysis_result, data.get('feedback'))
                    
                    # Add the solutions to the result
                    result = {
                        'success': True,
                        'analysis': analysis_result,
                        'solutions': solutions
                    }
                except Exception as e:
                    app.logger.error(f"Error in process_log: {str(e)}")
                    result = {'success': False, 'error': f'Analysis failed: {str(e)}'}
            
            # Start processing thread
            thread = threading.Thread(target=process_log)
            thread.daemon = True
            thread.start()
            
            # Wait with timeout
            start_time = time.time()
            while thread.is_alive() and (time.time() - start_time) < timeout:
                time.sleep(0.1)
            
            # If thread is still running after timeout, terminate it
            if thread.is_alive():
                _terminate_thread(thread)
                result = {'success': False, 'error': f'Analysis timed out after {timeout} seconds. The operation was terminated.'}
            
            return result
        
        # Run the processing with timeout
        processing_result = process_with_timeout()
        
        if not processing_result.get('success', False):
            return jsonify({'error': processing_result.get('error', 'Unknown error during analysis')}), 500
            
        return jsonify({
            'analysis': processing_result['analysis'],
            'solutions': processing_result['solutions']
        })
            
    except Exception as e:
        app.logger.error(f"Error analyzing log: {str(e)}")
        return jsonify({'error': f'Analysis failed: {str(e)}'}), 500

@app.route('/api/learn', methods=['POST'])
def learn():
    """Endpoint for the system to learn from user feedback."""
    data = request.json
    if not data:
        return jsonify({'success': False, 'error': 'No JSON data provided'}), 400
        
    # Log the incoming feedback data for debugging
    app.logger.info(f"Received feedback data: {data}")
    
    # Extract solution data for structured learning
    solution_data = None
    if data.get('solution_applied'):
        solution_data = {
            'title': 'User solution for ' + (data.get('analysis', {}).get('error_type', 'unknown error')),
            'description': data.get('feedback', 'No description provided'),
            'steps': [data.get('solution_applied', 'No steps provided')],
            'code_snippet': data.get('solution_applied', '# No code provided')
        }
    
    # Add structured solution if available
    if solution_data and data.get('solution_worked', False):
        error_type = data.get('analysis', {}).get('error_type', 'unknown')
        context = data.get('analysis', {}).get('context', [])
        knowledge_base.add_solution(error_type, context, solution_data)
        app.logger.info(f"Added new solution from feedback: {solution_data['title']}")
    
    # Also learn from unstructured feedback
    success = knowledge_base.learn(
        data.get('log_content'),
        data.get('analysis'),
        data.get('feedback'),
        data.get('solution_applied'),
        data.get('solution_worked')
    )
    
    return jsonify({'success': success})

@app.route('/api/scrape', methods=['POST'])
def scrape():
    """Endpoint to trigger web scraping for learning."""
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'No URL provided'}), 400
    
    # Scrape the content
    content = web_scraper.fetch_content(url)
    
    # Extract knowledge
    knowledge = web_scraper.extract_knowledge(content, url)
    
    # Store in knowledge base
    if knowledge:
        knowledge_base.add_knowledge(knowledge)
        return jsonify({'success': True, 'knowledge_count': len(knowledge)})
    
    return jsonify({'success': False, 'error': 'No knowledge extracted'})

@app.route('/api/train', methods=['POST'])
def train_model():
    """Endpoint to train the model by scraping common error documentation."""
    try:
        total_items = 0
        
        # Scrape documentation sites for common errors
        for url in web_scraper.error_doc_sites:
            try:
                content = web_scraper.fetch_content(url)
                if content:
                    knowledge = web_scraper.extract_knowledge(content, url)
                    if knowledge:
                        count = knowledge_base.add_knowledge(knowledge)
                        total_items += count
                        app.logger.info(f"Added {count} items from {url}")
            except Exception as e:
                app.logger.error(f"Error scraping {url}: {str(e)}")
        
        # Add custom solutions for common errors
        add_custom_solutions()
        
        return jsonify({
            'success': True, 
            'message': f'Training completed. Added {total_items} knowledge items.'
        })
    except Exception as e:
        app.logger.error(f"Error during training: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/knowledge/export', methods=['GET'])
def export_knowledge_base():
    """Export the entire knowledge base as JSON"""
    try:
        # Get the knowledge base data
        kb_data = knowledge_base.export_data()
        return jsonify(kb_data)
    except Exception as e:
        app.logger.error(f"Error exporting knowledge base: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/knowledge/import', methods=['POST'])
def import_knowledge_base():
    """Import knowledge base data from JSON"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        # Import the knowledge base data
        result = knowledge_base.import_data(data)
        return jsonify({"success": True, "message": f"Imported {result} solutions successfully"})
    except Exception as e:
        app.logger.error(f"Error importing knowledge base: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

# Dashboard API endpoints
@app.route('/api/dashboard/summary', methods=['GET'])
def dashboard_summary():
    """Get summary statistics for the dashboard"""
    try:
        # In a real implementation, this would query a database or analytics service
        # For this demo, return mock data
        return jsonify({
            "total_errors": 24,
            "critical_errors": 5,
            "warning_errors": 12,
            "resolved_errors": 7,
            "trends": {
                "dates": ["2025-03-01", "2025-03-02", "2025-03-03", "2025-03-04", "2025-03-05", "2025-03-06", "2025-03-07"],
                "critical": [1, 0, 2, 0, 1, 1, 0],
                "error": [2, 1, 3, 2, 1, 2, 1],
                "warning": [1, 2, 3, 1, 3, 1, 1]
            }
        })
    except Exception as e:
        app.logger.error(f"Error getting dashboard summary: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/errors', methods=['GET'])
def get_errors():
    """Get list of errors with optional filtering"""
    try:
        # Get filter parameters
        severity = request.args.get('severity', 'all')
        status = request.args.get('status', 'all')
        search = request.args.get('search', '')
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        
        # In a real implementation, these filters would be applied to a database query
        # For this demo, return mock data
        all_errors = [
            {
                "id": "ERR-1001",
                "timestamp": "2025-03-06 08:32:15",
                "type": "DatabaseError",
                "message": "Connection timeout: failed to connect to database after 30s",
                "severity": "critical",
                "status": "new"
            },
            {
                "id": "ERR-1002",
                "timestamp": "2025-03-06 09:14:22",
                "type": "MemoryError",
                "message": "Out of memory: Killed process 12345 (node)",
                "severity": "error",
                "status": "investigating"
            },
            {
                "id": "ERR-1003",
                "timestamp": "2025-03-06 10:05:51",
                "type": "NetworkError",
                "message": "Unable to connect to external API: Connection refused",
                "severity": "warning",
                "status": "resolved"
            },
            {
                "id": "ERR-1004",
                "timestamp": "2025-03-05 14:32:10",
                "type": "SyntaxError",
                "message": "Unexpected token in JSON at position 43",
                "severity": "error",
                "status": "new"
            },
            {
                "id": "ERR-1005",
                "timestamp": "2025-03-05 16:45:33",
                "type": "AuthenticationError",
                "message": "Invalid credentials: token expired",
                "severity": "critical",
                "status": "investigating"
            },
            {
                "id": "ERR-1006",
                "timestamp": "2025-03-04 11:23:05",
                "type": "ValidationError",
                "message": "Required field \"user_id\" is missing",
                "severity": "warning",
                "status": "resolved"
            },
            {
                "id": "ERR-1007",
                "timestamp": "2025-03-04 09:17:40",
                "type": "ConfigurationError",
                "message": "Invalid environment variable: REDIS_URL not defined",
                "severity": "error",
                "status": "resolved"
            },
            {
                "id": "ERR-1008",
                "timestamp": "2025-03-03 17:56:12",
                "type": "PermissionError",
                "message": "Access denied: user lacks required permission \"admin:write\"",
                "severity": "critical",
                "status": "new"
            }
        ]
        
        # Apply filters
        filtered_errors = all_errors
        
        if severity != 'all':
            filtered_errors = [e for e in filtered_errors if e['severity'] == severity]
            
        if status != 'all':
            filtered_errors = [e for e in filtered_errors if e['status'] == status]
            
        if search:
            search = search.lower()
            filtered_errors = [e for e in filtered_errors if
                              search in e['id'].lower() or
                              search in e['type'].lower() or
                              search in e['message'].lower()]
        
        # Calculate pagination
        total = len(filtered_errors)
        total_pages = max(1, (total + limit - 1) // limit)
        page = min(page, total_pages)
        
        # Get the current page data
        start = (page - 1) * limit
        end = min(start + limit, total)
        current_page_data = filtered_errors[start:end]
        
        return jsonify({
            "errors": current_page_data,
            "pagination": {
                "page": page,
                "limit": limit,
                "total": total,
                "total_pages": total_pages
            }
        })
    except Exception as e:
        app.logger.error(f"Error getting errors: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/errors/<error_id>', methods=['GET'])
def get_error_detail(error_id):
    """Get detailed information about a specific error"""
    try:
        # In a real implementation, this would query a database for the specific error
        # For this demo, we'll generate mock data based on the error ID
        
        # Common error message templates by type
        error_templates = {
            "DatabaseError": {
                "message": "Connection timeout: failed to connect to database after 30s",
                "context": "2025-03-06 08:32:10.123 INFO  [pool-2-thread-1] Attempting to connect to database at db-prod-01.example.com:5432\n2025-03-06 08:32:15.234 WARN  [pool-2-thread-1] Database connection attempt 1 failed: timeout\n2025-03-06 08:32:20.345 WARN  [pool-2-thread-1] Database connection attempt 2 failed: timeout\n2025-03-06 08:32:25.456 WARN  [pool-2-thread-1] Database connection attempt 3 failed: timeout\n2025-03-06 08:32:30.567 ERROR [pool-2-thread-1] Connection timeout: failed to connect to database after 30s\n2025-03-06 08:32:30.678 ERROR [pool-2-thread-1] Application startup failed\n2025-03-06 08:32:30.789 ERROR [main] java.sql.SQLException: Connection timed out\n    at com.example.db.ConnectionManager.getConnection(ConnectionManager.java:142)\n    at com.example.service.DatabaseService.initialize(DatabaseService.java:58)\n    at com.example.Application.start(Application.java:87)\n    at com.example.Application.main(Application.java:31)",
                "technology": "PostgreSQL",
                "root_causes": [
                    {"probability": 0.85, "cause": "Database server is unreachable due to network connectivity issues"},
                    {"probability": 0.65, "cause": "Database service not running on the target machine"},
                    {"probability": 0.45, "cause": "Incorrect connection credentials in configuration"},
                    {"probability": 0.25, "cause": "Database under heavy load and not responding to new connections"}
                ],
                "solutions": [
                    {
                        "title": "Check Network Connectivity",
                        "description": "Verify network connectivity between the application server and database server.",
                        "steps": [
                            "Check if database server is reachable",
                            "Verify the database port is open",
                            "Check firewall rules"
                        ],
                        "code_snippet": "# Check if database server is reachable\nping db-prod-01.example.com\n\n# Verify the database port is open\ntelnet db-prod-01.example.com 5432\n\n# Check firewall rules\nsudo iptables -L | grep 5432",
                        "match_score": 0.98
                    },
                    {
                        "title": "Verify Database Service Status",
                        "description": "Check if the database service is running properly.",
                        "steps": [
                            "Check service status",
                            "Review database logs",
                            "Restart the service if needed"
                        ],
                        "code_snippet": "# For PostgreSQL on Linux\nsudo systemctl status postgresql\n\n# Check PostgreSQL logs\nsudo tail -n 100 /var/log/postgresql/postgresql-14-main.log",
                        "match_score": 0.85
                    }
                ]
            },
            "MemoryError": {
                "message": "Out of memory: Killed process 12345 (node)",
                "context": "2025-03-06 09:14:15.452 INFO  [app] Server running with 4GB allocated memory\n2025-03-06 09:14:18.734 INFO  [app] Processing large data batch\n2025-03-06 09:14:20.128 WARN  [app] Memory usage at 85% (3.4GB/4GB)\n2025-03-06 09:14:21.562 WARN  [app] Memory usage at 95% (3.8GB/4GB)\n2025-03-06 09:14:22.103 ERROR [app] Out of memory: Killed process 12345 (node)\n2025-03-06 09:14:22.234 ERROR [system] Process terminated with signal: SIGKILL\n2025-03-06 09:14:22.456 ERROR [system] Core dump written to /var/crash/core.12345",
                "technology": "Node.js",
                "root_causes": [
                    {"probability": 0.92, "cause": "Application is consuming too much memory"},
                    {"probability": 0.78, "cause": "Memory leak in the application code"},
                    {"probability": 0.65, "cause": "Insufficient system resources allocated"},
                    {"probability": 0.40, "cause": "Large dataset being processed without streaming"}
                ],
                "solutions": [
                    {
                        "title": "Increase Node.js Memory Limit",
                        "description": "Adjust the memory limit for the Node.js process.",
                        "steps": [
                            "Set the max-old-space-size option",
                            "Update service configuration",
                            "Monitor memory usage"
                        ],
                        "code_snippet": "# Run Node.js with increased memory limit\nnode --max-old-space-size=8192 app.js\n\n# In package.json script\n\"start\": \"node --max-old-space-size=8192 app.js\"",
                        "match_score": 0.95
                    },
                    {
                        "title": "Optimize Memory Usage",
                        "description": "Implement memory optimization techniques in your code.",
                        "steps": [
                            "Use streams for large data processing",
                            "Implement pagination for large datasets",
                            "Free unused resources",
                            "Fix memory leaks"
                        ],
                        "code_snippet": "// Use streams instead of loading entire files\nconst fs = require('fs');\nfs.createReadStream('large-file.csv')\n  .pipe(csv.parse())\n  .pipe(transform)\n  .pipe(process.stdout);",
                        "match_score": 0.88
                    }
                ]
            }
        }
        
        # Parse the error ID to extract type
        parts = error_id.split('-')
        error_num = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
        
        # Determine error type and severity based on ID
        error_type = "DatabaseError" if error_num % 3 == 1 else "MemoryError" if error_num % 3 == 2 else "NetworkError"
        severity = "critical" if error_num % 5 == 0 else "error" if error_num % 5 == 1 else "warning"
        status = "new" if error_num % 3 == 0 else "investigating" if error_num % 3 == 1 else "resolved"
        
        # Get template based on type
        template = error_templates.get(error_type, error_templates.get("DatabaseError"))
        
        # Generate timestamps for metrics
        from datetime import datetime, timedelta
        today = datetime.now()
        timestamps = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(10, -1, -1)]
        
        # Generate random occurrence counts
        import random
        occurrences = [random.randint(0, 5) for _ in range(11)]
        
        # Generate history events
        history = []
        if error_num % 3 != 2:  # Not resolved
            # Error occurred
            error_time = today - timedelta(hours=random.randint(1, 24))
            history.append({
                "timestamp": error_time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "Error Occurred",
                "details": template["message"],
                "severity": severity
            })
            
            # Error detected
            detect_time = error_time + timedelta(minutes=random.randint(1, 5))
            history.append({
                "timestamp": detect_time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "Error Detected",
                "details": "Monitoring system alerted DevOps team"
            })
            
            # Status changed to investigating
            if error_num % 3 == 1:  # Investigating
                investigate_time = detect_time + timedelta(minutes=random.randint(3, 10))
                history.append({
                    "timestamp": investigate_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "event": "Status Changed",
                    "details": "Status changed from New to Investigating\nAssigned to: John Doe"
                })
        else:  # Resolved
            # Error occurred
            error_time = today - timedelta(days=random.randint(1, 3))
            history.append({
                "timestamp": error_time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "Error Occurred",
                "details": template["message"],
                "severity": severity
            })
            
            # Error detected
            detect_time = error_time + timedelta(minutes=random.randint(1, 5))
            history.append({
                "timestamp": detect_time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "Error Detected",
                "details": "Monitoring system alerted DevOps team"
            })
            
            # Status changed to investigating
            investigate_time = detect_time + timedelta(minutes=random.randint(3, 10))
            history.append({
                "timestamp": investigate_time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "Status Changed",
                "details": "Status changed from New to Investigating\nAssigned to: John Doe"
            })
            
            # Solution applied
            solution_time = investigate_time + timedelta(minutes=random.randint(5, 15))
            solution = template["solutions"][0]
            history.append({
                "timestamp": solution_time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "Solution Applied",
                "details": f"Solution \"{solution['title']}\" applied"
            })
            
            # Resolved
            resolved_time = solution_time + timedelta(minutes=random.randint(5, 15))
            history.append({
                "timestamp": resolved_time.strftime("%Y-%m-%d %H:%M:%S"),
                "event": "Status Changed",
                "details": "Status changed from Investigating to Resolved"
            })
        
        # Return the error detail
        return jsonify({
            "id": error_id,
            "timestamp": (today - timedelta(hours=random.randint(1, 48))).strftime("%Y-%m-%d %H:%M:%S"),
            "type": error_type,
            "message": template["message"],
            "severity": severity,
            "status": status,
            "technology": template["technology"],
            "context": template["context"],
            "root_causes": template["root_causes"],
            "solutions": template["solutions"],
            "metrics": {
                "first_occurrence": (today - timedelta(days=random.randint(1, 5))).strftime("%Y-%m-%d %H:%M:%S"),
                "latest_occurrence": today.strftime("%Y-%m-%d %H:%M:%S"),
                "total_occurrences": sum(occurrences),
                "avg_recovery_time": f"{random.randint(10, 45)} min",
                "impact_score": round(random.uniform(1, 10), 1),
                "affected_users": random.randint(10, 500),
                "timeline": {
                    "dates": timestamps,
                    "counts": occurrences
                },
                "impact": {
                    "revenue_loss": f"${random.randint(500, 5000)}",
                    "sla_violations": random.randint(0, 5),
                    "user_sessions": random.randint(100, 2000)
                }
            },
            "history": history
        })
    except Exception as e:
        app.logger.error(f"Error getting error detail: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/errors/<error_id>', methods=['PUT'])
def update_error(error_id):
    """Update error status or assignment"""
    try:
        data = request.json
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
            
        # In a real implementation, this would update a database record
        # For this demo, just return success
        return jsonify({
            "success": True,
            "error_id": error_id,
            "message": f"Error {error_id} updated successfully",
            "updated_fields": list(data.keys())
        })
    except Exception as e:
        app.logger.error(f"Error updating error: {str(e)}")
        return jsonify({"success": False, "error": str(e)}), 500

def add_custom_solutions():
    """Add custom solutions for common errors."""
    # Requests module missing
    requests_solution = {
        'title': 'Install the requests package',
        'description': 'The error indicates that the Python requests module is missing. This HTTP library needs to be installed.',
        'steps': [
            'Run: pip install requests',
            'If using a virtual environment, activate it first: source venv/bin/activate',
            'Add requests to your requirements.txt file for dependency management'
        ],
        'code_snippet': '# Install the requests package\npip install requests\n\n# Or add to requirements.txt\nrequests==2.28.1',
        'references': [
            {'title': 'Requests Documentation', 'url': 'https://requests.readthedocs.io/'},
            {'title': 'PyPI Package', 'url': 'https://pypi.org/project/requests/'}
        ]
    }
    knowledge_base.add_solution('dependency', ['module requests', 'ModuleNotFoundError'], requests_solution)
    
    # Connection error
    connection_solution = {
        'title': 'Fix connection refused error',
        'description': 'Your application is unable to connect to a server or service. This could be due to incorrect URL, server down, or network issues.',
        'steps': [
            'Verify the URL or hostname is correct',
            'Check if the server is running and accessible',
            'Check firewall settings',
            'Verify network connectivity'
        ],
        'code_snippet': '# Add error handling for connection issues\ntry:\n    response = requests.get(url, timeout=10)\n    response.raise_for_status()\nexcept requests.ConnectionError:\n    print("Connection error - please verify the server is running")\nexcept requests.Timeout:\n    print("Request timed out - the server might be overloaded")',
        'references': [
            {'title': 'Requests Exception Handling', 'url': 'https://requests.readthedocs.io/en/latest/user/quickstart/#errors-and-exceptions'}
        ]
    }
    knowledge_base.add_solution('network', ['connection refused', 'ConnectionError'], connection_solution)
    
    # Type error in Python
    type_error_solution = {
        'title': 'Fix TypeError or type conversion issue',
        'description': 'This error occurs when an operation or function is applied to an object of the wrong type.',
        'steps': [
            'Check the type of variables using type(variable)',
            'Convert variables to the correct type before operations',
            'Use appropriate type conversion functions like int(), str(), float()',
            'Add proper validation before type conversions'
        ],
        'code_snippet': '# Safely convert string to integer with validation\ndef safe_convert_to_int(value):\n    try:\n        return int(value)\n    except (TypeError, ValueError):\n        return None\n\n# Example usage\nuser_input = "123"\nnumber = safe_convert_to_int(user_input)\nif number is not None:\n    result = number * 2\nelse:\n    print("Invalid input, unable to convert to number")',
        'references': [
            {'title': 'Python Type Conversion', 'url': 'https://docs.python.org/3/library/functions.html#int'}
        ]
    }
    knowledge_base.add_solution('exception', ['TypeError', 'type', 'conversion'], type_error_solution)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))  # Changed from 5001 to 5002
    debug = os.environ.get('DEBUG', 'true').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)

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
            
            result = {'success': False, 'error': 'Analysis timed out after {} seconds'.format(timeout)}
            
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
                    
                    # Analyze the log
                    analysis_result = log_analyzer.analyze(log_content)
                    
                    # Get solution suggestions
                    solutions = knowledge_base.get_solutions(analysis_result['error_type'], analysis_result.get('context', []))
                    
                    # Learn from this analysis
                    knowledge_base.learn(log_content, analysis_result, data.get('feedback'))
                    
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5002))  # Changed from 5001 to 5002
    debug = os.environ.get('DEBUG', 'true').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)

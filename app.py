import os
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
    data = request.json
    log_url = data.get('log_url')
    log_content = data.get('log_content')
    
    if log_url:
        # Fetch log from URL
        log_content = web_scraper.fetch_content(log_url)
    
    if not log_content:
        return jsonify({'error': 'No log content provided'}), 400
    
    # Analyze the log
    analysis_result = log_analyzer.analyze(log_content)
    
    # Get solution suggestions
    solutions = knowledge_base.get_solutions(analysis_result['error_type'], analysis_result['context'])
    
    # Learn from this analysis
    knowledge_base.learn(log_content, analysis_result, data.get('feedback'))
    
    return jsonify({
        'analysis': analysis_result,
        'solutions': solutions
    })

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
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)

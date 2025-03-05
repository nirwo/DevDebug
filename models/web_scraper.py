import requests
from bs4 import BeautifulSoup
import re
import json
import os
from urllib.parse import urlparse
import logging

class WebScraper:
    """
    Handles web scraping to fetch log content from URLs and learn from technical documentation.
    """
    
    def __init__(self):
        """Initialize the web scraper with necessary configurations."""
        self.headers = {
            'User-Agent': 'DevOpsDebugWizard/1.0 (Learning Tool for DevOps Debugging)'
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.logger = logging.getLogger(__name__)
        
        # Load known documentation sites
        self.doc_sites = self._load_doc_sites()
    
    def _load_doc_sites(self):
        """Load known documentation sites from a JSON file."""
        sites_file = os.path.join(os.path.dirname(__file__), 'doc_sites.json')
        
        # Create default sites if file doesn't exist
        if not os.path.exists(sites_file):
            default_sites = {
                "kubernetes": [
                    "kubernetes.io/docs",
                    "k8s.io"
                ],
                "docker": [
                    "docs.docker.com"
                ],
                "python": [
                    "docs.python.org",
                    "flask.palletsprojects.com",
                    "django-docs.readthedocs.io"
                ],
                "java": [
                    "docs.oracle.com/javase",
                    "docs.spring.io"
                ],
                "database": [
                    "dev.mysql.com/doc",
                    "postgresql.org/docs",
                    "mongodb.com/docs"
                ],
                "cloud": [
                    "docs.aws.amazon.com",
                    "cloud.google.com/docs",
                    "docs.microsoft.com/azure"
                ]
            }
            
            with open(sites_file, 'w') as f:
                json.dump(default_sites, f, indent=2)
                
            return default_sites
        
        # Load existing sites
        with open(sites_file, 'r') as f:
            return json.load(f)
    
    def fetch_content(self, url):
        """Fetch content from a URL."""
        if not url:
            return None
            
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()  # Raise an exception for 4XX/5XX responses
            
            # Check if it's likely a text-based content
            content_type = response.headers.get('Content-Type', '').lower()
            if 'text' in content_type or 'json' in content_type or 'xml' in content_type:
                return response.text
                
            # For binary content, log a warning and return a placeholder
            self.logger.warning(f"Binary content detected at {url}")
            return f"Binary content from {url} (could not parse as text)"
            
        except requests.RequestException as e:
            self.logger.error(f"Error fetching content from {url}: {str(e)}")
            return None
    
    def extract_knowledge(self, content, url):
        """
        Extract knowledge from content for learning.
        
        Args:
            content (str): The content to extract knowledge from
            url (str): The URL the content was fetched from
            
        Returns:
            list: Extracted knowledge items
        """
        # Skip if no content
        if not content:
            return []
        
        # Determine the type of content based on the URL
        domain = urlparse(url).netloc
        
        # Check if this is a documentation site
        content_type = self._identify_content_type(domain)
        
        if content_type == 'documentation':
            return self._extract_from_documentation(content, url)
        elif content_type == 'issue':
            return self._extract_from_issue(content, url)
        elif content_type == 'stackoverflow':
            return self._extract_from_stackoverflow(content, url)
        else:
            # Generic extraction
            return self._extract_generic(content, url)
    
    def _identify_content_type(self, domain):
        """Identify the type of content based on the domain."""
        if 'stackoverflow.com' in domain:
            return 'stackoverflow'
        
        if 'github.com' in domain or 'gitlab.com' in domain:
            return 'issue'
        
        # Check if it's a known documentation site
        for tech, sites in self.doc_sites.items():
            if any(site in domain for site in sites):
                return 'documentation'
        
        return 'generic'
    
    def _extract_log_from_html(self, html_content, url):
        """Extract log content from HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Look for common log containers
        log_containers = soup.select('pre, code, .log, .console, .terminal')
        
        if log_containers:
            # Join all log container contents
            return '\n'.join(container.get_text() for container in log_containers)
        
        # Check if this is a GitHub issue or similar platform
        if 'github.com' in url or 'gitlab.com' in url:
            # Look for issue description and comments
            issue_content = []
            
            # Issue description
            description = soup.select_one('.comment-body, .markdown-body')
            if description:
                issue_content.append(description.get_text())
            
            # Comments
            comments = soup.select('.comment-body, .markdown-body')
            for comment in comments:
                issue_content.append(comment.get_text())
            
            return '\n'.join(issue_content)
        
        # If no specific log containers found, return the body text
        body = soup.body
        if body:
            return body.get_text()
        
        return html_content
    
    def _extract_from_documentation(self, content, url):
        """Extract knowledge from documentation."""
        knowledge = []
        
        # Extract headings and their content
        soup = BeautifulSoup(content, 'html.parser')
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])
        
        for heading in headings:
            heading_text = heading.get_text().strip()
            
            # Skip if heading is too generic
            if len(heading_text.split()) <= 2:
                continue
            
            # Get the content under this heading
            content_elements = []
            element = heading.next_sibling
            
            while element and element.name not in ['h1', 'h2', 'h3', 'h4']:
                if element.name in ['p', 'pre', 'code', 'ul', 'ol']:
                    content_elements.append(element.get_text().strip())
                element = element.next_sibling
            
            if content_elements:
                knowledge.append({
                    'type': 'documentation',
                    'title': heading_text,
                    'content': '\n'.join(content_elements),
                    'source': url
                })
        
        return knowledge
    
    def _extract_from_issue(self, content, url):
        """Extract knowledge from issue trackers."""
        # Look for error patterns and solutions
        error_pattern = r'(?:error|exception|failed|failure)[\s\:]+([\w\s\.\-]+)'
        solution_pattern = r'(?:fix|solve|resolve|solution)[\s\:]+([\w\s\.\-]+)'
        
        errors = re.findall(error_pattern, content, re.IGNORECASE)
        solutions = re.findall(solution_pattern, content, re.IGNORECASE)
        
        knowledge = []
        
        # Match errors with solutions
        for i, error in enumerate(errors):
            if i < len(solutions):
                knowledge.append({
                    'type': 'issue',
                    'error': error.strip(),
                    'solution': solutions[i].strip(),
                    'source': url
                })
            else:
                knowledge.append({
                    'type': 'issue',
                    'error': error.strip(),
                    'source': url
                })
        
        return knowledge
    
    def _extract_from_stackoverflow(self, content, url):
        """Extract knowledge from Stack Overflow."""
        soup = BeautifulSoup(content, 'html.parser')
        
        knowledge = []
        
        # Get the question
        question_element = soup.select_one('.question-hyperlink, .question-title h1')
        if question_element:
            question = question_element.get_text().strip()
            
            # Get the accepted answer
            accepted_answer = soup.select_one('.accepted-answer .post-text, .accepted-answer .s-prose')
            
            if accepted_answer:
                knowledge.append({
                    'type': 'stackoverflow',
                    'question': question,
                    'answer': accepted_answer.get_text().strip(),
                    'source': url
                })
            else:
                # Get the top answer if no accepted answer
                top_answer = soup.select_one('.answer .post-text, .answer .s-prose')
                if top_answer:
                    knowledge.append({
                        'type': 'stackoverflow',
                        'question': question,
                        'answer': top_answer.get_text().strip(),
                        'source': url
                    })
        
        return knowledge
    
    def _extract_generic(self, content, url):
        """Extract knowledge from generic content."""
        # Look for patterns that might indicate useful information
        knowledge = []
        
        # Look for error-solution pairs
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if re.search(r'(?:error|exception|failed|failure)', line, re.IGNORECASE):
                # Look for solution in the next few lines
                for j in range(i+1, min(i+10, len(lines))):
                    if re.search(r'(?:fix|solve|resolve|solution)', lines[j], re.IGNORECASE):
                        knowledge.append({
                            'type': 'generic',
                            'error': line.strip(),
                            'solution': lines[j].strip(),
                            'source': url
                        })
                        break
        
        return knowledge

import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import os
import json
from collections import Counter

class LogAnalyzer:
    """
    Analyzes log files to identify errors, their context, and potential solutions.
    Uses NLP and pattern matching to extract meaningful information from logs.
    """
    
    def __init__(self):
        """Initialize the log analyzer with necessary resources."""
        # Download NLTK resources if not already present
        try:
            nltk.data.find('tokenizers/punkt')
            nltk.data.find('corpora/stopwords')
        except LookupError:
            nltk.download('punkt')
            nltk.download('stopwords')
        
        # Load error patterns
        self.error_patterns = self._load_error_patterns()
        self.stop_words = set(stopwords.words('english'))
        
    def _load_error_patterns(self):
        """Load known error patterns from a JSON file."""
        patterns_file = os.path.join(os.path.dirname(__file__), 'error_patterns.json')
        
        # Create default patterns if file doesn't exist
        if not os.path.exists(patterns_file):
            default_patterns = {
                "exception": r"(?i)exception|error|failure|failed|traceback",
                "timeout": r"(?i)timeout|timed out|connection refused",
                "memory": r"(?i)out of memory|memory (error|exceeded|limit)",
                "permission": r"(?i)permission denied|access denied|unauthorized",
                "syntax": r"(?i)syntax error|parse error|invalid syntax",
                "dependency": r"(?i)module not found|import error|cannot find|not installed",
                "network": r"(?i)network (error|unreachable)|connection (refused|reset|error)"
            }
            
            with open(patterns_file, 'w') as f:
                json.dump(default_patterns, f, indent=2)
                
            return default_patterns
        
        # Load existing patterns
        with open(patterns_file, 'r') as f:
            return json.load(f)
    
    def analyze(self, log_content):
        """
        Analyze the log content to identify errors and their context.
        
        Args:
            log_content (str): The content of the log to analyze
            
        Returns:
            dict: Analysis results including error type, context, and severity
        """
        # Identify the technology/framework
        technology = self._identify_technology(log_content)
        
        # Extract error information
        error_type, error_message = self._extract_error(log_content)
        
        # Get context around the error
        context = self._extract_context(log_content, error_message)
        
        # Determine severity
        severity = self._determine_severity(error_type, error_message, context)
        
        # Extract relevant code snippets if present
        code_snippets = self._extract_code_snippets(log_content)
        
        # Identify potential root causes
        root_causes = self._identify_root_causes(error_type, error_message, context, technology)
        
        return {
            'technology': technology,
            'error_type': error_type,
            'error_message': error_message,
            'context': context,
            'severity': severity,
            'code_snippets': code_snippets,
            'root_causes': root_causes
        }
    
    def _identify_technology(self, log_content):
        """Identify the technology or framework from the log content."""
        tech_indicators = {
            'java': ['java.', 'springframework', 'jakarta', 'javax.'],
            'python': ['traceback', 'File "', 'ImportError', 'ModuleNotFoundError'],
            'javascript': ['TypeError', 'ReferenceError', 'node_modules', 'npm', 'yarn'],
            'docker': ['docker', 'container', 'image', 'Dockerfile'],
            'kubernetes': ['kubectl', 'pod', 'deployment', 'k8s', 'namespace'],
            'database': ['SQL', 'query', 'database', 'mysql', 'postgres', 'mongodb'],
            'web': ['http', 'https', 'status code', 'request', 'response']
        }
        
        tech_counts = {tech: 0 for tech in tech_indicators}
        
        for tech, indicators in tech_indicators.items():
            for indicator in indicators:
                if re.search(r'\b' + re.escape(indicator) + r'\b', log_content, re.IGNORECASE):
                    tech_counts[tech] += 1
        
        # Get the technology with the highest count
        if any(tech_counts.values()):
            return max(tech_counts.items(), key=lambda x: x[1])[0]
        
        return 'unknown'
    
    def _extract_error(self, log_content):
        """Extract the error type and message from the log content."""
        for error_type, pattern in self.error_patterns.items():
            match = re.search(pattern, log_content)
            if match:
                # Try to extract the full error message
                line_with_error = next((line for line in log_content.split('\n') 
                                       if re.search(pattern, line)), '')
                
                return error_type, line_with_error.strip()
        
        return 'unknown', 'No specific error pattern detected'
    
    def _extract_context(self, log_content, error_message):
        """Extract the context around the error message."""
        if not error_message or error_message not in log_content:
            return []
        
        lines = log_content.split('\n')
        
        # Find the line with the error message
        error_line_idx = next((i for i, line in enumerate(lines) 
                              if error_message in line), -1)
        
        if error_line_idx == -1:
            return []
        
        # Get context (5 lines before and after the error)
        start_idx = max(0, error_line_idx - 5)
        end_idx = min(len(lines), error_line_idx + 6)
        
        return lines[start_idx:end_idx]
    
    def _determine_severity(self, error_type, error_message, context):
        """Determine the severity of the error."""
        # Critical errors
        if any(term in error_message.lower() for term in 
               ['critical', 'fatal', 'crash', 'down', 'outage']):
            return 'critical'
        
        # High severity errors
        if error_type in ['exception', 'memory', 'network']:
            return 'high'
        
        # Medium severity errors
        if error_type in ['timeout', 'permission', 'dependency']:
            return 'medium'
        
        # Low severity errors
        if error_type in ['syntax']:
            return 'low'
        
        # Default
        return 'medium'
    
    def _extract_code_snippets(self, log_content):
        """Extract code snippets from the log content."""
        # Look for code blocks that might be in the log
        code_blocks = re.findall(r'```(?:\w+)?\n(.*?)\n```', log_content, re.DOTALL)
        
        # Look for file paths with line numbers (common in stack traces)
        file_lines = re.findall(r'(?:at |File ")([^"]+):(\d+)', log_content)
        
        return {
            'blocks': code_blocks,
            'file_references': file_lines
        }
    
    def _identify_root_causes(self, error_type, error_message, context, technology):
        """Identify potential root causes based on the error and context."""
        root_causes = []
        
        # Common root causes based on error type
        error_type_causes = {
            'exception': ['Bug in application code', 'Unexpected input'],
            'timeout': ['Network congestion', 'Service overload', 'Deadlock'],
            'memory': ['Memory leak', 'Insufficient resources', 'Large dataset'],
            'permission': ['Incorrect permissions', 'Security policy', 'Authentication issue'],
            'syntax': ['Code error', 'Incompatible versions'],
            'dependency': ['Missing library', 'Version conflict'],
            'network': ['Network failure', 'Firewall issue', 'DNS problem']
        }
        
        # Add general causes for the error type
        if error_type in error_type_causes:
            root_causes.extend(error_type_causes[error_type])
        
        # Look for specific indicators in the context
        context_text = ' '.join(context).lower()
        
        if 'disk' in context_text and 'space' in context_text:
            root_causes.append('Disk space issue')
            
        if 'cpu' in context_text and any(term in context_text for term in ['high', 'load', 'usage']):
            root_causes.append('High CPU usage')
            
        if 'connection' in context_text and 'refused' in context_text:
            root_causes.append('Service unavailable')
            
        if 'version' in context_text and any(term in context_text for term in ['mismatch', 'incompatible']):
            root_causes.append('Version incompatibility')
        
        # Technology-specific causes
        tech_causes = {
            'java': ['JVM issues', 'Garbage collection problems'],
            'python': ['GIL contention', 'Package conflicts'],
            'javascript': ['Async/callback issues', 'Browser compatibility'],
            'docker': ['Container resource limits', 'Image issues'],
            'kubernetes': ['Pod scheduling', 'Resource quotas'],
            'database': ['Query performance', 'Lock contention'],
            'web': ['CORS issues', 'API rate limits']
        }
        
        if technology in tech_causes:
            # Only add technology-specific causes if they seem relevant
            for cause in tech_causes[technology]:
                keywords = cause.lower().split()
                if any(keyword in context_text for keyword in keywords):
                    root_causes.append(cause)
        
        return root_causes[:5]  # Limit to top 5 most likely causes

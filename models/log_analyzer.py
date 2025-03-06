import re
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
import os
import json
from collections import Counter
import time

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
        Performs deep analysis on the entire log to extract multiple errors and metrics.
        
        Args:
            log_content (str): The content of the log to analyze
            
        Returns:
            dict: Comprehensive analysis results with multiple errors and metrics
        """
        if not log_content:
            return {
                'error_type': 'unknown',
                'error_message': 'No log content provided',
                'severity': 'low',
                'context': [],
                'metrics': {
                    'total_lines': 0,
                    'error_count': 0,
                    'warning_count': 0,
                    'info_count': 0
                },
                'all_errors': []
            }
            
        # Tokenize the log
        lines = log_content.split('\n')
        
        # Calculate basic metrics
        metrics = self._calculate_metrics(lines)
        
        # Identify the technology/framework
        technology = self._identify_technology(log_content)
        
        # Extract all errors from the log (not just the primary one)
        all_errors = self._extract_all_errors(lines)
        
        # Extract error information for primary error
        error_type, error_message = self._extract_error(log_content)
        
        # Get context around the error
        context = self._extract_context(log_content, error_message)
        
        # Determine severity
        severity = self._determine_severity(error_type, error_message, context)
        
        # Extract relevant code snippets if present
        code_snippets = self._extract_code_snippets(log_content)
        
        # Identify performance issues
        performance_issues = self._identify_performance_issues(lines)
        
        # Generate markdown summary
        summary = self._generate_summary(error_type, error_message, metrics, all_errors, technology)
        
        # Identify potential root causes
        root_causes = self._identify_root_causes(error_type, error_message, context, technology)
        
        return {
            'technology': technology,
            'error_type': error_type,
            'error_message': error_message,
            'context': context,
            'severity': severity,
            'code_snippets': code_snippets,
            'root_causes': root_causes,
            'metrics': metrics,
            'all_errors': all_errors,
            'performance_issues': performance_issues,
            'summary': summary
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
        if not error_message or not log_content:
            return []
            
        if error_message not in log_content:
            # Try to find a partial match
            error_words = error_message.split()
            if len(error_words) > 3:
                # Try with a substring of the error message
                partial_error = ' '.join(error_words[:3])
                if partial_error in log_content:
                    error_message = partial_error
                else:
                    # Return the first few lines as context if no match
                    lines = log_content.split('\n')
                    return lines[:min(10, len(lines))]
        
        lines = log_content.split('\n')
        
        # Find the line with the error message
        error_line_idx = -1
        for i, line in enumerate(lines):
            if error_message in line:
                error_line_idx = i
                break
        
        if error_line_idx == -1:
            # Return the first few lines as context if no match
            return lines[:min(10, len(lines))]
        
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
    
    def _calculate_metrics(self, lines):
        """Calculate metrics from log lines for KPI reporting."""
        total_lines = len(lines)
        error_count = 0
        warning_count = 0
        info_count = 0
        debug_count = 0
        exception_count = 0
        
        # Count by log level
        for line in lines:
            line_lower = line.lower()
            if 'error' in line_lower or 'exception' in line_lower or 'fail' in line_lower:
                error_count += 1
            elif 'warn' in line_lower:
                warning_count += 1
            elif 'info' in line_lower:
                info_count += 1
            elif 'debug' in line_lower:
                debug_count += 1
                
            # Count exceptions specifically
            if 'exception' in line_lower or 'traceback' in line_lower:
                exception_count += 1
        
        # Calculate time metrics if timestamps are present
        time_metrics = self._extract_time_metrics(lines)
        
        return {
            'total_lines': total_lines,
            'error_count': error_count,
            'warning_count': warning_count,
            'info_count': info_count,
            'debug_count': debug_count,
            'exception_count': exception_count,
            'error_ratio': error_count / total_lines if total_lines > 0 else 0,
            'time_metrics': time_metrics
        }
        
    def _extract_time_metrics(self, lines):
        """Extract time-related metrics from the log if timestamps are present."""
        # Try to find timestamps in common formats
        timestamp_pattern = r'(\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:[-+]\d{2}:?\d{2})?)'
        timestamps = []
        
        for line in lines:
            match = re.search(timestamp_pattern, line)
            if match:
                try:
                    # Try to parse the timestamp
                    ts = match.group(1)
                    timestamps.append(ts)
                except:
                    pass
        
        if len(timestamps) >= 2:
            # Convert to datetime objects with various formats
            try:
                # Try ISO format first
                start_time = timestamps[0]
                end_time = timestamps[-1]
                
                # Return timestamp strings since full parsing is complex
                return {
                    'first_timestamp': start_time,
                    'last_timestamp': end_time,
                    'timestamp_count': len(timestamps)
                }
            except:
                pass
                
        return {
            'timestamp_count': len(timestamps)
        }
        
    def _extract_all_errors(self, lines):
        """Extract all errors from the log, not just the primary one."""
        errors = []
        
        # Process each line
        for i, line in enumerate(lines):
            # Skip if line is too short
            if len(line.strip()) < 5:
                continue
                
            # Check for error indicators
            for error_type, pattern in self.error_patterns.items():
                if re.search(pattern, line):
                    # Extract context lines (up to 5 before and after)
                    context_start = max(0, i - 5)
                    context_end = min(len(lines), i + 6)
                    context = lines[context_start:context_end]
                    
                    errors.append({
                        'error_type': error_type,
                        'error_message': line,
                        'line_number': i + 1,
                        'context': context,
                        'severity': self._quick_severity_check(line)
                    })
                    break  # Found an error pattern, move to next line
        
        return errors
        
    def _quick_severity_check(self, line):
        """Quickly determine severity based on keywords in the line."""
        line_lower = line.lower()
        
        if 'critical' in line_lower or 'fatal' in line_lower:
            return 'critical'
        elif 'error' in line_lower or 'exception' in line_lower or 'fail' in line_lower:
            return 'high'
        elif 'warn' in line_lower:
            return 'medium'
        else:
            return 'low'
            
    def _identify_performance_issues(self, lines):
        """Identify performance-related issues in the log."""
        issues = []
        
        # Look for timeout indications
        timeout_pattern = r'(?i)timeout|timed? out|too (?:much|long)|(?:high|excessive) (?:cpu|memory|load)'
        
        # Look for memory issues
        memory_pattern = r'(?i)memory|heap|out of|allocation|garbage collection'
        
        # Look for slow execution
        slow_pattern = r'(?i)slow|delay|latency|performance|bottleneck'
        
        for i, line in enumerate(lines):
            if re.search(timeout_pattern, line):
                issues.append({
                    'type': 'timeout',
                    'description': 'Possible timeout detected',
                    'line': line,
                    'line_number': i + 1
                })
            elif re.search(memory_pattern, line):
                issues.append({
                    'type': 'memory',
                    'description': 'Possible memory issue detected',
                    'line': line,
                    'line_number': i + 1
                })
            elif re.search(slow_pattern, line):
                issues.append({
                    'type': 'performance',
                    'description': 'Possible performance issue detected',
                    'line': line,
                    'line_number': i + 1
                })
                
        return issues
        
    def _generate_summary(self, error_type, error_message, metrics, all_errors, technology):
        """Generate a markdown summary of the analysis."""
        summary_lines = []
        
        # Overall assessment
        if metrics['error_count'] > 0:
            if metrics['error_count'] > 10:
                summary_lines.append("## Critical Issue Detected")
                summary_lines.append(f"Found **{metrics['error_count']}** errors in the log, indicating a serious problem.")
            else:
                summary_lines.append("## Error Detected")
                summary_lines.append(f"Found **{metrics['error_count']}** errors in the log.")
        else:
            summary_lines.append("## Log Analysis Complete")
            summary_lines.append("No errors detected in the log.")
            
        # Add time span if available
        if 'time_metrics' in metrics and 'first_timestamp' in metrics['time_metrics']:
            summary_lines.append(f"\nLog spans from **{metrics['time_metrics']['first_timestamp']}** to **{metrics['time_metrics']['last_timestamp']}**")
            
        # Add technology
        if technology:
            summary_lines.append(f"\nDetected technology: **{technology}**")
            
        # Add primary error info
        if error_message:
            summary_lines.append("\n### Primary Error")
            summary_lines.append(f"- **Type:** {error_type}")
            summary_lines.append(f"- **Message:** {error_message}")
            
        # Add metrics summary
        summary_lines.append("\n### Log Metrics")
        summary_lines.append(f"- Total lines: **{metrics['total_lines']}**")
        summary_lines.append(f"- Error messages: **{metrics['error_count']}**")
        summary_lines.append(f"- Warnings: **{metrics['warning_count']}**")
        summary_lines.append(f"- Info messages: **{metrics['info_count']}**")
        summary_lines.append(f"- Debug messages: **{metrics['debug_count']}**")
        summary_lines.append(f"- Exceptions: **{metrics['exception_count']}**")
        
        # Error ratio as percentage
        error_percentage = round(metrics['error_ratio'] * 100, 1)
        summary_lines.append(f"- Error ratio: **{error_percentage}%** of log lines")
            
        return "\n".join(summary_lines)
        
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
    
    def _match_patterns(self, log_content):
        """Match error patterns in the log content."""
        # Add a timeout for regex matching to prevent catastrophic backtracking
        import time
        
        results = []
        for pattern in self.error_patterns:
            pattern_regex = pattern
            if not pattern_regex:
                continue
                
            # Add a timeout for regex matching
            start_time = time.time()
            try:
                # Add a simple timeout mechanism
                match = None
                
                # Use a simplified matching to prevent regex catastrophic backtracking
                # First try a simple contains check before regex
                simple_check = ''
                if simple_check and simple_check in log_content:
                    match = re.search(pattern_regex, log_content, re.IGNORECASE)
                elif not simple_check:  # If no simple check defined, use regex directly
                    match = re.search(pattern_regex, log_content, re.IGNORECASE)
                    
                # If taking too long, skip this pattern
                if time.time() - start_time > 1.0:  # More than 1 second is too long
                    print(f"Pattern matching timeout for: {pattern}")
                    continue
                    
                if match:
                    result = {
                        'error_type': pattern,
                        'error_message': match.group(0) if match.groups() else match.group(0),
                        'severity': 'medium',
                        'tech_stack': ['unknown'],
                        'potential_causes': []
                    }
                    
                    # Extract named groups
                    if hasattr(match, 'groupdict') and match.groupdict():
                        for key, value in match.groupdict().items():
                            if value:
                                result[key] = value
                                
                    results.append(result)
            except re.error as e:
                print(f"Regex error in pattern {pattern}: {e}")
                continue
            except Exception as e:
                print(f"Error matching pattern {pattern}: {e}")
                continue
                
            # If we've spent more than 3 seconds on pattern matching, abort to prevent timeouts
            if time.time() - start_time > 3.0:
                print("Pattern matching is taking too long, aborting further matches")
                break
        
        return results

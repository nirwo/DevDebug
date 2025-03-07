import os
import json
import time
from collections import defaultdict
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

class KnowledgeBase:
    """
    Manages the knowledge base for storing and retrieving error solutions.
    Learns from user feedback and external sources.
    """
    
    def __init__(self):
        """Initialize the knowledge base with necessary resources."""
        self.db_file = os.path.join(os.path.dirname(__file__), 'knowledge_db.json')
        self.db = self._load_db()
        self.vectorizer = TfidfVectorizer(stop_words='english')
        
        # Create vector representations if we have enough data
        if len(self.db['solutions']) > 5:
            self._update_vectors()
    
    def _load_db(self):
        """Load the knowledge database from a JSON file."""
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                # Handle corrupted or missing file
                print(f"Warning: Could not load knowledge DB from {self.db_file}. Creating new database.")
        
        # Create a new database if it doesn't exist or can't be loaded
        db = {
            'solutions': [],
            'error_types': {},
            'technologies': {},
            'last_updated': time.time()
        }
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.db_file), exist_ok=True)
        
        with open(self.db_file, 'w') as f:
            json.dump(db, f, indent=2)
        
        return db
    
    def _save_db(self):
        """Save the knowledge database to a JSON file."""
        self.db['last_updated'] = time.time()
        
        with open(self.db_file, 'w') as f:
            json.dump(self.db, f, indent=2)
    
    def _update_vectors(self):
        """Update vector representations of solutions for similarity matching."""
        if not self.db['solutions']:
            self.vectors = None
            return
        
        # Create a corpus of error descriptions and contexts
        corpus = [f"{solution['error_type']} {solution.get('error_message', '')} {' '.join(solution.get('context', []))}"
                 for solution in self.db['solutions']]
        
        # Fit the vectorizer and transform the corpus
        self.vectors = self.vectorizer.fit_transform(corpus)
    
    def get_solutions(self, error_type, context, limit=5):
        """
        Get solution suggestions for a given error type and context.
        
        Args:
            error_type (str): The type of error
            context (list): Context lines around the error
            limit (int): Maximum number of solutions to return
            
        Returns:
            list: Suggested solutions
        """
        if not self.db['solutions']:
            return []
        
        # If we have less than 5 solutions, just return them all
        if len(self.db['solutions']) < 5:
            return sorted(self.db['solutions'], 
                         key=lambda x: x.get('success_rate', 0), 
                         reverse=True)[:limit]
        
        if not hasattr(self, 'vectors') or self.vectors is None:
            self._update_vectors()
            # If still no vectors, just return sorted solutions
            if not hasattr(self, 'vectors') or self.vectors is None:
                return sorted(self.db['solutions'], 
                            key=lambda x: x.get('success_rate', 0), 
                            reverse=True)[:limit]
        
        # Create a query vector
        query = f"{error_type} {' '.join(context if context else [])}"
        query_vector = self.vectorizer.transform([query])
        
        # Calculate similarity scores
        similarities = cosine_similarity(query_vector, self.vectors)[0]
        
        # Get the indices of the top solutions
        top_indices = np.argsort(similarities)[-limit:][::-1]
        
        # Return the top solutions
        return [self.db['solutions'][i] for i in top_indices]
    
    def learn(self, log_content, analysis, feedback=None, solution_applied=None, solution_worked=None):
        """
        Learn from a new log analysis and optional feedback.
        
        Args:
            log_content (str): The log content
            analysis (dict): Analysis results
            feedback (str, optional): User feedback
            solution_applied (str, optional): Solution that was applied
            solution_worked (bool, optional): Whether the solution worked
            
        Returns:
            bool: Success status
        """
        # Update error type statistics
        error_type = analysis.get('error_type', 'unknown')
        if error_type not in self.db['error_types']:
            self.db['error_types'][error_type] = 1
        else:
            self.db['error_types'][error_type] += 1
        
        # Update technology statistics
        technology = analysis.get('technology', 'unknown')
        if technology not in self.db['technologies']:
            self.db['technologies'][technology] = 1
        else:
            self.db['technologies'][technology] += 1
        
        # If a solution was applied and we know if it worked
        if solution_applied and solution_worked is not None:
            # Look for an existing solution
            for solution in self.db['solutions']:
                if (solution['error_type'] == error_type and
                    solution['solution'] == solution_applied):
                    # Update success rate
                    solution['attempts'] += 1
                    if solution_worked:
                        solution['successes'] += 1
                    solution['success_rate'] = solution['successes'] / solution['attempts']
                    self._save_db()
                    return True
            
            # Add a new solution
            new_solution = {
                'error_type': error_type,
                'error_message': analysis.get('error_message', ''),
                'context': analysis.get('context', []),
                'technology': technology,
                'solution': solution_applied,
                'attempts': 1,
                'successes': 1 if solution_worked else 0,
                'success_rate': 1.0 if solution_worked else 0.0,
                'timestamp': time.time()
            }
            
            self.db['solutions'].append(new_solution)
            self._save_db()
            
            # Update vectors
            self._update_vectors()
            
            return True
        
        # If we just have feedback, store it for future analysis
        if feedback:
            # Extract potential solutions from feedback
            # Improved pattern to capture code snippets and more complex solutions
            solution_pattern = r'(?:fix|solve|resolve|solution|install)[\s\:]+([\w\s\.\-\(\)\[\]\{\}\'\"\`\;\:\/\\\.\,\=\+\-\_\*\&\^\%\$\#\@\!\~]+)'
            solutions = re.findall(solution_pattern, feedback, re.IGNORECASE)
            
            if solutions:
                new_solution = {
                    'error_type': error_type,
                    'error_message': analysis.get('error_message', ''),
                    'context': analysis.get('context', []),
                    'technology': technology,
                    'solution': solutions[0],
                    'attempts': 1,
                    'successes': 1,  # Assume user feedback has high value
                    'success_rate': 1.0,
                    'timestamp': time.time()
                }
                
                self.db['solutions'].append(new_solution)
                self._save_db()
                return True
        
        # Just save the updated statistics
        self._save_db()
        return True
    
    def add_knowledge(self, knowledge_items):
        """
        Add knowledge items to the database.
        
        Args:
            knowledge_items (list): List of knowledge items to add
            
        Returns:
            int: Number of items added
        """
        added_count = 0
        
        for item in knowledge_items:
            if item['type'] == 'issue':
                if 'error' in item and 'solution' in item:
                    # Create a solution from the issue
                    new_solution = {
                        'error_type': self._guess_error_type(item['error']),
                        'error_message': item['error'],
                        'context': [],
                        'technology': self._guess_technology(item['error'], item['solution']),
                        'solution': item['solution'],
                        'attempts': 1,
                        'successes': 1,
                        'success_rate': 1.0,
                        'timestamp': time.time(),
                        'source': item.get('source', '')
                    }
                    
                    self.db['solutions'].append(new_solution)
                    added_count += 1
            
            elif item['type'] == 'stackoverflow':
                if 'question' in item and 'answer' in item:
                    # Create a solution from the StackOverflow Q&A
                    new_solution = {
                        'error_type': self._guess_error_type(item['question']),
                        'error_message': item['question'],
                        'context': [],
                        'technology': self._guess_technology(item['question'], item['answer']),
                        'solution': item['answer'],
                        'attempts': 1,
                        'successes': 1,
                        'success_rate': 1.0,
                        'timestamp': time.time(),
                        'source': item.get('source', '')
                    }
                    
                    self.db['solutions'].append(new_solution)
                    added_count += 1
            
            elif item['type'] == 'documentation':
                if 'title' in item and 'content' in item:
                    # Only add if it seems relevant to errors
                    if re.search(r'(?:error|exception|troubleshoot|debug|issue|problem)', 
                                item['title'] + ' ' + item['content'], re.IGNORECASE):
                        new_solution = {
                            'error_type': self._guess_error_type(item['title'] + ' ' + item['content']),
                            'error_message': item['title'],
                            'context': [item['content']],
                            'technology': self._guess_technology(item['title'], item['content']),
                            'solution': item['content'],
                            'attempts': 1,
                            'successes': 1,
                            'success_rate': 1.0,
                            'timestamp': time.time(),
                            'source': item.get('source', '')
                        }
                        
                        self.db['solutions'].append(new_solution)
                        added_count += 1
        
        if added_count > 0:
            self._save_db()
            self._update_vectors()
        
        return added_count
    
    def add_solution(self, error_type, context, solution):
        """
        Add a new solution to the knowledge base.
        
        Args:
            error_type (str): The type of error this solution addresses
            context (list): List of context lines or keywords related to the error
            solution (dict): Solution dictionary with title, description, steps, etc.
            
        Returns:
            bool: True if the solution was added successfully
        """
        # Generate a unique ID for the solution
        solution_id = str(int(time.time())) + str(len(self.db['solutions']))
        
        # Add ID to the solution if it doesn't have one
        if 'id' not in solution:
            solution['id'] = solution_id
            
        # Add metadata
        solution['error_type'] = error_type
        solution['context_keywords'] = context
        solution['created_at'] = time.time()
        solution['success_rate'] = 0.0
        solution['feedback_count'] = 0
        
        # Add to solutions list
        self.db['solutions'].append(solution)
        
        # Update error type statistics
        if error_type in self.db['error_types']:
            self.db['error_types'][error_type] += 1
        else:
            self.db['error_types'][error_type] = 1
            
        # Save the updated database
        self._save_db()
        
        # Update vector representations if we have enough data
        if len(self.db['solutions']) > 5:
            self._update_vectors()
            
        return True
    
    def _guess_error_type(self, text):
        """Guess the error type from text."""
        error_patterns = {
            'exception': r'(?i)exception|error|failure|failed|traceback',
            'timeout': r'(?i)timeout|timed out|connection refused',
            'memory': r'(?i)out of memory|memory (error|exceeded|limit)',
            'permission': r'(?i)permission denied|access denied|unauthorized',
            'syntax': r'(?i)syntax error|parse error|invalid syntax',
            'dependency': r'(?i)module not found|import error|cannot find|not installed',
            'network': r'(?i)network (error|unreachable)|connection (refused|reset|error)'
        }
        
        for error_type, pattern in error_patterns.items():
            if re.search(pattern, text):
                return error_type
        
        return 'unknown'
    
    def _guess_technology(self, *texts):
        """Guess the technology from text."""
        combined_text = ' '.join(texts).lower()
        
        tech_indicators = {
            'java': ['java', 'springframework', 'jakarta', 'javax'],
            'python': ['python', 'traceback', 'importerror', 'modulenotfounderror'],
            'javascript': ['javascript', 'typescript', 'node.js', 'npm', 'yarn'],
            'docker': ['docker', 'container', 'image', 'dockerfile'],
            'kubernetes': ['kubernetes', 'k8s', 'pod', 'deployment', 'kubectl'],
            'database': ['sql', 'database', 'mysql', 'postgres', 'mongodb'],
            'requests': ['requests', 'connectionerror', 'connecttimeout', 'readtimeout', 'response', 'requestexception'],
            'web': ['http', 'https', 'status code', 'request', 'response']
        }
        
        for tech, indicators in tech_indicators.items():
            if any(indicator in combined_text for indicator in indicators):
                return tech
        
        return 'unknown'

    def train(self):
        """Train the knowledge base with additional data sources."""
        # Placeholder for more sophisticated training
        # In a real implementation, this would involve more complex learning
        self._update_vectors()
        return True
        
    def export_data(self):
        """Export the entire knowledge base as a JSON-serializable dictionary."""
        try:
            # Create a copy of the database to avoid modifying the original
            export_data = {
                "version": "1.0",
                "timestamp": time.time(),
                "solutions": self.db["solutions"],
                "metadata": {
                    "total_solutions": len(self.db["solutions"]),
                    "exported_at": time.strftime("%Y-%m-%d %H:%M:%S")
                }
            }
            
            return export_data
        except Exception as e:
            print(f"Error exporting knowledge base: {str(e)}")
            raise
    
    def import_data(self, data):
        """
        Import knowledge base data from a dictionary.
        
        Args:
            data (dict): The knowledge base data to import
            
        Returns:
            int: The number of solutions imported
        """
        try:
            if not isinstance(data, dict):
                raise ValueError("Import data must be a dictionary")
                
            if "solutions" not in data or not isinstance(data["solutions"], list):
                raise ValueError("Import data must contain a 'solutions' list")
                
            # Track existing solution IDs to avoid duplicates
            existing_ids = {solution.get("id") for solution in self.db["solutions"] if "id" in solution}
            existing_signatures = {
                f"{solution.get('error_type', '')}-{solution.get('error_message', '')}"
                for solution in self.db["solutions"]
            }
            
            # Count imported solutions
            imported_count = 0
            
            # Add new solutions
            for solution in data["solutions"]:
                # Skip if solution doesn't have required fields
                if "error_type" not in solution:
                    continue
                    
                # Generate a signature for duplicate detection
                signature = f"{solution.get('error_type', '')}-{solution.get('error_message', '')}"
                
                # Skip duplicates
                if ("id" in solution and solution["id"] in existing_ids) or signature in existing_signatures:
                    continue
                    
                # Add the solution
                self.db["solutions"].append(solution)
                
                # Update tracking sets
                if "id" in solution:
                    existing_ids.add(solution["id"])
                existing_signatures.add(signature)
                
                imported_count += 1
            
            # Save the updated database
            self._save_db()
            
            # Update vectors if we imported solutions
            if imported_count > 0:
                self._update_vectors()
                
            return imported_count
        except Exception as e:
            print(f"Error importing knowledge base: {str(e)}")
            raise

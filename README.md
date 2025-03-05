# DevOps Debug Wizard

A powerful online tool for DevOps and SRE teams to analyze and debug failures quickly and efficiently.

## Features

- **Log Analysis**: Process logs from URLs, pasted content, or uploaded files
- **Error Detection**: Identify error types, context, and severity
- **Root Cause Analysis**: Get potential root causes of issues
- **Solution Recommendations**: Receive suggestions based on historical data and user feedback
- **Self-Learning**: The system learns from each analysis to improve future recommendations
- **Web Scraping**: Autonomously scrapes knowledge from documentation and other sources

## Getting Started

### Prerequisites

- Python 3.7+
- pip

### Installation

1. Clone the repository:

   ```
   git clone https://github.com/yourusername/devops-debug-wizard.git
   cd devops-debug-wizard
   ```

2. Install dependencies:

   ```
   pip install -r requirements.txt
   ```

3. Copy the example environment file and configure your settings:

   ```
   cp .env.example .env
   ```

   Edit the `.env` file to set your preferences.

4. Run the application:
   ```
   python app.py
   ```

The application will be available at `http://localhost:5001` (or the port you specified in the .env file).

## Usage

1. Navigate to the web interface
2. Choose how to provide your log data:
   - Enter a URL to a log file
   - Paste log content directly
   - Upload a log file
3. Submit the log for analysis
4. Review the detailed error analysis and suggested solutions
5. Provide feedback on the solutions to help improve the system

## Development

### Project Structure

```
devops-debug-wizard/
├── app.py                # Main Flask application
├── models/               # Core logic modules
│   ├── log_analyzer.py   # Log analysis engine
│   ├── knowledge_base.py # Solution database and learning system
│   ├── web_scraper.py    # Web scraping capabilities
│   └── ...
├── static/               # Static assets
│   ├── css/              # Stylesheets
│   ├── js/               # JavaScript files
│   └── img/              # Images and icons
├── templates/            # HTML templates
│   └── index.html        # Main application template
├── data/                 # Data files
│   ├── error_patterns.json   # Error pattern definitions
│   └── doc_sites.json        # Documentation site references
└── requirements.txt      # Python dependencies
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

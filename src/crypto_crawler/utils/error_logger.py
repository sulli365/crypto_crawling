#!/usr/bin/env python
import os
import sys
from datetime import datetime
from typing import Optional

# Import the sanitize_text function from the crawler module
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from crypto_crawler.crawling.crawler import sanitize_text
except ImportError:
    # Fallback sanitize_text function in case of import issues
    def sanitize_text(text: str) -> str:
        """
        Sanitize text to handle encoding issues.
        Replace problematic Unicode characters with their ASCII equivalents or remove them.
        """
        # Common problematic character replacements
        replacements = {
            '\u2192': '->',  # → (right arrow)
            '\u2190': '<-',  # ← (left arrow)
            '\u2022': '*',   # • (bullet)
            '\u2018': "'",   # ' (left single quote)
            '\u2019': "'",   # ' (right single quote)
            '\u201c': '"',   # " (left double quote)
            '\u201d': '"',   # " (right double quote)
            '\u2013': '-',   # – (en dash)
            '\u2014': '--',  # — (em dash)
            '\u00a0': ' ',   # non-breaking space
        }
        
        # Replace known problematic characters
        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        
        # For any other characters that might cause issues, replace with '?'
        # This is a fallback to ensure we don't crash on unknown characters
        encoded_text = ''
        for char in text:
            try:
                # Test if character can be encoded in the system's default encoding
                char.encode(sys.stdout.encoding or 'utf-8')
                encoded_text += char
            except UnicodeEncodeError:
                encoded_text += '?'
        
        return encoded_text

class ErrorLogger:
    """Logger for crawling errors."""
    
    def __init__(self, log_dir: Optional[str] = None):
        """Initialize the error logger."""
        if log_dir is None:
            # Get the project root directory (4 levels up from this file)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
            log_dir = os.path.join(project_root, "error_logs")
            
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
    def log_error(self, api_name: str, url: str, error: str, error_type: Optional[str] = None):
        """Log an error to a markdown file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Sanitize the error message to handle encoding issues
        sanitized_error = sanitize_text(error)
        sanitized_url = sanitize_text(url)
        sanitized_api_name = sanitize_text(api_name)
        
        # Create the log file path
        log_file = os.path.join(self.log_dir, f"{sanitized_api_name}_errors.md")
        
        # Check if file exists
        file_exists = os.path.exists(log_file)
        
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                # Write header if file is new
                if not file_exists:
                    f.write(f"# Error Log for {sanitized_api_name}\n\n")
                    
                # Write error entry
                f.write(f"## Error at {timestamp}\n")
                if error_type:
                    f.write(f"**Type:** {sanitize_text(error_type)}\n")
                f.write(f"**URL:** {sanitized_url}\n")
                f.write(f"**Error:** {sanitized_error}\n\n")
                
            print(f"Logged error for {sanitized_api_name} at {sanitized_url}")
        except Exception as e:
            # If we still have issues writing to the file, print a fallback error message
            print(f"Error logging to file: {str(e)}")
            print(f"Original error for {sanitized_api_name}: {sanitized_error}")
        
    def log_rate_limit_error(self, api_name: str, url: str, error: str):
        """Log a rate limit error."""
        self.log_error(api_name, url, error, "Rate Limit")
        
    def log_connection_error(self, api_name: str, url: str, error: str):
        """Log a connection error."""
        self.log_error(api_name, url, error, "Connection")
        
    def log_parsing_error(self, api_name: str, url: str, error: str):
        """Log a parsing error."""
        self.log_error(api_name, url, error, "Parsing")
        
    def log_general_error(self, api_name: str, url: str, error: str):
        """Log a general error."""
        self.log_error(api_name, url, error, "General")
        
    def get_error_summary(self, api_name: Optional[str] = None):
        """Get a summary of errors."""
        if api_name:
            log_files = [os.path.join(self.log_dir, f"{api_name}_errors.md")]
        else:
            log_files = [os.path.join(self.log_dir, f) for f in os.listdir(self.log_dir) if f.endswith("_errors.md")]
            
        summary = {}
        
        for log_file in log_files:
            if not os.path.exists(log_file):
                continue
                
            api = os.path.basename(log_file).replace("_errors.md", "")
            summary[api] = {"total": 0, "rate_limit": 0, "connection": 0, "parsing": 0, "general": 0}
            
            with open(log_file, "r") as f:
                content = f.read()
                
                # Count total errors
                summary[api]["total"] = content.count("## Error at")
                
                # Count error types
                summary[api]["rate_limit"] = content.count("**Type:** Rate Limit")
                summary[api]["connection"] = content.count("**Type:** Connection")
                summary[api]["parsing"] = content.count("**Type:** Parsing")
                summary[api]["general"] = content.count("**Type:** General")
                
        return summary

# Global instance
logger = ErrorLogger()

if __name__ == "__main__":
    # Test the error logger
    logger.log_rate_limit_error("TestAPI", "https://example.com/api", "Too many requests")
    logger.log_connection_error("TestAPI", "https://example.com/api/v1", "Connection refused")
    
    summary = logger.get_error_summary()
    print(summary)

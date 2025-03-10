#!/usr/bin/env python
import os
from datetime import datetime
from typing import Optional

class ErrorLogger:
    """Logger for crawling errors."""
    
    def __init__(self, log_dir: str = "error_logs"):
        """Initialize the error logger."""
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        
    def log_error(self, api_name: str, url: str, error: str, error_type: Optional[str] = None):
        """Log an error to a markdown file."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Create the log file path
        log_file = os.path.join(self.log_dir, f"{api_name}_errors.md")
        
        # Check if file exists
        file_exists = os.path.exists(log_file)
        
        with open(log_file, "a") as f:
            # Write header if file is new
            if not file_exists:
                f.write(f"# Error Log for {api_name}\n\n")
                
            # Write error entry
            f.write(f"## Error at {timestamp}\n")
            if error_type:
                f.write(f"**Type:** {error_type}\n")
            f.write(f"**URL:** {url}\n")
            f.write(f"**Error:** {error}\n\n")
            
        print(f"Logged error for {api_name} at {url}")
        
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

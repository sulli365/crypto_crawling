#!/usr/bin/env python
"""
Crypto API Documentation Crawler - Main Entry Point

This script serves as the main entry point for the Crypto API Documentation Crawler.
It provides a command-line interface for different operations such as crawling,
processing, and querying cryptocurrency API documentation.
"""

import argparse
import asyncio
import os
import sys
from typing import List, Optional

# Import from our package
from crypto_crawler.api.config import CryptoApiConfig, load_crypto_api_configs
from crypto_crawler.crawling.url_extractor import get_crypto_api_urls
from crypto_crawler.crawling.crawler import crawl_api_documentation
from crypto_crawler.utils.error_logger import logger
from crypto_crawler.ui.streamlit_app import run_streamlit_app

def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Crypto API Documentation Crawler",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl API documentation")
    crawl_parser.add_argument("--api", help="API name to crawl (default: all)", default=None)
    crawl_parser.add_argument("--max-urls", type=int, help="Maximum URLs to crawl", default=100)
    crawl_parser.add_argument("--concurrency", type=int, help="Concurrency level", default=5)
    
    # Process command
    process_parser = subparsers.add_parser("process", help="Process crawled documentation")
    process_parser.add_argument("--api", help="API name to process (default: all)", default=None)
    process_parser.add_argument("--batch-size", type=int, help="Batch size for processing", default=10)
    
    # UI command
    ui_parser = subparsers.add_parser("ui", help="Run the Streamlit UI")
    ui_parser.add_argument("--port", type=int, help="Port to run the UI on", default=8501)
    
    # Explore command
    explore_parser = subparsers.add_parser("explore", help="Explore an API URL")
    explore_parser.add_argument("url", help="URL to explore")
    explore_parser.add_argument("--depth", type=int, help="Crawl depth", default=2)
    
    # Generate configs command
    generate_parser = subparsers.add_parser("generate-configs", help="Generate API configurations")
    
    return parser.parse_args()

async def crawl_command(api_name: Optional[str] = None, max_urls: int = 100, concurrency: int = 5):
    """Run the crawl command."""
    configs = load_crypto_api_configs()
    
    if api_name:
        configs = [config for config in configs if config.name.lower() == api_name.lower()]
        if not configs:
            print(f"Error: API '{api_name}' not found in configurations.")
            return
    
    for config in configs:
        print(f"Crawling {config.name}...")
        urls = await get_crypto_api_urls(config)
        
        # Limit the number of URLs to crawl
        urls = urls[:max_urls]
        
        print(f"Found {len(urls)} URLs for {config.name}. Starting crawl...")
        await crawl_api_documentation(config, urls, concurrency)
        print(f"Finished crawling {config.name}.")

def process_command(api_name: Optional[str] = None, batch_size: int = 10):
    """Run the process command."""
    # This would be implemented to process the crawled documentation
    print("Processing command not yet implemented.")

def ui_command(port: int = 8501):
    """Run the UI command."""
    run_streamlit_app(port)

async def explore_command(url: str, depth: int = 2):
    """Run the explore command."""
    from crypto_crawler.scripts.explore_api_url import explore_url
    await explore_url(url, depth)

def generate_configs_command():
    """Run the generate configs command."""
    from crypto_crawler.scripts.generate_api_configs import generate_configs
    generate_configs()

async def main():
    """Main entry point."""
    args = parse_args()
    
    if args.command == "crawl":
        await crawl_command(args.api, args.max_urls, args.concurrency)
    elif args.command == "process":
        process_command(args.api, args.batch_size)
    elif args.command == "ui":
        ui_command(args.port)
    elif args.command == "explore":
        await explore_command(args.url, args.depth)
    elif args.command == "generate-configs":
        generate_configs_command()
    else:
        print("Please specify a command. Use --help for more information.")

if __name__ == "__main__":
    asyncio.run(main())

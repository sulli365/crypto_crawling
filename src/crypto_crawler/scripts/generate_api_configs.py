#!/usr/bin/env python
import os
import asyncio
import argparse
from typing import List, Dict, Any, Optional
import json

from crypto_crawler.api.config import CryptoApiConfig, save_crypto_api_configs
from crypto_crawler.scripts.explore_api_url import explore_url, check_sitemap
from urllib.parse import urlparse

async def analyze_api_url(url: str) -> Dict[str, Any]:
    """Analyze an API URL to determine its characteristics."""
    print(f"Analyzing URL: {url}")
    
    # Check if the site has a sitemap
    has_sitemap = await check_sitemap(url)
    
    # Explore the URL
    analysis = await explore_url(url)
    
    if not analysis:
        return {
            "has_sitemap": has_sitemap,
            "recommended_depth": 2,
            "regex_patterns": [],
            "internal_link_count": 0
        }
    
    # Add sitemap information
    analysis["has_sitemap"] = has_sitemap
    
    return analysis

async def generate_configs_from_markdown(markdown_path: str, analyze: bool = False) -> List[CryptoApiConfig]:
    """Generate API configurations from a markdown file."""
    import re
    
    # Ensure we have the full path
    if not os.path.isabs(markdown_path):
        # Get the project root directory (4 levels up from this file)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
        markdown_path = os.path.join(project_root, "docs", markdown_path)
    
    # Parse the markdown file to extract API information
    with open(markdown_path, "r") as f:
        content = f.read()
        
    # Extract API sections using regex
    api_sections = re.findall(r'## \d+\. (.+?)\n\*\*Website:\*\* (https?://[^\n]+)', content)
    
    configs = []
    for i, (name, website) in enumerate(api_sections):
        name = name.strip()
        website = website.strip()
        
        print(f"Processing {i+1}/{len(api_sections)}: {name}")
        
        # Default configuration
        config = {
            "name": name,
            "base_url": website,
            "category": "market_data",  # Default category
            "has_sitemap": False,
            "max_depth": 2,
            "url_patterns": [],
            "delay_between_requests": 1.0,
            "max_retries": 3
        }
        
        # Analyze the URL if requested
        if analyze:
            try:
                analysis = await analyze_api_url(website)
                
                # Update config with analysis results
                config["has_sitemap"] = analysis["has_sitemap"]
                config["max_depth"] = analysis["recommended_depth"]
                config["url_patterns"] = analysis.get("regex_patterns", [])
                
                print(f"  - Has sitemap: {config['has_sitemap']}")
                print(f"  - Recommended depth: {config['max_depth']}")
                print(f"  - URL patterns: {config['url_patterns']}")
                
                # Add a small delay between API analyses to avoid rate limiting
                await asyncio.sleep(2)
            except Exception as e:
                print(f"Error analyzing {name}: {e}")
        
        configs.append(CryptoApiConfig(**config))
    
    return configs

async def main():
    parser = argparse.ArgumentParser(description="Generate API configurations from markdown")
    parser.add_argument("--markdown", default="crypto-apis.md", help="Path to markdown file with API information")
    parser.add_argument("--analyze", action="store_true", help="Analyze URLs to determine characteristics")
    parser.add_argument("--output", default=None, help="Output file for configurations (defaults to config/crypto_api_configs.json)")
    
    args = parser.parse_args()
    
    # Generate configurations
    configs = await generate_configs_from_markdown(args.markdown, args.analyze)
    
    # Save configurations
    save_crypto_api_configs(configs)
    
    # Get the output path
    if args.output:
        output_path = args.output
    else:
        # Get the project root directory (4 levels up from this file)
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
        output_path = os.path.join(project_root, "config", "crypto_api_configs.json")
    
    print(f"\nGenerated {len(configs)} API configurations")
    print(f"Saved to {output_path}")

if __name__ == "__main__":
    asyncio.run(main())

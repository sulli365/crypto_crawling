#!/usr/bin/env python
import os
import asyncio
import argparse
import re
from urllib.parse import urlparse
from typing import Dict, List, Any, Optional
import json
import sys

# Add the current directory to the path to ensure imports work
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig
from dotenv import load_dotenv

load_dotenv()

async def explore_url(url: str, max_depth: int = 1):
    """Explore a URL and analyze its structure and content."""
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()
    
    try:
        print(f"Exploring URL: {url}")
        result = await crawler.arun(url=url)
        
        if not result.success:
            print(f"Failed to crawl URL: {result.error_message}")
            return
            
        # Analyze page content
        content_length = len(result.markdown_v2.raw_markdown)
        print(f"Content length: {content_length} characters")
        
        # Extract and categorize links
        internal_links = result.links["internal"]
        external_links = result.links["external"]
        
        print(f"Found {len(internal_links)} internal links and {len(external_links)} external links")
        
        # Analyze URL structure
        parsed_url = urlparse(url)
        base_path = parsed_url.path
        print(f"Base path: {base_path}")
        
        # Identify common patterns in internal links
        path_patterns = {}
        for link in internal_links:
            parsed_link = urlparse(link['href'])
            path = parsed_link.path
            
            # Extract path components
            components = path.strip('/').split('/')
            if len(components) > 0:
                first_component = components[0]
                if first_component:  # Skip empty components
                    path_patterns[first_component] = path_patterns.get(first_component, 0) + 1
                
        print("\nCommon path patterns:")
        for pattern, count in sorted(path_patterns.items(), key=lambda x: x[1], reverse=True):
            print(f"  /{pattern}/ - {count} occurrences")
            
        # Recommend crawl depth
        if len(internal_links) > 100:
            recommended_depth = 1
        elif len(internal_links) > 50:
            recommended_depth = 2
        else:
            recommended_depth = 3
            
        print(f"\nRecommended crawl depth: {recommended_depth}")
        
        # Sample some internal links
        print("\nSample internal links:")
        for link in internal_links[:5]:
            print(f"  {link['href']}")
            
        # Check for API documentation patterns
        api_patterns = []
        doc_keywords = ['api', 'docs', 'documentation', 'reference', 'endpoints', 'v1', 'v2', 'v3']
        
        for link in internal_links:
            href = link['href'].lower()
            path = urlparse(href).path
            
            # Check if path contains API documentation keywords
            if any(keyword in path for keyword in doc_keywords):
                api_patterns.append(path)
                
        print("\nPotential API documentation paths:")
        for pattern in api_patterns[:10]:  # Show top 10
            print(f"  {pattern}")
            
        # Generate regex patterns for API docs
        regex_patterns = []
        
        # Common documentation patterns
        if any("/api/" in link['href'] for link in internal_links):
            regex_patterns.append(r"/api/")
        if any("/docs/" in link['href'] for link in internal_links):
            regex_patterns.append(r"/docs/")
        if any("/reference/" in link['href'] for link in internal_links):
            regex_patterns.append(r"/reference/")
        if any("/endpoints/" in link['href'] for link in internal_links):
            regex_patterns.append(r"/endpoints/")
            
        # Look for API version patterns (v1, v2, etc.)
        version_pattern = re.compile(r'/v\d+/')
        version_matches = [version_pattern.search(link['href']) for link in internal_links]
        version_matches = [m.group(0) for m in version_matches if m]
        
        if version_matches:
            regex_patterns.append(r"/v\d+/")
            
        print("\nRecommended regex patterns for API docs:")
        for pattern in regex_patterns:
            print(f"  {pattern}")
        
        # Return analysis results
        return {
            "recommended_depth": recommended_depth,
            "common_patterns": [p for p, c in sorted(path_patterns.items(), key=lambda x: x[1], reverse=True)[:5]],
            "internal_link_count": len(internal_links),
            "regex_patterns": regex_patterns,
            "api_doc_paths": api_patterns[:10]
        }
    finally:
        await crawler.close()

async def check_sitemap(url: str) -> bool:
    """Check if a site has a sitemap.xml file."""
    # Parse the URL to get the base
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    
    # Try common sitemap locations
    sitemap_urls = [
        f"{base_url}/sitemap.xml",
        f"{base_url}/sitemap_index.xml",
        f"{base_url}/sitemap/sitemap.xml"
    ]
    
    import aiohttp
    
    async with aiohttp.ClientSession() as session:
        for sitemap_url in sitemap_urls:
            try:
                print(f"Checking for sitemap at: {sitemap_url}")
                async with session.get(sitemap_url) as response:
                    if response.status == 200:
                        content_type = response.headers.get('Content-Type', '')
                        if 'xml' in content_type or 'text/plain' in content_type:
                            print(f"Found sitemap at: {sitemap_url}")
                            return True
            except Exception as e:
                print(f"Error checking {sitemap_url}: {e}")
                
    print("No sitemap found")
    return False

async def main():
    parser = argparse.ArgumentParser(description="Explore an API documentation URL")
    parser.add_argument("url", help="URL to explore")
    parser.add_argument("--depth", type=int, default=1, help="Exploration depth")
    parser.add_argument("--output", help="Output file for analysis results (JSON)")
    
    args = parser.parse_args()
    
    # Check if the site has a sitemap
    has_sitemap = await check_sitemap(args.url)
    
    # Explore the URL
    analysis = await explore_url(args.url, args.depth)
    
    if analysis:
        # Add sitemap information
        analysis["has_sitemap"] = has_sitemap
        
        # Save to file if requested
        if args.output:
            with open(args.output, 'w') as f:
                json.dump(analysis, f, indent=2)
            print(f"Analysis saved to {args.output}")

if __name__ == "__main__":
    asyncio.run(main())

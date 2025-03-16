#!/usr/bin/env python
import os
import asyncio
import re
from typing import List, Set, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
import requests
from xml.etree import ElementTree

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode

# Import from our package
from crypto_crawler.api.config import CryptoApiConfig, get_urls_from_sitemap, is_documentation_url
from crypto_crawler.utils.error_logger import logger

async def extract_internal_documentation_urls(
    api_config: CryptoApiConfig,
    browser_config: Optional[BrowserConfig] = None
) -> List[str]:
    """Extract internal documentation URLs by crawling the site."""
    if not browser_config:
        browser_config = BrowserConfig(
            headless=True,
            verbose=False,
            extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
        )
    
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()
    
    try:
        # Start with the base URL
        base_url = api_config.base_url
        all_urls = set([base_url])
        urls_to_process = [base_url]
        processed_urls = set()
        
        # Process URLs up to the specified depth
        for depth in range(api_config.max_depth):
            print(f"Crawling depth {depth+1}/{api_config.max_depth} for {api_config.name}")
            new_urls_to_process = []
            
            for url in urls_to_process:
                if url in processed_urls:
                    continue
                
                # Add delay between requests
                await asyncio.sleep(api_config.delay_between_requests)
                
                try:
                    result = await crawler.arun(
                        url=url,
                        config=CrawlerRunConfig(
                            exclude_external_links=True,
                            cache_mode=CacheMode.BYPASS
                        ),
                        session_id=f"session_{api_config.name}"
                    )
                    
                    if result.success:
                        # Extract internal links
                        internal_links = [link['href'] for link in result.links["internal"]]
                        
                        # Normalize URLs
                        normalized_links = []
                        for link in internal_links:
                            # Handle relative URLs
                            if not link.startswith('http'):
                                link = urljoin(url, link)
                            normalized_links.append(link)
                        
                        # Filter for likely documentation URLs
                        doc_links = []
                        for link in normalized_links:
                            if is_documentation_url(link, api_config.url_patterns):
                                doc_links.append(link)
                        
                        # Add to our collection
                        new_urls_to_process.extend(doc_links)
                        all_urls.update(doc_links)
                        
                        print(f"Found {len(doc_links)} documentation links at {url}")
                    else:
                        logger.log_general_error(
                            api_config.name, 
                            url, 
                            f"Crawl failed: {result.error_message}"
                        )
                except Exception as e:
                    error_message = str(e).lower()
                    
                    # Check if it's a rate limit error
                    if any(term in error_message for term in ["rate limit", "too many requests", "429"]):
                        logger.log_rate_limit_error(api_config.name, url, str(e))
                    else:
                        logger.log_general_error(api_config.name, url, str(e))
                
                processed_urls.add(url)
            
            # Update URLs to process for next depth level
            urls_to_process = list(set(new_urls_to_process) - processed_urls)
            
            print(f"Depth {depth+1} complete. Found {len(all_urls)} total URLs, {len(urls_to_process)} new to process.")
            
            # If no more URLs to process, break early
            if not urls_to_process:
                break
        
        return list(all_urls)
    finally:
        await crawler.close()

async def get_crypto_api_urls(api_config: CryptoApiConfig) -> List[str]:
    """Get URLs from a crypto API documentation site using either sitemap or crawling."""
    print(f"Getting URLs for {api_config.name}...")
    
    if api_config.has_sitemap:
        # Use sitemap approach
        sitemap_url = api_config.sitemap_url or f"{api_config.base_url.rstrip('/')}/sitemap.xml"
        print(f"Using sitemap at {sitemap_url}")
        urls = get_urls_from_sitemap(sitemap_url)
        
        # Filter URLs using patterns if available
        if api_config.url_patterns:
            urls = [url for url in urls if is_documentation_url(url, api_config.url_patterns)]
            
        print(f"Found {len(urls)} URLs from sitemap for {api_config.name}")
        return urls
    else:
        # Use internal link extraction approach
        print(f"Crawling for internal links for {api_config.name}")
        urls = await extract_internal_documentation_urls(api_config)
        print(f"Found {len(urls)} URLs from crawling for {api_config.name}")
        return urls

if __name__ == "__main__":
    # Test the URL extractor
    from crypto_crawler.api.config import load_crypto_api_configs
    
    async def test():
        configs = load_crypto_api_configs()
        if configs:
            # Test with the first config
            test_config = configs[0]
            print(f"Testing URL extraction for {test_config.name}")
            
            # Add some test patterns
            test_config.url_patterns = [r"/api/", r"/docs/", r"/reference/"]
            
            urls = await get_crypto_api_urls(test_config)
            print(f"Found {len(urls)} URLs")
            for url in urls[:5]:  # Print first 5 URLs
                print(f"- {url}")
    
    asyncio.run(test())

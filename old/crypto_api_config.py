#!/usr/bin/env python
import os
import json
import re
from dataclasses import dataclass, field, asdict
from typing import List, Optional, Dict, Any
from urllib.parse import urlparse
import requests
from xml.etree import ElementTree

@dataclass
class CryptoApiConfig:
    """Configuration for a cryptocurrency API documentation site."""
    name: str                # API name (e.g., "CoinGecko")
    base_url: str            # Base documentation URL
    category: str            # Category (e.g., "market_data", "blockchain", "defi")
    has_sitemap: bool = False  # Whether the site has a sitemap.xml
    sitemap_url: Optional[str] = None  # Custom sitemap URL if different from base_url/sitemap.xml
    max_depth: int = 2       # How deep to crawl for internal links
    url_patterns: List[str] = field(default_factory=list)  # Regex patterns for valid doc URLs
    delay_between_requests: float = 1.0  # Seconds to wait between requests
    max_retries: int = 3     # Number of retries for rate limit errors

def load_crypto_api_configs() -> List[CryptoApiConfig]:
    """Load crypto API configurations from a JSON file."""
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "crypto_api_configs.json")
    
    try:
        with open(config_path, "r") as f:
            configs_data = json.load(f)
            
        return [CryptoApiConfig(**config) for config in configs_data]
    except FileNotFoundError:
        # If file doesn't exist, create default configs from crypto-apis.md
        configs = create_default_configs()
        save_crypto_api_configs(configs)
        return configs

def save_crypto_api_configs(configs: List[CryptoApiConfig]):
    """Save API configurations to a JSON file."""
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "crypto_api_configs.json")
    
    # Convert dataclasses to dictionaries
    configs_data = [asdict(config) for config in configs]
    
    with open(config_path, "w") as f:
        json.dump(configs_data, f, indent=2)

def create_default_configs() -> List[CryptoApiConfig]:
    """Create default configurations from crypto-apis.md."""
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    markdown_path = os.path.join(script_dir, "crypto-apis.md")
    
    # Parse the markdown file to extract API information
    with open(markdown_path, "r") as f:
        content = f.read()
        
    # Extract API sections using regex
    api_sections = re.findall(r'## \d+\. (.+?)\n\*\*Website:\*\* (https?://[^\n]+)', content)
    
    configs = []
    for name, website in api_sections:
        # Create a basic config for each API
        configs.append(CryptoApiConfig(
            name=name.strip(),
            base_url=website.strip(),
            category="market_data",  # Default category
            has_sitemap=False,       # Default to no sitemap
            max_depth=2,             # Default depth
            delay_between_requests=1.0,
            max_retries=3
        ))
        
    return configs

def get_urls_from_sitemap(sitemap_url: str) -> List[str]:
    """Get URLs from a sitemap.xml file."""
    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        
        # Parse the XML
        root = ElementTree.fromstring(response.content)
        
        # Extract all URLs from the sitemap
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        urls = [loc.text for loc in root.findall('.//ns:loc', namespace)]
        
        return urls
    except Exception as e:
        print(f"Error fetching sitemap: {e}")
        return []

def is_documentation_url(url: str, patterns: List[str]) -> bool:
    """Check if a URL matches documentation patterns."""
    # If no patterns defined, accept all URLs
    if not patterns:
        return True
        
    # Check if URL matches any pattern
    return any(re.search(pattern, url) for pattern in patterns)

def filter_api_urls(urls: List[str], api_config: CryptoApiConfig) -> List[str]:
    """Filter URLs to only include API documentation URLs."""
    if not api_config.url_patterns:
        return urls
        
    return [url for url in urls if is_documentation_url(url, api_config.url_patterns)]

if __name__ == "__main__":
    # Test the configuration system
    configs = load_crypto_api_configs()
    print(f"Loaded {len(configs)} API configurations")
    
    for config in configs[:5]:  # Print first 5 configs
        print(f"- {config.name}: {config.base_url}")

#!/usr/bin/env python
import os
import json
import asyncio
import argparse
import requests
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlparse
from dotenv import load_dotenv

from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from openai import AsyncOpenAI
from supabase import create_client, Client

# Import from our package
from crypto_crawler.api.config import CryptoApiConfig, load_crypto_api_configs, save_crypto_api_configs
from crypto_crawler.crawling.url_extractor import get_crypto_api_urls
from crypto_crawler.utils.error_logger import logger

load_dotenv()

# Initialize OpenAI and Supabase clients
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

@dataclass
class ProcessedChunk:
    url: str
    chunk_number: int
    title: str
    summary: str
    content: str
    metadata: Dict[str, Any]
    embedding: List[float]

def chunk_text(text: str, chunk_size: int = 5000) -> List[str]:
    """Split text into chunks, respecting code blocks and paragraphs."""
    chunks = []
    start = 0
    text_length = len(text)

    while start < text_length:
        # Calculate end position
        end = start + chunk_size

        # If we're at the end of the text, just take what's left
        if end >= text_length:
            chunks.append(text[start:].strip())
            break

        # Try to find a code block boundary first (```)
        chunk = text[start:end]
        code_block = chunk.rfind('```')
        if code_block != -1 and code_block > chunk_size * 0.3:
            end = start + code_block

        # If no code block, try to break at a paragraph
        elif '\n\n' in chunk:
            # Find the last paragraph break
            last_break = chunk.rfind('\n\n')
            if last_break > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
                end = start + last_break

        # If no paragraph break, try to break at a sentence
        elif '. ' in chunk:
            # Find the last sentence break
            last_period = chunk.rfind('. ')
            if last_period > chunk_size * 0.3:  # Only break if we're past 30% of chunk_size
                end = start + last_period + 1

        # Extract chunk and clean it up
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        # Move start position for next chunk
        start = max(start + 1, end)

    return chunks

async def get_title_and_summary(chunk: str, url: str) -> Dict[str, str]:
    """Extract title and summary using GPT-4."""
    system_prompt = """You are an AI that extracts titles and summaries from documentation chunks.
    Return a JSON object with 'title' and 'summary' keys.
    For the title: If this seems like the start of a document, extract its title. If it's a middle chunk, derive a descriptive title.
    For the summary: Create a concise summary of the main points in this chunk.
    Keep both title and summary concise but informative."""
    
    try:
        response = await openai_client.chat.completions.create(
            model=os.getenv("LLM_MODEL", "gpt-4o-mini"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"URL: {url}\n\nContent:\n{chunk[:1000]}..."}  # Send first 1000 chars for context
            ],
            response_format={ "type": "json_object" }
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"Error getting title and summary: {e}")
        return {"title": "Error processing title", "summary": "Error processing summary"}

async def get_embedding(text: str) -> List[float]:
    """Get embedding vector from OpenAI."""
    try:
        response = await openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding
    except Exception as e:
        print(f"Error getting embedding: {e}")
        return [0] * 1536  # Return zero vector on error

async def process_chunk(chunk: str, chunk_number: int, url: str, api_name: str) -> ProcessedChunk:
    """Process a single chunk of text."""
    # Get title and summary
    extracted = await get_title_and_summary(chunk, url)
    
    # Get embedding
    embedding = await get_embedding(chunk)
    
    # Create metadata with dynamic source based on API name
    metadata = {
        "source": api_name,
        "chunk_size": len(chunk),
        "crawled_at": datetime.now(timezone.utc).isoformat(),
        "url_path": urlparse(url).path
    }
    
    return ProcessedChunk(
        url=url,
        chunk_number=chunk_number,
        title=extracted['title'],
        summary=extracted['summary'],
        content=chunk,  # Store the original chunk content
        metadata=metadata,
        embedding=embedding
    )

async def insert_chunk(chunk: ProcessedChunk):
    """Insert a processed chunk into Supabase."""
    try:
        data = {
            "url": chunk.url,
            "chunk_number": chunk.chunk_number,
            "title": chunk.title,
            "summary": chunk.summary,
            "content": chunk.content,
            "metadata": chunk.metadata,
            "embedding": chunk.embedding
        }
        
        result = supabase.table("crypto_api_site_pages").insert(data).execute()
        
        print(f"Inserted chunk {chunk.chunk_number} for {chunk.url}")
        return result
    except Exception as e:
        print(f"Error inserting chunk: {e}")
        print(f"Error details: {str(e)}")
        # Print more detailed error information if available
        if hasattr(e, 'response'):
            print(f"Response status: {e.response.status_code}")
            print(f"Response content: {e.response.content}")
        return None

async def process_and_store_document(url: str, markdown: str, api_name: str):
    """Process a document and store its chunks in parallel."""
    # Split into chunks
    chunks = chunk_text(markdown)
    
    # Process chunks in parallel
    tasks = [
        process_chunk(chunk, i, url, api_name) 
        for i, chunk in enumerate(chunks)
    ]
    processed_chunks = await asyncio.gather(*tasks)
    
    # Store chunks in parallel
    insert_tasks = [
        insert_chunk(chunk) 
        for chunk in processed_chunks
    ]
    await asyncio.gather(*insert_tasks)

async def crawl_with_rate_limit(
    crawler: AsyncWebCrawler, 
    url: str, 
    config: CrawlerRunConfig, 
    api_config: CryptoApiConfig
) -> Optional[Any]:
    """Crawl a URL with rate limiting and retry logic."""
    for attempt in range(api_config.max_retries + 1):
        try:
            # Add delay between requests (except first attempt)
            if attempt > 0:
                retry_delay = api_config.delay_between_requests * (2 ** (attempt - 1))  # Exponential backoff
                print(f"Retry {attempt} for {url}, waiting {retry_delay:.2f}s")
                await asyncio.sleep(retry_delay)
            else:
                await asyncio.sleep(api_config.delay_between_requests)
                
            # Attempt to crawl
            result = await crawler.arun(
                url=url,
                config=config,
                session_id=f"session_{api_config.name}"
            )
            
            return result
            
        except Exception as e:
            error_message = str(e).lower()
            
            # Check if it's a rate limit error
            is_rate_limit = any(term in error_message for term in 
                               ["rate limit", "too many requests", "429"])
            
            # If it's the last attempt or not a rate limit error, log and continue
            if attempt == api_config.max_retries or not is_rate_limit:
                if is_rate_limit:
                    logger.log_rate_limit_error(api_config.name, url, str(e))
                else:
                    logger.log_general_error(api_config.name, url, str(e))
                return None
                
    return None

async def crawl_parallel(urls: List[str], api_config: CryptoApiConfig, max_concurrent: int = 5):
    """Crawl multiple URLs in parallel with a concurrency limit."""
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=["--disable-gpu", "--disable-dev-shm-usage", "--no-sandbox"],
    )
    crawl_config = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)

    # Create the crawler instance
    crawler = AsyncWebCrawler(config=browser_config)
    await crawler.start()

    try:
        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def process_url(url: str):
            async with semaphore:
                result = await crawl_with_rate_limit(crawler, url, crawl_config, api_config)
                
                if result and result.success:
                    print(f"Successfully crawled: {url}")
                    await process_and_store_document(
                        url, 
                        result.markdown_v2.raw_markdown, 
                        api_config.name
                    )
                elif result:
                    logger.log_general_error(
                        api_config.name, 
                        url, 
                        f"Crawl failed: {result.error_message}"
                    )
                    print(f"Failed: {url} - Error: {result.error_message}")
                else:
                    print(f"Failed after retries: {url}")
        
        # Process all URLs in parallel with limited concurrency
        await asyncio.gather(*[process_url(url) for url in urls])
    finally:
        await crawler.close()

async def process_api(api_config: CryptoApiConfig):
    """Process a single API's documentation."""
    print(f"\n{'='*50}")
    print(f"Processing {api_config.name} API documentation...")
    print(f"{'='*50}")
    
    # Get URLs for this API
    urls = await get_crypto_api_urls(api_config)
    if not urls:
        print(f"No URLs found for {api_config.name}")
        return
    
    print(f"Found {len(urls)} URLs for {api_config.name}")
    
    # Crawl and process the URLs
    await crawl_parallel(urls, api_config)
    
    print(f"Completed processing for {api_config.name}")

async def main():
    parser = argparse.ArgumentParser(description="Crawl cryptocurrency API documentation")
    parser.add_argument("--api", help="Specific API to crawl (by name)")
    parser.add_argument("--category", help="Category of APIs to crawl")
    parser.add_argument("--list", action="store_true", help="List available APIs and exit")
    parser.add_argument("--explore", help="Explore a specific API URL and generate config")
    parser.add_argument("--max-apis", type=int, default=None, help="Maximum number of APIs to process")
    
    args = parser.parse_args()
    
    # Load API configurations
    all_configs = load_crypto_api_configs()
    print(f"Loaded {len(all_configs)} API configurations")
    
    # List APIs if requested
    if args.list:
        print("\nAvailable APIs:")
        for i, config in enumerate(all_configs):
            print(f"{i+1}. {config.name} - {config.base_url}")
        return
        
    # Explore a URL if requested
    if args.explore:
        # Import here to avoid circular imports
        from crypto_crawler.scripts.explore_api_url import explore_url, check_sitemap
        
        print(f"Exploring URL: {args.explore}")
        has_sitemap = await check_sitemap(args.explore)
        analysis = await explore_url(args.explore)
        
        if analysis:
            print("\nAnalysis complete. Recommended configuration:")
            api_name = urlparse(args.explore).netloc.split('.')[-2]
            print(f"Name: {api_name}")
            print(f"Base URL: {args.explore}")
            print(f"Has sitemap: {has_sitemap}")
            print(f"Recommended depth: {analysis['recommended_depth']}")
            print(f"Recommended patterns: {analysis.get('regex_patterns', [])}")
        return
    
    # Filter APIs based on selection criteria
    selected_configs = all_configs
    
    if args.api:
        selected_configs = [config for config in all_configs if config.name.lower() == args.api.lower()]
        if not selected_configs:
            print(f"No API found with name: {args.api}")
            return
            
    elif args.category:
        selected_configs = [config for config in all_configs if config.category.lower() == args.category.lower()]
        if not selected_configs:
            print(f"No APIs found in category: {args.category}")
            return
    
    # Limit the number of APIs if requested
    if args.max_apis and len(selected_configs) > args.max_apis:
        selected_configs = selected_configs[:args.max_apis]
        
    print(f"Selected {len(selected_configs)} APIs to process")
    
    # Process each API
    for api_config in selected_configs:
        await process_api(api_config)
        
    print("\nAll processing complete!")

if __name__ == "__main__":
    asyncio.run(main())

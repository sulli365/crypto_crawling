#!/usr/bin/env python
import os
import json
import asyncio
import argparse
import requests
import psutil
import sys
import glob
import shutil
import gc
from typing import List, Dict, Any, Optional, Tuple
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

async def check_chunk_exists(url: str, chunk_number: int) -> bool:
    """Check if a chunk already exists in the database."""
    try:
        result = supabase.table("crypto_api_site_pages").select("id").eq("url", url).eq("chunk_number", chunk_number).execute()
        return len(result.data) > 0
    except Exception as e:
        # Extract API name from URL if possible
        api_name = urlparse(url).netloc.split('.')[-2] if urlparse(url).netloc else "unknown"
        # Sanitize error message before logging
        sanitized_error = sanitize_text(str(e))
        logger.log_general_error(api_name, url, f"Error checking chunk existence: {sanitized_error}")
        return False

async def insert_chunk(chunk: ProcessedChunk):
    """Insert a processed chunk into Supabase if it doesn't already exist."""
    try:
        # Check if chunk already exists
        if await check_chunk_exists(chunk.url, chunk.chunk_number):
            print(f"Chunk {chunk.chunk_number} for {chunk.url} already exists - skipping")
            return None
            
        data = {
            "url": chunk.url,
            "chunk_number": chunk.chunk_number,
            "title": chunk.title,
            "summary": chunk.summary,
            "content": chunk.content,
            "metadata": chunk.metadata,
            "embedding": chunk.embedding
        }
        
        # Use upsert to handle race conditions
        result = supabase.table("crypto_api_site_pages").upsert(
            data,
            on_conflict="url,chunk_number"  # Assuming these columns have a unique constraint
        ).execute()
        
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
            char.encode(sys.stdout.encoding)
            encoded_text += char
        except UnicodeEncodeError:
            encoded_text += '?'
    
    return encoded_text

async def process_and_store_document(url: str, markdown: str, api_name: str):
    """Process a document and store its chunks in parallel."""
    try:
        # Sanitize markdown to handle encoding issues
        sanitized_markdown = sanitize_text(markdown)
        
        # Split into chunks
        chunks = chunk_text(sanitized_markdown)
        
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
    except Exception as e:
        # Sanitize error message before logging and printing
        sanitized_error = sanitize_text(str(e))
        logger.log_general_error(api_name, url, f"Error processing document: {sanitized_error}")
        print(f"Error processing {url}: {sanitized_error}")

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
                # Sanitize error message before logging
                sanitized_error = sanitize_text(str(e))
                if is_rate_limit:
                    logger.log_rate_limit_error(api_config.name, url, sanitized_error)
                else:
                    logger.log_general_error(api_config.name, url, sanitized_error)
                return None
                
    return None

# Memory management constants
MEMORY_THRESHOLD = 0.6  # 60% system memory utilization
SAFETY_BUFFER = 0.05    # 5% buffer below OS OOM killer
MIN_BATCH_SIZE = 20     # Minimum batch size for efficiency
MAX_BATCH_SIZE = 100    # Maximum batch size
MIN_CONCURRENCY = 2     # Minimum concurrency
MAX_CONCURRENCY = 8     # Maximum concurrency

def get_memory_usage() -> Tuple[float, float]:
    """
    Get current memory usage as a percentage and available memory in GB.
    
    Returns:
        Tuple of (memory_percent, available_gb)
    """
    mem = psutil.virtual_memory()
    memory_percent = mem.percent / 100.0
    available_gb = mem.available / (1024 ** 3)
    return memory_percent, available_gb

def should_reduce_resources() -> bool:
    """
    Check if we should reduce resource usage based on memory threshold.
    
    Returns:
        True if memory usage is above threshold, False otherwise
    """
    memory_percent, _ = get_memory_usage()
    return memory_percent > (MEMORY_THRESHOLD - SAFETY_BUFFER)

def get_dynamic_batch_size() -> int:
    """
    Calculate dynamic batch size based on available memory.
    
    Returns:
        Batch size between MIN_BATCH_SIZE and MAX_BATCH_SIZE
    """
    memory_percent, available_gb = get_memory_usage()
    
    if memory_percent > MEMORY_THRESHOLD:
        # If memory usage is high, use minimum batch size
        return MIN_BATCH_SIZE
    
    # Scale batch size based on available memory
    # More available memory = larger batch size
    if available_gb > 8:
        return MAX_BATCH_SIZE
    elif available_gb > 4:
        return int(MIN_BATCH_SIZE + (MAX_BATCH_SIZE - MIN_BATCH_SIZE) * 0.75)
    elif available_gb > 2:
        return int(MIN_BATCH_SIZE + (MAX_BATCH_SIZE - MIN_BATCH_SIZE) * 0.5)
    else:
        return MIN_BATCH_SIZE

def get_dynamic_concurrency(default_concurrency: int = 5) -> int:
    """
    Calculate dynamic concurrency based on available memory.
    
    Args:
        default_concurrency: Default concurrency level
        
    Returns:
        Concurrency level between MIN_CONCURRENCY and MAX_CONCURRENCY
    """
    memory_percent, available_gb = get_memory_usage()
    
    if memory_percent > MEMORY_THRESHOLD:
        # If memory usage is high, use minimum concurrency
        return MIN_CONCURRENCY
    
    # Scale concurrency based on available memory
    if available_gb > 8:
        return MAX_CONCURRENCY
    elif available_gb > 4:
        return min(default_concurrency, 6)
    elif available_gb > 2:
        return min(default_concurrency, 4)
    else:
        return MIN_CONCURRENCY

async def save_progress(api_name: str, completed_urls: List[str]):
    """Save crawling progress to a file."""
    progress_dir = "progress"
    os.makedirs(progress_dir, exist_ok=True)
    progress_file = os.path.join(progress_dir, f"{api_name}_progress.json")
    
    # Save with timestamp and additional metadata
    data = {
        'completed_urls': completed_urls,
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'total_completed': len(completed_urls)
    }
    
    with open(progress_file, 'w') as f:
        json.dump(data, f, indent=2)

async def load_progress(api_name: str) -> List[str]:
    """Load previously saved progress."""
    progress_dir = "progress"
    progress_file = os.path.join(progress_dir, f"{api_name}_progress.json")
    
    if os.path.exists(progress_file):
        try:
            with open(progress_file, 'r') as f:
                data = json.load(f)
                return data.get('completed_urls', [])
        except json.JSONDecodeError as e:
            # Sanitize error message before logging
            sanitized_error = sanitize_text(str(e))
            logger.log_general_error(api_name, progress_file, f"Error loading progress file: {sanitized_error}")
            # Backup corrupted file and return empty list
            backup_file = f"{progress_file}.bak"
            os.rename(progress_file, backup_file)
            print(f"Backed up corrupted progress file to {backup_file}")
            return []
    return []

async def cleanup_browser(crawler: AsyncWebCrawler, api_config: Optional[CryptoApiConfig] = None):
    """Improved resource cleanup with multiple strategies."""
    try:
        # First try proper shutdown with timeout
        try:
            await asyncio.wait_for(crawler.close(), timeout=10)
        except (asyncio.TimeoutError, Exception) as e:
            print(f"Normal browser shutdown failed: {str(e)}")
        
        # Then kill any remaining Chrome processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                if proc.info['cmdline'] and any('chrome' in part.lower() for part in proc.info['cmdline']):
                    try:
                        proc.terminate()
                        print(f"Terminated Chrome process {proc.info['pid']}")
                    except psutil.NoSuchProcess:
                        pass
            except (psutil.AccessDenied, psutil.ZombieProcess, Exception) as e:
                print(f"Error checking process {proc.pid}: {str(e)}")
                
        # Clear Chromium temp directories
        temp_dirs = [
            os.path.join(os.getenv('TEMP', os.path.join(os.path.expanduser('~'), 'AppData', 'Local', 'Temp')), 'puppeteer*'),
            os.path.expanduser('~/.cache/puppeteer')
        ]
        for pattern in temp_dirs:
            try:
                for path in glob.glob(pattern):
                    try:
                        shutil.rmtree(path, ignore_errors=True)
                        print(f"Cleaned up temp directory: {path}")
                    except Exception as e:
                        print(f"Error cleaning temp directory {path}: {str(e)}")
            except Exception as e:
                print(f"Error processing temp pattern {pattern}: {str(e)}")
                
        # Force garbage collection
        gc.collect()
                
    except Exception as e:
        # Sanitize error message before logging and printing
        sanitized_error = sanitize_text(str(e))
        if 'api_config' in locals():
            logger.log_general_error(api_config.name, "cleanup", f"Cleanup error: {sanitized_error}")
        else:
            print(f"Cleanup error: {sanitized_error}")

async def crawl_parallel(urls: List[str], api_config: CryptoApiConfig, max_concurrent: int = 5):
    """Crawl multiple URLs in parallel with dynamic batch sizing and concurrency based on memory usage."""
    # Load previous progress
    completed_urls = await load_progress(api_config.name)
    remaining_urls = [url for url in urls if url not in completed_urls]
    
    print(f"Resuming crawl for {api_config.name}: {len(completed_urls)} completed, {len(remaining_urls)} remaining")
    
    browser_config = BrowserConfig(
        headless=True,
        verbose=False,
        extra_args=[
            "--disable-gpu",
            "--disable-dev-shm-usage",
            "--no-sandbox",
            "--js-flags=--max-old-space-size=4096",  # 4GB JS heap limit
            "--no-first-run", 
            "--disable-setuid-sandbox",
            "--disable-accelerated-2d-canvas",
            # Remove problematic flags for SPAs
            # "--single-process",  # Can cause issues with complex SPAs
            # "--no-zygote",  # Can cause stability issues
            # "--disable-site-isolation-trials"  # Can interfere with SPA rendering
        ],
    )
    # Adaptive configuration based on site characteristics
    # For known SPAs or sites with dynamic content, use more patient settings
    is_spa = api_config.name in ["CoinDesk"] or any(pattern in api_config.base_url for pattern in [
        "react", "vue", "angular", "nuxt", "next", "gatsby", "spa", "single-page"
    ])
    
    # Use networkidle for SPAs to ensure content is fully loaded
    wait_until = "networkidle" if is_spa else "domcontentloaded"
    
    # Adjust page_timeout based on site type
    page_timeout = 60000 if is_spa else 30000  # 60s for SPAs, 30s for regular sites
    
    crawl_config = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS,
        wait_until=wait_until,
        page_timeout=page_timeout
    )

    # Start with a reasonable batch size
    current_batch_size = get_dynamic_batch_size()
    
    # Process URLs in dynamically sized batches
    i = 0
    while i < len(remaining_urls):
        # Check memory usage and adjust batch size
        memory_percent, available_gb = get_memory_usage()
        print(f"Memory usage: {memory_percent*100:.1f}%, Available: {available_gb:.1f}GB")
        
        # Adjust batch size based on memory usage
        current_batch_size = get_dynamic_batch_size()
        
        # Get current batch of URLs
        batch_urls = remaining_urls[i:i + current_batch_size]
        print(f"\nProcessing batch {i//current_batch_size + 1} ({len(batch_urls)} URLs, Batch size: {current_batch_size})")
        
        # Create new crawler instance for each batch
        crawler = AsyncWebCrawler(config=browser_config)
        await crawler.start()

        try:
            # Determine concurrency based on memory usage
            current_concurrency = get_dynamic_concurrency(max_concurrent)
            print(f"Using concurrency level: {current_concurrency}")
            
            # Create a semaphore to limit concurrency
            semaphore = asyncio.Semaphore(current_concurrency)
            
            async def process_url(url: str):
                async with semaphore:
                    try:
                        result = await crawl_with_rate_limit(crawler, url, crawl_config, api_config)
                        
                        if result and result.success:
                            print(f"Successfully crawled: {url}")
                            await process_and_store_document(
                                url, 
                                result.markdown_v2.raw_markdown, 
                                api_config.name
                            )
                            completed_urls.append(url)
                            await save_progress(api_config.name, completed_urls)
                        elif result:
                            # Sanitize error message before logging and printing
                            sanitized_error = sanitize_text(result.error_message)
                            logger.log_general_error(
                                api_config.name, 
                                url, 
                                f"Crawl failed: {sanitized_error}"
                            )
                            print(f"Failed: {url} - Error: {sanitized_error}")
                        else:
                            print(f"Failed after retries: {url}")
                    except Exception as e:
                        # Sanitize error message before logging and printing
                        sanitized_error = sanitize_text(str(e))
                        logger.log_general_error(api_config.name, url, f"Unexpected error: {sanitized_error}")
                        print(f"Error processing {url}: {sanitized_error}")
                    finally:
                        # Force cleanup after each URL to prevent memory leaks
                        try:
                            # Clear browser cache and perform garbage collection
                            if hasattr(crawler, '_page') and crawler._page:
                                await crawler._page.evaluate("""() => {
                                    window.performance.clearResourceTimings();
                                    if (window.gc) window.gc();
                                }""")
                            
                            # Force Python garbage collection
                            gc.collect()
                        except Exception as e:
                            # Sanitize error message before logging
                            sanitized_error = sanitize_text(str(e))
                            logger.log_general_error(api_config.name, url, f"Error during mid-URL cleanup: {sanitized_error}")
            
            # Process batch URLs in parallel with limited concurrency
            await asyncio.gather(*[process_url(url) for url in batch_urls])
            
            # Increment index for next batch
            i += len(batch_urls)
            
        except Exception as e:
            # Sanitize error message before logging
            sanitized_error = sanitize_text(str(e))
            logger.log_general_error(api_config.name, "batch_processing", f"Batch processing error: {sanitized_error}")
            # On error, still move forward to next batch to avoid getting stuck
            i += len(batch_urls)
        finally:
            # Cleanup browser after each batch
            await cleanup_browser(crawler, api_config)
            
            # Force garbage collection after each batch
            gc.collect()
            
        # Short pause between batches
        await asyncio.sleep(2)
        
        # Add additional memory cleanup between batches
        if should_reduce_resources():
            print("High memory usage detected, performing additional cleanup...")
            gc.collect()
            await asyncio.sleep(5)  # Allow OS to reclaim memory

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

async def crawl_api_documentation(api_config: CryptoApiConfig, urls: List[str], concurrency: int = 5):
    """
    Crawl API documentation for a specific API configuration.
    
    Args:
        api_config: The API configuration to use
        urls: List of URLs to crawl
        concurrency: Maximum number of concurrent requests
        
    Returns:
        None
    """
    print(f"Crawling documentation for {api_config.name} with {len(urls)} URLs...")
    await crawl_parallel(urls, api_config, concurrency)
    print(f"Finished crawling documentation for {api_config.name}")

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

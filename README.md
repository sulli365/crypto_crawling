# Crypto API Documentation Crawler

A system for crawling, processing, and storing cryptocurrency API documentation in a vector database for RAG (Retrieval-Augmented Generation) applications.

## Overview

This project extends the Pydantic AI documentation crawler to work with multiple cryptocurrency API documentation sites. It:

1. Crawls API documentation websites
2. Processes content into semantic chunks
3. Generates embeddings for each chunk
4. Stores everything in a Supabase vector database
5. Provides a RAG interface for querying the documentation

## Features

- Support for 20+ cryptocurrency API documentation sites
- Intelligent URL discovery (sitemap or crawling)
- Smart content chunking that preserves code blocks and context
- Rate limiting with exponential backoff for retries
- Error logging and reporting
- Configurable crawling depth and patterns
- API selection mechanism for targeted crawling

## Prerequisites

- Python 3.11+
- Supabase account and database
- OpenAI API key
- Crawl4AI library

## Installation

1. Clone the repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```
3. Set up environment variables:
   - Rename `.env.example` to `.env`
   - Add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_KEY=your_supabase_service_key
   LLM_MODEL=gpt-4o-mini  # or your preferred model
   ```

## Database Setup

Execute the SQL commands in `site_pages.sql` to:
1. Create the necessary tables
2. Enable vector similarity search
3. Set up Row Level Security policies

## Usage

### Generating API Configurations

Before crawling, you need to generate configurations for the APIs:

```bash
python generate_api_configs.py
```

This will:
1. Parse the `crypto-apis.md` file
2. Create a configuration for each API
3. Save them to `crypto_api_configs.json`

For more detailed analysis of each API (recommended):

```bash
python generate_api_configs.py --analyze
```

This will:
1. Visit each API documentation site
2. Check for sitemaps
3. Analyze URL patterns
4. Recommend crawling depth
5. Generate optimized configurations

### Exploring a Specific API

To analyze a single API documentation site:

```bash
python crawl_crypto_api_docs.py --explore https://api-site.com/docs
```

This will:
1. Check if the site has a sitemap
2. Analyze internal links
3. Recommend URL patterns
4. Suggest optimal crawling depth

### Crawling API Documentation

To crawl all configured APIs:

```bash
python crawl_crypto_api_docs.py
```

To crawl a specific API:

```bash
python crawl_crypto_api_docs.py --api CoinGecko
```

To crawl APIs in a specific category:

```bash
python crawl_crypto_api_docs.py --category market_data
```

To limit the number of APIs processed:

```bash
python crawl_crypto_api_docs.py --max-apis 3
```

To list all available APIs:

```bash
python crawl_crypto_api_docs.py --list
```

### Error Handling

Errors are logged to markdown files in the `error_logs` directory, organized by API name. Each error includes:
- Timestamp
- Error type (Rate Limit, Connection, Parsing, General)
- URL
- Error message

## Components

- `crawl_crypto_api_docs.py`: Main crawler script
- `crypto_api_config.py`: API configuration management
- `url_extractor.py`: URL discovery and filtering
- `error_logger.py`: Error logging and reporting
- `explore_api_url.py`: API documentation analysis
- `generate_api_configs.py`: Configuration generation

## Customization

### Adjusting Crawling Parameters

Edit `crypto_api_configs.json` to customize:
- `max_depth`: How deep to crawl (1-3 recommended)
- `delay_between_requests`: Seconds to wait between requests (higher = slower but less likely to hit rate limits)
- `max_retries`: Number of retry attempts for rate-limited requests
- `url_patterns`: Regex patterns to filter documentation URLs

### Adding New APIs

1. Add the API to `crypto-apis.md` following the existing format
2. Run `python generate_api_configs.py --analyze` to update configurations

## Troubleshooting

### Rate Limiting

If you encounter rate limiting:
1. Increase `delay_between_requests` in the API's configuration
2. Reduce `max_concurrent` in `crawl_parallel()` function
3. Try crawling during off-peak hours

### Missing Content

If documentation is missing:
1. Check the error logs for that API
2. Verify URL patterns are correct
3. Try increasing `max_depth` for more thorough crawling
4. Manually explore the site with `--explore` to identify issues

## Future Improvements

- Support for authentication-required documentation
- PDF documentation processing
- Automatic categorization of API endpoints
- Incremental updates to avoid re-crawling unchanged content

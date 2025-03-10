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

## Project Structure

The project follows a modern Python package structure with a src-layout approach:

```
crypto_crawler/
├── src/
│   └── crypto_crawler/
│       ├── __init__.py
│       ├── api/
│       │   ├── __init__.py
│       │   ├── config.py
│       │   └── expert.py
│       ├── crawling/
│       │   ├── __init__.py
│       │   ├── crawler.py
│       │   └── url_extractor.py
│       ├── utils/
│       │   ├── __init__.py
│       │   └── error_logger.py
│       ├── ui/
│       │   ├── __init__.py
│       │   └── streamlit_app.py
│       └── scripts/
│           ├── __init__.py
│           ├── explore_api_url.py
│           ├── generate_api_configs.py
│           ├── run_test.py
│           └── test_supabase_connection.py
├── config/
│   ├── crypto_api_configs.json
│   └── site_pages.sql
├── docs/
│   └── crypto-apis.md
├── error_logs/
├── main.py
├── setup.py
└── pyproject.toml
```

## Prerequisites

- Python 3.11+
- Supabase account and database
- OpenAI API key
- Crawl4AI library

## Installation

### Development Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On Unix/MacOS
   source venv/bin/activate
   ```
3. Install in development mode:
   ```bash
   pip install -e .
   ```

### User Installation

```bash
pip install git+https://github.com/yourusername/crypto_crawler.git
```

## Configuration

1. Set up environment variables:
   - Rename `.env.example` to `.env`
   - Add your API keys:
   ```
   OPENAI_API_KEY=your_openai_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_SERVICE_KEY=your_supabase_service_key
   LLM_MODEL=gpt-4o-mini  # or your preferred model
   ```

2. Database Setup:
   Execute the SQL commands in `config/site_pages.sql` to:
   - Create the necessary tables
   - Enable vector similarity search
   - Set up Row Level Security policies

## Usage

The project provides a command-line interface through the `main.py` script:

### Generating API Configurations

```bash
python main.py generate-configs
```

This will:
1. Parse the `docs/crypto-apis.md` file
2. Create a configuration for each API
3. Save them to `config/crypto_api_configs.json`

### Exploring a Specific API

```bash
python main.py explore https://api-site.com/docs --depth 2
```

This will:
1. Check if the site has a sitemap
2. Analyze internal links
3. Recommend URL patterns
4. Suggest optimal crawling depth

### Crawling API Documentation

To crawl all configured APIs:

```bash
python main.py crawl
```

To crawl a specific API:

```bash
python main.py crawl --api CoinGecko
```

To limit the number of URLs processed:

```bash
python main.py crawl --max-urls 50
```

To adjust concurrency:

```bash
python main.py crawl --concurrency 3
```

### Running the UI

```bash
python main.py ui
```

Or with a custom port:

```bash
python main.py ui --port 8502
```

## Command-line Scripts

After installation, the following command-line scripts are available:

- `crypto-crawler`: Main entry point with all commands
- `crypto-crawl`: Direct access to the crawler functionality
- `crypto-ui`: Launch the Streamlit UI

## Error Handling

Errors are logged to markdown files in the `error_logs` directory, organized by API name. Each error includes:
- Timestamp
- Error type (Rate Limit, Connection, Parsing, General)
- URL
- Error message

## Customization

### Adjusting Crawling Parameters

Edit `config/crypto_api_configs.json` to customize:
- `max_depth`: How deep to crawl (1-3 recommended)
- `delay_between_requests`: Seconds to wait between requests (higher = slower but less likely to hit rate limits)
- `max_retries`: Number of retry attempts for rate-limited requests
- `url_patterns`: Regex patterns to filter documentation URLs

### Adding New APIs

1. Add the API to `docs/crypto-apis.md` following the existing format
2. Run `python main.py generate-configs` to update configurations

## Troubleshooting

### Rate Limiting

If you encounter rate limiting:
1. Increase `delay_between_requests` in the API's configuration
2. Reduce `concurrency` when running the crawl command
3. Try crawling during off-peak hours

### Missing Content

If documentation is missing:
1. Check the error logs for that API
2. Verify URL patterns are correct
3. Try increasing `max_depth` for more thorough crawling
4. Manually explore the site with the explore command to identify issues

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

The project uses Black and isort for code formatting:

```bash
black src/
isort src/
```

## Future Improvements

- Support for authentication-required documentation
- PDF documentation processing
- Automatic categorization of API endpoints
- Incremental updates to avoid re-crawling unchanged content

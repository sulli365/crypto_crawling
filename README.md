# Crypto API Documentation Crawler

A specialized RAG (Retrieval-Augmented Generation) application designed to crawl, process, and store documentation from 20+ cryptocurrency API providers. This system enables users to query information about different cryptocurrencies through a unified interface, leveraging the power of large language models and vector search.

## Features

- Crawls and indexes documentation from 20+ cryptocurrency API providers
- Processes content with intelligent chunking that preserves code examples and context
- Stores processed content in a vector database for semantic search
- Provides an agentic RAG interface for querying cryptocurrency API information
- Supports natural language queries about cryptocurrency APIs

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
│           └── test_rag_agent.py
├── config/
│   ├── crypto_api_configs.json
│   └── site_pages.sql
├── docs/
│   └── crypto-apis.md
├── examples/
│   └── crawl4AI-examples/
├── error_logs/
├── memory-bank/
├── setup.py
└── pyproject.toml
```

## Installation

1. Clone the repository:

```bash
git clone https://github.com/yourusername/crypto-crawler.git
cd crypto-crawler
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
.\venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

3. Install the package in development mode:

```bash
pip install -e .
```

4. Set up environment variables:

Create a `.env` file in the project root with the following variables:

```
OPENAI_API_KEY=your_openai_api_key
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_KEY=your_supabase_service_key
LLM_MODEL=gpt-4o-mini  # or preferred model
```

5. Set up the database:

Run the SQL scripts in the `config` directory to set up the database schema and functions.

## Usage

### Crawling API Documentation

```bash
python -m crypto_crawler crawl --api CoinGecko
```

### Running the UI

```bash
python -m crypto_crawler ui
```

### Testing the RAG Agent

```bash
python -m crypto_crawler.scripts.test_rag_agent
```

## Database Schema

The system uses a Supabase database with the following schema:

```sql
create table crypto_api_site_pages (
    id bigserial primary key,
    url varchar not null,
    chunk_number integer not null,
    title varchar not null,
    summary varchar not null,
    content text not null,
    metadata jsonb not null default '{}'::jsonb,
    embedding vector(1536),
    created_at timestamp with time zone default timezone('utc'::text, now()) not null,
    
    unique(url, chunk_number)
);
```

## RAG Agent

The RAG agent provides the following tools:

- `retrieve_relevant_documentation`: Retrieve relevant documentation chunks based on a query
- `list_documentation_pages`: List available documentation pages
- `get_page_content`: Get the full content of a specific documentation page
- `list_available_apis`: List all available cryptocurrency APIs
- `compare_api_endpoints`: Compare similar endpoints across different APIs

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

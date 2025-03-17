# Technical Context

## Technology Stack

The Crypto API Documentation Crawler is built on a modern technology stack designed for performance, scalability, and maintainability:

### Core Technologies

1. **Python 3.11+**: The primary programming language for the entire system.
2. **Crawl4AI**: A specialized web crawling library optimized for AI applications.
3. **OpenAI API**: Used for generating embeddings and powering the RAG agent.
4. **Supabase**: Vector database for storing and retrieving documentation chunks.
5. **Streamlit**: Frontend framework for the user interface.
6. **Pydantic-AI**: Framework for building tool-based AI agents.

### Key Libraries and Dependencies

1. **Web Crawling and Processing**
   - `Crawl4AI`: High-performance web crawling with browser automation
   - `BeautifulSoup4`: HTML parsing and manipulation
   - `Playwright`: Browser automation for JavaScript-heavy sites
   - `aiohttp`: Asynchronous HTTP requests
   - `requests`: Synchronous HTTP requests for simpler operations
   - `psutil`: Process and system utilities for resource management

2. **Natural Language Processing**
   - `OpenAI API`: Embeddings and LLM capabilities
   - `tiktoken`: Token counting for chunking
   - `nltk`: Natural language toolkit for text processing

3. **Database and Storage**
   - `Supabase`: PostgreSQL database with vector extensions
   - `pgvector`: Vector similarity search in PostgreSQL
   - `asyncpg`: Asynchronous PostgreSQL client

4. **User Interface**
   - `Streamlit`: Interactive web application framework
   - `pydantic-ai`: Agent framework for the RAG component

5. **Utilities and Infrastructure**
   - `asyncio`: Asynchronous I/O for concurrent operations
   - `dotenv`: Environment variable management
   - `logfire`: Structured logging
   - `dataclasses`: Structured data modeling
   - `argparse`: Command-line argument parsing
   - `json`: JSON data handling
   - `xml.etree`: XML parsing for sitemaps

## Development Environment

### Local Development Setup

1. **Python Environment**
   - Python 3.11+ with virtual environment
   - Dependencies installed via `pip install -r requirements.txt`
   - Package installation in development mode: `pip install -e .`

2. **Environment Variables**
   - `.env` file with the following variables:
     ```
     OPENAI_API_KEY=your_openai_api_key
     SUPABASE_URL=your_supabase_url
     SUPABASE_SERVICE_KEY=your_supabase_service_key
     LLM_MODEL=gpt-4o-mini  # or preferred model
     ```

3. **Database Setup**
   - Supabase project with pgvector extension enabled
   - Tables created using the SQL in `config/site_pages.sql`
   - Database functions deployed from `config/db_functions.sql`
   - API source functions from `config/get_distinct_api_sources.sql`

### Project Structure

1. **Package Organization**
   - src-layout with `crypto_crawler` package
   - Modular organization with subpackages for different components
   - Entry points defined in `setup.py`
   - Main CLI interface in `main.py`

2. **Configuration Management**
   - API configurations in JSON format
   - SQL files in `config/` directory
   - Documentation in `docs/` directory
   - Error logs in `error_logs/` directory

### Deployment Options

1. **Local Deployment**
   - Run the Streamlit UI locally with `streamlit run src/crypto_crawler/ui/streamlit_app.py`
   - Crawling and processing run via CLI: `python main.py crawl`
   - Database cleanup via CLI: `python main.py cleanup`

2. **Docker Deployment**
   - Docker and docker-compose configuration available
   - Containerized deployment for consistent environments

3. **Cloud Deployment Options**
   - Streamlit Cloud for the UI component
   - Cloud Functions/Lambdas for the crawling component
   - Supabase for the database component

## External Dependencies

### API Services

1. **OpenAI API**
   - Used for:
     - Generating embeddings (text-embedding-3-small)
     - Extracting titles and summaries (gpt-4o-mini)
     - Powering the RAG agent (gpt-4o-mini)
   - Rate limits and quotas apply based on OpenAI pricing tier

2. **Supabase**
   - Used for:
     - Vector storage and retrieval
     - Metadata storage
     - Row-level security
     - Database functions for efficient queries
   - Performance depends on chosen Supabase tier

### Third-Party Documentation Sites

The system interacts with 20+ cryptocurrency API documentation sites, each with its own:
- Rate limiting policies
- Content structure
- Authentication requirements
- JavaScript dependencies
- Robots.txt restrictions
- Sitemap availability

## Technical Constraints

1. **Rate Limiting**
   - Most API documentation sites implement rate limiting
   - Crawling must respect these limits to avoid being blocked
   - Exponential backoff and retry mechanisms are essential
   - Different APIs have different rate limit policies

2. **JavaScript-Heavy Sites**
   - Many modern documentation sites rely heavily on JavaScript
   - Full browser rendering (via Playwright) is required
   - Increases resource usage compared to simple HTTP requests
   - Single-page applications (SPAs) require special handling:
     - Adaptive wait conditions ("networkidle" vs "domcontentloaded")
     - Increased page timeouts for complex SPAs
     - Removal of problematic browser flags that interfere with SPA rendering
     - Automatic detection of SPAs based on URL patterns and site characteristics
     - Dynamic configuration adjustments based on site type

3. **Memory Usage**
   - Browser automation is memory-intensive
   - Dynamic batch sizing and concurrency based on real-time memory monitoring
   - Adaptive resource allocation with configurable thresholds (MEMORY_THRESHOLD, SAFETY_BUFFER)
   - Multi-stage browser cleanup process (graceful shutdown, forced termination, temp directory cleanup)
   - Text sanitization to handle problematic Unicode characters that cause browser hangs
   - Forced garbage collection between batches to prevent memory leaks
   - Process monitoring using psutil for memory usage statistics

4. **Token Limits**
   - OpenAI models have context window limits
   - Chunking strategy must balance context preservation with token limits
   - Embedding generation has its own rate limits and quotas
   - Title and summary generation requires efficient prompt design

5. **Database Performance**
   - Vector similarity search can be computationally expensive
   - Indexing is crucial for acceptable query performance
   - Connection pooling helps manage concurrent database access
   - Metadata filtering efficiency impacts query performance

## Security Considerations

1. **API Keys**
   - OpenAI and Supabase keys must be securely stored
   - Environment variables used for local development
   - Secrets management for production deployment
   - No hardcoded credentials in source code

2. **Data Privacy**
   - Only publicly available documentation is crawled
   - No user data is collected beyond query history
   - Row-level security in Supabase controls access
   - Clear attribution of information sources

3. **Rate Limit Compliance**
   - System designed to respect website rate limits
   - Configurable delays between requests
   - User-agent identification follows best practices
   - Exponential backoff for rate limit errors

4. **Error Handling**
   - Categorized error logging for security-related issues
   - No sensitive information in error logs
   - Proper exception handling to prevent information leakage
   - Secure error reporting

## Performance Considerations

1. **Crawling Efficiency**
   - Parallel processing with configurable concurrency
   - Session reuse to minimize browser startup overhead
   - Caching to avoid redundant requests
   - Batch processing with progress tracking
   - Resumable crawls for reliability

2. **Database Optimization**
   - Vector indexing for faster similarity search
   - Metadata indexing for efficient filtering
   - Connection pooling for better resource utilization
   - Duplicate prevention and cleanup

3. **Memory Management**
   - Dynamic batch sizing based on available system memory
   - Real-time memory usage monitoring with configurable thresholds
   - Proactive resource cleanup between batches
   - Enhanced browser cleanup with multi-stage process
   - Character sanitization to prevent browser hangs on problematic Unicode
   - Forced garbage collection at strategic points in the pipeline
   - Chrome process termination for hanging browser instances

4. **Response Time**
   - Vector search optimization for sub-second query response
   - Response streaming for better user experience
   - Caching frequently accessed documentation
   - Efficient metadata filtering

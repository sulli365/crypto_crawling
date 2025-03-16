# Technical Context

## Technology Stack

The Crypto API Documentation Crawler is built on a modern technology stack designed for performance, scalability, and maintainability:

### Core Technologies

1. **Python 3.11+**: The primary programming language for the entire system.
2. **Crawl4AI**: A specialized web crawling library optimized for AI applications.
3. **OpenAI API**: Used for generating embeddings and powering the RAG agent.
4. **Supabase**: Vector database for storing and retrieving documentation chunks.
5. **Streamlit**: Frontend framework for the user interface.

### Key Libraries and Dependencies

1. **Web Crawling and Processing**
   - `Crawl4AI`: High-performance web crawling with browser automation
   - `BeautifulSoup4`: HTML parsing and manipulation
   - `Playwright`: Browser automation for JavaScript-heavy sites
   - `aiohttp`: Asynchronous HTTP requests

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

## Development Environment

### Local Development Setup

1. **Python Environment**
   - Python 3.11+ with virtual environment
   - Dependencies installed via `pip install -r requirements.txt`

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
   - Tables created using the SQL in `site_pages.sql`

### Deployment Options

1. **Local Deployment**
   - Run the Streamlit UI locally with `streamlit run streamlit_ui.py`
   - Crawling and processing run as separate processes

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
   - Performance depends on chosen Supabase tier

### Third-Party Documentation Sites

The system interacts with 20+ cryptocurrency API documentation sites, each with its own:
- Rate limiting policies
- Content structure
- Authentication requirements
- JavaScript dependencies
- Robots.txt restrictions

## Technical Constraints

1. **Rate Limiting**
   - Most API documentation sites implement rate limiting
   - Crawling must respect these limits to avoid being blocked
   - Exponential backoff and retry mechanisms are essential

2. **JavaScript-Heavy Sites**
   - Many modern documentation sites rely heavily on JavaScript
   - Full browser rendering (via Playwright) is required
   - Increases resource usage compared to simple HTTP requests

3. **Memory Usage**
   - Browser automation is memory-intensive
   - Parallel crawling must be carefully managed to avoid OOM errors
   - Batch processing is used to control memory consumption

4. **Token Limits**
   - OpenAI models have context window limits
   - Chunking strategy must balance context preservation with token limits
   - Embedding generation has its own rate limits and quotas

5. **Database Performance**
   - Vector similarity search can be computationally expensive
   - Indexing is crucial for acceptable query performance
   - Connection pooling helps manage concurrent database access

## Security Considerations

1. **API Keys**
   - OpenAI and Supabase keys must be securely stored
   - Environment variables used for local development
   - Secrets management for production deployment

2. **Data Privacy**
   - Only publicly available documentation is crawled
   - No user data is collected beyond query history
   - Row-level security in Supabase controls access

3. **Rate Limit Compliance**
   - System designed to respect website rate limits
   - Configurable delays between requests
   - User-agent identification follows best practices

## Performance Considerations

1. **Crawling Efficiency**
   - Parallel processing with configurable concurrency
   - Session reuse to minimize browser startup overhead
   - Caching to avoid redundant requests

2. **Database Optimization**
   - Vector indexing for faster similarity search
   - Metadata indexing for efficient filtering
   - Connection pooling for better resource utilization

3. **Memory Management**
   - Batch processing to control memory usage
   - Resource monitoring during crawling
   - Garbage collection optimization

4. **Response Time**
   - Vector search optimization for sub-second query response
   - Response streaming for better user experience
   - Caching frequently accessed documentation

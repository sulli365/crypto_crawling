# Active Context

## Current Focus

The project is currently in the early development phase, with a focus on establishing the core infrastructure for crawling, processing, and storing cryptocurrency API documentation. The immediate priorities are:

1. **Extending API Coverage**: Building on the successful implementation with CoinGecko API to cover all 20+ cryptocurrency APIs.
2. **Refining the RAG Agent**: Updating the agent to properly query and retrieve information from the crypto API documentation database.
3. **Enhancing the User Interface**: Improving the Streamlit UI for a better user experience.
4. **Database Function Deployment**: Deploying SQL functions for duplicate detection and vector search.

## Recent Developments

### Completed

1. **Project Structure Refinement**:
   - Implemented proper Python package structure with src layout
   - Created modular organization with api, crawling, utils, ui, and scripts subpackages
   - Added setup.py and pyproject.toml for package installation
   - Updated imports to reflect the new structure
   - Moved configuration files to the config/ directory
   - Moved documentation to the docs/ directory
   - Created a main entry point script at the project root with comprehensive CLI

2. **Duplicate Prevention and Cleanup**:
   - Added unique constraint on url and chunk_number
   - Implemented duplicate detection during insertion
   - Created database cleanup functions for existing duplicates
   - Added batch processing with progress tracking
   - Improved browser cleanup with retry logic

3. **Crawling Improvements**:
   - Implemented progress tracking and resumable crawls
   - Added batch processing to control memory usage
   - Enhanced error handling with categorized logging
   - Improved browser cleanup with retry logic
   - Added exponential backoff for rate limit errors

4. **RAG Agent Enhancement**:
   - Implemented tool-based architecture using pydantic-ai
   - Created specialized tools for API documentation retrieval
   - Added API comparison capabilities
   - Implemented documentation listing functionality

### In Progress

1. **Multi-API Support**:
   - Testing crawling with additional cryptocurrency APIs
   - Refining rate limiting and retry mechanisms
   - Optimizing parallel crawling for better performance
   - Implementing API-specific chunking parameters

2. **Database Function Deployment**:
   - Deploying SQL functions for duplicate detection
   - Setting up vector search functions
   - Implementing efficient metadata filtering
   - Testing database performance with larger datasets

3. **Streamlit UI Enhancement**:
   - Improving response formatting
   - Adding API selection dropdown
   - Implementing source attribution
   - Enhancing message history management

## Key Decisions

1. **Chunking Strategy**:
   - Decision: Implement intelligent chunking that preserves code blocks and context
   - Rationale: API documentation often contains code examples and structured information that should be kept together
   - Implementation: Custom chunking algorithm that respects code blocks, paragraphs, and semantic boundaries

2. **Database Schema**:
   - Decision: Use a single table with metadata filtering rather than separate tables per API
   - Rationale: Simplifies vector search across all APIs while allowing filtering by source
   - Implementation: JSON metadata field with API name, crawl timestamp, and other attributes

3. **Crawling Approach**:
   - Decision: Support both sitemap-based and crawl-based URL discovery
   - Rationale: Different API documentation sites have different structures; some provide sitemaps while others require crawling
   - Implementation: Dual-strategy approach with configurable parameters

4. **Error Handling**:
   - Decision: Implement categorized error logging with markdown output
   - Rationale: Different error types require different handling; markdown format improves readability
   - Implementation: ErrorLogger class with specialized methods for different error types

5. **Project Structure**:
   - Decision: Adopt a src-layout Python package structure
   - Rationale: Follows modern Python packaging best practices and improves maintainability
   - Implementation: Organized code into logical modules (api, crawling, utils, ui, scripts)
   - Added proper entry points for command-line scripts

6. **Agent Architecture**:
   - Decision: Use pydantic-ai for the RAG agent implementation
   - Rationale: Provides a structured, tool-based approach for agent development
   - Implementation: Created specialized tools for documentation retrieval and API comparison

## Current Challenges

1. **Database Functions Setup**:
   - Need to execute SQL functions for duplicate detection
   - Supabase REST API limitations for DDL statements
   - Environment variable loading in scripts
   - Testing database functions with larger datasets

2. **Rate Limiting Variability**:
   - Different API documentation sites have different rate limiting policies
   - Need to fine-tune delay parameters for each API
   - Implementing adaptive rate limiting based on response headers
   - Handling temporary IP blocks from aggressive crawling

3. **JavaScript-Heavy Sites**:
   - Some documentation sites rely heavily on JavaScript for content rendering
   - Requires full browser automation, increasing resource usage
   - Exploring optimizations to reduce memory consumption
   - Handling single-page applications with dynamic content loading

4. **Content Structure Diversity**:
   - API documentation varies widely in structure and organization
   - Chunking strategy may need refinement for different documentation styles
   - Considering API-specific chunking parameters
   - Handling complex nested documentation structures

5. **Memory Management**:
   - Browser automation is memory-intensive
   - Need to optimize batch size and concurrency settings
   - Implementing better resource cleanup
   - Monitoring memory usage during long crawling sessions

## Next Steps

### Immediate (Next 1-2 Weeks)

1. **Deploy Database Functions**:
   - Execute SQL functions for duplicate detection
   - Set up vector search functions
   - Test with larger datasets
   - Optimize query performance

2. **Complete Multi-API Crawling**:
   - Test and refine crawling for all 20+ cryptocurrency APIs
   - Optimize crawling parameters for each API
   - Implement monitoring for crawling progress
   - Fine-tune rate limiting for each API

3. **Enhance RAG Agent**:
   - Test all implemented tools with real queries
   - Improve response formatting and source attribution
   - Implement API comparison capabilities
   - Add code example extraction

4. **Improve User Interface**:
   - Enhance the Streamlit UI with better formatting
   - Add filtering options for specific APIs
   - Implement source attribution for responses
   - Add visualization for API capabilities

### Medium-Term (Next 2-4 Weeks)

1. **Incremental Updates**:
   - Implement a system for updating documentation without full recrawling
   - Track changes in API documentation over time
   - Optimize update frequency based on API update patterns
   - Add versioning for documentation chunks

2. **Advanced Query Capabilities**:
   - Add support for code generation based on API documentation
   - Implement comparison tools for different APIs
   - Develop specialized query templates for common use cases
   - Add support for multi-step reasoning

3. **Performance Optimization**:
   - Profile and optimize the entire pipeline
   - Implement caching for frequently accessed documentation
   - Refine vector search parameters for better relevance
   - Optimize memory usage during crawling

### Long-Term (Beyond 4 Weeks)

1. **Authentication Support**:
   - Add support for crawling documentation behind authentication
   - Implement secure credential management
   - Test with APIs requiring authentication
   - Handle session-based authentication

2. **PDF Documentation**:
   - Add support for processing PDF documentation
   - Implement PDF-specific extraction and chunking strategies
   - Test with APIs that provide documentation in PDF format
   - Handle complex PDF layouts and tables

3. **API Categorization**:
   - Implement automatic categorization of API endpoints
   - Develop a taxonomy for cryptocurrency API capabilities
   - Enable filtering and searching by capability category
   - Create visualization of API ecosystem

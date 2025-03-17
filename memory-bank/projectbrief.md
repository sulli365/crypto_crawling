# Crypto API Documentation Crawler - Project Brief

## Project Overview

The Crypto API Documentation Crawler is a specialized RAG (Retrieval-Augmented Generation) application designed to crawl, process, and store documentation from 20+ cryptocurrency API providers. This system enables users to query information about different cryptocurrencies through a unified interface, leveraging the power of large language models and vector search.

## Core Objectives

1. **Comprehensive API Coverage**: Crawl and index documentation from 20+ cryptocurrency API providers.
2. **Intelligent Content Processing**: Extract, chunk, and process API documentation in a way that preserves context and code examples.
3. **Efficient Vector Storage**: Store processed content in a vector database for semantic search capabilities.
4. **Agentic RAG Interface**: Provide an intelligent interface for querying cryptocurrency API information.
5. **Scalable Architecture**: Design a system that can handle the addition of new API providers with minimal configuration.
6. **Robust Resource Management**: Implement dynamic memory management and cleanup processes to ensure stable operation during intensive crawling operations.

## Key Requirements

### Functional Requirements

1. **API Documentation Crawling**
   - Discover and extract documentation URLs from cryptocurrency API websites
   - Support both sitemap-based and crawl-based URL discovery
   - Implement rate limiting and retry mechanisms to avoid overloading API servers
   - Filter URLs to focus on relevant documentation pages

2. **Content Processing**
   - Convert HTML to markdown while preserving structure
   - Chunk content intelligently to maintain context and code examples
   - Generate embeddings for vector search
   - Extract titles and summaries for improved retrieval

3. **Storage and Retrieval**
   - Store processed content in Supabase vector database
   - Implement efficient vector search for relevant content retrieval
   - Maintain metadata for filtering and organization

4. **User Interface**
   - Provide a Streamlit-based interface for querying API information
   - Support natural language queries about cryptocurrency APIs
   - Display relevant documentation snippets with source attribution

### Non-Functional Requirements

1. **Performance**
   - Optimize crawling speed with parallel processing
   - Minimize database query latency for real-time responses
   - Efficient memory usage during crawling and processing with dynamic resource allocation
   - Adaptive batch sizing and concurrency based on system memory availability
   - Proactive memory monitoring and cleanup to prevent resource exhaustion

2. **Reliability**
   - Implement robust error handling and logging
   - Ensure system resilience against network failures and rate limits
   - Validate data integrity throughout the pipeline
   - Handle problematic characters and encoding issues that may cause browser hangs
   - Implement multi-stage cleanup processes to recover from browser failures

3. **Maintainability**
   - Modular architecture for easy extension
   - Comprehensive documentation of code and processes
   - Configuration-driven approach to adding new APIs

## Success Criteria

1. Successfully crawl and process documentation from all 20+ cryptocurrency APIs
2. Achieve high relevance in query responses (measured by user feedback)
3. Maintain system stability under various query loads
4. Enable users to find relevant API information faster than manual searching

## Project Constraints

1. Must use Crawl4AI for web crawling
2. Must use Supabase for vector storage
3. Must use OpenAI for embeddings and LLM capabilities
4. Must respect API rate limits and terms of service

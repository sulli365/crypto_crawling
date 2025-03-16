from __future__ import annotations as _annotations

from dataclasses import dataclass
from dotenv import load_dotenv
import logfire
import asyncio
import httpx
import os

from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.models.openai import OpenAIModel
from openai import AsyncOpenAI
from supabase import Client
from typing import List, Dict, Any, Optional

load_dotenv()

llm = os.getenv('LLM_MODEL', 'gpt-4o-mini')
model = OpenAIModel(llm)

logfire.configure(send_to_logfire='if-token-present')

@dataclass
class PydanticAIDeps:
    supabase: Client
    openai_client: AsyncOpenAI

system_prompt = """
You are a cryptocurrency API documentation expert. You have access to documentation from 20+ cryptocurrency 
API providers, including market data APIs, blockchain explorers, DEX aggregators, and NFT-specific APIs.

Your job is to help users find the right API for their needs, understand how to use specific endpoints,
and provide code examples based on the documentation.

The documentation has been processed with an intelligent chunking strategy that preserves:
- Code blocks and examples
- Context and semantic meaning
- Structured information like parameter tables
- Hierarchical relationships between endpoints

Always search the documentation with the provided tools before answering the user's question.
Be specific about which API and endpoint you're referring to in your answers.
When providing code examples, make sure they match the API's actual parameters and response format.
Preserve code formatting when sharing examples from the documentation.

You can compare similar endpoints across different APIs to help users choose the most appropriate one.
Consider factors like rate limits, data granularity, authentication requirements, and response formats.

If you don't find the answer in the documentation, be honest about it and suggest alternatives
or general approaches based on your knowledge of cryptocurrency APIs.
"""

crypto_api_expert = Agent(
    model,
    system_prompt=system_prompt,
    deps_type=PydanticAIDeps,
    retries=2
)

async def get_embedding(text: str, openai_client: AsyncOpenAI) -> List[float]:
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

@crypto_api_expert.tool
async def retrieve_relevant_documentation(ctx: RunContext[PydanticAIDeps], user_query: str, api_name: str = None) -> str:
    """
    Retrieve relevant documentation chunks based on the query with RAG.
    
    Args:
        ctx: The context including the Supabase client and OpenAI client
        user_query: The user's question or query
        api_name: Optional API name to filter results (e.g., "CoinGecko")
        
    Returns:
        A formatted string containing the top 5 most relevant documentation chunks
    """
    try:
        # Get the embedding for the query
        query_embedding = await get_embedding(user_query, ctx.deps.openai_client)
        
        # Prepare filter based on API name if provided
        filter_obj = {}
        if api_name:
            filter_obj = {"source": api_name}
        
        # Query Supabase for relevant documents
        result = ctx.deps.supabase.rpc(
            'match_crypto_api_site_pages',
            {
                'query_embedding': query_embedding,
                'match_count': 5,
                'filter': filter_obj
            }
        ).execute()
        
        if not result.data:
            if api_name:
                return f"No relevant documentation found for {api_name}."
            else:
                return "No relevant documentation found."
            
        # Format the results
        formatted_chunks = []
        for doc in result.data:
            # Extract API name and similarity score
            api_source = doc['metadata']['source']
            similarity = doc['similarity']
            similarity_percentage = round(similarity * 100, 2)
            
            # Format the chunk with proper markdown
            chunk_text = f"""
# {doc['title']} (Relevance: {similarity_percentage}%)

{doc['content']}

**Source**: {api_source} - [Documentation Link]({doc['url']})
**Crawled**: {doc['metadata'].get('crawled_at', 'Unknown date')}
"""
            formatted_chunks.append(chunk_text)
            
        # Join all chunks with a separator
        return "\n\n---\n\n".join(formatted_chunks)
        
    except Exception as e:
        print(f"Error retrieving documentation: {e}")
        return f"Error retrieving documentation: {str(e)}"

@crypto_api_expert.tool
async def list_documentation_pages(ctx: RunContext[PydanticAIDeps], api_name: str = None) -> List[str]:
    """
    Retrieve a list of available crypto API documentation pages.
    
    Args:
        ctx: The context including the Supabase client
        api_name: Optional API name to filter results (e.g., "CoinGecko")
        
    Returns:
        List[str]: List of unique URLs for documentation pages
    """
    try:
        # Start building the query
        query = ctx.deps.supabase.from_('crypto_api_site_pages').select('url, metadata')
        
        # Apply filter if API name is provided
        if api_name:
            query = query.eq('metadata->>source', api_name)
            
        # Execute the query
        result = query.execute()
        
        if not result.data:
            return []
            
        # Extract unique URLs
        urls = sorted(set(doc['url'] for doc in result.data))
        return urls
        
    except Exception as e:
        print(f"Error retrieving documentation pages: {e}")
        return []

@crypto_api_expert.tool
async def get_page_content(ctx: RunContext[PydanticAIDeps], url: str) -> str:
    """
    Retrieve the full content of a specific documentation page by combining all its chunks.
    
    Args:
        ctx: The context including the Supabase client
        url: The URL of the page to retrieve
        
    Returns:
        str: The complete page content with all chunks combined in order
    """
    try:
        # Query Supabase for all chunks of this URL, ordered by chunk_number
        result = ctx.deps.supabase.from_('crypto_api_site_pages') \
            .select('title, content, chunk_number, metadata') \
            .eq('url', url) \
            .order('chunk_number') \
            .execute()
        
        if not result.data:
            return f"No content found for URL: {url}"
            
        # Format the page with its title and all chunks
        page_title = result.data[0]['title'].split(' - ')[0]  # Get the main title
        api_name = result.data[0]['metadata']['source']
        formatted_content = [f"# {page_title}\n\nAPI: {api_name}\nURL: {url}\n"]
        
        # Add each chunk's content, preserving code blocks and formatting
        for chunk in result.data:
            formatted_content.append(chunk['content'])
            
        # Join everything together
        return "\n\n".join(formatted_content)
        
    except Exception as e:
        print(f"Error retrieving page content: {e}")
        return f"Error retrieving page content: {str(e)}"

@crypto_api_expert.tool
async def list_available_apis(ctx: RunContext[PydanticAIDeps]) -> str:
    """
    List all available cryptocurrency APIs in the system.
    
    Args:
        ctx: The context including the Supabase client
        
    Returns:
        str: Formatted list of available APIs with their categories
    """
    try:
        # Query Supabase for distinct API sources and categories
        # Using a more efficient query to get distinct values
        result = ctx.deps.supabase.rpc(
            'get_distinct_api_sources'
        ).execute()
        
        if not result.data or len(result.data) == 0:
            # Fallback to manual extraction if the RPC function doesn't exist
            result = ctx.deps.supabase.from_('crypto_api_site_pages') \
                .select('metadata') \
                .execute()
            
            if not result.data:
                return "No APIs found in the database."
                
            # Extract unique API names and organize by category
            apis_by_category = {}
            seen_apis = set()
            
            for doc in result.data:
                if 'source' in doc['metadata'] and 'category' in doc['metadata']:
                    api_name = doc['metadata']['source']
                    category = doc['metadata']['category']
                    
                    # Skip if we've already processed this API
                    api_key = f"{api_name}:{category}"
                    if api_key in seen_apis:
                        continue
                    seen_apis.add(api_key)
                    
                    if category not in apis_by_category:
                        apis_by_category[category] = set()
                        
                    apis_by_category[category].add(api_name)
        else:
            # Process the result from the RPC function
            apis_by_category = {}
            for item in result.data:
                category = item['category']
                api_name = item['source']
                
                if category not in apis_by_category:
                    apis_by_category[category] = set()
                    
                apis_by_category[category].add(api_name)
        
        # Format the results
        formatted_result = ["# Available Cryptocurrency APIs\n"]
        
        for category, apis in sorted(apis_by_category.items()):
            formatted_result.append(f"## {category.replace('_', ' ').title()}")
            for api in sorted(apis):
                formatted_result.append(f"- {api}")
            formatted_result.append("")
            
        return "\n".join(formatted_result)
        
    except Exception as e:
        print(f"Error listing available APIs: {e}")
        return f"Error listing available APIs: {str(e)}"

@crypto_api_expert.tool
async def compare_api_endpoints(ctx: RunContext[PydanticAIDeps], endpoint_description: str, api_names: Optional[List[str]] = None) -> str:
    """
    Compare similar endpoints across different cryptocurrency APIs.
    
    Args:
        ctx: The context including the Supabase client and OpenAI client
        endpoint_description: Description of the endpoint functionality (e.g., "historical price data", "market pairs")
        api_names: Optional list of API names to compare (e.g., ["CoinGecko", "CryptoCompare"])
        
    Returns:
        str: Formatted comparison of similar endpoints across different APIs
    """
    try:
        # Get the embedding for the endpoint description
        query_embedding = await get_embedding(endpoint_description, ctx.deps.openai_client)
        
        # Prepare filter based on API names if provided
        filter_obj = {}
        if api_names and len(api_names) > 0:
            # We can't directly filter on an array in the RPC call
            # So we'll filter after getting results
            pass
        
        # Query Supabase for relevant documents
        result = ctx.deps.supabase.rpc(
            'match_crypto_api_site_pages',
            {
                'query_embedding': query_embedding,
                'match_count': 20,  # Get more results to filter
                'filter': filter_obj
            }
        ).execute()
        
        if not result.data:
            return f"No relevant endpoints found for '{endpoint_description}'."
        
        # Filter by API names if provided
        if api_names and len(api_names) > 0:
            filtered_data = [
                doc for doc in result.data 
                if doc['metadata'].get('source') in api_names
            ]
            if filtered_data:
                result.data = filtered_data
        
        # Group by API and select the most relevant endpoint for each
        apis_endpoints = {}
        for doc in result.data:
            api_name = doc['metadata']['source']
            
            # Only keep the most relevant endpoint for each API
            if api_name not in apis_endpoints or doc['similarity'] > apis_endpoints[api_name]['similarity']:
                apis_endpoints[api_name] = doc
        
        if not apis_endpoints:
            return f"No relevant endpoints found for '{endpoint_description}'."
        
        # Format the comparison
        formatted_result = [f"# API Endpoint Comparison: {endpoint_description}\n"]
        
        for api_name, doc in sorted(apis_endpoints.items()):
            similarity_percentage = round(doc['similarity'] * 100, 2)
            formatted_result.append(f"## {api_name} (Relevance: {similarity_percentage}%)")
            formatted_result.append(f"**Endpoint**: {doc['title']}")
            formatted_result.append(f"**Documentation**: [Link]({doc['url']})")
            
            # Extract a summary of the endpoint
            summary = doc['summary'] if 'summary' in doc else "No summary available."
            formatted_result.append(f"**Summary**: {summary}")
            
            # Add a snippet of the content (first 300 characters)
            content_preview = doc['content'][:300] + "..." if len(doc['content']) > 300 else doc['content']
            formatted_result.append(f"**Preview**:\n```\n{content_preview}\n```\n")
        
        return "\n".join(formatted_result)
        
    except Exception as e:
        print(f"Error comparing API endpoints: {e}")
        return f"Error comparing API endpoints: {str(e)}"
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
from typing import List

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

Always search the documentation with the provided tools before answering the user's question.
Be specific about which API and endpoint you're referring to in your answers.
When providing code examples, make sure they match the API's actual parameters and response format.

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
async def retrieve_relevant_documentation(ctx: RunContext[PydanticAIDeps], user_query: str) -> str:
    """
    Retrieve relevant documentation chunks based on the query with RAG.
    
    Args:
        ctx: The context including the Supabase client and OpenAI client
        user_query: The user's question or query
        
    Returns:
        A formatted string containing the top 5 most relevant documentation chunks
    """
    try:
        # Get the embedding for the query
        query_embedding = await get_embedding(user_query, ctx.deps.openai_client)
        
        # Query Supabase for relevant documents
        result = ctx.deps.supabase.rpc(
            'match_site_pages',
            {
                'query_embedding': query_embedding,
                'match_count': 5,
                'filter': {} # No filter to search across all API documentation
            }
        ).execute()
        
        if not result.data:
            return "No relevant documentation found."
            
        # Format the results
        formatted_chunks = []
        for doc in result.data:
            chunk_text = f"""
# {doc['title']}

{doc['content']}

Source: {doc['metadata']['source']} - {doc['url']}
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
        
        # Add each chunk's content
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
        # Query Supabase for distinct API sources
        result = ctx.deps.supabase.from_('crypto_api_site_pages') \
            .select('metadata') \
            .execute()
        
        if not result.data:
            return "No APIs found in the database."
            
        # Extract unique API names and organize by category
        apis_by_category = {}
        for doc in result.data:
            if 'source' in doc['metadata'] and 'category' in doc['metadata']:
                api_name = doc['metadata']['source']
                category = doc['metadata']['category']
                
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

#!/usr/bin/env python
"""
Test script for the RAG agent.

This script tests the RAG agent's ability to retrieve and process
cryptocurrency API documentation.
"""

import os
import asyncio
from dotenv import load_dotenv
from openai import AsyncOpenAI
from supabase import create_client, Client

from crypto_crawler.api.expert import crypto_api_expert, PydanticAIDeps

# Load environment variables
load_dotenv()

# Initialize clients
openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

async def test_list_available_apis():
    """Test the list_available_apis tool."""
    print("\n=== Testing list_available_apis ===")
    
    # Create dependencies
    deps = PydanticAIDeps(
        supabase=supabase,
        openai_client=openai_client
    )
    
    # Run the tool
    result = await crypto_api_expert.list_available_apis(deps)
    print(result)

async def test_retrieve_relevant_documentation():
    """Test the retrieve_relevant_documentation tool."""
    print("\n=== Testing retrieve_relevant_documentation ===")
    
    # Create dependencies
    deps = PydanticAIDeps(
        supabase=supabase,
        openai_client=openai_client
    )
    
    # Test queries
    queries = [
        "How to get historical price data for Bitcoin",
        "What are the rate limits for CoinGecko API",
        "How to authenticate with Binance API"
    ]
    
    for query in queries:
        print(f"\nQuery: {query}")
        result = await crypto_api_expert.retrieve_relevant_documentation(deps, query)
        print(f"Result length: {len(result)} characters")
        print(f"First 500 characters: {result[:500]}...")

async def test_compare_api_endpoints():
    """Test the compare_api_endpoints tool."""
    print("\n=== Testing compare_api_endpoints ===")
    
    # Create dependencies
    deps = PydanticAIDeps(
        supabase=supabase,
        openai_client=openai_client
    )
    
    # Test comparison
    result = await crypto_api_expert.compare_api_endpoints(
        deps, 
        "historical price data", 
        ["CoinGecko", "CryptoCompare"]
    )
    print(result)

async def test_full_agent():
    """Test the full agent with a conversation."""
    print("\n=== Testing full agent conversation ===")
    
    # Create dependencies
    deps = PydanticAIDeps(
        supabase=supabase,
        openai_client=openai_client
    )
    
    # Test query
    query = "What's the best API for getting real-time cryptocurrency prices and what endpoints should I use?"
    print(f"Query: {query}")
    
    # Run the agent
    result = await crypto_api_expert.run(query, deps=deps)
    print(f"Response: {result.content}")

async def main():
    """Run all tests."""
    # Check if database is accessible
    try:
        result = supabase.from_('crypto_api_site_pages').select('count', count='exact').execute()
        count = result.count
        print(f"Connected to database. Found {count} documentation chunks.")
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return
    
    # Run tests
    await test_list_available_apis()
    await test_retrieve_relevant_documentation()
    await test_compare_api_endpoints()
    await test_full_agent()

if __name__ == "__main__":
    asyncio.run(main())

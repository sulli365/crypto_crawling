#!/usr/bin/env python
import os
from dotenv import load_dotenv
from supabase import create_client, Client

def test_supabase_connection():
    """Test the connection to Supabase."""
    load_dotenv()
    
    # Get Supabase credentials from environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_KEY")
    
    if not supabase_url or not supabase_key:
        print("Error: Supabase credentials not found in environment variables.")
        print("Make sure SUPABASE_URL and SUPABASE_SERVICE_KEY are set in your .env file.")
        return False
    
    try:
        # Initialize Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Test connection by fetching a small amount of data
        result = supabase.table("crypto_api_site_pages").select("count").limit(1).execute()
        
        # Check if the query was successful
        if hasattr(result, 'data'):
            print("Successfully connected to Supabase!")
            print(f"Table 'crypto_api_site_pages' exists.")
            return True
        else:
            print("Error: Could not query the database.")
            return False
    except Exception as e:
        print(f"Error connecting to Supabase: {str(e)}")
        return False

if __name__ == "__main__":
    test_supabase_connection()

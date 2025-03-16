"""
Script to set up database functions and constraints.
"""

import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from supabase import create_client, Client

# Add project root to Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Load environment variables
env_path = project_root / '.env'
load_dotenv(env_path)

# Initialize Supabase client
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_SERVICE_KEY")

if not supabase_url or not supabase_key:
    print("Error: SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in .env file")
    sys.exit(1)

print(f"Connecting to Supabase at {supabase_url}")
supabase: Client = create_client(supabase_url, supabase_key)

async def setup_database():
    """Set up database functions and constraints."""
    print("\nSetting up database functions and constraints...")
    
    try:
        # Read SQL file from project root
        sql_path = project_root / "config" / "db_functions.sql"
        with open(sql_path, "r") as f:
            sql = f.read()
            
        # Split into individual statements
        statements = sql.split(';')
        
        # Execute each statement
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                try:
                    # Execute raw SQL using REST API
                    response = supabase.postgrest.rpc(
                        'exec',
                        {'command': stmt}
                    ).execute()
                    print(f"Successfully executed SQL statement:\n{stmt[:200]}...")
                except Exception as e:
                    if "already exists" in str(e).lower():
                        print(f"Function or constraint already exists - skipping:\n{stmt[:200]}...")
                    else:
                        print(f"Error executing statement: {e}")
                        print(f"Statement was:\n{stmt}")
        
        print("\nDatabase setup complete!")
        
    except Exception as e:
        print(f"Error setting up database: {e}")

if __name__ == "__main__":
    asyncio.run(setup_database())

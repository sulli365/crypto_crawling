"""
Database cleanup utilities for removing duplicate entries.
"""

import os
from typing import Optional, List, Dict, Any
from supabase import create_client, Client

from crypto_crawler.utils.error_logger import logger

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_SERVICE_KEY")
)

async def get_duplicates(api_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Find duplicate entries in the database."""
    try:
        # Base query to find duplicates based on url and chunk_number
        query = """
        WITH duplicates AS (
            SELECT url, chunk_number, COUNT(*) as count,
                   array_agg(id ORDER BY created_at) as ids,
                   array_agg(created_at ORDER BY created_at) as dates
            FROM crypto_api_site_pages
            GROUP BY url, chunk_number
            HAVING COUNT(*) > 1
        )
        SELECT * FROM duplicates
        """
        
        if api_name:
            # Add API filter if specified
            result = supabase.rpc(
                'find_duplicates_by_api',
                {'api_source': api_name}
            ).execute()
        else:
            result = supabase.rpc('find_duplicates').execute()
            
        return result.data
        
    except Exception as e:
        logger.log_general_error("db_cleanup", "get_duplicates", f"Error finding duplicates: {e}")
        return []

async def delete_duplicates(duplicates: List[Dict[str, Any]], dry_run: bool = False) -> int:
    """Delete duplicate entries, keeping the most recent version."""
    deleted_count = 0
    
    try:
        for dup in duplicates:
            # Get all IDs except the last one (most recent)
            ids_to_delete = dup['ids'][:-1]
            
            if dry_run:
                print(f"Would delete {len(ids_to_delete)} duplicates for {dup['url']} chunk {dup['chunk_number']}")
                deleted_count += len(ids_to_delete)
                continue
                
            # Delete older duplicates in batches of 100
            for i in range(0, len(ids_to_delete), 100):
                batch = ids_to_delete[i:i + 100]
                result = supabase.table("crypto_api_site_pages").delete().in_("id", batch).execute()
                
                if result.data:
                    deleted_count += len(result.data)
                    print(f"Deleted {len(result.data)} duplicates for {dup['url']} chunk {dup['chunk_number']}")
            
    except Exception as e:
        logger.log_general_error("db_cleanup", "delete_duplicates", f"Error deleting duplicates: {e}")
        
    return deleted_count

async def cleanup_duplicates(api_name: Optional[str] = None, dry_run: bool = False):
    """Main cleanup function."""
    print(f"\nSearching for duplicates{f' for {api_name}' if api_name else ''}...")
    
    duplicates = await get_duplicates(api_name)
    
    if not duplicates:
        print("No duplicates found!")
        return
        
    total_duplicates = sum(dup['count'] - 1 for dup in duplicates)
    print(f"\nFound {len(duplicates)} URLs with duplicates ({total_duplicates} total duplicate entries)")
    
    if dry_run:
        print("\nDRY RUN - No changes will be made")
        
    deleted = await delete_duplicates(duplicates, dry_run)
    
    if dry_run:
        print(f"\nWould delete {deleted} duplicate entries")
    else:
        print(f"\nDeleted {deleted} duplicate entries")
        
    print("\nCleanup complete!")

-- Function to find all duplicates
CREATE OR REPLACE FUNCTION find_duplicates()
RETURNS TABLE (
    url text,
    chunk_number integer,
    count bigint,
    ids bigint[],
    dates timestamp with time zone[]
) AS $$
BEGIN
    RETURN QUERY
    WITH duplicates AS (
        SELECT 
            url, 
            chunk_number, 
            COUNT(*) as count,
            array_agg(id ORDER BY created_at) as ids,
            array_agg(created_at ORDER BY created_at) as dates
        FROM crypto_api_site_pages
        GROUP BY url, chunk_number
        HAVING COUNT(*) > 1
    )
    SELECT * FROM duplicates;
END;
$$ LANGUAGE plpgsql;

-- Function to find duplicates for a specific API
CREATE OR REPLACE FUNCTION find_duplicates_by_api(api_source text)
RETURNS TABLE (
    url text,
    chunk_number integer,
    count bigint,
    ids bigint[],
    dates timestamp with time zone[]
) AS $$
BEGIN
    RETURN QUERY
    WITH duplicates AS (
        SELECT 
            url, 
            chunk_number, 
            COUNT(*) as count,
            array_agg(id ORDER BY created_at) as ids,
            array_agg(created_at ORDER BY created_at) as dates
        FROM crypto_api_site_pages
        WHERE metadata->>'source' = api_source
        GROUP BY url, chunk_number
        HAVING COUNT(*) > 1
    )
    SELECT * FROM duplicates;
END;
$$ LANGUAGE plpgsql;

-- Add unique constraint to prevent future duplicates
ALTER TABLE crypto_api_site_pages
ADD CONSTRAINT unique_url_chunk UNIQUE (url, chunk_number);

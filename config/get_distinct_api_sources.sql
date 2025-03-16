-- Function to get distinct API sources and categories from the crypto_api_site_pages table
CREATE OR REPLACE FUNCTION get_distinct_api_sources()
RETURNS TABLE (
    source text,
    category text
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        metadata->>'source' as source,
        COALESCE(metadata->>'category', 'unknown') as category
    FROM
        crypto_api_site_pages
    WHERE
        metadata->>'source' IS NOT NULL
    ORDER BY
        source;
END;
$$;

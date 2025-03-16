# Configuration Files

This directory contains configuration files for the Crypto API Documentation Crawler.

## Files

- `crypto_api_configs.json`: Configuration for cryptocurrency API documentation sites
- `site_pages.sql`: SQL schema for the database
- `get_distinct_api_sources.sql`: SQL function to get distinct API sources and categories

## Using the SQL Files

To set up the database:

1. First run the `site_pages.sql` script to create the table and basic functions:

```bash
psql -U your_username -d your_database -f site_pages.sql
```

2. Then run the `get_distinct_api_sources.sql` script to create the helper function:

```bash
psql -U your_username -d your_database -f get_distinct_api_sources.sql
```

Or if you're using Supabase, you can run these SQL scripts in the SQL Editor in the Supabase dashboard.

## API Configuration

The `crypto_api_configs.json` file contains configurations for each cryptocurrency API to be crawled. Each configuration includes:

- `name`: API name (e.g., "CoinGecko")
- `base_url`: Base documentation URL
- `category`: Category (e.g., "market_data", "blockchain", "defi")
- `has_sitemap`: Whether the site has a sitemap.xml
- `sitemap_url`: Custom sitemap URL if different from base_url/sitemap.xml
- `max_depth`: How deep to crawl for internal links
- `url_patterns`: Regex patterns for valid doc URLs
- `delay_between_requests`: Seconds to wait between requests
- `max_retries`: Number of retries for rate limit errors

### From Crawl4AI docs

import asyncio
from crawl4ai import AsyncWebCrawler
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.async_configs import BrowserConfig, CrawlerRunConfig

# Define the seed URLs for API documentation
seed_urls = [
    "https://docs.python.org/3/library/asyncio.html"  # Using Python docs as a test
]

async def main():
    try:
        browser_config = BrowserConfig(
            verbose=True,
            headless=True,  # Set to False if you want to see the browser in action
        )
        
        run_config = CrawlerRunConfig(
            # Content filtering
            excluded_tags=['form', 'header'],
            exclude_external_links=True,

            # Content processing
            process_iframes=True,
            remove_overlay_elements=True,
            markdown_generator=DefaultMarkdownGenerator(),
        )

        print("Starting crawler...")
        async with AsyncWebCrawler(config=browser_config) as crawler:
            print(f"Crawling URL: {seed_urls[0]}")
            result = await crawler.arun(
                url=seed_urls[0],  # Pass single URL instead of list
                config=run_config
            )

            if result.success:
                print("\nContent (first 500 chars):")
                print("-" * 50)
                print(result.markdown_v2.raw_markdown[:500])
                print("-" * 50)

                print("\nInternal links found:")
                print("-" * 50)
                for link in result.links["internal"]:
                    print(f"Internal link: {link['href']}")
            else:
                print(f"Crawl failed: {result.error_message}")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        print(traceback.format_exc())

if __name__ == "__main__":
    asyncio.run(main())

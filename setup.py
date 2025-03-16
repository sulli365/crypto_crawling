from setuptools import setup, find_packages

setup(
    name="crypto_crawler",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    description="A tool for crawling, processing, and storing cryptocurrency API documentation",
    author="Crypto Crawler Team",
    python_requires=">=3.11",
    install_requires=[
        "aiofiles>=24.1.0",
        "aiohttp>=3.11.0",
        "beautifulsoup4>=4.12.0",
        "Crawl4AI>=0.4.247",
        "openai>=1.59.0",
        "pydantic>=2.10.0",
        "pydantic-ai>=0.0.18",
        "python-dotenv>=1.0.0",
        "streamlit>=1.41.0",
        "supabase>=2.11.0",
        "tiktoken>=0.8.0",
        "playwright>=1.49.0",
    ],
    entry_points={
        "console_scripts": [
            "crypto-crawler=main:main",  # Main entry point
            "crypto-crawl=crypto_crawler.crawling.crawler:main",
            "crypto-ui=crypto_crawler.ui.streamlit_app:main",
        ],
    },
    include_package_data=True,
    package_data={
        "crypto_crawler": ["config/*", "docs/*"],
    },
)

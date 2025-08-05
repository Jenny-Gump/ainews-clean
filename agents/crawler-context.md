# News Crawler Context
Updated: 2025-08-02

## Current State
- 26 RSS sources (100% RSS coverage)
- RSS+Scrape is the primary parsing method
- Processing ~500-1000 articles/day
- Rate limiting: 100 requests/minute (Scrape API)

## Active Issues
- Some RSS feeds return partial content
- Memory usage during batch processing
- Duplicate articles from cross-posted content

## Key Files
- sources.json (26 source definitions)
- main.py (entry point with RSS+Scrape)
- rss_scrape_parser.py (primary parser)
- firecrawl_service.py (API wrapper)

## API Documentation
- **Firecrawl API Docs**: https://docs.firecrawl.dev/introduction
- **Scrape API**: https://docs.firecrawl.dev/features/scrape
- **Rate Limits**: https://docs.firecrawl.dev/getting-started/self-host
- **Error Handling**: https://docs.firecrawl.dev/api-reference/errors

## Recent Changes
- MIGRATION COMPLETED: Removed unified_crawl_parser.py and crawl_service.py
- RSS+Scrape is now the default method in main.py
- Added backward compatibility for all old commands
- System works exclusively with RSS feeds
- LOGGING AUDIT COMPLETED (2025-08-02): Centralized logging fully integrated
- Removed temporary debug code and print() statements from production files
- All core RSS files use structured JSON logging with contextual information
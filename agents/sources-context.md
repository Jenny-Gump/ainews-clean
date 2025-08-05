# Source Manager Context
Updated: 2025-08-02

## Current State
- 26 high-quality AI-focused sources
- 100% RSS coverage (all sources have RSS)
- No crawl-only sources remaining
- Validation system operational

## Active Issues
- VentureBeat RSS feed unstable
- TechCrunch rate limiting aggressive
- Some RSS feeds return partial content

## Key Files
- sources.json (26 source definitions)
- source_validator.py (validation logic)
- rss_discovery_service.py (RSS finder)
- check_all_rss.py (RSS health check)
- auto_fix_sources.py (auto-repair)

## Recent Changes
- Optimized from 48 to 26 sources (removed 3 without RSS)
- Added RSS for Distill publication
- Removed url_depths_config.json (crawl-specific)
- Updated all documentation for RSS-only architecture
- Synchronized database with new source list
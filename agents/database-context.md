# Database Specialist Context
Updated: 2025-08-02

## Current State
- Main DB: data/ainews.db (SQLite) - optimized for RSS workflow
- Monitoring DB: data/monitoring.db
- 261 articles (29 completed, 232 pending)
- Auto-migration system active

## Active Issues
- Media files table growing rapidly
- Need automated backup strategy

## Key Files
- database.py (main DB operations)
- migrations/ (SQL migration files)
- monitoring/database.py (monitoring DB)
- monitoring/models.py (SQLAlchemy models)
- monitoring/database_views.sql (materialized views)

## Recent Changes
- OPTIMIZED FOR RSS: Added RSS-specific fields (rss_url, rss_guid, etc.)
- Created 6 new indexes for RSS workflow performance
- Removed old Crawl metadata (10 crawl-discovered articles)
- Database backup created (ainews_backup_20250802_132922.db)
- All 26 RSS sources properly stored in DB
# Database Specialist Context
Updated: 2025-08-14

## Current State
- Main DB: Supabase (mtguynupyltlqiwhmilc.supabase.co) - fully migrated from SQLite
- Monitoring DB: data/monitoring.db
- 782 articles (0 duplicates) - ALL DUPLICATES RESOLVED
- UNIQUE constraint protection active

## RESOLVED Issues ✅
- ✅ DUPLICATE ARTICLES FIXED: Removed all URL duplicates
- ✅ DATABASE PROTECTION: Added UNIQUE constraint on url field
- ✅ DEDUPLICATION LOGIC: Fixed article_exists() and url_exists() methods
- ✅ SOURCE CLEANUP: Removed duplicate sources (huggingface -> hugging_face)

## Key Files
- services/supabase_client.py (main DB operations with duplicate protection)
- services/rss_discovery.py (RSS workflow with proper deduplication)
- data/tracking_sources.json (cleaned up duplicate sources)
- core/database_factory.py (Supabase factory)
- core/db_config.py (database configuration)

## Recent Changes (August 14, 2025) 
- ✅ COMPLETE DUPLICATE FIX: Removed 1 duplicate article, prevented future duplicates
- ✅ UNIQUE CONSTRAINT: Added articles_url_unique constraint to prevent duplicates
- ✅ INDEX OPTIMIZATION: Created idx_articles_url index for fast URL lookups
- ✅ SOURCE DEDUPLICATION: Unified hugging_face and huggingface sources
- ✅ METHOD IMPROVEMENTS: Enhanced article_exists(), url_exists(), insert_article()
- ✅ ERROR HANDLING: Added graceful handling of UNIQUE constraint violations
- ✅ BACKUP CREATED: backups/duplicate_fix_20250814_175153/

## Database Protection Status
- UNIQUE constraint: ✅ ACTIVE (articles_url_unique)
- Duplicate detection: ✅ WORKING (checks is_deleted status)
- Error handling: ✅ GRACEFUL (handles constraint violations)
- Source validation: ✅ CLEAN (no duplicate feed_urls)
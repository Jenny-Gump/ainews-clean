-- ============================================================================
-- AI News Parser - Schema Rollback Script
-- Removes all PostgreSQL schema elements
-- Generated: 2025-08-13
-- ============================================================================

-- ============================================================================
-- WARNING: This script will DELETE ALL DATA and SCHEMA
-- Make sure to backup before running!
-- ============================================================================

-- Disable foreign key checks temporarily
SET session_replication_role = 'replica';

-- ============================================================================
-- DROP ALL POLICIES
-- ============================================================================

-- Drop all RLS policies on main tables
DROP POLICY IF EXISTS "articles_public_read" ON articles;
DROP POLICY IF EXISTS "articles_authenticated_all" ON articles;
DROP POLICY IF EXISTS "articles_service_all" ON articles;

DROP POLICY IF EXISTS "sources_public_read" ON sources;
DROP POLICY IF EXISTS "sources_authenticated_all" ON sources;
DROP POLICY IF EXISTS "sources_service_all" ON sources;

DROP POLICY IF EXISTS "media_files_public_read" ON media_files;
DROP POLICY IF EXISTS "media_files_authenticated_all" ON media_files;
DROP POLICY IF EXISTS "media_files_service_all" ON media_files;

DROP POLICY IF EXISTS "wordpress_articles_public_read" ON wordpress_articles;
DROP POLICY IF EXISTS "wordpress_articles_authenticated_all" ON wordpress_articles;
DROP POLICY IF EXISTS "wordpress_articles_service_all" ON wordpress_articles;

DROP POLICY IF EXISTS "related_links_public_read" ON related_links;
DROP POLICY IF EXISTS "related_links_authenticated_all" ON related_links;
DROP POLICY IF EXISTS "related_links_service_all" ON related_links;

DROP POLICY IF EXISTS "global_config_public_read" ON global_config;
DROP POLICY IF EXISTS "global_config_authenticated_read" ON global_config;
DROP POLICY IF EXISTS "global_config_service_all" ON global_config;

DROP POLICY IF EXISTS "pipeline_operations_authenticated_read" ON pipeline_operations;
DROP POLICY IF EXISTS "pipeline_operations_service_all" ON pipeline_operations;

DROP POLICY IF EXISTS "tracked_articles_authenticated_all" ON tracked_articles;
DROP POLICY IF EXISTS "tracked_articles_service_all" ON tracked_articles;

DROP POLICY IF EXISTS "tracked_urls_authenticated_all" ON tracked_urls;
DROP POLICY IF EXISTS "tracked_urls_service_all" ON tracked_urls;

-- Drop all RLS policies on monitoring tables
DROP POLICY IF EXISTS "system_metrics_authenticated_read" ON system_metrics;
DROP POLICY IF EXISTS "system_metrics_service_all" ON system_metrics;

DROP POLICY IF EXISTS "performance_metrics_authenticated_read" ON performance_metrics;
DROP POLICY IF EXISTS "performance_metrics_service_all" ON performance_metrics;

DROP POLICY IF EXISTS "source_metrics_authenticated_read" ON source_metrics;
DROP POLICY IF EXISTS "source_metrics_service_all" ON source_metrics;

DROP POLICY IF EXISTS "article_stats_public_read" ON article_stats;
DROP POLICY IF EXISTS "article_stats_service_all" ON article_stats;

DROP POLICY IF EXISTS "memory_metrics_service_all" ON memory_metrics;

DROP POLICY IF EXISTS "memory_alerts_authenticated_read" ON memory_alerts;
DROP POLICY IF EXISTS "memory_alerts_service_all" ON memory_alerts;

DROP POLICY IF EXISTS "rss_feed_metrics_authenticated_read" ON rss_feed_metrics;
DROP POLICY IF EXISTS "rss_feed_metrics_service_all" ON rss_feed_metrics;

DROP POLICY IF EXISTS "extract_api_metrics_service_all" ON extract_api_metrics;

DROP POLICY IF EXISTS "extract_api_errors_authenticated_read" ON extract_api_errors;
DROP POLICY IF EXISTS "extract_api_errors_service_all" ON extract_api_errors;

DROP POLICY IF EXISTS "parsing_progress_authenticated_read" ON parsing_progress;
DROP POLICY IF EXISTS "parsing_progress_service_all" ON parsing_progress;

DROP POLICY IF EXISTS "emergency_snapshots_service_all" ON emergency_snapshots;
DROP POLICY IF EXISTS "watchdog_actions_service_all" ON watchdog_actions;

DROP POLICY IF EXISTS "source_health_reports_authenticated_read" ON source_health_reports;
DROP POLICY IF EXISTS "source_health_reports_service_all" ON source_health_reports;

DROP POLICY IF EXISTS "error_logs_authenticated_read" ON error_logs;
DROP POLICY IF EXISTS "error_logs_service_all" ON error_logs;

DROP POLICY IF EXISTS "context_enrichment_metrics_service_all" ON context_enrichment_metrics;
DROP POLICY IF EXISTS "supabase_performance_metrics_service_all" ON supabase_performance_metrics;

DROP POLICY IF EXISTS "api_cost_tracking_authenticated_read" ON api_cost_tracking;
DROP POLICY IF EXISTS "api_cost_tracking_service_all" ON api_cost_tracking;

DROP POLICY IF EXISTS "vector_search_performance_service_all" ON vector_search_performance;

DROP POLICY IF EXISTS "context_pipeline_metrics_authenticated_read" ON context_pipeline_metrics;
DROP POLICY IF EXISTS "context_pipeline_metrics_service_all" ON context_pipeline_metrics;

-- ============================================================================
-- DROP ALL TRIGGERS
-- ============================================================================

DROP TRIGGER IF EXISTS update_articles_updated_at ON articles;
DROP TRIGGER IF EXISTS update_sources_updated_at ON sources;
DROP TRIGGER IF EXISTS update_media_files_updated_at ON media_files;
DROP TRIGGER IF EXISTS update_wordpress_articles_updated_at ON wordpress_articles;
DROP TRIGGER IF EXISTS update_tracked_articles_updated_at ON tracked_articles;
DROP TRIGGER IF EXISTS update_global_config_updated_at ON global_config;
DROP TRIGGER IF EXISTS update_parsing_progress_updated_at ON parsing_progress;

-- ============================================================================
-- DROP ALL FUNCTIONS
-- ============================================================================

-- Timestamp management
DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;

-- Article processing functions
DROP FUNCTION IF EXISTS generate_article_id(TEXT) CASCADE;
DROP FUNCTION IF EXISTS article_exists(TEXT) CASCADE;
DROP FUNCTION IF EXISTS get_article_status(TEXT) CASCADE;

-- Source management functions
DROP FUNCTION IF EXISTS update_source_stats(TEXT) CASCADE;
DROP FUNCTION IF EXISTS check_source_health(TEXT) CASCADE;

-- Media processing functions
DROP FUNCTION IF EXISTS count_article_media(TEXT) CASCADE;
DROP FUNCTION IF EXISTS clean_orphaned_media() CASCADE;

-- Statistics and aggregation functions
DROP FUNCTION IF EXISTS get_daily_stats(DATE) CASCADE;
DROP FUNCTION IF EXISTS get_source_ranking(INTEGER) CASCADE;

-- Monitoring and alerting functions
DROP FUNCTION IF EXISTS check_system_thresholds() CASCADE;

-- Cleanup and maintenance functions
DROP FUNCTION IF EXISTS archive_old_data(INTEGER) CASCADE;
DROP FUNCTION IF EXISTS maintenance_vacuum_analyze() CASCADE;

-- Logging and audit functions
DROP FUNCTION IF EXISTS log_pipeline_operation(BIGINT, TEXT, TEXT, TEXT, JSONB) CASCADE;
DROP FUNCTION IF EXISTS log_error(TEXT, TEXT, TEXT, TEXT, JSONB) CASCADE;

-- Search and discovery functions
DROP FUNCTION IF EXISTS search_articles(TEXT, INTEGER, INTEGER) CASCADE;
DROP FUNCTION IF EXISTS find_duplicate_articles(REAL) CASCADE;

-- ============================================================================
-- DROP ALL INDEXES
-- ============================================================================

-- Articles indexes
DROP INDEX IF EXISTS idx_articles_source_id;
DROP INDEX IF EXISTS idx_articles_content_status;
DROP INDEX IF EXISTS idx_articles_published_date;
DROP INDEX IF EXISTS idx_articles_created_at;
DROP INDEX IF EXISTS idx_articles_is_deleted;
DROP INDEX IF EXISTS idx_articles_discovered_via;
DROP INDEX IF EXISTS idx_articles_url_hash;
DROP INDEX IF EXISTS idx_articles_title_gin;
DROP INDEX IF EXISTS idx_articles_content_gin;

-- Media files indexes
DROP INDEX IF EXISTS idx_media_files_article_id;
DROP INDEX IF EXISTS idx_media_files_source_id;
DROP INDEX IF EXISTS idx_media_files_status;
DROP INDEX IF EXISTS idx_media_files_wp_upload_status;
DROP INDEX IF EXISTS idx_media_files_processing_session;

-- WordPress articles indexes
DROP INDEX IF EXISTS idx_wordpress_articles_article_id;
DROP INDEX IF EXISTS idx_wordpress_articles_translation_status;
DROP INDEX IF EXISTS idx_wordpress_articles_published_to_wp;
DROP INDEX IF EXISTS idx_wordpress_articles_wp_post_id;
DROP INDEX IF EXISTS idx_wordpress_articles_slug;
DROP INDEX IF EXISTS idx_wordpress_articles_title_gin;
DROP INDEX IF EXISTS idx_wordpress_articles_content_gin;

-- Sources indexes
DROP INDEX IF EXISTS idx_sources_type;
DROP INDEX IF EXISTS idx_sources_has_rss;
DROP INDEX IF EXISTS idx_sources_category;
DROP INDEX IF EXISTS idx_sources_last_parsed;
DROP INDEX IF EXISTS idx_sources_validation_status;

-- Related links indexes
DROP INDEX IF EXISTS idx_related_links_article_id;

-- Pipeline operations indexes
DROP INDEX IF EXISTS idx_pipeline_operations_session_id;
DROP INDEX IF EXISTS idx_pipeline_operations_phase;
DROP INDEX IF EXISTS idx_pipeline_operations_timestamp;

-- Tracked articles indexes
DROP INDEX IF EXISTS idx_tracked_articles_source_id;
DROP INDEX IF EXISTS idx_tracked_articles_change_detected;
DROP INDEX IF EXISTS idx_tracked_articles_exported_to_main;
DROP INDEX IF EXISTS idx_tracked_articles_url_hash;

-- Tracked URLs indexes
DROP INDEX IF EXISTS idx_tracked_urls_source_domain;
DROP INDEX IF EXISTS idx_tracked_urls_is_new;
DROP INDEX IF EXISTS idx_tracked_urls_exported_to_articles;
DROP INDEX IF EXISTS idx_tracked_urls_discovered_at;

-- Monitoring indexes
DROP INDEX IF EXISTS idx_system_metrics_timestamp;
DROP INDEX IF EXISTS idx_performance_metrics_timestamp;
DROP INDEX IF EXISTS idx_performance_metrics_metric_type;
DROP INDEX IF EXISTS idx_source_metrics_source_id;
DROP INDEX IF EXISTS idx_source_metrics_timestamp;
DROP INDEX IF EXISTS idx_article_stats_timestamp;
DROP INDEX IF EXISTS idx_memory_metrics_timestamp;
DROP INDEX IF EXISTS idx_memory_alerts_resolved;
DROP INDEX IF EXISTS idx_rss_feed_metrics_source_id;
DROP INDEX IF EXISTS idx_extract_api_metrics_timestamp;
DROP INDEX IF EXISTS idx_error_logs_timestamp;
DROP INDEX IF EXISTS idx_error_logs_resolved;

-- ============================================================================
-- REVOKE PERMISSIONS
-- ============================================================================

-- Revoke permissions from anon role
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM anon;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM anon;

-- Revoke permissions from authenticated role
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM authenticated;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM authenticated;

-- ============================================================================
-- DROP ALL TABLES (in correct order due to foreign keys)
-- ============================================================================

-- Drop monitoring tables first (no dependencies)
DROP TABLE IF EXISTS context_pipeline_metrics CASCADE;
DROP TABLE IF EXISTS vector_search_performance CASCADE;
DROP TABLE IF EXISTS api_cost_tracking CASCADE;
DROP TABLE IF EXISTS supabase_performance_metrics CASCADE;
DROP TABLE IF EXISTS context_enrichment_metrics CASCADE;
DROP TABLE IF EXISTS error_logs CASCADE;
DROP TABLE IF EXISTS source_health_reports CASCADE;
DROP TABLE IF EXISTS watchdog_actions CASCADE;
DROP TABLE IF EXISTS emergency_snapshots CASCADE;
DROP TABLE IF EXISTS parsing_progress CASCADE;
DROP TABLE IF EXISTS extract_api_errors CASCADE;
DROP TABLE IF EXISTS extract_api_metrics CASCADE;
DROP TABLE IF EXISTS rss_feed_metrics CASCADE;
DROP TABLE IF EXISTS memory_alerts CASCADE;
DROP TABLE IF EXISTS memory_metrics CASCADE;
DROP TABLE IF EXISTS article_stats CASCADE;
DROP TABLE IF EXISTS source_metrics CASCADE;
DROP TABLE IF EXISTS performance_metrics CASCADE;
DROP TABLE IF EXISTS system_metrics CASCADE;

-- Drop dependent tables
DROP TABLE IF EXISTS pipeline_operations CASCADE;
DROP TABLE IF EXISTS global_config CASCADE;
DROP TABLE IF EXISTS tracked_urls CASCADE;
DROP TABLE IF EXISTS tracked_articles CASCADE;
DROP TABLE IF EXISTS related_links CASCADE;
DROP TABLE IF EXISTS wordpress_articles CASCADE;
DROP TABLE IF EXISTS media_files CASCADE;

-- Drop main tables
DROP TABLE IF EXISTS articles CASCADE;
DROP TABLE IF EXISTS sources CASCADE;

-- ============================================================================
-- DROP EXTENSIONS (optional - be careful with these)
-- ============================================================================

-- Only drop if you're sure no other schemas use them
-- DROP EXTENSION IF EXISTS "uuid-ossp";
-- DROP EXTENSION IF EXISTS "pg_trgm";
-- DROP EXTENSION IF EXISTS "btree_gin";

-- Re-enable foreign key checks
SET session_replication_role = 'origin';

-- ============================================================================
-- VERIFICATION
-- ============================================================================

-- List remaining tables (should be empty or only system tables)
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_type = 'BASE TABLE'
ORDER BY table_name;

-- ============================================================================
-- END OF ROLLBACK SCRIPT
-- ============================================================================
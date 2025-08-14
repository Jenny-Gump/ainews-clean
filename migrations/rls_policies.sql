-- ============================================================================
-- AI News Parser - Row Level Security (RLS) Policies
-- For Supabase PostgreSQL
-- Generated: 2025-08-13
-- ============================================================================

-- ============================================================================
-- ENABLE RLS ON ALL TABLES
-- ============================================================================

-- Main content tables
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE wordpress_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE related_links ENABLE ROW LEVEL SECURITY;
ALTER TABLE global_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE pipeline_operations ENABLE ROW LEVEL SECURITY;
ALTER TABLE tracked_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE tracked_urls ENABLE ROW LEVEL SECURITY;

-- Monitoring tables
ALTER TABLE system_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE article_stats ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE memory_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE rss_feed_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE extract_api_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE extract_api_errors ENABLE ROW LEVEL SECURITY;
ALTER TABLE parsing_progress ENABLE ROW LEVEL SECURITY;
ALTER TABLE emergency_snapshots ENABLE ROW LEVEL SECURITY;
ALTER TABLE watchdog_actions ENABLE ROW LEVEL SECURITY;
ALTER TABLE source_health_reports ENABLE ROW LEVEL SECURITY;
ALTER TABLE error_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE context_enrichment_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE supabase_performance_metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_cost_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE vector_search_performance ENABLE ROW LEVEL SECURITY;
ALTER TABLE context_pipeline_metrics ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- ARTICLES TABLE POLICIES
-- ============================================================================

-- Allow public read access to published articles
CREATE POLICY "articles_public_read" ON articles
    FOR SELECT
    USING (
        is_deleted = false 
        AND content_status = 'completed'
    );

-- Allow authenticated users full access
CREATE POLICY "articles_authenticated_all" ON articles
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Allow service role unrestricted access
CREATE POLICY "articles_service_all" ON articles
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- SOURCES TABLE POLICIES
-- ============================================================================

-- Allow public read access to active sources
CREATE POLICY "sources_public_read" ON sources
    FOR SELECT
    USING (validation_status = 'valid');

-- Allow authenticated users to manage sources
CREATE POLICY "sources_authenticated_all" ON sources
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Allow service role unrestricted access
CREATE POLICY "sources_service_all" ON sources
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- MEDIA FILES TABLE POLICIES
-- ============================================================================

-- Allow public read access to processed media
CREATE POLICY "media_files_public_read" ON media_files
    FOR SELECT
    USING (status = 'completed');

-- Allow authenticated users full access
CREATE POLICY "media_files_authenticated_all" ON media_files
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Allow service role unrestricted access
CREATE POLICY "media_files_service_all" ON media_files
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- WORDPRESS ARTICLES TABLE POLICIES
-- ============================================================================

-- Allow public read access to published articles
CREATE POLICY "wordpress_articles_public_read" ON wordpress_articles
    FOR SELECT
    USING (published_to_wp = true);

-- Allow authenticated users full access
CREATE POLICY "wordpress_articles_authenticated_all" ON wordpress_articles
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Allow service role unrestricted access
CREATE POLICY "wordpress_articles_service_all" ON wordpress_articles
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- RELATED LINKS TABLE POLICIES
-- ============================================================================

-- Allow public read access
CREATE POLICY "related_links_public_read" ON related_links
    FOR SELECT
    USING (true);

-- Allow authenticated users to manage links
CREATE POLICY "related_links_authenticated_all" ON related_links
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Allow service role unrestricted access
CREATE POLICY "related_links_service_all" ON related_links
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- GLOBAL CONFIG TABLE POLICIES
-- ============================================================================

-- Allow public read access to non-sensitive config
CREATE POLICY "global_config_public_read" ON global_config
    FOR SELECT
    USING (
        key NOT LIKE '%secret%' 
        AND key NOT LIKE '%key%' 
        AND key NOT LIKE '%password%'
        AND key NOT LIKE '%token%'
    );

-- Allow authenticated users to read all config
CREATE POLICY "global_config_authenticated_read" ON global_config
    FOR SELECT
    TO authenticated
    USING (true);

-- Allow service role full access
CREATE POLICY "global_config_service_all" ON global_config
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- PIPELINE OPERATIONS TABLE POLICIES
-- ============================================================================

-- Allow authenticated users read access
CREATE POLICY "pipeline_operations_authenticated_read" ON pipeline_operations
    FOR SELECT
    TO authenticated
    USING (true);

-- Allow service role full access
CREATE POLICY "pipeline_operations_service_all" ON pipeline_operations
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- TRACKED ARTICLES TABLE POLICIES
-- ============================================================================

-- Allow authenticated users full access
CREATE POLICY "tracked_articles_authenticated_all" ON tracked_articles
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Allow service role unrestricted access
CREATE POLICY "tracked_articles_service_all" ON tracked_articles
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- TRACKED URLS TABLE POLICIES
-- ============================================================================

-- Allow authenticated users full access
CREATE POLICY "tracked_urls_authenticated_all" ON tracked_urls
    FOR ALL
    TO authenticated
    USING (true)
    WITH CHECK (true);

-- Allow service role unrestricted access
CREATE POLICY "tracked_urls_service_all" ON tracked_urls
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- MONITORING TABLES POLICIES (Restricted Access)
-- ============================================================================

-- System metrics - authenticated read only
CREATE POLICY "system_metrics_authenticated_read" ON system_metrics
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "system_metrics_service_all" ON system_metrics
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Performance metrics - authenticated read only
CREATE POLICY "performance_metrics_authenticated_read" ON performance_metrics
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "performance_metrics_service_all" ON performance_metrics
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Source metrics - authenticated read only
CREATE POLICY "source_metrics_authenticated_read" ON source_metrics
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "source_metrics_service_all" ON source_metrics
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Article stats - public read for aggregated data
CREATE POLICY "article_stats_public_read" ON article_stats
    FOR SELECT
    USING (true);

CREATE POLICY "article_stats_service_all" ON article_stats
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Memory metrics - service role only
CREATE POLICY "memory_metrics_service_all" ON memory_metrics
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Memory alerts - authenticated read, service write
CREATE POLICY "memory_alerts_authenticated_read" ON memory_alerts
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "memory_alerts_service_all" ON memory_alerts
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- RSS feed metrics - authenticated read only
CREATE POLICY "rss_feed_metrics_authenticated_read" ON rss_feed_metrics
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "rss_feed_metrics_service_all" ON rss_feed_metrics
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Extract API metrics - service role only
CREATE POLICY "extract_api_metrics_service_all" ON extract_api_metrics
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Extract API errors - authenticated read, service write
CREATE POLICY "extract_api_errors_authenticated_read" ON extract_api_errors
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "extract_api_errors_service_all" ON extract_api_errors
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Parsing progress - authenticated read only
CREATE POLICY "parsing_progress_authenticated_read" ON parsing_progress
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "parsing_progress_service_all" ON parsing_progress
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Emergency snapshots - service role only
CREATE POLICY "emergency_snapshots_service_all" ON emergency_snapshots
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Watchdog actions - service role only
CREATE POLICY "watchdog_actions_service_all" ON watchdog_actions
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Source health reports - authenticated read only
CREATE POLICY "source_health_reports_authenticated_read" ON source_health_reports
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "source_health_reports_service_all" ON source_health_reports
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Error logs - authenticated read, service write
CREATE POLICY "error_logs_authenticated_read" ON error_logs
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "error_logs_service_all" ON error_logs
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Context enrichment metrics - service role only
CREATE POLICY "context_enrichment_metrics_service_all" ON context_enrichment_metrics
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Supabase performance metrics - service role only
CREATE POLICY "supabase_performance_metrics_service_all" ON supabase_performance_metrics
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- API cost tracking - authenticated read, service write
CREATE POLICY "api_cost_tracking_authenticated_read" ON api_cost_tracking
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "api_cost_tracking_service_all" ON api_cost_tracking
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Vector search performance - service role only
CREATE POLICY "vector_search_performance_service_all" ON vector_search_performance
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- Context pipeline metrics - authenticated read, service write
CREATE POLICY "context_pipeline_metrics_authenticated_read" ON context_pipeline_metrics
    FOR SELECT
    TO authenticated
    USING (true);

CREATE POLICY "context_pipeline_metrics_service_all" ON context_pipeline_metrics
    FOR ALL
    TO service_role
    USING (true)
    WITH CHECK (true);

-- ============================================================================
-- GRANT PERMISSIONS FOR ANON ROLE (Limited Public Access)
-- ============================================================================

-- Grant select on specific tables for anonymous users
GRANT SELECT ON articles TO anon;
GRANT SELECT ON sources TO anon;
GRANT SELECT ON media_files TO anon;
GRANT SELECT ON wordpress_articles TO anon;
GRANT SELECT ON related_links TO anon;
GRANT SELECT ON global_config TO anon;
GRANT SELECT ON article_stats TO anon;

-- ============================================================================
-- GRANT PERMISSIONS FOR AUTHENTICATED ROLE
-- ============================================================================

-- Grant full access to content tables
GRANT ALL ON articles TO authenticated;
GRANT ALL ON sources TO authenticated;
GRANT ALL ON media_files TO authenticated;
GRANT ALL ON wordpress_articles TO authenticated;
GRANT ALL ON related_links TO authenticated;
GRANT ALL ON tracked_articles TO authenticated;
GRANT ALL ON tracked_urls TO authenticated;

-- Grant read access to monitoring tables
GRANT SELECT ON system_metrics TO authenticated;
GRANT SELECT ON performance_metrics TO authenticated;
GRANT SELECT ON source_metrics TO authenticated;
GRANT SELECT ON article_stats TO authenticated;
GRANT SELECT ON memory_alerts TO authenticated;
GRANT SELECT ON rss_feed_metrics TO authenticated;
GRANT SELECT ON extract_api_errors TO authenticated;
GRANT SELECT ON parsing_progress TO authenticated;
GRANT SELECT ON source_health_reports TO authenticated;
GRANT SELECT ON error_logs TO authenticated;
GRANT SELECT ON api_cost_tracking TO authenticated;
GRANT SELECT ON context_pipeline_metrics TO authenticated;

-- Grant read access to config and operations
GRANT SELECT ON global_config TO authenticated;
GRANT SELECT ON pipeline_operations TO authenticated;

-- Grant usage on sequences
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO authenticated;

-- ============================================================================
-- GRANT PERMISSIONS FOR SERVICE ROLE (Full Access)
-- ============================================================================

-- Grant all permissions on all tables
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO service_role;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON POLICY "articles_public_read" ON articles IS 'Allow public access to completed, non-deleted articles';
COMMENT ON POLICY "sources_public_read" ON sources IS 'Allow public access to validated sources only';
COMMENT ON POLICY "media_files_public_read" ON media_files IS 'Allow public access to completed media files';
COMMENT ON POLICY "wordpress_articles_public_read" ON wordpress_articles IS 'Allow public access to published WordPress articles';
COMMENT ON POLICY "global_config_public_read" ON global_config IS 'Allow public access to non-sensitive configuration';
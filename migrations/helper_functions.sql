-- ============================================================================
-- AI News Parser - Helper Functions and Triggers
-- For Supabase PostgreSQL
-- Generated: 2025-08-13
-- ============================================================================

-- ============================================================================
-- TIMESTAMP MANAGEMENT FUNCTIONS
-- ============================================================================

-- Function to automatically update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- APPLY UPDATED_AT TRIGGERS
-- ============================================================================

-- Articles table
CREATE TRIGGER update_articles_updated_at 
    BEFORE UPDATE ON articles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Sources table
CREATE TRIGGER update_sources_updated_at 
    BEFORE UPDATE ON sources
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Media files table
CREATE TRIGGER update_media_files_updated_at 
    BEFORE UPDATE ON media_files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- WordPress articles table
CREATE TRIGGER update_wordpress_articles_updated_at 
    BEFORE UPDATE ON wordpress_articles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Tracked articles table
CREATE TRIGGER update_tracked_articles_updated_at 
    BEFORE UPDATE ON tracked_articles
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Global config table
CREATE TRIGGER update_global_config_updated_at 
    BEFORE UPDATE ON global_config
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Parsing progress table
CREATE TRIGGER update_parsing_progress_updated_at 
    BEFORE UPDATE ON parsing_progress
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- ARTICLE PROCESSING FUNCTIONS
-- ============================================================================

-- Function to generate article ID from URL
CREATE OR REPLACE FUNCTION generate_article_id(p_url TEXT)
RETURNS TEXT AS $$
BEGIN
    RETURN LOWER(REPLACE(MD5(p_url), '-', ''));
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Function to check if article exists
CREATE OR REPLACE FUNCTION article_exists(p_url TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN EXISTS (
        SELECT 1 FROM articles 
        WHERE url = p_url 
        AND is_deleted = false
    );
END;
$$ LANGUAGE plpgsql;

-- Function to get article processing status
CREATE OR REPLACE FUNCTION get_article_status(p_article_id TEXT)
RETURNS TABLE(
    content_status TEXT,
    media_status TEXT,
    translation_status TEXT,
    published_to_wp BOOLEAN
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.content_status,
        a.media_status,
        wa.translation_status,
        wa.published_to_wp
    FROM articles a
    LEFT JOIN wordpress_articles wa ON a.article_id = wa.article_id
    WHERE a.article_id = p_article_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SOURCE MANAGEMENT FUNCTIONS
-- ============================================================================

-- Function to update source statistics
CREATE OR REPLACE FUNCTION update_source_stats(p_source_id TEXT)
RETURNS VOID AS $$
DECLARE
    v_total_articles INTEGER;
    v_success_count INTEGER;
    v_total_count INTEGER;
BEGIN
    -- Count total articles
    SELECT COUNT(*) INTO v_total_articles
    FROM articles
    WHERE source_id = p_source_id
    AND is_deleted = false;
    
    -- Calculate success rate
    SELECT 
        COUNT(*) FILTER (WHERE content_status = 'completed'),
        COUNT(*)
    INTO v_success_count, v_total_count
    FROM articles
    WHERE source_id = p_source_id
    AND content_status IN ('completed', 'failed');
    
    -- Update source
    UPDATE sources
    SET 
        total_articles = v_total_articles,
        success_rate = CASE 
            WHEN v_total_count > 0 THEN v_success_count::DOUBLE PRECISION / v_total_count
            ELSE 0
        END
    WHERE source_id = p_source_id;
END;
$$ LANGUAGE plpgsql;

-- Function to check source health
CREATE OR REPLACE FUNCTION check_source_health(p_source_id TEXT)
RETURNS JSONB AS $$
DECLARE
    v_result JSONB;
    v_last_success TIMESTAMP WITH TIME ZONE;
    v_consecutive_failures INTEGER;
    v_avg_response_time DOUBLE PRECISION;
    v_health_score DOUBLE PRECISION;
BEGIN
    -- Get last successful fetch
    SELECT MAX(created_at) INTO v_last_success
    FROM articles
    WHERE source_id = p_source_id
    AND content_status = 'completed';
    
    -- Get consecutive failures
    SELECT consecutive_failures INTO v_consecutive_failures
    FROM sources
    WHERE source_id = p_source_id;
    
    -- Calculate average response time from recent metrics
    SELECT AVG(fetch_duration_ms) INTO v_avg_response_time
    FROM source_metrics
    WHERE source_id = p_source_id
    AND timestamp > CURRENT_TIMESTAMP - INTERVAL '24 hours';
    
    -- Calculate health score (0-100)
    v_health_score := CASE
        WHEN v_consecutive_failures >= 10 THEN 0
        WHEN v_consecutive_failures >= 5 THEN 25
        WHEN v_consecutive_failures >= 3 THEN 50
        WHEN v_consecutive_failures >= 1 THEN 75
        ELSE 100
    END;
    
    -- Adjust for response time
    IF v_avg_response_time > 10000 THEN
        v_health_score := v_health_score * 0.8;
    ELSIF v_avg_response_time > 5000 THEN
        v_health_score := v_health_score * 0.9;
    END IF;
    
    v_result := jsonb_build_object(
        'health_score', v_health_score,
        'last_success', v_last_success,
        'consecutive_failures', v_consecutive_failures,
        'avg_response_time_ms', v_avg_response_time,
        'status', CASE
            WHEN v_health_score >= 80 THEN 'healthy'
            WHEN v_health_score >= 50 THEN 'degraded'
            WHEN v_health_score >= 25 THEN 'unhealthy'
            ELSE 'critical'
        END
    );
    
    RETURN v_result;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- MEDIA PROCESSING FUNCTIONS
-- ============================================================================

-- Function to count media by type for an article
CREATE OR REPLACE FUNCTION count_article_media(p_article_id TEXT)
RETURNS TABLE(
    total_media INTEGER,
    images INTEGER,
    videos INTEGER,
    completed INTEGER,
    failed INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*)::INTEGER as total_media,
        COUNT(*) FILTER (WHERE type = 'image')::INTEGER as images,
        COUNT(*) FILTER (WHERE type = 'video')::INTEGER as videos,
        COUNT(*) FILTER (WHERE status = 'completed')::INTEGER as completed,
        COUNT(*) FILTER (WHERE status = 'failed')::INTEGER as failed
    FROM media_files
    WHERE article_id = p_article_id;
END;
$$ LANGUAGE plpgsql;

-- Function to clean orphaned media files
CREATE OR REPLACE FUNCTION clean_orphaned_media()
RETURNS INTEGER AS $$
DECLARE
    v_deleted_count INTEGER;
BEGIN
    DELETE FROM media_files
    WHERE article_id NOT IN (SELECT article_id FROM articles)
    RETURNING COUNT(*) INTO v_deleted_count;
    
    RETURN v_deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- STATISTICS AND AGGREGATION FUNCTIONS
-- ============================================================================

-- Function to get daily article statistics
CREATE OR REPLACE FUNCTION get_daily_stats(p_date DATE DEFAULT CURRENT_DATE)
RETURNS JSONB AS $$
DECLARE
    v_stats JSONB;
BEGIN
    SELECT jsonb_build_object(
        'date', p_date,
        'articles_discovered', COUNT(*) FILTER (WHERE DATE(created_at) = p_date),
        'articles_parsed', COUNT(*) FILTER (WHERE DATE(parsed_at) = p_date),
        'articles_translated', COUNT(*) FILTER (WHERE DATE(wa.translated_at) = p_date),
        'articles_published', COUNT(*) FILTER (WHERE DATE(wa.created_at) = p_date AND wa.published_to_wp = true),
        'media_processed', (
            SELECT COUNT(*) FROM media_files 
            WHERE DATE(created_at) = p_date
        ),
        'sources_active', COUNT(DISTINCT source_id),
        'errors_count', (
            SELECT COUNT(*) FROM error_logs 
            WHERE DATE(timestamp) = p_date
        )
    ) INTO v_stats
    FROM articles a
    LEFT JOIN wordpress_articles wa ON a.article_id = wa.article_id
    WHERE DATE(a.created_at) = p_date 
       OR DATE(a.parsed_at) = p_date 
       OR DATE(wa.translated_at) = p_date;
    
    RETURN v_stats;
END;
$$ LANGUAGE plpgsql;

-- Function to get source performance ranking
CREATE OR REPLACE FUNCTION get_source_ranking(p_limit INTEGER DEFAULT 10)
RETURNS TABLE(
    source_id TEXT,
    source_name TEXT,
    total_articles INTEGER,
    success_rate DOUBLE PRECISION,
    avg_parse_time_ms DOUBLE PRECISION,
    health_score DOUBLE PRECISION,
    rank INTEGER
) AS $$
BEGIN
    RETURN QUERY
    WITH source_stats AS (
        SELECT 
            s.source_id,
            s.name as source_name,
            s.total_articles,
            s.success_rate,
            AVG(sm.parse_duration_ms) as avg_parse_time_ms,
            (check_source_health(s.source_id)->>'health_score')::DOUBLE PRECISION as health_score
        FROM sources s
        LEFT JOIN source_metrics sm ON s.source_id = sm.source_id
        WHERE sm.timestamp > CURRENT_TIMESTAMP - INTERVAL '7 days'
        GROUP BY s.source_id, s.name, s.total_articles, s.success_rate
    )
    SELECT 
        ss.*,
        ROW_NUMBER() OVER (ORDER BY ss.health_score DESC, ss.success_rate DESC)::INTEGER as rank
    FROM source_stats ss
    ORDER BY rank
    LIMIT p_limit;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- MONITORING AND ALERTING FUNCTIONS
-- ============================================================================

-- Function to check system thresholds
CREATE OR REPLACE FUNCTION check_system_thresholds()
RETURNS JSONB AS $$
DECLARE
    v_alerts JSONB[] := ARRAY[]::JSONB[];
    v_memory_percent DOUBLE PRECISION;
    v_disk_percent DOUBLE PRECISION;
    v_error_rate DOUBLE PRECISION;
BEGIN
    -- Check memory usage
    SELECT memory_percent INTO v_memory_percent
    FROM system_metrics
    ORDER BY timestamp DESC
    LIMIT 1;
    
    IF v_memory_percent > 80 THEN
        v_alerts := array_append(v_alerts, jsonb_build_object(
            'type', 'memory',
            'severity', CASE 
                WHEN v_memory_percent > 90 THEN 'critical'
                ELSE 'warning'
            END,
            'value', v_memory_percent,
            'threshold', 80,
            'message', format('Memory usage at %.1f%%', v_memory_percent)
        ));
    END IF;
    
    -- Check disk usage
    SELECT disk_percent INTO v_disk_percent
    FROM system_metrics
    ORDER BY timestamp DESC
    LIMIT 1;
    
    IF v_disk_percent > 85 THEN
        v_alerts := array_append(v_alerts, jsonb_build_object(
            'type', 'disk',
            'severity', CASE 
                WHEN v_disk_percent > 95 THEN 'critical'
                ELSE 'warning'
            END,
            'value', v_disk_percent,
            'threshold', 85,
            'message', format('Disk usage at %.1f%%', v_disk_percent)
        ));
    END IF;
    
    -- Check error rate (last hour)
    SELECT 
        COUNT(*) FILTER (WHERE error_level IN ('ERROR', 'CRITICAL')) * 100.0 / 
        NULLIF(COUNT(*), 0)
    INTO v_error_rate
    FROM error_logs
    WHERE timestamp > CURRENT_TIMESTAMP - INTERVAL '1 hour';
    
    IF v_error_rate > 5 THEN
        v_alerts := array_append(v_alerts, jsonb_build_object(
            'type', 'error_rate',
            'severity', CASE 
                WHEN v_error_rate > 10 THEN 'critical'
                ELSE 'warning'
            END,
            'value', v_error_rate,
            'threshold', 5,
            'message', format('Error rate at %.1f%%', v_error_rate)
        ));
    END IF;
    
    RETURN jsonb_build_object(
        'timestamp', CURRENT_TIMESTAMP,
        'alerts', v_alerts,
        'alert_count', array_length(v_alerts, 1)
    );
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- CLEANUP AND MAINTENANCE FUNCTIONS
-- ============================================================================

-- Function to archive old data
CREATE OR REPLACE FUNCTION archive_old_data(p_days_to_keep INTEGER DEFAULT 90)
RETURNS JSONB AS $$
DECLARE
    v_archived_articles INTEGER;
    v_archived_media INTEGER;
    v_archived_metrics INTEGER;
BEGIN
    -- Archive old monitoring data (keep less time)
    DELETE FROM system_metrics 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '30 days'
    RETURNING COUNT(*) INTO v_archived_metrics;
    
    DELETE FROM performance_metrics 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
    DELETE FROM source_metrics 
    WHERE timestamp < CURRENT_TIMESTAMP - INTERVAL '30 days';
    
    -- Mark old articles as deleted (soft delete)
    UPDATE articles 
    SET is_deleted = true, 
        deleted_at = CURRENT_TIMESTAMP,
        deleted_by = 'archive_function'
    WHERE created_at < CURRENT_TIMESTAMP - (p_days_to_keep || ' days')::INTERVAL
    AND is_deleted = false
    RETURNING COUNT(*) INTO v_archived_articles;
    
    -- Count media files that would be archived
    SELECT COUNT(*) INTO v_archived_media
    FROM media_files m
    JOIN articles a ON m.article_id = a.article_id
    WHERE a.is_deleted = true;
    
    RETURN jsonb_build_object(
        'archived_at', CURRENT_TIMESTAMP,
        'articles_archived', v_archived_articles,
        'media_files_affected', v_archived_media,
        'metrics_deleted', v_archived_metrics,
        'days_kept', p_days_to_keep
    );
END;
$$ LANGUAGE plpgsql;

-- Function to vacuum and analyze tables
CREATE OR REPLACE FUNCTION maintenance_vacuum_analyze()
RETURNS VOID AS $$
BEGIN
    -- Vacuum and analyze main tables
    VACUUM ANALYZE articles;
    VACUUM ANALYZE sources;
    VACUUM ANALYZE media_files;
    VACUUM ANALYZE wordpress_articles;
    
    -- Vacuum monitoring tables
    VACUUM ANALYZE system_metrics;
    VACUUM ANALYZE performance_metrics;
    VACUUM ANALYZE source_metrics;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- LOGGING AND AUDIT FUNCTIONS
-- ============================================================================

-- Function to log pipeline operations
CREATE OR REPLACE FUNCTION log_pipeline_operation(
    p_session_id BIGINT,
    p_phase TEXT,
    p_operation TEXT,
    p_status TEXT,
    p_details JSONB DEFAULT NULL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO pipeline_operations (
        session_id, 
        phase, 
        operation, 
        status, 
        details, 
        timestamp
    ) VALUES (
        p_session_id,
        p_phase,
        p_operation,
        p_status,
        p_details,
        CURRENT_TIMESTAMP
    );
END;
$$ LANGUAGE plpgsql;

-- Function to log errors with context
CREATE OR REPLACE FUNCTION log_error(
    p_error_level TEXT,
    p_error_type TEXT,
    p_error_message TEXT,
    p_stack_trace TEXT DEFAULT NULL,
    p_context JSONB DEFAULT NULL
)
RETURNS BIGINT AS $$
DECLARE
    v_error_id BIGINT;
BEGIN
    INSERT INTO error_logs (
        error_level,
        error_type,
        error_message,
        stack_trace,
        context,
        timestamp
    ) VALUES (
        p_error_level,
        p_error_type,
        p_error_message,
        p_stack_trace,
        p_context,
        CURRENT_TIMESTAMP
    ) RETURNING id INTO v_error_id;
    
    RETURN v_error_id;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- SEARCH AND DISCOVERY FUNCTIONS
-- ============================================================================

-- Function to search articles by keyword
CREATE OR REPLACE FUNCTION search_articles(
    p_query TEXT,
    p_limit INTEGER DEFAULT 20,
    p_offset INTEGER DEFAULT 0
)
RETURNS TABLE(
    article_id TEXT,
    title TEXT,
    content TEXT,
    published_date TIMESTAMP WITH TIME ZONE,
    source_name TEXT,
    relevance REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a.article_id,
        a.title,
        a.content,
        a.published_date,
        s.name as source_name,
        ts_rank(
            to_tsvector('english', COALESCE(a.title, '') || ' ' || COALESCE(a.content, '')),
            plainto_tsquery('english', p_query)
        ) as relevance
    FROM articles a
    JOIN sources s ON a.source_id = s.source_id
    WHERE to_tsvector('english', COALESCE(a.title, '') || ' ' || COALESCE(a.content, ''))
        @@ plainto_tsquery('english', p_query)
    AND a.is_deleted = false
    ORDER BY relevance DESC, a.published_date DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- Function to find duplicate articles
CREATE OR REPLACE FUNCTION find_duplicate_articles(p_threshold REAL DEFAULT 0.8)
RETURNS TABLE(
    article_id_1 TEXT,
    article_id_2 TEXT,
    title_1 TEXT,
    title_2 TEXT,
    similarity REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        a1.article_id as article_id_1,
        a2.article_id as article_id_2,
        a1.title as title_1,
        a2.title as title_2,
        similarity(a1.title, a2.title) as similarity
    FROM articles a1
    CROSS JOIN articles a2
    WHERE a1.article_id < a2.article_id
    AND a1.is_deleted = false
    AND a2.is_deleted = false
    AND similarity(a1.title, a2.title) > p_threshold
    ORDER BY similarity DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- COMMENTS
-- ============================================================================

COMMENT ON FUNCTION update_updated_at_column() IS 'Automatically updates the updated_at timestamp on row modification';
COMMENT ON FUNCTION generate_article_id(TEXT) IS 'Generates a unique article ID from URL using MD5 hash';
COMMENT ON FUNCTION article_exists(TEXT) IS 'Checks if an article with given URL exists and is not deleted';
COMMENT ON FUNCTION get_article_status(TEXT) IS 'Returns complete processing status for an article';
COMMENT ON FUNCTION update_source_stats(TEXT) IS 'Updates source statistics including total articles and success rate';
COMMENT ON FUNCTION check_source_health(TEXT) IS 'Performs comprehensive health check on a source';
COMMENT ON FUNCTION count_article_media(TEXT) IS 'Counts media files by type and status for an article';
COMMENT ON FUNCTION clean_orphaned_media() IS 'Removes media files that no longer have associated articles';
COMMENT ON FUNCTION get_daily_stats(DATE) IS 'Returns comprehensive daily statistics for the system';
COMMENT ON FUNCTION get_source_ranking(INTEGER) IS 'Returns top performing sources based on health score';
COMMENT ON FUNCTION check_system_thresholds() IS 'Checks system metrics against defined thresholds and returns alerts';
COMMENT ON FUNCTION archive_old_data(INTEGER) IS 'Archives old data based on retention policy';
COMMENT ON FUNCTION maintenance_vacuum_analyze() IS 'Performs vacuum and analyze on main tables';
COMMENT ON FUNCTION log_pipeline_operation(BIGINT, TEXT, TEXT, TEXT, JSONB) IS 'Logs pipeline operations with session tracking';
COMMENT ON FUNCTION log_error(TEXT, TEXT, TEXT, TEXT, JSONB) IS 'Logs errors with full context and returns error ID';
COMMENT ON FUNCTION search_articles(TEXT, INTEGER, INTEGER) IS 'Full-text search across article titles and content';
COMMENT ON FUNCTION find_duplicate_articles(REAL) IS 'Finds potentially duplicate articles based on title similarity';
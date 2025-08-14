-- ============================================================================
-- AI News Parser - PostgreSQL Schema Migration
-- From SQLite to Supabase PostgreSQL
-- Generated: 2025-08-13
-- ============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm"; -- For text search optimization
CREATE EXTENSION IF NOT EXISTS "btree_gin"; -- For composite indexes

-- ============================================================================
-- MAIN SCHEMA: Articles and Content Management
-- ============================================================================

-- Sources table: News sources configuration
CREATE TABLE IF NOT EXISTS sources (
    source_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    url TEXT NOT NULL,
    type TEXT,
    has_rss BOOLEAN DEFAULT false,
    last_status TEXT,
    last_error TEXT,
    success_rate DOUBLE PRECISION DEFAULT 0.0,
    last_parsed TIMESTAMP WITH TIME ZONE,
    total_articles INTEGER DEFAULT 0,
    selectors JSONB, -- Changed from TEXT to JSONB for better querying
    category TEXT,
    validation_status TEXT,
    circuit_breaker_failures INTEGER DEFAULT 0,
    circuit_breaker_reset_time TIMESTAMP WITH TIME ZONE,
    last_article_discovery TIMESTAMP WITH TIME ZONE,
    consecutive_failures INTEGER DEFAULT 0,
    rss_url TEXT,
    last_rss_check TIMESTAMP WITH TIME ZONE,
    rss_fetch_frequency INTEGER DEFAULT 3600,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Articles table: Main content storage
CREATE TABLE IF NOT EXISTS articles (
    article_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title TEXT,
    content TEXT,
    published_date TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    content_status TEXT DEFAULT 'pending',
    content_error TEXT,
    parsed_at TIMESTAMP WITH TIME ZONE,
    media_count INTEGER DEFAULT 0,
    media_status TEXT DEFAULT 'pending',
    description TEXT,
    discovered_via TEXT DEFAULT 'rss',
    llm_content_raw JSONB, -- Changed from TEXT to JSONB
    llm_translation_raw JSONB, -- Changed from TEXT to JSONB
    llm_tags_raw JSONB, -- Changed from TEXT to JSONB
    is_deleted BOOLEAN DEFAULT false,
    deleted_at TIMESTAMP WITH TIME ZONE,
    deleted_by TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Media files table: Images and videos associated with articles
CREATE TABLE IF NOT EXISTS media_files (
    id BIGSERIAL PRIMARY KEY, -- Changed from INTEGER to BIGSERIAL
    article_id TEXT NOT NULL REFERENCES articles(article_id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    type TEXT,
    file_path TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    media_id TEXT,
    source_id TEXT REFERENCES sources(source_id) ON DELETE SET NULL,
    file_size INTEGER,
    mime_type TEXT,
    width INTEGER,
    height INTEGER,
    alt_text TEXT,
    status TEXT DEFAULT 'pending',
    error TEXT,
    source TEXT,
    caption TEXT,
    wp_media_id INTEGER,
    wp_upload_status TEXT DEFAULT 'pending',
    wp_uploaded_at TIMESTAMP WITH TIME ZONE,
    alt_text_ru TEXT,
    caption_ru TEXT,
    image_order INTEGER,
    processing_session_id TEXT,
    wp_source_url TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- WordPress articles table: Translated content ready for publication
CREATE TABLE IF NOT EXISTS wordpress_articles (
    id BIGSERIAL PRIMARY KEY,
    article_id TEXT NOT NULL REFERENCES articles(article_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    excerpt TEXT,
    slug TEXT NOT NULL,
    categories JSONB, -- Changed from TEXT to JSONB
    tags JSONB, -- Changed from TEXT to JSONB
    _yoast_wpseo_title TEXT,
    _yoast_wpseo_metadesc TEXT,
    focus_keyword TEXT,
    featured_image_index INTEGER,
    images_data JSONB, -- Changed from TEXT to JSONB
    translation_status TEXT DEFAULT 'pending',
    translation_error TEXT,
    translated_at TIMESTAMP WITH TIME ZONE,
    published_to_wp BOOLEAN DEFAULT false,
    wp_post_id INTEGER,
    source_language TEXT,
    target_language TEXT DEFAULT 'ru',
    llm_model TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE,
    processing_session_id TEXT
);

-- Related links table: External links found in articles
CREATE TABLE IF NOT EXISTS related_links (
    id BIGSERIAL PRIMARY KEY,
    article_id TEXT NOT NULL REFERENCES articles(article_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    url TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Global configuration table: System-wide settings
CREATE TABLE IF NOT EXISTS global_config (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    description TEXT,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Pipeline operations table: Processing history
CREATE TABLE IF NOT EXISTS pipeline_operations (
    id BIGSERIAL PRIMARY KEY,
    session_id BIGINT,
    phase TEXT NOT NULL,
    operation TEXT NOT NULL,
    status TEXT NOT NULL,
    details JSONB, -- Changed from TEXT to JSONB
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tracked articles table: Change detection system
CREATE TABLE IF NOT EXISTS tracked_articles (
    article_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    published_date TIMESTAMP WITH TIME ZONE,
    content TEXT,
    last_checked TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    previous_hash TEXT,
    current_hash TEXT,
    change_detected BOOLEAN DEFAULT false,
    change_status TEXT,
    exported_to_main BOOLEAN DEFAULT false,
    exported_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Tracked URLs table: URL discovery and tracking
CREATE TABLE IF NOT EXISTS tracked_urls (
    id BIGSERIAL PRIMARY KEY,
    source_page_url TEXT NOT NULL,
    article_url TEXT NOT NULL,
    article_title TEXT,
    discovered_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_domain TEXT NOT NULL,
    is_new BOOLEAN DEFAULT true,
    exported_to_articles BOOLEAN DEFAULT false,
    exported_at TIMESTAMP WITH TIME ZONE
);

-- ============================================================================
-- MONITORING SCHEMA: System Performance and Metrics
-- ============================================================================

-- System metrics table: Overall system health
CREATE TABLE IF NOT EXISTS system_metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    cpu_percent DOUBLE PRECISION,
    memory_percent DOUBLE PRECISION,
    disk_percent DOUBLE PRECISION,
    process_count INTEGER,
    ainews_process_count INTEGER,
    network_connections INTEGER,
    open_files INTEGER
);

-- Performance metrics table: Application performance
CREATE TABLE IF NOT EXISTS performance_metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    metric_type TEXT NOT NULL,
    operation TEXT NOT NULL,
    duration_ms DOUBLE PRECISION,
    success BOOLEAN,
    error_message TEXT,
    details JSONB
);

-- Source metrics table: Per-source statistics
CREATE TABLE IF NOT EXISTS source_metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_id TEXT REFERENCES sources(source_id) ON DELETE CASCADE,
    articles_found INTEGER,
    articles_processed INTEGER,
    fetch_duration_ms DOUBLE PRECISION,
    parse_duration_ms DOUBLE PRECISION,
    error_count INTEGER,
    success_rate DOUBLE PRECISION
);

-- Article stats table: Article processing statistics
CREATE TABLE IF NOT EXISTS article_stats (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    total_articles INTEGER,
    pending_parsing INTEGER,
    parsed_articles INTEGER,
    failed_parsing INTEGER,
    pending_translation INTEGER,
    translated_articles INTEGER,
    published_to_wp INTEGER,
    articles_with_media INTEGER
);

-- Memory metrics table: Memory usage tracking
CREATE TABLE IF NOT EXISTS memory_metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    process_name TEXT,
    memory_mb DOUBLE PRECISION,
    cpu_percent DOUBLE PRECISION,
    threads INTEGER,
    open_files INTEGER
);

-- Memory alerts table: Memory threshold violations
CREATE TABLE IF NOT EXISTS memory_alerts (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    alert_type TEXT NOT NULL,
    memory_mb DOUBLE PRECISION,
    threshold_mb DOUBLE PRECISION,
    process_name TEXT,
    action_taken TEXT,
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP WITH TIME ZONE
);

-- RSS feed metrics table: RSS feed performance
CREATE TABLE IF NOT EXISTS rss_feed_metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_id TEXT REFERENCES sources(source_id) ON DELETE CASCADE,
    feed_url TEXT,
    fetch_time_ms DOUBLE PRECISION,
    items_found INTEGER,
    new_items INTEGER,
    parse_errors INTEGER,
    http_status_code INTEGER,
    error_message TEXT
);

-- Extract API metrics table: Firecrawl API usage
CREATE TABLE IF NOT EXISTS extract_api_metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    url TEXT NOT NULL,
    source_id TEXT,
    request_time_ms DOUBLE PRECISION,
    response_status INTEGER,
    content_length INTEGER,
    extraction_method TEXT,
    success BOOLEAN,
    cost_credits DOUBLE PRECISION
);

-- Extract API errors table: API error tracking
CREATE TABLE IF NOT EXISTS extract_api_errors (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    url TEXT NOT NULL,
    error_type TEXT,
    error_message TEXT,
    status_code INTEGER,
    retry_count INTEGER,
    resolved BOOLEAN DEFAULT false
);

-- Parsing progress table: Real-time parsing status
CREATE TABLE IF NOT EXISTS parsing_progress (
    id BIGSERIAL PRIMARY KEY,
    session_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    total_items INTEGER,
    processed_items INTEGER,
    failed_items INTEGER,
    current_item TEXT,
    status TEXT,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Emergency snapshots table: System state during issues
CREATE TABLE IF NOT EXISTS emergency_snapshots (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    trigger_reason TEXT NOT NULL,
    memory_state JSONB,
    process_state JSONB,
    active_operations JSONB,
    error_context JSONB,
    recovery_action TEXT
);

-- Watchdog actions table: Automated system interventions
CREATE TABLE IF NOT EXISTS watchdog_actions (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    action_type TEXT NOT NULL,
    target_process TEXT,
    reason TEXT,
    metrics_before JSONB,
    metrics_after JSONB,
    success BOOLEAN,
    error_message TEXT
);

-- Source health reports table: Periodic source health checks
CREATE TABLE IF NOT EXISTS source_health_reports (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    source_id TEXT REFERENCES sources(source_id) ON DELETE CASCADE,
    health_score DOUBLE PRECISION,
    availability_percent DOUBLE PRECISION,
    avg_response_time_ms DOUBLE PRECISION,
    error_rate DOUBLE PRECISION,
    last_successful_fetch TIMESTAMP WITH TIME ZONE,
    consecutive_failures INTEGER,
    recommendations JSONB
);

-- Error logs table: Centralized error logging
CREATE TABLE IF NOT EXISTS error_logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    error_level TEXT NOT NULL,
    error_type TEXT,
    error_message TEXT,
    stack_trace TEXT,
    context JSONB,
    resolved BOOLEAN DEFAULT false,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT
);

-- Context enrichment metrics table: LLM enrichment tracking
CREATE TABLE IF NOT EXISTS context_enrichment_metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    article_id TEXT REFERENCES articles(article_id) ON DELETE CASCADE,
    enrichment_type TEXT,
    llm_model TEXT,
    tokens_used INTEGER,
    cost_usd DOUBLE PRECISION,
    processing_time_ms DOUBLE PRECISION,
    success BOOLEAN,
    error_message TEXT
);

-- Supabase performance metrics table: Database performance
CREATE TABLE IF NOT EXISTS supabase_performance_metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    query_type TEXT,
    table_name TEXT,
    execution_time_ms DOUBLE PRECISION,
    rows_affected INTEGER,
    query_hash TEXT,
    success BOOLEAN,
    error_message TEXT
);

-- API cost tracking table: External API usage costs
CREATE TABLE IF NOT EXISTS api_cost_tracking (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    api_provider TEXT NOT NULL,
    endpoint TEXT,
    tokens_used INTEGER,
    requests_made INTEGER,
    cost_usd DOUBLE PRECISION,
    cost_period TEXT,
    quota_used_percent DOUBLE PRECISION
);

-- Vector search performance table: Vector search metrics
CREATE TABLE IF NOT EXISTS vector_search_performance (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    search_query TEXT,
    vector_dimension INTEGER,
    results_returned INTEGER,
    search_time_ms DOUBLE PRECISION,
    similarity_threshold DOUBLE PRECISION,
    index_used TEXT
);

-- Context pipeline metrics table: Pipeline performance
CREATE TABLE IF NOT EXISTS context_pipeline_metrics (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    pipeline_stage TEXT,
    articles_processed INTEGER,
    total_time_ms DOUBLE PRECISION,
    avg_time_per_article_ms DOUBLE PRECISION,
    errors_encountered INTEGER,
    memory_used_mb DOUBLE PRECISION
);

-- ============================================================================
-- INDEXES: Performance Optimization
-- ============================================================================

-- Articles indexes
CREATE INDEX idx_articles_source_id ON articles(source_id);
CREATE INDEX idx_articles_content_status ON articles(content_status);
CREATE INDEX idx_articles_published_date ON articles(published_date DESC);
CREATE INDEX idx_articles_created_at ON articles(created_at DESC);
CREATE INDEX idx_articles_is_deleted ON articles(is_deleted);
CREATE INDEX idx_articles_discovered_via ON articles(discovered_via);
CREATE INDEX idx_articles_url_hash ON articles(MD5(url)); -- For fast URL lookups

-- Media files indexes
CREATE INDEX idx_media_files_article_id ON media_files(article_id);
CREATE INDEX idx_media_files_source_id ON media_files(source_id);
CREATE INDEX idx_media_files_status ON media_files(status);
CREATE INDEX idx_media_files_wp_upload_status ON media_files(wp_upload_status);
CREATE INDEX idx_media_files_processing_session ON media_files(processing_session_id);

-- WordPress articles indexes
CREATE INDEX idx_wordpress_articles_article_id ON wordpress_articles(article_id);
CREATE INDEX idx_wordpress_articles_translation_status ON wordpress_articles(translation_status);
CREATE INDEX idx_wordpress_articles_published_to_wp ON wordpress_articles(published_to_wp);
CREATE INDEX idx_wordpress_articles_wp_post_id ON wordpress_articles(wp_post_id);
CREATE INDEX idx_wordpress_articles_slug ON wordpress_articles(slug);

-- Sources indexes
CREATE INDEX idx_sources_type ON sources(type);
CREATE INDEX idx_sources_has_rss ON sources(has_rss);
CREATE INDEX idx_sources_category ON sources(category);
CREATE INDEX idx_sources_last_parsed ON sources(last_parsed DESC);
CREATE INDEX idx_sources_validation_status ON sources(validation_status);

-- Related links indexes
CREATE INDEX idx_related_links_article_id ON related_links(article_id);

-- Pipeline operations indexes
CREATE INDEX idx_pipeline_operations_session_id ON pipeline_operations(session_id);
CREATE INDEX idx_pipeline_operations_phase ON pipeline_operations(phase);
CREATE INDEX idx_pipeline_operations_timestamp ON pipeline_operations(timestamp DESC);

-- Tracked articles indexes
CREATE INDEX idx_tracked_articles_source_id ON tracked_articles(source_id);
CREATE INDEX idx_tracked_articles_change_detected ON tracked_articles(change_detected);
CREATE INDEX idx_tracked_articles_exported_to_main ON tracked_articles(exported_to_main);
CREATE INDEX idx_tracked_articles_url_hash ON tracked_articles(MD5(url));

-- Tracked URLs indexes
CREATE INDEX idx_tracked_urls_source_domain ON tracked_urls(source_domain);
CREATE INDEX idx_tracked_urls_is_new ON tracked_urls(is_new);
CREATE INDEX idx_tracked_urls_exported_to_articles ON tracked_urls(exported_to_articles);
CREATE INDEX idx_tracked_urls_discovered_at ON tracked_urls(discovered_at DESC);

-- Monitoring indexes
CREATE INDEX idx_system_metrics_timestamp ON system_metrics(timestamp DESC);
CREATE INDEX idx_performance_metrics_timestamp ON performance_metrics(timestamp DESC);
CREATE INDEX idx_performance_metrics_metric_type ON performance_metrics(metric_type);
CREATE INDEX idx_source_metrics_source_id ON source_metrics(source_id);
CREATE INDEX idx_source_metrics_timestamp ON source_metrics(timestamp DESC);
CREATE INDEX idx_article_stats_timestamp ON article_stats(timestamp DESC);
CREATE INDEX idx_memory_metrics_timestamp ON memory_metrics(timestamp DESC);
CREATE INDEX idx_memory_alerts_resolved ON memory_alerts(resolved);
CREATE INDEX idx_rss_feed_metrics_source_id ON rss_feed_metrics(source_id);
CREATE INDEX idx_extract_api_metrics_timestamp ON extract_api_metrics(timestamp DESC);
CREATE INDEX idx_error_logs_timestamp ON error_logs(timestamp DESC);
CREATE INDEX idx_error_logs_resolved ON error_logs(resolved);

-- Full-text search indexes (using GIN)
CREATE INDEX idx_articles_title_gin ON articles USING gin(to_tsvector('english', title));
CREATE INDEX idx_articles_content_gin ON articles USING gin(to_tsvector('english', content));
CREATE INDEX idx_wordpress_articles_title_gin ON wordpress_articles USING gin(to_tsvector('russian', title));
CREATE INDEX idx_wordpress_articles_content_gin ON wordpress_articles USING gin(to_tsvector('russian', content));

-- ============================================================================
-- CONSTRAINTS: Data Integrity
-- ============================================================================

-- Unique constraints
ALTER TABLE articles ADD CONSTRAINT unique_article_url UNIQUE(url);
ALTER TABLE sources ADD CONSTRAINT unique_source_url UNIQUE(url);
ALTER TABLE wordpress_articles ADD CONSTRAINT unique_wp_article_id UNIQUE(article_id);
ALTER TABLE wordpress_articles ADD CONSTRAINT unique_wp_slug UNIQUE(slug);
ALTER TABLE tracked_urls ADD CONSTRAINT unique_tracked_url UNIQUE(article_url);

-- Check constraints
ALTER TABLE articles ADD CONSTRAINT check_content_status 
    CHECK (content_status IN ('pending', 'processing', 'completed', 'failed', 'skipped'));
    
ALTER TABLE articles ADD CONSTRAINT check_media_status 
    CHECK (media_status IN ('pending', 'processing', 'completed', 'failed', 'skipped'));
    
ALTER TABLE wordpress_articles ADD CONSTRAINT check_translation_status 
    CHECK (translation_status IN ('pending', 'processing', 'completed', 'failed'));
    
ALTER TABLE sources ADD CONSTRAINT check_validation_status 
    CHECK (validation_status IN ('valid', 'invalid', 'checking', 'unknown'));

-- ============================================================================
-- COMMENTS: Documentation
-- ============================================================================

-- Table comments
COMMENT ON TABLE articles IS 'Main articles table storing all discovered and parsed news articles';
COMMENT ON TABLE sources IS 'News sources configuration and health tracking';
COMMENT ON TABLE media_files IS 'Media files (images, videos) associated with articles';
COMMENT ON TABLE wordpress_articles IS 'Translated articles ready for WordPress publication';
COMMENT ON TABLE system_metrics IS 'System-wide performance and resource usage metrics';
COMMENT ON TABLE pipeline_operations IS 'Processing pipeline execution history and status';

-- Column comments
COMMENT ON COLUMN articles.llm_content_raw IS 'Raw LLM response for content extraction stored as JSONB';
COMMENT ON COLUMN articles.llm_translation_raw IS 'Raw LLM response for translation stored as JSONB';
COMMENT ON COLUMN articles.llm_tags_raw IS 'Raw LLM response for tag generation stored as JSONB';
COMMENT ON COLUMN sources.selectors IS 'CSS selectors for content extraction stored as JSONB';
COMMENT ON COLUMN sources.circuit_breaker_failures IS 'Number of consecutive failures before circuit breaker activates';
COMMENT ON COLUMN media_files.processing_session_id IS 'Session ID for batch processing operations';
COMMENT ON COLUMN wordpress_articles.images_data IS 'Structured data about images in the article stored as JSONB';
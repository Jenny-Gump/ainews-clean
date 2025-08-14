-- Supabase schema for AI News Parser
-- Run this in Supabase SQL Editor to create tables

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Articles table
CREATE TABLE IF NOT EXISTS articles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    article_id TEXT UNIQUE NOT NULL,
    source_id TEXT,
    url TEXT NOT NULL,
    title TEXT,
    content TEXT,
    summary TEXT,
    published_at TIMESTAMP,
    content_status TEXT DEFAULT 'pending',
    media_status TEXT DEFAULT 'pending',
    error_message TEXT,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX idx_articles_status ON articles(content_status);
CREATE INDEX idx_articles_source ON articles(source_id);
CREATE INDEX idx_articles_created ON articles(created_at DESC);

-- Media files table
CREATE TABLE IF NOT EXISTS media_files (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    article_id TEXT REFERENCES articles(article_id) ON DELETE CASCADE,
    url TEXT NOT NULL,
    local_path TEXT,
    alt_text TEXT,
    alt_text_ru TEXT,
    width INTEGER,
    height INTEGER,
    file_size INTEGER,
    mime_type TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for article_id
CREATE INDEX idx_media_article ON media_files(article_id);

-- WordPress articles table
CREATE TABLE IF NOT EXISTS wordpress_articles (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    article_id TEXT REFERENCES articles(article_id) ON DELETE CASCADE,
    wordpress_id INTEGER UNIQUE,
    title_ru TEXT,
    content_ru TEXT,
    excerpt_ru TEXT,
    tags TEXT[],
    categories INTEGER[],
    featured_image_id INTEGER,
    status TEXT DEFAULT 'draft',
    published_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create index for article_id
CREATE INDEX idx_wp_article ON wordpress_articles(article_id);
CREATE INDEX idx_wp_wordpress_id ON wordpress_articles(wordpress_id);

-- Sources table
CREATE TABLE IF NOT EXISTS sources (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    source_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    url TEXT,
    feed_url TEXT,
    language TEXT DEFAULT 'en',
    category TEXT,
    active BOOLEAN DEFAULT true,
    last_checked TIMESTAMP,
    error_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index for active sources
CREATE INDEX idx_sources_active ON sources(active);

-- Processing logs table (for monitoring)
CREATE TABLE IF NOT EXISTS processing_logs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    article_id TEXT,
    phase TEXT NOT NULL, -- 'rss', 'parse', 'media', 'translate', 'publish'
    status TEXT NOT NULL, -- 'started', 'completed', 'failed'
    message TEXT,
    duration_ms INTEGER,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for logs
CREATE INDEX idx_logs_article ON processing_logs(article_id);
CREATE INDEX idx_logs_phase ON processing_logs(phase);
CREATE INDEX idx_logs_created ON processing_logs(created_at DESC);

-- API usage tracking table
CREATE TABLE IF NOT EXISTS api_usage (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    service TEXT NOT NULL, -- 'firecrawl', 'deepseek', 'openai'
    endpoint TEXT,
    article_id TEXT,
    tokens_input INTEGER,
    tokens_output INTEGER,
    cost_usd DECIMAL(10, 6),
    response_time_ms INTEGER,
    status_code INTEGER,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for API usage
CREATE INDEX idx_api_service ON api_usage(service);
CREATE INDEX idx_api_created ON api_usage(created_at DESC);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Add triggers to update updated_at
CREATE TRIGGER update_articles_updated_at BEFORE UPDATE ON articles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_sources_updated_at BEFORE UPDATE ON sources
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for article statistics
CREATE OR REPLACE VIEW article_stats AS
SELECT 
    COUNT(*) as total_articles,
    COUNT(CASE WHEN content_status = 'pending' THEN 1 END) as pending_articles,
    COUNT(CASE WHEN content_status = 'parsed' THEN 1 END) as parsed_articles,
    COUNT(CASE WHEN content_status = 'published' THEN 1 END) as published_articles,
    COUNT(CASE WHEN content_status = 'failed' THEN 1 END) as failed_articles,
    COUNT(DISTINCT source_id) as active_sources
FROM articles;

-- Create view for recent articles with details
CREATE OR REPLACE VIEW recent_articles_view AS
SELECT 
    a.article_id,
    a.title,
    a.url,
    a.source_id,
    s.name as source_name,
    a.content_status,
    a.media_status,
    wa.wordpress_id,
    wa.title_ru,
    a.created_at,
    a.updated_at
FROM articles a
LEFT JOIN sources s ON a.source_id = s.source_id
LEFT JOIN wordpress_articles wa ON a.article_id = wa.article_id
ORDER BY a.created_at DESC
LIMIT 100;

-- Row Level Security (RLS) - Optional but recommended
-- Enable RLS on all tables
ALTER TABLE articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE media_files ENABLE ROW LEVEL SECURITY;
ALTER TABLE wordpress_articles ENABLE ROW LEVEL SECURITY;
ALTER TABLE sources ENABLE ROW LEVEL SECURITY;
ALTER TABLE processing_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_usage ENABLE ROW LEVEL SECURITY;

-- Create policies for service role (full access)
CREATE POLICY "Service role has full access to articles" ON articles
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role has full access to media_files" ON media_files
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role has full access to wordpress_articles" ON wordpress_articles
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role has full access to sources" ON sources
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role has full access to processing_logs" ON processing_logs
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

CREATE POLICY "Service role has full access to api_usage" ON api_usage
    FOR ALL USING (auth.jwt() ->> 'role' = 'service_role');

-- Create policies for anon role (read-only for some tables)
CREATE POLICY "Anon can read published articles" ON articles
    FOR SELECT USING (content_status = 'published');

CREATE POLICY "Anon can read sources" ON sources
    FOR SELECT USING (active = true);

-- Grant permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO service_role;
GRANT SELECT ON articles, sources TO anon;
GRANT SELECT ON article_stats, recent_articles_view TO anon;

-- Insert some initial sources (optional)
INSERT INTO sources (source_id, name, feed_url, language, category, active) VALUES
('openai', 'OpenAI Blog', 'https://openai.com/blog/rss.xml', 'en', 'AI Research', true),
('anthropic', 'Anthropic News', 'https://www.anthropic.com/rss.xml', 'en', 'AI Research', true),
('mit_ai', 'MIT AI News', 'https://news.mit.edu/rss/topic/artificial-intelligence2', 'en', 'Research', true)
ON CONFLICT (source_id) DO NOTHING;
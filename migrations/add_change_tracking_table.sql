-- Migration: Add Change Tracking Table
-- Purpose: Track article changes and new articles from sources
-- Date: 2025-08-06

-- Create tracked_articles table (mirror of articles structure)
CREATE TABLE IF NOT EXISTS tracked_articles (
    -- Same fields as articles for compatibility
    article_id TEXT PRIMARY KEY,
    source_id TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    title TEXT NOT NULL,
    description TEXT,
    published_date DATETIME,
    content TEXT,
    
    -- Tracking specific fields
    last_checked DATETIME DEFAULT CURRENT_TIMESTAMP,
    previous_hash TEXT,
    current_hash TEXT,
    change_detected BOOLEAN DEFAULT FALSE,
    change_status TEXT, -- 'new', 'changed', 'unchanged'
    
    -- For export management
    exported_to_main BOOLEAN DEFAULT FALSE,
    exported_at DATETIME,
    
    -- Metadata
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_tracked_url ON tracked_articles(url);
CREATE INDEX IF NOT EXISTS idx_tracked_source ON tracked_articles(source_id);
CREATE INDEX IF NOT EXISTS idx_tracked_exported ON tracked_articles(exported_to_main);
CREATE INDEX IF NOT EXISTS idx_tracked_change ON tracked_articles(change_detected);
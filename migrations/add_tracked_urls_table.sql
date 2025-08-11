-- Migration: Add tracked_urls table for URL extraction from change tracking
-- Date: 2025-08-07
-- Purpose: Track discovered article URLs from scanned pages

CREATE TABLE IF NOT EXISTS tracked_urls (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_page_url TEXT NOT NULL,           -- https://mistral.ai/news
    article_url TEXT NOT NULL,               -- https://mistral.ai/news/article-1
    article_title TEXT,                      -- заголовок статьи
    discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    source_domain TEXT NOT NULL,             -- mistral_ai
    is_new BOOLEAN DEFAULT 1,                -- новый URL с последнего скана
    exported_to_articles BOOLEAN DEFAULT 0, -- экспортирован в articles
    exported_at DATETIME,                    -- время экспорта
    UNIQUE(source_page_url, article_url)
);

-- Индексы для производительности
CREATE INDEX IF NOT EXISTS idx_tracked_urls_source_page ON tracked_urls(source_page_url);
CREATE INDEX IF NOT EXISTS idx_tracked_urls_domain ON tracked_urls(source_domain);
CREATE INDEX IF NOT EXISTS idx_tracked_urls_is_new ON tracked_urls(is_new);
CREATE INDEX IF NOT EXISTS idx_tracked_urls_exported ON tracked_urls(exported_to_articles);
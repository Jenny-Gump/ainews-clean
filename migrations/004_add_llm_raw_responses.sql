-- Migration: 004_add_llm_raw_responses.sql
-- Purpose: Store raw LLM responses for debugging and analysis
-- Date: 2025-08-09
-- Description: Adds fields to store raw responses from DeepSeek/GPT-4o/GPT-3.5
--              to help debug JSON parsing errors and understand LLM outputs

-- Add field for raw content cleaning response from DeepSeek
-- Used in content_parser.py during content extraction phase
ALTER TABLE articles ADD COLUMN llm_content_raw TEXT;

-- Add field for raw translation response from DeepSeek/GPT-4o
-- Used in wordpress_publisher.py during article translation phase
ALTER TABLE articles ADD COLUMN llm_translation_raw TEXT;

-- Add field for raw tags generation response from DeepSeek/GPT-3.5
-- Used in wordpress_publisher.py during tag generation phase
ALTER TABLE articles ADD COLUMN llm_tags_raw TEXT;

-- Create indexes for faster queries when searching for articles with LLM responses
-- These partial indexes only include rows where the field is not NULL
CREATE INDEX idx_articles_llm_content ON articles(article_id) WHERE llm_content_raw IS NOT NULL;
CREATE INDEX idx_articles_llm_translation ON articles(article_id) WHERE llm_translation_raw IS NOT NULL;
CREATE INDEX idx_articles_llm_tags ON articles(article_id) WHERE llm_tags_raw IS NOT NULL;

-- Verification query to check migration was successful
-- SELECT COUNT(*) as new_columns FROM pragma_table_info('articles') 
-- WHERE name IN ('llm_content_raw', 'llm_translation_raw', 'llm_tags_raw');
-- Expected result: 3
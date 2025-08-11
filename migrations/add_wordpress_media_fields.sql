-- Migration to add WordPress media fields to media_files table
-- Run this script to update the database schema

-- Add WordPress media ID field
ALTER TABLE media_files ADD COLUMN wp_media_id INTEGER;

-- Add WordPress upload status field
ALTER TABLE media_files ADD COLUMN wp_upload_status TEXT DEFAULT 'pending';

-- Add WordPress upload timestamp
ALTER TABLE media_files ADD COLUMN wp_uploaded_at DATETIME;

-- Add translated metadata fields
ALTER TABLE media_files ADD COLUMN alt_text_ru TEXT;
ALTER TABLE media_files ADD COLUMN caption_ru TEXT;

-- Add WordPress source URL field (for local media URLs)
ALTER TABLE media_files ADD COLUMN wp_source_url TEXT;

-- Create indexes for faster queries
CREATE INDEX idx_media_wp_status ON media_files(wp_upload_status) WHERE wp_upload_status IS NOT NULL;
CREATE INDEX idx_media_wp_id ON media_files(wp_media_id) WHERE wp_media_id IS NOT NULL;
CREATE INDEX idx_media_wp_source_url ON media_files(wp_source_url) WHERE wp_source_url IS NOT NULL;
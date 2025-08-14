-- Migration: Drop unused monitoring tables
-- Date: August 14, 2025
-- Description: Remove empty tables that were never used after Supabase migration

-- These tables have 0 records and are not used anywhere in the codebase
DROP TABLE IF EXISTS process_monitoring CASCADE;
DROP TABLE IF EXISTS memory_alerts CASCADE;
DROP TABLE IF EXISTS system_alerts CASCADE;
DROP TABLE IF EXISTS wordpress_sync_status CASCADE;
DROP TABLE IF EXISTS data_quality_metrics CASCADE;
DROP TABLE IF EXISTS llm_usage_tracking CASCADE;
DROP TABLE IF EXISTS session_management CASCADE;
DROP TABLE IF EXISTS audit_logs CASCADE;
DROP TABLE IF EXISTS api_usage_metrics CASCADE;

-- Log the cleanup
INSERT INTO global_config (key, value, updated_at) 
VALUES (
    'migration_drop_unused_tables', 
    '{"dropped_tables": ["process_monitoring", "memory_alerts", "system_alerts", "wordpress_sync_status", "data_quality_metrics", "llm_usage_tracking", "session_management", "audit_logs", "api_usage_metrics"], "date": "2025-08-14"}',
    NOW()
) 
ON CONFLICT (key) 
DO UPDATE SET 
    value = EXCLUDED.value,
    updated_at = NOW();
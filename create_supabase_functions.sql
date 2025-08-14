-- Create RPC function to get top sources with article counts
CREATE OR REPLACE FUNCTION get_top_sources()
RETURNS TABLE (
    source_id TEXT,
    name TEXT,
    article_count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.source_id,
        s.name,
        COUNT(a.article_id) as article_count
    FROM sources s
    LEFT JOIN articles a ON s.source_id = a.source_id
    GROUP BY s.source_id, s.name
    ORDER BY article_count DESC
    LIMIT 10;
END;
$$ LANGUAGE plpgsql;
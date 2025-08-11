-- Useful queries for analyzing LLM raw responses

-- 1. Find articles with JSON parsing errors
SELECT 
    article_id,
    title,
    content_error,
    LENGTH(llm_content_raw) as content_len,
    LENGTH(llm_translation_raw) as trans_len,
    LENGTH(llm_tags_raw) as tags_len,
    SUBSTR(llm_content_raw, 1, 200) as content_preview
FROM articles 
WHERE content_error LIKE '%JSON%' 
   OR content_error LIKE '%parse%'
   OR content_error LIKE '%escape%'
ORDER BY created_at DESC
LIMIT 10;

-- 2. Check which LLM responses we have for recent articles
SELECT 
    article_id,
    title,
    CASE WHEN llm_content_raw IS NOT NULL THEN '✓' ELSE '✗' END as has_content,
    CASE WHEN llm_translation_raw IS NOT NULL THEN '✓' ELSE '✗' END as has_translation,
    CASE WHEN llm_tags_raw IS NOT NULL THEN '✓' ELSE '✗' END as has_tags,
    content_status,
    media_status
FROM articles 
WHERE created_at > datetime('now', '-1 day')
ORDER BY created_at DESC;

-- 3. Find articles where LLM responded but processing failed
SELECT 
    article_id,
    title,
    content_status,
    content_error,
    LENGTH(llm_content_raw) as resp_size
FROM articles 
WHERE llm_content_raw IS NOT NULL 
  AND content_status = 'failed'
ORDER BY created_at DESC;

-- 4. Statistics on LLM response sizes
SELECT 
    COUNT(*) as total_articles,
    COUNT(llm_content_raw) as with_content_resp,
    COUNT(llm_translation_raw) as with_trans_resp,
    COUNT(llm_tags_raw) as with_tags_resp,
    AVG(LENGTH(llm_content_raw)) as avg_content_size,
    AVG(LENGTH(llm_translation_raw)) as avg_trans_size,
    AVG(LENGTH(llm_tags_raw)) as avg_tags_size
FROM articles;

-- 5. View raw LLM response for specific article
-- Replace 'ARTICLE_ID' with actual article_id
SELECT 
    article_id,
    title,
    llm_content_raw,
    llm_translation_raw,
    llm_tags_raw
FROM articles 
WHERE article_id = 'ARTICLE_ID';

-- 6. Find articles with very short LLM responses (potential errors)
SELECT 
    article_id,
    title,
    LENGTH(llm_content_raw) as content_len,
    LENGTH(llm_translation_raw) as trans_len,
    content_error
FROM articles 
WHERE (llm_content_raw IS NOT NULL AND LENGTH(llm_content_raw) < 100)
   OR (llm_translation_raw IS NOT NULL AND LENGTH(llm_translation_raw) < 100)
ORDER BY created_at DESC;
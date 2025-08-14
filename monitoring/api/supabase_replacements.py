"""
Supabase replacements for all SQLite functions in articles.py
"""
from fastapi import HTTPException
from typing import Optional, Dict, Any, List
from datetime import datetime
import json
import os
import logging

logger = logging.getLogger(__name__)

def get_supabase_client():
    """Get Supabase client instance"""
    from supabase import create_client, Client
    
    url = os.getenv("SUPABASE_URL", "https://mtguynupyltlqiwhmilc.supabase.co")
    key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not key:
        raise HTTPException(status_code=500, detail="Supabase key not configured")
    
    return create_client(url, key)

async def get_article_details_supabase(article_id: str) -> Dict[str, Any]:
    """Get article details from Supabase"""
    supabase = get_supabase_client()
    
    # Get article info
    article_result = supabase.table('articles').select('*').eq('article_id', article_id).single().execute()
    
    if not article_result.data:
        raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
    
    article = article_result.data
    
    # Get source info separately
    source_info = None
    if article.get('source_id'):
        source_result = supabase.table('sources').select('name, url, category').eq('source_id', article['source_id']).single().execute()
        if source_result.data:
            source_info = source_result.data
            # Map category to type for compatibility
            source_info['type'] = source_info.get('category', 'rss')
    
    # Get media files
    media_result = supabase.table('media_files').select('*').eq('article_id', article_id).execute()
    media_files = []
    for media in media_result.data if media_result.data else []:
        media_files.append({
            "file_id": media.get("id"),
            "original_url": media.get("url"),
            "local_path": media.get("file_path") or media.get("local_path"),
            "alt_text": media.get("alt_text"),
            "file_size": media.get("file_size"),
            "width": media.get("width"),
            "height": media.get("height"),
            "status": media.get("status", "pending")
        })
    
    # Get WordPress data
    tags = []
    categories = []
    summary = ""
    
    try:
        wp_result = supabase.table('wordpress_articles').select('*').eq('article_id', article_id).maybe_single().execute()
        if wp_result and wp_result.data:
            wp_data = wp_result.data
            if wp_data.get("tags"):
                try:
                    tags = json.loads(wp_data["tags"]) if isinstance(wp_data["tags"], str) else wp_data["tags"]
                except:
                    tags = []
            if wp_data.get("categories"):
                try:
                    categories = json.loads(wp_data["categories"]) if isinstance(wp_data["categories"], str) else wp_data["categories"]
                except:
                    categories = []
            summary = wp_data.get("excerpt", "")
    except Exception as e:
        # WordPress data may not exist for all articles
        pass
    
    # Calculate word count
    word_count = len(article.get("content", "").split()) if article.get("content") else 0
    
    return {
        "article_id": article.get("article_id"),
        "title": article.get("title"),
        "url": article.get("url"),
        "content": article.get("content"),
        "summary": summary,
        "source_id": article.get("source_id"),
        "published_at": article.get("published_date"),
        "created_at": article.get("created_at"),
        "updated_at": article.get("parsed_at"),
        "status": article.get("content_status"),
        "has_media": len(media_files) > 0,
        "media_count": len(media_files),
        "word_count": word_count,
        "tags": tags,
        "categories": categories,
        "source": {
            "name": source_info.get("name", "Unknown") if source_info else "Unknown",
            "url": source_info.get("url", "") if source_info else "",
            "type": source_info.get("type", "rss") if source_info else "rss"
        } if source_info else None,
        "media_files": media_files
    }

async def restore_article_supabase(article_id: str) -> Dict[str, Any]:
    """Restore a soft-deleted article in Supabase"""
    supabase = get_supabase_client()
    
    # Check if article exists and is deleted
    check_result = supabase.table('articles').select('article_id').eq('article_id', article_id).eq('is_deleted', 1).single().execute()
    
    if not check_result.data:
        raise HTTPException(status_code=404, detail=f"Deleted article {article_id} not found")
    
    # Restore the article
    update_result = supabase.table('articles').update({
        'is_deleted': 0,
        'deleted_at': None,
        'deleted_by': None,
        'content_status': 'pending'
    }).eq('article_id', article_id).execute()
    
    return {
        "success": True,
        "message": f"Article {article_id} restored successfully",
        "article_id": article_id
    }

async def delete_article_supabase(article_id: str) -> Dict[str, Any]:
    """Soft delete an article in Supabase"""
    supabase = get_supabase_client()
    
    # Check if article exists and is not already deleted
    check_result = supabase.table('articles').select('article_id').eq('article_id', article_id).eq('is_deleted', 0).single().execute()
    
    if not check_result.data:
        raise HTTPException(status_code=404, detail=f"Article {article_id} not found or already deleted")
    
    # Soft delete the article
    update_result = supabase.table('articles').update({
        'is_deleted': 1,
        'deleted_at': datetime.now().isoformat(),
        'deleted_by': 'dashboard',
        'content_status': 'deleted'
    }).eq('article_id', article_id).execute()
    
    return {
        "success": True,
        "message": f"Article {article_id} marked as deleted",
        "article_id": article_id
    }

async def reprocess_article_supabase(article_id: str) -> Dict[str, Any]:
    """Mark an article for reprocessing in Supabase"""
    supabase = get_supabase_client()
    
    # Check if article exists
    check_result = supabase.table('articles').select('article_id, content_status').eq('article_id', article_id).single().execute()
    
    if not check_result.data:
        raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
    
    old_status = check_result.data.get('content_status')
    
    # Update status to trigger reprocessing
    update_result = supabase.table('articles').update({
        'content_status': 'pending_reprocess',
        'parsed_at': datetime.now().isoformat()
    }).eq('article_id', article_id).execute()
    
    return {
        "success": True,
        "message": f"Article {article_id} marked for reprocessing",
        "article_id": article_id,
        "old_status": old_status,
        "new_status": "pending_reprocess"
    }

async def bulk_reprocess_articles_supabase(article_ids: List[str]) -> Dict[str, Any]:
    """Mark multiple articles for reprocessing"""
    supabase = get_supabase_client()
    
    updated_count = 0
    not_found = []
    
    for article_id in article_ids:
        try:
            update_result = supabase.table('articles').update({
                'content_status': 'pending_reprocess',
                'parsed_at': datetime.now().isoformat()
            }).eq('article_id', article_id).execute()
            
            if update_result.data:
                updated_count += 1
            else:
                not_found.append(article_id)
        except:
            not_found.append(article_id)
    
    return {
        "success": True,
        "message": f"Bulk reprocess completed: {updated_count} articles marked for reprocessing",
        "requested": len(article_ids),
        "updated": updated_count,
        "not_found": not_found
    }

async def get_search_suggestions_supabase(query: str, limit: int = 10) -> Dict[str, Any]:
    """Get search suggestions from Supabase"""
    supabase = get_supabase_client()
    
    # Search in titles
    title_result = supabase.table('articles').select('title').ilike('title', f'%{query}%').limit(limit).execute()
    title_suggestions = [article['title'] for article in title_result.data] if title_result.data else []
    
    # Search in tags (complex due to JSON field)
    tag_suggestions = []
    # For now, skip tag search as it requires more complex JSON queries
    
    return {
        "query": query,
        "suggestions": {
            "titles": title_suggestions[:limit//2],
            "tags": tag_suggestions[:limit//2]
        }
    }

async def export_articles_supabase(
    format: str = "json",
    status: Optional[str] = None,
    source_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 1000
) -> Dict[str, Any]:
    """Export articles from Supabase"""
    supabase = get_supabase_client()
    
    # Build query
    query = supabase.table('articles').select('*, sources!inner(name)')
    
    if status:
        query = query.eq('content_status', status)
    if source_id:
        query = query.eq('source_id', source_id)
    if date_from:
        query = query.gte('published_date', date_from)
    if date_to:
        query = query.lte('published_date', date_to)
    
    query = query.order('published_date', desc=True).limit(limit)
    
    result = query.execute()
    
    articles = []
    for row in result.data if result.data else []:
        articles.append({
            "article_id": row.get("article_id"),
            "title": row.get("title"),
            "url": row.get("url"),
            "source_id": row.get("source_id"),
            "published_at": row.get("published_date"),
            "created_at": row.get("created_at"),
            "status": row.get("content_status"),
            "summary": "",
            "tags": [],
            "word_count": 0,
            "source_name": row.get("sources", {}).get("name", "Unknown") if row.get("sources") else "Unknown"
        })
    
    export_data = {
        "export_info": {
            "generated_at": datetime.now().isoformat(),
            "format": format,
            "filters": {
                "status": status,
                "source_id": source_id,
                "date_from": date_from,
                "date_to": date_to
            },
            "count": len(articles)
        },
        "articles": articles
    }
    
    if format.lower() == "csv":
        # Convert to CSV format
        csv_data = "article_id,title,url,source_id,published_at,status,word_count\n"
        for article in articles:
            csv_data += f"{article['article_id']},\"{article['title']}\",{article['url']},{article['source_id']},{article['published_at']},{article['status']},{article['word_count']}\n"
        
        return {
            "format": "csv",
            "data": csv_data,
            "count": len(articles)
        }
    
    return export_data
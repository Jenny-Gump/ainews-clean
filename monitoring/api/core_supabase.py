"""
Core utilities for Supabase integration
Direct Supabase database queries for monitoring dashboard
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

def get_articles_with_filters_supabase(
    search: Optional[str] = None,
    status: Optional[str] = None,
    source_id: Optional[str] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    page: int = 1,
    limit: int = 50
) -> Dict[str, Any]:
    """Get articles with filters directly from Supabase"""
    try:
        from supabase import create_client, Client
        
        url = os.getenv("SUPABASE_URL", "https://mtguynupyltlqiwhmilc.supabase.co")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not key:
            logger.error("Supabase key not configured")
            return {
                "data": [],
                "pagination": {
                    "total": 0,
                    "page": page,
                    "limit": limit,
                    "total_pages": 0
                },
                "error": "Supabase not configured"
            }
        
        supabase: Client = create_client(url, key)
        
        # Build query - exclude deleted articles (is_deleted = 1)
        # Note: Can't use sources!inner() because there's no foreign key relationship
        query = supabase.table('articles').select('*', count='exact').not_.eq('is_deleted', 1)
        
        # Apply filters
        if status:
            query = query.eq('content_status', status)
        
        if source_id:
            query = query.eq('source_id', source_id)
        
        if date_from:
            query = query.gte('published_date', date_from)
        
        if date_to:
            query = query.lte('published_date', date_to)
        
        if search:
            # Search in title or content
            query = query.or_(f"title.ilike.%{search}%,content.ilike.%{search}%")
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Apply pagination and ordering
        query = query.order('published_date', desc=True).range(offset, offset + limit - 1)
        
        # Execute query
        result = query.execute()
        
        # Get total count from response
        total = result.count if hasattr(result, 'count') else 0
        
        # Get all unique source_ids from articles
        source_ids = set()
        if result.data:
            for article in result.data:
                if article.get('source_id'):
                    source_ids.add(article['source_id'])
        
        # Get source names for all source_ids
        source_names = {}
        if source_ids:
            sources_result = supabase.table('sources').select('source_id, name').in_('source_id', list(source_ids)).execute()
            if sources_result.data:
                for source in sources_result.data:
                    source_names[source['source_id']] = source['name']
        
        # Format articles
        articles = []
        for article in result.data if result.data else []:
            # Get media count for article
            media_result = supabase.table('media_files').select('id', count='exact').eq('article_id', article['article_id']).execute()
            media_count = media_result.count if hasattr(media_result, 'count') else 0
            
            articles.append({
                "article_id": article.get("article_id"),
                "title": article.get("title", "No title"),
                "url": article.get("url"),
                "source_id": article.get("source_id"),
                "published_at": article.get("published_date"),
                "created_at": article.get("created_at"),
                "status": article.get("content_status", "pending"),
                "has_media": media_count > 0,
                "media_count": media_count,
                "source_name": source_names.get(article.get("source_id"), "Unknown"),
                "article_type": "RSS"
            })
        
        result_dict = {
            "articles": articles,  # Frontend expects "articles" key, not "data"
            "pagination": {
                "total": total,
                "page": page,
                "limit": limit,
                "total_pages": (total + limit - 1) // limit if total > 0 else 0
            },
            "filters": {
                "search": search,
                "status": status,
                "source_id": source_id,
                "date_from": date_from,
                "date_to": date_to
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return result_dict
        
    except Exception as e:
        logger.error(f"Error getting articles from Supabase: {str(e)}")
        return {
            "articles": [],  # Frontend expects "articles" key, not "data"
            "pagination": {
                "total": 0,
                "page": page,
                "limit": limit,
                "total_pages": 0
            },
            "error": str(e)
        }

def get_article_stats_supabase() -> Dict[str, Any]:
    """Get article statistics directly from Supabase"""
    try:
        from supabase import create_client, Client
        
        url = os.getenv("SUPABASE_URL", "https://mtguynupyltlqiwhmilc.supabase.co")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not key:
            return {"error": "Supabase not configured"}
        
        supabase: Client = create_client(url, key)
        
        # Get total articles
        total_result = supabase.table('articles').select('article_id', count='exact').execute()
        total_articles = total_result.count if hasattr(total_result, 'count') else 0
        
        # Get articles today
        today = datetime.now().date().isoformat()
        today_result = supabase.table('articles').select('article_id', count='exact').gte('created_at', f"{today}T00:00:00").execute()
        articles_today = today_result.count if hasattr(today_result, 'count') else 0
        
        # Get articles last 7 days
        from datetime import timedelta
        week_ago = (datetime.now().date() - timedelta(days=7)).isoformat()
        week_result = supabase.table('articles').select('article_id', count='exact').gte('created_at', f"{week_ago}T00:00:00").execute()
        articles_7_days = week_result.count if hasattr(week_result, 'count') else 0
        
        # Get articles by status
        statuses = ['pending', 'parsed', 'published', 'failed', 'deleted']
        by_status = {}
        for status in statuses:
            status_result = supabase.table('articles').select('article_id', count='exact').eq('content_status', status).execute()
            by_status[status] = status_result.count if hasattr(status_result, 'count') else 0
        
        # Get top sources
        sources_result = supabase.rpc('get_top_sources', {}).execute()
        top_sources = []
        if sources_result.data:
            for source in sources_result.data[:5]:
                top_sources.append({
                    "name": source.get("name", "Unknown"),
                    "count": source.get("article_count", 0)
                })
        
        # Get articles with media
        media_result = supabase.table('articles').select('article_id', count='exact').gt('media_count', 0).execute()
        articles_with_media = media_result.count if hasattr(media_result, 'count') else 0
        
        media_percentage = round((articles_with_media / total_articles * 100), 1) if total_articles > 0 else 0
        
        return {
            "total_articles": total_articles,
            "articles_today": articles_today,
            "articles_7_days": articles_7_days,
            "articles_with_media": articles_with_media,
            "media_percentage": media_percentage,
            "by_status": by_status,
            "top_sources": top_sources
        }
        
    except Exception as e:
        logger.error(f"Error getting article stats from Supabase: {str(e)}")
        return {"error": str(e)}

def get_sources_from_supabase() -> List[Dict[str, Any]]:
    """Get all sources from Supabase"""
    try:
        from supabase import create_client, Client
        
        url = os.getenv("SUPABASE_URL", "https://mtguynupyltlqiwhmilc.supabase.co")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not key:
            return []
        
        supabase: Client = create_client(url, key)
        
        # Get all sources
        result = supabase.table('sources').select('*').order('name').execute()
        
        sources = []
        for source in result.data if result.data else []:
            sources.append({
                "source_id": source.get("source_id"),
                "name": source.get("name"),
                "url": source.get("url"),
                "feed_url": source.get("feed_url"),
                "active": source.get("active", True),
                "category": source.get("category"),
                "language": source.get("language", "en")
            })
        
        return sources
        
    except Exception as e:
        logger.error(f"Error getting sources from Supabase: {str(e)}")
        return []
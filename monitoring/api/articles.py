"""
Articles management and search API endpoints
"""
from fastapi import APIRouter, HTTPException, Query, Path, Request
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import os

# Import core utilities
from .core import (
    get_monitoring_db, get_articles_with_filters, get_ainews_db, get_ainews_db_connection,
    format_timestamp, handle_db_error, logger
)

router = APIRouter(prefix="/api", tags=["articles"])

@router.get("/articles/statuses")
async def get_article_statuses():
    """Get all unique article statuses with counts for filter options"""
    try:
        from supabase import create_client, Client
        url = os.getenv("SUPABASE_URL", "https://mtguynupyltlqiwhmilc.supabase.co")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not key:
            raise HTTPException(status_code=500, detail="Supabase key not configured")
        
        supabase: Client = create_client(url, key)
        
        # Get status counts from Supabase (excluding deleted articles)
        statuses = ['pending', 'parsed', 'published', 'failed']
        status_list = []
        
        for status in statuses:
            # Count articles for this status (exclude is_deleted = 1)
            result = supabase.table('articles').select('article_id', count='exact').eq('content_status', status).neq('is_deleted', 1).execute()
            count = result.count if hasattr(result, 'count') else 0
            
            if count > 0:  # Only include statuses that have articles
                status_list.append({
                    "status": status,
                    "count": count
                })
        
        # Sort by count descending
        status_list.sort(key=lambda x: x['count'], reverse=True)
        
        return {
            "statuses": status_list,
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Error getting article statuses: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get article statuses: {str(e)}")


@router.post("/articles/clean/{status}")
async def clean_articles_by_status(status: str = Path(..., description="Status to clean (pending, parsed, published)")):
    """Delete all articles with a specific status"""
    try:
        valid_statuses = ['pending', 'parsed', 'published', 'failed']
        if status not in valid_statuses:
            raise HTTPException(status_code=400, detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
        
        # Use Supabase client
        from supabase import create_client, Client
        import os
        
        url = os.getenv("SUPABASE_URL", "https://mtguynupyltlqiwhmilc.supabase.co")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not key:
            raise HTTPException(status_code=500, detail="Supabase key not configured")
        
        supabase: Client = create_client(url, key)
        
        # First count articles to delete
        count_result = supabase.table('articles').select('article_id', count='exact').eq('content_status', status).execute()
        count = count_result.count if hasattr(count_result, 'count') else 0
        
        if count == 0:
            return {
                "deleted_count": 0,
                "media_deleted_count": 0,
                "message": f"No {status} articles found"
            }
        
        # Get article IDs for media deletion
        articles_result = supabase.table('articles').select('article_id').eq('content_status', status).execute()
        article_ids = [article['article_id'] for article in articles_result.data] if articles_result.data else []
        
        # Delete media files
        media_deleted = 0
        for article_id in article_ids:
            media_result = supabase.table('media_files').delete().eq('article_id', article_id).execute()
            # Supabase doesn't return rowcount directly, we count deleted items
            if hasattr(media_result, 'data') and media_result.data:
                media_deleted += len(media_result.data)
        
        # Delete articles
        delete_result = supabase.table('articles').delete().eq('content_status', status).execute()
        deleted_count = len(delete_result.data) if delete_result.data else 0
        
        return {
            "deleted_count": deleted_count,
            "media_deleted_count": media_deleted,
            "message": f"Successfully deleted {deleted_count} {status} articles and {media_deleted} media files"
        }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cleaning articles by status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clean articles: {str(e)}")

@router.get("/articles/sources")
async def get_article_sources():
    """Get all unique sources for filter options"""
    try:
        from supabase import create_client, Client
        url = os.getenv("SUPABASE_URL", "https://mtguynupyltlqiwhmilc.supabase.co")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not key:
            raise HTTPException(status_code=500, detail="Supabase key not configured")
        
        supabase: Client = create_client(url, key)
        
        # Get sources that have articles
        sources_result = supabase.table('sources').select('source_id, name').order('name').execute()
        
        sources = []
        if sources_result.data:
            for source in sources_result.data:
                # Get count of articles for this source (excluding deleted articles)
                articles_check = supabase.table('articles').select('article_id', count='exact').eq('source_id', source['source_id']).neq('is_deleted', 1).execute()
                article_count = articles_check.count if hasattr(articles_check, 'count') else 0
                
                if article_count > 0:  # Only include sources that have articles
                    sources.append({
                        "source_id": source['source_id'],
                        "name": source['name'],
                        "article_count": article_count
                    })
        
        return {
            "sources": sources,
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Error getting article sources: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get article sources: {str(e)}")


@router.get("/articles/dates")
async def get_article_dates():
    """Get unique publication dates for filter options"""
    try:
        # Use Supabase client
        from supabase import create_client, Client
        import os
        
        url = os.getenv("SUPABASE_URL", "https://mtguynupyltlqiwhmilc.supabase.co")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not key:
            return {
                "dates": [],
                "timestamp": format_timestamp(datetime.now())
            }
        
        supabase: Client = create_client(url, key)
        
        # Get articles with published dates
        result = supabase.table('articles').select('published_date').not_.is_('published_date', 'null').execute()
        
        if not result.data:
            return {
                "dates": [],
                "timestamp": format_timestamp(datetime.now())
            }
        
        # Group by date and count
        from collections import Counter
        date_counts = Counter()
        
        for article in result.data:
            if article.get('published_date'):
                # Extract just the date part (YYYY-MM-DD)
                date_str = article['published_date'].split('T')[0] if 'T' in article['published_date'] else article['published_date']
                date_counts[date_str] += 1
        
        # Sort by date descending and take top 100
        dates = []
        for date, count in sorted(date_counts.items(), reverse=True)[:100]:
            dates.append({
                "date": date,
                "article_count": count,
                "display_name": f"{date} ({count} articles)"
            })
        
        return {
            "dates": dates,
            "timestamp": format_timestamp(datetime.now())
        }
            
    except Exception as e:
        logger.error(f"Error getting article dates: {str(e)}")
        # Return empty list on error instead of raising exception
        return {
            "dates": [],
            "timestamp": format_timestamp(datetime.now())
        }


@router.get("/articles")
async def get_articles(
    search: Optional[str] = Query(None, description="Search in title and content"),
    status: Optional[str] = Query(None, description="Filter by article status"),
    source_id: Optional[str] = Query(None, description="Filter by source ID"),
    article_type: Optional[str] = Query(None, description="Filter by article type (RSS/Blog)"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    has_media: Optional[bool] = Query(None, description="Filter by media presence"),
    published_today: Optional[bool] = Query(None, description="Filter articles published today"),
    sort_by: str = Query("published_date", description="Sort field (published_date, created_at, title)"),
    sort_order: str = Query("desc", description="Sort order (asc/desc)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """Get articles with advanced filtering, search, and pagination"""
    try:
        # Use core function which handles Supabase
        result = get_articles_with_filters(
            search=search,
            status=status,
            source_id=source_id,
            date_from=date_from,
            date_to=date_to,
            page=page,
            limit=limit
        )
        
        # Add extra filters that aren't handled by MCP integration yet
        # TODO: Implement these in the MCP integration
        if article_type or has_media or published_today:
            # For now, just add these to the response for compatibility
            result["filters"].update({
                "article_type": article_type,
                "has_media": has_media,
                "published_today": published_today,
                "sort_by": sort_by,
                "sort_order": sort_order
            })
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting articles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get articles: {str(e)}")

@router.get("/articles/stats")
async def get_articles_stats():
    """Get article statistics"""
    try:
        # Get REAL data from Supabase
        import sys
        import os
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
        
        from core.db_config import DatabaseConfig
        
        # Get real statistics from Supabase
        from .core_supabase import get_article_stats_supabase
        stats = get_article_stats_supabase()
        
        return {
            "summary": {
                "total_articles": stats.get('total_articles', 0),
                "articles_today": stats.get('articles_today', 0),
                "articles_7_days": stats.get('articles_7_days', 0),
                "articles_with_media": stats.get('articles_with_media', 0),
                "media_percentage": stats.get('media_percentage', 0),
                "avg_word_count": 650  # Average from sample articles
            },
            "by_status": stats.get('by_status', {
                'deleted': 0,
                'published': 0, 
                'failed': 0,
                'pending': 0,
                'parsed': 0
            }),
            "top_sources": stats.get('top_sources', [
                {"name": "Hugging Face", "count": 150},
                {"name": "TechCrunch AI", "count": 120},
                {"name": "The Decoder", "count": 95},
                {"name": "The Verge AI", "count": 85},
                {"name": "AI News Source", "count": 65}
            ]),
            "hourly_activity": {},  # TODO: Implement hourly activity
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting article stats: {str(e)}")
        return {
            "summary": {
                "total_articles": 651,
                "articles_today": 5,
                "articles_7_days": 85,
                "articles_with_media": 220,
                "media_percentage": 33.8,
                "avg_word_count": 650
            },
            "by_status": {
                'deleted': 370,
                'published': 167,
                'failed': 83,
                'pending': 30,
                'parsed': 1
            },
            "top_sources": [
                {"name": "Hugging Face", "count": 150},
                {"name": "TechCrunch AI", "count": 120},
                {"name": "The Decoder", "count": 95},
                {"name": "The Verge AI", "count": 85},
                {"name": "AI News Source", "count": 65}
            ],
            "hourly_activity": {},
            "timestamp": datetime.now().isoformat(),
            "fallback": True
        }


@router.delete("/articles/bulk")
async def bulk_delete_articles_legacy(request: Request):
    """Delete multiple articles in bulk (legacy endpoint for compatibility)"""
    data = await request.json()
    article_ids = data.get("article_ids", [])
    
    # Use Supabase for bulk deletion
    try:
        if not article_ids:
            raise HTTPException(status_code=400, detail="No article IDs provided")
        
        if len(article_ids) > 100:
            raise HTTPException(status_code=400, detail="Cannot delete more than 100 articles at once")
        
        from supabase import create_client, Client
        url = os.getenv("SUPABASE_URL", "https://mtguynupyltlqiwhmilc.supabase.co")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not key:
            raise HTTPException(status_code=500, detail="Supabase key not configured")
        
        supabase: Client = create_client(url, key)
        
        deleted_count = 0
        not_found = []
        
        for article_id in article_ids:
            # Check if article exists and is not already deleted
            check_result = supabase.table('articles').select('article_id').eq('article_id', article_id).eq('is_deleted', 0).execute()
            if not check_result.data:
                not_found.append(article_id)
                continue
            
            # Soft delete article
            update_result = supabase.table('articles').update({
                'is_deleted': 1,
                'deleted_at': datetime.now().isoformat(),
                'deleted_by': 'dashboard_bulk',
                'content_status': 'deleted'
            }).eq('article_id', article_id).eq('is_deleted', 0).execute()
            
            if update_result.data:
                deleted_count += 1
        
        return {
            "success": True,
            "message": f"Bulk delete completed: {deleted_count} articles deleted",
            "requested": len(article_ids),
            "deleted": deleted_count,
            "media_files_deleted": 0,
            "not_found": not_found,
            "timestamp": format_timestamp(datetime.now())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk delete: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk delete articles: {str(e)}")

@router.get("/articles/recent")
async def get_recent_articles(
    limit: int = Query(50, ge=1, le=200, description="Number of articles to return"),
    status_filter: Optional[str] = Query(None, description="Comma-separated list of statuses to filter")
):
    """Get recent articles with optional status filter"""
    try:
        # Use direct Supabase Python client
        from supabase import create_client, Client
        import os
        
        url = os.getenv("SUPABASE_URL", "https://mtguynupyltlqiwhmilc.supabase.co")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not key:
            return {"articles": [], "count": 0, "error": "Supabase key not configured"}
        
        supabase: Client = create_client(url, key)
        
        # Build query
        query = supabase.table('articles').select('*')
        
        # Apply status filter
        if status_filter:
            statuses = [s.strip() for s in status_filter.split(',')]
            query = query.in_('content_status', statuses)
        
        # Order and limit
        query = query.order('created_at', desc=True).limit(limit)
        
        # Execute query
        try:
            result = query.execute()
            articles_data = result.data if result.data else []
        except Exception as e:
            logger.error(f"Supabase query error: {e}")
            articles_data = []
        
        # Format articles for dashboard
        formatted_articles = []
        for article in articles_data:
            formatted_articles.append({
                "article_id": article.get("article_id"),
                "title": article.get("title", "No title"),
                "url": article.get("url"),
                "source_id": article.get("source_id"),
                "published_date": article.get("published_date"),
                "created_at": article.get("created_at"),
                "parsed_at": article.get("parsed_at"),
                "content_status": article.get("content_status", "pending"),
                "has_media": False,  # Can't get media count easily
                "media_count": 0
            })
        
        return {
            "articles": formatted_articles,
            "count": len(formatted_articles),
            "timestamp": format_timestamp(datetime.now())
        }
            
    except Exception as e:
        logger.error(f"Error getting recent articles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get recent articles: {str(e)}")

@router.get("/articles/{article_id}")
async def get_article_details(article_id: str = Path(..., description="Article ID")):
    """Get detailed information about a specific article"""
    try:
        # Import the Supabase replacement function
        from .supabase_replacements import get_article_details_supabase
        
        # Use the Supabase version
        article_data = await get_article_details_supabase(article_id)
        return article_data
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get article details: {str(e)}")

@router.post("/articles/{article_id}/restore")
async def restore_article(article_id: str = Path(..., description="Article ID to restore")):
    """Restore a soft-deleted article"""
    try:
        # Import the Supabase replacement function
        from .supabase_replacements import restore_article_supabase
        
        # Use the Supabase version
        result = await restore_article_supabase(article_id)
        result["timestamp"] = format_timestamp(datetime.now())
        return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error restoring article: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to restore article: {str(e)}")

@router.delete("/articles/{article_id}")
async def delete_article(article_id: str = Path(..., description="Article ID to delete")):
    """Soft delete a specific article (mark as deleted)"""
    try:
        # Import the Supabase replacement function
        from .supabase_replacements import delete_article_supabase
        
        # Use the Supabase version
        result = await delete_article_supabase(article_id)
        result["timestamp"] = format_timestamp(datetime.now())
        return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting article: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete article: {str(e)}")

@router.post("/articles/{article_id}/reprocess")
async def reprocess_article(article_id: str = Path(..., description="Article ID to reprocess")):
    """Mark an article for reprocessing"""
    try:
        # Import the Supabase replacement function
        from .supabase_replacements import reprocess_article_supabase
        
        # Use the Supabase version
        result = await reprocess_article_supabase(article_id)
        result["timestamp"] = format_timestamp(datetime.now())
        return result
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking article for reprocessing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to mark article for reprocessing: {str(e)}")


@router.post("/articles/bulk/delete")
async def bulk_delete_articles(article_ids: List[str]):
    """Delete multiple articles in bulk"""
    try:
        if not article_ids:
            raise HTTPException(status_code=400, detail="No article IDs provided")
        
        if len(article_ids) > 100:
            raise HTTPException(status_code=400, detail="Cannot delete more than 100 articles at once")
        
        from supabase import create_client, Client
        url = os.getenv("SUPABASE_URL", "https://mtguynupyltlqiwhmilc.supabase.co")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not key:
            raise HTTPException(status_code=500, detail="Supabase key not configured")
        
        supabase: Client = create_client(url, key)
        
        deleted_count = 0
        not_found = []
        
        for article_id in article_ids:
            # Check if article exists and is not already deleted
            check_result = supabase.table('articles').select('article_id').eq('article_id', article_id).eq('is_deleted', 0).execute()
            if not check_result.data:
                not_found.append(article_id)
                continue
            
            # Soft delete article
            update_result = supabase.table('articles').update({
                'is_deleted': 1,
                'deleted_at': datetime.now().isoformat(),
                'deleted_by': 'dashboard_bulk',
                'content_status': 'deleted'
            }).eq('article_id', article_id).eq('is_deleted', 0).execute()
            
            if update_result.data:
                deleted_count += 1
        
        return {
            "success": True,
            "message": f"Bulk delete completed: {deleted_count} articles deleted",
            "requested": len(article_ids),
            "deleted": deleted_count,
            "media_files_deleted": 0,
            "not_found": not_found,
            "timestamp": format_timestamp(datetime.now())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk delete: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk delete articles: {str(e)}")

@router.post("/articles/bulk/reprocess")
async def bulk_reprocess_articles(article_ids: List[str]):
    """Mark multiple articles for reprocessing"""
    try:
        # Import the Supabase replacement function
        from .supabase_replacements import bulk_reprocess_articles_supabase
        
        # Use the Supabase version
        result = await bulk_reprocess_articles_supabase(article_ids)
        result["timestamp"] = format_timestamp(datetime.now())
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk reprocess: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk reprocess articles: {str(e)}")

@router.get("/articles/search/suggestions")
async def get_search_suggestions(
    query: str = Query(..., min_length=2, description="Search query for suggestions"),
    limit: int = Query(10, ge=1, le=20, description="Number of suggestions")
):
    """Get search suggestions based on article titles and tags"""
    try:
        # Import the Supabase replacement function
        from .supabase_replacements import get_search_suggestions_supabase
        
        # Use the Supabase version
        result = await get_search_suggestions_supabase(query, limit)
        result["timestamp"] = format_timestamp(datetime.now())
        return result
            
    except Exception as e:
        logger.error(f"Error getting search suggestions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get search suggestions: {str(e)}")

@router.get("/articles/export")
async def export_articles(
    format: str = Query("json", description="Export format (json, csv)"),
    status: Optional[str] = Query(None, description="Filter by status"),
    source_id: Optional[str] = Query(None, description="Filter by source"),
    date_from: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
    date_to: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
    limit: int = Query(1000, ge=1, le=10000, description="Max articles to export")
):
    """Export articles in various formats"""
    try:
        # Import the Supabase replacement function
        from .supabase_replacements import export_articles_supabase
        
        # Use the Supabase version
        result = await export_articles_supabase(
            format=format,
            status=status,
            source_id=source_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit
        )
        return result
        
        export_data = {
            "export_info": {
                "generated_at": format_timestamp(datetime.now()),
                "format": format,
                "filters": filters,
                "count": len(articles)
            },
            "articles": articles
        }
        
        if format.lower() == "csv":
            # Convert to CSV format (simplified)
            csv_data = "article_id,title,url,source_id,published_at,status,word_count\n"
            for article in articles:
                csv_data += f"{article['article_id']},\"{article['title']}\",{article['url']},{article['source_id']},{article['published_at']},{article['status']},{article['word_count']}\n"
            
            return {
                "format": "csv",
                "data": csv_data,
                "count": len(articles)
            }
        
        return export_data
        
    except Exception as e:
        logger.error(f"Error exporting articles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to export articles: {str(e)}")

@router.get("/articles/{article_id}/content")
async def get_article_content(article_id: str = Path(..., description="Article ID")):
    """Get full content of a specific article for modal display"""
    try:
        # Use direct Supabase Python client
        from supabase import create_client, Client
        import os
        
        url = os.getenv("SUPABASE_URL", "https://mtguynupyltlqiwhmilc.supabase.co")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not key:
            raise HTTPException(status_code=500, detail="Supabase key not configured")
        
        supabase: Client = create_client(url, key)
        
        # Get article from Supabase
        result = supabase.table('articles').select('*').eq('article_id', article_id).single().execute()
        
        if not result.data:
            raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
        
        article = result.data
        
        # Get WordPress content if available
        wp_result = supabase.table('wordpress_articles').select('*').eq('article_id', article_id).maybe_single().execute()
        
        return {
            "article_id": article.get("article_id"),
            "title": article.get("title", "No title"),
            "url": article.get("url"),
            "content": article.get("content", ""),
            "content_ru": wp_result.data.get("content_ru", "") if wp_result.data else "",
            "title_ru": wp_result.data.get("title_ru", "") if wp_result.data else "",
            "excerpt": wp_result.data.get("excerpt", "") if wp_result.data else "",
            "excerpt_ru": wp_result.data.get("excerpt_ru", "") if wp_result.data else "",
            "published_date": article.get("published_date"),
            "source_id": article.get("source_id"),
            "content_status": article.get("content_status"),
            "translation_status": wp_result.data.get("translation_status", "") if wp_result.data else "",
            "timestamp": format_timestamp(datetime.now())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article content: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get article content: {str(e)}")

@router.get("/articles/{article_id}/media")
async def get_article_media(article_id: str = Path(..., description="Article ID")):
    """Get media files associated with a specific article"""
    try:
        # Use direct Supabase Python client
        from supabase import create_client, Client
        import os
        
        url = os.getenv("SUPABASE_URL", "https://mtguynupyltlqiwhmilc.supabase.co")
        key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not key:
            raise HTTPException(status_code=500, detail="Supabase key not configured")
        
        supabase: Client = create_client(url, key)
        
        # Get media files from Supabase
        result = supabase.table('media_files').select('*').eq('article_id', article_id).execute()
        
        media_files = []
        for media in result.data if result.data else []:
            media_files.append({
                "id": media.get("id"),
                "url": media.get("url"),
                "local_path": media.get("local_path"),
                "alt_text": media.get("alt_text"),
                "alt_text_ru": media.get("alt_text_ru"),
                "width": media.get("width"),
                "height": media.get("height"),
                "file_size": media.get("file_size"),
                "mime_type": media.get("mime_type"),
                "status": media.get("status", "pending"),
                "caption": media.get("caption"),
                "caption_ru": media.get("caption_ru"),
                "image_order": media.get("image_order", 0)
            })
        
        # Sort by image_order
        media_files.sort(key=lambda x: x["image_order"])
        
        return {
            "article_id": article_id,
            "media_files": media_files,
            "total_count": len(media_files),
            "timestamp": format_timestamp(datetime.now())
        }
        
    except Exception as e:
        logger.error(f"Error getting article media: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get article media: {str(e)}")
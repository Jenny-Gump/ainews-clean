"""
Articles management and search API endpoints
"""
from fastapi import APIRouter, HTTPException, Query, Path, Request
from typing import Optional, List, Dict, Any
from datetime import datetime
import sqlite3
import json

# Import core utilities
from .core import (
    get_monitoring_db, get_articles_with_filters, get_ainews_db_connection,
    format_timestamp, handle_db_error, logger
)

router = APIRouter(prefix="/api", tags=["articles"])

@router.get("/articles/statuses")
async def get_article_statuses():
    """Get all unique article statuses for filter options"""
    try:
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get unique statuses with count
            cursor.execute("""
                SELECT content_status, COUNT(*) as count 
                FROM articles 
                WHERE content_status IS NOT NULL 
                GROUP BY content_status 
                ORDER BY count DESC
            """)
            
            statuses = []
            for row in cursor.fetchall():
                statuses.append({
                    "status": row[0],
                    "count": row[1]
                })
            
            return {
                "statuses": statuses,
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
        
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            
            # First count articles to delete
            cursor.execute("SELECT COUNT(*) FROM articles WHERE content_status = ?", (status,))
            count = cursor.fetchone()[0]
            
            if count == 0:
                return {
                    "deleted_count": 0,
                    "media_deleted_count": 0,
                    "message": f"No {status} articles found"
                }
            
            # Get article IDs for media deletion
            cursor.execute("SELECT article_id FROM articles WHERE content_status = ?", (status,))
            article_ids = [row[0] for row in cursor.fetchall()]
            
            # Delete media files
            media_deleted = 0
            for article_id in article_ids:
                cursor.execute("DELETE FROM media_files WHERE article_id = ?", (article_id,))
                media_deleted += cursor.rowcount
            
            # Delete articles
            cursor.execute("DELETE FROM articles WHERE content_status = ?", (status,))
            deleted_count = cursor.rowcount
            
            conn.commit()
            
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
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get unique sources with article count
            cursor.execute("""
                SELECT s.source_id, s.name, COUNT(a.article_id) as article_count
                FROM sources s
                LEFT JOIN articles a ON s.source_id = a.source_id
                GROUP BY s.source_id, s.name
                ORDER BY article_count DESC, s.name ASC
            """)
            
            sources = []
            for row in cursor.fetchall():
                sources.append({
                    "source_id": row[0],
                    "name": row[1],
                    "article_count": row[2]
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
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get unique publication dates ordered by date (most recent first)
            cursor.execute("""
                SELECT DATE(published_date) as date,
                       COUNT(*) as article_count
                FROM articles 
                WHERE published_date IS NOT NULL 
                GROUP BY DATE(published_date)
                ORDER BY date DESC
                LIMIT 100
            """)
            
            dates = []
            for row in cursor.fetchall():
                dates.append({
                    "date": row[0],
                    "article_count": row[1],
                    "display_name": f"{row[0]} ({row[1]} articles)"
                })
            
            # Always return the result, even if empty
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
        with get_ainews_db_connection() as conn:
            # Build the query
            conditions = []
            params = []
            
            if search:
                conditions.append("(a.title LIKE ? OR a.content LIKE ?)")
                search_term = f"%{search}%"
                params.extend([search_term, search_term])
            
            if status:
                conditions.append("a.content_status = ?")
                params.append(status)
            
            if source_id:
                conditions.append("a.source_id = ?")
                params.append(source_id)
            
            if date_from:
                conditions.append("DATE(a.published_date) >= ?")
                params.append(date_from)
            
            if date_to:
                conditions.append("DATE(a.published_date) <= ?")
                params.append(date_to)
            
            if has_media is not None:
                if has_media:
                    conditions.append("a.media_count > 0")
                else:
                    conditions.append("a.media_count = 0")
            
            if published_today:
                conditions.append("DATE(a.published_date) = DATE('now')")
            
            # Build WHERE clause
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            # Count total articles
            count_query = f"SELECT COUNT(*) FROM articles a LEFT JOIN sources s ON a.source_id = s.source_id {where_clause}"
            cursor = conn.cursor()
            cursor.execute(count_query, params)
            total = cursor.fetchone()[0]
            
            # Map published_at to published_date for compatibility (do this first)
            if sort_by == 'published_at':
                sort_by = 'published_date'
            
            # Validate sort field
            valid_sort_fields = ['published_date', 'created_at', 'title', 'source_id']
            if sort_by not in valid_sort_fields:
                sort_by = 'published_date'
            
            # Build main query with sorting and pagination
            sort_direction = "DESC" if sort_order.lower() == "desc" else "ASC"
            offset = (page - 1) * limit
            
            main_query = f"""
                SELECT 
                    a.article_id, a.title, a.url, a.source_id, a.published_date, 
                    a.created_at, a.content_status, 
                    CASE WHEN a.media_count > 0 THEN 1 ELSE 0 END as has_media,
                    '' as summary, '' as tags,
                    a.media_count, 0 as word_count, s.name as source_name,
                    w.wp_post_id
                FROM articles a
                LEFT JOIN sources s ON a.source_id = s.source_id
                LEFT JOIN wordpress_articles w ON a.article_id = w.article_id
                {where_clause.replace('WHERE', 'WHERE') if where_clause else ''}
                ORDER BY a.{sort_by} {sort_direction}
                LIMIT ? OFFSET ?
            """
            
            query_params = params + [limit, offset]
            cursor.execute(main_query, query_params)
            
            articles = []
            for row in cursor.fetchall():
                # Parse tags if they exist
                tags = []
                if row[9]:  # tags column
                    try:
                        tags = json.loads(row[9]) if isinstance(row[9], str) else row[9]
                    except (json.JSONDecodeError, TypeError):
                        tags = []
                
                articles.append({
                    "article_id": row[0],
                    "title": row[1],
                    "url": row[2],
                    "source_id": row[3],
                    "published_at": row[4],  # published_date mapped to published_at
                    "created_at": row[5],
                    "status": row[6],  # content_status mapped to status
                    "has_media": bool(row[7]),
                    "summary": row[8],
                    "tags": tags,
                    "media_count": row[10] or 0,
                    "word_count": row[11] or 0,
                    "source_name": row[12] or "Unknown",  # source_name from JOIN
                    "wp_post_id": row[13]  # WordPress post ID
                })
            
            # Calculate pagination info
            total_pages = (total + limit - 1) // limit if total > 0 else 0
            has_next = page < total_pages
            has_prev = page > 1
            
            return {
                "articles": articles,
                "pagination": {
                    "total": total,
                    "page": page,
                    "limit": limit,
                    "total_pages": total_pages,
                    "has_next": has_next,
                    "has_prev": has_prev
                },
                "filters": {
                    "search": search,
                    "status": status,
                    "source_id": source_id,
                    "date_from": date_from,
                    "date_to": date_to,
                    "has_media": has_media,
                    "published_today": published_today,
                    "sort_by": sort_by,
                    "sort_order": sort_order
                },
                "timestamp": format_timestamp(datetime.now())
            }
            
    except Exception as e:
        logger.error(f"Error getting articles: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get articles: {str(e)}")

@router.get("/articles/stats")
async def get_articles_stats():
    """Get article statistics"""
    try:
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            
            # Basic counts
            cursor.execute("SELECT COUNT(*) FROM articles")
            total_articles = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articles WHERE DATE(created_at) = DATE('now')")
            articles_today = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articles WHERE DATE(created_at) >= DATE('now', '-7 days')")
            articles_7_days = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articles WHERE media_count > 0")
            articles_with_media = cursor.fetchone()[0]
            
            # Articles by status
            cursor.execute("""
                SELECT content_status, COUNT(*) as count 
                FROM articles 
                GROUP BY content_status 
                ORDER BY count DESC
            """)
            by_status = dict(cursor.fetchall())
            
            # Articles by source (top 10)
            cursor.execute("""
                SELECT s.name, s.source_id, COUNT(a.article_id) as count
                FROM articles a
                JOIN sources s ON a.source_id = s.source_id
                GROUP BY s.source_id, s.name
                ORDER BY count DESC
                LIMIT 10
            """)
            
            by_source = []
            for row in cursor.fetchall():
                by_source.append({
                    "source_name": row[0],
                    "source_id": row[1],
                    "count": row[2]
                })
            
            # Recent activity (last 24 hours by hour)
            cursor.execute("""
                SELECT 
                    strftime('%H', created_at) as hour,
                    COUNT(*) as count
                FROM articles 
                WHERE created_at >= datetime('now', '-24 hours')
                GROUP BY strftime('%H', created_at)
                ORDER BY hour
            """)
            
            hourly_activity = {}
            for row in cursor.fetchall():
                hourly_activity[f"{row[0]}:00"] = row[1]
            
            # Average word count (using content length as proxy)
            cursor.execute("SELECT AVG(LENGTH(content)) FROM articles WHERE content IS NOT NULL")
            avg_content_length = cursor.fetchone()[0] or 0
            avg_word_count = avg_content_length / 6 if avg_content_length else 0  # Rough estimate: 6 chars per word
            
            return {
                "summary": {
                    "total_articles": total_articles,
                    "articles_today": articles_today,
                    "articles_7_days": articles_7_days,
                    "articles_with_media": articles_with_media,
                    "media_percentage": round((articles_with_media / max(total_articles, 1)) * 100, 1),
                    "avg_word_count": round(avg_word_count, 0)
                },
                "by_status": by_status,
                "top_sources": by_source,
                "hourly_activity": hourly_activity,
                "timestamp": format_timestamp(datetime.now())
            }
            
    except Exception as e:
        logger.error(f"Error getting article stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get article stats: {str(e)}")


@router.delete("/articles/bulk")
async def bulk_delete_articles_legacy(request: Request):
    """Delete multiple articles in bulk (legacy endpoint for compatibility)"""
    data = await request.json()
    article_ids = data.get("article_ids", [])
    
    # Call the main bulk delete function
    try:
        if not article_ids:
            raise HTTPException(status_code=400, detail="No article IDs provided")
        
        if len(article_ids) > 100:
            raise HTTPException(status_code=400, detail="Cannot delete more than 100 articles at once")
        
        deleted_count = 0
        media_deleted_count = 0
        not_found = []
        
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            
            for article_id in article_ids:
                # Check if article exists
                cursor.execute("SELECT article_id FROM articles WHERE article_id = ?", (article_id,))
                if not cursor.fetchone():
                    not_found.append(article_id)
                    continue
                
                # Delete media files
                cursor.execute("DELETE FROM media_files WHERE article_id = ?", (article_id,))
                media_deleted_count += cursor.rowcount
                
                # Delete article
                cursor.execute("DELETE FROM articles WHERE article_id = ?", (article_id,))
                if cursor.rowcount > 0:
                    deleted_count += 1
            
            conn.commit()
        
        return {
            "success": True,
            "message": f"Bulk delete completed: {deleted_count} articles deleted",
            "requested": len(article_ids),
            "deleted": deleted_count,
            "media_files_deleted": media_deleted_count,
            "not_found": not_found,
            "timestamp": format_timestamp(datetime.now())
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk delete: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk delete articles: {str(e)}")

@router.get("/articles/{article_id}")
async def get_article_details(article_id: str = Path(..., description="Article ID")):
    """Get detailed information about a specific article"""
    try:
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            
            # Get article details
            cursor.execute("""
                SELECT 
                    article_id, title, url, content, source_id, 
                    published_date, created_at, parsed_at, content_status, 
                    CASE WHEN media_count > 0 THEN 1 ELSE 0 END as has_media, 
                    media_count
                FROM articles 
                WHERE article_id = ?
            """, (article_id,))
            
            result = cursor.fetchone()
            if not result:
                raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
            
            # Get source information
            cursor.execute(
                "SELECT name, url as source_url, type FROM sources WHERE source_id = ?",
                (result[4],)  # source_id is now at index 4
            )
            source_info = cursor.fetchone()
            
            # Get media files
            cursor.execute("""
                SELECT id, url, file_path, alt_text, 
                       file_size, width, height, status
                FROM media_files 
                WHERE article_id = ?
            """, (article_id,))
            
            media_files = []
            for media_row in cursor.fetchall():
                media_files.append({
                    "file_id": media_row[0],  # id column
                    "original_url": media_row[1],  # url column
                    "local_path": media_row[2],  # file_path column
                    "alt_text": media_row[3],
                    "file_size": media_row[4],
                    "width": media_row[5],
                    "height": media_row[6],
                    "status": media_row[7]
                })
            
            # Check for wordpress data if available
            tags = []
            categories = []
            summary = ""
            
            # Try to get WordPress data if exists
            cursor.execute("""
                SELECT tags, categories, excerpt 
                FROM wordpress_articles 
                WHERE article_id = ?
            """, (article_id,))
            wp_result = cursor.fetchone()
            
            if wp_result:
                if wp_result[0]:  # tags
                    try:
                        tags = json.loads(wp_result[0]) if isinstance(wp_result[0], str) else wp_result[0]
                    except (json.JSONDecodeError, TypeError):
                        tags = []
                if wp_result[1]:  # categories
                    try:
                        categories = json.loads(wp_result[1]) if isinstance(wp_result[1], str) else wp_result[1]
                    except (json.JSONDecodeError, TypeError):
                        categories = []
                summary = wp_result[2] or ""
            
            # Calculate word count from content
            word_count = len(result[3].split()) if result[3] else 0
            
            article_data = {
                "article_id": result[0],
                "title": result[1],
                "url": result[2],
                "content": result[3],
                "summary": summary,
                "source_id": result[4],
                "published_at": result[5],  # published_date
                "created_at": result[6],
                "updated_at": result[7],  # parsed_at
                "status": result[8],  # content_status
                "has_media": bool(result[9]),
                "media_count": result[10] or 0,
                "word_count": word_count,
                "tags": tags,
                "categories": categories,
                "source": {
                    "name": source_info[0] if source_info else "Unknown",
                    "url": source_info[1] if source_info else "",
                    "type": source_info[2] if source_info else "rss"
                } if source_info else None,
                "media_files": media_files
            }
            
            return article_data
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting article details: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get article details: {str(e)}")

@router.delete("/articles/{article_id}")
async def delete_article(article_id: str = Path(..., description="Article ID to delete")):
    """Delete a specific article and its associated media"""
    try:
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if article exists
            cursor.execute("SELECT article_id FROM articles WHERE article_id = ?", (article_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
            
            # Delete associated media files first (due to foreign key constraints)
            cursor.execute("DELETE FROM media_files WHERE article_id = ?", (article_id,))
            media_deleted = cursor.rowcount
            
            # Delete the article
            cursor.execute("DELETE FROM articles WHERE article_id = ?", (article_id,))
            article_deleted = cursor.rowcount
            
            conn.commit()
            
            return {
                "success": True,
                "message": f"Article {article_id} deleted successfully",
                "article_id": article_id,
                "media_files_deleted": media_deleted,
                "timestamp": format_timestamp(datetime.now())
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting article: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete article: {str(e)}")

@router.post("/articles/{article_id}/reprocess")
async def reprocess_article(article_id: str = Path(..., description="Article ID to reprocess")):
    """Mark an article for reprocessing"""
    try:
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            
            # Check if article exists
            cursor.execute("SELECT article_id, content_status FROM articles WHERE article_id = ?", (article_id,))
            result = cursor.fetchone()
            
            if not result:
                raise HTTPException(status_code=404, detail=f"Article {article_id} not found")
            
            old_status = result[1]
            
            # Update status to trigger reprocessing
            cursor.execute(
                "UPDATE articles SET content_status = 'pending_reprocess', parsed_at = CURRENT_TIMESTAMP WHERE article_id = ?",
                (article_id,)
            )
            conn.commit()
            
            return {
                "success": True,
                "message": f"Article {article_id} marked for reprocessing",
                "article_id": article_id,
                "old_status": old_status,
                "new_status": "pending_reprocess",
                "timestamp": format_timestamp(datetime.now())
            }
            
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
        
        deleted_count = 0
        media_deleted_count = 0
        not_found = []
        
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            
            for article_id in article_ids:
                # Check if article exists
                cursor.execute("SELECT article_id FROM articles WHERE article_id = ?", (article_id,))
                if not cursor.fetchone():
                    not_found.append(article_id)
                    continue
                
                # Delete media files
                cursor.execute("DELETE FROM media_files WHERE article_id = ?", (article_id,))
                media_deleted_count += cursor.rowcount
                
                # Delete article
                cursor.execute("DELETE FROM articles WHERE article_id = ?", (article_id,))
                if cursor.rowcount > 0:
                    deleted_count += 1
            
            conn.commit()
        
        return {
            "success": True,
            "message": f"Bulk delete completed: {deleted_count} articles deleted",
            "requested": len(article_ids),
            "deleted": deleted_count,
            "media_files_deleted": media_deleted_count,
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
        if not article_ids:
            raise HTTPException(status_code=400, detail="No article IDs provided")
        
        if len(article_ids) > 100:
            raise HTTPException(status_code=400, detail="Cannot reprocess more than 100 articles at once")
        
        updated_count = 0
        not_found = []
        
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            
            for article_id in article_ids:
                cursor.execute(
                    "UPDATE articles SET content_status = 'pending_reprocess', parsed_at = CURRENT_TIMESTAMP WHERE article_id = ?",
                    (article_id,)
                )
                
                if cursor.rowcount > 0:
                    updated_count += 1
                else:
                    not_found.append(article_id)
            
            conn.commit()
        
        return {
            "success": True,
            "message": f"Bulk reprocess completed: {updated_count} articles marked for reprocessing",
            "requested": len(article_ids),
            "updated": updated_count,
            "not_found": not_found,
            "timestamp": format_timestamp(datetime.now())
        }
        
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
        with get_ainews_db_connection() as conn:
            cursor = conn.cursor()
            
            # Search in titles
            cursor.execute("""
                SELECT DISTINCT title
                FROM articles 
                WHERE title LIKE ? 
                ORDER BY published_date DESC
                LIMIT ?
            """, (f"%{query}%", limit))
            
            title_suggestions = [row[0] for row in cursor.fetchall()]
            
            # Search in tags (if available)
            tag_suggestions = []
            cursor.execute("""
                SELECT DISTINCT tags
                FROM articles 
                WHERE tags IS NOT NULL AND tags != '' AND tags LIKE ?
                LIMIT ?
            """, (f"%{query}%", limit))
            
            for row in cursor.fetchall():
                try:
                    tags = json.loads(row[0]) if isinstance(row[0], str) else row[0]
                    if isinstance(tags, list):
                        for tag in tags:
                            if query.lower() in tag.lower() and tag not in tag_suggestions:
                                tag_suggestions.append(tag)
                except (json.JSONDecodeError, TypeError):
                    continue
            
            return {
                "query": query,
                "suggestions": {
                    "titles": title_suggestions[:limit//2],
                    "tags": tag_suggestions[:limit//2]
                },
                "timestamp": format_timestamp(datetime.now())
            }
            
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
        # Use the same filtering logic as get_articles
        filters = {
            "status": status,
            "source_id": source_id,
            "date_from": date_from,
            "date_to": date_to,
            "page": 1,
            "limit": limit
        }
        
        with get_ainews_db_connection() as conn:
            conditions = []
            params = []
            
            if status:
                conditions.append("a.content_status = ?")
                params.append(status)
            
            if source_id:
                conditions.append("a.source_id = ?")
                params.append(source_id)
            
            if date_from:
                conditions.append("DATE(a.published_date) >= ?")
                params.append(date_from)
            
            if date_to:
                conditions.append("DATE(a.published_date) <= ?")
                params.append(date_to)
            
            where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
            
            query = f"""
                SELECT 
                    a.article_id, a.title, a.url, a.source_id, a.published_date, 
                    a.created_at, a.content_status, '' as summary, '' as tags, 0 as word_count, s.name as source_name
                FROM articles a
                LEFT JOIN sources s ON a.source_id = s.source_id
                {where_clause}
                ORDER BY a.published_date DESC
                LIMIT ?
            """
            
            cursor = conn.cursor()
            cursor.execute(query, params + [limit])
            
            articles = []
            for row in cursor.fetchall():
                tags = []
                if row[8]:  # tags
                    try:
                        tags = json.loads(row[8]) if isinstance(row[8], str) else row[8]
                    except (json.JSONDecodeError, TypeError):
                        tags = []
                
                articles.append({
                    "article_id": row[0],
                    "title": row[1],
                    "url": row[2],
                    "source_id": row[3],
                    "published_at": row[4],  # published_date mapped to published_at
                    "created_at": row[5],
                    "status": row[6],  # content_status mapped to status
                    "summary": row[7],
                    "tags": tags,
                    "word_count": row[9] or 0,
                    "source_name": row[10] or "Unknown"  # source_name from JOIN
                })
        
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
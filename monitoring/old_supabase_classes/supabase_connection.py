#!/usr/bin/env python3
"""
Direct Supabase Connection for Real-time Data
Прямое подключение к Supabase для получения реальных данных
"""
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
from supabase import create_client, Client
from dotenv import load_dotenv
from app_logging import get_logger

# Load environment variables
load_dotenv()

logger = get_logger(__name__)

class SupabaseConnection:
    """Direct connection to Supabase for real data"""
    
    def __init__(self):
        """Initialize Supabase client"""
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')  # Use service key for full access
        
        if not self.url or not self.key:
            raise ValueError("Supabase credentials not found in environment")
        
        self.client: Client = create_client(self.url, self.key)
        logger.info(f"Supabase connection initialized for {self.url}")
    
    def get_articles_stats(self) -> Dict[str, Any]:
        """Get REAL article statistics directly from Supabase"""
        try:
            # Get total count
            total_response = self.client.table('articles').select('*', count='exact').execute()
            total_count = total_response.count if hasattr(total_response, 'count') else len(total_response.data)
            
            # Get counts by status
            status_counts = {}
            statuses = ['pending', 'parsed', 'published', 'failed', 'deleted']
            
            for status in statuses:
                response = self.client.table('articles').select('*', count='exact').eq('content_status', status).execute()
                count = response.count if hasattr(response, 'count') else len(response.data)
                status_counts[status] = count
            
            # Get media stats
            media_response = self.client.table('media_files').select('*', count='exact').execute()
            total_media = media_response.count if hasattr(media_response, 'count') else len(media_response.data)
            
            # Get top sources
            sources_response = self.client.table('articles').select('source_id').execute()
            source_counts = {}
            for article in sources_response.data:
                source_id = article.get('source_id', 'unknown')
                source_counts[source_id] = source_counts.get(source_id, 0) + 1
            
            # Sort and get top 5
            top_sources = sorted(source_counts.items(), key=lambda x: x[1], reverse=True)[:5]
            top_sources_list = [
                {"source_id": source_id, "count": count, "source_name": source_id.replace('_', ' ').title()}
                for source_id, count in top_sources
            ]
            
            stats = {
                'total_articles': total_count,
                'by_status': status_counts,
                'articles_today': 0,  # TODO: Calculate from created_at
                'articles_7_days': 0,  # TODO: Calculate from created_at
                'articles_with_media': 0,  # TODO: Join with media_files
                'total_media': total_media,
                'media_by_status': {
                    'completed': 0,  # TODO: Get from media_files
                    'failed': 0
                },
                'top_sources': top_sources_list,
                'media_percentage': 0,
                'timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Retrieved real Supabase stats: {total_count} articles, statuses: {status_counts}")
            return stats
            
        except Exception as e:
            logger.error(f"Failed to get Supabase stats: {e}")
            # Return empty stats on error
            return {
                'total_articles': 0,
                'by_status': {},
                'articles_today': 0,
                'articles_7_days': 0,
                'articles_with_media': 0,
                'total_media': 0,
                'media_by_status': {},
                'top_sources': [],
                'media_percentage': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_articles(self, page: int = 1, limit: int = 50, status: Optional[str] = None) -> Dict[str, Any]:
        """Get paginated articles from Supabase"""
        try:
            offset = (page - 1) * limit
            
            # Build query
            query = self.client.table('articles').select('*')
            
            # Add status filter if provided
            if status and status != 'all':
                query = query.eq('content_status', status)
            
            # Add pagination and ordering
            query = query.order('created_at', desc=True).range(offset, offset + limit - 1)
            
            # Execute query
            response = query.execute()
            
            # Get total count for pagination
            count_query = self.client.table('articles').select('*', count='exact')
            if status and status != 'all':
                count_query = count_query.eq('content_status', status)
            count_response = count_query.execute()
            total_count = count_response.count if hasattr(count_response, 'count') else len(count_response.data)
            
            return {
                'articles': response.data,
                'total': total_count,
                'page': page,
                'pages': (total_count + limit - 1) // limit,
                'limit': limit
            }
            
        except Exception as e:
            logger.error(f"Failed to get articles from Supabase: {e}")
            return {
                'articles': [],
                'total': 0,
                'page': 1,
                'pages': 1,
                'limit': limit,
                'error': str(e)
            }
    
    def test_connection(self) -> bool:
        """Test if Supabase connection is working"""
        try:
            response = self.client.table('articles').select('article_id').limit(1).execute()
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            return False

# Singleton instance
_supabase_connection = None

def get_supabase_connection() -> SupabaseConnection:
    """Get or create Supabase connection singleton"""
    global _supabase_connection
    if _supabase_connection is None:
        _supabase_connection = SupabaseConnection()
    return _supabase_connection
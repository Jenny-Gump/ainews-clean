"""
Consolidated Supabase client for monitoring system.
Combines functionality from multiple redundant implementations.
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from collections import defaultdict
import logging

from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class SupabaseClient:
    """
    Unified Supabase client for monitoring system.
    Consolidates functionality from:
    - SupabaseMonitoring
    - SupabaseMonitoringDatabase
    - SupabaseConnection
    - SupabaseMonitoringAdapter
    - SupabaseRealtimeMonitor
    """
    
    def __init__(self):
        self.url = os.getenv('SUPABASE_URL')
        self.key = os.getenv('SUPABASE_ANON_KEY')
        
        if not self.url or not self.key:
            raise ValueError("Supabase credentials not found in environment variables")
        
        self.client: Client = create_client(self.url, self.key)
        self._cache = {}
        self._cache_ttl = 300  # 5 minutes cache TTL
        self._last_cache_clear = datetime.now()
        
        # Realtime subscriptions
        self._subscriptions = {}
        self._listeners = defaultdict(list)
        
        logger.info(f"Initialized SupabaseClient with URL: {self.url[:30]}...")
    
    # ========== Core Database Operations ==========
    
    def get_table(self, table_name: str):
        """Get table reference for operations."""
        return self.client.table(table_name)
    
    def execute_query(self, query: str, params: Optional[Dict] = None) -> List[Dict]:
        """Execute raw SQL query."""
        try:
            if params:
                result = self.client.rpc('sql', {'query': query, 'params': params}).execute()
            else:
                result = self.client.rpc('sql', {'query': query}).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Query execution error: {e}")
            return []
    
    # ========== Article Operations ==========
    
    def get_articles(self, limit: int = 100, offset: int = 0, 
                    filters: Optional[Dict] = None) -> List[Dict]:
        """Get articles with optional filters."""
        cache_key = f"articles_{limit}_{offset}_{json.dumps(filters or {})}"
        
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if (datetime.now() - cached_time).seconds < self._cache_ttl:
                return cached_data
        
        try:
            query = self.client.table('articles').select('*')
            
            if filters:
                for key, value in filters.items():
                    if value is not None:
                        query = query.eq(key, value)
            
            query = query.order('created_at', desc=True)
            query = query.range(offset, offset + limit - 1)
            
            result = query.execute()
            data = result.data if result.data else []
            
            # Cache the result
            self._cache[cache_key] = (data, datetime.now())
            
            return data
            
        except Exception as e:
            logger.error(f"Error fetching articles: {e}")
            return []
    
    def get_article_by_id(self, article_id: str) -> Optional[Dict]:
        """Get single article by ID."""
        try:
            result = self.client.table('articles').select('*').eq('article_id', article_id).single().execute()
            return result.data
        except Exception as e:
            logger.error(f"Error fetching article {article_id}: {e}")
            return None
    
    def update_article(self, article_id: str, updates: Dict) -> bool:
        """Update article data."""
        try:
            updates['updated_at'] = datetime.now().isoformat()
            result = self.client.table('articles').update(updates).eq('article_id', article_id).execute()
            self._invalidate_cache('articles')
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating article {article_id}: {e}")
            return False
    
    def delete_article(self, article_id: str) -> bool:
        """Delete article."""
        try:
            result = self.client.table('articles').delete().eq('article_id', article_id).execute()
            self._invalidate_cache('articles')
            return True
        except Exception as e:
            logger.error(f"Error deleting article {article_id}: {e}")
            return False
    
    # ========== Source Operations ==========
    
    def get_sources(self) -> List[Dict]:
        """Get all RSS sources."""
        cache_key = "sources_all"
        
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if (datetime.now() - cached_time).seconds < self._cache_ttl:
                return cached_data
        
        try:
            # First try sources table
            result = self.client.table('sources').select('*').execute()
            if result.data:
                self._cache[cache_key] = (result.data, datetime.now())
                return result.data
            
            # Fallback to global_config
            result = self.client.table('global_config').select('*').eq('key', 'rss_sources').single().execute()
            if result.data and result.data.get('value'):
                sources = json.loads(result.data['value'])
                self._cache[cache_key] = (sources, datetime.now())
                return sources
            
            return []
            
        except Exception as e:
            logger.error(f"Error fetching sources: {e}")
            return []
    
    def update_source(self, source_id: str, updates: Dict) -> bool:
        """Update source configuration."""
        try:
            result = self.client.table('sources').update(updates).eq('id', source_id).execute()
            self._invalidate_cache('sources')
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error updating source {source_id}: {e}")
            return False
    
    # ========== Monitoring Operations ==========
    
    def get_system_stats(self) -> Dict:
        """Get system statistics."""
        cache_key = "system_stats"
        
        if cache_key in self._cache:
            cached_data, cached_time = self._cache[cache_key]
            if (datetime.now() - cached_time).seconds < 60:  # 1 minute cache for stats
                return cached_data
        
        try:
            stats = {
                'total_articles': 0,
                'total_sources': 0,
                'articles_today': 0,
                'articles_week': 0,
                'last_update': None
            }
            
            # Get article counts
            result = self.client.table('articles').select('article_id', count='exact').execute()
            stats['total_articles'] = result.count if result.count else 0
            
            # Get today's articles
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            result = self.client.table('articles').select('article_id', count='exact').gte('created_at', today.isoformat()).execute()
            stats['articles_today'] = result.count if result.count else 0
            
            # Get week's articles
            week_ago = today - timedelta(days=7)
            result = self.client.table('articles').select('article_id', count='exact').gte('created_at', week_ago.isoformat()).execute()
            stats['articles_week'] = result.count if result.count else 0
            
            # Get source count
            sources = self.get_sources()
            stats['total_sources'] = len(sources)
            
            # Get last update time
            result = self.client.table('articles').select('created_at').order('created_at', desc=True).limit(1).execute()
            if result.data:
                stats['last_update'] = result.data[0]['created_at']
            
            self._cache[cache_key] = (stats, datetime.now())
            return stats
            
        except Exception as e:
            logger.error(f"Error fetching system stats: {e}")
            return {}
    
    def get_pipeline_operations(self, limit: int = 100) -> List[Dict]:
        """Get recent pipeline operations."""
        try:
            result = self.client.table('pipeline_operations').select('*').order('created_at', desc=True).limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching pipeline operations: {e}")
            return []
    
    def record_pipeline_operation(self, operation_type: str, details: Dict) -> bool:
        """Record a pipeline operation."""
        try:
            record = {
                'operation_type': operation_type,
                'details': json.dumps(details),
                'created_at': datetime.now().isoformat(),
                'status': details.get('status', 'completed')
            }
            result = self.client.table('pipeline_operations').insert(record).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error recording pipeline operation: {e}")
            return False
    
    # ========== URL Tracking Operations ==========
    
    def get_tracked_urls(self, limit: int = 1000) -> List[Dict]:
        """Get tracked URLs."""
        try:
            result = self.client.table('tracked_urls').select('*').order('last_seen', desc=True).limit(limit).execute()
            return result.data if result.data else []
        except Exception as e:
            logger.error(f"Error fetching tracked URLs: {e}")
            return []
    
    def is_url_tracked(self, url: str) -> bool:
        """Check if URL is already tracked."""
        try:
            result = self.client.table('tracked_urls').select('url').eq('url', url).execute()
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error checking URL tracking: {e}")
            return False
    
    def track_url(self, url: str, source: Optional[str] = None) -> bool:
        """Track a new URL."""
        try:
            record = {
                'url': url,
                'source': source,
                'first_seen': datetime.now().isoformat(),
                'last_seen': datetime.now().isoformat(),
                'count': 1
            }
            
            # Try to update existing record first
            existing = self.client.table('tracked_urls').select('*').eq('url', url).execute()
            if existing.data:
                # Update count and last_seen
                update = {
                    'last_seen': datetime.now().isoformat(),
                    'count': existing.data[0]['count'] + 1
                }
                result = self.client.table('tracked_urls').update(update).eq('url', url).execute()
            else:
                # Insert new record
                result = self.client.table('tracked_urls').insert(record).execute()
            
            return bool(result.data)
        except Exception as e:
            logger.error(f"Error tracking URL: {e}")
            return False
    
    # ========== Cache Management ==========
    
    def _invalidate_cache(self, prefix: Optional[str] = None):
        """Invalidate cache entries."""
        if prefix:
            keys_to_remove = [k for k in self._cache.keys() if k.startswith(prefix)]
            for key in keys_to_remove:
                del self._cache[key]
        else:
            self._cache.clear()
    
    def _clear_old_cache(self):
        """Clear expired cache entries."""
        now = datetime.now()
        if (now - self._last_cache_clear).seconds > 600:  # Clear every 10 minutes
            keys_to_remove = []
            for key, (data, cached_time) in self._cache.items():
                if (now - cached_time).seconds > self._cache_ttl:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self._cache[key]
            
            self._last_cache_clear = now
    
    # ========== Realtime Operations ==========
    
    async def subscribe_to_changes(self, table: str, callback):
        """Subscribe to realtime changes on a table."""
        try:
            # Note: Supabase Python client doesn't support realtime yet
            # This is a placeholder for future implementation
            logger.info(f"Realtime subscription requested for table: {table}")
            self._listeners[table].append(callback)
        except Exception as e:
            logger.error(f"Error subscribing to changes: {e}")
    
    async def unsubscribe_from_changes(self, table: str):
        """Unsubscribe from realtime changes."""
        try:
            if table in self._listeners:
                del self._listeners[table]
            logger.info(f"Unsubscribed from table: {table}")
        except Exception as e:
            logger.error(f"Error unsubscribing: {e}")
    
    # ========== Health Check ==========
    
    def health_check(self) -> Dict:
        """Check Supabase connection health."""
        try:
            # Try a simple query
            result = self.client.table('global_config').select('key').limit(1).execute()
            return {
                'status': 'healthy',
                'connected': True,
                'url': self.url[:30] + '...',
                'cache_size': len(self._cache)
            }
        except Exception as e:
            return {
                'status': 'unhealthy',
                'connected': False,
                'error': str(e)
            }
    
    def close(self):
        """Close Supabase connection and clear cache."""
        self._cache.clear()
        self._listeners.clear()
        logger.info("SupabaseClient closed")


# Singleton instance
_supabase_client = None

def get_supabase_client() -> SupabaseClient:
    """Get or create singleton Supabase client instance."""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client
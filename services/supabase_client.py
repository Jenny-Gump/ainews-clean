"""
Supabase client for AI News Parser
Handles connection and operations with Supabase database
"""

import os
from typing import Optional, Dict, List, Any
from supabase import create_client, Client
from dotenv import load_dotenv
import logging
import httpx

logger = logging.getLogger(__name__)

class SupabaseClient:
    """Supabase client wrapper for AI News operations"""
    
    def __init__(self):
        """Initialize Supabase client with credentials from .env"""
        load_dotenv()
        
        self.url = os.getenv('SUPABASE_URL')
        self.anon_key = os.getenv('SUPABASE_ANON_KEY')
        self.service_key = os.getenv('SUPABASE_SERVICE_KEY')
        
        if not self.url or not self.anon_key:
            raise ValueError("Supabase credentials not found in .env file")
        
        # Use service key for admin operations if available
        key = self.service_key if self.service_key else self.anon_key
        
        # Configure httpx with proper timeouts and connection limits
        httpx_client = httpx.Client(
            timeout=httpx.Timeout(
                connect=5.0,    # 5 seconds to connect (not 120!)
                read=30.0,      # 30 seconds to read response
                write=10.0,     # 10 seconds to write request
                pool=60.0       # 60 seconds for connection pool
            ),
            limits=httpx.Limits(
                max_keepalive_connections=5,  # Limit persistent connections
                max_connections=10             # Total connection limit
            )
        )
        
        try:
            # Import client options for proper configuration
            from supabase.lib.client_options import SyncClientOptions
            
            # Create options with our configured httpx client
            options = SyncClientOptions(
                httpx_client=httpx_client,
                postgrest_client_timeout=30  # Reduce from default 120 to 30
            )
            
            self.client: Client = create_client(self.url, key, options)
            logger.info(f"Connected to Supabase with optimized timeouts: {self.url}")
            
            # Track requests for connection pool management
            self.request_count = 0
            self.max_requests_per_session = 100
            
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            raise
    
    def test_connection(self) -> bool:
        """Test Supabase connection"""
        try:
            # Try to fetch tables list
            response = self.client.table('articles').select('count', count='exact').limit(1).execute()
            logger.info("Supabase connection successful")
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            return False
    
    def create_tables(self) -> bool:
        """Create necessary tables in Supabase if they don't exist"""
        # Note: Table creation should be done via Supabase Dashboard or SQL Editor
        # This is just a placeholder for documentation
        tables_sql = """
        -- Articles table
        CREATE TABLE IF NOT EXISTS articles (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            article_id TEXT UNIQUE NOT NULL,
            source_id TEXT,
            url TEXT NOT NULL,
            title TEXT,
            content TEXT,
            published_at TIMESTAMP,
            content_status TEXT,
            media_status TEXT,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Media files table
        CREATE TABLE IF NOT EXISTS media_files (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            article_id TEXT REFERENCES articles(article_id),
            url TEXT NOT NULL,
            local_path TEXT,
            alt_text TEXT,
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- WordPress articles table
        CREATE TABLE IF NOT EXISTS wordpress_articles (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            article_id TEXT REFERENCES articles(article_id),
            wordpress_id INTEGER,
            title_ru TEXT,
            content_ru TEXT,
            tags TEXT[],
            categories INTEGER[],
            created_at TIMESTAMP DEFAULT NOW()
        );
        
        -- Sources table
        CREATE TABLE IF NOT EXISTS sources (
            id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
            source_id TEXT UNIQUE NOT NULL,
            name TEXT,
            url TEXT,
            feed_url TEXT,
            language TEXT,
            active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT NOW()
        );
        """
        logger.info("Tables should be created via Supabase Dashboard SQL Editor")
        return True
    
    def insert_article(self, article_data: Dict[str, Any]) -> Optional[Dict]:
        """Insert new article into Supabase with duplicate protection"""
        try:
            url = article_data.get('url')
            if not url:
                logger.error("Cannot insert article without URL")
                return None
                
            # Double-check for duplicates before insertion
            if self.url_exists(url):
                logger.debug(f"Article already exists, skipping: {url[:100]}")
                return None
            
            # Convert datetime objects to ISO strings for Supabase
            processed_data = {}
            for key, value in article_data.items():
                if hasattr(value, 'isoformat'):  # datetime object
                    processed_data[key] = value.isoformat()
                else:
                    processed_data[key] = value
            
            response = self.client.table('articles').insert(processed_data).execute()
            logger.info(f"Article inserted: {article_data.get('article_id')}")
            return response.data[0] if response.data else None
            
        except Exception as e:
            error_msg = str(e).lower()
            # Handle UNIQUE constraint violation gracefully
            if 'unique' in error_msg or 'duplicate' in error_msg:
                logger.debug(f"Duplicate article detected by database constraint: {article_data.get('url', '')[:100]}")
                return None
            else:
                logger.error(f"Failed to insert article: {e}")
                return None
    
    def get_article(self, article_id: str) -> Optional[Dict]:
        """Get article by ID"""
        try:
            response = self.client.table('articles').select('*').eq('article_id', article_id).single().execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get article {article_id}: {e}")
            return None
    
    def update_article(self, article_id: str, update_data: Dict[str, Any]) -> bool:
        """Update article in Supabase"""
        try:
            response = self.client.table('articles').update(update_data).eq('article_id', article_id).execute()
            logger.info(f"Article updated: {article_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update article {article_id}: {e}")
            return False
    
    def get_pending_articles(self, limit: int = 10) -> List[Dict]:
        """Get pending articles for processing"""
        try:
            response = self.client.table('articles')\
                .select('*')\
                .eq('content_status', 'pending')\
                .limit(limit)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get pending articles: {e}")
            return []
    
    def insert_media(self, media_data: Dict[str, Any]) -> Optional[Dict]:
        """Insert media file record"""
        try:
            response = self.client.table('media_files').insert(media_data).execute()
            logger.info(f"Media inserted for article: {media_data.get('article_id')}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to insert media: {e}")
            return None
    
    def get_article_media(self, article_id: str) -> List[Dict]:
        """Get all media files for an article"""
        try:
            response = self.client.table('media_files')\
                .select('*')\
                .eq('article_id', article_id)\
                .execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get media for article {article_id}: {e}")
            return []
    
    def insert_wordpress_article(self, wp_data: Dict[str, Any]) -> Optional[Dict]:
        """Insert WordPress article data"""
        try:
            response = self.client.table('wordpress_articles').insert(wp_data).execute()
            logger.info(f"WordPress article inserted: {wp_data.get('article_id')}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to insert WordPress article: {e}")
            return None
    
    def get_sources(self, active_only: bool = True) -> List[Dict]:
        """Get all sources"""
        try:
            query = self.client.table('sources').select('*')
            if active_only:
                query = query.eq('active', True)
            response = query.execute()
            return response.data
        except Exception as e:
            logger.error(f"Failed to get sources: {e}")
            return []
    
    def upsert_source(self, source_data: Dict[str, Any]) -> Optional[Dict]:
        """Insert or update source"""
        try:
            response = self.client.table('sources').upsert(
                source_data,
                on_conflict='source_id'  # Указываем конфликтную колонку для корректного UPSERT
            ).execute()
            logger.info(f"Source upserted: {source_data.get('source_id')}")
            return response.data[0] if response.data else None
        except Exception as e:
            logger.error(f"Failed to upsert source: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics - main.py compatible format"""
        try:
            # Count articles by status
            total = self.client.table('articles').select('count', count='exact').execute()
            pending = self.client.table('articles').select('count', count='exact').eq('content_status', 'pending').execute()
            parsed = self.client.table('articles').select('count', count='exact').eq('content_status', 'parsed').execute()
            published = self.client.table('articles').select('count', count='exact').eq('content_status', 'published').execute()
            failed = self.client.table('articles').select('count', count='exact').eq('content_status', 'failed').execute()
            
            # Count media and sources
            media = self.client.table('media_files').select('count', count='exact').execute()
            sources = self.client.table('sources').select('count', count='exact').execute()
            
            # EXACT format expected by main.py
            return {
                'articles': {
                    'total': total.count if total else 0,
                    'by_status': {
                        'pending': pending.count if pending else 0,
                        'parsed': parsed.count if parsed else 0,
                        'published': published.count if published else 0,
                        'failed': failed.count if failed else 0
                    }
                },
                'sources': sources.count if sources else 0,
                'media': {
                    'total': media.count if media else 0
                }
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {
                'articles': {'total': 0, 'by_status': {}},
                'sources': 0,
                'media': {'total': 0}
            }
    
    def get_sources_with_stats(self) -> List[Dict]:
        """Get sources with article counts for main.py"""
        try:
            # Get all sources
            sources_response = self.client.table('sources').select('source_id, name').execute()
            sources = sources_response.data if sources_response.data else []
            
            result = []
            for source in sources:
                # Count articles for each source
                count_response = self.client.table('articles')\
                    .select('count', count='exact')\
                    .eq('source_id', source['source_id'])\
                    .execute()
                
                result.append({
                    'source_id': source['source_id'],
                    'name': source['name'],
                    'article_count': count_response.count if count_response else 0
                })
            
            # Sort by article count descending
            result.sort(key=lambda x: x['article_count'], reverse=True)
            return result
            
        except Exception as e:
            logger.error(f"Failed to get sources with stats: {e}")
            return []
    
    def get_global_config(self, key: str) -> Optional[str]:
        """Get global configuration value"""
        try:
            response = self.client.table('global_config')\
                .select('value')\
                .eq('key', key)\
                .limit(1)\
                .execute()
            
            if response.data and len(response.data) > 0:
                return response.data[0]['value']
            return None
            
        except Exception as e:
            logger.error(f"Failed to get global config {key}: {e}")
            return None
    
    def set_global_config(self, key: str, value: str, description: Optional[str] = None) -> bool:
        """Set global configuration value"""
        try:
            config_data = {
                'key': key,
                'value': value,
                'description': description,
                'updated_at': 'now()'
            }
            
            response = self.client.table('global_config')\
                .upsert(config_data)\
                .execute()
            
            logger.info(f"Global config updated: {key} = {value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set global config {key}: {e}")
            return False
    
    def get_global_last_parsed(self) -> str:
        """Get global last parsed timestamp"""
        value = self.get_global_config('global_last_parsed')
        return value if value else '2025-08-01T00:00:00Z'
    
    def set_global_last_parsed(self, timestamp: str) -> bool:
        """Set global last parsed timestamp"""
        return self.set_global_config('global_last_parsed', timestamp, 'Global last parsed timestamp for all sources')
    
    def article_exists(self, url: str) -> bool:
        """Check if article exists and is not deleted with timeout protection"""
        import time
        start_time = time.time()
        
        try:
            # Add timeout protection - max 3 seconds
            response = self.client.table('articles')\
                .select('article_id')\
                .eq('url', url)\
                .neq('content_status', 'deleted')\
                .limit(1)\
                .execute()
            
            elapsed = time.time() - start_time
            if elapsed > 2:
                logger.warning(f"Slow article_exists check: {elapsed:.2f}s for URL: {url[:100]}")
            
            return len(response.data) > 0
            
        except Exception as e:
            elapsed = time.time() - start_time
            if elapsed > 3:
                logger.error(f"article_exists timeout after {elapsed:.2f}s for URL: {url[:100]}")
                # При таймауте возвращаем False чтобы продолжить обработку
                return False
            logger.error(f"Failed to check article existence: {e}")
            return False
    
    def update_article_basic_content(self, article_id: str, title: str, content: str, 
                                   description: str = None, media_count: int = 0) -> bool:
        """Update article with basic content info"""
        try:
            update_data = {
                'title': title,
                'content': content,
                'content_status': 'parsed',
                'parsed_at': 'now()',
                'media_count': media_count
            }
            
            if description:
                update_data['description'] = description
            
            response = self.client.table('articles')\
                .update(update_data)\
                .eq('article_id', article_id)\
                .execute()
            
            logger.info(f"Article content updated: {article_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update article content {article_id}: {e}")
            return False
    
    def update_article_status(self, article_id: str, status: str, error: str = None) -> bool:
        """Update article status"""
        try:
            update_data = {
                'content_status': status
            }
            
            if error:
                update_data['content_error'] = error
                
            if status == 'parsed':
                update_data['parsed_at'] = 'now()'
            
            response = self.client.table('articles')\
                .update(update_data)\
                .eq('article_id', article_id)\
                .execute()
            
            logger.info(f"Article status updated: {article_id} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update article status {article_id}: {e}")
            return False
    
    def url_exists(self, url: str) -> bool:
        """Check if URL already exists and is not deleted"""
        try:
            response = self.client.table('articles')\
                .select('article_id')\
                .eq('url', url)\
                .neq('content_status', 'deleted')\
                .limit(1)\
                .execute()
            
            return len(response.data) > 0
            
        except Exception as e:
            logger.error(f"Failed to check URL existence: {e}")
            return False
    
    def add_media_file(self, article_id: str, url: str, alt_text: str = '', 
                      caption: str = '', media_type: str = 'image') -> Optional[str]:
        """Add media file record"""
        try:
            media_data = {
                'article_id': article_id,
                'url': url,
                'alt_text': alt_text,
                'caption': caption,
                'type': media_type,
                'status': 'pending'
            }
            
            response = self.client.table('media_files')\
                .insert(media_data)\
                .execute()
            
            if response.data:
                media_id = response.data[0]['id']
                logger.info(f"Media file added: {media_id} for article {article_id}")
                return str(media_id)
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to add media file: {e}")
            return None
    
    def update_article_media_status(self, article_id: str, status: str) -> bool:
        """Update article media status"""
        try:
            update_data = {
                'media_status': status
            }
            
            response = self.client.table('articles')\
                .update(update_data)\
                .eq('article_id', article_id)\
                .execute()
            
            logger.info(f"Article media status updated: {article_id} -> {status}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update media status {article_id}: {e}")
            return False
    
    def update_article_media_count(self, article_id: str, media_count: int) -> bool:
        """Update article media count"""
        try:
            update_data = {
                'media_count': media_count
            }
            
            response = self.client.table('articles')\
                .update(update_data)\
                .eq('article_id', article_id)\
                .execute()
            
            logger.info(f"Article media count updated: {article_id} -> {media_count}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update media count {article_id}: {e}")
            return False
    
    def get_connection(self):
        """Context manager compatibility - return self"""
        return self
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        pass
    
    def reset_client(self):
        """Reset Supabase client to clear connection pool"""
        try:
            # Close existing httpx client if it exists
            if hasattr(self.client, '_client') and hasattr(self.client._client, 'close'):
                self.client._client.close()
                logger.info("Closed existing Supabase httpx client")
            
            # Recreate the client with fresh connections
            key = self.service_key if self.service_key else self.anon_key
            
            # Configure new httpx client
            httpx_client = httpx.Client(
                timeout=httpx.Timeout(
                    connect=5.0,
                    read=30.0,
                    write=10.0,
                    pool=60.0
                ),
                limits=httpx.Limits(
                    max_keepalive_connections=5,
                    max_connections=10
                )
            )
            
            from supabase.lib.client_options import SyncClientOptions
            options = SyncClientOptions(
                httpx_client=httpx_client,
                postgrest_client_timeout=30
            )
            
            self.client = create_client(self.url, key, options)
            self.request_count = 0
            logger.info("Supabase client reset with fresh connection pool")
            
        except Exception as e:
            logger.error(f"Failed to reset Supabase client: {e}")
    
    def check_and_reset_if_needed(self):
        """Check request count and reset client if needed"""
        self.request_count += 1
        if self.request_count >= self.max_requests_per_session:
            logger.info(f"Resetting Supabase client after {self.request_count} requests")
            self.reset_client()
    
    
    def get_article_for_wordpress_prep(self, article_id: str) -> dict:
        """Get article data for WordPress preparation"""
        try:
            response = self.client.table('articles')\
                .select('*')\
                .eq('article_id', article_id)\
                .single()\
                .execute()
            
            return response.data if response.data else {}
            
        except Exception as e:
            logger.error(f"Failed to get article for WP prep {article_id}: {e}")
            return {}
    
    def get_article_media_files(self, article_id: str) -> list:
        """Get media files for article"""
        try:
            response = self.client.table('media_files')\
                .select('*')\
                .eq('article_id', article_id)\
                .execute()
            
            return response.data if response.data else []
            
        except Exception as e:
            logger.error(f"Failed to get media files for {article_id}: {e}")
            return []
    
    def save_wordpress_article(self, article_data: dict) -> bool:
        """Save WordPress article data"""
        try:
            response = self.client.table('wordpress_articles')\
                .insert(article_data)\
                .execute()
            
            logger.info(f"WordPress article saved: {article_data.get('article_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save WordPress article: {e}")
            return False
    
    def get_wordpress_article(self, article_id: str) -> dict:
        """Get WordPress article by article_id"""
        try:
            response = self.client.table('wordpress_articles')\
                .select('*')\
                .eq('article_id', article_id)\
                .limit(1)\
                .execute()
            
            return response.data[0] if response.data else {}
            
        except Exception as e:
            logger.error(f"Failed to get WordPress article {article_id}: {e}")
            return {}
    
    def update_wordpress_published(self, article_id: str, wp_post_id: int) -> bool:
        """Mark WordPress article as published"""
        try:
            # Update wordpress_articles table
            self.client.table('wordpress_articles')\
                .update({'published_to_wp': True, 'wp_post_id': wp_post_id})\
                .eq('article_id', article_id)\
                .execute()
            
            # Update main articles table
            self.client.table('articles')\
                .update({'content_status': 'published'})\
                .eq('article_id', article_id)\
                .execute()
            
            logger.info(f"Article marked as published: {article_id} -> WP {wp_post_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark as published {article_id}: {e}")
            return False
    
    def update_media_file(self, media_id: str, file_path: str = None, file_size: int = None, 
                         width: int = None, height: int = None, status: str = None) -> bool:
        """Update media file information"""
        try:
            update_data = {}
            
            if file_path is not None:
                update_data['file_path'] = file_path
            if file_size is not None:
                update_data['file_size'] = file_size
            if width is not None:
                update_data['width'] = width
            if height is not None:
                update_data['height'] = height  
            if status is not None:
                update_data['status'] = status
                
            if not update_data:
                return True  # Nothing to update
                
            response = self.client.table('media_files')\
                .update(update_data)\
                .eq('id', media_id)\
                .execute()
            
            logger.info(f"Media file updated: {media_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update media file {media_id}: {e}")
            return False


# Singleton instance
_supabase_client: Optional[SupabaseClient] = None

def get_supabase_client() -> SupabaseClient:
    """Get or create Supabase client instance"""
    global _supabase_client
    if _supabase_client is None:
        _supabase_client = SupabaseClient()
    return _supabase_client


if __name__ == "__main__":
    # Test connection
    logging.basicConfig(level=logging.INFO)
    
    client = get_supabase_client()
    
    # Test connection
    if client.test_connection():
        print("✅ Supabase connection successful!")
        
        # Get stats
        stats = client.get_stats()
        print("\n📊 Database Statistics:")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    else:
        print("❌ Failed to connect to Supabase")
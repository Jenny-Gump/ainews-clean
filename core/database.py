"""
Database module for AI News Parser - Extract API System
Simplified and optimized for Extract API functionality only
"""
import sqlite3
import os
import hashlib
import time
import json
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from contextlib import contextmanager
from app_logging import get_logger

logger = get_logger(__name__)


class Database:
    """Simplified database management for Extract API system"""
    
    def __init__(self, db_path: str = "data/ainews.db"):
        self.db_path = db_path
        self._ensure_db_directory()
        self._init_database()
    
    def _ensure_db_directory(self):
        """Creates database directory if it doesn't exist"""
        db_dir = os.path.dirname(self.db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir)
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections with performance logging"""
        start_time = time.time()
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA busy_timeout = 30000")
        
        # Track connection acquisition time
        connect_time = time.time() - start_time
        if connect_time > 0.1:  # Log slow connections (>100ms)
            from app_logging import log_operation
            log_operation('db_connection_slow',
                duration_seconds=connect_time,
                db_path=self.db_path,
                timeout_setting=30.0
            )
        
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            # Log database errors
            from app_logging import log_error
            log_error('database_error', str(e),
                db_path=self.db_path,
                connection_time=connect_time
            )
            raise
        finally:
            conn.close()
    
    def _log_slow_query(self, query: str, duration: float, params=None, table_name: str = None):
        """Log slow database queries for performance monitoring"""
        if duration > 0.1:  # Log queries taking >100ms
            from app_logging import log_operation
            log_operation('db_query_slow',
                query_type=self._get_query_type(query),
                table_name=table_name or self._extract_table_name(query),
                duration_seconds=duration,
                query_preview=query[:200],  # First 200 chars of query
                has_params=params is not None,
                params_count=len(params) if params else 0
            )
    
    def _get_query_type(self, query: str) -> str:
        """Extract query type (SELECT, INSERT, UPDATE, DELETE) from SQL"""
        query_upper = query.strip().upper()
        if query_upper.startswith('SELECT'):
            return 'SELECT'
        elif query_upper.startswith('INSERT'):
            return 'INSERT'
        elif query_upper.startswith('UPDATE'):
            return 'UPDATE'
        elif query_upper.startswith('DELETE'):
            return 'DELETE'
        elif query_upper.startswith('CREATE'):
            return 'CREATE'
        else:
            return 'OTHER'
    
    def _extract_table_name(self, query: str) -> str:
        """Extract table name from SQL query"""
        import re
        # Simple regex to extract table name
        patterns = [
            r'FROM\s+([\w_]+)',
            r'INSERT\s+INTO\s+([\w_]+)',
            r'UPDATE\s+([\w_]+)',
            r'CREATE\s+TABLE\s+(?:IF\s+NOT\s+EXISTS\s+)?([\w_]+)'
        ]
        
        query_upper = query.upper()
        for pattern in patterns:
            match = re.search(pattern, query_upper)
            if match:
                return match.group(1).lower()
        
        return 'unknown'
    
    def execute_with_timing(self, conn, query: str, params=None, table_name: str = None):
        """Execute query with performance timing"""
        start_time = time.time()
        try:
            if params:
                result = conn.execute(query, params)
            else:
                result = conn.execute(query)
            
            duration = time.time() - start_time
            self._log_slow_query(query, duration, params, table_name)
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            # Log failed query
            from app_logging import log_error
            log_error('db_query_failed', str(e),
                query_type=self._get_query_type(query),
                table_name=table_name or self._extract_table_name(query),
                duration_seconds=duration,
                query_preview=query[:200]
            )
            raise
    
    def _init_database(self):
        """Initialize database schema"""
        with self.get_connection() as conn:
            # Create sources table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS sources (
                    source_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    url TEXT NOT NULL,
                    type TEXT DEFAULT 'rss',
                    has_rss INTEGER DEFAULT 1,
                    last_status TEXT DEFAULT 'active',
                    last_error TEXT,
                    success_rate REAL DEFAULT 1.0,
                    last_parsed DATETIME,
                    total_articles INTEGER DEFAULT 0,
                    category TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create articles table with Extract API fields
            conn.execute("""
                CREATE TABLE IF NOT EXISTS articles (
                    article_id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    url TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL,
                    description TEXT,
                    published_date DATETIME,
                    content TEXT,
                    content_status TEXT DEFAULT 'pending',
                    content_error TEXT,
                    parsed_at DATETIME,
                    media_count INTEGER DEFAULT 0,
                    summary TEXT,
                    tags TEXT,
                    categories TEXT,
                    language TEXT,
                    word_count INTEGER,
                    reading_time_minutes INTEGER,
                    discovered_via TEXT DEFAULT 'rss',
                    retry_count INTEGER DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES sources(source_id)
                )
            """)
            
            # Create media_files table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS media_files (
                    media_id TEXT PRIMARY KEY,
                    article_id TEXT NOT NULL,
                    source_id TEXT NOT NULL,
                    url TEXT NOT NULL,
                    file_path TEXT,
                    file_size INTEGER,
                    type TEXT DEFAULT 'image',
                    mime_type TEXT,
                    width INTEGER,
                    height INTEGER,
                    alt_text TEXT,
                    caption TEXT,
                    image_order INTEGER,
                    status TEXT DEFAULT 'pending',
                    error TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles(article_id),
                    FOREIGN KEY (source_id) REFERENCES sources(source_id)
                )
            """)
            
            # Create related_links table for Extract API
            conn.execute("""
                CREATE TABLE IF NOT EXISTS related_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    article_id TEXT NOT NULL,
                    title TEXT NOT NULL,
                    url TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (article_id) REFERENCES articles(article_id)
                )
            """)
            
            # Create global_config table for system-wide settings
            conn.execute("""
                CREATE TABLE IF NOT EXISTS global_config (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Initialize default global config values
            conn.execute("""
                INSERT OR IGNORE INTO global_config (key, value, description)
                VALUES ('global_last_parsed', '2025-08-01T00:00:00Z', 'Global last parsed timestamp for all sources')
            """)
            
            # Create indexes for performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_source_id ON articles(source_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(content_status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_articles_created ON articles(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_media_article_id ON media_files(article_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_media_status ON media_files(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_related_links_article_id ON related_links(article_id)")
    
    @staticmethod
    def generate_article_id(url: str) -> str:
        """Generate article_id as SHA256 hash of URL"""
        return hashlib.sha256(url.encode()).hexdigest()[:16]
    
    @staticmethod
    def generate_media_id(article_id: str, url: str) -> str:
        """Generate media_id"""
        return hashlib.sha256(f"{article_id}_{url}".encode()).hexdigest()[:16]
    
    # === Source Management ===
    
    def get_sources(self, active_only: bool = True) -> List[Dict]:
        """Get list of sources"""
        with self.get_connection() as conn:
            query = "SELECT * FROM sources"
            if active_only:
                query += " WHERE last_status = 'active' OR last_status IS NULL"
            query += " ORDER BY name"
            
            cursor = conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_source_status(self, source_id: str, status: str, error: Optional[str] = None):
        """Update source status"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE sources 
                SET last_status = ?, last_error = ?, last_parsed = CURRENT_TIMESTAMP
                WHERE source_id = ?
            """, (status, error, source_id))
            
    
    def update_source_last_parsed(self, source_id: str, timestamp: Optional[datetime] = None):
        """Update source last parsed timestamp"""
        if timestamp is None:
            timestamp = datetime.now()
            
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE sources 
                SET last_parsed = ?
                WHERE source_id = ?
            """, (timestamp, source_id))
    
    def get_source_stats(self, source_id: str) -> Optional[Dict]:
        """Get source statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT success_rate, total_articles, last_status
                FROM sources
                WHERE source_id = ?
            """, (source_id,))
            
            result = cursor.fetchone()
            if result:
                return dict(result)
            return None
    
    def get_source_info(self, source_id: str) -> Optional[Dict]:
        """Get information about a source"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sources WHERE source_id = ?
            """, (source_id,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
    
    # === Article Management ===
    
    def article_exists(self, url: str) -> bool:
        """Check if article exists"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT 1 FROM articles WHERE url = ? LIMIT 1', (url,))
            return cursor.fetchone() is not None
    
    def insert_article(self, article: Dict) -> Optional[str]:
        """Insert new article"""
        required_fields = ['url', 'title', 'source_id']
        if not all(field in article for field in required_fields):
            logger.error(f"Missing required fields: {required_fields}")
            return None
        
        # Generate article_id
        article_id = article.get('article_id') or self.generate_article_id(article['url'])
        
        # Check deduplication
        if self.article_exists(article['url']):
            logger.debug(f"Article already exists: {article['url']}")
            return None
        
        try:
            with self.get_connection() as conn:
                # Insert article with performance timing
                self.execute_with_timing(conn, """
                    INSERT INTO articles (
                        article_id, source_id, url, title, description,
                        published_date, content_status, discovered_via, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 'pending', ?, CURRENT_TIMESTAMP)
                """, (
                    article_id,
                    article['source_id'],
                    article['url'],
                    article['title'],
                    article.get('description'),
                    article.get('published_date'),
                    article.get('discovered_via', 'rss')
                ), table_name='articles')
                
                # Update source statistics with timing
                self.execute_with_timing(conn, """
                    UPDATE sources 
                    SET total_articles = total_articles + 1
                    WHERE source_id = ?
                """, (article['source_id'],), table_name='sources')
                
                return article_id
                
        except sqlite3.IntegrityError as e:
            logger.warning(f"Integrity error inserting article: {e}")
            return None
        except Exception as e:
            logger.error(f"Error inserting article: {e}")
            return None
    
    def get_pending_articles_count(self) -> int:
        """Count articles with 'pending' status"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) as count FROM articles WHERE content_status = 'pending'
            """)
            
            row = cursor.fetchone()
            return row['count'] if row else 0
    
    def get_pending_articles(self, limit: int = 10, source_id: Optional[str] = None) -> List[Dict]:
        """Get pending articles for parsing"""
        with self.get_connection() as conn:
            query = """
                SELECT article_id, source_id, url, title, description, 
                       published_date, retry_count, created_at
                FROM articles 
                WHERE content_status = 'pending'
            """
            
            params = []
            if source_id:
                query += " AND source_id = ?"
                params.append(source_id)
            
            query += " ORDER BY retry_count ASC, created_at DESC LIMIT ?"
            params.append(limit)
            
            cursor = conn.cursor()
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def update_article_content(self, article_id: str, content_data: Dict):
        """Update article with parsed content"""
        with self.get_connection() as conn:
            # Build update query dynamically
            fields = []
            values = []
            
            # Always update these fields
            fields.extend(['content = ?', 'content_status = ?', 'parsed_at = CURRENT_TIMESTAMP'])
            values.extend([content_data.get('content'), 'parsed'])
            
            # Optional Extract API fields
            optional_fields = {
                'summary': 'summary',
                'tags': 'tags',
                'categories': 'categories',
                'language': 'language',
                'word_count': 'word_count',
                'reading_time_minutes': 'reading_time_minutes'
            }
            
            for db_field, data_field in optional_fields.items():
                if data_field in content_data:
                    fields.append(f"{db_field} = ?")
                    value = content_data[data_field]
                    # Convert lists to JSON strings
                    if isinstance(value, list):
                        value = json.dumps(value)
                    values.append(value)
            
            values.append(article_id)
            query = f"UPDATE articles SET {', '.join(fields)} WHERE article_id = ?"
            
            conn.execute(query, values)
    
    def update_article_status(self, article_id: str, status: str, error: Optional[str] = None):
        """Update article status"""
        with self.get_connection() as conn:
            if error:
                conn.execute("""
                    UPDATE articles 
                    SET content_status = ?, content_error = ?
                    WHERE article_id = ?
                """, (status, error, article_id))
            else:
                conn.execute("""
                    UPDATE articles 
                    SET content_status = ?
                    WHERE article_id = ?
                """, (status, article_id))
            
    
    def increment_article_retry_count(self, article_id: str):
        """Increment retry count for article"""
        with self.get_connection() as conn:
            conn.execute("""
                UPDATE articles 
                SET retry_count = retry_count + 1
                WHERE article_id = ?
            """, (article_id,))
    
    # === Media Management ===
    
    def insert_media(self, media: Dict) -> Optional[str]:
        """Insert media file record"""
        required_fields = ['article_id', 'source_id', 'url']
        if not all(field in media for field in required_fields):
            logger.warning(f"Missing required fields for media: {required_fields}")
            return None
        
        # Check file size limit (2MB)
        file_size = media.get('file_size', 0)
        if file_size > 2097152:
            logger.warning(f"File too large: {file_size/1024/1024:.1f}MB")
            return None
        
        media_id = Database.generate_media_id(media['article_id'], media['url'])
        
        with self.get_connection() as conn:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO media_files (
                        media_id, article_id, source_id, url, file_path,
                        file_size, type, mime_type, width, height, 
                        alt_text, caption, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    media_id,
                    media['article_id'],
                    media['source_id'],
                    media['url'],
                    media.get('file_path'),
                    file_size,
                    media.get('type', 'image'),
                    media.get('mime_type'),
                    media.get('width'),
                    media.get('height'),
                    media.get('alt_text'),
                    media.get('caption'),
                    media.get('status', 'pending')
                ))
                
                # Update media count in article
                conn.execute("""
                    UPDATE articles 
                    SET media_count = media_count + 1
                    WHERE article_id = ?
                """, (media['article_id'],))
                
                return media_id
                
            except sqlite3.IntegrityError:
                return None
    
    def get_pending_media(self, limit: int = 10) -> List[Dict]:
        """Get pending media files for download"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM media_files 
                WHERE status = 'pending'
                ORDER BY created_at DESC
                LIMIT ?
            """, (limit,))
            return [dict(row) for row in cursor.fetchall()]
    
    def update_media_status(self, media_id: str, status: str, 
                           file_path: Optional[str] = None,
                           error: Optional[str] = None):
        """Update media file status"""
        with self.get_connection() as conn:
            if file_path:
                conn.execute("""
                    UPDATE media_files 
                    SET status = ?, file_path = ?, error = ?
                    WHERE media_id = ?
                """, (status, file_path, error, media_id))
            else:
                conn.execute("""
                    UPDATE media_files 
                    SET status = ?, error = ?
                    WHERE media_id = ?
                """, (status, error, media_id))
    
    # === Related Links Management ===
    
    def insert_related_links(self, article_id: str, links: List[Dict]):
        """Insert related links for article"""
        if not links:
            return
        
        with self.get_connection() as conn:
            for link in links:
                if 'url' in link and 'title' in link:
                    conn.execute("""
                        INSERT INTO related_links (article_id, title, url)
                        VALUES (?, ?, ?)
                    """, (article_id, link['title'], link['url']))
    
    # === Global Configuration ===
    
    def get_global_config(self, key: str) -> Optional[str]:
        """Get global configuration value"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT value FROM global_config WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row['value'] if row else None
    
    def set_global_config(self, key: str, value: str, description: Optional[str] = None):
        """Set global configuration value"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO global_config (key, value, description, updated_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (key, value, description))
    
    def get_global_last_parsed(self) -> str:
        """Get global last parsed timestamp"""
        value = self.get_global_config('global_last_parsed')
        return value if value else '2025-08-01T00:00:00Z'
    
    def set_global_last_parsed(self, timestamp: str):
        """Set global last parsed timestamp"""
        self.set_global_config('global_last_parsed', timestamp, 'Global last parsed timestamp for all sources')
    
    # === Statistics ===
    
    def get_stats(self) -> Dict:
        """Get database statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total counts
            cursor.execute("SELECT COUNT(*) FROM sources")
            stats['total_sources'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM articles")
            stats['total_articles'] = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM media_files")
            stats['total_media'] = cursor.fetchone()[0]
            
            # Articles by status
            cursor.execute("""
                SELECT content_status, COUNT(*) as count 
                FROM articles 
                GROUP BY content_status
            """)
            stats['articles_by_status'] = {row['content_status']: row['count'] 
                                          for row in cursor.fetchall()}
            
            # Media by status
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM media_files 
                GROUP BY status
            """)
            stats['media_by_status'] = {row['status']: row['count'] 
                                       for row in cursor.fetchall()}
            
            # Top sources
            cursor.execute("""
                SELECT s.name, s.total_articles, s.success_rate
                FROM sources s
                WHERE s.total_articles > 0
                ORDER BY s.total_articles DESC
                LIMIT 10
            """)
            stats['top_sources'] = [dict(row) for row in cursor.fetchall()]
            
            # Database size
            if os.path.exists(self.db_path):
                stats['db_size'] = os.path.getsize(self.db_path)
            else:
                stats['db_size'] = 0
            
            return stats
    
    def get_parsing_statistics(self) -> Dict:
        """Get parsing statistics"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Status counts
            cursor.execute("""
                SELECT content_status, COUNT(*) as count 
                FROM articles 
                GROUP BY content_status
            """)
            status_counts = {row['content_status']: row['count'] for row in cursor.fetchall()}
            
            stats['articles_by_status'] = status_counts
            stats['total_articles'] = sum(status_counts.values())
            stats['pending_articles'] = status_counts.get('pending', 0)
            stats['completed_articles'] = status_counts.get('parsed', 0)
            stats['failed_articles'] = status_counts.get('failed', 0)
            
            # Calculate rates
            total_processed = stats['completed_articles'] + stats['failed_articles']
            if total_processed > 0:
                stats['completion_rate'] = round((stats['completed_articles'] / total_processed) * 100, 1)
                stats['failure_rate'] = round((stats['failed_articles'] / total_processed) * 100, 1)
            else:
                stats['completion_rate'] = 0
                stats['failure_rate'] = 0
            
            # Today's statistics
            cursor.execute("""
                SELECT 
                    COUNT(CASE WHEN content_status = 'parsed' THEN 1 END) as completed_today,
                    COUNT(CASE WHEN content_status = 'failed' THEN 1 END) as failed_today
                FROM articles
                WHERE created_at >= date('now', '-1 day')
            """)
            
            row = cursor.fetchone()
            if row:
                stats['completed_today'] = row['completed_today']
                stats['failed_today'] = row['failed_today']
            
            return stats
    
    # === Maintenance ===
    
    def delete_old_articles(self, days: int = 30) -> int:
        """Delete old articles"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                DELETE FROM articles 
                WHERE created_at < datetime('now', '-' || ? || ' days')
            """, (days,))
            return cursor.rowcount
    
    def vacuum(self):
        """Optimize database with performance logging"""
        start_time = time.time()
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("VACUUM")
            vacuum_time = time.time() - start_time
            
            # Log vacuum operation
            from app_logging import log_operation
            log_operation('db_vacuum',
                duration_seconds=vacuum_time,
                db_path=self.db_path,
                operation='database_optimization'
            )
            
            logger.info(f"Database VACUUM completed in {vacuum_time:.2f}s")
            
        except Exception as e:
            # Log vacuum failure
            from app_logging import log_error
            log_error('db_vacuum_failed', str(e),
                db_path=self.db_path,
                duration_seconds=time.time() - start_time
            )
            raise
        finally:
            conn.close()
    
    def check_database_health(self) -> Dict:
        """Check database health and log any issues"""
        health_report = {
            'healthy': True,
            'issues': [],
            'metrics': {}
        }
        
        start_time = time.time()
        try:
            with self.get_connection() as conn:
                # Check database integrity
                integrity_start = time.time()
                cursor = conn.execute("PRAGMA integrity_check")
                integrity_result = cursor.fetchone()[0]
                integrity_time = time.time() - integrity_start
                
                if integrity_result != 'ok':
                    health_report['healthy'] = False
                    health_report['issues'].append(f'Integrity check failed: {integrity_result}')
                
                # Check table sizes and potential performance issues
                cursor = conn.execute("""
                    SELECT name, 
                           (SELECT COUNT(*) FROM sqlite_master 
                            WHERE type='table' AND name=m.name) as table_count
                    FROM sqlite_master m 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                
                tables = cursor.fetchall()
                total_tables = len(tables)
                
                # Check article table size
                cursor = conn.execute("SELECT COUNT(*) FROM articles")
                articles_count = cursor.fetchone()[0]
                
                # Check for potential performance issues
                if articles_count > 100000:
                    health_report['issues'].append(f'Large articles table: {articles_count} rows')
                
                # Check database file size
                import os
                if os.path.exists(self.db_path):
                    db_size_mb = os.path.getsize(self.db_path) / 1024 / 1024
                    health_report['metrics']['db_size_mb'] = round(db_size_mb, 2)
                    
                    if db_size_mb > 1000:  # >1GB
                        health_report['issues'].append(f'Large database file: {db_size_mb:.1f}MB')
                
                health_report['metrics']['total_tables'] = total_tables
                health_report['metrics']['articles_count'] = articles_count
                health_report['metrics']['integrity_check_time'] = integrity_time
                
        except Exception as e:
            health_report['healthy'] = False
            health_report['issues'].append(f'Health check failed: {str(e)}')
        
        check_duration = time.time() - start_time
        
        # Log database health check
        from app_logging import log_operation
        log_operation('db_health_check',
            healthy=health_report['healthy'],
            issues_count=len(health_report['issues']),
            duration_seconds=check_duration,
            db_size_mb=health_report['metrics'].get('db_size_mb', 0),
            articles_count=health_report['metrics'].get('articles_count', 0)
        )
        
        if not health_report['healthy']:
            from app_logging import log_error
            log_error('db_health_issues', 
                      f"Database health issues: {'; '.join(health_report['issues'])}",
                      issues_count=len(health_report['issues'])
            )
        
        return health_report
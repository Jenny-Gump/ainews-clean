"""
Session Manager for AI News Parser
Manages session lifecycle and prevents duplicate article processing
"""

import uuid
import os
import socket
import sqlite3
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from contextlib import contextmanager
from app_logging import get_logger

logger = get_logger(__name__)


class SessionManager:
    """Manages processing sessions to prevent duplicate article processing"""
    
    def __init__(self, db_path: str = "data/ainews.db"):
        """
        Initialize SessionManager
        
        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        self.session_uuid = None
        self.worker_id = None
        self.worker_id_suffix = ""  # Дополнительный суффикс для worker_id
        self.session_id = None
        self.hostname = socket.gethostname()
        self.pid = os.getpid()
        self._heartbeat_thread = None
        self._stop_heartbeat = threading.Event()
        self._current_article_id = None
        
    @contextmanager
    def get_connection(self):
        """Context manager for database connections"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
            
    def start_session(self) -> str:
        """
        Start a new processing session
        
        Returns:
            session_uuid: Unique identifier for the session
        """
        self.session_uuid = str(uuid.uuid4())
        self.worker_id = f"{self.hostname}_{self.pid}_{self.session_uuid[:8]}{self.worker_id_suffix}"
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pipeline_sessions 
                (session_uuid, worker_id, status, started_at, last_heartbeat, hostname, pid, total_articles, success_count, error_count)
                VALUES (?, ?, 'active', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?, 0, 0, 0)
            """, (self.session_uuid, self.worker_id, self.hostname, self.pid))
            
            self.session_id = cursor.lastrowid
            conn.commit()
            
        # Start heartbeat thread
        self._start_heartbeat()
        
        logger.info(f"Started session {self.session_uuid} with worker {self.worker_id}")
        return self.session_uuid
    
    def claim_article(self, article_id: str) -> bool:
        """
        Atomically claim an article for processing
        
        Args:
            article_id: Article ID to claim
            
        Returns:
            bool: True if successfully claimed, False if already locked
        """
        if not self.session_uuid:
            raise RuntimeError("Session not started. Call start_session() first.")
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # First check if article is already locked
            cursor.execute("""
                SELECT sl.*, a.processing_session_id 
                FROM session_locks sl
                LEFT JOIN articles a ON sl.article_id = a.article_id
                WHERE sl.article_id = ? 
                  AND sl.status = 'locked'
                  AND sl.heartbeat > datetime('now', '-30 minutes')
            """, (article_id,))
            
            existing_lock = cursor.fetchone()
            if existing_lock:
                logger.warning(f"Article {article_id} already locked by session {existing_lock['session_uuid']}")
                return False
            
            # Try to acquire lock atomically
            try:
                # First, delete any released or expired locks for this article
                cursor.execute("""
                    DELETE FROM session_locks 
                    WHERE article_id = ? 
                      AND (status IN ('released', 'expired') 
                           OR heartbeat < datetime('now', '-30 minutes'))
                """, (article_id,))
                
                # Insert lock record
                cursor.execute("""
                    INSERT INTO session_locks 
                    (article_id, session_uuid, worker_id, locked_at, heartbeat, status)
                    VALUES (?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 'locked')
                """, (article_id, self.session_uuid, self.worker_id))
                
                # Update article record
                cursor.execute("""
                    UPDATE articles 
                    SET processing_session_id = ?,
                        processing_started_at = CURRENT_TIMESTAMP,
                        processing_worker_id = ?
                    WHERE article_id = ?
                      AND (processing_session_id IS NULL 
                           OR processing_started_at < datetime('now', '-30 minutes'))
                """, (self.session_uuid, self.worker_id, article_id))
                
                # Update session with current article
                cursor.execute("""
                    UPDATE pipeline_sessions
                    SET current_article_id = ?,
                        last_heartbeat = CURRENT_TIMESTAMP
                    WHERE session_uuid = ?
                """, (article_id, self.session_uuid))
                
                conn.commit()
                
                self._current_article_id = article_id
                logger.info(f"Successfully claimed article {article_id} for session {self.session_uuid}")
                return True
                
            except sqlite3.IntegrityError as e:
                # Article already locked
                conn.rollback()
                logger.warning(f"Failed to claim article {article_id}: {e}")
                return False
                
    def release_article(self, article_id: str, success: bool = True):
        """
        Release a claimed article after processing
        
        Args:
            article_id: Article ID to release
            success: Whether processing was successful
        """
        if not self.session_uuid:
            return
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Update lock record
            cursor.execute("""
                UPDATE session_locks
                SET status = 'released',
                    released_at = CURRENT_TIMESTAMP
                WHERE article_id = ?
                  AND session_uuid = ?
            """, (article_id, self.session_uuid))
            
            # Update article record
            cursor.execute("""
                UPDATE articles
                SET processing_completed_at = CURRENT_TIMESTAMP
                WHERE article_id = ?
                  AND processing_session_id = ?
            """, (article_id, self.session_uuid))
            
            # Update session statistics
            if success:
                cursor.execute("""
                    UPDATE pipeline_sessions
                    SET success_count = success_count + 1,
                        total_articles = total_articles + 1,
                        current_article_id = NULL,
                        last_heartbeat = CURRENT_TIMESTAMP
                    WHERE session_uuid = ?
                """, (self.session_uuid,))
            else:
                cursor.execute("""
                    UPDATE pipeline_sessions
                    SET error_count = error_count + 1,
                        total_articles = total_articles + 1,
                        current_article_id = NULL,
                        last_heartbeat = CURRENT_TIMESTAMP
                    WHERE session_uuid = ?
                """, (self.session_uuid,))
                
            conn.commit()
            
        self._current_article_id = None
        logger.info(f"Released article {article_id} (success={success})")
        
    def update_heartbeat(self):
        """Update session heartbeat to indicate we're still alive"""
        if not self.session_uuid:
            return
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Update session heartbeat
            cursor.execute("""
                UPDATE pipeline_sessions
                SET last_heartbeat = CURRENT_TIMESTAMP
                WHERE session_uuid = ?
            """, (self.session_uuid,))
            
            # Update lock heartbeat if we have an active article
            if self._current_article_id:
                cursor.execute("""
                    UPDATE session_locks
                    SET heartbeat = CURRENT_TIMESTAMP
                    WHERE article_id = ?
                      AND session_uuid = ?
                      AND status = 'locked'
                """, (self._current_article_id, self.session_uuid))
                
            conn.commit()
            
    def _heartbeat_loop(self):
        """Background thread to update heartbeat every 30 seconds"""
        while not self._stop_heartbeat.wait(30):
            try:
                self.update_heartbeat()
            except Exception as e:
                logger.error(f"Error updating heartbeat: {e}")
                
    def _start_heartbeat(self):
        """Start the heartbeat thread"""
        if self._heartbeat_thread is None or not self._heartbeat_thread.is_alive():
            self._stop_heartbeat.clear()
            self._heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
            self._heartbeat_thread.start()
            
    def _stop_heartbeat_thread(self):
        """Stop the heartbeat thread"""
        self._stop_heartbeat.set()
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=5)
            
    def cleanup_stale_sessions(self, timeout_minutes: int = 30):
        """
        Clean up stale sessions and release their locks
        
        Args:
            timeout_minutes: Consider sessions stale after this many minutes
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Mark stale sessions as abandoned
            cursor.execute("""
                UPDATE pipeline_sessions
                SET status = 'abandoned',
                    completed_at = CURRENT_TIMESTAMP
                WHERE status = 'active'
                  AND last_heartbeat < datetime('now', ? || ' minutes')
            """, (-timeout_minutes,))
            
            abandoned_count = cursor.rowcount
            
            # Release locks from stale sessions
            cursor.execute("""
                UPDATE session_locks
                SET status = 'expired'
                WHERE status = 'locked'
                  AND heartbeat < datetime('now', ? || ' minutes')
            """, (-timeout_minutes,))
            
            expired_locks = cursor.rowcount
            
            # Clear processing info from articles with stale sessions
            cursor.execute("""
                UPDATE articles
                SET processing_session_id = NULL,
                    processing_started_at = NULL,
                    processing_worker_id = NULL
                WHERE processing_session_id IN (
                    SELECT session_uuid 
                    FROM pipeline_sessions
                    WHERE status = 'abandoned'
                )
                AND processing_completed_at IS NULL
            """)
            
            cleared_articles = cursor.rowcount
            
            conn.commit()
            
        if abandoned_count > 0 or expired_locks > 0:
            logger.info(f"Cleanup: {abandoned_count} sessions abandoned, {expired_locks} locks expired, {cleared_articles} articles cleared")
            
    def end_session(self):
        """End the current session"""
        if not self.session_uuid:
            return
            
        # Stop heartbeat thread
        self._stop_heartbeat_thread()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Release any active locks
            cursor.execute("""
                UPDATE session_locks
                SET status = 'released',
                    released_at = CURRENT_TIMESTAMP
                WHERE session_uuid = ?
                  AND status = 'locked'
            """, (self.session_uuid,))
            
            # Mark session as completed
            cursor.execute("""
                UPDATE pipeline_sessions
                SET status = 'completed',
                    completed_at = CURRENT_TIMESTAMP,
                    last_heartbeat = CURRENT_TIMESTAMP
                WHERE session_uuid = ?
            """, (self.session_uuid,))
            
            conn.commit()
            
        logger.info(f"Ended session {self.session_uuid}")
        self.session_uuid = None
        self.worker_id = None
        self.session_id = None
        
    def get_next_available_article(self) -> Optional[Dict[str, Any]]:
        """
        Get next available article that isn't locked
        
        Returns:
            Article data dict or None if no articles available
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # First cleanup stale sessions
            self.cleanup_stale_sessions()
            
            # Find next unlocked article with pending content
            cursor.execute("""
                SELECT a.*
                FROM articles a
                LEFT JOIN session_locks sl ON a.article_id = sl.article_id
                WHERE a.content_status = 'pending'
                  AND (a.processing_session_id IS NULL 
                       OR a.processing_started_at < datetime('now', '-30 minutes'))
                  AND (sl.article_id IS NULL 
                       OR sl.status != 'locked'
                       OR sl.heartbeat < datetime('now', '-30 minutes'))
                ORDER BY a.created_at ASC
                LIMIT 1
            """)
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return None
            
    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics for current session"""
        if not self.session_uuid:
            return {}
            
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT *
                FROM pipeline_sessions
                WHERE session_uuid = ?
            """, (self.session_uuid,))
            
            row = cursor.fetchone()
            if row:
                return dict(row)
            return {}
            
    def __enter__(self):
        """Context manager entry"""
        self.start_session()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.end_session()
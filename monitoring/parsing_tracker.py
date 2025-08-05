"""
Parsing Progress Tracker for real-time monitoring of parsing operations
"""
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Callable
from pathlib import Path
import json

try:
    from app_logging import get_logger
except ImportError:
    import logging
    def get_logger(name):
        return logging.getLogger(name)

from .database import MonitoringDatabase
from .process_manager import ProcessStatus


class ParsingProgressTracker:
    """
    Tracks real-time progress of parsing operations
    
    Features:
    - Current source being parsed
    - Article count and parsing speed
    - Progress persistence in database
    - WebSocket broadcast integration
    - Visual pipeline representation data
    - Multi-phase tracking (RSS, Parse, Media)
    """
    
    def __init__(self, monitoring_db: MonitoringDatabase):
        self.logger = get_logger('monitoring.parsing_tracker')
        self.monitoring_db = monitoring_db
        
        # Current parsing state
        self._current_state = {
            'parser_pid': None,
            'status': 'idle',
            'current_source': None,
            'current_source_name': None,
            'total_sources': 0,
            'processed_sources': 0,
            'total_articles': 0,
            'start_time': None,
            'last_update': None,
            'articles_per_minute': 0,
            'estimated_completion': None,
            'pipeline_stage': 'idle',  # idle, fetching, parsing, storing, complete
            'current_phase': 'idle',  # idle, rss_discovery, content_parsing, media_processing
            'phase_progress': {}  # Track progress per phase
        }
        
        # Phase tracking
        self._phase_data = {
            'rss_discovery': {
                'start_time': None,
                'total_feeds': 0,
                'processed_feeds': 0,
                'total_articles_found': 0,
                'new_articles_found': 0,
                'errors': 0,
                'speed': 0  # feeds per minute
            },
            'content_parsing': {
                'start_time': None,
                'total_articles': 0,
                'processed_articles': 0,
                'successful': 0,
                'failed': 0,
                'speed': 0  # articles per minute
            },
            'media_processing': {
                'start_time': None,
                'total_media': 0,
                'processed_media': 0,
                'downloaded': 0,
                'failed': 0,
                'skipped': 0,
                'speed': 0  # files per minute
            }
        }
        
        # Performance tracking
        self._source_timings = {}  # source_id -> start_time
        self._article_counts = {}  # source_id -> count
        self._speed_history = []  # List of (timestamp, articles_per_minute)
        self._max_speed_history = 60  # Keep last 60 measurements
        
        # Phase-specific speed history
        self._phase_speed_history = {
            'rss_discovery': [],
            'content_parsing': [],
            'media_processing': []
        }
        
        # Callbacks for WebSocket updates
        self._update_callbacks: List[Callable[[Dict], None]] = []
        
        # Thread safety
        self._lock = threading.Lock()
        
        # Persistence thread - DISABLED TO PREVENT DB LOCKS
        self._persist_thread = None
        self._persist_interval = 60  # Reduced frequency to prevent locks
        self._running = False
        self._persistence_enabled = False  # Disable database persistence
        
        self.logger.info("ParsingProgressTracker initialized")
    
    def register_update_callback(self, callback: Callable[[Dict], None]):
        """Register callback for progress updates"""
        self._update_callbacks.append(callback)
    
    def start(self):
        """Start the progress tracker"""
        self._running = True
        # DISABLED: persistence thread to prevent database locks
        # self._persist_thread = threading.Thread(target=self._persist_loop, daemon=True)
        # self._persist_thread.start()
        self.logger.info("Progress tracking started (persistence disabled)")
    
    def stop(self):
        """Stop the progress tracker"""
        self._running = False
        if self._persist_thread:
            self._persist_thread.join(timeout=5)
        self._save_to_database()
        self.logger.info("Progress tracking stopped")
    
    def start_parsing(self, parser_pid: int, total_sources: int):
        """Mark the start of a parsing session"""
        with self._lock:
            self._current_state.update({
                'parser_pid': parser_pid,
                'status': 'running',
                'total_sources': total_sources,
                'processed_sources': 0,
                'total_articles': 0,
                'start_time': datetime.now(),
                'last_update': datetime.now(),
                'pipeline_stage': 'initializing',
                'current_phase': 'idle',
                'phase_progress': {}
            })
            
            # Clear previous session data
            self._source_timings.clear()
            self._article_counts.clear()
            self._speed_history.clear()
            
            # Reset phase data
            for phase in self._phase_data:
                self._phase_data[phase] = {
                    'start_time': None,
                    'total_feeds': 0 if phase == 'rss_discovery' else 0,
                    'processed_feeds': 0 if phase == 'rss_discovery' else 0,
                    'total_articles': 0 if phase == 'content_parsing' else 0,
                    'processed_articles': 0 if phase == 'content_parsing' else 0,
                    'total_media': 0 if phase == 'media_processing' else 0,
                    'processed_media': 0 if phase == 'media_processing' else 0,
                    'total_articles_found': 0,
                    'new_articles_found': 0,
                    'successful': 0,
                    'failed': 0,
                    'downloaded': 0,
                    'skipped': 0,
                    'errors': 0,
                    'speed': 0
                }
            
            # Clear phase speed history
            for phase in self._phase_speed_history:
                self._phase_speed_history[phase].clear()
        
        self._broadcast_update()
        self._save_to_database()
        
        self.logger.info(f"Started tracking parser PID {parser_pid} with {total_sources} sources")
    
    def update_source(self, source_id: str, source_name: str = None):
        """Update current source being processed"""
        self.logger.debug(f"DEBUG: update_source called with source_id={source_id}")
        try:
            with self._lock:
                self.logger.debug(f"DEBUG: acquired lock in update_source")
                # Mark previous source as complete
                if self._current_state['current_source'] and self._current_state['current_source'] != source_id:
                    self.logger.debug(f"DEBUG: completing previous source: {self._current_state['current_source']}")
                    self._complete_source(self._current_state['current_source'])
                
                self.logger.debug(f"DEBUG: updating current_state for source_id={source_id}")
                self._current_state['current_source'] = source_id
                self._current_state['current_source_name'] = source_name or source_id
                self._current_state['pipeline_stage'] = 'fetching'
                self._current_state['last_update'] = datetime.now()
                self.logger.debug(f"DEBUG: update_source completed for source_id={source_id}")
        except Exception as e:
            self.logger.error(f"DEBUG ERROR: update_source failed: {e}")
            
            # Track source start time
            self._source_timings[source_id] = datetime.now()
        
        self._broadcast_update()
    
    def update_pipeline_stage(self, stage: str):
        """Update current pipeline stage"""
        self.logger.debug(f"DEBUG: update_pipeline_stage called with stage={stage}")
        valid_stages = ['idle', 'initializing', 'fetching', 'parsing', 'storing', 'complete', 'error']
        if stage not in valid_stages:
            self.logger.warning(f"Invalid pipeline stage: {stage}")
            return
        
        try:
            self.logger.debug(f"DEBUG: attempting to acquire lock in update_pipeline_stage")
            with self._lock:
                self.logger.debug(f"DEBUG: acquired lock in update_pipeline_stage, updating to stage={stage}")
                self._current_state['pipeline_stage'] = stage
                self._current_state['last_update'] = datetime.now()
                self.logger.debug(f"DEBUG: update_pipeline_stage completed for stage={stage}")
        except Exception as e:
            self.logger.error(f"DEBUG ERROR: update_pipeline_stage failed: {e}")
        
        self._broadcast_update()
    
    def add_articles(self, source_id: str, article_count: int):
        """Add articles processed for a source"""
        with self._lock:
            # Update article counts
            if source_id not in self._article_counts:
                self._article_counts[source_id] = 0
            self._article_counts[source_id] += article_count
            self._current_state['total_articles'] += article_count
            self._current_state['last_update'] = datetime.now()
            
            # Update parsing speed
            self._update_parsing_speed()
        
        self._broadcast_update()
    
    def complete_source(self, source_id: str, success: bool = True):
        """Mark a source as completed"""
        with self._lock:
            self._complete_source(source_id)
            self._current_state['pipeline_stage'] = 'idle' if success else 'error'
        
        self._broadcast_update()
        self._save_to_database()
    
    def complete_parsing(self):
        """Mark parsing session as complete"""
        with self._lock:
            self._current_state['status'] = 'complete'
            self._current_state['pipeline_stage'] = 'complete'
            self._current_state['current_source'] = None
            self._current_state['estimated_completion'] = None
            self._current_state['last_update'] = datetime.now()
        
        self._broadcast_update()
        self._save_to_database()
        
        total_time = (datetime.now() - self._current_state['start_time']).total_seconds() / 60
        self.logger.info(
            f"Parsing complete: {self._current_state['processed_sources']} sources, "
            f"{self._current_state['total_articles']} articles in {total_time:.1f} minutes"
        )
    
    def pause_parsing(self):
        """Mark parsing as paused"""
        with self._lock:
            self._current_state['status'] = 'paused'
            self._current_state['pipeline_stage'] = 'paused'
        
        self._broadcast_update()
        self._save_to_database()
    
    def resume_parsing(self):
        """Mark parsing as resumed"""
        with self._lock:
            self._current_state['status'] = 'running'
            self._current_state['pipeline_stage'] = 'fetching'
        
        self._broadcast_update()
    
    def error_parsing(self, error_message: str):
        """Mark parsing as errored"""
        with self._lock:
            self._current_state['status'] = 'error'
            self._current_state['pipeline_stage'] = 'error'
            self._current_state['error_message'] = error_message
        
        self._broadcast_update()
        self._save_to_database()
    
    # Phase-specific methods
    def start_phase(self, phase_name: str, total_items: int = 0):
        """Start a specific phase (rss_discovery, content_parsing, media_processing)"""
        self.logger.debug(f"DEBUG: start_phase called with phase_name={phase_name}, total_items={total_items}")
        if phase_name not in self._phase_data:
            self.logger.warning(f"Invalid phase name: {phase_name}")
            return
        
        try:
            self.logger.debug(f"DEBUG: attempting to acquire lock in start_phase")
            with self._lock:
                self.logger.debug(f"DEBUG: acquired lock in start_phase, setting phase={phase_name}")
                self._current_state['current_phase'] = phase_name
                self._phase_data[phase_name]['start_time'] = datetime.now()
                
                if phase_name == 'rss_discovery':
                    self._phase_data[phase_name]['total_feeds'] = total_items
                elif phase_name == 'content_parsing':
                    self._phase_data[phase_name]['total_articles'] = total_items
                elif phase_name == 'media_processing':
                    self._phase_data[phase_name]['total_media'] = total_items
                self.logger.debug(f"DEBUG: start_phase completed for phase_name={phase_name}")
        except Exception as e:
            self.logger.error(f"DEBUG ERROR: start_phase failed: {e}")
        
        self._broadcast_update()
        self.logger.info(f"Started phase: {phase_name} with {total_items} items")
    
    def update_phase_progress(self, phase_name: str, progress_data: Dict[str, Any]):
        """Update progress for a specific phase"""
        if phase_name not in self._phase_data:
            return
        
        with self._lock:
            phase = self._phase_data[phase_name]
            
            # Update phase-specific fields
            for key, value in progress_data.items():
                if key in phase:
                    if isinstance(value, (int, float)) and isinstance(phase[key], (int, float)):
                        # For numeric fields, increment if it's a count
                        if key in ['processed_feeds', 'processed_articles', 'processed_media', 
                                  'successful', 'failed', 'downloaded', 'skipped', 'errors',
                                  'total_articles_found', 'new_articles_found']:
                            phase[key] += value
                        else:
                            phase[key] = value
                    else:
                        phase[key] = value
            
            # Update speed calculation
            if phase['start_time']:
                elapsed_minutes = (datetime.now() - phase['start_time']).total_seconds() / 60
                if elapsed_minutes > 0:
                    if phase_name == 'rss_discovery' and phase['processed_feeds'] > 0:
                        phase['speed'] = phase['processed_feeds'] / elapsed_minutes
                    elif phase_name == 'content_parsing' and phase['processed_articles'] > 0:
                        phase['speed'] = phase['processed_articles'] / elapsed_minutes
                    elif phase_name == 'media_processing' and phase['processed_media'] > 0:
                        phase['speed'] = phase['processed_media'] / elapsed_minutes
                    
                    # Update speed history
                    speed_history = self._phase_speed_history[phase_name]
                    speed_history.append((datetime.now(), phase['speed']))
                    if len(speed_history) > self._max_speed_history:
                        speed_history.pop(0)
            
            # Update overall progress
            self._update_phase_progress()
        
        self._broadcast_update()
    
    def complete_phase(self, phase_name: str):
        """Mark a phase as complete"""
        if phase_name not in self._phase_data:
            return
        
        with self._lock:
            phase = self._phase_data[phase_name]
            if phase['start_time']:
                duration = (datetime.now() - phase['start_time']).total_seconds() / 60
                self.logger.info(
                    f"Phase {phase_name} completed in {duration:.1f} minutes. "
                    f"Processed: {phase.get('processed_feeds', 0) or phase.get('processed_articles', 0) or phase.get('processed_media', 0)} items"
                )
            
            # Move to next phase or complete
            if phase_name == 'rss_discovery':
                self._current_state['current_phase'] = 'content_parsing'
            elif phase_name == 'content_parsing':
                self._current_state['current_phase'] = 'media_processing'
            else:
                self._current_state['current_phase'] = 'complete'
        
        self._broadcast_update()
    
    def get_phase_stats(self, phase_name: str = None) -> Dict[str, Any]:
        """Get statistics for a specific phase or all phases"""
        with self._lock:
            if phase_name:
                if phase_name not in self._phase_data:
                    return {}
                return self._format_phase_stats(phase_name, self._phase_data[phase_name])
            else:
                stats = {}
                for phase, data in self._phase_data.items():
                    stats[phase] = self._format_phase_stats(phase, data)
                return stats
    
    def _format_phase_stats(self, phase_name: str, phase_data: Dict) -> Dict[str, Any]:
        """Format phase statistics for output"""
        stats = phase_data.copy()
        
        # Calculate progress percentage
        if phase_name == 'rss_discovery' and phase_data['total_feeds'] > 0:
            stats['progress_percent'] = (phase_data['processed_feeds'] / phase_data['total_feeds']) * 100
        elif phase_name == 'content_parsing' and phase_data['total_articles'] > 0:
            stats['progress_percent'] = (phase_data['processed_articles'] / phase_data['total_articles']) * 100
        elif phase_name == 'media_processing' and phase_data['total_media'] > 0:
            stats['progress_percent'] = (phase_data['processed_media'] / phase_data['total_media']) * 100
        else:
            stats['progress_percent'] = 0
        
        # Calculate elapsed time
        if phase_data['start_time']:
            stats['elapsed_minutes'] = (datetime.now() - phase_data['start_time']).total_seconds() / 60
            
            # Estimate completion
            if stats['progress_percent'] > 0 and stats['progress_percent'] < 100:
                total_estimated = stats['elapsed_minutes'] / (stats['progress_percent'] / 100)
                stats['eta_minutes'] = total_estimated - stats['elapsed_minutes']
                stats['eta'] = (datetime.now() + timedelta(minutes=stats['eta_minutes'])).isoformat()
        
        # Get speed history for chart
        if phase_name in self._phase_speed_history:
            stats['speed_history'] = [
                {'timestamp': ts.isoformat(), 'speed': speed}
                for ts, speed in self._phase_speed_history[phase_name][-20:]  # Last 20 points
            ]
        
        return stats
    
    def _update_phase_progress(self):
        """Update overall progress based on phase data"""
        # Calculate total progress across all phases
        total_progress = 0
        phase_weights = {
            'rss_discovery': 0.3,  # 30%
            'content_parsing': 0.5,  # 50%
            'media_processing': 0.2  # 20%
        }
        
        for phase, weight in phase_weights.items():
            phase_data = self._phase_data[phase]
            phase_progress = 0
            
            if phase == 'rss_discovery' and phase_data['total_feeds'] > 0:
                phase_progress = (phase_data['processed_feeds'] / phase_data['total_feeds']) * 100
            elif phase == 'content_parsing' and phase_data['total_articles'] > 0:
                phase_progress = (phase_data['processed_articles'] / phase_data['total_articles']) * 100
            elif phase == 'media_processing' and phase_data['total_media'] > 0:
                phase_progress = (phase_data['processed_media'] / phase_data['total_media']) * 100
            
            total_progress += phase_progress * weight
        
        self._current_state['phase_progress'] = {
            'overall': total_progress,
            'rss_discovery': self._phase_data['rss_discovery'].get('progress_percent', 0),
            'content_parsing': self._phase_data['content_parsing'].get('progress_percent', 0),
            'media_processing': self._phase_data['media_processing'].get('progress_percent', 0)
        }
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current parsing state"""
        with self._lock:
            state = self._current_state.copy()
            
            # Add calculated fields
            if state['start_time']:
                elapsed = (datetime.now() - state['start_time']).total_seconds()
                state['elapsed_minutes'] = elapsed / 60
                
                # Progress percentage
                if state['total_sources'] > 0:
                    state['progress_percent'] = (state['processed_sources'] / state['total_sources']) * 100
                else:
                    state['progress_percent'] = 0
                
                # Pipeline visualization data
                state['pipeline_data'] = self._get_pipeline_visualization()
            
            # Add phase data - БЕЗ дополнительной блокировки для избежания deadlock
            stats = {}
            for phase, data in self._phase_data.items():
                stats[phase] = self._format_phase_stats(phase, data)
            state['phases'] = stats
            
            # Add current phase info
            current_phase = state.get('current_phase', 'idle')
            if current_phase in self._phase_data:
                state['current_phase_data'] = self._format_phase_stats(current_phase, self._phase_data[current_phase])
            
            return state
    
    def get_source_stats(self) -> Dict[str, Any]:
        """Get statistics for all processed sources"""
        with self._lock:
            stats = []
            for source_id, article_count in self._article_counts.items():
                if source_id in self._source_timings:
                    duration = (datetime.now() - self._source_timings[source_id]).total_seconds()
                    stats.append({
                        'source_id': source_id,
                        'articles': article_count,
                        'duration_seconds': duration,
                        'articles_per_minute': (article_count / duration * 60) if duration > 0 else 0
                    })
            
            return {
                'sources': stats,
                'total_sources': len(stats),
                'total_articles': sum(s['articles'] for s in stats),
                'avg_articles_per_source': sum(s['articles'] for s in stats) / len(stats) if stats else 0
            }
    
    def _complete_source(self, source_id: str):
        """Internal method to mark a source as complete"""
        self._current_state['processed_sources'] += 1
        
        # Calculate estimated completion time
        if self._current_state['processed_sources'] > 0 and self._current_state['total_sources'] > 0:
            elapsed = (datetime.now() - self._current_state['start_time']).total_seconds()
            avg_time_per_source = elapsed / self._current_state['processed_sources']
            remaining_sources = self._current_state['total_sources'] - self._current_state['processed_sources']
            estimated_remaining = avg_time_per_source * remaining_sources
            self._current_state['estimated_completion'] = datetime.now() + timedelta(seconds=estimated_remaining)
    
    def _update_parsing_speed(self):
        """Update parsing speed calculation"""
        if not self._current_state['start_time']:
            return
        
        elapsed_minutes = (datetime.now() - self._current_state['start_time']).total_seconds() / 60
        if elapsed_minutes > 0:
            speed = self._current_state['total_articles'] / elapsed_minutes
            self._current_state['articles_per_minute'] = speed
            
            # Update speed history
            self._speed_history.append((datetime.now(), speed))
            if len(self._speed_history) > self._max_speed_history:
                self._speed_history.pop(0)
    
    def _get_pipeline_visualization(self) -> Dict[str, Any]:
        """Generate pipeline visualization data"""
        current_phase = self._current_state.get('current_phase', 'idle')
        
        pipeline_data = {
            'stages': [],
            'phases': []
        }
        
        # Phase-level pipeline
        phase_order = ['rss_discovery', 'content_parsing', 'media_processing']
        for phase in phase_order:
            phase_data = self._phase_data[phase]
            status = 'pending'
            
            if current_phase == phase:
                status = 'active'
            elif phase_order.index(phase) < phase_order.index(current_phase) if current_phase in phase_order else False:
                status = 'complete'
            
            phase_info = {
                'name': phase.replace('_', ' ').title(),
                'status': status,
                'progress': 0
            }
            
            # Add progress for active or completed phases
            if phase == 'rss_discovery' and phase_data['total_feeds'] > 0:
                phase_info['progress'] = (phase_data['processed_feeds'] / phase_data['total_feeds']) * 100
                phase_info['count'] = f"{phase_data['processed_feeds']}/{phase_data['total_feeds']}"
                phase_info['speed'] = f"{phase_data['speed']:.1f} feeds/min" if phase_data['speed'] > 0 else "calculating..."
            elif phase == 'content_parsing' and phase_data['total_articles'] > 0:
                phase_info['progress'] = (phase_data['processed_articles'] / phase_data['total_articles']) * 100
                phase_info['count'] = f"{phase_data['processed_articles']}/{phase_data['total_articles']}"
                phase_info['speed'] = f"{phase_data['speed']:.1f} art/min" if phase_data['speed'] > 0 else "calculating..."
            elif phase == 'media_processing' and phase_data['total_media'] > 0:
                phase_info['progress'] = (phase_data['processed_media'] / phase_data['total_media']) * 100
                phase_info['count'] = f"{phase_data['processed_media']}/{phase_data['total_media']}"
                phase_info['speed'] = f"{phase_data['speed']:.1f} files/min" if phase_data['speed'] > 0 else "calculating..."
            
            pipeline_data['phases'].append(phase_info)
        
        # Stage-level pipeline (for current phase)
        stages = ['fetching', 'parsing', 'storing']
        current_stage = self._current_state['pipeline_stage']
        
        for stage in stages:
            if current_stage == 'idle' or current_stage == 'initializing':
                status = 'pending'
            elif stage == current_stage:
                status = 'active'
            elif stages.index(stage) < stages.index(current_stage) if current_stage in stages else False:
                status = 'complete'
            else:
                status = 'pending'
            
            pipeline_data['stages'].append({
                'name': stage.capitalize(),
                'status': status
            })
        
        # Add current source info
        if self._current_state['current_source']:
            pipeline_data['current_item'] = {
                'id': self._current_state['current_source'],
                'name': self._current_state['current_source_name'],
                'articles': self._article_counts.get(self._current_state['current_source'], 0),
                'phase': current_phase
            }
        
        return pipeline_data
    
    def _broadcast_update(self):
        """Broadcast update to all registered callbacks"""
        state = self.get_current_state()
        for callback in self._update_callbacks:
            try:
                callback(state)
            except Exception as e:
                self.logger.error(f"Error in update callback: {e}")
    
    def _persist_loop(self):
        """Background thread to persist state to database"""
        while self._running:
            try:
                time.sleep(self._persist_interval)
                self._save_to_database()
            except Exception as e:
                self.logger.error(f"Error in persist loop: {e}")
    
    def _save_to_database(self):
        """Save current progress to database"""
        # DISABLED: database persistence to prevent locks during parsing
        if not self._persistence_enabled:
            return
            
        try:
            with self._lock:
                if not self._current_state['parser_pid']:
                    return
                
                state = self._current_state.copy()
            
            with sqlite3.connect(self.monitoring_db.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if record exists
                cursor.execute(
                    "SELECT id FROM parsing_progress WHERE parser_pid = ? ORDER BY timestamp DESC LIMIT 1",
                    (state['parser_pid'],)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing record
                    cursor.execute("""
                        UPDATE parsing_progress SET
                            status = ?,
                            current_source = ?,
                            total_sources = ?,
                            processed_sources = ?,
                            total_articles = ?,
                            progress_percent = ?,
                            estimated_completion = ?,
                            last_update = ?
                        WHERE id = ?
                    """, (
                        state['status'],
                        state['current_source'],
                        state['total_sources'],
                        state['processed_sources'],
                        state['total_articles'],
                        (state['processed_sources'] / state['total_sources'] * 100) if state['total_sources'] > 0 else 0,
                        state.get('estimated_completion'),
                        datetime.now(),
                        existing[0]
                    ))
                else:
                    # Insert new record
                    cursor.execute("""
                        INSERT INTO parsing_progress
                        (parser_pid, status, current_source, total_sources, processed_sources,
                         total_articles, progress_percent, estimated_completion, last_update)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        state['parser_pid'],
                        state['status'],
                        state['current_source'],
                        state['total_sources'],
                        state['processed_sources'],
                        state['total_articles'],
                        (state['processed_sources'] / state['total_sources'] * 100) if state['total_sources'] > 0 else 0,
                        state.get('estimated_completion'),
                        datetime.now()
                    ))
                
                conn.commit()
                
        except Exception as e:
            self.logger.error(f"Error saving progress to database: {e}")
    
    def load_from_database(self, parser_pid: int) -> bool:
        """Load progress state from database for a given PID"""
        try:
            with sqlite3.connect(self.monitoring_db.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT status, current_source, total_sources, processed_sources,
                           total_articles, estimated_completion, timestamp, last_update
                    FROM parsing_progress
                    WHERE parser_pid = ?
                    ORDER BY timestamp DESC
                    LIMIT 1
                """, (parser_pid,))
                
                row = cursor.fetchone()
                if row:
                    with self._lock:
                        self._current_state.update({
                            'parser_pid': parser_pid,
                            'status': row[0],
                            'current_source': row[1],
                            'total_sources': row[2],
                            'processed_sources': row[3],
                            'total_articles': row[4],
                            'estimated_completion': row[5],
                            'start_time': row[6],
                            'last_update': row[7]
                        })
                    
                    self.logger.info(f"Loaded progress state for PID {parser_pid}")
                    return True
                
        except Exception as e:
            self.logger.error(f"Error loading progress from database: {e}")
        
        return False
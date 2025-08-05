"""
Real-time log reader for monitoring system
"""
import asyncio
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional, Set, Dict, Any
import aiofiles
from asyncio import Queue

try:
    from app_logging import get_logger
except ImportError:
    # Fallback logging if app_logging is not available
    import logging
    def get_logger(name):
        return logging.getLogger(name)


class LogReader:
    """Reads log files and streams them in real-time"""
    
    def __init__(self, log_dir: str = "../logs"):
        self.log_dir = Path(log_dir)
        self.readers: Dict[str, asyncio.Task] = {}
        self.queue: Queue = Queue(maxsize=1000)
        self.running = False
        self.logger = get_logger('monitoring.log_reader')
        self._shutdown_event = asyncio.Event()
        
        # Log files to monitor
        self.log_files = {
            'main': 'ai_news_parser.log',
            'parsing': 'parsing.log',
            'api': 'api.log',
            'database': 'database.log',
            'validation': 'validation.log',
            'errors': 'errors.log'
        }
        
        # Track file positions
        self.file_positions = {}
        self._load_positions()
    
    def _load_positions(self):
        """Load saved file positions"""
        position_file = self.log_dir / '.log_positions.json'
        if position_file.exists():
            try:
                with open(position_file, 'r') as f:
                    self.file_positions = json.load(f)
            except Exception:
                self.file_positions = {}
    
    def _save_positions(self):
        """Save current file positions"""
        position_file = self.log_dir / '.log_positions.json'
        try:
            with open(position_file, 'w') as f:
                json.dump(self.file_positions, f)
        except Exception:
            pass
    
    async def start(self):
        """Start monitoring log files"""
        self.running = True
        
        # Start a reader for each log file
        for name, filename in self.log_files.items():
            filepath = self.log_dir / filename
            if filepath.exists():
                task = asyncio.create_task(self._read_log_file(name, filepath))
                self.readers[name] = task
    
    async def stop(self):
        """Stop monitoring with proper cleanup"""
        self.logger.info("Stopping log reader...")
        self.running = False
        self._shutdown_event.set()
        
        if not self.readers:
            self.logger.info("No active readers to stop")
            return
        
        # Cancel all reader tasks with timeout
        self.logger.info(f"Cancelling {len(self.readers)} reader tasks...")
        for name, task in self.readers.items():
            if not task.done():
                self.logger.debug(f"Cancelling reader task: {name}")
                task.cancel()
        
        # Wait for tasks to complete with timeout
        try:
            await asyncio.wait_for(
                asyncio.gather(*self.readers.values(), return_exceptions=True),
                timeout=5.0
            )
            self.logger.info("All reader tasks stopped successfully")
        except asyncio.TimeoutError:
            self.logger.warning("Some reader tasks did not stop within timeout")
            # Force completion by gathering with return_exceptions=True
            await asyncio.gather(*self.readers.values(), return_exceptions=True)
        
        self.readers.clear()
        
        # Save positions
        try:
            self._save_positions()
            self.logger.info("Log positions saved")
        except Exception as e:
            self.logger.error(f"Failed to save log positions: {e}")
    
    async def _read_log_file(self, name: str, filepath: Path):
        """Read a single log file continuously with proper cancellation handling"""
        position = self.file_positions.get(str(filepath), 0)
        
        try:
            while self.running and not self._shutdown_event.is_set():
                try:
                    # Check if file exists and has new content
                    if not filepath.exists():
                        try:
                            await asyncio.wait_for(asyncio.sleep(1), timeout=1.0)
                        except asyncio.TimeoutError:
                            pass
                        continue
                    
                    file_size = filepath.stat().st_size
                    if file_size < position:
                        # File was truncated/rotated
                        position = 0
                    
                    if file_size == position:
                        # No new content - use short sleep with timeout
                        try:
                            await asyncio.wait_for(asyncio.sleep(0.5), timeout=0.5)
                        except asyncio.TimeoutError:
                            pass
                        continue
                    
                    # Read new content with proper exception handling
                    try:
                        async with aiofiles.open(filepath, 'r') as f:
                            await f.seek(position)
                            
                            while self.running and not self._shutdown_event.is_set():
                                line = await f.readline()
                                if not line:
                                    break
                                
                                # Update position
                                position = await f.tell()
                                self.file_positions[str(filepath)] = position
                                
                                # Parse JSON log entry
                                try:
                                    log_entry = json.loads(line.strip())
                                    log_entry['log_file'] = name
                                    
                                    # Add to queue (non-blocking)
                                    try:
                                        self.queue.put_nowait(log_entry)
                                    except asyncio.QueueFull:
                                        # Remove oldest entry if queue is full
                                        try:
                                            self.queue.get_nowait()
                                            self.queue.put_nowait(log_entry)
                                        except:
                                            pass
                                            
                                except json.JSONDecodeError:
                                    # Skip non-JSON lines
                                    pass
                    
                    except (OSError, IOError) as e:
                        self.logger.warning(f"File I/O error reading {filepath}: {e}")
                        try:
                            await asyncio.wait_for(asyncio.sleep(1), timeout=1.0)
                        except asyncio.TimeoutError:
                            pass
                    
                except Exception as e:
                    self.logger.error(f"Unexpected error reading log file {filepath}: {e}")
                    try:
                        await asyncio.wait_for(asyncio.sleep(1), timeout=1.0)
                    except asyncio.TimeoutError:
                        pass
        
        except asyncio.CancelledError:
            self.logger.info(f"Log reader task for {name} was cancelled")
        except Exception as e:
            self.logger.error(f"Fatal error in log reader for {name}: {e}")
        finally:
            # Ensure position is saved on exit
            self.file_positions[str(filepath)] = position
            self.logger.debug(f"Log reader for {name} finished, final position: {position}")
    
    async def get_log_entry(self) -> Optional[Dict[str, Any]]:
        """Get next log entry from queue with proper cancellation handling"""
        try:
            # Use wait_for with timeout to allow for clean shutdown
            return await asyncio.wait_for(self.queue.get(), timeout=1.0)
        except asyncio.TimeoutError:
            # Return None on timeout to allow checking for shutdown
            return None
        except asyncio.CancelledError:
            self.logger.debug("Log entry retrieval was cancelled")
            return None
        except Exception as e:
            self.logger.error(f"Error getting log entry: {e}")
            return None


# Global log reader instance
log_reader: Optional[LogReader] = None


def initialize_log_reader(log_dir: str = "../logs") -> LogReader:
    """Initialize global log reader"""
    global log_reader
    if log_reader is None:
        log_reader = LogReader(log_dir)
    return log_reader


def get_log_reader() -> Optional[LogReader]:
    """Get global log reader instance"""
    return log_reader


async def cleanup_log_reader():
    """Clean up global log reader instance"""
    global log_reader
    if log_reader is not None:
        await log_reader.stop()
        log_reader = None
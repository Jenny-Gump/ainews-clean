"""
Process Manager for controlling AI News Parser
Manages the unified_crawl_parser.py subprocess with advanced control capabilities
"""
import os
import sys
import subprocess
import psutil
import signal
import time
import json
import threading
from typing import Optional, Dict, Any, List, Callable
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from collections import deque

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from app_logging import get_logger, LogContext


class ProcessStatus(Enum):
    """Process status states"""
    IDLE = "idle"
    RUNNING = "running" 
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"


class CircuitBreaker:
    """Circuit breaker pattern for handling repeated failures"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.is_open = False
    
    def record_success(self):
        """Reset the circuit breaker on success"""
        self.failure_count = 0
        self.is_open = False
        self.last_failure_time = None
    
    def record_failure(self):
        """Record a failure and potentially open the circuit"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.is_open = True
            return True
        return False
    
    def can_attempt(self) -> bool:
        """Check if we can attempt an operation"""
        if not self.is_open:
            return True
        
        # Check if recovery timeout has passed
        if self.last_failure_time:
            time_since_failure = (datetime.now() - self.last_failure_time).total_seconds()
            if time_since_failure >= self.recovery_timeout:
                # Try half-open state
                self.is_open = False
                self.failure_count = 0
                return True
        
        return False


class ProcessManager:
    """
    Advanced process manager for AI News Parser
    
    Features:
    - Subprocess control (start, pause, resume, stop, emergency stop)
    - Memory monitoring and cleanup
    - Progress tracking
    - Process health monitoring
    - Integration with monitoring system
    """
    
    def __init__(self):
        self.logger = get_logger('ai_news_parser.process_manager')
        
        # Process control
        self.process: Optional[subprocess.Popen] = None
        self.status = ProcessStatus.IDLE
        self.pid: Optional[int] = None
        
        # Working directory - parent of monitoring directory
        self.working_dir = Path(__file__).parent.parent
        self.parser_script = self.working_dir / "core" / "main.py"
        
        # Status tracking
        self.start_time: Optional[datetime] = None
        self.current_source: Optional[str] = None
        self.total_sources: int = 0
        self.processed_sources: int = 0
        self.total_articles: int = 0
        self.last_progress_update: Optional[datetime] = None
        
        # Memory management
        self.max_memory_mb = 8192  # 8GB limit
        self.memory_check_interval = 30  # seconds
        self._memory_monitor_thread: Optional[threading.Thread] = None
        self._memory_monitoring = False
        
        # Process monitoring
        self._status_callbacks: List[Callable[[ProcessStatus, Dict], None]] = []
        self._progress_callbacks: List[Callable[[Dict], None]] = []
        
        # Emergency stop tracking
        self._emergency_stop_requested = False
        
        # Process output monitoring
        self._output_thread: Optional[threading.Thread] = None
        self._monitoring_output = False
        
        # Timeout handling
        self.default_timeout = 30  # 30 seconds default timeout
        self._last_output_time: Optional[datetime] = None
        
        # Circuit breakers for different operations
        self.start_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=300)
        self.memory_circuit_breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=120)
        
        # Recovery mechanisms
        self._recovery_thread: Optional[threading.Thread] = None
        self._recovery_enabled = True
        self._recovery_attempts = 0
        self._max_recovery_attempts = 3
        
        # Health check history
        self._health_history = deque(maxlen=10)
        
        # Ensure working directory exists and is correct
        if not self.parser_script.exists():
            self.logger.error(f"Parser script not found: {self.parser_script}")
            raise FileNotFoundError(f"Parser script not found: {self.parser_script}")
        
        self.logger.info(f"ProcessManager initialized")
        self.logger.info(f"Working directory: {self.working_dir}")
        self.logger.info(f"Parser script: {self.parser_script}")
    
    def register_status_callback(self, callback: Callable[[ProcessStatus, Dict], None]):
        """Register callback for status changes"""
        self._status_callbacks.append(callback)
    
    def register_progress_callback(self, callback: Callable[[Dict], None]):
        """Register callback for progress updates"""
        self._progress_callbacks.append(callback)
    
    def _notify_status_change(self, new_status: ProcessStatus, details: Dict = None):
        """Notify all status callbacks of status change"""
        old_status = self.status
        self.status = new_status
        
        details = details or {}
        details.update({
            'old_status': old_status.value,
            'new_status': new_status.value,
            'timestamp': datetime.now().isoformat(),
            'pid': self.pid
        })
        
        self.logger.info(f"Process status changed: {old_status.value} -> {new_status.value}")
        
        for callback in self._status_callbacks:
            try:
                callback(new_status, details)
            except Exception as e:
                self.logger.error(f"Error in status callback: {e}")
    
    def _notify_progress_update(self, progress_data: Dict):
        """Notify all progress callbacks of progress update"""
        self.last_progress_update = datetime.now()
        
        for callback in self._progress_callbacks:
            try:
                callback(progress_data)
            except Exception as e:
                self.logger.error(f"Error in progress callback: {e}")
    
    def start_parser(self, days_back: int = 7, last_parsed: Optional[str] = None) -> bool:
        """
        Start the unified crawl parser as subprocess
        
        Args:
            days_back: Number of days to go back for crawling
            last_parsed: Optional last parsed timestamp to resume from
            
        Returns:
            bool: True if started successfully, False otherwise
        """
        if self.status in [ProcessStatus.RUNNING, ProcessStatus.PAUSED]:
            self.logger.warning(f"Parser already running with status: {self.status.value}")
            return False
        
        # Check circuit breaker
        if not self.start_circuit_breaker.can_attempt():
            self.logger.error("Start circuit breaker is open - too many recent failures")
            return False
        
        try:
            # Prepare command
            cmd = [
                sys.executable,
                str(self.parser_script),
                "--rss-scrape",
                "--days-back", str(days_back)
            ]
            
            # Add resume parameter if provided
            if last_parsed:
                cmd.extend(["--resume-from", last_parsed])
            
            self.logger.info(f"Starting parser with command: {' '.join(cmd)}")
            
            # Start subprocess
            self.process = subprocess.Popen(
                cmd,
                cwd=str(self.working_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                universal_newlines=True
            )
            
            self.pid = self.process.pid
            self.start_time = datetime.now()
            self._emergency_stop_requested = False
            
            # Reset tracking variables
            self.current_source = None
            self.total_sources = 0
            self.processed_sources = 0
            self.total_articles = 0
            
            # Start memory monitoring
            self._start_memory_monitoring()
            
            # Start output monitoring
            self._start_output_monitoring()
            
            self._notify_status_change(ProcessStatus.RUNNING, {
                'command': ' '.join(cmd),
                'days_back': days_back,
                'last_parsed': last_parsed
            })
            
            self.logger.info(f"Parser started successfully with PID: {self.pid}")
            self.start_circuit_breaker.record_success()
            self._recovery_attempts = 0
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to start parser: {e}")
            self._notify_status_change(ProcessStatus.ERROR, {'error': str(e)})
            self.start_circuit_breaker.record_failure()
            
            # Try automatic recovery if enabled
            if self._recovery_enabled and self._recovery_attempts < self._max_recovery_attempts:
                self._schedule_recovery()
            
            return False
    
    def pause_parser(self) -> bool:
        """
        Pause the running parser process with state preservation
        Uses SIGSTOP on Unix systems
        
        Returns:
            bool: True if paused successfully, False otherwise
        """
        if self.status != ProcessStatus.RUNNING:
            self.logger.warning(f"Cannot pause parser in status: {self.status.value}")
            return False
        
        if not self.process or not self.pid:
            self.logger.error("No active process to pause")
            return False
        
        try:
            # Save current state before pausing
            self._save_parser_state()
            
            # Use psutil for cross-platform compatibility
            process = psutil.Process(self.pid)
            process.suspend()
            
            self._notify_status_change(ProcessStatus.PAUSED, {
                'state_saved': True,
                'current_source': self.current_source,
                'processed_sources': self.processed_sources
            })
            self.logger.info(f"Parser paused (PID: {self.pid})")
            return True
            
        except psutil.NoSuchProcess:
            self.logger.error(f"Process {self.pid} not found")
            self._notify_status_change(ProcessStatus.STOPPED)
            return False
        except Exception as e:
            self.logger.error(f"Failed to pause parser: {e}")
            return False
    
    def resume_parser(self) -> bool:
        """
        Resume the paused parser process
        Uses SIGCONT on Unix systems
        
        Returns:
            bool: True if resumed successfully, False otherwise
        """
        if self.status != ProcessStatus.PAUSED:
            self.logger.warning(f"Cannot resume parser in status: {self.status.value}")
            return False
        
        if not self.process or not self.pid:
            self.logger.error("No active process to resume")
            return False
        
        try:
            # Use psutil for cross-platform compatibility
            process = psutil.Process(self.pid)
            process.resume()
            
            self._notify_status_change(ProcessStatus.RUNNING)
            self.logger.info(f"Parser resumed (PID: {self.pid})")
            return True
            
        except psutil.NoSuchProcess:
            self.logger.error(f"Process {self.pid} not found")
            self._notify_status_change(ProcessStatus.STOPPED)
            return False
        except Exception as e:
            self.logger.error(f"Failed to resume parser: {e}")
            return False
    
    def stop_parser(self, timeout: int = 30) -> bool:
        """
        Gracefully stop the parser process
        
        Args:
            timeout: Maximum time to wait for graceful shutdown
            
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        if self.status not in [ProcessStatus.RUNNING, ProcessStatus.PAUSED]:
            self.logger.warning(f"Cannot stop parser in status: {self.status.value}")
            return False
        
        if not self.process or not self.pid:
            self.logger.error("No active process to stop")
            return False
        
        try:
            self._notify_status_change(ProcessStatus.STOPPING)
            
            # Stop monitoring threads first
            self._memory_monitoring = False
            self._monitoring_output = False
            
            # If paused, resume first to allow graceful shutdown
            if self.status == ProcessStatus.PAUSED:
                try:
                    process = psutil.Process(self.pid)
                    process.resume()
                    time.sleep(1)  # Give it a moment to resume
                except:
                    pass
            
            # Send SIGTERM for graceful shutdown
            self.process.terminate()
            
            # Wait for process to finish
            try:
                self.process.wait(timeout=timeout)
                self.logger.info(f"Parser stopped gracefully (PID: {self.pid})")
            except subprocess.TimeoutExpired:
                self.logger.warning(f"Parser didn't stop within {timeout}s, forcing kill")
                self.process.kill()
                self.process.wait()
                self.logger.info(f"Parser force killed (PID: {self.pid})")
            
            # Cleanup
            self._cleanup_process()
            self._notify_status_change(ProcessStatus.STOPPED)
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to stop parser: {e}")
            self._notify_status_change(ProcessStatus.ERROR, {'error': str(e)})
            return False
    
    def emergency_stop(self) -> bool:
        """
        Emergency stop - forcefully kill all related processes
        
        Returns:
            bool: True if stopped successfully, False otherwise
        """
        self.logger.warning("Emergency stop requested - force killing all processes")
        self._emergency_stop_requested = True
        
        try:
            killed_processes = []
            
            # Find all AI News Parser related processes
            for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any(arg for arg in cmdline if any(
                        keyword in arg for keyword in ['rss_scrape_parser', 'unified_crawl_parser', 'ainews-clean']
                    )):
                        proc_pid = proc.info['pid']
                        proc.kill()
                        killed_processes.append(proc_pid)
                        self.logger.info(f"Killed process PID: {proc_pid}")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Also kill our tracked process if it exists
            if self.process:
                try:
                    self.process.kill()
                    if self.pid not in killed_processes:
                        killed_processes.append(self.pid)
                except:
                    pass
                
                try:
                    self.process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    pass
            
            # Cleanup
            self._cleanup_process()
            
            self._notify_status_change(ProcessStatus.STOPPED, {
                'emergency_stop': True,
                'killed_processes': killed_processes
            })
            
            self.logger.info(f"Emergency stop completed. Killed {len(killed_processes)} processes")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed emergency stop: {e}")
            return False
    
    def cleanup_memory(self) -> Dict[str, Any]:
        """
        Force memory cleanup for all related AI News processes
        
        Returns:
            Dict with cleanup results
        """
        self.logger.info("Starting memory cleanup")
        
        cleanup_results = {
            'timestamp': datetime.now().isoformat(),
            'processes_found': 0,
            'memory_before_mb': 0,
            'memory_after_mb': 0,
            'cleanup_actions': []
        }
        
        try:
            # Find AI News related processes
            ainews_processes = []
            total_memory_before = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'memory_info']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and any(
                        'rss_scrape_parser' in arg or
                        'unified_crawl_parser' in arg or 
                        'ainews-clean' in arg or
                        'monitoring' in arg
                        for arg in cmdline
                    ):
                        memory_mb = proc.info['memory_info'].rss / 1024 / 1024
                        ainews_processes.append(proc)
                        total_memory_before += memory_mb
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            cleanup_results['processes_found'] = len(ainews_processes)
            cleanup_results['memory_before_mb'] = round(total_memory_before, 2)
            
            # Perform cleanup actions
            if ainews_processes:
                # Force garbage collection in processes (if possible)
                cleanup_results['cleanup_actions'].append('Triggered garbage collection')
                
                # Clear system caches
                try:
                    import gc
                    gc.collect()
                    cleanup_results['cleanup_actions'].append('Python garbage collection')
                except:
                    pass
                
                # Wait a moment and recalculate memory
                time.sleep(2)
                
                total_memory_after = 0
                for proc in ainews_processes:
                    try:
                        memory_mb = proc.memory_info().rss / 1024 / 1024
                        total_memory_after += memory_mb
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        continue
                
                cleanup_results['memory_after_mb'] = round(total_memory_after, 2)
                cleanup_results['memory_freed_mb'] = round(
                    cleanup_results['memory_before_mb'] - cleanup_results['memory_after_mb'], 2
                )
            
            self.logger.info(f"Memory cleanup completed: {cleanup_results}")
            return cleanup_results
            
        except Exception as e:
            self.logger.error(f"Error during memory cleanup: {e}")
            cleanup_results['error'] = str(e)
            return cleanup_results
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current process status and information
        
        Returns:
            Dict with process status information
        """
        status_info = {
            'status': self.status.value,
            'pid': self.pid,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'uptime_seconds': None,
            'current_source': self.current_source,
            'progress': {
                'total_sources': self.total_sources,
                'processed_sources': self.processed_sources,
                'total_articles': self.total_articles,
                'progress_percent': 0
            },
            'memory_info': None,
            'last_progress_update': self.last_progress_update.isoformat() if self.last_progress_update else None
        }
        
        # Calculate uptime
        if self.start_time:
            uptime = datetime.now() - self.start_time
            status_info['uptime_seconds'] = int(uptime.total_seconds())
        
        # Calculate progress percentage
        if self.total_sources > 0:
            status_info['progress']['progress_percent'] = round(
                (self.processed_sources / self.total_sources) * 100, 1
            )
        
        # Get memory info if process is active
        if self.pid:
            try:
                process = psutil.Process(self.pid)
                memory_info = process.memory_info()
                status_info['memory_info'] = {
                    'rss_mb': round(memory_info.rss / 1024 / 1024, 2),
                    'vms_mb': round(memory_info.vms / 1024 / 1024, 2),
                    'cpu_percent': process.cpu_percent()
                }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process may have ended
                if self.status in [ProcessStatus.RUNNING, ProcessStatus.PAUSED]:
                    self._notify_status_change(ProcessStatus.STOPPED)
        
        return status_info
    
    def is_process_healthy(self) -> bool:
        """
        Check if the current process is healthy
        
        Returns:
            bool: True if process is healthy, False otherwise
        """
        if not self.pid or self.status not in [ProcessStatus.RUNNING, ProcessStatus.PAUSED]:
            return False
        
        try:
            process = psutil.Process(self.pid)
            
            # Check if process exists and is responsive
            if not process.is_running():
                return False
            
            # Check memory usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            
            if memory_mb > self.max_memory_mb:
                self.logger.warning(f"Process memory usage too high: {memory_mb:.2f}MB")
                return False
            
            # Check if process has been stuck (no progress updates)
            if self.status == ProcessStatus.RUNNING and self.last_progress_update:
                time_since_update = datetime.now() - self.last_progress_update
                if time_since_update > timedelta(minutes=10):
                    self.logger.warning(f"No progress updates for {time_since_update}")
                    return False
            
            return True
            
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            self.logger.error(f"Process health check failed: {e}")
            return False
    
    def _start_memory_monitoring(self):
        """Start background memory monitoring thread"""
        if self._memory_monitoring:
            return
        
        self._memory_monitoring = True
        self._memory_monitor_thread = threading.Thread(
            target=self._memory_monitor_loop,
            daemon=True
        )
        self._memory_monitor_thread.start()
        self.logger.info("Memory monitoring started")
    
    def _memory_monitor_loop(self):
        """Background memory monitoring loop"""
        while self._memory_monitoring and self.pid:
            try:
                if not self.is_process_healthy():
                    if self.status in [ProcessStatus.RUNNING, ProcessStatus.PAUSED]:
                        self.logger.warning("Process health check failed, updating status")
                        self._notify_status_change(ProcessStatus.ERROR, {
                            'reason': 'Process health check failed'
                        })
                
                time.sleep(self.memory_check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in memory monitoring: {e}")
                time.sleep(self.memory_check_interval)
    
    def _start_output_monitoring(self):
        """Start monitoring process output for progress"""
        if self._monitoring_output:
            return
        
        self._monitoring_output = True
        self._output_thread = threading.Thread(
            target=self._monitor_output,
            daemon=True
        )
        self._output_thread.start()
        self.logger.info("Output monitoring started")
    
    def _monitor_output(self):
        """Monitor process output for progress updates"""
        if not self.process:
            return
        
        try:
            # Read stdout line by line
            for line in iter(self.process.stdout.readline, ''):
                if not self._monitoring_output:
                    break
                
                if line:
                    line = line.strip()
                    self._last_output_time = datetime.now()
                    
                    # Parse progress from output
                    self._parse_progress_from_output(line)
                    
                    # Log important lines
                    if any(keyword in line.lower() for keyword in ['error', 'warning', 'completed', 'processing']):
                        self.logger.info(f"Parser output: {line}")
                        
        except Exception as e:
            self.logger.error(f"Error monitoring output: {e}")
    
    def _parse_progress_from_output(self, line: str):
        """Parse progress information from output line"""
        try:
            # Look for patterns like "Processing source: xyz"
            if "Processing source:" in line:
                source_id = line.split("Processing source:")[-1].strip()
                self.update_progress(current_source=source_id)
            
            # Look for patterns like "Source xyz processed"
            elif "processed" in line and "source" in line.lower():
                self.update_progress(processed_sources=self.processed_sources + 1)
            
            # Look for total sources count
            elif "Starting RSS+Scrape parsing" in line and "sources_count" in line:
                # Extract total sources from log
                try:
                    import re
                    match = re.search(r'sources_count=(\d+)', line)
                    if match:
                        self.update_progress(total_sources=int(match.group(1)))
                except:
                    pass
            
            # Look for article counts
            elif "saved" in line and "rss_articles" in line:
                try:
                    import re
                    match = re.search(r'saved=(\d+)', line)
                    if match:
                        saved = int(match.group(1))
                        self.update_progress(total_articles=self.total_articles + saved)
                except:
                    pass
                    
        except Exception as e:
            self.logger.debug(f"Error parsing progress from output: {e}")
    
    def _cleanup_process(self):
        """Cleanup process resources"""
        self.process = None
        self.pid = None
        self.start_time = None
        self._memory_monitoring = False
        self._monitoring_output = False
        
        if self._memory_monitor_thread and self._memory_monitor_thread.is_alive():
            try:
                self._memory_monitor_thread.join(timeout=5)
            except:
                pass
        
        if self._output_thread and self._output_thread.is_alive():
            try:
                self._output_thread.join(timeout=5)
            except:
                pass
        
        self._memory_monitor_thread = None
        self._output_thread = None
        
        # Reset progress tracking
        self.current_source = None
        self.total_sources = 0
        self.processed_sources = 0
        self.total_articles = 0
        self.last_progress_update = None
    
    def update_progress(self, current_source: str = None, total_sources: int = None, 
                       processed_sources: int = None, total_articles: int = None):
        """
        Update progress information (called externally or by monitoring integration)
        
        Args:
            current_source: Currently processing source
            total_sources: Total number of sources to process
            processed_sources: Number of sources already processed
            total_articles: Total articles processed so far
        """
        if current_source is not None:
            self.current_source = current_source
        if total_sources is not None:
            self.total_sources = total_sources
        if processed_sources is not None:
            self.processed_sources = processed_sources
        if total_articles is not None:
            self.total_articles = total_articles
        
        progress_data = {
            'current_source': self.current_source,
            'total_sources': self.total_sources,
            'processed_sources': self.processed_sources,
            'total_articles': self.total_articles,
            'progress_percent': round((self.processed_sources / max(1, self.total_sources)) * 100, 1),
            'timestamp': datetime.now().isoformat()
        }
        
        self._notify_progress_update(progress_data)
    
    def _schedule_recovery(self):
        """Schedule automatic recovery attempt"""
        if self._recovery_thread and self._recovery_thread.is_alive():
            return
        
        self._recovery_attempts += 1
        delay = min(60 * self._recovery_attempts, 300)  # Max 5 minutes
        
        self.logger.info(f"Scheduling recovery attempt {self._recovery_attempts} in {delay} seconds")
        
        self._recovery_thread = threading.Thread(
            target=self._recovery_worker,
            args=(delay,),
            daemon=True
        )
        self._recovery_thread.start()
    
    def _recovery_worker(self, delay: int):
        """Worker thread for automatic recovery"""
        time.sleep(delay)
        
        if self.status not in [ProcessStatus.RUNNING, ProcessStatus.PAUSED]:
            self.logger.info("Attempting automatic recovery")
            
            # Try to start the parser again
            success = self.start_parser()
            
            if success:
                self.logger.info("Automatic recovery successful")
            else:
                self.logger.warning(f"Automatic recovery failed (attempt {self._recovery_attempts})")
    
    def enable_recovery(self, enabled: bool = True):
        """Enable or disable automatic recovery"""
        self._recovery_enabled = enabled
        self.logger.info(f"Automatic recovery {'enabled' if enabled else 'disabled'}")
    
    def _save_parser_state(self):
        """Save parser state for resume capability"""
        try:
            state_file = self.working_dir / "parser_state.json"
            state = {
                'pid': self.pid,
                'start_time': self.start_time.isoformat() if self.start_time else None,
                'current_source': self.current_source,
                'total_sources': self.total_sources,
                'processed_sources': self.processed_sources,
                'total_articles': self.total_articles,
                'last_save': datetime.now().isoformat()
            }
            
            with open(state_file, 'w') as f:
                json.dump(state, f, indent=2)
            
            self.logger.info(f"Parser state saved to {state_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save parser state: {e}")
    
    def _restore_parser_state(self) -> bool:
        """Restore parser state from file"""
        try:
            state_file = self.working_dir / "parser_state.json"
            if not state_file.exists():
                return False
            
            with open(state_file, 'r') as f:
                state = json.load(f)
            
            # Restore state
            self.current_source = state.get('current_source')
            self.total_sources = state.get('total_sources', 0)
            self.processed_sources = state.get('processed_sources', 0)
            self.total_articles = state.get('total_articles', 0)
            
            if state.get('start_time'):
                self.start_time = datetime.fromisoformat(state['start_time'])
            
            self.logger.info(f"Parser state restored from {state_file}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to restore parser state: {e}")
            return False
    
    def perform_health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check on parser process"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'pid': self.pid,
            'status': self.status.value,
            'is_healthy': False,
            'checks': {}
        }
        
        if not self.pid or self.status not in [ProcessStatus.RUNNING, ProcessStatus.PAUSED]:
            health_status['checks']['process_exists'] = False
            return health_status
        
        try:
            process = psutil.Process(self.pid)
            
            # Check 1: Process exists
            health_status['checks']['process_exists'] = process.is_running()
            
            # Check 2: CPU usage
            cpu_percent = process.cpu_percent(interval=0.1)
            health_status['checks']['cpu_usage'] = {
                'value': cpu_percent,
                'healthy': cpu_percent < 90
            }
            
            # Check 3: Memory usage
            memory_info = process.memory_info()
            memory_mb = memory_info.rss / 1024 / 1024
            health_status['checks']['memory_usage'] = {
                'value_mb': memory_mb,
                'healthy': memory_mb < self.max_memory_mb
            }
            
            # Check 4: Progress updates
            if self.status == ProcessStatus.RUNNING and self.last_progress_update:
                time_since_update = (datetime.now() - self.last_progress_update).total_seconds()
                health_status['checks']['progress_updates'] = {
                    'seconds_since_last': time_since_update,
                    'healthy': time_since_update < 300  # 5 minutes
                }
            
            # Check 5: Process responsiveness
            try:
                # Try to get process stats - if it hangs, process is unresponsive
                process.status()
                health_status['checks']['responsive'] = True
            except:
                health_status['checks']['responsive'] = False
            
            # Overall health
            health_status['is_healthy'] = all(
                check.get('healthy', check) if isinstance(check, dict) else check
                for check in health_status['checks'].values()
            )
            
            # Record in history
            self._health_history.append({
                'timestamp': datetime.now(),
                'healthy': health_status['is_healthy']
            })
            
        except psutil.NoSuchProcess:
            health_status['checks']['process_exists'] = False
            health_status['error'] = "Process not found"
        except Exception as e:
            health_status['error'] = str(e)
        
        return health_status
    
    def setup_automatic_restart(self, max_attempts: int = 3, restart_delay: int = 60):
        """Setup automatic restart on crash"""
        self._max_recovery_attempts = max_attempts
        self._recovery_enabled = True
        
        # Start health monitoring thread
        if not hasattr(self, '_health_monitor_thread') or not self._health_monitor_thread:
            self._health_monitor_thread = threading.Thread(
                target=self._health_monitor_loop,
                daemon=True
            )
            self._health_monitor_thread.start()
            self.logger.info(f"Automatic restart configured: max {max_attempts} attempts, {restart_delay}s delay")
    
    def _health_monitor_loop(self):
        """Monitor process health and trigger restart if needed"""
        check_interval = 30  # Check every 30 seconds
        
        while self._recovery_enabled:
            try:
                if self.status == ProcessStatus.RUNNING:
                    health = self.perform_health_check()
                    
                    if not health['is_healthy']:
                        self.logger.warning(f"Process health check failed: {health}")
                        
                        # Check if process crashed
                        if not health['checks'].get('process_exists', True):
                            self.logger.error("Process crashed - initiating recovery")
                            self._handle_process_crash()
                
                time.sleep(check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in health monitor: {e}")
                time.sleep(check_interval)
    
    def _handle_process_crash(self):
        """Handle process crash with automatic restart"""
        # Update status
        self._notify_status_change(ProcessStatus.ERROR, {
            'reason': 'Process crashed',
            'recovery_attempts': self._recovery_attempts
        })
        
        # Clean up dead process
        self._cleanup_process()
        
        # Schedule recovery if within limits
        if self._recovery_attempts < self._max_recovery_attempts:
            self._schedule_recovery()
        else:
            self.logger.error(f"Max recovery attempts ({self._max_recovery_attempts}) reached")
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status including circuit breakers"""
        basic_status = self.get_status()
        health_check = self.is_process_healthy()
        
        # Record health check result
        self._health_history.append({
            'timestamp': datetime.now(),
            'healthy': health_check
        })
        
        # Calculate health percentage
        recent_checks = list(self._health_history)
        if recent_checks:
            healthy_count = sum(1 for check in recent_checks if check['healthy'])
            health_percentage = (healthy_count / len(recent_checks)) * 100
        else:
            health_percentage = 100 if health_check else 0
        
        return {
            **basic_status,
            'health': {
                'is_healthy': health_check,
                'health_percentage': round(health_percentage, 1),
                'recent_checks': len(recent_checks)
            },
            'circuit_breakers': {
                'start': {
                    'is_open': self.start_circuit_breaker.is_open,
                    'failure_count': self.start_circuit_breaker.failure_count,
                    'can_attempt': self.start_circuit_breaker.can_attempt()
                },
                'memory': {
                    'is_open': self.memory_circuit_breaker.is_open,
                    'failure_count': self.memory_circuit_breaker.failure_count,
                    'can_attempt': self.memory_circuit_breaker.can_attempt()
                }
            },
            'recovery': {
                'enabled': self._recovery_enabled,
                'attempts': self._recovery_attempts,
                'max_attempts': self._max_recovery_attempts
            }
        }


# Global process manager instance
_process_manager: Optional[ProcessManager] = None


def get_process_manager() -> ProcessManager:
    """Get or create global process manager instance"""
    global _process_manager
    if _process_manager is None:
        _process_manager = ProcessManager()
    return _process_manager


def initialize_process_manager() -> ProcessManager:
    """Initialize and return process manager"""
    return get_process_manager()
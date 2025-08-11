"""
MVP Logging module for AI News Parser Clean
Simple and effective logging with minimal overhead
"""
import logging
import json
import os
from datetime import datetime
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Simple configuration
_configured = False

def _write_to_rotating_log(filename, data):
    """Write data to a rotating log file using simple rotation logic"""
    os.makedirs('logs', exist_ok=True)
    
    # Check file size and rotate if needed (10MB limit)
    max_size = 10 * 1024 * 1024  # 10MB
    
    if os.path.exists(filename):
        file_size = os.path.getsize(filename)
        if file_size > max_size:
            # Rotate the file
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            base_name = filename.replace('.jsonl', '')
            rotated_name = f"{base_name}_{timestamp}.jsonl"
            os.rename(filename, rotated_name)
            
            # Clean up old rotated files (keep only 5 most recent)
            import glob
            pattern = f"{base_name}_*.jsonl"
            rotated_files = sorted(glob.glob(pattern))
            if len(rotated_files) > 5:
                for old_file in rotated_files[:-5]:
                    try:
                        os.remove(old_file)
                    except:
                        pass
    
    # Write to file
    with open(filename, 'a', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False) + '\n')

def configure_logging():
    """Simple logging setup"""
    global _configured
    if _configured:
        return
    
    # Basic console logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create logs directory
    os.makedirs('logs', exist_ok=True)
    _configured = True

def get_logger(name):
    """Get simple logger"""
    configure_logging()
    return logging.getLogger(name)

def log_operation(operation, **kwargs):
    """Log critical operations to JSONL file and notify monitoring
    
    Args:
        operation: Operation name (e.g., 'api_call', 'phase_start')
        **kwargs: Additional context (url, cost, duration, etc.)
    """
    data = {
        'timestamp': datetime.utcnow().isoformat(),
        'operation': operation,
        **kwargs
    }
    
    # Use rotating log handler
    _write_to_rotating_log('logs/operations.jsonl', data)
    
    # Notify monitoring dashboard about new operation
    try:
        import requests
        requests.post('http://localhost:8001/api/pipeline/broadcast', 
                     json={'operation': data}, 
                     timeout=0.5)
    except:
        pass  # Ignore errors - monitoring might not be running

def log_error(error_type, message, **context):
    """Log errors to JSONL file
    
    Args:
        error_type: Type of error (e.g., 'api_error', 'parsing_failed')
        message: Error message
        **context: Additional context (article_id, url, phase, etc.)
    """
    data = {
        'timestamp': datetime.utcnow().isoformat(),
        'error_type': error_type,
        'message': str(message),
        **context
    }
    
    # Use rotating log handler
    _write_to_rotating_log('logs/errors.jsonl', data)

# Compatibility stub for old code that uses LogContext
class LogContext:
    """Stub for backward compatibility with old logging system"""
    @staticmethod
    def operation(name, **kwargs):
        class DummyContext:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return DummyContext()
    
    @staticmethod
    def article(article_id, **kwargs):
        class DummyContext:
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
        return DummyContext()

# Stub for log_execution_time decorator (compatibility)
def log_execution_time(func):
    """Stub decorator for backward compatibility"""
    return func

# Stub handlers for backward compatibility
def handle_websocket_error(logger, error, context=None):
    """Stub for compatibility"""
    log_error('websocket_error', str(error), **(context or {}))

def handle_database_error(logger, error, context=None):
    """Stub for compatibility"""
    log_error('database_error', str(error), **(context or {}))

def handle_api_error(logger, error, context=None):
    """Stub for compatibility"""
    log_error('api_error', str(error), **(context or {}))

def handle_process_error(logger, error, context=None):
    """Stub for compatibility"""
    log_error('process_error', str(error), **(context or {}))

def handle_monitoring_error(logger, error, context=None):
    """Stub for compatibility"""
    log_error('monitoring_error', str(error), **(context or {}))

# Stub classes for compatibility
class MonitoringErrorHandler:
    """Stub for compatibility"""
    def __init__(self, logger_name='monitoring'):
        pass
    
    def log_error(self, error, context=None):
        log_error('monitoring_error', str(error), **(context or {}))

def safe_operation(operation_name):
    """Stub decorator for compatibility"""
    def decorator(func):
        return func
    return decorator
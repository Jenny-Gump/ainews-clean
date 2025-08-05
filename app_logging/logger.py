"""
Enhanced logging module for AI News Parser Clean
Provides centralized logging functionality with context management
"""
import logging
import logging.handlers
import sys
import json
import os
from datetime import datetime
from typing import Optional, Dict, Any
from pathlib import Path
from contextlib import contextmanager


# Load logging configuration
def load_logging_config():
    """Load logging configuration from config.json"""
    config_path = Path(__file__).parent / "config.json"
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}


# Global logging configuration
_logging_configured = False
_config = load_logging_config()


def configure_logging():
    """Configure global logging settings"""
    global _logging_configured
    if _logging_configured:
        return
    
    # Get log level from config or environment
    log_level = _config.get('file_level', 'INFO')
    if isinstance(log_level, str):
        log_level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    
    # Create logs directory if it doesn't exist
    base_log_dir = _config.get('base_log_dir', 'logs')
    os.makedirs(base_log_dir, exist_ok=True)
    
    # Configure specialized file handlers
    specialized_logs = _config.get('specialized_logs', {})
    
    # Add handler for media logs specifically
    if 'media' in specialized_logs:
        media_config = specialized_logs['media']
        media_handler = logging.handlers.RotatingFileHandler(
            os.path.join(base_log_dir, media_config['filename']),
            maxBytes=media_config.get('max_bytes', 52428800),
            backupCount=_config.get('backup_count', 10)
        )
        media_handler.setLevel(getattr(logging, media_config.get('level', 'INFO')))
        media_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        
        # Add handler to media-related loggers
        media_logger = logging.getLogger('extract_system.media_downloader_playwright')
        media_logger.addHandler(media_handler)
        media_logger.setLevel(logging.DEBUG)  # Allow all levels, handler will filter
    
    _logging_configured = True


class EnhancedLogger:
    """Logger wrapper that supports extra parameters like in the old system"""
    
    def __init__(self, logger: logging.Logger):
        self._logger = logger
    
    def _format_message(self, message: str, **kwargs) -> str:
        """Format message with additional parameters if needed"""
        if kwargs:
            # Add parameters to message for compatibility
            params = ', '.join(f'{k}={v}' for k, v in kwargs.items())
            return f"{message} ({params})"
        return message
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional parameters"""
        # Extract special logging parameters to avoid conflicts
        exc_info = kwargs.pop('exc_info', None)
        stack_info = kwargs.pop('stack_info', None)
        stacklevel = kwargs.pop('stacklevel', 1)
        
        self._logger.debug(
            self._format_message(message, **kwargs), 
            extra=kwargs,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel
        )
    
    def info(self, message: str, **kwargs):
        """Log info message with optional parameters"""
        # Extract special logging parameters to avoid conflicts
        exc_info = kwargs.pop('exc_info', None)
        stack_info = kwargs.pop('stack_info', None)
        stacklevel = kwargs.pop('stacklevel', 1)
        
        self._logger.info(
            self._format_message(message, **kwargs), 
            extra=kwargs,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel
        )
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional parameters"""
        # Extract special logging parameters to avoid conflicts
        exc_info = kwargs.pop('exc_info', None)
        stack_info = kwargs.pop('stack_info', None)
        stacklevel = kwargs.pop('stacklevel', 1)
        
        self._logger.warning(
            self._format_message(message, **kwargs), 
            extra=kwargs,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel
        )
    
    def error(self, message: str, **kwargs):
        """Log error message with optional parameters"""
        # Extract special logging parameters to avoid conflicts
        exc_info = kwargs.pop('exc_info', None)
        stack_info = kwargs.pop('stack_info', None)
        stacklevel = kwargs.pop('stacklevel', 1)
        
        # Pass remaining kwargs as extra, special params separately
        self._logger.error(
            self._format_message(message, **kwargs), 
            extra=kwargs,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel
        )
    
    def critical(self, message: str, **kwargs):
        """Log critical message with optional parameters"""
        # Extract special logging parameters to avoid conflicts
        exc_info = kwargs.pop('exc_info', None)
        stack_info = kwargs.pop('stack_info', None)
        stacklevel = kwargs.pop('stacklevel', 1)
        
        self._logger.critical(
            self._format_message(message, **kwargs), 
            extra=kwargs,
            exc_info=exc_info,
            stack_info=stack_info,
            stacklevel=stacklevel
        )
    
    # Delegate other methods to the underlying logger
    def __getattr__(self, name):
        return getattr(self._logger, name)


def get_logger(name: str) -> EnhancedLogger:
    """
    Get a logger instance with standardized configuration
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Configured logger instance with enhanced capabilities
    """
    # Ensure logging is configured
    configure_logging()
    
    logger = logging.getLogger(name)
    return EnhancedLogger(logger)


class LogContext:
    """Enhanced context manager for logging operations with structured context"""
    
    @classmethod
    @contextmanager
    def operation(cls, operation: str, **kwargs):
        """Context manager for logging operations"""
        logger = get_logger('operation')
        start_time = datetime.now()
        
        # Log operation start
        logger.info(f"Starting {operation}", extra=kwargs)
        
        try:
            yield
            # Log successful completion
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(
                f"Completed {operation} in {duration:.2f}s",
                extra={**kwargs, 'duration': duration}
            )
        except Exception as e:
            # Log failure
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(
                f"Failed {operation} after {duration:.2f}s: {e}",
                extra={**kwargs, 'duration': duration, 'error': str(e)}
            )
            raise
    
    @classmethod
    @contextmanager
    def article(cls, article_id: str, article_url: str = None, article_title: str = None):
        """Context manager for article processing"""
        context = {'article_id': article_id}
        if article_url:
            context['article_url'] = article_url
        if article_title:
            context['article_title'] = article_title
        
        with cls.operation("article_processing", **context):
            yield
    
    @classmethod
    @contextmanager
    def source(cls, source_id: str, source_name: str = None):
        """Context manager for source processing"""
        context = {'source_id': source_id}
        if source_name:
            context['source_name'] = source_name
        
        with cls.operation("source_processing", **context):
            yield


def log_execution_time(func):
    """Decorator to log function execution time"""
    def wrapper(*args, **kwargs):
        logger = get_logger(f"{func.__module__}.{func.__name__}")
        start_time = datetime.now()
        
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"{func.__name__} completed in {duration:.2f}s")
            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"{func.__name__} failed after {duration:.2f}s: {e}")
            raise
    
    return wrapper


def log_error(logger: logging.Logger, error: Exception, context: Dict[str, Any] = None):
    """Log an error with optional context"""
    error_info = {
        'error_type': type(error).__name__,
        'error_message': str(error)
    }
    
    if context:
        error_info.update(context)
    
    logger.error(f"Error occurred: {error}", extra=error_info)


# Specialized error handlers for monitoring system
class MonitoringErrorHandler:
    """Centralized error handling for monitoring system"""
    
    def __init__(self, logger_name: str = 'monitoring'):
        self.logger = get_logger(logger_name)
        self.config = _config
        self.capture_stack_traces = self.config.get('capture_stack_traces', True)
        self.stack_trace_depth = self.config.get('stack_trace_depth', 10)
    
    def handle_websocket_error(self, error: Exception, websocket=None, context: Dict[str, Any] = None):
        """Handle WebSocket-related errors gracefully"""
        error_context = {
            'error_type': 'websocket',
            'websocket_state': getattr(websocket, 'client_state', 'unknown') if websocket else None,
        }
        if context:
            error_context.update(context)
        
        # Log with appropriate level based on error type
        error_type_name = type(error).__name__
        
        if error_type_name == 'WebSocketDisconnect' or isinstance(error, ConnectionResetError):
            self.logger.info(f"WebSocket connection closed: {error}", extra=error_context)
        elif error_type_name == 'ConnectionAbortedError':
            self.logger.warning(f"WebSocket connection aborted: {error}", extra=error_context)
        elif "disconnected" in str(error).lower() or "closed" in str(error).lower():
            self.logger.info(f"WebSocket disconnected: {error}", extra=error_context)
        elif "timeout" in str(error).lower():
            self.logger.warning(f"WebSocket timeout: {error}", extra=error_context)
        else:
            self.logger.error(f"WebSocket error: {error}", extra=error_context, exc_info=self.capture_stack_traces)
    
    def handle_database_error(self, error: Exception, operation: str = None, context: Dict[str, Any] = None):
        """Handle database-related errors with context"""
        error_context = {
            'error_type': 'database',
            'operation': operation,
            'database_error': True
        }
        if context:
            error_context.update(context)
        
        # Determine severity
        if "locked" in str(error).lower():
            self.logger.warning(f"Database locked during {operation}: {error}", extra=error_context)
        elif "no such table" in str(error).lower():
            self.logger.error(f"Database schema error in {operation}: {error}", extra=error_context, exc_info=self.capture_stack_traces)
        else:
            self.logger.error(f"Database error in {operation}: {error}", extra=error_context, exc_info=self.capture_stack_traces)
    
    def handle_api_error(self, error: Exception, endpoint: str = None, context: Dict[str, Any] = None):
        """Handle API-related errors"""
        error_context = {
            'error_type': 'api',
            'endpoint': endpoint,
            'api_error': True
        }
        if context:
            error_context.update(context)
        
        # Log based on HTTP status or error type
        if hasattr(error, 'status_code'):
            if 400 <= error.status_code < 500:
                self.logger.warning(f"API client error at {endpoint}: {error}", extra=error_context)
            else:
                self.logger.error(f"API server error at {endpoint}: {error}", extra=error_context, exc_info=self.capture_stack_traces)
        else:
            self.logger.error(f"API error at {endpoint}: {error}", extra=error_context, exc_info=self.capture_stack_traces)
    
    def handle_process_error(self, error: Exception, process_name: str = None, context: Dict[str, Any] = None):
        """Handle process management errors"""
        error_context = {
            'error_type': 'process',
            'process_name': process_name,
            'process_error': True
        }
        if context:
            error_context.update(context)
        
        # Handle specific process errors
        if "No such process" in str(error):
            self.logger.info(f"Process {process_name} no longer exists: {error}", extra=error_context)
        elif "Permission denied" in str(error):
            self.logger.warning(f"Permission denied for process {process_name}: {error}", extra=error_context)
        else:
            self.logger.error(f"Process error for {process_name}: {error}", extra=error_context, exc_info=self.capture_stack_traces)
    
    def handle_monitoring_error(self, error: Exception, component: str = None, context: Dict[str, Any] = None):
        """Handle general monitoring system errors"""
        error_context = {
            'error_type': 'monitoring',
            'component': component,
            'monitoring_error': True
        }
        if context:
            error_context.update(context)
        
        self.logger.error(f"Monitoring error in {component}: {error}", extra=error_context, exc_info=self.capture_stack_traces)


def safe_operation(operation_name: str = None, fallback_result=None, log_success: bool = False):
    """Decorator for safe operations with centralized error handling"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Safe module name handling
            module_name = getattr(func, '__module__', 'unknown') or 'unknown'
            error_handler = MonitoringErrorHandler(f"monitoring.{module_name}")
            op_name = operation_name or f"{func.__name__}"
            
            try:
                result = func(*args, **kwargs)
                if log_success:
                    error_handler.logger.debug(f"Successfully completed {op_name}")
                return result
            except Exception as e:
                error_handler.handle_monitoring_error(
                    e, 
                    component=op_name,
                    context={
                        'function': func.__name__,
                        'module': module_name,
                        'args_count': len(args),
                        'kwargs_keys': list(kwargs.keys()) if kwargs else []
                    }
                )
                return fallback_result
        return wrapper
    return decorator


# Convenience functions for direct use
def handle_websocket_error(error: Exception, websocket=None, context: Dict[str, Any] = None):
    """Direct access to WebSocket error handler"""
    handler = MonitoringErrorHandler()
    handler.handle_websocket_error(error, websocket, context)

def handle_database_error(error: Exception, operation: str = None, context: Dict[str, Any] = None):
    """Direct access to database error handler"""
    handler = MonitoringErrorHandler()
    handler.handle_database_error(error, operation, context)

def handle_api_error(error: Exception, endpoint: str = None, context: Dict[str, Any] = None):
    """Direct access to API error handler"""
    handler = MonitoringErrorHandler()
    handler.handle_api_error(error, endpoint, context)

def handle_process_error(error: Exception, process_name: str = None, context: Dict[str, Any] = None):
    """Direct access to process error handler"""
    handler = MonitoringErrorHandler()
    handler.handle_process_error(error, process_name, context)

def handle_monitoring_error(error: Exception, component: str = None, context: Dict[str, Any] = None):
    """Direct access to monitoring error handler"""
    handler = MonitoringErrorHandler()
    handler.handle_monitoring_error(error, component, context)
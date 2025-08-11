"""
MVP logging module for AI News Parser Clean
"""

from .logger import (
    get_logger,
    configure_logging,
    log_operation,
    log_error,
    # Compatibility exports for old code
    LogContext,
    log_execution_time,
    MonitoringErrorHandler,
    safe_operation,
    handle_websocket_error,
    handle_database_error,
    handle_api_error,
    handle_process_error,
    handle_monitoring_error
)

__all__ = [
    'get_logger',
    'configure_logging', 
    'log_operation',
    'log_error',
    # Compatibility
    'LogContext',
    'log_execution_time',
    'MonitoringErrorHandler',
    'safe_operation',
    'handle_websocket_error',
    'handle_database_error',
    'handle_api_error',
    'handle_process_error',
    'handle_monitoring_error'
]
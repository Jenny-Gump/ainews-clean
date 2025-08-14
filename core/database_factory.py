#!/usr/bin/env python3
"""
Database Factory for AI News Parser
Автоматический выбор database adapter (Supabase MCP или SQLite)
"""

import os
import logging
from typing import Any
from app_logging import get_logger
from core.config import Config

logger = get_logger(__name__)


def create_database() -> Any:
    """
    Create appropriate database adapter based on configuration
    Создает подходящий database adapter на основе конфигурации
    """
    try:
        # Используем РЕАЛЬНЫЙ Python Supabase client
        logger.info("🚀 Initializing REAL Python Supabase Database")
        
        try:
            from core.db_config import DatabaseConfig
            database = DatabaseConfig.get_database()
            
            # Тестируем подключение
            if hasattr(database, 'test_connection') and database.test_connection():
                logger.info("✅ REAL Python Supabase database initialized successfully")
                return database
            else:
                logger.error("❌ Real Supabase connection test failed")
                
        except ImportError as e:
            logger.error(f"❌ Real Supabase client not available: {e}")
        except Exception as e:
            logger.error(f"❌ Failed to initialize real Supabase database: {e}")
        
        # ТОЛЬКО Supabase - SQLite отключен
        raise Exception("КРИТИЧНО: Real Supabase database failed to initialize. SQLite отключен.")
            
    except Exception as e:
        logger.error(f"❌ Database factory failed: {e}")
        raise Exception(f"Failed to create database adapter: {e}")


def test_database_connection() -> bool:
    """
    Test database connection
    Тестирует подключение к базе данных
    """
    try:
        database = create_database()
        
        # Тест базового подключения
        if hasattr(database, 'test_connection'):
            return database.test_connection()
        elif hasattr(database, 'get_stats'):
            # Пробуем получить статистику как тест
            stats = database.get_stats()
            return isinstance(stats, dict) and 'total_articles' in stats
        else:
            logger.warning("Database doesn't support connection testing")
            return True
            
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def get_database_info() -> dict:
    """
    Get database information and configuration
    Получает информацию о базе данных и конфигурации
    """
    try:
        database = create_database()
        
        info = {
            "type": "Real Python Supabase",
            "connection_working": test_database_connection()
        }
        
        # Добавляем статистику если доступна
        if hasattr(database, 'get_stats'):
            try:
                stats = database.get_stats()
                info.update(stats)
            except Exception as e:
                logger.warning(f"Failed to get database stats: {e}")
                info["stats_error"] = str(e)
        
        # Информация о Supabase
        info.update({
            "project_ref": Config.SUPABASE_PROJECT_REF,
            "url": Config.SUPABASE_URL,
            "real_client": True
        })
        
        return info
        
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {
            "type": "Unknown",
            "connection_working": False,
            "error": str(e)
        }


# Utility functions for common operations
def execute_sql_safe(query: str, params: list = None) -> list:
    """
    Safely execute SQL query with proper error handling
    Безопасно выполняет SQL запрос с обработкой ошибок
    """
    try:
        database = create_database()
        
        if hasattr(database, 'execute_sql'):
            return database.execute_sql(query, params)
        elif hasattr(database, '_execute_sql'):
            return database._execute_sql(query, params)
        else:
            logger.error("Database doesn't support direct SQL execution")
            return []
            
    except Exception as e:
        logger.error(f"Safe SQL execution failed: {e}")
        return []


def get_database_stats_safe() -> dict:
    """
    Safely get database statistics
    Безопасно получает статистику базы данных
    """
    try:
        database = create_database()
        
        if hasattr(database, 'get_stats'):
            return database.get_stats()
        else:
            logger.warning("Database doesn't support stats")
            return {"error": "Stats not supported"}
            
    except Exception as e:
        logger.error(f"Failed to get database stats safely: {e}")
        return {"error": str(e)}


# Test function
def test_database_factory():
    """Test database factory functionality"""
    logger.info("=" * 60)
    logger.info("🧪 TESTING DATABASE FACTORY")
    logger.info("=" * 60)
    
    # Test configuration
    config_summary = Config.get_summary()
    logger.info(f"Configuration: {config_summary}")
    
    # Test database creation
    try:
        database = create_database()
        logger.info(f"✅ Database created: {type(database).__name__}")
        
        # Test connection
        connection_ok = test_database_connection()
        logger.info(f"Connection test: {'✅ PASSED' if connection_ok else '❌ FAILED'}")
        
        # Test stats
        stats = get_database_stats_safe()
        logger.info(f"Stats: {stats}")
        
    except Exception as e:
        logger.error(f"❌ Database factory test failed: {e}")
    
    logger.info("=" * 60)
    logger.info("✅ Database factory test completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    test_database_factory()
#!/usr/bin/env python3
"""
Database Configuration Manager
Управляет переключением между SQLite и Supabase
"""
import os
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from app_logging import get_logger

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

logger = get_logger(__name__)

class DatabaseConfig:
    """Конфигурация и переключение баз данных"""
    
    @staticmethod
    def use_supabase() -> bool:
        """ВСЕГДА возвращает True - SQLite полностью отключен"""
        # SQLite ПОЛНОСТЬЮ ОТКЛЮЧЕН - всегда используем Supabase
        return True
    
    @staticmethod
    def get_supabase_config() -> Optional[dict]:
        """Возвращает конфигурацию Supabase если доступна"""
        if not DatabaseConfig.use_supabase():
            return None
            
        url = os.getenv('SUPABASE_URL')
        anon_key = os.getenv('SUPABASE_ANON_KEY')
        service_role_key = os.getenv('SUPABASE_SERVICE_ROLE_KEY')
        
        if not url or not anon_key:
            logger.warning("Supabase enabled but missing credentials")
            return None
        
        return {
            'url': url,
            'anon_key': anon_key,
            'service_role_key': service_role_key,
            'project_ref': os.getenv('SUPABASE_PROJECT_REF', ''),
            'access_token': os.getenv('SUPABASE_ACCESS_TOKEN', '')
        }
    
    @staticmethod
    def get_database():
        """Возвращает РЕАЛЬНЫЙ Python Supabase client"""
        config = DatabaseConfig.get_supabase_config()
        if not config:
            raise Exception("КРИТИЧНО: Supabase конфигурация отсутствует. Проверьте .env файл.")
        
        try:
            from services.supabase_client import get_supabase_client
            logger.info("✅ Using REAL Python Supabase client")
            return get_supabase_client()
        except Exception as e:
            logger.error(f"Failed to initialize real Supabase client: {e}")
            raise Exception(f"Real Supabase client initialization failed: {e}")
    
    @staticmethod
    def test_supabase_connection() -> bool:
        """Тестирует подключение к РЕАЛЬНОМУ Supabase"""
        try:
            db = DatabaseConfig.get_database()
            return db.test_connection()
        except Exception as e:
            logger.error(f"Real Supabase connection test failed: {e}")
            return False
    
    @staticmethod
    def get_database_info() -> dict:
        """Возвращает информацию о текущей базе данных"""
        return {
            'type': 'supabase',
            'supabase_available': DatabaseConfig.get_supabase_config() is not None,
            'supabase_connection_ok': DatabaseConfig.test_supabase_connection() if DatabaseConfig.get_supabase_config() else False,
            'config': {
                'USE_SUPABASE': os.getenv('USE_SUPABASE', 'true'),
                'project_ref': os.getenv('SUPABASE_PROJECT_REF', 'not_set'),
                'has_access_token': bool(os.getenv('SUPABASE_ACCESS_TOKEN')),
                'has_anon_key': bool(os.getenv('SUPABASE_ANON_KEY')),
                'has_service_role_key': bool(os.getenv('SUPABASE_SERVICE_ROLE_KEY'))
            }
        }
#!/usr/bin/env python3
"""
Config for AI News Parser Clean System
Конфигурация для AI News Parser Clean системы
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Конфигурация для AI News Parser Clean системы"""
    
    # Extract API настройки
    FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY')
    EXTRACT_API_URL = "https://api.firecrawl.dev/v1/extract"
    
    # OpenAI API настройки для WordPress
    openai_api_key = os.getenv('OPENAI_API_KEY')
    wordpress_llm_model = os.getenv('WORDPRESS_LLM_MODEL', 'gpt-4o-mini')
    
    # WordPress настройки
    wordpress_retry_attempts = int(os.getenv('WORDPRESS_RETRY_ATTEMPTS', '3'))
    
    # WordPress API настройки
    wordpress_api_url = os.getenv('WORDPRESS_API_URL')
    wordpress_username = os.getenv('WORDPRESS_USERNAME')
    wordpress_app_password = os.getenv('WORDPRESS_APP_PASSWORD')
    
    # Custom Post Meta Endpoint настройки
    use_custom_meta_endpoint = os.getenv('USE_CUSTOM_META_ENDPOINT', 'false').lower() == 'true'
    custom_post_meta_api_key = os.getenv('CUSTOM_POST_META_API_KEY', '')
    
    # Ограничения и тайм-ауты
    REQUEST_TIMEOUT = 120  # 2 минуты на Extract запрос
    MAX_RETRIES = 2
    MAX_CONCURRENT_DOWNLOADS = 3  # Меньше чем в основной системе
    
    # Размеры файлов
    MAX_FILE_SIZE = 2 * 1024 * 1024   # 2MB максимум для медиа
    MIN_FILE_SIZE = 2 * 1024          # 2KB минимум
    
    # Размеры изображений (пиксели)
    MIN_IMAGE_WIDTH = 250   # Минимальная ширина 250px
    MIN_IMAGE_HEIGHT = 250  # Минимальная высота 250px
    
    # База данных (общая с основной системой)
    DATABASE_PATH = "data/ainews.db"
    
    # Папки
    MEDIA_DIR = "data/media"
    LOGS_DIR = "extract_system/logs"
    
    # RSS настройки
    RSS_SOURCES_FILE = "extract_system/sources_extract.json"
    DEFAULT_DAYS_BACK = 7
    RSS_BATCH_SIZE = 10
    
    # Мониторинг
    MONITORING_ENABLED = True
    LOGGING_PREFIX = "extract_system"
    
    # Extract API Schema (оптимизированная для новостей)
    EXTRACT_SCHEMA = {
        "type": "object",
        "properties": {
            "title": {"type": "string"},
            "author": {"type": "string"},
            "published_date": {"type": "string"},
            "source": {"type": "string"},
            "content": {"type": "string"},
            "summary": {"type": "string"},
            "language": {"type": "string"},
            "word_count": {"type": "number"},
            "reading_time_minutes": {"type": "number"},
            "tags": {
                "type": "array",
                "items": {"type": "string"}
            },
            "categories": {
                "type": "array", 
                "items": {"type": "string"}
            },
            "images": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "url": {"type": "string"},
                        "alt_text": {"type": "string"},
                        "caption": {"type": "string"}
                    }
                }
            },
            "media_urls": {
                "type": "array",
                "items": {"type": "string"}
            },
            "related_links": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "url": {"type": "string"}
                    }
                }
            },
            "meta_description": {"type": "string"}
        }
    }
    
    # Extract API Prompt
    EXTRACT_PROMPT = '''Extract all available information including:
    - Full article content and metadata
    - All images with their alt text and captions
    - Any videos or embedded media URLs
    - Related links and references
    - Tags and categories
    - SEO metadata
    '''
    
    @classmethod
    def validate_config(cls):
        """Проверяет конфигурацию системы"""
        errors = []
        
        if not cls.FIRECRAWL_API_KEY:
            errors.append("FIRECRAWL_API_KEY не найден в переменных окружения")
        
        if not cls.openai_api_key:
            errors.append("OPENAI_API_KEY не найден в переменных окружения")
        
        return errors
    
    @classmethod
    def get_summary(cls):
        """Возвращает сводку конфигурации"""
        return {
            "api_configured": bool(cls.FIRECRAWL_API_KEY),
            "database_path": cls.DATABASE_PATH,
            "media_dir": cls.MEDIA_DIR,
            "sources_file": cls.RSS_SOURCES_FILE,
            "request_timeout": cls.REQUEST_TIMEOUT,
            "max_file_size_mb": cls.MAX_FILE_SIZE / 1024 / 1024,
            "monitoring_enabled": cls.MONITORING_ENABLED
        }
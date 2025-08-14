#!/usr/bin/env python3
"""
Тестовый скрипт для проверки Continuous Pipeline с Supabase
Проверяет подключение, конфигурацию и запуск основных операций
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Загружаем переменные окружения
load_dotenv()

# Импортируем модули
from core.db_config import DatabaseConfig
from app_logging import configure_logging, get_logger
from services.rss_discovery import ExtractRSSDiscovery

# Настройка логирования
configure_logging()
logger = get_logger(__name__)


def test_environment():
    """Тестирует переменные окружения"""
    logger.info("🔧 Проверка переменных окружения:")
    
    env_vars = {
        'USE_SUPABASE': os.getenv('USE_SUPABASE', 'не установлено'),
        'SUPABASE_PROJECT_REF': os.getenv('SUPABASE_PROJECT_REF', 'не установлено'),
        'SUPABASE_ACCESS_TOKEN': 'установлено' if os.getenv('SUPABASE_ACCESS_TOKEN') else 'не установлено',
        'SUPABASE_ANON_KEY': 'установлено' if os.getenv('SUPABASE_ANON_KEY') else 'не установлено',
        'SUPABASE_SERVICE_ROLE_KEY': 'установлено' if os.getenv('SUPABASE_SERVICE_ROLE_KEY') else 'не установлено'
    }
    
    for var, value in env_vars.items():
        logger.info(f"   {var}: {value}")
    
    return all(value != 'не установлено' for var, value in env_vars.items() if var != 'USE_SUPABASE')


def test_database_config():
    """Тестирует конфигурацию базы данных"""
    logger.info("\n📊 Тестирование конфигурации базы данных:")
    
    try:
        # Проверяем настройки
        logger.info(f"   USE_SUPABASE: {DatabaseConfig.use_supabase()}")
        
        # Получаем информацию о БД
        db_info = DatabaseConfig.get_database_info()
        logger.info(f"   Database type: {db_info['type']}")
        logger.info(f"   Supabase available: {db_info['supabase_available']}")
        logger.info(f"   Supabase connection OK: {db_info['supabase_connection_ok']}")
        
        return db_info['supabase_available']
        
    except Exception as e:
        logger.error(f"   ❌ Ошибка конфигурации: {e}")
        return False


def test_database_connection():
    """Тестирует подключение к базе данных"""
    logger.info("\n🔗 Тестирование подключения к Supabase:")
    
    try:
        # Получаем экземпляр базы данных
        db = DatabaseConfig.get_database()
        logger.info(f"   ✅ Инициализация БД успешна: {type(db).__name__}")
        
        # Тестируем простой запрос
        stats = db.get_stats()
        logger.info(f"   ✅ Получены статистики: {len(stats)} полей")
        logger.info(f"   - Источников: {stats.get('total_sources', 0)}")
        logger.info(f"   - Статей: {stats.get('total_articles', 0)}")
        
        return True
        
    except Exception as e:
        logger.error(f"   ❌ Ошибка подключения: {e}")
        return False


async def test_rss_discovery():
    """Тестирует RSS Discovery"""
    logger.info("\n📡 Тестирование RSS Discovery:")
    
    try:
        discovery = ExtractRSSDiscovery()
        
        # Получаем список источников
        db = DatabaseConfig.get_database()
        sources = db.get_sources(active_only=True)
        logger.info(f"   ✅ Активных источников: {len(sources)}")
        
        if len(sources) == 0:
            logger.warning("   ⚠️ Нет активных источников для тестирования")
            return False
        
        # Показываем первые 5 источников
        logger.info("   Первые источники:")
        for i, source in enumerate(sources[:5]):
            logger.info(f"   {i+1}. {source['name']} ({source['source_id']})")
        
        return True
        
    except Exception as e:
        logger.error(f"   ❌ Ошибка RSS Discovery: {e}")
        return False


def test_pending_articles():
    """Проверяет наличие pending статей"""
    logger.info("\n📰 Проверка pending статей:")
    
    try:
        db = DatabaseConfig.get_database()
        
        # Получаем количество pending статей
        pending_count = db.get_pending_articles_count()
        logger.info(f"   ✅ Pending статей: {pending_count}")
        
        if pending_count > 0:
            # Показываем первые 3 pending статьи
            pending_articles = db.get_pending_articles(limit=3)
            logger.info("   Первые pending статьи:")
            for i, article in enumerate(pending_articles):
                title = article['title'][:50]
                logger.info(f"   {i+1}. {title}... ({article['article_id']})")
        
        return True
        
    except Exception as e:
        logger.error(f"   ❌ Ошибка проверки статей: {e}")
        return False


async def test_continuous_pipeline_dry_run():
    """Тестирует continuous pipeline в сухом режиме"""
    logger.info("\n🔄 Тестирование Continuous Pipeline (dry run):")
    
    try:
        # Импортируем pipeline
        from core.single_pipeline import SingleArticlePipeline
        
        pipeline = SingleArticlePipeline()
        logger.info("   ✅ Pipeline инициализирован")
        
        # Проверяем наличие статей для обработки
        db = DatabaseConfig.get_database()
        pending_count = db.get_pending_articles_count()
        
        if pending_count == 0:
            logger.info("   ℹ️ Нет pending статей для обработки")
            return True
        
        logger.info(f"   ℹ️ Готовы к обработке {pending_count} статей")
        logger.info("   ✅ Pipeline готов к запуску")
        
        return True
        
    except Exception as e:
        logger.error(f"   ❌ Ошибка тестирования pipeline: {e}")
        return False


async def main():
    """Основная функция тестирования"""
    logger.info("🚀 Тестирование системы AI News Parser с Supabase")
    logger.info("=" * 60)
    
    tests = [
        ("Environment", test_environment),
        ("Database Config", test_database_config), 
        ("Database Connection", test_database_connection),
        ("RSS Discovery", test_rss_discovery),
        ("Pending Articles", test_pending_articles),
        ("Continuous Pipeline", test_continuous_pipeline_dry_run)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            if asyncio.iscoroutinefunction(test_func):
                success = await test_func()
            else:
                success = test_func()
            
            results.append((test_name, success))
            
        except Exception as e:
            logger.error(f"❌ Тест '{test_name}' провален с исключением: {e}")
            results.append((test_name, False))
    
    # Финальный отчет
    logger.info("\n" + "=" * 60)
    logger.info("📊 ОТЧЕТ О ТЕСТИРОВАНИИ:")
    logger.info("=" * 60)
    
    passed = 0
    for test_name, success in results:
        status = "✅ ПРОЙДЕН" if success else "❌ ПРОВАЛЕН"
        logger.info(f"{status:12} {test_name}")
        if success:
            passed += 1
    
    logger.info(f"\nИТОГ: {passed}/{len(results)} тестов пройдено")
    
    if passed == len(results):
        logger.info("🎉 ВСЕ ТЕСТЫ ПРОЙДЕНЫ! Система готова к работе с Supabase")
        return True
    else:
        logger.warning("⚠️ Некоторые тесты провалены. Проверьте конфигурацию.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
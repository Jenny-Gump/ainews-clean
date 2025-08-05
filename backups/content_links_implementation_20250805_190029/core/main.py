#!/usr/bin/env python3
"""
AI News Parser - Extract API System
Полностью параллельная система на базе Firecrawl Extract API
Строго по 1 статье, с поддержкой всех функций логирования и мониторинга
"""
import argparse
import sys
import time
from datetime import datetime
from dotenv import load_dotenv
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
load_dotenv()

from core.database import Database
from core.config import Config
from app_logging import configure_logging, get_logger, LogContext

# Services imports
from services.content_parser import ContentParser
from services.rss_discovery import ExtractRSSDiscovery
from services.media_processor import ExtractMediaDownloaderPlaywright
from services.wordpress_publisher import WordPressPublisher

# Optional monitoring (graceful fallback if not available)
try:
    from monitoring.integration import MonitoringIntegration
    MONITORING_AVAILABLE = True
    # Shared monitoring database instance to prevent multiple connections
    _shared_monitoring_db = None
except ImportError as e:
    MonitoringIntegration = None
    MONITORING_AVAILABLE = False
    _shared_monitoring_db = None

def get_shared_monitoring_db():
    """Get shared monitoring database instance"""
    global _shared_monitoring_db
    if _shared_monitoring_db is None and MONITORING_AVAILABLE:
        from monitoring.database import MonitoringDatabase
        monitoring_db_path = str(Path(__file__).parent.parent / "data" / "monitoring.db")
        _shared_monitoring_db = MonitoringDatabase(monitoring_db_path)
    return _shared_monitoring_db

def parse_arguments():
    """Парсит аргументы командной строки для Extract API системы"""
    parser = argparse.ArgumentParser(
        description='AI News Parser - Extract API система (параллельная)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования Extract API системы:

🔄 EXTRACT API ПАРСИНГ (строго по 1 статье):
  python extract_system/main_extract.py --rss-full           # Полный цикл
  python extract_system/main_extract.py --rss-discover       # Phase 1: RSS поиск
  python extract_system/main_extract.py --parse-pending      # Phase 2: Extract парсинг
  
📊 УПРАВЛЕНИЕ:
  python extract_system/main_extract.py --list-sources       # Список источников
  python extract_system/main_extract.py --stats              # Статистика
  python extract_system/main_extract.py --cleanup            # Очистка

🚀 Рекомендуемый способ: python extract_system/main_extract.py --rss-full
        """
    )
    
    # Режимы работы (упрощенные для Extract API)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--run-once',
        action='store_true',
        help='Выполнить однократный полный цикл парсинга'
    )
    
    # Дополнительные опции
    parser.add_argument(
        '--list-sources',
        action='store_true',
        help='Показать список всех источников'
    )
    parser.add_argument(
        '--stats',
        action='store_true',
        help='Показать статистику по статьям и источникам'
    )
    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Очистить старые статьи (старше 30 дней)'
    )
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Количество дней для очистки (по умолчанию: 30)'
    )
    
    # Extract API парсинг (упрощенный - без batch лимитов)
    parser.add_argument(
        '--rss-discover',
        action='store_true',
        help='Phase 1: Discover new articles from RSS feeds (saves as pending)'
    )
    parser.add_argument(
        '--parse-pending',
        action='store_true',
        help='Phase 2: Parse content for pending articles using Extract API (строго по 1)'
    )
    parser.add_argument(
        '--rss-full',
        action='store_true',
        help='Run full RSS cycle: discovery + extract parsing (строго по 1)'
    )
    parser.add_argument(
        '--days-back',
        type=int, 
        default=7,
        help='Filter articles newer than N days (default: 7)'
    )
    
    # Медиа-обработка Extract API
    parser.add_argument(
        '--media-only',
        action='store_true',
        help='Download media for articles that have Extract API data'
    )
    parser.add_argument(
        '--media-stats',
        action='store_true',
        help='Показать статистику по медиа-файлам'
    )
    
    # WordPress publishing (Phase 4)
    parser.add_argument(
        '--wordpress-prepare',
        action='store_true',
        help='Phase 4: Prepare articles for WordPress publishing (translation and rewriting)'
    )
    parser.add_argument(
        '--wordpress-publish',
        action='store_true',
        help='Phase 5: Publish prepared articles to WordPress'
    )
    parser.add_argument(
        '--upload-media-to-wordpress',
        action='store_true',
        help='Upload media files to WordPress for published articles'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=10,
        help='Limit number of articles to process (default: 10)'
    )
    
    return parser.parse_args()


def setup_monitoring():
    """Настройка мониторинга (общая с основной системой)"""
    logger = get_logger('extract_system.main')
    monitoring = None
    
    if MONITORING_AVAILABLE:
        try:
            logger.debug("DEBUG: Creating MonitoringIntegration")
            monitoring = MonitoringIntegration()
            logger.info("Monitoring integration активирован для Extract API системы")
        except Exception as e:
            logger.warning(f"Не удалось инициализировать мониторинг: {e}")
            monitoring = None
    else:
        logger.info("Мониторинг отключен - работаем без него")
    
    return monitoring


async def run_rss_discovery():
    """
    Phase 1: RSS Discovery для Extract API системы
    Использует sources_extract.json
    """
    logger = get_logger('extract_system.discovery')
    
    with LogContext.operation("extract_rss_discovery", 
                             system="extract_api", 
                             phase=1):
        logger.info("Начинаем RSS Discovery для Extract API системы")
        
        # Get monitoring integration if available
        progress_tracker = None
        if MONITORING_AVAILABLE:
            try:
                from monitoring.parsing_tracker import ParsingProgressTracker
                monitoring_db = get_shared_monitoring_db()
                if monitoring_db:
                    progress_tracker = ParsingProgressTracker(monitoring_db)
                    progress_tracker.start()
                    logger.info("Progress tracking enabled for RSS discovery")
                else:
                    logger.warning("Could not initialize shared monitoring database")
            except Exception as e:
                logger.warning(f"Could not initialize progress tracker: {e}")
        
        discovery = ExtractRSSDiscovery()
        stats = await discovery.discover_from_sources(progress_tracker=progress_tracker)
        
        # Stop progress tracker
        if progress_tracker:
            progress_tracker.stop()
        
        logger.info(f"RSS Discovery завершен: {stats}")
        logger.info("===== RSS DISCOVERY PHASE COMPLETED =====")
        return stats


async def run_extract_parsing():
    """
    Phase 2: Extract API парсинг
    СТРОГО ПО 1 СТАТЬЕ с проверкой last_parsed
    """
    logger = get_logger('extract_system.parsing')
    
    with LogContext.operation("extract_api_parsing", 
                             system="extract_api", 
                             phase=2):
        logger.info("Начинаем Extract API парсинг (строго по 1 статье)")
        
        # Get monitoring integration if available
        progress_tracker = None
        if MONITORING_AVAILABLE:
            try:
                from monitoring.parsing_tracker import ParsingProgressTracker
                monitoring_db = get_shared_monitoring_db()
                if monitoring_db:
                    progress_tracker = ParsingProgressTracker(monitoring_db)
                    progress_tracker.start()
                    logger.info("Progress tracking enabled for content parsing")
                else:
                    logger.warning("Could not initialize shared monitoring database")
            except Exception as e:
                logger.warning(f"Could not initialize progress tracker: {e}")
        
        async with ContentParser() as parser:
            # Получаем pending статьи с учетом last_parsed - ЯВНО закрываем соединение
            db = Database()
            pending_articles = []
            
            # ВАЖНО: Используем отдельный блок с явным закрытием соединения
            logger.debug("DEBUG: Opening database connection to get pending articles")
            with db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT article_id, source_id, url, title 
                    FROM articles 
                    WHERE content_status = 'pending'
                    ORDER BY created_at ASC
                """)
                pending_articles = cursor.fetchall()
                logger.debug("DEBUG: Got pending articles from database")
            # Соединение с БД автоматически закрыто здесь
            
            logger.debug("DEBUG: Database connection closed, converting to list")
            pending_articles = [dict(row) for row in pending_articles]
            
            if not pending_articles:
                logger.info("Нет pending статей для парсинга")
                if progress_tracker:
                    progress_tracker.stop()
                return {"processed": 0, "successful": 0, "failed": 0}
            
            logger.info(f"Найдено {len(pending_articles)} pending статей для парсинга")
            logger.debug("DEBUG: IMMEDIATELY after finding pending articles - DB connection is closed")
            
            # Start content parsing phase
            logger.debug("DEBUG: About to start content parsing phase")
            if progress_tracker:
                logger.debug("DEBUG: Calling progress_tracker.start_phase")
                try:
                    progress_tracker.start_phase('content_parsing', len(pending_articles))
                    logger.debug("DEBUG: progress_tracker.start_phase completed successfully")
                except Exception as e:
                    logger.error(f"DEBUG ERROR: progress_tracker.start_phase failed: {e}")
                    raise
            else:
                logger.debug("DEBUG: No progress_tracker available")
            
            stats = {"processed": 0, "successful": 0, "failed": 0}
            
            # СТРОГО ПО 1 СТАТЬЕ
            logger.debug("DEBUG: Starting article processing loop")
            for article in pending_articles:
                logger.debug(f"DEBUG: Processing article {article['article_id']}")
                with LogContext.article(article_id=article['article_id'], 
                                      article_url=article['url'],
                                      article_title=article['title']):
                    try:
                        logger.info(f"Парсинг статьи: {article['title'][:50]}...")
                        
                        # Update progress tracker
                        if progress_tracker:
                            logger.debug("DEBUG: About to call progress_tracker.update_source")
                            source_name = article.get('source_id', 'Unknown')
                            progress_tracker.update_source(article['source_id'], source_name)
                            logger.debug("DEBUG: progress_tracker.update_source completed")
                            
                            logger.debug("DEBUG: About to call progress_tracker.update_pipeline_stage")
                            progress_tracker.update_pipeline_stage('parsing')
                            logger.debug("DEBUG: progress_tracker.update_pipeline_stage completed")
                        
                        result = await parser.parse_single_article(
                            article_id=article['article_id'],
                            url=article['url'],
                            source_id=article['source_id']
                        )
                        
                        stats["processed"] += 1
                        if result.get("success"):
                            stats["successful"] += 1
                            logger.info(f"Успешно спарсено: {article['title'][:50]}")
                            
                            if progress_tracker:
                                progress_tracker.update_phase_progress('content_parsing', {
                                    'processed_articles': 1,
                                    'successful': 1
                                })
                        else:
                            stats["failed"] += 1
                            logger.warning(f"Ошибка парсинга: {article['title'][:50]}")
                            
                            if progress_tracker:
                                progress_tracker.update_phase_progress('content_parsing', {
                                    'processed_articles': 1,
                                    'failed': 1
                                })
                        
                    except Exception as e:
                        stats["processed"] += 1
                        stats["failed"] += 1
                        logger.error(f"Исключение при парсинге {article['article_id']}: {e}")
                        
                        if progress_tracker:
                            progress_tracker.update_phase_progress('content_parsing', {
                                'processed_articles': 1,
                                'failed': 1
                            })
            
            # Complete content parsing phase
            if progress_tracker:
                progress_tracker.complete_phase('content_parsing')
                progress_tracker.stop()
            
            logger.info(f"Extract парсинг завершен: {stats}")
            logger.info("===== CONTENT PARSING PHASE COMPLETED =====")
            return stats


async def run_media_download():
    """
    Phase 3: Скачивание медиа для Extract API данных
    """
    logger = get_logger('extract_system.media')
    
    with LogContext.operation("extract_media_download", 
                             system="extract_api", 
                             phase=3):
        logger.info("Начинаем скачивание медиа для Extract API статей")
        
        # Используем Playwright версию для безопасного скачивания
        from services.media_processor import ExtractMediaDownloaderPlaywright
        
        async with ExtractMediaDownloaderPlaywright() as downloader:
            stats = await downloader.download_all_media()
        
        logger.info(f"Скачивание медиа завершено: {stats}")
        logger.info("===== MEDIA PROCESSING PHASE COMPLETED =====")
        return stats


async def run_full_extract_cycle():
    """
    Полный цикл Extract API системы:
    1. RSS Discovery
    2. Extract API парсинг (строго по 1)
    3. Скачивание медиа
    """
    logger = get_logger('extract_system.full_cycle')
    
    with LogContext.operation("extract_full_cycle", 
                             system="extract_api", 
                             phases="all"):
        logger.info("Запуск полного цикла Extract API системы")
        
        # Phase 1: RSS Discovery
        discovery_stats = await run_rss_discovery()
        
        # Phase 2: Extract API парсинг
        parsing_stats = await run_extract_parsing()
        
        # Phase 3: Медиа скачивание
        media_stats = await run_media_download()
        
        total_stats = {
            "discovery": discovery_stats,
            "parsing": parsing_stats,
            "media": media_stats
        }
        
        logger.info(f"Полный цикл Extract API завершен: {total_stats}")
        logger.info("===== FULL EXTRACT API CYCLE COMPLETED =====")
        return total_stats


async def run_wordpress_prepare(limit: int = 10):
    """
    Phase 4: WordPress preparation
    Translate and rewrite articles for WordPress publishing
    """
    logger = get_logger('extract_system.wordpress')
    
    with LogContext.operation("wordpress_prepare", 
                             system="extract_api", 
                             phase=4):
        logger.info(f"Начинаем подготовку статей для WordPress (лимит: {limit})")
        
        # Initialize WordPress publisher
        config = Config()
        db = Database()
        
        # Validate configuration
        config_errors = config.validate_config()
        if config_errors:
            logger.error(f"Ошибки конфигурации: {config_errors}")
            return {"error": "Configuration errors", "details": config_errors}
        
        publisher = WordPressPublisher(config, db)
        
        try:
            stats = publisher.process_articles_batch(limit=limit)
            logger.info(f"WordPress подготовка завершена: {stats}")
            logger.info("===== WORDPRESS PREPARATION PHASE COMPLETED =====")
            return stats
        except Exception as e:
            logger.error(f"Ошибка WordPress подготовки: {e}")
            return {"error": str(e)}


async def run_wordpress_publish(limit: int = 5):
    """
    Phase 5: WordPress publishing
    Publish translated articles to WordPress
    """
    logger = get_logger('extract_system.wordpress_publish')
    
    with LogContext.operation("wordpress_publish", 
                             system="extract_api", 
                             phase=5):
        logger.info(f"Начинаем публикацию статей в WordPress (лимит: {limit})")
        
        # Initialize WordPress publisher
        config = Config()
        db = Database()
        
        # Validate WordPress API configuration
        if not all([config.wordpress_api_url, 
                   config.wordpress_username, 
                   config.wordpress_app_password]):
            logger.error("WordPress API не настроен в .env файле")
            return {
                "error": "WordPress API not configured",
                "details": "Настройте WORDPRESS_API_URL, WORDPRESS_USERNAME и WORDPRESS_APP_PASSWORD в .env"
            }
        
        publisher = WordPressPublisher(config, db)
        
        try:
            stats = publisher.publish_to_wordpress(limit=limit)
            logger.info(f"WordPress публикация завершена: {stats}")
            logger.info("===== WORDPRESS PUBLISHING PHASE COMPLETED =====")
            return stats
        except Exception as e:
            logger.error(f"Ошибка WordPress публикации: {e}")
            return {"error": str(e)}


async def run_upload_media_to_wordpress(limit: int = 10):
    """
    Upload media files to WordPress for published articles
    """
    logger = get_logger('extract_system.wordpress_media')
    
    with LogContext.operation("wordpress_media_upload", 
                             system="extract_api", 
                             phase="media"):
        logger.info(f"Начинаем загрузку медиафайлов в WordPress (лимит: {limit})")
        
        # Initialize WordPress publisher
        config = Config()
        db = Database()
        
        # Validate WordPress API configuration
        if not all([config.wordpress_api_url, 
                   config.wordpress_username, 
                   config.wordpress_app_password]):
            logger.error("WordPress API не настроен в .env файле")
            return {
                "error": "WordPress API not configured",
                "details": "Настройте WORDPRESS_API_URL, WORDPRESS_USERNAME и WORDPRESS_APP_PASSWORD в .env"
            }
        
        publisher = WordPressPublisher(config, db)
        
        try:
            stats = publisher.upload_media_to_wordpress(limit=limit)
            logger.info(f"Загрузка медиафайлов завершена: {stats}")
            logger.info("===== WORDPRESS MEDIA UPLOAD COMPLETED =====")
            return stats
        except Exception as e:
            logger.error(f"Ошибка загрузки медиафайлов: {e}")
            return {"error": str(e)}


def show_sources():
    """Показать список источников для Extract API системы"""
    logger = get_logger('extract_system.sources')
    
    try:
        discovery = ExtractRSSDiscovery()
        sources = discovery.load_sources()
        
        logger.info(f"Extract API система источники: {len(sources)} шт.")
        
        # Log source information
        for source in sources:
            logger.info(f"Источник {source['id']}: {source['name']}", 
                       source_id=source['id'], 
                       source_name=source['name'],
                       rss_url=source.get('rss_url', 'N/A'))
        
        # Also provide user-friendly output
        logger.info(f"\n📋 Источники Extract API системы ({len(sources)} шт.):\n" + 
                   "=" * 60 + "\n" +
                   "\n".join([f"🔸 {source['id']}: {source['name']}\n   RSS: {source.get('rss_url', 'N/A')}" 
                             for source in sources]))
            
    except Exception as e:
        logger.error(f"Ошибка при загрузке источников: {e}")


def show_stats():
    """Показать статистику Extract API системы"""
    logger = get_logger('extract_system.stats')
    
    try:
        db = Database()
        with db.get_connection() as conn:
            # Статистика статей
            articles_stats = conn.execute("""
                SELECT 
                    content_status,
                    COUNT(*) as count
                FROM articles 
                GROUP BY content_status
            """).fetchall()
            
            # Статистика медиа
            media_stats = conn.execute("""
                SELECT 
                    COUNT(*) as total_media,
                    COUNT(CASE WHEN alt_text IS NOT NULL THEN 1 END) as with_metadata
                FROM media_files
            """).fetchall()
            
            # Статистика related_links
            related_stats = conn.execute("""
                SELECT COUNT(*) as total_related_links
                FROM related_links
            """).fetchone()
            
        print(f"\nСтатистика Extract API системы:")
        print("=" * 50)
        
        print("Статьи по статусам:")
        for stat in articles_stats:
            print(f"   {stat['content_status']}: {stat['count']}")
        
        if media_stats:
            media = media_stats[0]
            print(f"\n📸 Медиа-файлы:")
            print(f"   Всего: {media['total_media']}")
            print(f"   С метаданными: {media['with_metadata']}")
        
        if related_stats:
            print(f"\n🔗 Связанные ссылки: {related_stats['total_related_links']}")
            
    except Exception as e:
        logger.error(f"Ошибка при получении статистики: {e}")


def cleanup_old_articles(days=30):
    """Очистка старых статей (общая логика с основной системой)"""
    logger = get_logger('extract_system.cleanup')
    
    try:
        db = Database()
        with db.get_connection() as conn:
            # Удаляем статьи старше N дней
            result = conn.execute("""
                DELETE FROM articles 
                WHERE created_at < datetime('now', '-{} days')
            """.format(days))
            
            deleted_count = result.rowcount
            
        logger.info(f"Cleanup completed: removed {deleted_count} articles older than {days} days", 
                   deleted_count=deleted_count, cleanup_days=days)
        logger.info(f"🗑️ Удалено {deleted_count} статей старше {days} дней")
        
    except Exception as e:
        logger.error(f"Ошибка при очистке: {e}")


async def main():
    """Главная функция Extract API системы"""
    # Настройка логирования с префиксом extract_system
    configure_logging()
    
    logger = get_logger('extract_system.main')
    args = parse_arguments()
    
    # Настройка мониторинга
    monitoring = setup_monitoring()
    
    try:
        logger.info("Запуск Extract API системы")
        
        if args.list_sources:
            show_sources()
        elif args.stats:
            show_stats()
        elif args.cleanup:
            cleanup_old_articles(days=args.days)
        elif args.rss_discover:
            await run_rss_discovery()
        elif args.parse_pending:
            await run_extract_parsing()
        elif args.media_only:
            await run_media_download()
        elif args.rss_full or args.run_once:
            await run_full_extract_cycle()
        elif args.wordpress_prepare:
            await run_wordpress_prepare(limit=args.limit)
        elif args.wordpress_publish:
            await run_wordpress_publish(limit=args.limit)
        elif args.upload_media_to_wordpress:
            await run_upload_media_to_wordpress(limit=args.limit)
        else:
            logger.error("No operation mode specified. Use --help for available options")
            logger.info("Не указан режим работы. Используйте --help для справки")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Extract API система остановлена пользователем")
    except Exception as e:
        logger.error(f"Критическая ошибка Extract API системы: {e}")
        sys.exit(1)
    finally:
        logger.info("Extract API система завершена")


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
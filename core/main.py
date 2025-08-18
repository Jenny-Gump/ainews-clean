#!/usr/bin/env python3
"""
AI News Parser - Single Pipeline System
Единый пайплайн для обработки новостей об ИИ
"""
import argparse
import sys
import asyncio
import signal
from datetime import datetime
from dotenv import load_dotenv
import os
from pathlib import Path

# Добавляем родительскую директорию в path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Загружаем переменные окружения
load_dotenv()

from core.db_config import DatabaseConfig
from core.config import Config
from core.single_pipeline import SingleArticlePipeline
from app_logging import configure_logging, get_logger, LogContext, log_operation, log_error
from services.rss_discovery import ExtractRSSDiscovery
from change_tracking import ChangeMonitor

# Глобальная переменная для graceful shutdown
shutdown_requested = False

def signal_handler(signum, frame):
    """Обработчик сигналов для graceful shutdown"""
    global shutdown_requested
    shutdown_requested = True
    logger = get_logger('core.main')
    logger.info("\n⚠️ Получен сигнал остановки. Завершаем текущую операцию...")
    sys.exit(0)

def parse_arguments():
    """Парсинг аргументов командной строки"""
    parser = argparse.ArgumentParser(
        description='AI News Parser - Single Pipeline System',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ:

📡 RSS Discovery (поиск новых статей):
  python core/main.py --rss-discover

🔄 Continuous Pipeline (обработка ВСЕХ pending статей) - ОСНОВНОЙ РЕЖИМ:
  python core/main.py  # запуск без параметров = continuous-pipeline
  python core/main.py --continuous-pipeline
  python core/main.py --continuous-pipeline --max-articles 10
  python core/main.py --continuous-pipeline --delay-between 10

🔧 Обработка конкретной статьи:
  python core/main.py --process-article ARTICLE_ID


📊 Информация:
  python core/main.py --stats
  python core/main.py --list-sources

🔍 Change Tracking (мониторинг изменений):
  python core/main.py --change-tracking --scan --limit 5
  python core/main.py --change-tracking --stats
  python core/main.py --change-tracking --export

РЕКОМЕНДУЕМЫЙ WORKFLOW:
  1. python core/main.py --rss-discover  # Найти новые статьи
  2. python core/main.py  # Обработать ВСЕ статьи (continuous режим по умолчанию)
  
WORKFLOW С CHANGE TRACKING:
  1. python core/main.py --change-tracking --scan  # Сканировать изменения
  2. python core/main.py --change-tracking --export  # Экспорт в основной пайплайн
  3. python core/main.py  # Обработать ВСЕ (continuous режим по умолчанию)
        """
    )
    
    # Основные команды
    mode_group = parser.add_mutually_exclusive_group()
    
    mode_group.add_argument(
        '--rss-discover',
        action='store_true',
        help='Phase 1: Найти новые статьи из RSS лент'
    )
    
    
    mode_group.add_argument(
        '--continuous-pipeline',
        action='store_true',
        help='Непрерывная обработка ВСЕХ pending статей в цикле'
    )
    
    mode_group.add_argument(
        '--process-article',
        type=str,
        metavar='ARTICLE_ID',
        help='Обработать конкретную статью по ID'
    )
    
    # Информационные команды
    mode_group.add_argument(
        '--stats',
        action='store_true',
        help='Показать статистику системы'
    )
    
    mode_group.add_argument(
        '--list-sources',
        action='store_true',
        help='Показать список источников'
    )
    
    mode_group.add_argument(
        '--cleanup',
        action='store_true',
        help='Очистить старые статьи (старше 30 дней)'
    )
    
    # Change Tracking commands
    mode_group.add_argument(
        '--change-tracking',
        action='store_true',
        help='Режим отслеживания изменений на веб-страницах'
    )
    
    mode_group.add_argument(
        '--monitor-sessions',
        action='store_true',
        help='Показать активные сессии и заблокированные статьи'
    )
    
    # Дополнительные параметры
    parser.add_argument(
        '--days',
        type=int,
        default=30,
        help='Количество дней для cleanup (по умолчанию: 30)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='Лимит источников для сканирования (по умолчанию: все источники)'
    )
    
    parser.add_argument(
        '--max-articles',
        type=int,
        help='Максимум статей для обработки в continuous mode'
    )
    
    parser.add_argument(
        '--delay-between',
        type=int,
        default=5,
        help='Задержка между статьями в секундах (по умолчанию: 5)'
    )
    
    # Change tracking sub-commands
    parser.add_argument(
        '--scan',
        action='store_true',
        help='Сканировать источники на изменения (используется с --change-tracking)'
    )
    
    parser.add_argument(
        '--complete-scan',
        action='store_true',
        help='Завершить сканирование - только неотсканированные источники (используется с --change-tracking)'
    )
    
    parser.add_argument(
        '--export',
        action='store_true',
        help='Экспортировать изменения в основной пайплайн (используется с --change-tracking)'
    )
    
    parser.add_argument(
        '--tracking-stats',
        action='store_true', 
        help='Показать статистику отслеживания (используется с --change-tracking)'
    )
    
    parser.add_argument(
        '--batch-size',
        type=int,
        default=3,
        help='Размер батча для сканирования (по умолчанию: 3)'
    )
    
    parser.add_argument(
        '--extract-urls',
        action='store_true',
        help='Извлечь URL статей из отслеживаемых страниц (используется с --change-tracking)'
    )
    
    parser.add_argument(
        '--show-new-urls',
        action='store_true',
        help='Показать найденные новые URL (используется с --change-tracking)'
    )
    
    parser.add_argument(
        '--export-articles',
        action='store_true',
        help='Экспортировать новые URL в таблицу articles (используется с --change-tracking)'
    )
    
    parser.add_argument(
        '--export-changes',
        action='store_true',
        help='Экспортировать изменившиеся статьи в основную таблицу (используется с --change-tracking)'
    )
    
    return parser.parse_args()


async def run_rss_discovery():
    """Phase 1: RSS Discovery - поиск новых статей"""
    logger = get_logger('core.main')
    
    with LogContext.operation("rss_discovery", phase=1):
        logger.info("🔍 Начинаем поиск новых статей из RSS лент...")
        
        # Log start for dashboard
        log_operation('rss_discovery_start')
        
        discovery = ExtractRSSDiscovery()
        stats = await discovery.discover_from_sources()
        
        logger.info(f"✅ RSS Discovery завершен: {stats}")
        return stats


async def run_single_pipeline():
    """Запуск Single Pipeline - обработка ОДНОЙ статьи через все фазы"""
    logger = get_logger('core.main')
    
    with LogContext.operation("single_pipeline", phase="all"):
        logger.info("🚀 Запуск Single Pipeline (1 статья через все фазы)")
        
        # Log start for dashboard integration
        log_operation('single_pipeline_start')
        
        pipeline = SingleArticlePipeline()
        result = await pipeline.run_pipeline()
        
        if result.get('success'):
            logger.info(f"✅ Статья успешно обработана: {result.get('article_id')}")
            log_operation('single_pipeline_complete', 
                         success=True, 
                         article_id=result.get('article_id'))
        elif result.get('error') == 'No pending articles':
            logger.info("📭 Нет статей для обработки (все pending уже обработаны)")
            log_operation('single_pipeline_complete',
                         success=False,
                         reason='no_pending_articles')
        else:
            logger.warning(f"⚠️ Ошибка обработки: {result.get('error')}")
            log_operation('single_pipeline_complete',
                         success=False,
                         error=result.get('error'))
        
        return result



async def run_continuous_pipeline(max_articles=None, delay_between=5):
    """Запуск Continuous Pipeline - обработка ВСЕХ pending статей в цикле"""
    logger = get_logger('core.main')
    
    with LogContext.operation("continuous_pipeline", mode="continuous"):
        logger.info("🔄 Запуск CONTINUOUS Pipeline")
        logger.info(f"   Лимит статей: {max_articles if max_articles else 'без ограничений'}")
        logger.info(f"   Задержка между статьями: {delay_between} сек")
        logger.info("   Для остановки нажмите Ctrl+C")
        
        pipeline = SingleArticlePipeline()
        
        # Обработчик сигнала Ctrl+C для graceful shutdown
        def signal_handler(sig, frame):
            logger.info("\n⚠️ Получен сигнал остановки. Завершение после текущей статьи...")
            pipeline.request_stop()
        
        signal.signal(signal.SIGINT, signal_handler)
        
        try:
            # Запускаем пайплайн в continuous mode
            result = await pipeline.run_pipeline(
                continuous_mode=True,
                max_articles=max_articles,
                delay_between=delay_between
            )
        except Exception as e:
            logger.error(f"❌ Ошибка в пайплайне: {e}")
            # Логируем критическую ошибку пайплайна
            log_error('pipeline_fatal_error', str(e),
                     mode='continuous' if continuous else 'single',
                     module='main')
            result = {'processed_count': 0, 'success_count': 0, 'error_count': 1, 'wordpress_published': 0, 'duration_seconds': 0}
        
        # Выводим финальную статистику
        logger.info("\n" + "="*60)
        logger.info("📊 ФИНАЛЬНАЯ СТАТИСТИКА CONTINUOUS PIPELINE:")
        logger.info("="*60)
        logger.info(f"✅ Обработано статей: {result['processed_count']}")
        logger.info(f"   - Успешно: {result['success_count']}")
        logger.info(f"   - С ошибками: {result['error_count']}")
        logger.info(f"📰 Опубликовано в WordPress: {result['wordpress_published']}")
        logger.info(f"⏱️ Общее время: {result['duration_seconds']:.1f} сек ({result['duration_seconds']/60:.1f} мин)")
        if result['processed_count'] > 0:
            logger.info(f"⚡ Среднее время на статью: {result['duration_seconds']/result['processed_count']:.1f} сек")
        logger.info("="*60)
        
        # Детализация по фазам если есть
        if 'phase_stats' in result:
            logger.info("\n📈 Статистика по фазам:")
            for phase, stats in result['phase_stats'].items():
                logger.info(f"   {phase}: успех={stats['success']}, ошибки={stats['failed']}")
        
        return result



async def process_specific_article(article_id: str):
    """Обработка конкретной статьи по ID"""
    logger = get_logger('core.main')
    
    with LogContext.operation("process_specific", article_id=article_id):
        logger.info(f"🎯 Обработка конкретной статьи: {article_id}")
        
        pipeline = SingleArticlePipeline()
        
        # Получаем статью из БД
        db = DatabaseConfig.get_database()
        
        # Используем get_article для поиска статьи по ID
        try:
            article = db.get_article(article_id)
            
            if not article:
                logger.error(f"❌ Статья {article_id} не найдена")
                return {"success": False, "error": "Article not found"}
            
        except Exception as e:
            logger.error(f"❌ Ошибка при поиске статьи {article_id}: {e}")
            return {"success": False, "error": f"Database error: {e}"}
        
        # Обрабатываем через пайплайн
        result = await pipeline.process_single_article(article)
        
        if result['success']:
            logger.info(f"✅ Статья {article_id} успешно обработана")
        else:
            logger.error(f"❌ Ошибка при обработке {article_id}: {result.get('error')}")
        
        return result


def show_stats():
    """Показать статистику системы"""
    logger = get_logger('core.main')
    db = DatabaseConfig.get_database()
    
    # Используем методы database напрямую для совместимости
    stats = db.get_stats()
    
    logger.info("\n📊 СТАТИСТИКА СТАТЕЙ:")
    logger.info("-" * 40)
    
    # Статистика по статьям из готовых методов
    articles_by_status = stats.get('articles', {}).get('by_status', {})
    total = stats.get('articles', {}).get('total', 0)
    
    for status, count in articles_by_status.items():
        emoji = {
            'pending': '⏳',
            'parsed': '📄', 
            'published': '✅',
            'failed': '❌',
            'completed': '✅'
        }.get(status, '❓')
        logger.info(f"{emoji} {status:15} {count:5} статей")
    
    logger.info("-" * 40)
    logger.info(f"📚 ВСЕГО:           {total:5} статей\n")
    
    # ТОП источники (получаем через отдельный метод)
    try:
        top_sources = db.get_sources_with_stats()[:10]
    except:
        top_sources = []
    if top_sources:
        logger.info("📡 ТОП-10 ИСТОЧНИКОВ:")
        logger.info("-" * 60)
        logger.info(f"{'Источник':<30} {'Статей':>10} {'Рейтинг':<10}")
        logger.info("-" * 60)
        for source in top_sources:
            name = source.get('name', source.get('source_id', 'Unknown'))[:30]
            count = source.get('article_count', 0)
            rate = "N/A"
            logger.info(f"{name:<30} {count:>10} {rate:<10}")
    
    # Статистика по медиа
    media_by_status = stats.get('media', {}).get('by_status', {})
    if media_by_status:
        logger.info("\n🖼️ СТАТИСТИКА МЕДИАФАЙЛОВ:")
        logger.info("-" * 40)
        for status, count in media_by_status.items():
            logger.info(f"  {status:15} {count:5} файлов")
    
    # Общие счетчики
    logger.info(f"\n📈 ОБЩАЯ СТАТИСТИКА:")
    logger.info("-" * 40)
    logger.info(f"  Источников:      {stats.get('sources', 0):5}")
    logger.info(f"  Статей:          {stats.get('articles', {}).get('total', 0):5}")
    logger.info(f"  Медиафайлов:     {stats.get('media', {}).get('total', 0):5}")


def show_sources():
    """Показать список источников"""
    logger = get_logger('core.main')
    db = DatabaseConfig.get_database()
    
    # Используем метод get_sources_with_stats для получения источников со статистикой
    sources_with_stats = db.get_sources_with_stats()
    
    logger.info("\n📡 ИСТОЧНИКИ НОВОСТЕЙ:")
    logger.info("=" * 80)
    
    # Группируем по категориям
    sources_by_category = {}
    for source in sources_with_stats:
        category = source.get('category', 'Uncategorized')
        if category not in sources_by_category:
            sources_by_category[category] = []
        sources_by_category[category].append(source)
    
    # Выводим по категориям
    for category, sources in sorted(sources_by_category.items()):
        logger.info(f"\n{category}:")
        logger.info("-" * 80)
        
        for source in sorted(sources, key=lambda x: x.get('name', '')):
            name = source.get('name', 'Unknown')[:30]
            article_count = source.get('article_count', 0)
            url = source.get('url', '')[:70]
            logger.info(f"📡 {name:<30} [{article_count:>3} статей]")
            logger.info(f"   {url}")


def cleanup_old_articles(days: int = 30):
    """Очистка старых статей"""
    logger = get_logger('core.main')
    db = DatabaseConfig.get_database()
    
    # Подсчитываем сколько удалим используя _execute_sql
    try:
        count_result = db._execute_sql(
            "SELECT COUNT(*) as count FROM articles WHERE created_at < datetime('now', ? || ' days')",
            [-days]
        )
        
        count = count_result[0]['count'] if count_result else 0
        
        if count == 0:
            logger.info(f"Нет статей старше {days} дней для удаления")
            return
        
        # Удаляем старые статьи
        db._execute_sql(
            "DELETE FROM articles WHERE created_at < datetime('now', ? || ' days')",
            [-days]
        )
        
        # Удаляем осиротевшие медиафайлы
        db._execute_sql(
            "DELETE FROM media_files WHERE article_id NOT IN (SELECT article_id FROM articles)",
            []
        )
        
        # Удаляем осиротевшие WordPress статьи (если таблица существует)
        try:
            db._execute_sql(
                "DELETE FROM wordpress_articles WHERE article_id NOT IN (SELECT article_id FROM articles)",
                []
            )
        except Exception as e:
            logger.warning(f"WordPress articles cleanup skipped: {e}")
        
        # VACUUM для оптимизации (может не поддерживаться в Supabase)
        try:
            db._execute_sql("VACUUM", [])
        except Exception as e:
            logger.warning(f"VACUUM operation skipped: {e}")
        
        logger.info(f"✅ Удалено {count} статей старше {days} дней")
        logger.info(f"✅ Очистка завершена: удалено {count} статей")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при очистке статей: {e}")
        raise


async def run_change_tracking(args):
    """Запуск модуля отслеживания изменений"""
    logger = get_logger('core.main')
    
    if args.scan or args.complete_scan:
        # Сканирование источников
        scan_type = "complete" if args.complete_scan else "regular"
        with LogContext.operation("change_tracking_scan", scan_type=scan_type):
            
            if args.complete_scan:
                logger.info("🎯 Завершаем сканирование - только неотсканированные источники...")
                monitor = ChangeMonitor()
                results = await monitor.scan_sources_batch(
                    batch_size=args.batch_size,
                    only_unscanned=True
                )
            else:
                logger.info("🔍 Начинаем сканирование источников на изменения...")
                monitor = ChangeMonitor()
                results = await monitor.scan_sources_batch(
                    batch_size=args.batch_size,
                    limit=args.limit
                )
            
            # Показываем результаты
            logger.info(f"\n📊 РЕЗУЛЬТАТЫ СКАНИРОВАНИЯ:")
            logger.info("=" * 60)
            logger.info(f"  📋 Всего проверено: {results['total']}")
            logger.info(f"  🆕 Новых страниц:   {results['new']}")
            logger.info(f"  🔄 Изменений:       {results['changed']}")
            logger.info(f"  ⚪ Без изменений:   {results['unchanged']}")
            logger.info(f"  ❌ Ошибок:         {results['errors']}")
            
            # Детали новых и измененных
            new_and_changed = [
                d for d in results['details'] 
                if d['status'] in ['new', 'changed']
            ]
            
            if new_and_changed:
                logger.info(f"\n🔥 ОБНАРУЖЕНЫ ИЗМЕНЕНИЯ ({len(new_and_changed)}):")
                logger.info("-" * 60)
                for i, detail in enumerate(new_and_changed[:10], 1):
                    status_icon = '🆕' if detail['status'] == 'new' else '🔄'
                    url_short = detail['url'][:50] + '...' if len(detail['url']) > 50 else detail['url']
                    logger.info(f"  {i:2}. {status_icon} {url_short}")
                    if detail.get('article_id'):
                        logger.info(f"      📝 ID: {detail['article_id']}")
                
                if len(new_and_changed) > 10:
                    logger.info(f"      ... и ещё {len(new_and_changed) - 10}")
            
            # Показываем ошибки
            errors = [d for d in results['details'] if d['status'] == 'error']
            if errors:
                logger.info(f"\n❌ ОШИБКИ ({len(errors)}):")
                for i, detail in enumerate(errors[:5], 1):
                    url_short = detail['url'][:50] + '...' if len(detail['url']) > 50 else detail['url']
                    error_short = detail.get('error', '')[:80] + '...' if len(detail.get('error', '')) > 80 else detail.get('error', '')
                    logger.info(f"  {i}. {url_short}")
                    logger.info(f"     💥 {error_short}")
    
    elif args.export:
        # Экспорт изменений в основной пайплайн
        with LogContext.operation("change_tracking_export"):
            logger.info("📤 Экспорт изменений в основной пайплайн...")
            
            monitor = ChangeMonitor()
            changed_articles = monitor.get_changed_articles()
            
            if not changed_articles:
                logger.info("ℹ️ Нет изменений для экспорта")
                return
            
            logger.info(f"🔄 Найдено {len(changed_articles)} статей с изменениями:")
            for article in changed_articles[:5]:
                logger.info(f"  📄 {article['title'][:60]}...")
                logger.info(f"      🌐 {article['url'][:70]}...")
            
            if len(changed_articles) > 5:
                logger.info(f"  ... и ещё {len(changed_articles) - 5}")
            
            # Export functionality removed - use change_tracking module
            logger.info("⚠️ Экспорт в основной пайплайн пока не реализован")
            logger.info("💡 Статьи остаются в таблице tracked_articles")
    
    elif args.tracking_stats or not (args.scan or args.complete_scan or args.export or args.extract_urls or args.show_new_urls or args.export_articles or args.export_changes):
        # Показать статистику (по умолчанию)
        with LogContext.operation("change_tracking_stats"):
            logger.info("📊 СТАТИСТИКА ОТСЛЕЖИВАНИЯ ИЗМЕНЕНИЙ")
            logger.info("=" * 60)
            
            monitor = ChangeMonitor()
            stats = monitor.get_tracking_stats()
            
            if 'error' in stats:
                logger.error(f"❌ Ошибка получения статистики: {stats['error']}")
                return
            
            # Общая статистика
            logger.info(f"📋 Всего отслеживается: {stats.get('total_tracked', 0)} страниц")
            
            # По статусам
            if stats.get('by_status'):
                logger.info(f"\n📈 ПО СТАТУСАМ:")
                status_icons = {
                    'new': '🆕',
                    'changed': '🔄', 
                    'unchanged': '⚪',
                    'unknown': '❓'
                }
                for status, count in stats['by_status'].items():
                    icon = status_icons.get(status, '📄')
                    logger.info(f"  {icon} {status.upper():12}: {count:4} страниц")
            
            # По источникам (топ 10)
            if stats.get('by_source'):
                logger.info(f"\n🌐 ТОП ИСТОЧНИКИ:")
                sorted_sources = sorted(
                    stats['by_source'].items(), 
                    key=lambda x: x[1], 
                    reverse=True
                )
                for i, (source, count) in enumerate(sorted_sources[:10], 1):
                    logger.info(f"  {i:2}. {source:25} {count:3} страниц")
            
            # Последние изменения
            if stats.get('recent_changes'):
                logger.info(f"\n🔥 ПОСЛЕДНИЕ ИЗМЕНЕНИЯ:")
                for i, change in enumerate(stats['recent_changes'][:5], 1):
                    status_icon = '🆕' if change['status'] == 'new' else '🔄'
                    url_short = change['url'][:45] + '...' if len(change['url']) > 45 else change['url']
                    logger.info(f"  {i}. {status_icon} {url_short}")
                    logger.info(f"     ⏰ {change['checked']}")
    
    elif args.extract_urls:
        # Извлечение URL из отслеживаемых страниц
        with LogContext.operation("change_tracking_extract_urls"):
            logger.info("🔗 Извлечение URL статей из отслеживаемых страниц...")
            
            monitor = ChangeMonitor()
            results = await monitor.extract_urls_from_all_tracked(limit=args.limit)
            
            logger.info(f"\n📊 РЕЗУЛЬТАТЫ ИЗВЛЕЧЕНИЯ URL:")
            logger.info("=" * 60)
            logger.info(f"  📋 Обработано страниц: {results['processed']}")
            logger.info(f"  🔗 Найдено новых URL:  {results['new_urls']}")
            
            if results.get('error'):
                logger.error(f"❌ Ошибка: {results['error']}")
            else:
                logger.info(f"✅ {results.get('message', 'Извлечение завершено')}")
    
    elif args.show_new_urls:
        # Показать новые найденные URL
        with LogContext.operation("change_tracking_show_urls"):
            logger.info("📋 НОВЫЕ НАЙДЕННЫЕ URL")
            logger.info("=" * 80)
            
            monitor = ChangeMonitor()
            url_stats = monitor.get_url_extraction_stats()
            
            if url_stats.get('error'):
                logger.error(f"❌ Ошибка получения статистики: {url_stats['error']}")
                return
            
            logger.info(f"📊 СТАТИСТИКА URL:")
            logger.info(f"  🔗 Всего найдено:      {url_stats.get('total_urls', 0)}")
            logger.info(f"  🆕 Новых:              {url_stats.get('new_urls', 0)}")
            logger.info(f"  📤 Экспортировано:     {url_stats.get('exported_urls', 0)}")
            logger.info(f"  ⏳ Ожидает экспорта:   {url_stats.get('pending_export', 0)}")
            
            # Показать топ доменов
            if url_stats.get('top_domains'):
                logger.info(f"\n🌐 ТОП ДОМЕНЫ:")
                for i, (domain, count) in enumerate(list(url_stats['top_domains'].items())[:10], 1):
                    logger.info(f"  {i:2}. {domain:25} {count:3} URL")
            
            # Показать последние URL
            if url_stats.get('recent_urls'):
                logger.info(f"\n🔥 ПОСЛЕДНИЕ НАЙДЕННЫЕ URL:")
                for i, url_data in enumerate(url_stats['recent_urls'][:5], 1):
                    title = url_data['title'][:50] + '...' if len(url_data['title']) > 50 else url_data['title']
                    logger.info(f"  {i}. {title}")
                    logger.info(f"     🌐 {url_data['url'][:70]}...")
                    logger.info(f"     📅 {url_data['discovered']}")
    
    elif args.export_articles:
        # Экспорт новых URL в таблицу articles
        with LogContext.operation("change_tracking_export_articles"):
            logger.info("📤 Экспорт новых URL в таблицу articles...")
            
            monitor = ChangeMonitor()
            results = monitor.export_new_urls_to_articles(limit=args.limit)
            
            logger.info(f"\n📊 РЕЗУЛЬТАТЫ ЭКСПОРТА:")
            logger.info("=" * 60)
            logger.info(f"  📤 Экспортировано:     {results['exported']}")
            
            if 'total_available' in results:
                logger.info(f"  📋 Было доступно:      {results['total_available']}")
            
            if results.get('error'):
                logger.error(f"❌ Ошибка: {results['error']}")
            else:
                logger.info(f"✅ {results.get('message', 'Экспорт завершен')}")
                
                if results['exported'] > 0:
                    logger.info(f"\n💡 СЛЕДУЮЩИЙ ШАГ:")
                    logger.info(f"   Для обработки экспортированных статей используйте:")
                    logger.info(f"   python core/main.py --single-pipeline")
    
    elif args.export_changes:
        # Экспорт изменившихся статей из tracked_articles
        with LogContext.operation("change_tracking_export_changes"):
            logger.info("📤 Экспорт изменившихся статей в основную таблицу...")
            
            monitor = ChangeMonitor()
            results = monitor.export_changed_articles(limit=args.limit)
            
            logger.info(f"\n📊 РЕЗУЛЬТАТЫ ЭКСПОРТА ИЗМЕНЕНИЙ:")
            logger.info("=" * 60)
            logger.info(f"  📤 Экспортировано:     {results['exported']}")
            
            if 'total_available' in results:
                logger.info(f"  📋 Было доступно:      {results['total_available']}")
            
            if results.get('error'):
                logger.error(f"❌ Ошибка: {results['error']}")
            else:
                logger.info(f"✅ {results.get('message', 'Экспорт завершен')}")
                
                if results['exported'] > 0:
                    logger.info(f"\n💡 СЛЕДУЮЩИЙ ШАГ:")
                    logger.info(f"   Для обработки экспортированных статей используйте:")
                    logger.info(f"   python core/main.py --continuous-pipeline")
    
    else:
        logger.info("❌ Неизвестная команда для --change-tracking")
        logger.info("💡 Используйте: --scan, --complete-scan, --export, --tracking-stats,")
        logger.info("    --extract-urls, --show-new-urls, --export-articles, или --export-changes")


async def run_monitoring(rss_url: str, limit: int = 20):
    """Мониторинг изменений в RSS источнике"""
    logger = get_logger('core.main')
    
    with LogContext.operation("change_monitoring", source=rss_url):
        logger.info(f"🔍 Начинаем мониторинг источника: {rss_url}")
        
        monitor = ChangeMonitor()
        results = await monitor.scan_source(rss_url, limit)
        
        # Показать результаты
        logger.info(f"\n🔍 РЕЗУЛЬТАТЫ МОНИТОРИНГА: {rss_url}")
        logger.info("=" * 80)
        
        logger.info(f"📊 СТАТИСТИКА:")
        logger.info(f"  ✅ Новых статей:     {len(results['new'])}")
        logger.info(f"  🔄 Измененных:       {len(results['changed'])}")
        logger.info(f"  ⚪ Без изменений:    {len(results['unchanged'])}")
        logger.info(f"  ❌ Ошибок:          {len(results['errors'])}")
        
        if results['new']:
            logger.info(f"\n📰 НОВЫЕ СТАТЬИ ({len(results['new'])}):")
            logger.info("-" * 80)
            for i, article in enumerate(results['new'][:10], 1):  # Показываем первые 10
                title = article['title'][:70]
                article_id = article['article_id'][:8]
                logger.info(f"{i:2}. [{article_id}] {title}")
            
            if len(results['new']) > 10:
                logger.info(f"    ... и ещё {len(results['new']) - 10} статей")
        
        if results['changed']:
            logger.info(f"\n🔄 ИЗМЕНЕННЫЕ СТАТЬИ ({len(results['changed'])}):")
            logger.info("-" * 80)
            for i, article in enumerate(results['changed'][:5], 1):  # Показываем первые 5
                title = article['title'][:70]
                article_id = article['article_id'][:8]
                logger.info(f"{i:2}. [{article_id}] {title}")
                
            if len(results['changed']) > 5:
                logger.info(f"    ... и ещё {len(results['changed']) - 5} статей")
        
        if results['errors']:
            logger.info(f"\n❌ ОШИБКИ ({len(results['errors'])}):")
            logger.info("-" * 80)
            for error in results['errors'][:3]:  # Показываем первые 3
                url = error.get('url', 'unknown')[:50]
                error_msg = error.get('error', 'unknown')[:50]
                logger.info(f"  • {url}: {error_msg}")
        
        total_detected = len(results['new']) + len(results['changed'])
        if total_detected > 0:
            logger.info(f"\n💡 СЛЕДУЮЩИЙ ШАГ:")
            logger.info(f"   Для экспорта найденных изменений в основную БД используйте:")
            logger.info(f"   python core/main.py --export-tracked --all")
        
        logger.info(f"✅ Мониторинг завершен: {total_detected} изменений найдено")
        return results


async def export_tracked_articles(export_all: bool = False, article_ids: str = None):
    """Экспорт отслеживаемых статей в основную БД"""
    logger = get_logger('core.main')
    
    with LogContext.operation("export_tracked"):
        logger.info("📤 Начинаем экспорт отслеживаемых статей...")
        
        monitor = ChangeMonitor()
        
        # Подготовить список ID
        ids_list = None
        if article_ids:
            ids_list = [id.strip() for id in article_ids.split(',')]
            logger.info(f"Экспорт конкретных статей: {len(ids_list)} ID")
        elif export_all:
            logger.info("Экспорт всех новых/измененных статей")
        else:
            # Показать список доступных для экспорта
            pending = monitor.get_pending_export(limit=20)
            if not pending:
                logger.info("📭 Нет статей для экспорта")
                return
            
            logger.info(f"\n📋 СТАТЬИ ДОСТУПНЫЕ ДЛЯ ЭКСПОРТА ({len(pending)}):")
            logger.info("=" * 80)
            for i, article in enumerate(pending, 1):
                title = article['title'][:60]
                article_id = article['article_id'][:8]
                status = article['change_status']
                logger.info(f"{i:2}. [{article_id}] {status:8} {title}")
            
            logger.info(f"\n💡 ДЛЯ ЭКСПОРТА ИСПОЛЬЗУЙТЕ:")
            logger.info(f"   --export-tracked --all  (экспортировать все)")
            logger.info(f"   --export-tracked --ids ID1,ID2,ID3  (конкретные)")
            return
        
        # Выполнить экспорт
        results = await monitor.export_to_main(ids_list)
        
        # Показать результаты
        logger.info(f"\n📤 РЕЗУЛЬТАТЫ ЭКСПОРТА:")
        logger.info("=" * 50)
        logger.info(f"✅ Экспортировано:     {results['total_exported']} статей")
        logger.info(f"⚠️ Дублей пропущено:   {len(results['duplicates'])} статей")
        logger.info(f"❌ Ошибок:            {len(results['errors'])} статей")
        
        if results['exported']:
            logger.info(f"\n📰 ЭКСПОРТИРОВАННЫЕ СТАТЬИ:")
            logger.info("-" * 60)
            for article in results['exported'][:10]:  # Показываем первые 10
                title = article['title'][:50]
                new_id = article['new_id'][:8]
                logger.info(f"  [{new_id}] {title}")
            
            if len(results['exported']) > 10:
                logger.info(f"    ... и ещё {len(results['exported']) - 10} статей")
        
        if results['duplicates']:
            logger.info(f"\n⚠️ ДУБЛИ ПРОПУЩЕНЫ:")
            logger.info("-" * 60)
            for dup in results['duplicates'][:5]:  # Показываем первые 5
                title = dup['title'][:50]
                existing_id = dup['existing_id'][:8]
                logger.info(f"  [{existing_id}] {title}")
        
        if results['errors']:
            logger.info(f"\n❌ ОШИБКИ:")
            logger.info("-" * 60)
            for error in results['errors'][:3]:
                title = error.get('title', 'unknown')[:40]
                error_msg = error.get('error', 'unknown')[:30]
                logger.info(f"  {title}: {error_msg}")
        
        if results['total_exported'] > 0:
            logger.info(f"\n💡 СЛЕДУЮЩИЙ ШАГ:")
            logger.info(f"   Для обработки экспортированных статей используйте:")
            logger.info(f"   python core/main.py --single-pipeline")
        
        logger.info(f"✅ Экспорт завершен: {results['total_exported']} статей")
        return results


def show_tracking_stats():
    """Показать статистику отслеживания"""
    monitor = ChangeMonitor()
    stats = monitor.get_tracking_stats()
    
    logger.info(f"\n📊 СТАТИСТИКА ОТСЛЕЖИВАНИЯ:")
    logger.info("=" * 50)
    logger.info(f"📚 Всего отслеживается:   {stats['total_tracked']} статей")
    logger.info(f"📤 Ожидают экспорта:      {stats['pending_export']} статей")
    
    if stats['by_status']:
        logger.info(f"\n🔍 ПО СТАТУСУ ИЗМЕНЕНИЙ:")
        logger.info("-" * 40)
        for status, count in stats['by_status'].items():
            emoji = {
                'new': '🆕',
                'changed': '🔄',
                'unchanged': '⚪'
            }.get(status, '❓')
            logger.info(f"{emoji} {status:12} {count:5} статей")
    
    if stats['by_source']:
        logger.info(f"\n📡 ПО ИСТОЧНИКАМ:")
        logger.info("-" * 50)
        for source_id, count in sorted(stats['by_source'].items(), 
                                       key=lambda x: x[1], reverse=True)[:10]:
            logger.info(f"📡 {source_id:<25} {count:5} статей")
    
    # Показать список ожидающих экспорта
    if stats['pending_export'] > 0:
        pending = monitor.get_pending_export(limit=5)
        logger.info(f"\n📋 ПОСЛЕДНИЕ ИЗМЕНЕНИЯ (топ-5):")
        logger.info("-" * 70)
        for article in pending:
            title = article['title'][:50]
            status = article['change_status']
            last_checked = article['last_checked'][:19] if article['last_checked'] else 'unknown'
            logger.info(f"🔄 {status:8} {last_checked} {title}")


async def main():
    """Главная функция"""
    # Настройка обработчиков сигналов
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Настройка логирования
    configure_logging()
    logger = get_logger('core.main')
    
    # Парсинг аргументов
    args = parse_arguments()
    
    try:
        logger.info("🚀 AI News Parser - Single Pipeline System")
        
        # Выполнение команд
        if args.rss_discover:
            await run_rss_discovery()
            
        elif args.continuous_pipeline:
            # Запуск continuous mode с параметрами
            await run_continuous_pipeline(
                max_articles=args.max_articles,
                delay_between=args.delay_between
            )
            
        elif args.process_article:
            await process_specific_article(args.process_article)
            
        elif args.stats:
            show_stats()
            
        elif args.list_sources:
            show_sources()
            
        elif args.cleanup:
            cleanup_old_articles(args.days)
            
        elif args.change_tracking:
            await run_change_tracking(args)
            
        else:
            # По умолчанию запускаем continuous-pipeline
            logger.info("🔄 Запуск по умолчанию: continuous-pipeline")
            await run_continuous_pipeline()
            
    except KeyboardInterrupt:
        logger.info("⚠️ Остановлено пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
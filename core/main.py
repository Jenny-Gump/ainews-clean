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

from core.database import Database
from core.config import Config
from core.single_pipeline import SingleArticlePipeline
from app_logging import configure_logging, get_logger, LogContext
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

🚀 Single Pipeline (обработка 1 статьи через все фазы):
  python core/main.py --single-pipeline

🔄 Continuous Pipeline (обработка ВСЕХ pending статей):
  python core/main.py --continuous-pipeline
  python core/main.py --continuous-pipeline --max-articles 10
  python core/main.py --continuous-pipeline --delay-between 10

🔧 Обработка конкретной статьи:
  python core/main.py --process-article ARTICLE_ID

⚡ Параллельная обработка:
  python core/main.py --parallel-workers 3
  python core/main.py --parallel-workers 3 --max-articles 20

📊 Информация:
  python core/main.py --stats
  python core/main.py --list-sources
  python core/main.py --monitor-sessions

🔍 Change Tracking (мониторинг изменений):
  python core/main.py --change-tracking --scan --limit 5
  python core/main.py --change-tracking --stats
  python core/main.py --change-tracking --export

РЕКОМЕНДУЕМЫЙ WORKFLOW:
  1. python core/main.py --rss-discover  # Найти новые статьи
  2. python core/main.py --continuous-pipeline  # Обработать ВСЕ статьи
  
АЛЬТЕРНАТИВНЫЙ WORKFLOW (по одной):
  1. python core/main.py --rss-discover  # Найти новые статьи
  2. python core/main.py --single-pipeline  # Обработать 1 статью
  3. Повторить шаг 2 для обработки следующих статей
  
WORKFLOW С CHANGE TRACKING:
  1. python core/main.py --change-tracking --scan  # Сканировать изменения
  2. python core/main.py --change-tracking --export  # Экспорт в основной пайплайн
  3. python core/main.py --continuous-pipeline  # Обработать ВСЕ
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
        '--single-pipeline',
        action='store_true',
        help='Обработать ОДНУ статью через все фазы (2-5)'
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
    
    # Параллельные воркеры
    parser.add_argument(
        '--parallel-workers',
        type=int,
        metavar='N',
        help='Запуск N параллельных воркеров для обработки статей'
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
        default=5,
        help='Лимит источников для сканирования (по умолчанию: 5)'
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
    
    return parser.parse_args()


async def run_rss_discovery():
    """Phase 1: RSS Discovery - поиск новых статей"""
    logger = get_logger('core.main')
    
    with LogContext.operation("rss_discovery", phase=1):
        logger.info("🔍 Начинаем поиск новых статей из RSS лент...")
        
        discovery = ExtractRSSDiscovery()
        stats = await discovery.discover_from_sources()
        
        logger.info(f"✅ RSS Discovery завершен: {stats}")
        return stats


async def run_single_pipeline():
    """Запуск Single Pipeline - обработка ОДНОЙ статьи через все фазы"""
    logger = get_logger('core.main')
    
    with LogContext.operation("single_pipeline", phase="all"):
        logger.info("🚀 Запуск Single Pipeline (1 статья через все фазы)")
        
        pipeline = SingleArticlePipeline()
        result = await pipeline.run_pipeline()
        
        if result.get('success'):
            logger.info(f"✅ Статья успешно обработана: {result.get('article_id')}")
        elif result.get('error') == 'No pending articles':
            logger.info("📭 Нет статей для обработки (все pending уже обработаны)")
        else:
            logger.warning(f"⚠️ Ошибка обработки: {result.get('error')}")
        
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
        
        # Запускаем пайплайн в continuous mode
        result = await pipeline.run_pipeline(
            continuous_mode=True,
            max_articles=max_articles,
            delay_between=delay_between
        )
        
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


async def run_parallel_workers(num_workers: int, max_articles: int = None, delay_between: int = 5):
    """Запуск нескольких параллельных воркеров для обработки статей"""
    logger = get_logger('core.main')
    
    with LogContext.operation("parallel_workers", num_workers=num_workers):
        logger.info("⚡ Запуск параллельных воркеров")
        logger.info(f"   Количество воркеров: {num_workers}")
        logger.info(f"   Лимит статей на воркер: {max_articles if max_articles else 'без ограничений'}")
        logger.info(f"   Задержка между статьями: {delay_between} сек")
        logger.info("   Для остановки нажмите Ctrl+C")
        
        # Создаем задачи для каждого воркера
        tasks = []
        for worker_num in range(num_workers):
            worker_id = f"worker_{worker_num + 1}"
            task = asyncio.create_task(
                run_single_worker(worker_id, max_articles, delay_between),
                name=f"Worker-{worker_id}"
            )
            tasks.append(task)
        
        # Graceful shutdown handler
        stop_event = asyncio.Event()
        
        def signal_handler(sig, frame):
            logger.info("\n⚠️ Получен сигнал остановки. Завершение всех воркеров...")
            stop_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        
        # Запускаем все воркеры параллельно
        try:
            # Ждем либо завершения всех задач, либо сигнала остановки
            done, pending = await asyncio.wait(
                tasks + [asyncio.create_task(stop_event.wait())],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            # Если получен сигнал остановки, отменяем все задачи
            if stop_event.is_set():
                logger.info("Отменяем все активные воркеры...")
                for task in pending:
                    task.cancel()
                
                # Ждем завершения отмененных задач
                await asyncio.gather(*pending, return_exceptions=True)
            
        except KeyboardInterrupt:
            logger.info("Прерывание работы...")
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        
        # Собираем статистику от всех воркеров
        total_processed = 0
        total_success = 0
        total_errors = 0
        total_published = 0
        
        for task in tasks:
            if task.done() and not task.cancelled():
                try:
                    result = task.result()
                    if result:
                        total_processed += result.get('processed_count', 0)
                        total_success += result.get('success_count', 0)
                        total_errors += result.get('error_count', 0)
                        total_published += result.get('wordpress_published', 0)
                except Exception as e:
                    logger.error(f"Ошибка получения результата от воркера: {e}")
        
        # Выводим финальную статистику
        logger.info("\n" + "="*60)
        logger.info("📊 ФИНАЛЬНАЯ СТАТИСТИКА ПАРАЛЛЕЛЬНЫХ ВОРКЕРОВ:")
        logger.info("="*60)
        logger.info(f"👥 Количество воркеров: {num_workers}")
        logger.info(f"✅ Всего обработано: {total_processed} статей")
        logger.info(f"   - Успешно: {total_success}")
        logger.info(f"   - С ошибками: {total_errors}")
        logger.info(f"📰 Опубликовано в WordPress: {total_published}")
        logger.info("="*60)
        
        return {
            'num_workers': num_workers,
            'total_processed': total_processed,
            'total_success': total_success,
            'total_errors': total_errors,
            'wordpress_published': total_published
        }


async def run_single_worker(worker_id: str, max_articles: int = None, delay_between: int = 5):
    """Отдельный воркер для обработки статей"""
    logger = get_logger(f'core.worker.{worker_id}')
    
    logger.info(f"🚀 Запуск воркера {worker_id}")
    
    # Каждый воркер создает свой пайплайн с уникальной сессией
    pipeline = SingleArticlePipeline()
    
    # Добавляем worker_id в session_manager для уникальности
    pipeline.session_manager.worker_id_suffix = f"_{worker_id}"
    
    try:
        # Запускаем пайплайн в continuous mode
        result = await pipeline.run_pipeline(
            continuous_mode=True,
            max_articles=max_articles,
            delay_between=delay_between
        )
        
        logger.info(f"✅ Воркер {worker_id} завершил работу: {result['processed_count']} статей")
        return result
        
    except asyncio.CancelledError:
        logger.info(f"⏹️ Воркер {worker_id} был остановлен")
        return {
            'processed_count': pipeline.processed_count,
            'success_count': pipeline.success_count,
            'error_count': pipeline.error_count,
            'wordpress_published': pipeline.wordpress_published
        }
    except Exception as e:
        logger.error(f"❌ Воркер {worker_id} завершился с ошибкой: {e}")
        return {
            'processed_count': pipeline.processed_count,
            'success_count': pipeline.success_count, 
            'error_count': pipeline.error_count,
            'wordpress_published': pipeline.wordpress_published
        }


def show_session_monitoring():
    """Показать информацию об активных сессиях и заблокированных статьях"""
    logger = get_logger('core.main')
    db = Database()
    
    with db.get_connection() as conn:
        # Активные сессии
        cursor = conn.execute("""
            SELECT 
                session_uuid,
                worker_id,
                status,
                started_at,
                last_heartbeat,
                current_article_id,
                total_articles,
                success_count,
                error_count,
                hostname,
                pid,
                CASE 
                    WHEN last_heartbeat < datetime('now', '-5 minutes') THEN 'STALE'
                    WHEN last_heartbeat < datetime('now', '-2 minutes') THEN 'INACTIVE' 
                    ELSE 'ACTIVE'
                END as health_status
            FROM pipeline_sessions
            WHERE status = 'active'
            ORDER BY started_at DESC
        """)
        
        sessions = cursor.fetchall()
        
        logger.info("\n👥 АКТИВНЫЕ СЕССИИ:")
        logger.info("=" * 120)
        
        if not sessions:
            logger.info("📭 Нет активных сессий")
        else:
            logger.info(f"{'Worker ID':<20} {'Status':<8} {'Health':<8} {'Started':<19} {'Articles':<8} {'S/E':<7} {'Current Article':<15}")
            logger.info("-" * 120)
            
            for session in sessions:
                worker_id = session['worker_id'][:19]
                status = session['status']
                health = session['health_status']
                started = session['started_at'][:19] if session['started_at'] else 'Unknown'
                total = session['total_articles'] or 0
                success = session['success_count'] or 0
                error = session['error_count'] or 0
                current_article = session['current_article_id'][:14] if session['current_article_id'] else 'None'
                
                health_icon = {
                    'ACTIVE': '🟢',
                    'INACTIVE': '🟡', 
                    'STALE': '🔴'
                }.get(health, '❓')
                
                logger.info(f"{worker_id:<20} {status:<8} {health_icon}{health:<7} {started:<19} {total:<8} {success}/{error:<6} {current_article:<15}")
        
        # Заблокированные статьи
        cursor = conn.execute("""
            SELECT 
                sl.article_id,
                sl.session_uuid,
                sl.worker_id,
                sl.locked_at,
                sl.heartbeat,
                a.title,
                a.content_status,
                CASE 
                    WHEN sl.heartbeat < datetime('now', '-5 minutes') THEN 'EXPIRED'
                    WHEN sl.heartbeat < datetime('now', '-2 minutes') THEN 'STALE'
                    ELSE 'ACTIVE'
                END as lock_status
            FROM session_locks sl
            LEFT JOIN articles a ON sl.article_id = a.article_id
            WHERE sl.status = 'locked'
            ORDER BY sl.locked_at DESC
            LIMIT 20
        """)
        
        locks = cursor.fetchall()
        
        logger.info(f"\n🔒 ЗАБЛОКИРОВАННЫЕ СТАТЬИ ({len(locks)}):")
        logger.info("=" * 120)
        
        if not locks:
            logger.info("📭 Нет заблокированных статей")
        else:
            logger.info(f"{'Article ID':<15} {'Lock Status':<12} {'Worker':<20} {'Locked At':<19} {'Title':<30}")
            logger.info("-" * 120)
            
            for lock in locks:
                article_id = lock['article_id'][:14]
                lock_status = lock['lock_status']
                worker_id = (lock['worker_id'] or 'Unknown')[:19]
                locked_at = lock['locked_at'][:19] if lock['locked_at'] else 'Unknown'
                title = (lock['title'] or 'No title')[:29]
                
                status_icon = {
                    'ACTIVE': '🟢',
                    'STALE': '🟡',
                    'EXPIRED': '🔴'
                }.get(lock_status, '❓')
                
                logger.info(f"{article_id:<15} {status_icon}{lock_status:<11} {worker_id:<20} {locked_at:<19} {title:<30}")
        
        # Статистика системы
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total_articles,
                SUM(CASE WHEN content_status = 'pending' THEN 1 ELSE 0 END) as pending_articles,
                SUM(CASE WHEN processing_session_id IS NOT NULL THEN 1 ELSE 0 END) as processing_articles
            FROM articles
        """)
        
        stats = cursor.fetchone()
        
        logger.info(f"\n📊 СИСТЕМНАЯ СТАТИСТИКА:")
        logger.info("-" * 40)
        logger.info(f"📚 Всего статей:        {stats['total_articles']:>6}")
        logger.info(f"⏳ Ожидают обработки:   {stats['pending_articles']:>6}")  
        logger.info(f"🔄 В обработке:         {stats['processing_articles']:>6}")
        
        # Рекомендации по очистке
        cursor = conn.execute("""
            SELECT COUNT(*) as stale_sessions
            FROM pipeline_sessions
            WHERE status = 'active'
              AND last_heartbeat < datetime('now', '-30 minutes')
        """)
        
        stale_count = cursor.fetchone()['stale_sessions']
        if stale_count > 0:
            logger.info(f"\n⚠️  ВНИМАНИЕ: Найдено {stale_count} устаревших сессий")
            logger.info("💡 Рекомендация: очистить устаревшие сессии:")
            logger.info("   python -c \"from core.session_manager import SessionManager; SessionManager().cleanup_stale_sessions()\"")


async def process_specific_article(article_id: str):
    """Обработка конкретной статьи по ID"""
    logger = get_logger('core.main')
    
    with LogContext.operation("process_specific", article_id=article_id):
        logger.info(f"🎯 Обработка конкретной статьи: {article_id}")
        
        pipeline = SingleArticlePipeline()
        
        # Получаем статью из БД
        db = Database()
        with db.get_connection() as conn:
            cursor = conn.execute(
                "SELECT * FROM articles WHERE article_id = ?",
                (article_id,)
            )
            row = cursor.fetchone()
            
            if not row:
                logger.error(f"❌ Статья {article_id} не найдена")
                return {"success": False, "error": "Article not found"}
            
            article = dict(row)
        
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
    db = Database()
    
    with db.get_connection() as conn:
        # Статистика по статьям
        cursor = conn.execute("""
            SELECT 
                content_status,
                COUNT(*) as count
            FROM articles
            GROUP BY content_status
            ORDER BY count DESC
        """)
        
        logger.info("\n📊 СТАТИСТИКА СТАТЕЙ:")
        logger.info("-" * 40)
        total = 0
        for row in cursor:
            status = row['content_status'] or 'unknown'
            count = row['count']
            total += count
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
        
        # Статистика по источникам
        cursor = conn.execute("""
            SELECT 
                s.name,
                s.source_id,
                COUNT(a.article_id) as article_count,
                MAX(a.created_at) as last_article
            FROM sources s
            LEFT JOIN articles a ON s.source_id = a.source_id
            GROUP BY s.source_id
            ORDER BY article_count DESC
            LIMIT 10
        """)
        
        logger.info("📡 ТОП-10 ИСТОЧНИКОВ:")
        logger.info("-" * 60)
        logger.info(f"{'Источник':<30} {'Статей':>10} {'Последняя':<20}")
        logger.info("-" * 60)
        for row in cursor:
            name = row['name'][:30]
            count = row['article_count']
            last = row['last_article'] or 'Never'
            if last != 'Never':
                last = last.split('.')[0]  # Убираем микросекунды
            logger.info(f"{name:<30} {count:>10} {last:<20}")
        
        # Статистика по медиа
        cursor = conn.execute("""
            SELECT 
                status,
                COUNT(*) as count
            FROM media_files
            GROUP BY status
        """)
        
        media_stats = list(cursor)
        if media_stats:
            logger.info("\n🖼️ СТАТИСТИКА МЕДИАФАЙЛОВ:")
            logger.info("-" * 40)
            for row in media_stats:
                status = row['status']
                count = row['count']
                logger.info(f"  {status:15} {count:5} файлов")
        
        # WordPress статистика
        cursor = conn.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN published_to_wp = 1 THEN 1 ELSE 0 END) as published
            FROM wordpress_articles
        """)
        
        wp_stats = cursor.fetchone()
        if wp_stats and wp_stats['total'] > 0:
            logger.info(f"\n📝 WORDPRESS:")
            logger.info("-" * 40)
            logger.info(f"  Подготовлено:    {wp_stats['total']:5} статей")
            logger.info(f"  Опубликовано:    {wp_stats['published']:5} статей")


def show_sources():
    """Показать список источников"""
    db = Database()
    
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT 
                source_id,
                name,
                url,
                category,
                (SELECT COUNT(*) FROM articles WHERE source_id = s.source_id) as article_count
            FROM sources s
            ORDER BY category, name
        """)
        
        logger.info("\n📡 ИСТОЧНИКИ НОВОСТЕЙ:")
        logger.info("=" * 80)
        
        current_category = None
        for row in cursor:
            if row['category'] != current_category:
                current_category = row['category']
                logger.info(f"\n{current_category or 'Uncategorized'}:")
                logger.info("-" * 80)
            
            logger.info(f"📡 {row['name']:<30} [{row['article_count']:>3} статей]")
            logger.info(f"   {row['url'][:70]}")


def cleanup_old_articles(days: int = 30):
    """Очистка старых статей"""
    logger = get_logger('core.main')
    db = Database()
    
    with db.get_connection() as conn:
        # Подсчитываем сколько удалим
        cursor = conn.execute("""
            SELECT COUNT(*) as count
            FROM articles
            WHERE created_at < datetime('now', ? || ' days')
        """, (-days,))
        
        count = cursor.fetchone()['count']
        
        if count == 0:
            logger.info(f"Нет статей старше {days} дней для удаления")
            return
        
        # Удаляем старые статьи
        conn.execute("""
            DELETE FROM articles
            WHERE created_at < datetime('now', ? || ' days')
        """, (-days,))
        
        # Удаляем осиротевшие медиафайлы
        conn.execute("""
            DELETE FROM media_files
            WHERE article_id NOT IN (SELECT article_id FROM articles)
        """)
        
        # Удаляем осиротевшие WordPress статьи
        conn.execute("""
            DELETE FROM wordpress_articles
            WHERE article_id NOT IN (SELECT article_id FROM articles)
        """)
        
        conn.commit()
        
        # VACUUM для оптимизации
        conn.execute("VACUUM")
        
        logger.info(f"✅ Удалено {count} статей старше {days} дней")
        logger.info(f"✅ Очистка завершена: удалено {count} статей")


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
    
    elif args.tracking_stats or not (args.scan or args.complete_scan or args.export or args.extract_urls or args.show_new_urls or args.export_articles):
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
    
    else:
        logger.info("❌ Неизвестная команда для --change-tracking")
        logger.info("💡 Используйте: --scan, --complete-scan, --export, --tracking-stats,")
        logger.info("    --extract-urls, --show-new-urls, или --export-articles")


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
            
        elif args.single_pipeline:
            await run_single_pipeline()
            
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
            
        elif args.parallel_workers is not None:
            # Запуск параллельных воркеров
            if args.parallel_workers < 1:
                logger.error("❌ Количество воркеров должно быть больше 0")
                sys.exit(1)
            elif args.parallel_workers > 10:
                logger.error("❌ Максимальное количество воркеров: 10")
                sys.exit(1)
            
            await run_parallel_workers(
                num_workers=args.parallel_workers,
                max_articles=args.max_articles,
                delay_between=args.delay_between
            )
            
        elif args.monitor_sessions:
            show_session_monitoring()
            
        else:
            logger.info("❌ Не указана команда. Используйте --help для справки")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("⚠️ Остановлено пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
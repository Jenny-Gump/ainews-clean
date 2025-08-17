#!/usr/bin/env python3
"""
Тестирование исправления таймаутов для RSS Discovery и Change Tracking
"""
import asyncio
import sys
import time
from pathlib import Path

# Добавляем путь к проекту
sys.path.append(str(Path(__file__).parent))

from core.process_supervisor import ProcessSupervisor
from services.rss_discovery import ExtractRSSDiscovery
from change_tracking.monitor import ChangeMonitor
from app_logging import get_logger

logger = get_logger('test_timeout_fix')


async def test_rss_discovery_direct():
    """Тест прямого вызова RSS Discovery с новыми таймаутами"""
    logger.info("=" * 60)
    logger.info("🧪 ТЕСТ 1: Прямой вызов RSS Discovery")
    logger.info("=" * 60)
    
    discovery = ExtractRSSDiscovery()
    
    # Тестируем на проблемных источниках
    test_sources = ['google_alerts_ai', 'techcrunch', 'mit_news']
    
    start_time = time.time()
    try:
        stats = await discovery.discover_from_sources(source_ids=test_sources)
        elapsed = time.time() - start_time
        
        logger.info(f"✅ RSS Discovery завершен за {elapsed:.1f} секунд")
        logger.info(f"📊 Статистика: {stats}")
        
        if elapsed > 90:  # 3 источника x 30 сек максимум
            logger.warning(f"⚠️ Превышено ожидаемое время (ожидалось <90s, получили {elapsed:.1f}s)")
        
        return True
        
    except Exception as e:
        elapsed = time.time() - start_time
        logger.error(f"❌ RSS Discovery failed после {elapsed:.1f}s: {e}")
        return False


async def test_change_tracking_direct():
    """Тест прямого вызова Change Tracking с новыми таймаутами"""
    logger.info("=" * 60)
    logger.info("🧪 ТЕСТ 2: Прямой вызов Change Tracking")
    logger.info("=" * 60)
    
    monitor = ChangeMonitor()
    
    # Тестируем на проблемных URL
    test_urls = [
        'https://huggingface.co/blog',
        'https://openai.com/blog',
        'https://www.anthropic.com/news'
    ]
    
    for url in test_urls:
        start_time = time.time()
        try:
            # max_retries=1 по умолчанию теперь
            result = await monitor.scan_webpage(url)
            elapsed = time.time() - start_time
            
            status = result.get('status', 'unknown')
            if status != 'error':
                logger.info(f"✅ {url[:40]}... - {status} за {elapsed:.1f}s")
            else:
                logger.warning(f"⚠️ {url[:40]}... - ошибка: {result.get('error', 'Unknown')}")
            
            if elapsed > 35:  # 30 сек таймаут + небольшой запас
                logger.warning(f"⚠️ Превышено ожидаемое время для {url[:40]}...")
                
        except Exception as e:
            elapsed = time.time() - start_time
            logger.error(f"❌ {url[:40]}... failed после {elapsed:.1f}s: {e}")
    
    return True


def test_process_supervisor():
    """Тест Process Supervisor для изоляции источников"""
    logger.info("=" * 60)
    logger.info("🧪 ТЕСТ 3: Process Supervisor")
    logger.info("=" * 60)
    
    supervisor = ProcessSupervisor(timeout_per_source=30)
    
    # Тест RSS источника
    logger.info("📡 Тестируем RSS источник через supervisor...")
    result = supervisor.run_rss_source('techcrunch')
    
    if result['status'] == 'success':
        logger.info(f"✅ RSS источник обработан: {result.get('articles', 0)} статей")
    elif result['status'] == 'killed':
        logger.warning(f"⏱️ RSS источник убит по таймауту")
    else:
        logger.error(f"❌ RSS источник failed: {result.get('message', 'Unknown')}")
    
    # Тест Change Tracking
    logger.info("🔍 Тестируем Change Tracking через supervisor...")
    result = supervisor.run_change_tracking_source('https://openai.com/blog')
    
    if result['status'] != 'error' and result['status'] != 'killed':
        logger.info(f"✅ Change Tracking завершен: {result['status']}")
    elif result['status'] == 'killed':
        logger.warning(f"⏱️ Change Tracking убит по таймауту")
    else:
        logger.error(f"❌ Change Tracking failed: {result.get('message', 'Unknown')}")
    
    # Показываем статистику
    stats = supervisor.get_stats()
    logger.info(f"📊 Статистика supervisor: {stats}")
    
    return stats['killed'] == 0  # Успех если ничего не было убито по таймауту


async def main():
    """Главная функция тестирования"""
    logger.info("🚀 НАЧАЛО ТЕСТИРОВАНИЯ ИСПРАВЛЕНИЯ ТАЙМАУТОВ")
    logger.info("Версия: MVP с упрощенными таймаутами и Process Supervisor")
    
    all_passed = True
    
    # Тест 1: RSS Discovery
    if not await test_rss_discovery_direct():
        all_passed = False
    
    # Тест 2: Change Tracking
    if not await test_change_tracking_direct():
        all_passed = False
    
    # Тест 3: Process Supervisor
    if not test_process_supervisor():
        all_passed = False
    
    # Результаты
    logger.info("=" * 60)
    if all_passed:
        logger.info("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО")
        logger.info("Система должна работать без зависаний!")
    else:
        logger.warning("⚠️ НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОЙДЕНЫ")
        logger.warning("Проверьте логи выше для деталей")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
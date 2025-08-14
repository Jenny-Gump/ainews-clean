#!/usr/bin/env python3
"""
Тестовый скрипт для проверки исправлений утечки памяти
"""
import asyncio
import sys
import os
import psutil
import time

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.single_pipeline import SingleArticlePipeline
from app_logging import get_logger

logger = get_logger('test_memory_fix')

def get_memory_usage():
    """Получить текущее использование памяти процессом в MB"""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

async def test_continuous_mode():
    """Тест continuous mode с мониторингом памяти"""
    logger.info("=" * 60)
    logger.info("🧪 ТЕСТ ИСПРАВЛЕНИЙ УТЕЧКИ ПАМЯТИ")
    logger.info("=" * 60)
    
    # Начальная память
    initial_memory = get_memory_usage()
    logger.info(f"📊 Начальная память: {initial_memory:.1f} MB")
    
    # Создаем пайплайн
    pipeline = SingleArticlePipeline()
    
    # Запускаем в continuous mode с лимитом 5 статей
    logger.info("🚀 Запуск continuous mode (max 5 статей)...")
    
    start_time = time.time()
    result = await pipeline.run_pipeline(
        continuous_mode=True,
        max_articles=5,
        delay_between=3  # 3 секунды между статьями
    )
    
    duration = time.time() - start_time
    
    # Финальная память
    final_memory = get_memory_usage()
    memory_increase = final_memory - initial_memory
    
    logger.info("\n" + "=" * 60)
    logger.info("📈 РЕЗУЛЬТАТЫ ТЕСТА")
    logger.info("=" * 60)
    logger.info(f"⏱️ Время выполнения: {duration:.1f} секунд")
    logger.info(f"📄 Обработано статей: {result.get('processed_count', 0)}")
    logger.info(f"✅ Успешно: {result.get('success_count', 0)}")
    logger.info(f"❌ Ошибок: {result.get('error_count', 0)}")
    logger.info(f"📊 Начальная память: {initial_memory:.1f} MB")
    logger.info(f"📊 Финальная память: {final_memory:.1f} MB")
    logger.info(f"📊 Прирост памяти: {memory_increase:.1f} MB")
    
    # Оценка результата
    if memory_increase < 50:
        logger.info("✅ ТЕСТ ПРОЙДЕН: Утечка памяти не обнаружена")
    elif memory_increase < 100:
        logger.warning("⚠️ ПРЕДУПРЕЖДЕНИЕ: Небольшой рост памяти")
    else:
        logger.error("❌ ТЕСТ ПРОВАЛЕН: Значительная утечка памяти")
    
    return result

async def test_single_mode():
    """Тест single mode с мониторингом памяти"""
    logger.info("\n" + "=" * 60)
    logger.info("🧪 ТЕСТ SINGLE MODE")
    logger.info("=" * 60)
    
    # Начальная память
    initial_memory = get_memory_usage()
    logger.info(f"📊 Начальная память: {initial_memory:.1f} MB")
    
    # Создаем пайплайн
    pipeline = SingleArticlePipeline()
    
    # Запускаем в single mode
    logger.info("🚀 Запуск single mode (1 статья)...")
    
    start_time = time.time()
    result = await pipeline.run_pipeline(
        continuous_mode=False
    )
    
    duration = time.time() - start_time
    
    # Финальная память
    final_memory = get_memory_usage()
    memory_increase = final_memory - initial_memory
    
    logger.info(f"⏱️ Время выполнения: {duration:.1f} секунд")
    logger.info(f"📊 Прирост памяти: {memory_increase:.1f} MB")
    
    return result

async def main():
    """Основная функция тестирования"""
    try:
        # Тест single mode
        await test_single_mode()
        
        # Пауза между тестами
        logger.info("\n⏳ Пауза 5 секунд между тестами...")
        await asyncio.sleep(5)
        
        # Тест continuous mode
        await test_continuous_mode()
        
        logger.info("\n✅ ВСЕ ТЕСТЫ ЗАВЕРШЕНЫ")
        
    except Exception as e:
        logger.error(f"❌ Ошибка в тестах: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
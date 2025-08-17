#!/usr/bin/env python3
"""
Скрипт для автоматического извлечения параметров LLM моделей из документации
и заполнения колонок G (Parameters Total) и H (Parameters Active) в Google Таблице
"""
import asyncio
import sys
import os
import json
import argparse
from pathlib import Path
from typing import Dict, Optional, Tuple, List
from datetime import datetime

# Добавляем корневую директорию в путь
sys.path.append(str(Path(__file__).parent.parent))

from services.firecrawl_client import FirecrawlClient
from app_logging import get_logger

# Настройка логирования
logger = get_logger('fetch_llm_parameters')

# ID таблицы
SPREADSHEET_ID = "1s-A1X5UQIYMDnJQjqhIySnrMUxp299lGtegHqOVft2k"

# Кэш для результатов
CACHE_FILE = Path(__file__).parent / "llm_parameters_cache.json"


def load_cache() -> Dict:
    """Загрузить кэш из файла"""
    if CACHE_FILE.exists():
        with open(CACHE_FILE, 'r') as f:
            return json.load(f)
    return {}


def save_cache(cache: Dict):
    """Сохранить кэш в файл"""
    with open(CACHE_FILE, 'w') as f:
        json.dump(cache, f, indent=2)


async def extract_parameters_from_content(
    firecrawl: FirecrawlClient,
    doc_url: str,
    model_name: str,
    organization: str
) -> Dict[str, Optional[str]]:
    """
    Извлечь параметры модели из документации
    
    Returns:
        Dict с ключами 'total' и 'active' (значения в миллиардах или None)
    """
    try:
        logger.info(f"Извлечение параметров для {model_name} из {doc_url}")
        
        # Специальная обработка для известных источников
        if "platform.openai.com" in doc_url:
            # OpenAI обычно не публикует точные параметры для проприетарных моделей
            if any(x in model_name.lower() for x in ['gpt-5', 'o1', 'o3', 'o4']):
                logger.info(f"Проприетарная модель OpenAI {model_name}, параметры не публикуются")
                return {'total': None, 'active': None}
            elif "GPT OSS" in model_name:
                # Open source модели имеют параметры в названии
                if "120B" in model_name:
                    return {'total': '120', 'active': None}
                elif "20B" in model_name:
                    return {'total': '20', 'active': None}
        
        elif "docs.anthropic.com" in doc_url:
            # Anthropic не публикует параметры для Claude
            logger.info(f"Проприетарная модель Anthropic {model_name}, параметры не публикуются")
            return {'total': None, 'active': None}
        
        elif "ai.google.dev" in doc_url or "deepmind.google" in doc_url:
            # Google обычно не публикует точные параметры для Gemini
            logger.info(f"Проприетарная модель Google {model_name}, параметры не публикуются")
            return {'total': None, 'active': None}
        
        elif "docs.x.ai" in doc_url:
            # xAI не публикует параметры для Grok
            logger.info(f"Проприетарная модель xAI {model_name}, параметры не публикуются")
            return {'total': None, 'active': None}
        
        # Для остальных пробуем извлечь через Firecrawl
        prompt = f"""
        Extract parameter information for the AI model: {model_name} by {organization}
        
        Look for:
        1. Total number of parameters (in billions, like 671B, 1000B, 235B)
        2. Active parameters for MoE (Mixture of Experts) models
        3. Model size specifications in the documentation
        
        Return ONLY the numbers without 'B' suffix if found.
        If the model is proprietary and parameters are not disclosed, return null.
        
        Format:
        {{
            "total_parameters": "number or null",
            "active_parameters": "number or null for MoE models"
        }}
        """
        
        # Сначала пробуем простой scrape
        logger.debug(f"Пробуем scrape для {doc_url}")
        content = await firecrawl.scrape_url(doc_url, formats=['markdown'])
        
        # Если контент получен, пробуем извлечь структурированные данные
        if content and content.get('markdown'):
            logger.debug(f"Получен контент, извлекаем параметры через LLM")
            
            # Используем extract для структурированного извлечения
            result = await firecrawl.extract_content(
                doc_url,
                prompt=prompt,
                schema={
                    "type": "object",
                    "properties": {
                        "total_parameters": {
                            "type": ["string", "null"],
                            "description": "Total parameters in billions"
                        },
                        "active_parameters": {
                            "type": ["string", "null"],
                            "description": "Active parameters for MoE models"
                        }
                    }
                }
            )
            
            if result and 'data' in result:
                data = result['data']
                return {
                    'total': data.get('total_parameters'),
                    'active': data.get('active_parameters')
                }
        
        logger.warning(f"Не удалось извлечь параметры для {model_name}")
        return {'total': None, 'active': None}
        
    except Exception as e:
        logger.error(f"Ошибка при извлечении параметров для {model_name}: {e}")
        return {'total': None, 'active': None}


async def process_model_row(
    firecrawl: FirecrawlClient,
    row_data: Dict,
    row_num: int,
    dry_run: bool = False,
    force: bool = False
) -> Dict:
    """
    Обработать одну строку с моделью
    """
    organization = row_data.get('A', '')
    model_name = row_data.get('C', '')
    doc_url = row_data.get('E', '')
    license_type = row_data.get('F', '')
    current_total = row_data.get('G', '')
    current_active = row_data.get('H', '')
    
    result = {
        'row': row_num,
        'model': model_name,
        'status': 'skipped',
        'total': None,
        'active': None
    }
    
    # Пропускаем если уже заполнено и не force
    if current_total and current_total != '-' and not force:
        logger.info(f"Строка {row_num}: {model_name} уже имеет параметры: {current_total}")
        result['status'] = 'already_filled'
        return result
    
    # Пропускаем если нет URL документации
    if not doc_url or doc_url == '*':
        logger.warning(f"Строка {row_num}: {model_name} не имеет URL документации")
        result['status'] = 'no_doc_url'
        return result
    
    # Извлекаем параметры
    params = await extract_parameters_from_content(
        firecrawl, doc_url, model_name, organization
    )
    
    # Обновляем результат
    result['total'] = params['total']
    result['active'] = params['active']
    
    if params['total'] or params['active']:
        result['status'] = 'extracted'
        logger.info(f"✓ {model_name}: Total={params['total']}, Active={params['active']}")
    else:
        result['status'] = 'not_found'
        logger.info(f"✗ {model_name}: Параметры не найдены")
    
    # В dry_run режиме не обновляем таблицу
    if not dry_run and (params['total'] or params['active']):
        await update_spreadsheet(row_num, params['total'], params['active'])
    
    return result


async def update_spreadsheet(row_num: int, total_params: Optional[str], active_params: Optional[str]):
    """
    Обновить Google Таблицу через MCP
    """
    try:
        # Импортируем здесь чтобы избежать проблем если MCP не настроен
        import subprocess
        import json
        
        # Обновляем колонку G (total parameters)
        if total_params is not None:
            cmd = [
                'claude', 'mcp', 'run',
                'gdrive', 'gsheets_update_cell',
                '--fileId', SPREADSHEET_ID,
                '--range', f'llmstat!G{row_num}',
                '--value', str(total_params) if total_params else '-'
            ]
            subprocess.run(cmd, capture_output=True, text=True)
            logger.debug(f"Обновлена ячейка G{row_num}: {total_params}")
        
        # Обновляем колонку H (active parameters)
        if active_params is not None:
            cmd = [
                'claude', 'mcp', 'run',
                'gdrive', 'gsheets_update_cell',
                '--fileId', SPREADSHEET_ID,
                '--range', f'llmstat!H{row_num}',
                '--value', str(active_params) if active_params else '-'
            ]
            subprocess.run(cmd, capture_output=True, text=True)
            logger.debug(f"Обновлена ячейка H{row_num}: {active_params}")
            
    except Exception as e:
        logger.error(f"Ошибка при обновлении таблицы для строки {row_num}: {e}")


async def main():
    """
    Главная функция
    """
    parser = argparse.ArgumentParser(description='Извлечение параметров LLM моделей')
    parser.add_argument('--dry-run', action='store_true', help='Тестовый режим без записи в таблицу')
    parser.add_argument('--start-row', type=int, default=2, help='Начальная строка (по умолчанию 2)')
    parser.add_argument('--end-row', type=int, default=30, help='Конечная строка (по умолчанию 30)')
    parser.add_argument('--models', help='Обработать только указанные модели (через запятую)')
    parser.add_argument('--force', action='store_true', help='Перезаписать существующие значения')
    parser.add_argument('--test', action='store_true', help='Тестовый режим - обработать только 3 модели')
    
    args = parser.parse_args()
    
    logger.info("=" * 60)
    logger.info("Запуск извлечения параметров LLM моделей")
    logger.info(f"Режим: {'ТЕСТ' if args.dry_run else 'ПРОДАКШН'}")
    logger.info(f"Диапазон строк: {args.start_row}-{args.end_row}")
    logger.info("=" * 60)
    
    # Тестовые данные из таблицы (уже прочитанные)
    test_data = [
        {'row': 2, 'A': 'xAI', 'C': 'Grok-4 Heavy', 'E': 'https://docs.x.ai/docs', 'F': 'Proprietary', 'G': '-', 'H': ''},
        {'row': 3, 'A': 'xAI', 'C': 'Grok-4', 'E': 'https://docs.x.ai/docs', 'F': 'Proprietary', 'G': '-', 'H': ''},
        {'row': 4, 'A': 'Google', 'C': 'Gemini 2.5 Pro Preview 06-05', 'E': 'https://ai.google.dev/gemini-api/docs/models', 'F': 'Proprietary', 'G': '-', 'H': ''},
        {'row': 5, 'A': 'OpenAI', 'C': 'GPT-5', 'E': 'https://openai.com/gpt-5/', 'F': 'Proprietary', 'G': '-', 'H': ''},
        {'row': 14, 'A': 'DeepSeek', 'C': 'DeepSeek-R1-0528', 'E': 'https://platform.deepseek.com/api-docs/', 'F': 'Open', 'G': '671', 'H': ''},
        {'row': 16, 'A': 'OpenAI', 'C': 'GPT OSS 120B', 'E': 'https://platform.openai.com/docs/models', 'F': 'Open', 'G': '120', 'H': ''},
    ]
    
    # Инициализация Firecrawl клиента
    async with FirecrawlClient() as firecrawl:
        results = []
        
        # Выбираем данные для обработки
        if args.test:
            # В тестовом режиме берем только 3 модели
            rows_to_process = test_data[:3]
            logger.info(f"Тестовый режим: обработка {len(rows_to_process)} моделей")
        else:
            rows_to_process = test_data
        
        # Обрабатываем каждую строку
        for row_data in rows_to_process:
            row_num = row_data['row']
            
            # Пропускаем если не в диапазоне
            if row_num < args.start_row or row_num > args.end_row:
                continue
            
            # Пропускаем если не в списке моделей
            if args.models:
                models_list = [m.strip() for m in args.models.split(',')]
                if row_data['C'] not in models_list:
                    continue
            
            # Обрабатываем строку
            result = await process_model_row(
                firecrawl, 
                row_data, 
                row_num,
                dry_run=args.dry_run,
                force=args.force
            )
            results.append(result)
            
            # Небольшая задержка между запросами
            await asyncio.sleep(2)
        
        # Выводим итоговую статистику
        logger.info("\n" + "=" * 60)
        logger.info("ИТОГОВАЯ СТАТИСТИКА")
        logger.info("=" * 60)
        
        extracted = [r for r in results if r['status'] == 'extracted']
        not_found = [r for r in results if r['status'] == 'not_found']
        skipped = [r for r in results if r['status'] in ['already_filled', 'no_doc_url', 'skipped']]
        
        logger.info(f"Обработано моделей: {len(results)}")
        logger.info(f"✓ Извлечено параметров: {len(extracted)}")
        logger.info(f"✗ Не найдено: {len(not_found)}")
        logger.info(f"⊘ Пропущено: {len(skipped)}")
        
        if extracted:
            logger.info("\nИзвлеченные параметры:")
            for r in extracted:
                logger.info(f"  • {r['model']}: Total={r['total']}, Active={r['active']}")
        
        if not_found:
            logger.info("\nПараметры не найдены для:")
            for r in not_found:
                logger.info(f"  • {r['model']}")
        
        # Сохраняем результаты в файл
        results_file = Path(__file__).parent / f"llm_parameters_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        logger.info(f"\nРезультаты сохранены в: {results_file}")


if __name__ == "__main__":
    asyncio.run(main())
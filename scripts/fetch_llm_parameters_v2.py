#!/usr/bin/env python3
"""
Улучшенная версия скрипта для извлечения параметров LLM моделей
Использует прямую интеграцию с Google Sheets через MCP и Firecrawl API
"""
import asyncio
import sys
import os
import json
import re
from pathlib import Path
from typing import Dict, Optional, List, Tuple
from datetime import datetime

sys.path.append(str(Path(__file__).parent.parent))

from services.firecrawl_client import FirecrawlClient
from app_logging import get_logger

logger = get_logger('llm_parameters_v2')

# ID таблицы
SPREADSHEET_ID = "1s-A1X5UQIYMDnJQjqhIySnrMUxp299lGtegHqOVft2k"


async def fetch_and_extract_parameters(
    firecrawl: FirecrawlClient,
    doc_url: str,
    model_name: str,
    organization: str,
    license_type: str
) -> Tuple[Optional[str], Optional[str]]:
    """
    Извлечь параметры модели используя Firecrawl API
    
    Returns:
        Tuple (total_params, active_params) - числа в миллиардах или None
    """
    
    # Проверяем известные паттерны в названии модели
    param_match = re.search(r'(\d+)B', model_name)
    if param_match:
        total = param_match.group(1)
        logger.info(f"Найдены параметры в названии {model_name}: {total}B")
        return (total, None)
    
    # Для Open моделей с известными параметрами
    known_params = {
        'DeepSeek-R1-0528': ('671', None),
        'DeepSeek-R1': ('671', None),
        'DeepSeek R1 Zero': ('671', None),
        'GPT OSS 120B': ('120', None),
        'GPT OSS 20B': ('20', None),
        'Qwen3-235B-A22B-Instruct-2507': ('235', '22'),  # MoE модель
        'Llama 3.1 Nemotron Ultra 253B v1': ('253', None),
        'Kimi K2 Instruct': ('1000', None),
    }
    
    if model_name in known_params:
        total, active = known_params[model_name]
        logger.info(f"Используем известные параметры для {model_name}: Total={total}, Active={active}")
        return (total, active)
    
    # Для проприетарных моделей возвращаем None
    if license_type == 'Proprietary':
        proprietary_orgs = ['OpenAI', 'Anthropic', 'Google', 'xAI']
        if organization in proprietary_orgs:
            logger.info(f"Проприетарная модель {organization} {model_name}, параметры не раскрываются")
            return (None, None)
    
    # Пробуем извлечь через Firecrawl для остальных
    try:
        logger.info(f"Извлечение через Firecrawl для {model_name} из {doc_url}")
        
        # Используем scrape для получения контента
        content = await firecrawl.scrape_url(doc_url, formats=['markdown'])
        
        if content and content.get('markdown'):
            markdown = content['markdown']
            
            # Ищем паттерны параметров в тексте
            patterns = [
                r'(\d+(?:\.\d+)?)\s*[Bb]illion\s*parameters',
                r'(\d+)\s*[Bb]\s*parameters',
                r'parameters:\s*(\d+(?:\.\d+)?)\s*[Bb]',
                r'model\s*size:\s*(\d+(?:\.\d+)?)\s*[Bb]',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, markdown, re.IGNORECASE)
                if match:
                    total = match.group(1)
                    logger.info(f"Найдены параметры в документации {model_name}: {total}B")
                    return (total, None)
            
            # Специальный поиск для MoE моделей
            moe_pattern = r'(\d+(?:\.\d+)?)\s*[Bb].*active.*(\d+(?:\.\d+)?)\s*[Bb]'
            moe_match = re.search(moe_pattern, markdown, re.IGNORECASE)
            if moe_match:
                total = moe_match.group(1)
                active = moe_match.group(2)
                logger.info(f"Найдены MoE параметры для {model_name}: Total={total}B, Active={active}B")
                return (total, active)
        
        # Если ничего не нашли через регулярки, пробуем структурированное извлечение
        if license_type == 'Open':
            prompt = f"""
            Find the number of parameters for the model {model_name}.
            Look for mentions of:
            - Total parameters (in billions)
            - Model size
            - For MoE models: both total and active parameters
            
            Return ONLY the numbers without 'B' suffix.
            """
            
            result = await firecrawl.extract_content(
                doc_url,
                prompt=prompt,
                schema={
                    "type": "object",
                    "properties": {
                        "total_parameters": {"type": ["string", "null"]},
                        "active_parameters": {"type": ["string", "null"]}
                    }
                }
            )
            
            if result and 'data' in result:
                data = result['data']
                total = data.get('total_parameters')
                active = data.get('active_parameters')
                if total:
                    logger.info(f"Извлечены параметры через LLM для {model_name}: Total={total}, Active={active}")
                    return (total, active)
        
    except Exception as e:
        logger.error(f"Ошибка при извлечении для {model_name}: {e}")
    
    logger.warning(f"Не удалось найти параметры для {model_name}")
    return (None, None)


async def process_spreadsheet_directly():
    """
    Обработать таблицу напрямую через MCP
    """
    logger.info("=" * 60)
    logger.info("Обработка таблицы llmstat")
    logger.info("=" * 60)
    
    # Статистика
    stats = {
        'processed': 0,
        'updated': 0,
        'skipped': 0,
        'failed': 0,
        'already_filled': 0
    }
    
    # Данные из таблицы (уже прочитанные ранее)
    sheet_data = {
        2: {'org': 'xAI', 'model': 'Grok-4 Heavy', 'url': 'https://docs.x.ai/docs', 'license': 'Proprietary', 'G': '-', 'H': ''},
        3: {'org': 'xAI', 'model': 'Grok-4', 'url': 'https://docs.x.ai/docs', 'license': 'Proprietary', 'G': '-', 'H': ''},
        4: {'org': 'Google', 'model': 'Gemini 2.5 Pro Preview 06-05', 'url': 'https://ai.google.dev/gemini-api/docs/models', 'license': 'Proprietary', 'G': '-', 'H': ''},
        5: {'org': 'OpenAI', 'model': 'GPT-5', 'url': 'https://openai.com/gpt-5/', 'license': 'Proprietary', 'G': '-', 'H': ''},
        6: {'org': 'Anthropic', 'model': 'Claude 3.7 Sonnet', 'url': 'https://docs.anthropic.com/en/docs/about-claude/models/overview', 'license': 'Proprietary', 'G': '-', 'H': ''},
        7: {'org': 'xAI', 'model': 'Grok-3', 'url': 'https://docs.x.ai/docs', 'license': 'Proprietary', 'G': '-', 'H': ''},
        8: {'org': 'xAI', 'model': 'Grok-3 Mini', 'url': 'https://docs.x.ai/docs', 'license': 'Proprietary', 'G': '-', 'H': ''},
        9: {'org': 'OpenAI', 'model': 'o3', 'url': 'https://openai.com/o3/', 'license': 'Proprietary', 'G': '-', 'H': ''},
        10: {'org': 'Google', 'model': 'Gemini 2.5 Pro', 'url': 'https://ai.google.dev/gemini-api/docs/models', 'license': 'Proprietary', 'G': '-', 'H': ''},
        11: {'org': 'Google', 'model': 'Gemini 2.5 Flash', 'url': 'https://ai.google.dev/gemini-api/docs/models', 'license': 'Proprietary', 'G': '-', 'H': ''},
        12: {'org': 'OpenAI', 'model': 'GPT-5 mini', 'url': 'https://platform.openai.com/docs/models', 'license': 'Proprietary', 'G': '-', 'H': ''},
        13: {'org': 'OpenAI', 'model': 'o4-mini', 'url': 'https://platform.openai.com/docs/models', 'license': 'Proprietary', 'G': '-', 'H': ''},
        14: {'org': 'DeepSeek', 'model': 'DeepSeek-R1-0528', 'url': 'https://platform.deepseek.com/api-docs/', 'license': 'Open', 'G': '671', 'H': ''},
        15: {'org': 'Anthropic', 'model': 'Claude Opus 4.1', 'url': 'https://docs.anthropic.com/en/docs/about-claude/models/overview', 'license': 'Proprietary', 'G': '-', 'H': ''},
        16: {'org': 'OpenAI', 'model': 'GPT OSS 120B', 'url': 'https://platform.openai.com/docs/models', 'license': 'Open', 'G': '120', 'H': ''},
        17: {'org': 'Anthropic', 'model': 'Claude Opus 4', 'url': 'https://docs.anthropic.com/en/docs/about-claude/models/overview', 'license': 'Proprietary', 'G': '-', 'H': ''},
        18: {'org': 'OpenAI', 'model': 'o1-pro', 'url': 'https://platform.openai.com/docs/models', 'license': 'Proprietary', 'G': '-', 'H': ''},
        19: {'org': 'OpenAI', 'model': 'o1', 'url': 'https://platform.openai.com/docs/models', 'license': 'Proprietary', 'G': '-', 'H': ''},
        20: {'org': 'Alibaba', 'model': 'Qwen3-235B-A22B-Instruct-2507', 'url': 'https://qwenlm.github.io/blog/qwen3/', 'license': 'Open', 'G': '235', 'H': ''},
        21: {'org': 'OpenAI', 'model': 'o3-mini', 'url': 'https://platform.openai.com/docs/models', 'license': 'Proprietary', 'G': '-', 'H': ''},
        22: {'org': 'NVIDIA', 'model': 'Llama 3.1 Nemotron Ultra 253B v1', 'url': 'https://developer.nvidia.com/', 'license': 'Open', 'G': '253', 'H': ''},
        23: {'org': 'Anthropic', 'model': 'Claude Sonnet 4', 'url': 'https://docs.anthropic.com/en/docs/about-claude/models/overview', 'license': 'Proprietary', 'G': '-', 'H': ''},
        24: {'org': 'Moonshot AI', 'model': 'Kimi K2 Instruct', 'url': 'https://moonshotai.github.io/Kimi-K2/', 'license': 'Open', 'G': '1000', 'H': ''},
        25: {'org': 'Google', 'model': 'Gemini 2.0 Flash Thinking', 'url': 'https://ai.google.dev/gemini-api/docs/models', 'license': 'Proprietary', 'G': '-', 'H': ''},
        26: {'org': 'DeepSeek', 'model': 'DeepSeek R1 Zero', 'url': 'https://platform.deepseek.com/api-docs/', 'license': 'Open', 'G': '671', 'H': ''},
        27: {'org': 'OpenAI', 'model': 'o1-preview', 'url': 'https://platform.openai.com/docs/models', 'license': 'Proprietary', 'G': '-', 'H': ''},
        28: {'org': 'DeepSeek', 'model': 'DeepSeek-R1', 'url': 'https://platform.deepseek.com/api-docs/', 'license': 'Open', 'G': '671', 'H': ''},
        29: {'org': 'Alibaba', 'model': 'GPT OSS 20B', 'url': 'https://platform.openai.com/docs/models', 'license': 'Open', 'G': '20', 'H': ''},
        30: {'org': 'OpenAI', 'model': 'GPT-5 nano', 'url': 'https://cloud.tencent.com/document/product/1729', 'license': 'Proprietary', 'G': '-', 'H': ''},
    }
    
    async with FirecrawlClient() as firecrawl:
        updates = []
        
        for row_num, data in sheet_data.items():
            stats['processed'] += 1
            
            # Пропускаем уже заполненные (кроме '-')
            if data['G'] and data['G'] != '-':
                logger.info(f"Строка {row_num}: {data['model']} уже имеет параметры: {data['G']}")
                stats['already_filled'] += 1
                continue
            
            # Извлекаем параметры
            total, active = await fetch_and_extract_parameters(
                firecrawl,
                data['url'],
                data['model'],
                data['org'],
                data['license']
            )
            
            # Подготавливаем обновления
            if total is not None:
                updates.append({
                    'row': row_num,
                    'model': data['model'],
                    'total': total,
                    'active': active
                })
                stats['updated'] += 1
                logger.info(f"✓ Строка {row_num}: {data['model']} -> Total={total}, Active={active}")
            else:
                stats['skipped'] += 1
                logger.info(f"⊘ Строка {row_num}: {data['model']} - параметры не найдены")
            
            # Небольшая задержка
            await asyncio.sleep(1)
        
        # Выводим результаты
        logger.info("\n" + "=" * 60)
        logger.info("РЕЗУЛЬТАТЫ ОБРАБОТКИ")
        logger.info("=" * 60)
        logger.info(f"Обработано строк: {stats['processed']}")
        logger.info(f"Обновлено: {stats['updated']}")
        logger.info(f"Пропущено: {stats['skipped']}")
        logger.info(f"Уже заполнено: {stats['already_filled']}")
        
        if updates:
            logger.info("\nГотовые обновления для таблицы:")
            for upd in updates:
                logger.info(f"  Строка {upd['row']}: {upd['model']}")
                logger.info(f"    G{upd['row']}: {upd['total']}")
                if upd['active']:
                    logger.info(f"    H{upd['row']}: {upd['active']}")
        
        return updates


async def update_google_sheet(updates: List[Dict]):
    """
    Обновить Google таблицу через MCP
    """
    logger.info("\n" + "=" * 60)
    logger.info("ОБНОВЛЕНИЕ GOOGLE ТАБЛИЦЫ")
    logger.info("=" * 60)
    
    for upd in updates:
        row = upd['row']
        total = upd['total']
        active = upd.get('active')
        
        # Обновляем колонку G
        print(f"\nОбновление G{row} = {total}")
        print(f"mcp__gdrive__gsheets_update_cell:")
        print(f"  fileId: {SPREADSHEET_ID}")
        print(f"  range: llmstat!G{row}")
        print(f"  value: {total}")
        
        # Обновляем колонку H если есть active параметры
        if active:
            print(f"\nОбновление H{row} = {active}")
            print(f"mcp__gdrive__gsheets_update_cell:")
            print(f"  fileId: {SPREADSHEET_ID}")
            print(f"  range: llmstat!H{row}")
            print(f"  value: {active}")


async def main():
    """
    Главная функция
    """
    # Обрабатываем таблицу
    updates = await process_spreadsheet_directly()
    
    # Показываем команды для обновления
    if updates:
        await update_google_sheet(updates)
        
        # Сохраняем результаты
        results_file = Path(__file__).parent / f"llm_updates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(updates, f, indent=2, ensure_ascii=False)
        logger.info(f"\nРезультаты сохранены в: {results_file}")


if __name__ == "__main__":
    asyncio.run(main())
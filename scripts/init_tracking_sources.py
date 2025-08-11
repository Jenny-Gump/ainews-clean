#!/usr/bin/env python3
"""
Initialize Tracking Sources
Инициализирует источники из sources.txt для системы отслеживания
"""

import sys
import json
from pathlib import Path
from urllib.parse import urlparse

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app_logging import get_logger
from core.database import Database


def parse_sources_txt(file_path: str):
    """Парсит sources.txt и возвращает список источников"""
    sources = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            url = line.strip()
            if url and not url.startswith('#'):
                # Извлекаем имя из URL
                parsed = urlparse(url)
                domain = parsed.netloc.replace('www.', '')
                path = parsed.path.strip('/')
                
                # Генерируем source_id
                source_id = domain.replace('.', '_')
                if path:
                    # Добавляем путь к ID для уникальности
                    path_part = path.replace('/', '_').replace('-', '_')
                    source_id = f"{source_id}_{path_part}"[:50]  # Ограничиваем длину
                
                # Генерируем имя
                name = domain.replace('.', ' ').title()
                if path:
                    path_title = path.replace('/', ' - ').replace('-', ' ').title()
                    name = f"{name} - {path_title}"
                
                # Пытаемся определить RSS URL (эвристика)
                rss_url = ""
                if 'blog' in url:
                    rss_url = f"{url}/feed" if not url.endswith('/') else f"{url}feed"
                elif 'news' in url:
                    rss_url = f"{url}/rss" if not url.endswith('/') else f"{url}rss"
                else:
                    # Стандартные варианты
                    rss_url = f"{url}/rss.xml" if not url.endswith('/') else f"{url}rss.xml"
                
                # Определяем категорию
                category = 'general'
                if 'research' in url or 'stanford' in url or 'mit.edu' in url:
                    category = 'ai_research'
                elif any(company in url for company in ['anthropic', 'openai', 'google', 'microsoft', 'meta']):
                    category = 'ai_companies'
                elif 'cloud' in url or 'aws' in url:
                    category = 'cloud_ai'
                elif 'hugging' in url or 'databricks' in url or 'scale' in url:
                    category = 'ai_platforms'
                elif 'robot' in url or 'waymo' in url:
                    category = 'ai_robotics'
                elif 'health' in url or 'medical' in url or 'pathai' in url:
                    category = 'ai_healthcare'
                
                sources.append({
                    'source_id': source_id,
                    'name': name,
                    'url': url,
                    'rss_url': rss_url,
                    'type': 'web',
                    'category': category
                })
    
    return sources


def main():
    logger = get_logger('scripts.init_tracking_sources')
    db = Database()
    
    # Путь к sources.txt
    sources_txt = Path('/Users/skynet/Desktop/sources.txt')
    
    if not sources_txt.exists():
        logger.error(f"File not found: {sources_txt}")
        return
    
    # Парсим источники
    logger.info(f"Parsing {sources_txt}...")
    sources = parse_sources_txt(sources_txt)
    logger.info(f"Found {len(sources)} sources")
    
    # Добавляем в БД
    added = 0
    updated = 0
    
    for source in sources:
        try:
            # Проверяем существование
            with db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT source_id, rss_url FROM sources WHERE source_id = ?",
                    (source['source_id'],)
                )
                existing = cursor.fetchone()
            
            if not existing:
                # Добавляем новый источник
                with db.get_connection() as conn:
                    conn.execute("""
                        INSERT INTO sources (
                            source_id, name, url, type, has_rss, rss_url,
                            category, validation_status
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        source['source_id'],
                        source['name'],
                        source['url'],
                        source['type'],
                        1,  # has_rss
                        source['rss_url'],
                        source['category'],
                        'active'
                    ))
                added += 1
                logger.info(f"✅ Added: {source['name']}")
            else:
                # Обновляем RSS URL если он пустой
                if not existing[1] and source['rss_url']:
                    with db.get_connection() as conn:
                        conn.execute("""
                            UPDATE sources 
                            SET rss_url = ?, has_rss = 1
                            WHERE source_id = ?
                        """, (source['rss_url'], source['source_id']))
                    updated += 1
                    logger.info(f"📝 Updated RSS for: {source['name']}")
                else:
                    logger.debug(f"⏭️ Exists: {source['name']}")
                    
        except Exception as e:
            logger.error(f"Error processing {source['name']}: {e}")
    
    # Также обновляем tracking_sources.json
    tracking_file = Path(__file__).parent.parent / 'data' / 'tracking_sources.json'
    
    # Читаем существующий файл или создаем новый
    if tracking_file.exists():
        with open(tracking_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    else:
        data = {
            "tracking_sources": [],
            "settings": {
                "default_limit": 20,
                "scan_interval_hours": 6,
                "export_after_scan": False,
                "tag_group_prefix": "tracking_"
            }
        }
    
    # Обновляем источники
    existing_ids = {s['source_id'] for s in data['tracking_sources']}
    
    for source in sources:
        if source['source_id'] not in existing_ids:
            data['tracking_sources'].append(source)
    
    # Сохраняем обновленный файл
    with open(tracking_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    logger.info(f"\n📊 РЕЗУЛЬТАТЫ:")
    logger.info(f"  ✅ Добавлено в БД: {added}")
    logger.info(f"  📝 Обновлено в БД: {updated}")
    logger.info(f"  📄 Обновлен файл: {tracking_file}")
    logger.info(f"  📚 Всего источников: {len(sources)}")
    
    # Показываем категории
    categories = {}
    for source in sources:
        cat = source['category']
        categories[cat] = categories.get(cat, 0) + 1
    
    logger.info(f"\n📂 КАТЕГОРИИ:")
    for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {cat}: {count}")
    
    logger.info(f"\n💡 СЛЕДУЮЩИЕ ШАГИ:")
    logger.info(f"  1. Проверьте RSS URLs командой:")
    logger.info(f"     python scripts/tracking_manager.py --scan --scan-limit 5")
    logger.info(f"  2. Исправьте неработающие RSS URLs в БД")
    logger.info(f"  3. Запустите полный цикл:")
    logger.info(f"     python scripts/tracking_manager.py --full-cycle")


if __name__ == '__main__':
    main()
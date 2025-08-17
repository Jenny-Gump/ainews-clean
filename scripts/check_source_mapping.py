#!/usr/bin/env python3
"""
Скрипт для проверки соответствия источников между tracking_sources.json и Supabase
"""
import json
import sys
from pathlib import Path

# Добавляем корневую директорию в path
sys.path.append(str(Path(__file__).parent.parent))

from services.supabase_client import get_supabase_client
from app_logging import get_logger

logger = get_logger(__name__)

def load_tracking_sources():
    """Загружает источники из tracking_sources.json"""
    json_file = Path(__file__).parent.parent / 'data' / 'tracking_sources.json'
    
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('tracking_sources', [])
    except Exception as e:
        logger.error(f"Error loading tracking_sources.json: {e}")
        return []

def get_supabase_sources():
    """Получает все источники из Supabase"""
    try:
        supabase = get_supabase_client()
        response = supabase.client.table('sources').select('source_id, name, url').execute()
        return response.data if response.data else []
    except Exception as e:
        logger.error(f"Error getting Supabase sources: {e}")
        return []

def check_source_mapping():
    """Проверяет соответствие источников"""
    print("🔍 Проверка соответствия источников между tracking_sources.json и Supabase...")
    print("=" * 80)
    
    # Загружаем данные
    tracking_sources = load_tracking_sources()
    supabase_sources = get_supabase_sources()
    
    if not tracking_sources:
        print("❌ Не удалось загрузить tracking_sources.json")
        return
    
    if not supabase_sources:
        print("❌ Не удалось загрузить источники из Supabase")
        return
    
    # Создаем множества для сравнения
    tracking_source_ids = {src['source_id'] for src in tracking_sources}
    supabase_source_ids = {src['source_id'] for src in supabase_sources}
    
    print(f"📊 Статистика:")
    print(f"   Tracking sources: {len(tracking_source_ids)}")
    print(f"   Supabase sources: {len(supabase_source_ids)}")
    print()
    
    # Находим несоответствия
    missing_in_supabase = tracking_source_ids - supabase_source_ids
    missing_in_tracking = supabase_source_ids - tracking_source_ids
    
    # Отчет
    if missing_in_supabase:
        print("❌ Source ID отсутствуют в Supabase sources table:")
        for source_id in sorted(missing_in_supabase):
            tracking_src = next(src for src in tracking_sources if src['source_id'] == source_id)
            print(f"   - {source_id:20} | {tracking_src['name']:30} | {tracking_src['url']}")
        print()
    
    if missing_in_tracking:
        print("⚠️  Source ID отсутствуют в tracking_sources.json:")
        for source_id in sorted(missing_in_tracking):
            supabase_src = next(src for src in supabase_sources if src['source_id'] == source_id)
            print(f"   - {source_id:20} | {supabase_src['name']:30} | {supabase_src.get('url', 'N/A')}")
        print()
    
    # Проверяем общие источники
    common_sources = tracking_source_ids & supabase_source_ids
    print(f"✅ Общие источники: {len(common_sources)}")
    
    if len(common_sources) > 0:
        print(f"   Примеры: {', '.join(sorted(list(common_sources))[:5])}")
        if len(common_sources) > 5:
            print(f"   ... и еще {len(common_sources) - 5}")
    print()
    
    # Итоговые рекомендации
    if missing_in_supabase or missing_in_tracking:
        print("🔧 Рекомендации:")
        if missing_in_supabase:
            print("   1. Добавить отсутствующие source_id в Supabase sources table")
        if missing_in_tracking:
            print("   2. Добавить отсутствующие источники в tracking_sources.json")
            print("   3. Или удалить неиспользуемые источники из Supabase")
    else:
        print("🎉 Все источники соответствуют между системами!")
    
    print("=" * 80)

if __name__ == "__main__":
    check_source_mapping()
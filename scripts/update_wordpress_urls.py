#!/usr/bin/env python3
"""
Скрипт для обновления WordPress URLs в существующих записях media_files
"""

import sys
import os
import requests
import time
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.config import Config
from core.database import Database
import logging

# Setup logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_wordpress_media_url(wp_api_url: str, wp_media_id: int) -> str:
    """Получить WordPress URL для медиа файла"""
    try:
        response = requests.get(
            f"{wp_api_url}/media/{wp_media_id}",
            timeout=30
        )
        
        if response.status_code == 200:
            media_data = response.json()
            source_url = media_data.get('source_url')
            if source_url:
                return source_url
    except Exception as e:
        logger.error(f"Error getting WP URL for media {wp_media_id}: {e}")
    
    return None

def main():
    """Обновить WordPress URLs для всех загруженных медиа файлов"""
    config = Config()
    db_path = "data/ainews.db"  # Default database path
    db = Database(db_path)
    
    wp_api_url = config.wordpress_api_url
    
    # Получаем все записи с wp_media_id но без wp_source_url
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT id, wp_media_id, article_id
            FROM media_files 
            WHERE wp_media_id IS NOT NULL 
              AND wp_source_url IS NULL
              AND status = 'completed'
        """)
        
        media_to_update = cursor.fetchall()
    
    logger.info(f"Found {len(media_to_update)} media files to update")
    
    updated_count = 0
    failed_count = 0
    
    for media in media_to_update:
        media_id = media['id']
        wp_media_id = media['wp_media_id']
        article_id = media['article_id']
        
        logger.info(f"Processing media {media_id} (WP ID: {wp_media_id}) for article {article_id}")
        
        # Получаем WordPress URL
        wp_source_url = get_wordpress_media_url(wp_api_url, wp_media_id)
        
        if wp_source_url:
            # Обновляем в базе данных
            with db.get_connection() as conn:
                conn.execute("""
                    UPDATE media_files
                    SET wp_source_url = ?
                    WHERE id = ?
                """, (wp_source_url, media_id))
            
            logger.info(f"✅ Updated media {media_id} with URL: {wp_source_url}")
            updated_count += 1
        else:
            logger.warning(f"❌ Failed to get URL for media {media_id} (WP ID: {wp_media_id})")
            failed_count += 1
        
        # Небольшая пауза между запросами
        time.sleep(0.5)
    
    logger.info(f"""
    =====================================
    Update completed:
    - Updated: {updated_count}
    - Failed: {failed_count}
    - Total: {len(media_to_update)}
    =====================================
    """)

if __name__ == "__main__":
    main()
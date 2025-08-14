#!/usr/bin/env python3
"""
Script to fix articles with generic "Article" titles
Generates proper titles from URLs for existing records
"""
import sys
import re
from pathlib import Path
from urllib.parse import urlparse

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app_logging import get_logger
from core.database import Database

logger = get_logger('fix_article_titles')


def generate_title_from_url(url: str) -> str:
    """
    Генерирует заголовок из URL пути
    
    Примеры:
    /blog/ai-powered-hvac-optimization -> "AI Powered HVAC Optimization"
    /news/2024/05/new-model-release -> "New Model Release"
    """
    try:
        parsed = urlparse(url)
        path = parsed.path.rstrip('/')
        
        # Берем последний сегмент пути
        segments = [s for s in path.split('/') if s]
        if not segments:
            return None
            
        # Берем последний значимый сегмент (пропускаем даты и номера)
        title_segment = None
        for segment in reversed(segments):
            # Пропускаем сегменты которые выглядят как даты или номера
            if not re.match(r'^\d{4}$|^\d{2}$|^\d+$|^page-\d+$', segment):
                title_segment = segment
                break
                
        if not title_segment:
            return None
            
        # Преобразуем дефисы и подчеркивания в пробелы
        title = title_segment.replace('-', ' ').replace('_', ' ')
        
        # Убираем расширения файлов если есть
        title = re.sub(r'\.(html?|php|aspx?)$', '', title, flags=re.IGNORECASE)
        
        # Капитализируем слова
        title_words = []
        for word in title.split():
            # Не капитализируем короткие служебные слова
            if len(word) <= 2 and word.lower() in ['a', 'an', 'at', 'by', 'in', 'of', 'on', 'or', 'to']:
                title_words.append(word.lower())
            # Сохраняем аббревиатуры в верхнем регистре
            elif word.isupper() and len(word) > 1:
                title_words.append(word)
            else:
                title_words.append(word.capitalize())
        
        final_title = ' '.join(title_words)
        
        # Проверяем минимальную длину
        if len(final_title) < 3:
            return None
            
        return final_title
        
    except Exception as e:
        logger.warning(f"Error generating title from URL {url}: {e}")
        return None


def fix_tracked_urls_titles():
    """Исправляет заголовки в таблице tracked_urls"""
    db = Database()
    
    # Получаем записи с заголовком "Article"
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT id, article_url, article_title, source_domain 
            FROM tracked_urls 
            WHERE article_title = 'Article'
        """)
        records = cursor.fetchall()
    
    if not records:
        logger.info("No records with 'Article' title found in tracked_urls")
        return 0
    
    logger.info(f"Found {len(records)} records with 'Article' title in tracked_urls")
    
    fixed_count = 0
    for record in records:
        url_id, article_url, old_title, source_domain = record
        
        # Генерируем новый заголовок из URL
        new_title = generate_title_from_url(article_url)
        
        if not new_title:
            # Fallback к домену
            new_title = f"Article from {source_domain}"
        
        # Обновляем запись
        try:
            with db.get_connection() as conn:
                conn.execute("""
                    UPDATE tracked_urls 
                    SET article_title = ? 
                    WHERE id = ?
                """, (new_title, url_id))
            
            logger.info(f"Fixed title for URL {article_url[:50]}... -> '{new_title}'")
            fixed_count += 1
            
        except Exception as e:
            logger.error(f"Error updating record {url_id}: {e}")
    
    return fixed_count


def fix_articles_titles():
    """Исправляет заголовки в таблице articles"""
    db = Database()
    
    # Получаем записи с заголовком "Article" которые пришли из change_tracking
    with db.get_connection() as conn:
        cursor = conn.execute("""
            SELECT article_id, url, title 
            FROM articles 
            WHERE title = 'Article' 
            AND discovered_via = 'change_tracking'
        """)
        records = cursor.fetchall()
    
    if not records:
        logger.info("No records with 'Article' title found in articles")
        return 0
    
    logger.info(f"Found {len(records)} records with 'Article' title in articles")
    
    fixed_count = 0
    for record in records:
        article_id, article_url, old_title = record
        
        # Генерируем новый заголовок из URL
        new_title = generate_title_from_url(article_url)
        
        if not new_title:
            # Fallback к простому форматированию
            parsed = urlparse(article_url)
            new_title = f"Article from {parsed.netloc}"
        
        # Обновляем запись
        try:
            with db.get_connection() as conn:
                conn.execute("""
                    UPDATE articles 
                    SET title = ? 
                    WHERE article_id = ?
                """, (new_title, article_id))
            
            logger.info(f"Fixed title for article {article_id}: '{old_title}' -> '{new_title}'")
            fixed_count += 1
            
        except Exception as e:
            logger.error(f"Error updating article {article_id}: {e}")
    
    return fixed_count


def main():
    """Main function"""
    logger.info("Starting to fix article titles...")
    
    # Исправляем tracked_urls
    logger.info("\n=== Fixing tracked_urls table ===")
    tracked_fixed = fix_tracked_urls_titles()
    
    # Исправляем articles
    logger.info("\n=== Fixing articles table ===")
    articles_fixed = fix_articles_titles()
    
    # Итоги
    logger.info("\n=== Summary ===")
    logger.info(f"Fixed {tracked_fixed} titles in tracked_urls table")
    logger.info(f"Fixed {articles_fixed} titles in articles table")
    logger.info(f"Total fixed: {tracked_fixed + articles_fixed}")
    
    if tracked_fixed > 0 or articles_fixed > 0:
        logger.info("\n✅ Article titles have been successfully fixed!")
        logger.info("New articles will now be extracted with proper titles from URLs")
    else:
        logger.info("\n✅ No articles with 'Article' title found - everything is good!")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
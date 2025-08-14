#!/usr/bin/env python3
"""
Extract Media Downloader с Playwright - Безопасное скачивание медиа
Использует браузер для обхода защит и неагрессивного скачивания
"""
import os
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import hashlib
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
import sys
import time
import random
import base64

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.db_config import DatabaseConfig
from core.config import Config
from app_logging import get_logger
from PIL import Image

# Load environment variables
load_dotenv()


class ExtractMediaDownloaderPlaywright:
    """
    Скачивание медиа через Playwright
    - Неагрессивное скачивание (1 файл одновременно)
    - Retry логика с экспоненциальной задержкой
    - Обход защит через браузер
    """
    
    def __init__(self):
        self.logger = get_logger('extract_system.media_downloader_playwright')
        self.db = DatabaseConfig.get_database()
        self.config = Config()
        
        # Настройки скачивания (неагрессивные)
        self.max_concurrent = 1  # Только 1 файл одновременно!
        self.max_file_size = self.config.MAX_FILE_SIZE  
        self.min_file_size = self.config.MIN_FILE_SIZE
        self.request_timeout = 30  # 30 секунд на файл
        self.batch_size = 5  # Маленькие батчи
        
        # Задержки (секунды)
        self.delay_between_files = (2, 5)  # Случайная задержка 2-5 сек
        
        # Папка для медиа
        self.media_dir = Path("data/media")
        self.media_dir.mkdir(parents=True, exist_ok=True)
        
        # Поддерживаемые типы
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.svg'}
        self.video_extensions = {'.mp4', '.avi', '.mov', '.webm'}
        
        # Статистика
        self.stats = {
            'processed': 0,
            'downloaded': 0,
            'skipped': 0,
            'failed': 0,
            'total_size': 0
        }
        
        # Browser state
        self.browser_open = False
        
        self.logger.info("ExtractMediaDownloaderPlaywright инициализирован (неагрессивный режим)")
    
    async def __aenter__(self):
        """Async context manager entry"""
        # Playwright будет использоваться через CLI команды
        self.browser_open = True
        self.logger.info("🌐 Готов к работе с браузером")
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        self.browser_open = False
        self.logger.info("✅ Работа завершена")
    
    def _get_article_info(self, article_id: str) -> Optional[Dict[str, Any]]:
        """Получает информацию о статье из БД"""
        try:
            article = self.db.get_article(article_id)
            if article:
                return {
                    'title': article.get('title', 'Unknown'), 
                    'source_id': article.get('source_id', 'unknown')
                }
        except Exception as e:
            self.logger.debug(f"Не удалось получить информацию о статье {article_id}: {e}")
        return None
    
    def _get_file_path(self, url: str, article_id: str) -> Path:
        """Генерирует путь для сохранения файла"""
        # Создаем хеш от URL для уникального имени
        url_hash = hashlib.md5(url.encode()).hexdigest()[:12]
        
        # Определяем расширение
        parsed = urlparse(url)
        path_ext = Path(parsed.path).suffix.lower()
        
        if not path_ext or path_ext not in (self.image_extensions | self.video_extensions):
            path_ext = '.jpg'  # По умолчанию для изображений
        
        # Создаем папку для статьи
        article_dir = self.media_dir / article_id[:8]
        article_dir.mkdir(exist_ok=True)
        
        filename = f"{url_hash}{path_ext}"
        return article_dir / filename
    
    def _validate_image_dimensions(self, file_path: Path) -> Dict[str, Any]:
        """
        Валидирует размеры изображения и возвращает метаданные
        Возвращает: {'valid': bool, 'width': int, 'height': int, 'error': str}
        """
        try:
            with Image.open(file_path) as img:
                width, height = img.size
                
                # Проверяем минимальные размеры
                if width < self.config.MIN_IMAGE_WIDTH or height < self.config.MIN_IMAGE_HEIGHT:
                    return {
                        'valid': False, 
                        'width': width, 
                        'height': height,
                        'error': f'Размеры {width}x{height}px меньше минимальных {self.config.MIN_IMAGE_WIDTH}x{self.config.MIN_IMAGE_HEIGHT}px'
                    }
                
                return {
                    'valid': True, 
                    'width': width, 
                    'height': height,
                    'error': None
                }
                
        except Exception as e:
            return {
                'valid': False, 
                'width': None, 
                'height': None,
                'error': f'Ошибка обработки изображения: {str(e)}'
            }
    
    
    async def _download_single_file(self, media_info: Dict, file_index: int = 1, total_files: int = 1) -> Dict[str, Any]:
        """
        Скачивает один медиа-файл через wget с браузерными заголовками
        """
        import subprocess
        
        media_id = media_info['id']
        url = media_info['url']
        article_id = media_info['article_id']
        source_id = media_info.get('source_id', 'unknown')
        
        # Debug: проверяем media_id
        self.logger.debug(f"DEBUG: Processing media_id={media_id}, url={url[:50]}...")
        
        # Защита от None media_id
        if media_id is None:
            self.logger.error(f"❌ media_id is None для URL: {url[:60]}...")
            return {
                'success': False,
                'media_id': None,
                'url': url,
                'processing_time': 0,
                'error': 'media_id is None'
            }
        
        # Получаем информацию о статье для лучшего логирования
        article_info = self._get_article_info(article_id)
        article_title = article_info.get('title', 'Unknown')[:50] if article_info else 'Unknown'
        
        start_time = time.time()
        
        try:
            self.logger.info(f"📥 Скачиваем медиа для статьи '{article_title}' из источника {source_id}: {url[:60]}...")
            
            # Генерируем путь для сохранения
            file_path = self._get_file_path(url, article_id)
            
            # Определяем referer из URL
            parsed = urlparse(url)
            referer = f"{parsed.scheme}://{parsed.netloc}/"
            
            # Используем wget с браузерными заголовками
            cmd = [
                'wget',
                '--quiet',  # Тихий режим
                '--timeout=30',  # Таймаут 30 сек
                '--tries=1',  # Без повторов (мы сами делаем retry)
                '--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                f'--referer={referer}',
                '--header=Accept: image/webp,image/*,*/*;q=0.8',
                '--header=Accept-Language: en-US,en;q=0.5',
                '--header=Cache-Control: no-cache',
                '-O', str(file_path),  # Выходной файл
                url
            ]
            
            # Запускаем wget
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8', errors='ignore').strip()
                if not error_msg:
                    error_msg = f"wget вернул код {process.returncode}"
                
                # Проверяем типичные ошибки
                if '403' in error_msg or 'Forbidden' in error_msg:
                    raise Exception("403 Forbidden - доступ запрещен")
                elif '404' in error_msg or 'Not Found' in error_msg:
                    raise Exception("404 Not Found - файл не найден")
                else:
                    raise Exception(f"wget error: {error_msg}")
            
            # Проверяем что файл существует
            if not file_path.exists():
                raise Exception("Файл не был создан")
            
            # Получаем размер файла
            actual_size = file_path.stat().st_size
            
            if actual_size == 0:
                os.remove(file_path)
                raise Exception("Скачан пустой файл")
            
            # Проверяем размер файла
            if actual_size < self.min_file_size:
                os.remove(file_path)
                raise Exception(f"Файл слишком маленький: {actual_size} < {self.min_file_size}")
            
            if actual_size > self.max_file_size:
                os.remove(file_path)
                raise Exception(f"Файл слишком большой: {actual_size} > {self.max_file_size}")
            
            # Определяем тип медиа по расширению
            ext = file_path.suffix.lower()
            if ext in self.video_extensions:
                media_type = 'video'
                width, height = None, None  # Для видео не проверяем размеры
            else:
                media_type = 'image'
                
                # Валидируем размеры изображения
                validation_result = self._validate_image_dimensions(file_path)
                if not validation_result['valid']:
                    os.remove(file_path)
                    raise Exception(f"Изображение не прошло валидацию: {validation_result['error']}")
                
                width = validation_result['width']
                height = validation_result['height']
                self.logger.info(f"✅ Изображение прошло валидацию: {width}x{height}px")
            
            # Обновляем БД с размерами изображения
            self.db.update_media_file(
                media_id=str(media_id),
                file_path=str(file_path),
                file_size=actual_size,
                width=width,
                height=height,
                status='completed'
            )
            
            processing_time = time.time() - start_time
            
            # Log successful media download
            from app_logging import log_operation
            log_operation(f'✅ Загрузка медиа {file_index}/{total_files} - Успех ({round(actual_size / 1024 / 1024, 2)} MB)',
                media_id=media_id,
                article_id=article_id,
                file_index=file_index,
                total_files=total_files,
                url=url[:100],  # Truncate URL
                file_size_bytes=actual_size,
                file_size_mb=round(actual_size / 1024 / 1024, 2),
                media_type=media_type,
                width=width,
                height=height,
                duration_seconds=processing_time,
                success=True,
                source_id=source_id
            )
            
            result = {
                'success': True,
                'media_id': media_id,
                'url': url,
                'file_path': str(file_path),
                'file_size': actual_size,
                'media_type': media_type,
                'processing_time': processing_time
            }
            
            self.stats['downloaded'] += 1
            self.stats['total_size'] += actual_size
            
            self.logger.info(f"✅ Успешно скачан медиа-файл для '{article_title}' [{source_id}]: {file_path.name} ({actual_size} bytes, {width}x{height}px) за {processing_time:.1f}с")
            return result
            
        except Exception as e:
            processing_time = time.time() - start_time  
            error_msg = str(e)
            self.logger.debug(f"DEBUG: Exception caught for media_id {media_id}: {error_msg}")
            
            # Log failed media download
            from app_logging import log_operation
            failure_reason = '403_forbidden' if '403' in error_msg or 'Forbidden' in error_msg else \
                           '404_not_found' if '404' in error_msg or 'Not Found' in error_msg else \
                           'timeout' if 'timeout' in error_msg.lower() else \
                           'file_too_small' if 'слишком маленький' in error_msg else \
                           'file_too_large' if 'слишком большой' in error_msg else \
                           'validation_failed' if 'валидация' in error_msg else \
                           'download_error'
            
            actual_size = locals().get('actual_size', 0) if 'file_path' in locals() and Path(file_path).exists() else 0
            
            log_operation(f'❌ Ошибка скачивания медиа {file_index}/{total_files}: {error_type}',
                media_id=media_id,
                article_id=article_id,
                file_index=file_index,
                total_files=total_files,
                url=url[:100],  # Truncate URL
                file_size_bytes=actual_size,
                duration_seconds=processing_time,
                success=False,
                failure_reason=failure_reason,
                error_message=error_msg[:200],  # Truncate error
                source_id=source_id
            )
            
            # Удаляем неполный файл если есть
            if 'file_path' in locals() and Path(file_path).exists():
                try:
                    os.remove(file_path)
                except:
                    pass
            
            # Обновляем БД со статусом failed
            try:
                success = self.db.update_media_file(
                    media_id=str(media_id),
                    status='failed'
                )
                if not success:
                    self.logger.warning(f"⚠️ Failed to update media_id {media_id} to failed status")
            except Exception as db_error:
                self.logger.error(f"❌ Ошибка обновления БД для {media_id}: {db_error}")
            
            result = {
                'success': False,
                'media_id': media_id,
                'url': url,
                'processing_time': processing_time,
                'error': error_msg
            }
            
            self.stats['failed'] += 1
            self.logger.error(f"❌ Ошибка скачивания медиа для '{article_title}' [{source_id}] за {processing_time:.1f}с: {error_msg}")
            return result
    
    async def _get_pending_media(self, limit: Optional[int] = None) -> List[Dict]:
        """Получает список медиа для скачивания"""
        try:
            # Используем Supabase для получения pending медиа
            response = self.db.client.table('media_files')\
                .select('id, article_id, url, type, alt_text, caption')\
                .eq('status', 'pending')\
                .order('created_at', desc=False)
            
            if limit:
                response = response.limit(limit)
                
            result = response.execute()
            media_list = result.data if result.data else []
            
            # Конвертируем в нужный формат (id -> media_id compatibility)
            formatted_media = []
            for media in media_list:
                formatted_media.append({
                    'id': media['id'],  # Используем UUID как media_id
                    'article_id': media['article_id'],
                    'url': media['url'],
                    'type': media['type'],
                    'alt_text': media.get('alt_text', ''),
                    'caption': media.get('caption', '')
                })
                
            return formatted_media
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка получения pending медиа: {e}")
            return []
    
    async def download_media_batch(self, media_list: List[Dict]) -> Dict[str, Any]:
        """
        Скачивает батч медиа-файлов ПОСЛЕДОВАТЕЛЬНО с задержками
        """
        if not media_list:
            return {"processed": 0, "downloaded": 0, "failed": 0}
        
        # Собираем статистику по источникам
        sources_count = {}
        for media in media_list:
            source = media.get('source_id', 'unknown')
            sources_count[source] = sources_count.get(source, 0) + 1
        
        sources_info = ', '.join([f"{src}: {cnt}" for src, cnt in sources_count.items()])
        self.logger.info(f"📥 Начинаем скачивание {len(media_list)} медиа-файлов от источников [{sources_info}]")
        
        batch_stats = {
            "processed": 0,
            "downloaded": 0,
            "failed": 0
        }
        
        # Скачиваем последовательно с задержками
        for i, media_info in enumerate(media_list):
            self.stats['processed'] += 1
            batch_stats["processed"] += 1
            
            # Скачиваем файл (без retry) с информацией о прогрессе
            result = await self._download_single_file(media_info, file_index=i+1, total_files=len(media_list))
            
            if result['success']:
                batch_stats["downloaded"] += 1
            else:
                batch_stats["failed"] += 1
            
            # Задержка между файлами (кроме последнего)
            if i < len(media_list) - 1:
                delay = random.uniform(*self.delay_between_files)
                self.logger.info(f"⏱️ Пауза {delay:.1f} сек перед следующим файлом...")
                await asyncio.sleep(delay)
        
        success_rate = (batch_stats["downloaded"] / batch_stats["processed"] * 100) if batch_stats["processed"] > 0 else 0
        
        # Log batch completion
        from app_logging import log_operation
        log_operation(f'✅ Батч завершен: скачано {batch_stats["downloaded"]}/{batch_stats["processed"]} ({round(success_rate, 1)}%), ошибок: {batch_stats["failed"]}',
            files_processed=batch_stats["processed"],
            files_downloaded=batch_stats["downloaded"],
            files_failed=batch_stats["failed"],
            success_rate=round(success_rate, 1),
            total_size_mb=round(self.stats['total_size'] / 1024 / 1024, 2),
            sources_info=sources_info[:200]  # Truncate sources info
        )
        
        self.logger.info(f"✅ Батч завершен: скачано {batch_stats['downloaded']}/{batch_stats['processed']} ({success_rate:.1f}%), ошибок: {batch_stats['failed']}")
        return batch_stats
    
    async def download_all_media(self) -> Dict[str, Any]:
        """
        Скачивает ВСЕ pending медиа файлы маленькими батчами
        """
        self.logger.info("📥 Начинаем неагрессивное скачивание всех pending медиа файлов")
        
        total_stats = {
            "processed": 0,
            "downloaded": 0,
            "failed": 0,
            "batches": 0
        }
        
        try:
            while True:
                # Получаем маленький батч
                pending_media = await self._get_pending_media(limit=self.batch_size)
                
                if not pending_media:
                    self.logger.info("📭 Нет больше pending медиа для скачивания")
                    break
                
                self.logger.info(f"📦 Обрабатываем батч {total_stats['batches'] + 1}: {len(pending_media)} файлов")
                
                # Скачиваем батч
                batch_stats = await self.download_media_batch(pending_media)
                
                # Обновляем общую статистику
                total_stats["processed"] += batch_stats["processed"]
                total_stats["downloaded"] += batch_stats["downloaded"]
                total_stats["failed"] += batch_stats["failed"]
                total_stats["batches"] += 1
                
                # Пауза между батчами
                if pending_media:  # Если были файлы
                    batch_delay = random.uniform(5, 10)
                    self.logger.info(f"⏱️ Пауза {batch_delay:.1f} сек между батчами...")
                    await asyncio.sleep(batch_delay)
                    
        except KeyboardInterrupt:
            self.logger.warning("⚠️ Процесс скачивания прерван пользователем")
        except Exception as e:
            self.logger.error(f"❌ Ошибка во время скачивания: {e}")
        finally:
            # Всегда выводим итоговую статистику
            total_stats["total_size_mb"] = round(self.stats['total_size'] / 1024 / 1024, 2)
            
            # Итоговая статистика
            if total_stats['processed'] > 0:
                success_rate = (total_stats['downloaded'] / total_stats['processed'] * 100)
                avg_size = self.stats['total_size'] / total_stats['downloaded'] if total_stats['downloaded'] > 0 else 0
                self.logger.info(
                    f"🏁 Скачивание завершено: обработано {total_stats['processed']} файлов, "
                    f"успешно скачано {total_stats['downloaded']} ({success_rate:.1f}%), "
                    f"ошибок {total_stats['failed']}, батчей {total_stats['batches']}, "
                    f"средний размер файла {avg_size/1024:.1f}KB"
                )
            else:
                self.logger.info("🏁 Скачивание завершено: нет файлов для обработки")
                
        # После завершения скачивания обновляем media_status для готовых статей
        await self._update_articles_media_status()
        
        return total_stats
    
    async def _update_articles_media_status(self):
        """Обновляет media_status для статей, где все медиафайлы обработаны"""
        try:
            # Получаем статьи с media_status = 'processing'
            processing_articles = self.db.client.table('articles')\
                .select('article_id')\
                .eq('media_status', 'processing')\
                .execute()
            
            updated_count = 0
            for article in processing_articles.data or []:
                article_id = article['article_id']
                
                # Проверяем есть ли pending медиа для этой статьи
                pending_media = self.db.client.table('media_files')\
                    .select('id')\
                    .eq('article_id', article_id)\
                    .eq('status', 'pending')\
                    .limit(1)\
                    .execute()
                
                # Если нет pending медиа - обновляем статус на ready
                if not pending_media.data:
                    success = self.db.update_article_media_status(article_id, 'ready')
                    if success:
                        updated_count += 1
                
            if updated_count > 0:
                self.logger.info(f"✅ Обновлено media_status для {updated_count} статей на 'ready'")
                
        except Exception as e:
            self.logger.error(f"❌ Ошибка обновления media_status: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Возвращает статистику скачивания"""
        return {
            "processed": self.stats['processed'],
            "downloaded": self.stats['downloaded'],
            "skipped": self.stats['skipped'],
            "failed": self.stats['failed'],
            "total_size_mb": round(self.stats['total_size'] / 1024 / 1024, 2),
            "success_rate": (
                self.stats['downloaded'] / max(1, self.stats['processed']) * 100
            )
        }


# Тестовая функция
async def test_playwright_downloader():
    """Тестирует Playwright скачиватель"""
    logger = get_logger('extract_system.test')
    
    async with ExtractMediaDownloaderPlaywright() as downloader:
        # Тестируем на одном файле
        test_media = [{
            'id': 1,
            'article_id': 'test123',
            'url': 'https://www.google.com/images/branding/googlelogo/2x/googlelogo_color_272x92dp.png',
            'type': 'image',
            'alt_text': 'Google Logo',
            'caption': None
        }]
        
        logger.info("🧪 Тестируем скачивание одного файла")
        result = await downloader.download_media_batch(test_media)
        
        logger.info(f"✅ Результат теста: {result}")
        logger.info(f"📊 Статистика: {downloader.get_statistics()}")


if __name__ == "__main__":
    asyncio.run(test_playwright_downloader())
#!/usr/bin/env python3
"""
Single Article Pipeline - обработка статей по одной через весь цикл
"""
import asyncio
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from enum import Enum

from core.database import Database
from core.config import Config
from app_logging import get_logger, LogContext
from services.content_parser import ContentParser
from services.media_processor import ExtractMediaDownloaderPlaywright
from services.wordpress_publisher import WordPressPublisher

logger = get_logger('core.single_pipeline')

class PipelineStatus(Enum):
    RUNNING = "running"
    PAUSED = "paused" 
    STOPPED = "stopped"
    ERROR = "error"

class SingleArticlePipeline:
    """Пайплайн обработки статей по одной через весь цикл"""
    
    def __init__(self):
        self.db = Database()
        self.config = Config()
        self.status = PipelineStatus.STOPPED
        self.current_article = None
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        self.wordpress_published = 0  # Счетчик опубликованных в WordPress
        self.start_time = None
        self.stop_requested = False
        
        # Создаем парсер один раз для всего пайплайна
        self.content_parser = None
        self.media_downloader = None
        
        # Статистика по фазам
        self.phase_stats = {
            'parsing': {'success': 0, 'failed': 0},
            'media': {'success': 0, 'failed': 0},
            'wordpress_prep': {'success': 0, 'failed': 0},
            'wordpress_pub': {'success': 0, 'failed': 0}
        }
        
        # WebSocket коллбэки для мониторинга
        self.callbacks = {
            'on_status_change': None,
            'on_article_start': None,
            'on_phase_complete': None,
            'on_article_complete': None,
            'on_error': None
        }
    
    def set_callback(self, event: str, callback):
        """Установить callback для WebSocket уведомлений"""
        if event in self.callbacks:
            self.callbacks[event] = callback
    
    async def _notify(self, event: str, data: Dict[str, Any]):
        """Отправить уведомление через callback"""
        if self.callbacks.get(event):
            try:
                await self.callbacks[event](data)
            except Exception as e:
                logger.error(f"Callback error for {event}: {e}")
    
    def get_next_article(self) -> Optional[Dict[str, Any]]:
        """Получить следующую статью для обработки"""
        try:
            with self.db.get_connection() as conn:
                # Берем pending статьи или parsed с готовыми медиа
                # Простая очередь FIFO - первая пришла, первая обработана
                cursor = conn.execute("""
                    SELECT article_id, title, url, source_id, content_status, media_status
                    FROM articles 
                    WHERE content_status IN ('pending', 'parsed')
                      AND (content_status = 'pending' OR media_status = 'ready')
                    ORDER BY created_at ASC
                    LIMIT 1
                """)
                
                row = cursor.fetchone()
                if row:
                    article = dict(row)
                    logger.info(f"📎 Next article: {article['article_id']} - {article['title'][:50]} (status: {article['content_status']}, media: {article.get('media_status', 'pending')})")
                    return article
                    
        except Exception as e:
            logger.error(f"Error getting next article: {e}")
        
        return None
    
    async def process_single_article(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Внутренняя реализация обработки статьи"""
        self.current_article = article
        article_id = article['article_id']
        title = article['title'][:50]
        
        result = {
            'article_id': article_id,
            'title': title,
            'phases_completed': [],
            'phases_failed': [],
            'success': False,
            'error': None
        }
        
        # Статья уже захвачена в get_next_article
        
        await self._notify('on_article_start', {
            'article_id': article_id,
            'title': title,
            'status': article['content_status']
        })
        
        try:
            with LogContext.article(article_id=article_id, article_title=title):
                logger.info(f"🚀 Начинаем обработку статьи: {title}")
                
                # Phase 2: Content Parsing (если pending)
                if article['content_status'] == 'pending':
                    phase_result = await self._phase_content_parsing(article)
                    if phase_result['success']:
                        result['phases_completed'].append('parsing')
                        self.phase_stats['parsing']['success'] += 1
                        article['content_status'] = 'parsed'  # Обновляем локальное состояние
                    else:
                        result['phases_failed'].append('parsing')
                        self.phase_stats['parsing']['failed'] += 1
                        result['error'] = phase_result.get('error')
                        logger.warning(f"⚠️ Phase 2 failed for {article_id}, article marked as 'failed' in DB. Completing this article.")
                        # Не продолжаем дальнейшие фазы, но завершаем обработку статьи корректно
                        result['success'] = False
                        # Логируем что последующие фазы пропускаются из-за ошибки парсинга
                        from app_logging import log_operation
                        log_operation('⏭️ Последующие фазы пропущены: парсинг не удался',
                            phase='pipeline',
                            reason='parsing_failed',
                            article_id=article_id,
                            skipped_phases=['media_processing', 'wordpress_prep', 'wordpress_pub']
                        )
                        return result  # ОТКАТ: return нужен для прерывания при ошибках
                
                # Phase 3: Media Processing (если есть медиа)
                if article['content_status'] == 'parsed':
                    media_count = self._get_article_media_count(article_id)
                    logger.info(f"📊 Media files count: {media_count}")
                    
                    if media_count > 0:
                        logger.info(f"🖼️ Processing {media_count} media files...")
                        phase_result = await self._phase_media_processing(article)
                        if phase_result['success']:
                            result['phases_completed'].append('media')
                            self.phase_stats['media']['success'] += 1
                            article['media_status'] = 'ready'
                            # ВАЖНО: Обновляем статус в БД тоже!
                            self._update_media_status(article_id, 'ready')
                        else:
                            result['phases_failed'].append('media')
                            self.phase_stats['media']['failed'] += 1
                            # ИСПРАВЛЕНИЕ КРИТИЧЕСКОГО БАГА: Медиа ошибки НЕ должны блокировать WordPress!
                            # Устанавливаем media_status = 'ready' чтобы процесс продолжился
                            logger.warning("Media processing failed, but continuing to WordPress phases...")
                            article['media_status'] = 'ready'
                            self._update_media_status(article_id, 'ready')
                    else:
                        logger.info("📭 No media files, marking as ready")
                        self._update_media_status(article_id, 'ready')
                        article['media_status'] = 'ready'
                    
                    # Обновляем статус статьи на parsed (в этой системе нет completed)
                    logger.info("✅ Article parsed, keeping status as 'parsed'")
                    # Статус уже обновлен в ContentParser на 'parsed'
                    article['content_status'] = 'parsed'
                
                    # Phase 4: WordPress Preparation (если ready)
                    logger.info(f"Checking WordPress phases: media_status={article['media_status']}")
                    if article['media_status'] == 'ready':
                        logger.info("Media is ready, checking WordPress preparation...")
                        # Проверяем, не переведена ли уже
                        if not self._is_wordpress_prepared(article_id):
                            logger.info("Article not prepared for WordPress, starting Phase 4...")
                            phase_result = await self._phase_wordpress_preparation(article)
                            if phase_result['success']:
                                result['phases_completed'].append('wordpress_prep')
                                self.phase_stats['wordpress_prep']['success'] += 1
                            else:
                                result['phases_failed'].append('wordpress_prep')
                                self.phase_stats['wordpress_prep']['failed'] += 1
                                result['error'] = phase_result.get('error')
                                return result  # ОТКАТ: return нужен для прерывания при ошибках
                        
                        # Phase 5: WordPress Publishing
                        if not self._is_wordpress_published(article_id):
                            phase_result = await self._phase_wordpress_publishing(article)
                            if phase_result['success']:
                                result['phases_completed'].append('wordpress_pub')
                                self.phase_stats['wordpress_pub']['success'] += 1
                                result['success'] = True
                            else:
                                result['phases_failed'].append('wordpress_pub')
                                self.phase_stats['wordpress_pub']['failed'] += 1
                                result['error'] = phase_result.get('error')
                                return result  # ОТКАТ: return нужен для прерывания при ошибках
                
                result['success'] = True  # ОТКАТ: установка success для успешно обработанных статей
                logger.info(f"✅ Статья успешно обработана: {title}")
                
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при обработке {article_id}: {e}")
            result['error'] = str(e)
        
        finally:
            await self._notify('on_article_complete', result)
            self.current_article = None
        
        return result
    
    async def _phase_content_parsing(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 2: Content Parsing"""
        logger.info("📄 Phase 2: Content Parsing")
        
        # Log phase start
        import time
        from app_logging import log_operation, log_error
        
        phase_start = time.time()
        article_title = article.get('title', 'Unknown Article')[:50] + '...' if len(article.get('title', '')) > 50 else article.get('title', 'Unknown Article')
        log_operation(f'Парсинг контента: {article_title}', 
                     phase='content_parsing', 
                     article_id=article['article_id'],
                     article_title=article_title)
        
        try:
            # Используем ContentParser через async context manager
            async with ContentParser() as parser:
                    result = await parser.parse_single_article(
                        article_id=article['article_id'],
                        url=article['url'],
                        source_id=article['source_id']
                    )
                    
                    await self._notify('on_phase_complete', {
                        'phase': 'parsing',
                        'success': result.get('success', False),
                        'article_id': article['article_id']
                    })
                    
                    if result.get("success"):
                        logger.info(f"✅ Successfully parsed: {result.get('content_length', 0)} chars")
                        # Log phase completion
                        log_operation(f'✅ Контент извлечен: {result.get("content_length", 0)} символов, {result.get("word_count", 0)} слов',
                            phase='content_parsing',
                            article_id=article['article_id'],
                            duration_seconds=time.time() - phase_start,
                            success=True,
                            content_length=result.get('content_length', 0),
                            word_count=result.get('word_count', 0)
                        )
                        return {'success': True}
                    else:
                        error_msg = result.get('error', 'Unknown parsing error')
                        logger.error(f"❌ Parsing failed: {error_msg}")
                        log_operation(f'❌ Парсинг неудачен: {error_msg}',
                            phase='content_parsing', 
                            success=False,
                            article_id=article['article_id'],
                            error_reason=error_msg
                        )
                        return {'success': False, 'error': error_msg}
        
        except Exception as e:
            error_msg = f"Content parsing failed: {e}"
            logger.error(error_msg)
            log_operation(f'❌ Критическая ошибка парсинга: {str(e)[:50]}...',
                phase='content_parsing', 
                success=False,
                article_id=article['article_id'],
                error_reason='critical_exception',
                error_message=str(e)[:100]
            )
            return {'success': False, 'error': error_msg}
    
    async def _phase_media_processing(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 3: Media Processing"""
        logger.info("🖼️ Phase 3: Media Processing")
        
        # Log phase start
        import time
        from app_logging import log_operation, log_error
        phase_start = time.time()
        media_count = self._get_article_media_count(article['article_id'])
        log_operation(f'Обработка медиа: {media_count} файлов',
                     phase='media_processing', 
                     article_id=article['article_id'],
                     media_count=media_count)
        
        try:
            async with ExtractMediaDownloaderPlaywright() as downloader:
                # Получаем медиа для конкретной статьи
                media_list = await self._get_article_media(article['article_id'])
                
                if not media_list:
                    logger.info("No media files found for article")
                    result = {'success': True, 'processed': 0}
                else:
                    # Обрабатываем медиа для этой статьи
                    result = await downloader.download_media_batch(media_list)
            
            # Log media processing result
            downloaded = result.get('downloaded', 0)
            processed = result.get('processed', 0)
            if downloaded > 0:
                log_operation(f'✅ Медиа загружено: {downloaded}/{processed} файлов',
                    phase='media_processing',
                    article_id=article['article_id'],
                    duration_seconds=time.time() - phase_start,
                    downloaded=downloaded,
                    processed=processed
                )
            elif processed > 0:
                log_operation(f'⚠️ Медиа не загружено: {processed} файлов не прошли валидацию',
                    phase='media_processing',
                    article_id=article['article_id'],
                    duration_seconds=time.time() - phase_start,
                    downloaded=downloaded,
                    processed=processed
                )
            else:
                log_operation('Медиа файлов не обнаружено',
                    phase='media_processing',
                    article_id=article['article_id'],
                    duration_seconds=time.time() - phase_start
                )
            
            await self._notify('on_phase_complete', {
                'phase': 'media',
                'success': result.get('downloaded', 0) > 0,
                'article_id': article['article_id'],
                'media_processed': result.get('processed', 0)
            })
            
            # ИСПРАВЛЕНИЕ: Медиа failure НЕ критичен для пайплайна
            # Всегда продолжаем процесс, даже если НИ ОДНА картинка не скачалась
            success = True  # Медиа ошибки не блокируют публикацию статьи
            
            return {
                'success': success,
                'processed': result.get('processed', 0),
                'downloaded': result.get('downloaded', 0),
                'original_success': result.get('downloaded', 0) > 0 or result.get('processed', 0) == 0
            }
        
        except Exception as e:
            error_msg = f"Media processing failed: {e}"
            logger.error(error_msg)
            # ИСПРАВЛЕНИЕ: Даже критические ошибки медиа не должны блокировать WordPress
            return {'success': True, 'error': error_msg, 'processed': 0, 'downloaded': 0}
    
    async def _phase_wordpress_preparation(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 4: WordPress Preparation"""
        logger.info("🌐 Phase 4: WordPress Preparation")
        
        # Log phase start
        import time
        from app_logging import log_operation, log_error
        phase_start = time.time()
        log_operation('Перевод и подготовка для WordPress',
                     phase='wordpress_prep', 
                     article_id=article['article_id'])
        
        try:
            from services.wordpress_publisher import WordPressPublisher
            publisher = WordPressPublisher(self.config, self.db)
            
            # Проверяем не обработана ли уже
            if publisher._is_already_processed(article['article_id']):
                logger.info(f"Article {article['article_id']} already processed in WordPress")
                return {'success': True, 'already_processed': True}
            
            # Получаем полные данные статьи из БД
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        a.article_id,
                        a.title,
                        a.content,
                        a.url,
                        a.published_date,
                        a.source_id,
                        s.name as source_name,
                        s.category
                    FROM articles a
                    JOIN sources s ON a.source_id = s.source_id
                    WHERE a.article_id = ?
                """, (article['article_id'],))
                
                row = cursor.fetchone()
                if not row:
                    return {'success': False, 'error': 'Article not found in database'}
                
                full_article = dict(row)
            
            # НОВОЕ: Очищаем плейсхолдеры failed картинок перед отправкой в ЛЛМ
            if full_article.get('content'):
                original_content = full_article['content']
                cleaned_content = self._clean_failed_image_placeholders(original_content, article['article_id'])
                if cleaned_content != original_content:
                    full_article['content'] = cleaned_content
                    logger.info(f"Cleaned failed image placeholders from content for LLM processing")
            
            # Функция для выполнения в event loop
            async def translation_task():
                # Обрабатываем конкретную статью через LLM (синхронный вызов)
                logger.info(f"Processing article {article['article_id']}: {full_article['title'][:50]}...")
                wp_data = await asyncio.get_event_loop().run_in_executor(
                    None, publisher._process_article_with_llm, full_article
                )
                
                if wp_data:
                    # Пауза перед генерацией тегов чтобы не перегружать DeepSeek API
                    logger.info("Waiting 5 seconds before tag generation to avoid API overload...")
                    await asyncio.sleep(5)
                    
                    # Генерируем теги для переведенной статьи
                    try:
                        logger.info("Generating tags for translated article...")
                        tags = await publisher._generate_tags_with_llm(wp_data)
                        wp_data['tags'] = tags
                        logger.info(f"Generated tags: {tags}")
                    except Exception as e:
                        logger.warning(f"Failed to generate tags: {e}, using empty tags")
                        wp_data['tags'] = []
                    
                    # Сохраняем результат с тегами
                    await asyncio.get_event_loop().run_in_executor(
                        None, publisher._save_wordpress_article, article['article_id'], wp_data
                    )
                    logger.info(f"✅ WordPress preparation successful for {article['article_id']}")
                    # Log phase completion
                    log_operation(f'✅ Статья переведена, создано {len(wp_data.get("tags", []))} тегов',
                        phase='wordpress_prep',
                        article_id=article['article_id'],
                        duration_seconds=time.time() - phase_start,
                        success=True,
                        tags_count=len(wp_data.get('tags', []))
                    )
                    return True
                else:
                    logger.error(f"❌ WordPress preparation failed for {article['article_id']}")
                    return False
            
            # Запускаем задачу перевода
            success = await translation_task()
            
            await self._notify('on_phase_complete', {
                'phase': 'wordpress_prep',
                'success': success,
                'article_id': article['article_id']
            })
            
            return {'success': success}
        
        except Exception as e:
            error_msg = f"WordPress preparation failed: {e}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    async def _phase_wordpress_publishing(self, article: Dict[str, Any]) -> Dict[str, Any]:
        """Phase 5: WordPress Publishing"""
        logger.info("📤 Phase 5: WordPress Publishing")
        
        # Log phase start
        import time
        from app_logging import log_operation, log_error
        phase_start = time.time()
        log_operation('Публикация в WordPress',
                     phase='wordpress_pub', 
                     article_id=article['article_id'])
        
        try:
            from services.wordpress_publisher import WordPressPublisher
            publisher = WordPressPublisher(self.config, self.db)
            
            # Получаем данные из wordpress_articles для конкретной статьи
            with self.db.get_connection() as conn:
                cursor = conn.execute("""
                    SELECT 
                        id,
                        title,
                        content,
                        excerpt,
                        slug,
                        categories,
                        tags,
                        _yoast_wpseo_title,
                        _yoast_wpseo_metadesc,
                        focus_keyword,
                        featured_image_index,
                        published_to_wp
                    FROM wordpress_articles
                    WHERE article_id = ? AND translation_status = 'translated'
                """, (article['article_id'],))
                
                row = cursor.fetchone()
                if not row:
                    logger.warning(f"No translated content found for article {article['article_id']}")
                    return {'success': False, 'error': 'Article not translated yet'}
                
                wp_article = dict(row)
                wp_article['article_id'] = article['article_id']
                
                # Проверяем не опубликована ли уже
                if wp_article['published_to_wp']:
                    logger.info(f"Article {article['article_id']} already published")
                    return {'success': True, 'already_published': True}
            
            logger.info(f"Publishing article: {wp_article['title'][:50]}...")
            
            # Подготавливаем данные для WordPress
            wp_post_data = publisher._prepare_wordpress_post(wp_article)
            
            # Создаем пост в WordPress
            wp_post_id = publisher._create_wordpress_post(wp_post_data)
            
            if wp_post_id:
                # Обновляем БД с WordPress post ID
                publisher._mark_as_published(wp_article['id'], wp_post_id)
                logger.info(f"✅ Successfully published article with WordPress ID: {wp_post_id}")
                # Log phase completion
                log_operation(f'✅ Опубликовано: ailynx.ru/?p={wp_post_id}',
                    phase='wordpress_pub',
                    article_id=article['article_id'],
                    duration_seconds=time.time() - phase_start,
                    success=True,
                    wp_post_id=wp_post_id,
                    wp_url=f'https://ailynx.ru/?p={wp_post_id}'
                )
                
                # Обрабатываем медиафайлы
                logger.info(f"Processing media for article {article['article_id']}")
                
                # Пауза после публикации перед обработкой медиа
                import time
                logger.info("Waiting 5 seconds before media processing...")
                time.sleep(5)
                
                media_result = publisher._process_media_for_article(
                    article['article_id'], 
                    wp_post_id,
                    wp_article['title']
                )
                
                if not media_result:
                    logger.warning("Media processing had issues but post was published")
                
                # НОВОЕ: После загрузки медиа обновляем контент с локальными URL
                logger.info(f"Replacing placeholders with local media URLs for post {wp_post_id}")
                updated_content = publisher._replace_image_placeholders(wp_article['content'], article['article_id'])
                
                # Обновляем контент поста в WordPress
                if publisher._update_post_content(wp_post_id, updated_content):
                    logger.info(f"✅ Post {wp_post_id} content updated with local media URLs")
                else:
                    logger.warning(f"⚠️ Failed to update post {wp_post_id} content, using external URLs")
                
                success = True
            else:
                logger.error(f"❌ Failed to create WordPress post for {article['article_id']}")
                success = False
            
            await self._notify('on_phase_complete', {
                'phase': 'wordpress_pub',
                'success': success,
                'article_id': article['article_id'],
                'wp_post_id': wp_post_id if success else None
            })
            
            return {
                'success': success,
                'wp_post_id': wp_post_id if success else None
            }
            
        except Exception as e:
            error_msg = f"WordPress publishing failed: {e}"
            logger.error(error_msg)
            return {'success': False, 'error': error_msg}
    
    async def run_pipeline(self, continuous_mode: bool = False, max_articles: Optional[int] = None, delay_between: int = 5) -> Dict[str, Any]:
        """Запустить пайплайн
        
        Args:
            continuous_mode: Если True, обрабатывает все pending статьи в цикле
            max_articles: Максимальное количество статей для обработки (None = все)
            delay_between: Задержка между статьями в секундах
        """
        self.status = PipelineStatus.RUNNING
        self.start_time = datetime.now()
        self.stop_requested = False
        self.wordpress_published = 0
        
        # Счетчики для continuous mode
        self.processed_count = 0
        self.success_count = 0
        self.error_count = 0
        cycle_count = 0
        
        await self._notify('on_status_change', {
            'status': self.status.value,
            'started_at': self.start_time.isoformat()
        })
        
        # Логирование старта
        from app_logging import log_operation
        
        # Start monitoring session для Single Pipeline
        session_id = None
        if not continuous_mode:
            try:
                import requests
                response = requests.post('http://localhost:8001/api/pipeline/session/start', timeout=1.0)
                if response.status_code == 200:
                    session_id = response.json().get('session_id')
                    logger.info(f"📊 Запущена сессия мониторинга: {session_id}")
            except:
                pass  # Мониторинг может быть не запущен
        
        if continuous_mode:
            logger.info(f"🔄 Запуск CONTINUOUS пайплайна: обработка всех pending статей")
            logger.info(f"   Максимум статей: {max_articles if max_articles else 'без лимита'}")
            logger.info(f"   Задержка между статьями: {delay_between} сек")
            log_operation('continuous_pipeline_start',
                mode='continuous',
                max_articles=max_articles,
                delay_between=delay_between
            )
        else:
            logger.info("🚀 Запуск одноматериального пайплайна: 1 статья от pending до WordPress")
        
        try:
            if continuous_mode:
                # CONTINUOUS MODE: обрабатываем все статьи в цикле
                while not self.stop_requested:
                    cycle_count += 1
                    cycle_start = time.time()
                    
                    # Проверяем лимит
                    if max_articles and self.processed_count >= max_articles:
                        logger.info(f"📊 Достигнут лимит статей: {max_articles}")
                        log_operation('continuous_pipeline_stop',
                            reason='max_reached',
                            total_processed=self.processed_count,
                            total_duration_seconds=time.time() - self.start_time.timestamp()
                        )
                        break
                    
                    # Берем следующую статью
                    article = self.get_next_article()
                    
                    if not article:
                        logger.info("✅ Все pending статьи обработаны!")
                        log_operation('continuous_pipeline_stop',
                            reason='no_more_articles',
                            total_processed=self.processed_count,
                            total_duration_seconds=time.time() - self.start_time.timestamp()
                        )
                        break
                    
                    logger.info(f"\n{'='*60}")
                    logger.info(f"🔄 Цикл #{cycle_count}: Обработка статьи {self.processed_count + 1}/{max_articles if max_articles else '∞'}")
                    logger.info(f"{'='*60}")
                    
                    # Обрабатываем статью
                    result = await self.process_single_article(article)
                    self.processed_count += 1
                    
                    if result['success']:
                        self.success_count += 1
                        if 'wordpress_pub' in result.get('phases_completed', []):
                            self.wordpress_published += 1
                            logger.info("✅ Статья успешно опубликована в WordPress!")
                        else:
                            logger.info("✅ Статья обработана")
                    else:
                        self.error_count += 1
                        logger.error(f"❌ Ошибка обработки: {result.get('error')}")
                    
                    # Логируем завершение цикла
                    log_operation('continuous_cycle_complete',
                        cycle_number=cycle_count,
                        articles_processed=self.processed_count,
                        success_count=self.success_count,
                        failed_count=self.error_count,
                        duration_seconds=time.time() - cycle_start
                    )
                    
                    # Задержка перед следующей статьей (если не последняя)
                    # ИСПРАВЛЕНИЕ: Убрали лишний вызов get_next_article() который создавал фантомные блокировки
                    # Статья должна браться только в начале цикла на строке 676
                    if not self.stop_requested and (not max_articles or self.processed_count < max_articles):
                        logger.info(f"⏳ Ожидание {delay_between} секунд перед следующей статьей...")
                        await asyncio.sleep(delay_between)
                
                # Логируем причину остановки если была остановка пользователем
                if self.stop_requested:
                    logger.info("⏹️ Пайплайн остановлен пользователем")
                    log_operation('continuous_pipeline_stop',
                        reason='user_requested',
                        total_processed=self.processed_count,
                        total_duration_seconds=time.time() - self.start_time.timestamp()
                    )
            
            else:
                # SINGLE MODE: обрабатываем одну статью (оригинальная логика)
                article = self.get_next_article()
                
                if not article:
                    logger.warning("⚠️ Нет pending статей для обработки")
                    return {
                        'status': 'no_articles',
                        'error': 'No pending articles available',
                        'processed_count': 0
                    }
                
                # Обрабатываем ЭТУ статью через все фазы
                result = await self.process_single_article(article)
                
                self.processed_count = 1
                
                if result['success']:
                    self.success_count = 1
                    # Проверяем, дошла ли статья до WordPress
                    if 'wordpress_pub' in result.get('phases_completed', []):
                        self.wordpress_published = 1
                        logger.info("✅ Статья успешно опубликована в WordPress!")
                    else:
                        logger.info("✅ Статья обработана, но не дошла до WordPress")
                else:
                    self.error_count = 1
                    logger.error(f"❌ Ошибка обработки статьи {article['article_id']}: {result.get('error')}")
            
        except Exception as e:
            logger.error(f"❌ Критическая ошибка пайплайна: {e}")
            self.status = PipelineStatus.ERROR
            await self._notify('on_error', {'error': str(e)})
        
        finally:
            # Complete monitoring session для Single Pipeline
            if not continuous_mode and session_id:
                try:
                    import requests
                    requests.post('http://localhost:8001/api/pipeline/session/complete', 
                                json={'total_articles': self.processed_count}, 
                                timeout=1.0)
                    logger.info(f"📊 Завершена сессия мониторинга: {session_id}")
                except:
                    pass  # Мониторинг может быть не запущен
            
            self.status = PipelineStatus.STOPPED
            duration = (datetime.now() - self.start_time).total_seconds()
            
            final_stats = {
                'status': self.status.value,
                'duration_seconds': duration,
                'processed_count': self.processed_count,
                'success_count': self.success_count,
                'error_count': self.error_count,
                'wordpress_published': self.wordpress_published,
                'phase_stats': self.phase_stats
            }
            
            await self._notify('on_status_change', final_stats)
            
            if continuous_mode:
                logger.info(f"\n{'='*60}")
                logger.info(f"🏁 CONTINUOUS PIPELINE ЗАВЕРШЕН")
                logger.info(f"{'='*60}")
                logger.info(f"📊 Итоговая статистика:")
                logger.info(f"   Обработано статей: {self.processed_count}")
                logger.info(f"   Успешно: {self.success_count}")
                logger.info(f"   С ошибками: {self.error_count}")
                logger.info(f"   Опубликовано в WordPress: {self.wordpress_published}")
                logger.info(f"   Общее время: {duration:.1f} сек ({duration/60:.1f} мин)")
                if self.processed_count > 0:
                    logger.info(f"   Среднее время на статью: {duration/self.processed_count:.1f} сек")
                logger.info(f"{'='*60}")
            else:
                logger.info(f"🏁 Пайплайн завершен: 1 статья обработана за {duration:.1f} сек, "
                           f"результат: {'успех' if self.success_count > 0 else 'ошибка'}, "
                           f"WordPress: {'да' if self.wordpress_published > 0 else 'нет'}")
            
            return final_stats
    
    def request_stop(self):
        """Запросить остановку пайплайна"""
        self.stop_requested = True
        self.status = PipelineStatus.STOPPED
        logger.info("⏹️ Запрошена остановка пайплайна")
    
    def pause(self):
        """Приостановить пайплайн"""
        self.status = PipelineStatus.PAUSED
        logger.info("⏸️ Пайплайн приостановлен")
    
    def resume(self):
        """Возобновить пайплайн"""
        if self.status == PipelineStatus.PAUSED:
            self.status = PipelineStatus.RUNNING
            logger.info("▶️ Пайплайн возобновлен")
    
    # Вспомогательные методы для работы с БД
    def _get_article_media_count(self, article_id: str) -> int:
        """Получить количество медиафайлов статьи"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM media_files WHERE article_id = ?",
                    (article_id,)
                )
                return cursor.fetchone()[0]
        except Exception:
            return 0
    
    async def _get_article_media(self, article_id: str) -> List[Dict[str, Any]]:
        """Получить медиафайлы статьи для обработки"""
        try:
            with self.db.get_connection() as conn:
                # Ищем медиа со статусом pending (не скачанные)
                cursor = conn.execute("""
                    SELECT media_id as id, article_id, source_id, url, type, alt_text, caption
                    FROM media_files 
                    WHERE article_id = ? AND status = 'pending'
                """, (article_id,))
                
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Error getting article media: {e}")
            return []
    
    def _update_media_status(self, article_id: str, status: str):
        """Обновить media_status статьи"""
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    "UPDATE articles SET media_status = ? WHERE article_id = ?",
                    (status, article_id)
                )
        except Exception as e:
            logger.error(f"Error updating media status: {e}")
    
    def _update_article_status(self, article_id: str, status: str):
        """Обновить content_status статьи"""
        try:
            with self.db.get_connection() as conn:
                conn.execute(
                    "UPDATE articles SET content_status = ? WHERE article_id = ?",
                    (status, article_id)
                )
        except Exception as e:
            logger.error(f"Error updating article status: {e}")
    
    def _is_wordpress_prepared(self, article_id: str) -> bool:
        """Проверить, подготовлена ли статья для WordPress"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id FROM wordpress_articles WHERE article_id = ? AND translation_status = 'translated'",
                    (article_id,)
                )
                return cursor.fetchone() is not None
        except Exception:
            return False
    
    def _is_wordpress_published(self, article_id: str) -> bool:
        """Проверить, опубликована ли статья в WordPress"""
        try:
            with self.db.get_connection() as conn:
                cursor = conn.execute(
                    "SELECT id FROM wordpress_articles WHERE article_id = ? AND published_to_wp = 1",
                    (article_id,)
                )
                return cursor.fetchone() is not None
        except Exception:
            return False
    
    def _clean_failed_image_placeholders(self, content: str, article_id: str) -> str:
        """
        Убирает плейсхолдеры [IMAGE_N] для картинок которые failed при обработке
        
        Args:
            content: Контент статьи с плейсхолдерами
            article_id: ID статьи для проверки медиа статуса
            
        Returns:
            Очищенный контент без плейсхолдеров failed картинок
        """
        import re
        
        try:
            with self.db.get_connection() as conn:
                # Получаем список медиа файлов со статусом failed или pending
                cursor = conn.execute("""
                    SELECT url, alt_text, status, image_order
                    FROM media_files 
                    WHERE article_id = ?
                    ORDER BY image_order
                """, (article_id,))
                
                media_files = cursor.fetchall()
                
                # Собираем номера failed/pending картинок
                failed_image_numbers = []
                for row in media_files:
                    if row['status'] in ('failed', 'pending') and row['image_order'] is not None:
                        failed_image_numbers.append(row['image_order'])
                
                # Убираем плейсхолдеры failed картинок
                cleaned_content = content
                for image_num in failed_image_numbers:
                    placeholder = f"[IMAGE_{image_num}]"
                    cleaned_content = cleaned_content.replace(placeholder, "")
                    logger.info(f"Removed placeholder {placeholder} for failed media")
                
                # Убираем лишние пробелы и переносы строк
                cleaned_content = re.sub(r'\n\s*\n', '\n\n', cleaned_content)
                cleaned_content = re.sub(r'  +', ' ', cleaned_content)
                
                return cleaned_content
                
        except Exception as e:
            logger.error(f"Error cleaning image placeholders: {e}")
            return content
    
    def get_status(self) -> Dict[str, Any]:
        """Получить текущий статус пайплайна"""
        return {
            'status': self.status.value,
            'current_article': self.current_article,
            'processed_count': self.processed_count,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'phase_stats': self.phase_stats,
            'start_time': self.start_time.isoformat() if self.start_time else None
        }
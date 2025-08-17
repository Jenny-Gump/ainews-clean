#!/usr/bin/env python3
"""
Process Supervisor для изоляции источников и предотвращения зависаний.
Каждый источник запускается в отдельном процессе с жёстким таймаутом.
"""
import subprocess
import sys
import json
import time
from typing import Dict, List, Any, Optional
from pathlib import Path
from app_logging import get_logger


class ProcessSupervisor:
    """
    Супервайзер для запуска каждого источника в изолированном процессе.
    Гарантирует, что зависший источник не блокирует всю систему.
    """
    
    def __init__(self, timeout_per_source: int = 60):
        """
        Args:
            timeout_per_source: Максимальное время на обработку одного источника (секунды)
        """
        self.logger = get_logger('process_supervisor')
        self.timeout = timeout_per_source
        self.stats = {
            'processed': 0,
            'successful': 0,
            'skipped': 0,
            'killed': 0,
            'errors': 0
        }
        
    def run_rss_source(self, source_id: str) -> Dict[str, Any]:
        """
        Запускает обработку одного RSS источника в изолированном процессе.
        
        Args:
            source_id: ID источника для обработки
            
        Returns:
            Результат обработки или статус ошибки/таймаута
        """
        start_time = time.time()
        
        # Подготовка команды для запуска в subprocess
        script = f"""
import sys
import asyncio
import aiohttp
sys.path.append('{Path.cwd()}')

from services.rss_discovery import ExtractRSSDiscovery

async def process_single_source():
    discovery = ExtractRSSDiscovery()
    source = next((s for s in discovery.rss_sources if s['id'] == '{source_id}'), None)
    if not source:
        return {{'status': 'error', 'message': 'Source not found'}}
    
    async with aiohttp.ClientSession() as session:
        source_id, articles = await discovery.fetch_rss_feed(session, source)
        return {{'status': 'success', 'source_id': source_id, 'articles': len(articles)}}

import json
result = asyncio.run(process_single_source())
print(json.dumps(result))
"""
        
        try:
            # Запускаем процесс с жёстким таймаутом
            result = subprocess.run(
                [sys.executable, '-c', script],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            elapsed = time.time() - start_time
            
            if result.returncode == 0:
                # Парсим результат
                try:
                    output = json.loads(result.stdout)
                    self.stats['successful'] += 1
                    self.logger.info(
                        f"✅ {source_id} processed in {elapsed:.1f}s - "
                        f"{output.get('articles', 0)} articles"
                    )
                    return output
                except json.JSONDecodeError:
                    self.stats['errors'] += 1
                    self.logger.error(f"❌ {source_id} - invalid output: {result.stdout[:200]}")
                    return {'status': 'error', 'message': 'Invalid JSON output'}
            else:
                # Процесс завершился с ошибкой
                self.stats['errors'] += 1
                error_msg = result.stderr[:500] if result.stderr else 'Unknown error'
                self.logger.error(f"❌ {source_id} failed: {error_msg}")
                return {'status': 'error', 'message': error_msg}
                
        except subprocess.TimeoutExpired:
            # Процесс превысил таймаут - убиваем его
            self.stats['killed'] += 1
            self.logger.warning(
                f"⏱️ {source_id} KILLED after {self.timeout}s timeout"
            )
            return {'status': 'killed', 'message': f'Timeout after {self.timeout}s'}
            
        except Exception as e:
            # Неожиданная ошибка
            self.stats['errors'] += 1
            self.logger.error(f"❌ {source_id} unexpected error: {str(e)}")
            return {'status': 'error', 'message': str(e)}
        
        finally:
            self.stats['processed'] += 1
    
    def run_change_tracking_source(self, url: str) -> Dict[str, Any]:
        """
        Запускает сканирование одной страницы Change Tracking в изолированном процессе.
        
        Args:
            url: URL страницы для сканирования
            
        Returns:
            Результат сканирования или статус ошибки/таймаута
        """
        start_time = time.time()
        
        # Подготовка команды для запуска в subprocess
        script = f"""
import sys
import asyncio
sys.path.append('{Path.cwd()}')

from change_tracking.monitor import ChangeMonitor

async def scan_single_page():
    monitor = ChangeMonitor()
    # Важно: отключаем retry для простоты
    result = await monitor.scan_webpage('{url}', max_retries=1)
    return result

import json
result = asyncio.run(scan_single_page())
print(json.dumps(result))
"""
        
        try:
            # Запускаем процесс с жёстким таймаутом
            result = subprocess.run(
                [sys.executable, '-c', script],
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            
            elapsed = time.time() - start_time
            
            if result.returncode == 0:
                # Парсим результат
                try:
                    output = json.loads(result.stdout)
                    status = output.get('status', 'unknown')
                    
                    if status != 'error':
                        self.stats['successful'] += 1
                        self.logger.info(f"✅ {url[:50]}... - {status} in {elapsed:.1f}s")
                    else:
                        self.stats['skipped'] += 1
                        self.logger.warning(f"⚠️ {url[:50]}... - skipped: {output.get('error', 'Unknown')}")
                    
                    return output
                    
                except json.JSONDecodeError:
                    self.stats['errors'] += 1
                    self.logger.error(f"❌ {url[:50]}... - invalid output")
                    return {'status': 'error', 'message': 'Invalid JSON output'}
            else:
                # Процесс завершился с ошибкой
                self.stats['errors'] += 1
                error_msg = result.stderr[:500] if result.stderr else 'Unknown error'
                self.logger.error(f"❌ {url[:50]}... failed: {error_msg}")
                return {'status': 'error', 'message': error_msg}
                
        except subprocess.TimeoutExpired:
            # Процесс превысил таймаут - убиваем его
            self.stats['killed'] += 1
            self.logger.warning(f"⏱️ {url[:50]}... KILLED after {self.timeout}s")
            return {'status': 'killed', 'message': f'Timeout after {self.timeout}s'}
            
        except Exception as e:
            # Неожиданная ошибка
            self.stats['errors'] += 1
            self.logger.error(f"❌ {url[:50]}... unexpected error: {str(e)}")
            return {'status': 'error', 'message': str(e)}
        
        finally:
            self.stats['processed'] += 1
    
    def run_all_rss_sources(self, source_ids: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Обрабатывает все RSS источники последовательно с изоляцией.
        
        Args:
            source_ids: Список ID источников (если None - все источники)
            
        Returns:
            Общая статистика обработки
        """
        self.logger.info(f"🚀 Starting RSS Discovery with {self.timeout}s timeout per source")
        
        # Получаем список источников
        from services.rss_discovery import ExtractRSSDiscovery
        discovery = ExtractRSSDiscovery()
        
        if source_ids:
            sources = [s for s in discovery.rss_sources if s['id'] in source_ids]
        else:
            sources = discovery.rss_sources
        
        self.logger.info(f"📋 Processing {len(sources)} RSS sources")
        
        # Обрабатываем каждый источник
        results = []
        for i, source in enumerate(sources, 1):
            self.logger.info(f"[{i}/{len(sources)}] Processing {source['id']}...")
            result = self.run_rss_source(source['id'])
            results.append(result)
            
            # Показываем прогресс
            if i % 5 == 0:
                self.logger.info(
                    f"Progress: {i}/{len(sources)} | "
                    f"Success: {self.stats['successful']} | "
                    f"Killed: {self.stats['killed']} | "
                    f"Errors: {self.stats['errors']}"
                )
        
        # Финальная статистика
        self.logger.info("=" * 60)
        self.logger.info(f"✅ RSS Discovery completed:")
        self.logger.info(f"  📊 Total processed: {self.stats['processed']}")
        self.logger.info(f"  ✅ Successful: {self.stats['successful']}")
        self.logger.info(f"  ⏱️ Killed (timeout): {self.stats['killed']}")
        self.logger.info(f"  ⚠️ Skipped: {self.stats['skipped']}")
        self.logger.info(f"  ❌ Errors: {self.stats['errors']}")
        
        return {
            'stats': self.stats,
            'results': results
        }
    
    def get_stats(self) -> Dict[str, int]:
        """Возвращает текущую статистику"""
        return self.stats.copy()


# CLI interface для тестирования
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Process Supervisor for RSS/Change Tracking')
    parser.add_argument('--mode', choices=['rss', 'change-tracking'], required=True,
                       help='Mode to run: rss or change-tracking')
    parser.add_argument('--timeout', type=int, default=60,
                       help='Timeout per source in seconds (default: 60)')
    parser.add_argument('--sources', nargs='+',
                       help='Specific source IDs to process (for RSS mode)')
    parser.add_argument('--url', help='URL to scan (for change-tracking mode)')
    
    args = parser.parse_args()
    
    supervisor = ProcessSupervisor(timeout_per_source=args.timeout)
    
    if args.mode == 'rss':
        # RSS Discovery mode
        result = supervisor.run_all_rss_sources(args.sources)
        print(json.dumps(result['stats'], indent=2))
        
    elif args.mode == 'change-tracking':
        # Change Tracking mode
        if not args.url:
            print("ERROR: --url required for change-tracking mode")
            sys.exit(1)
        
        result = supervisor.run_change_tracking_source(args.url)
        print(json.dumps(result, indent=2))
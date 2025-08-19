#!/usr/bin/env python3
"""
Скрипт диагностики errors.jsonl - анализ ошибок извлечения данных
Показывает проблемные источники и типы ошибок с причинами
"""

import json
import sys
import os
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Добавляем путь к корневой директории проекта
sys.path.append(str(Path(__file__).parent.parent))

class ErrorDiagnostics:
    """Диагностика ошибок из errors.jsonl"""
    
    def __init__(self, log_file_path: Optional[str] = None):
        self.log_file_path = log_file_path or "/Users/skynet/Desktop/AI DEV/ainews-clean/logs/errors.jsonl"
        self.errors = []
        
    def load_errors(self, hours_back: int = 24) -> int:
        """Загружает ошибки из файла за последние N часов"""
        if not os.path.exists(self.log_file_path):
            print(f"❌ Файл логов не найден: {self.log_file_path}")
            return 0
        
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        loaded_count = 0
        
        try:
            with open(self.log_file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        error_entry = json.loads(line)
                        
                        # Проверяем время ошибки
                        timestamp_str = error_entry.get('timestamp', '')
                        if timestamp_str:
                            error_time = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                            if error_time.replace(tzinfo=None) >= cutoff_time:
                                self.errors.append(error_entry)
                                loaded_count += 1
                        else:
                            # Если нет timestamp, включаем в анализ
                            self.errors.append(error_entry)
                            loaded_count += 1
                            
                    except json.JSONDecodeError as e:
                        print(f"⚠️ Некорректная JSON строка {line_num}: {e}")
                        continue
                        
        except Exception as e:
            print(f"❌ Ошибка чтения файла: {e}")
            return 0
            
        return loaded_count
    
    def analyze_data_extraction_errors(self) -> Dict[str, Any]:
        """Анализирует ошибки извлечения данных из источников"""
        
        # Фильтруем ошибки связанные с извлечением данных
        extraction_error_types = {
            'rss_http_error', 'rss_timeout', 'rss_parse_warning', 'rss_general_error',
            'tracking_scan_failed', 'tracking_timeout', 'tracking_fk_error', 'tracking_db_error',
            'content_parsing_failed', 'content_parsing_critical_error', 'article_parsing_failed',
            'firecrawl_error', 'redirect_resolve_failed', 'job_status_check_failed',
            'pending_articles_fetch_failed', 'content_save_failed'
        }
        
        extraction_errors = [
            error for error in self.errors 
            if error.get('error_type') in extraction_error_types
        ]
        
        if not extraction_errors:
            return {'total': 0, 'by_type': {}, 'by_source': {}, 'recent': []}
        
        # Группировка по типам ошибок
        by_type = Counter(error.get('error_type') for error in extraction_errors)
        
        # Группировка по источникам (source_id, url)
        source_errors = defaultdict(list)
        for error in extraction_errors:
            source_key = error.get('source_id') or error.get('url') or 'unknown'
            source_errors[source_key].append(error)
        
        # Топ источников с ошибками
        by_source = {
            source: len(errors) 
            for source, errors in source_errors.items()
        }
        
        # Последние ошибки
        recent_errors = sorted(
            extraction_errors, 
            key=lambda x: x.get('timestamp', ''), 
            reverse=True
        )[:10]
        
        return {
            'total': len(extraction_errors),
            'by_type': dict(by_type),
            'by_source': dict(sorted(by_source.items(), key=lambda x: x[1], reverse=True)),
            'recent': recent_errors,
            'source_details': dict(source_errors)
        }
    
    def analyze_pipeline_errors(self) -> Dict[str, Any]:
        """Анализирует ошибки пайплайна обработки"""
        
        pipeline_error_types = {
            'pipeline_critical_error', 'pipeline_fatal_error', 'system_critical_error',
            'wordpress_preparation_failed', 'wordpress_publishing_failed',
            'media_download_critical_error', 'pending_media_fetch_failed'
        }
        
        pipeline_errors = [
            error for error in self.errors 
            if error.get('error_type') in pipeline_error_types
        ]
        
        if not pipeline_errors:
            return {'total': 0, 'by_type': {}, 'recent': []}
        
        by_type = Counter(error.get('error_type') for error in pipeline_errors)
        
        recent_errors = sorted(
            pipeline_errors, 
            key=lambda x: x.get('timestamp', ''), 
            reverse=True
        )[:5]
        
        return {
            'total': len(pipeline_errors),
            'by_type': dict(by_type),
            'recent': recent_errors
        }
    
    def find_dead_sources(self, min_errors: int = 3) -> List[Dict[str, Any]]:
        """Находит 'мертвые' источники с частыми ошибками"""
        
        extraction_analysis = self.analyze_data_extraction_errors()
        dead_sources = []
        
        for source, error_count in extraction_analysis['by_source'].items():
            if error_count >= min_errors:
                source_errors = extraction_analysis['source_details'][source]
                
                # Анализируем типы ошибок для этого источника
                error_types = Counter(error.get('error_type') for error in source_errors)
                
                # Последняя ошибка
                latest_error = max(source_errors, key=lambda x: x.get('timestamp', ''))
                
                dead_sources.append({
                    'source': source,
                    'error_count': error_count,
                    'error_types': dict(error_types),
                    'latest_error': latest_error.get('timestamp'),
                    'latest_message': latest_error.get('message', '')[:100] + '...'
                })
        
        return sorted(dead_sources, key=lambda x: x['error_count'], reverse=True)
    
    def generate_report(self, hours_back: int = 24) -> str:
        """Генерирует полный отчет диагностики"""
        
        print(f"🔍 Загрузка ошибок за последние {hours_back} часов...")
        loaded_count = self.load_errors(hours_back)
        
        if loaded_count == 0:
            return "📭 Ошибки не найдены или файл логов пуст"
        
        print(f"✅ Загружено {loaded_count} записей об ошибках")
        
        report = []
        report.append("=" * 80)
        report.append("🚨 ДИАГНОСТИКА ОШИБОК ИЗВЛЕЧЕНИЯ ДАННЫХ")
        report.append("=" * 80)
        report.append(f"📊 Период анализа: последние {hours_back} часов")
        report.append(f"📋 Всего ошибок: {len(self.errors)}")
        report.append("")
        
        # Анализ ошибок извлечения данных
        extraction_analysis = self.analyze_data_extraction_errors()
        if extraction_analysis['total'] > 0:
            report.append("🔴 ОШИБКИ ИЗВЛЕЧЕНИЯ ДАННЫХ ИЗ ИСТОЧНИКОВ")
            report.append("-" * 60)
            report.append(f"Всего ошибок извлечения: {extraction_analysis['total']}")
            report.append("")
            
            # Топ типов ошибок
            report.append("📈 ТОП ТИПЫ ОШИБОК:")
            for error_type, count in list(extraction_analysis['by_type'].items())[:10]:
                report.append(f"  • {error_type}: {count} раз")
            report.append("")
            
            # Топ проблемных источников
            report.append("🌐 ТОП ПРОБЛЕМНЫЕ ИСТОЧНИКИ:")
            for source, count in list(extraction_analysis['by_source'].items())[:10]:
                source_short = source[:50] + '...' if len(source) > 50 else source
                report.append(f"  • {source_short}: {count} ошибок")
            report.append("")
        
        # Поиск мертвых источников
        dead_sources = self.find_dead_sources()
        if dead_sources:
            report.append("💀 МЕРТВЫЕ ИСТОЧНИКИ (≥3 ошибки):")
            report.append("-" * 60)
            for source_info in dead_sources[:5]:
                report.append(f"🔥 {source_info['source']}")
                report.append(f"   Ошибок: {source_info['error_count']}")
                report.append(f"   Типы: {', '.join(source_info['error_types'].keys())}")
                report.append(f"   Последняя: {source_info['latest_error']}")
                report.append(f"   Сообщение: {source_info['latest_message']}")
                report.append("")
        
        # Анализ ошибок пайплайна
        pipeline_analysis = self.analyze_pipeline_errors()
        if pipeline_analysis['total'] > 0:
            report.append("⚙️ ОШИБКИ ПАЙПЛАЙНА ОБРАБОТКИ")
            report.append("-" * 60)
            report.append(f"Всего ошибок пайплайна: {pipeline_analysis['total']}")
            report.append("")
            
            for error_type, count in pipeline_analysis['by_type'].items():
                report.append(f"  • {error_type}: {count} раз")
            report.append("")
        
        # Последние критические ошибки
        if extraction_analysis['recent']:
            report.append("🔥 ПОСЛЕДНИЕ КРИТИЧЕСКИЕ ОШИБКИ:")
            report.append("-" * 60)
            for i, error in enumerate(extraction_analysis['recent'][:5], 1):
                timestamp = error.get('timestamp', 'unknown')[:19]
                error_type = error.get('error_type', 'unknown')
                message = error.get('message', '')[:80] + '...' if len(error.get('message', '')) > 80 else error.get('message', '')
                source = error.get('source_id') or error.get('url') or 'unknown'
                
                report.append(f"{i}. {timestamp} | {error_type}")
                report.append(f"   Источник: {source[:60]}...")
                report.append(f"   Сообщение: {message}")
                report.append("")
        
        # Рекомендации
        report.append("💡 РЕКОМЕНДАЦИИ:")
        report.append("-" * 60)
        if dead_sources:
            report.append("1. Проверить доступность мертвых источников")
            report.append("2. Обновить URL источников или исключить неработающие")
        
        if extraction_analysis['total'] > 10:
            report.append("3. Увеличить таймауты для медленных источников")
            report.append("4. Добавить retry механизмы для временных сбоев")
        
        if pipeline_analysis['total'] > 5:
            report.append("5. Проверить конфигурацию пайплайна обработки")
            report.append("6. Увеличить ресурсы для обработки медиа")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    """Основная функция"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Диагностика ошибок извлечения данных")
    parser.add_argument("--hours", type=int, default=24, help="Анализ за последние N часов (по умолчанию: 24)")
    parser.add_argument("--log-file", type=str, help="Путь к файлу errors.jsonl")
    parser.add_argument("--dead-sources", action="store_true", help="Показать только мертвые источники")
    parser.add_argument("--min-errors", type=int, default=3, help="Минимум ошибок для 'мертвого' источника")
    
    args = parser.parse_args()
    
    diagnostics = ErrorDiagnostics(args.log_file)
    
    if args.dead_sources:
        # Показать только мертвые источники
        print(f"🔍 Поиск мертвых источников (≥{args.min_errors} ошибки)...")
        diagnostics.load_errors(args.hours)
        dead_sources = diagnostics.find_dead_sources(args.min_errors)
        
        if not dead_sources:
            print("✅ Мертвые источники не найдены!")
            return
        
        print("\n💀 МЕРТВЫЕ ИСТОЧНИКИ:")
        print("=" * 80)
        for i, source_info in enumerate(dead_sources, 1):
            print(f"{i}. {source_info['source']}")
            print(f"   🔥 Ошибок: {source_info['error_count']}")
            print(f"   📊 Типы: {', '.join(source_info['error_types'].keys())}")
            print(f"   ⏰ Последняя: {source_info['latest_error']}")
            print(f"   💬 Сообщение: {source_info['latest_message']}")
            print()
    else:
        # Полный отчет
        report = diagnostics.generate_report(args.hours)
        print(report)


if __name__ == "__main__":
    main()
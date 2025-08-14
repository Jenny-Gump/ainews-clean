#!/usr/bin/env python3
"""
Supabase Adapter for Monitoring System
Обеспечивает работу мониторинга с Supabase
"""
import os
import json
import asyncio
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
import sys
from dotenv import load_dotenv

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app_logging import get_logger
from core.db_config import DatabaseConfig

logger = get_logger(__name__)

class SupabaseMonitoringAdapter:
    """Адаптер для работы мониторинга с Supabase"""
    
    def __init__(self, monitoring_db=None):
        """
        Инициализация адаптера
        Args:
            monitoring_db: Экземпляр MonitoringDatabase для fallback
        """
        self.monitoring_db = monitoring_db
        self.use_supabase = DatabaseConfig.use_supabase()
        self.supabase_client = None
        self.realtime_client = None
        self.subscriptions = {}
        self.callbacks = {}
        
        if self.use_supabase:
            self._init_supabase()
    
    def _init_supabase(self):
        """Инициализация Supabase клиента через MCP"""
        try:
            config = DatabaseConfig.get_supabase_config()
            if not config:
                logger.warning("Supabase config not available, using SQLite")
                self.use_supabase = False
                return
            
            # Store config for MCP operations
            self.project_ref = config['project_ref']
            self.access_token = config['access_token']
            
            logger.info(f"Supabase monitoring adapter initialized for project {self.project_ref}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            self.use_supabase = False
    
    async def subscribe_to_table(self, table: str, callback: Callable, event_types: List[str] = None):
        """
        Подписка на изменения в таблице Supabase
        Args:
            table: Имя таблицы
            callback: Функция обратного вызова
            event_types: Типы событий (INSERT, UPDATE, DELETE)
        """
        if not self.use_supabase:
            return
        
        try:
            if event_types is None:
                event_types = ['INSERT', 'UPDATE', 'DELETE']
            
            # Store callback for this table
            if table not in self.callbacks:
                self.callbacks[table] = []
            self.callbacks[table].append({
                'callback': callback,
                'events': event_types
            })
            
            logger.info(f"Subscribed to {table} for events: {event_types}")
            
        except Exception as e:
            logger.error(f"Failed to subscribe to {table}: {e}")
    
    async def insert_metrics(self, table: str, data: Dict[str, Any]) -> bool:
        """
        Вставка метрик в Supabase или SQLite
        """
        try:
            if self.use_supabase:
                # Use MCP to insert data
                # For now, we'll prepare the data structure
                # Real implementation would use mcp__supabase__execute_sql
                
                # Ensure timestamp is ISO format
                if 'timestamp' in data and not isinstance(data['timestamp'], str):
                    data['timestamp'] = datetime.utcnow().isoformat()
                
                logger.debug(f"Would insert to Supabase {table}: {data}")
                return True
            else:
                # Fallback to SQLite
                if self.monitoring_db:
                    return self._insert_to_sqlite(table, data)
            
        except Exception as e:
            logger.error(f"Failed to insert metrics to {table}: {e}")
            return False
    
    def _insert_to_sqlite(self, table: str, data: Dict[str, Any]) -> bool:
        """Вставка в SQLite для совместимости"""
        try:
            if not self.monitoring_db:
                return False
            
            # Map table names to monitoring_db methods
            if table == 'performance_metrics':
                self.monitoring_db.record_performance_metric(
                    operation=data.get('operation', 'unknown'),
                    duration_ms=data.get('duration_ms', 0),
                    success=data.get('success', True),
                    error_message=data.get('error_message'),
                    metadata=data.get('metadata', {})
                )
            elif table == 'system_metrics':
                # System metrics - just log for now (Supabase mode)
                self.logger.debug(f"System metrics insert (Supabase mode): {data}")
            
            return True
            
        except Exception as e:
            logger.error(f"SQLite insert failed: {e}")
            return False
    
    async def batch_insert_metrics(self, table: str, data_list: List[Dict[str, Any]]) -> bool:
        """
        Пакетная вставка метрик для оптимизации
        """
        if not data_list:
            return True
        
        try:
            if self.use_supabase:
                # Prepare batch for Supabase
                for data in data_list:
                    if 'timestamp' in data and not isinstance(data['timestamp'], str):
                        data['timestamp'] = datetime.utcnow().isoformat()
                
                logger.debug(f"Would batch insert {len(data_list)} records to Supabase {table}")
                return True
            else:
                # SQLite batch insert
                success = True
                for data in data_list:
                    if not await self.insert_metrics(table, data):
                        success = False
                return success
                
        except Exception as e:
            logger.error(f"Batch insert failed: {e}")
            return False
    
    async def get_recent_metrics(self, table: str, minutes: int = 60, limit: int = 100) -> List[Dict]:
        """
        Получение последних метрик
        """
        try:
            if self.use_supabase:
                # Would use MCP to query Supabase
                since = (datetime.utcnow() - timedelta(minutes=minutes)).isoformat()
                logger.debug(f"Would query Supabase {table} since {since}")
                return []
            else:
                # SQLite disabled - return empty results
                logger.debug(f"SQLite disabled - returning empty metrics for {table}")
                return []
                    
        except Exception as e:
            logger.error(f"Failed to get recent metrics: {e}")
            return []
    
    async def get_aggregated_metrics(self, table: str, field: str, 
                                    aggregation: str = 'avg', 
                                    group_by: str = None,
                                    minutes: int = 60) -> Dict:
        """
        Получение агрегированных метрик
        """
        try:
            if self.use_supabase:
                # Would use MCP with SQL aggregation
                logger.debug(f"Would aggregate {aggregation}({field}) from Supabase {table}")
                return {}
            else:
                # SQLite disabled - return empty aggregation
                logger.debug(f"SQLite disabled - returning empty aggregation for {table}")
                return {}
                    
        except Exception as e:
            logger.error(f"Failed to get aggregated metrics: {e}")
            return {}
    
    async def cleanup_old_metrics(self, table: str, days: int = 7) -> int:
        """
        Очистка старых метрик
        """
        try:
            cutoff = datetime.utcnow() - timedelta(days=days)
            
            if self.use_supabase:
                # Would use MCP to delete old records
                logger.info(f"Would cleanup {table} older than {cutoff.isoformat()}")
                return 0
            else:
                # SQLite disabled - no cleanup
                logger.debug(f"SQLite disabled - no cleanup for {table}")
                return 0
                    
        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}")
            return 0
    
    def get_database_type(self) -> str:
        """Возвращает тип используемой базы данных"""
        return 'supabase' if self.use_supabase else 'sqlite'
    
    def is_supabase_active(self) -> bool:
        """Проверяет, активно ли подключение к Supabase"""
        return self.use_supabase
    
    async def test_connection(self) -> bool:
        """Тестирует подключение к базе данных"""
        try:
            if self.use_supabase:
                # Would test Supabase connection via MCP
                return DatabaseConfig.test_supabase_connection()
            else:
                # SQLite disabled
                logger.debug("SQLite disabled - connection test skipped")
                return False
            return False
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False


class SupabaseRealtimeMonitor:
    """
    Real-time монитор для Supabase subscriptions
    """
    
    def __init__(self, adapter: SupabaseMonitoringAdapter):
        self.adapter = adapter
        self.channels = {}
        self.running = False
        self._monitor_task = None
    
    async def start(self):
        """Запуск real-time мониторинга"""
        if not self.adapter.use_supabase:
            logger.info("Real-time monitoring not available without Supabase")
            return
        
        self.running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info("Supabase real-time monitor started")
    
    async def stop(self):
        """Остановка real-time мониторинга"""
        self.running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Supabase real-time monitor stopped")
    
    async def _monitor_loop(self):
        """Основной цикл мониторинга"""
        while self.running:
            try:
                # This would be replaced with actual Supabase real-time monitoring
                # For now, we'll simulate with periodic checks
                await asyncio.sleep(5)
                
                # Check for updates in critical tables
                for table in ['articles', 'performance_metrics', 'system_metrics']:
                    if table in self.adapter.callbacks:
                        # Simulate an update event
                        await self._process_event(table, 'UPDATE', {})
                
            except Exception as e:
                logger.error(f"Real-time monitor error: {e}")
                await asyncio.sleep(10)
    
    async def _process_event(self, table: str, event_type: str, data: Dict):
        """Обработка события от Supabase"""
        if table in self.adapter.callbacks:
            for cb_info in self.adapter.callbacks[table]:
                if event_type in cb_info['events']:
                    try:
                        callback = cb_info['callback']
                        if asyncio.iscoroutinefunction(callback):
                            await callback(event_type, data)
                        else:
                            callback(event_type, data)
                    except Exception as e:
                        logger.error(f"Callback error for {table}.{event_type}: {e}")
    
    async def subscribe_to_articles(self, callback: Callable):
        """Подписка на изменения статей"""
        await self.adapter.subscribe_to_table('articles', callback, ['INSERT', 'UPDATE'])
    
    async def subscribe_to_performance(self, callback: Callable):
        """Подписка на метрики производительности"""
        await self.adapter.subscribe_to_table('performance_metrics', callback, ['INSERT'])
    
    async def subscribe_to_system_metrics(self, callback: Callable):
        """Подписка на системные метрики"""
        await self.adapter.subscribe_to_table('system_metrics', callback, ['INSERT'])
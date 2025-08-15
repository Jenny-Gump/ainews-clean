#!/usr/bin/env python3
"""
Real-time Monitoring with Supabase
Использует Supabase real-time subscriptions для мониторинга
"""
import asyncio
import json
from typing import Dict, List, Any, Callable, Optional
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from app_logging import get_logger
from core.db_config import DatabaseConfig
from monitoring.supabase_client import get_supabase_client
SupabaseMonitoringAdapter = get_supabase_client  # Compatibility alias

logger = get_logger(__name__)

class RealtimeMonitor:
    """
    Real-time монитор с поддержкой Supabase и WebSocket broadcast
    """
    
    def __init__(self, monitoring_db=None, websocket_manager=None):
        """
        Инициализация real-time монитора
        Args:
            monitoring_db: Экземпляр MonitoringDatabase
            websocket_manager: Менеджер WebSocket соединений
        """
        self.monitoring_db = monitoring_db
        self.websocket_manager = websocket_manager
        self.adapter = SupabaseMonitoringAdapter(monitoring_db)
        self.running = False
        self._tasks = []
        
        # Счетчики и метрики
        self.metrics_buffer = []
        self.buffer_size = 100
        self.flush_interval = 10  # seconds
        
        # Callbacks для различных событий
        self.event_callbacks = {
            'article_created': [],
            'article_updated': [],
            'performance_metric': [],
            'system_metric': [],
            'error_logged': [],
            'source_health_changed': []
        }
    
    async def start(self):
        """Запуск real-time мониторинга"""
        if self.running:
            logger.warning("Realtime monitor already running")
            return
        
        self.running = True
        
        # Запуск задач мониторинга
        if self.adapter.use_supabase:
            # Подписка на Supabase real-time события
            await self._setup_supabase_subscriptions()
        else:
            # Fallback на polling для SQLite
            self._tasks.append(asyncio.create_task(self._sqlite_polling_loop()))
        
        # Запуск flush буфера метрик
        self._tasks.append(asyncio.create_task(self._metrics_flush_loop()))
        
        logger.info(f"Realtime monitor started using {self.adapter.get_database_type()}")
    
    async def stop(self):
        """Остановка real-time мониторинга"""
        self.running = False
        
        # Flush оставшиеся метрики
        await self._flush_metrics()
        
        # Отмена всех задач
        for task in self._tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._tasks.clear()
        logger.info("Realtime monitor stopped")
    
    async def _setup_supabase_subscriptions(self):
        """Настройка подписок на Supabase таблицы"""
        
        # Подписка на таблицу articles
        await self.adapter.subscribe_to_table(
            'articles',
            self._handle_article_event,
            ['INSERT', 'UPDATE']
        )
        
        # Подписка на performance_metrics
        await self.adapter.subscribe_to_table(
            'performance_metrics',
            self._handle_performance_event,
            ['INSERT']
        )
        
        # Подписка на system_metrics
        await self.adapter.subscribe_to_table(
            'system_metrics',
            self._handle_system_event,
            ['INSERT']
        )
        
        # Подписка на error_logs
        await self.adapter.subscribe_to_table(
            'error_logs',
            self._handle_error_event,
            ['INSERT']
        )
        
        logger.info("Supabase real-time subscriptions configured")
    
    async def _sqlite_polling_loop(self):
        """Polling loop для SQLite (fallback)"""
        last_check = datetime.utcnow()
        
        while self.running:
            try:
                current_time = datetime.utcnow()
                
                # Проверка новых записей каждые 5 секунд
                await asyncio.sleep(5)
                
                # Получение новых метрик с последней проверки
                new_metrics = await self._poll_sqlite_updates(last_check)
                
                # Обработка новых метрик
                for metric_type, metrics in new_metrics.items():
                    for metric in metrics:
                        await self._process_metric(metric_type, metric)
                
                last_check = current_time
                
            except Exception as e:
                logger.error(f"SQLite polling error: {e}")
                await asyncio.sleep(10)
    
    async def _poll_sqlite_updates(self, since: datetime) -> Dict[str, List]:
        """Получение обновлений из SQLite с последней проверки"""
        updates = {
            'performance': [],
            'system': [],
            'errors': []
        }
        
        if not self.monitoring_db:
            return updates
        
        try:
            # Получение новых performance_metrics
            perf_metrics = await self.adapter.get_recent_metrics(
                'performance_metrics', 
                minutes=1
            )
            updates['performance'] = [m for m in perf_metrics 
                                     if m.get('timestamp', '') > since.isoformat()]
            
            # Получение новых system_metrics
            sys_metrics = await self.adapter.get_recent_metrics(
                'system_metrics',
                minutes=1
            )
            updates['system'] = [m for m in sys_metrics
                               if m.get('timestamp', '') > since.isoformat()]
            
            # Получение новых ошибок
            error_logs = await self.adapter.get_recent_metrics(
                'error_logs',
                minutes=1
            )
            updates['errors'] = [e for e in error_logs
                               if e.get('timestamp', '') > since.isoformat()]
            
        except Exception as e:
            logger.error(f"Failed to poll SQLite updates: {e}")
        
        return updates
    
    async def _handle_article_event(self, event_type: str, data: Dict):
        """Обработка событий статей"""
        try:
            if event_type == 'INSERT':
                await self._trigger_callbacks('article_created', data)
            elif event_type == 'UPDATE':
                await self._trigger_callbacks('article_updated', data)
            
            # Broadcast через WebSocket
            if self.websocket_manager:
                await self.websocket_manager.broadcast({
                    'type': 'article_event',
                    'event': event_type.lower(),
                    'data': data,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error handling article event: {e}")
    
    async def _handle_performance_event(self, event_type: str, data: Dict):
        """Обработка событий производительности"""
        try:
            await self._trigger_callbacks('performance_metric', data)
            
            # Добавление в буфер для агрегации
            self.metrics_buffer.append({
                'type': 'performance',
                'data': data,
                'timestamp': datetime.utcnow()
            })
            
            # Broadcast критических метрик
            if data.get('duration_ms', 0) > 5000:  # Slow operations
                if self.websocket_manager:
                    await self.websocket_manager.broadcast({
                        'type': 'slow_operation',
                        'operation': data.get('operation'),
                        'duration_ms': data.get('duration_ms'),
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
        except Exception as e:
            logger.error(f"Error handling performance event: {e}")
    
    async def _handle_system_event(self, event_type: str, data: Dict):
        """Обработка системных событий"""
        try:
            await self._trigger_callbacks('system_metric', data)
            
            # Проверка критических значений
            cpu_percent = data.get('cpu_percent', 0)
            memory_percent = data.get('memory_percent', 0)
            
            if cpu_percent > 90 or memory_percent > 90:
                # Критическое использование ресурсов
                if self.websocket_manager:
                    await self.websocket_manager.broadcast({
                        'type': 'resource_alert',
                        'cpu_percent': cpu_percent,
                        'memory_percent': memory_percent,
                        'alert_level': 'critical',
                        'timestamp': datetime.utcnow().isoformat()
                    })
                    
        except Exception as e:
            logger.error(f"Error handling system event: {e}")
    
    async def _handle_error_event(self, event_type: str, data: Dict):
        """Обработка событий ошибок"""
        try:
            await self._trigger_callbacks('error_logged', data)
            
            # Broadcast ошибки
            if self.websocket_manager:
                await self.websocket_manager.broadcast({
                    'type': 'error_event',
                    'error_type': data.get('error_type'),
                    'message': data.get('error_message'),
                    'source': data.get('source_id'),
                    'timestamp': datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Error handling error event: {e}")
    
    async def _process_metric(self, metric_type: str, metric: Dict):
        """Обработка метрики"""
        if metric_type == 'performance':
            await self._handle_performance_event('INSERT', metric)
        elif metric_type == 'system':
            await self._handle_system_event('INSERT', metric)
        elif metric_type == 'errors':
            await self._handle_error_event('INSERT', metric)
    
    async def _metrics_flush_loop(self):
        """Периодический flush буфера метрик"""
        while self.running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_metrics()
                
            except Exception as e:
                logger.error(f"Metrics flush error: {e}")
    
    async def _flush_metrics(self):
        """Flush буфера метрик в базу данных"""
        if not self.metrics_buffer:
            return
        
        try:
            # Группировка метрик по типу
            grouped = {}
            for item in self.metrics_buffer:
                metric_type = item['type']
                if metric_type not in grouped:
                    grouped[metric_type] = []
                grouped[metric_type].append(item['data'])
            
            # Batch insert для каждого типа
            for metric_type, metrics in grouped.items():
                if metric_type == 'performance':
                    await self.adapter.batch_insert_metrics('performance_metrics', metrics)
                elif metric_type == 'system':
                    await self.adapter.batch_insert_metrics('system_metrics', metrics)
            
            logger.debug(f"Flushed {len(self.metrics_buffer)} metrics")
            self.metrics_buffer.clear()
            
        except Exception as e:
            logger.error(f"Failed to flush metrics: {e}")
    
    def register_callback(self, event_type: str, callback: Callable):
        """
        Регистрация callback для события
        Args:
            event_type: Тип события
            callback: Функция обратного вызова
        """
        if event_type in self.event_callbacks:
            self.event_callbacks[event_type].append(callback)
            logger.debug(f"Registered callback for {event_type}")
        else:
            logger.warning(f"Unknown event type: {event_type}")
    
    async def _trigger_callbacks(self, event_type: str, data: Dict):
        """Вызов зарегистрированных callbacks"""
        if event_type not in self.event_callbacks:
            return
        
        for callback in self.event_callbacks[event_type]:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(data)
                else:
                    callback(data)
            except Exception as e:
                logger.error(f"Callback error for {event_type}: {e}")
    
    async def record_metric(self, metric_type: str, data: Dict):
        """
        Запись метрики
        Args:
            metric_type: Тип метрики (performance, system, error)
            data: Данные метрики
        """
        try:
            # Добавление timestamp если отсутствует
            if 'timestamp' not in data:
                data['timestamp'] = datetime.utcnow().isoformat()
            
            # Добавление в буфер
            self.metrics_buffer.append({
                'type': metric_type,
                'data': data,
                'timestamp': datetime.utcnow()
            })
            
            # Flush если буфер переполнен
            if len(self.metrics_buffer) >= self.buffer_size:
                await self._flush_metrics()
                
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
    
    async def get_metrics_summary(self) -> Dict:
        """Получение сводки метрик"""
        try:
            summary = {
                'database_type': self.adapter.get_database_type(),
                'buffer_size': len(self.metrics_buffer),
                'is_running': self.running,
                'active_tasks': len(self._tasks)
            }
            
            # Получение агрегированных метрик за последний час
            if self.adapter.is_supabase_active():
                summary['performance_avg'] = await self.adapter.get_aggregated_metrics(
                    'performance_metrics', 'duration_ms', 'avg', minutes=60
                )
                summary['error_count'] = await self.adapter.get_aggregated_metrics(
                    'error_logs', 'id', 'count', minutes=60
                )
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
            return {}


# Singleton instance
_realtime_monitor: Optional[RealtimeMonitor] = None

def get_realtime_monitor(monitoring_db=None, websocket_manager=None) -> RealtimeMonitor:
    """Получение singleton экземпляра RealtimeMonitor"""
    global _realtime_monitor
    
    if _realtime_monitor is None:
        _realtime_monitor = RealtimeMonitor(monitoring_db, websocket_manager)
    
    return _realtime_monitor

async def init_realtime_monitor(monitoring_db=None, websocket_manager=None):
    """Инициализация и запуск real-time монитора"""
    monitor = get_realtime_monitor(monitoring_db, websocket_manager)
    await monitor.start()
    return monitor
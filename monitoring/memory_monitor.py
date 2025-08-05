"""
Системный мониторинг памяти с аварийной остановкой при превышении 10GB
Отслеживает все процессы в реальном времени и интегрируется в систему мониторинга
"""
import psutil
import os
import signal
import threading
import time
import gc
import weakref
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass
from enum import Enum


class MemoryAlertLevel(Enum):
    """Уровни тревоги по памяти"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class ProcessMemoryInfo:
    """Информация об использовании памяти процессом"""
    pid: int
    name: str
    memory_mb: float
    cpu_percent: float
    create_time: datetime
    parent_pid: Optional[int] = None
    cmdline: List[str] = None


@dataclass
class MemorySnapshot:
    """Снимок состояния памяти системы"""
    timestamp: datetime
    total_memory_mb: float
    available_memory_mb: float
    used_memory_mb: float
    processes: List[ProcessMemoryInfo]
    top_memory_consumers: List[ProcessMemoryInfo]
    ainews_processes: List[ProcessMemoryInfo]


class SystemMemoryMonitor:
    """
    Системный мониторинг памяти с аварийной остановкой
    
    Функции:
    1. Мониторинг всех процессов в реальном времени
    2. Особое внимание к процессам AI News
    3. Аварийная остановка при превышении 10GB
    4. Интеграция с системой мониторинга
    5. Алерты и уведомления
    """
    
    def __init__(
        self,
        max_memory_gb: float = 10.0,
        warning_threshold_gb: float = 7.0,
        critical_threshold_gb: float = 8.5,
        check_interval_seconds: int = 5,
        monitoring_db=None
    ):
        self.max_memory_gb = max_memory_gb
        self.max_memory_mb = max_memory_gb * 1024
        self.warning_threshold_mb = warning_threshold_gb * 1024
        self.critical_threshold_mb = critical_threshold_gb * 1024
        self.check_interval = check_interval_seconds
        self.monitoring_db = monitoring_db
        
        # Состояние мониторинга
        self._running = False
        self._thread = None
        self._last_check_time = None
        self._memory_history = []
        self._max_history_entries = 360  # 30 минут при проверке каждые 5 секунд - reduced from 1440
        
        # Callback'и для очистки памяти
        self._cleanup_callbacks = []
        self._emergency_callbacks = []
        
        # AI News процессы для особого мониторинга
        self._ainews_process_names = [
            'python', 'python3', 'uvicorn', 'gunicorn',
            'main.py', 'app.py', 'unified_crawl_parser.py'
        ]
        
        # Логирование
        self.logger = logging.getLogger(__name__)
        
        # Статистика
        self._alerts_sent = 0
        self._cleanups_performed = 0
        self._emergency_shutdowns = 0
        
        self.logger.info(f"SystemMemoryMonitor initialized: max={max_memory_gb}GB, "
                        f"warning={warning_threshold_gb}GB, critical={critical_threshold_gb}GB")
    
    def register_cleanup_callback(self, callback: Callable[[], None], name: str = "Unknown"):
        """Регистрация callback'а для очистки памяти"""
        self._cleanup_callbacks.append({
            'callback': weakref.ref(callback),
            'name': name,
            'calls': 0,
            'last_called': None
        })
        self.logger.debug(f"Registered cleanup callback: {name}")
    
    def register_emergency_callback(self, callback: Callable[[], None], name: str = "Unknown"):
        """Регистрация callback'а для экстренных ситуаций"""
        self._emergency_callbacks.append({
            'callback': weakref.ref(callback),
            'name': name,
            'calls': 0,
            'last_called': None
        })
        self.logger.debug(f"Registered emergency callback: {name}")
    
    def start(self):
        """Запуск мониторинга памяти"""
        if self._running:
            self.logger.warning("Memory monitor already running")
            return
        
        self._running = True
        self._thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._thread.start()
        self.logger.info("SystemMemoryMonitor started")
    
    def stop(self):
        """Остановка мониторинга памяти"""
        if not self._running:
            return
        
        self._running = False
        if self._thread:
            self._thread.join(timeout=10)
        self.logger.info("SystemMemoryMonitor stopped")
    
    def get_memory_snapshot(self) -> MemorySnapshot:
        """Получить текущий снимок памяти системы"""
        try:
            # Системная память
            memory_info = psutil.virtual_memory()
            total_memory_mb = memory_info.total / 1024 / 1024
            available_memory_mb = memory_info.available / 1024 / 1024
            used_memory_mb = memory_info.used / 1024 / 1024
            
            # Процессы
            processes = []
            ainews_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cpu_percent', 'create_time', 'ppid', 'cmdline']):
                try:
                    proc_info = proc.info
                    # FIXED: Проверяем что memory_info не None
                    if not proc_info['memory_info']:
                        continue
                    memory_mb = proc_info['memory_info'].rss / 1024 / 1024
                    
                    # Создаем ProcessMemoryInfo
                    process_memory = ProcessMemoryInfo(
                        pid=proc_info['pid'],
                        name=proc_info['name'],
                        memory_mb=memory_mb,
                        cpu_percent=proc_info['cpu_percent'] or 0.0,
                        create_time=datetime.fromtimestamp(proc_info['create_time']),
                        parent_pid=proc_info.get('ppid'),
                        cmdline=proc_info.get('cmdline', [])
                    )
                    
                    processes.append(process_memory)
                    
                    # Проверяем, относится ли к AI News
                    if self._is_ainews_process(process_memory):
                        ainews_processes.append(process_memory)
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Сортируем по использованию памяти
            processes.sort(key=lambda p: p.memory_mb, reverse=True)
            top_consumers = processes[:10]  # Топ-10 потребителей памяти
            
            # Считаем память AI News проекта
            ainews_memory_mb = sum(p.memory_mb for p in ainews_processes)
            
            return MemorySnapshot(
                timestamp=datetime.now(),
                total_memory_mb=total_memory_mb,
                available_memory_mb=available_memory_mb,
                used_memory_mb=ainews_memory_mb,  # Используем память AI News вместо системной
                processes=processes,
                top_memory_consumers=top_consumers,
                ainews_processes=ainews_processes
            )
            
        except Exception as e:
            self.logger.error(f"Error getting memory snapshot: {e}")
            raise
    
    def _is_ainews_process(self, process: ProcessMemoryInfo) -> bool:
        """Проверить, относится ли процесс к AI News"""
        # Проверяем имя процесса
        if any(name in process.name.lower() for name in ['python', 'uvicorn', 'gunicorn']):
            # Проверяем командную строку
            if process.cmdline:
                cmdline_str = ' '.join(process.cmdline).lower()
                ai_news_keywords = [
                    'ainews', 'ai-news', 'main.py', 'app.py', 
                    'unified_crawl_parser', 'monitoring'
                ]
                if any(keyword in cmdline_str for keyword in ai_news_keywords):
                    return True
        
        return False
    
    def _monitor_loop(self):
        """Основной цикл мониторинга"""
        while self._running:
            try:
                self._last_check_time = datetime.now()
                snapshot = self.get_memory_snapshot()
                
                # Добавляем в историю
                self._memory_history.append(snapshot)
                if len(self._memory_history) > self._max_history_entries:
                    self._memory_history.pop(0)
                
                # Анализируем использование памяти
                self._analyze_memory_usage(snapshot)
                
                # Сохраняем метрики в БД если доступно
                if self.monitoring_db:
                    self._save_memory_metrics(snapshot)
                
                time.sleep(self.check_interval)
                
            except Exception as e:
                self.logger.error(f"Error in memory monitoring loop: {e}")
                time.sleep(self.check_interval)
    
    def _analyze_memory_usage(self, snapshot: MemorySnapshot):
        """Анализ использования памяти и принятие мер"""
        used_memory_mb = snapshot.used_memory_mb
        ainews_memory_mb = sum(p.memory_mb for p in snapshot.ainews_processes)
        
        # Определяем уровень тревоги
        alert_level = self._get_alert_level(used_memory_mb)
        
        # Логируем текущее состояние
        self.logger.debug(f"Memory usage: {used_memory_mb:.1f}MB total, "
                         f"{ainews_memory_mb:.1f}MB AI News processes, "
                         f"Alert level: {alert_level.value}")
        
        # Принимаем меры в зависимости от уровня
        if alert_level == MemoryAlertLevel.WARNING:
            self._handle_warning(snapshot)
        elif alert_level == MemoryAlertLevel.CRITICAL:
            self._handle_critical(snapshot)
        elif alert_level == MemoryAlertLevel.EMERGENCY:
            self._handle_emergency(snapshot)
    
    def _get_alert_level(self, used_memory_mb: float) -> MemoryAlertLevel:
        """Определить уровень тревоги по использованию памяти"""
        if used_memory_mb >= self.max_memory_mb:
            return MemoryAlertLevel.EMERGENCY
        elif used_memory_mb >= self.critical_threshold_mb:
            return MemoryAlertLevel.CRITICAL
        elif used_memory_mb >= self.warning_threshold_mb:
            return MemoryAlertLevel.WARNING
        else:
            return MemoryAlertLevel.INFO
    
    def _handle_warning(self, snapshot: MemorySnapshot):
        """Обработка предупреждения о высоком использовании памяти"""
        self.logger.warning(f"High memory usage detected: {snapshot.used_memory_mb:.1f}MB "
                           f"(threshold: {self.warning_threshold_mb:.1f}MB)")
        
        # Отправляем алерт
        self._send_alert(MemoryAlertLevel.WARNING, snapshot)
        
        # Запускаем мягкую очистку
        self._trigger_soft_cleanup()
    
    def _handle_critical(self, snapshot: MemorySnapshot):
        """Обработка критического использования памяти"""
        self.logger.error(f"Critical memory usage detected: {snapshot.used_memory_mb:.1f}MB "
                         f"(threshold: {self.critical_threshold_mb:.1f}MB)")
        
        # Отправляем критический алерт
        self._send_alert(MemoryAlertLevel.CRITICAL, snapshot)
        
        # Запускаем агрессивную очистку
        self._trigger_aggressive_cleanup()
    
    def _handle_emergency(self, snapshot: MemorySnapshot):
        """Обработка экстренной ситуации - превышен лимит 10GB"""
        self.logger.critical(f"EMERGENCY: Memory usage exceeds maximum limit! "
                           f"Used: {snapshot.used_memory_mb:.1f}MB "
                           f"(limit: {self.max_memory_mb:.1f}MB)")
        
        # Отправляем экстренный алерт
        self._send_alert(MemoryAlertLevel.EMERGENCY, snapshot)
        
        # Запускаем экстренные callback'и
        self._trigger_emergency_callbacks()
        
        # Принудительная сборка мусора
        gc.collect()
        
        # Ждем немного и проверяем еще раз
        time.sleep(2)
        new_snapshot = self.get_memory_snapshot()
        
        if new_snapshot.used_memory_mb >= self.max_memory_mb:
            # Все еще превышен лимит - аварийная остановка
            self._emergency_shutdown(new_snapshot)
    
    def _trigger_soft_cleanup(self):
        """Мягкая очистка памяти"""
        self.logger.info("Triggering soft memory cleanup")
        
        # Сборка мусора
        collected = gc.collect()
        self.logger.debug(f"Garbage collection freed {collected} objects")
        
        # Вызываем cleanup callback'и
        for callback_info in self._cleanup_callbacks:
            try:
                callback = callback_info['callback']()
                if callback:
                    callback()
                    callback_info['calls'] += 1
                    callback_info['last_called'] = datetime.now()
                    self.logger.debug(f"Called cleanup callback: {callback_info['name']}")
            except Exception as e:
                self.logger.error(f"Error in cleanup callback {callback_info['name']}: {e}")
        
        self._cleanups_performed += 1
    
    def _trigger_aggressive_cleanup(self):
        """Агрессивная очистка памяти"""
        self.logger.warning("Triggering aggressive memory cleanup")
        
        # Сначала мягкая очистка
        self._trigger_soft_cleanup()
        
        # Дополнительные меры
        # Принудительная сборка мусора несколько раз
        for _ in range(3):
            gc.collect()
            time.sleep(0.1)
    
    def _trigger_emergency_callbacks(self):
        """Запуск экстренных callback'ов"""
        self.logger.critical("Triggering emergency callbacks")
        
        for callback_info in self._emergency_callbacks:
            try:
                callback = callback_info['callback']()
                if callback:
                    callback()
                    callback_info['calls'] += 1
                    callback_info['last_called'] = datetime.now()
                    self.logger.critical(f"Called emergency callback: {callback_info['name']}")
            except Exception as e:
                self.logger.error(f"Error in emergency callback {callback_info['name']}: {e}")
    
    def _emergency_shutdown(self, snapshot: MemorySnapshot):
        """Аварийная остановка системы"""
        self._emergency_shutdowns += 1
        
        self.logger.critical("INITIATING EMERGENCY SHUTDOWN - MEMORY LIMIT EXCEEDED!")
        self.logger.critical(f"Final memory usage: {snapshot.used_memory_mb:.1f}MB")
        
        # Логируем топ процессы
        self.logger.critical("Top memory consumers:")
        for i, proc in enumerate(snapshot.top_memory_consumers[:5], 1):
            self.logger.critical(f"  {i}. {proc.name} (PID {proc.pid}): {proc.memory_mb:.1f}MB")
        
        # Сохраняем финальный снимок
        if self.monitoring_db:
            try:
                self._save_emergency_snapshot(snapshot)
            except Exception as e:
                self.logger.error(f"Failed to save emergency snapshot: {e}")
        
        # Отправляем финальный алерт
        self._send_alert(MemoryAlertLevel.EMERGENCY, snapshot, is_shutdown=True)
        
        # Останавливаем текущий процесс
        self.logger.critical("Terminating current process to prevent system instability")
        os.kill(os.getpid(), signal.SIGTERM)
    
    def _send_alert(self, level: MemoryAlertLevel, snapshot: MemorySnapshot, is_shutdown: bool = False):
        """Отправка алерта"""
        try:
            alert_data = {
                'timestamp': snapshot.timestamp.isoformat(),
                'level': level.value,
                'memory_usage_mb': snapshot.used_memory_mb,
                'memory_limit_mb': self.max_memory_mb,
                'threshold_exceeded': snapshot.used_memory_mb / self.max_memory_mb * 100,
                'ainews_processes_count': len(snapshot.ainews_processes),
                'ainews_memory_mb': sum(p.memory_mb for p in snapshot.ainews_processes),
                'top_consumers': [
                    {'name': p.name, 'pid': p.pid, 'memory_mb': p.memory_mb}
                    for p in snapshot.top_memory_consumers[:3]
                ],
                'is_emergency_shutdown': is_shutdown
            }
            
            # Логируем алерт
            message = f"Memory Alert [{level.value.upper()}]: {snapshot.used_memory_mb:.1f}MB used"
            if is_shutdown:
                message += " - EMERGENCY SHUTDOWN INITIATED"
            
            if level == MemoryAlertLevel.EMERGENCY:
                self.logger.critical(message)
            elif level == MemoryAlertLevel.CRITICAL:
                self.logger.error(message)
            else:
                self.logger.warning(message)
            
            # Сохраняем в БД если доступно
            if self.monitoring_db:
                self._save_alert_to_db(alert_data)
            
            self._alerts_sent += 1
            
        except Exception as e:
            self.logger.error(f"Error sending memory alert: {e}")
    
    def _save_memory_metrics(self, snapshot: MemorySnapshot):
        """Сохранение метрик памяти в БД"""
        try:
            metrics_data = {
                'timestamp': snapshot.timestamp,
                'total_memory_mb': snapshot.total_memory_mb,
                'used_memory_mb': snapshot.used_memory_mb,
                'available_memory_mb': snapshot.available_memory_mb,
                'processes_count': len(snapshot.processes),
                'ainews_processes_count': len(snapshot.ainews_processes),
                'ainews_memory_mb': sum(p.memory_mb for p in snapshot.ainews_processes),
                'top_consumer_memory_mb': snapshot.top_memory_consumers[0].memory_mb if snapshot.top_memory_consumers else 0
            }
            
            # Сохраняем через API мониторинга
            self.monitoring_db.save_memory_metrics(metrics_data)
            
        except Exception as e:
            self.logger.error(f"Error saving memory metrics: {e}")
    
    def _save_alert_to_db(self, alert_data: Dict[str, Any]):
        """Сохранение алерта в БД"""
        try:
            self.monitoring_db.save_memory_alert(alert_data)
        except Exception as e:
            self.logger.error(f"Error saving memory alert to database: {e}")
    
    def _save_emergency_snapshot(self, snapshot: MemorySnapshot):
        """Сохранение экстренного снимка системы"""
        try:
            emergency_data = {
                'timestamp': snapshot.timestamp,
                'total_memory_mb': snapshot.total_memory_mb,
                'used_memory_mb': snapshot.used_memory_mb,
                'processes': [
                    {
                        'pid': p.pid,
                        'name': p.name,
                        'memory_mb': p.memory_mb,
                        'cpu_percent': p.cpu_percent,
                        'cmdline': ' '.join(p.cmdline) if p.cmdline else ''
                    }
                    for p in snapshot.top_memory_consumers[:20]
                ],
                'ainews_processes': [
                    {
                        'pid': p.pid,
                        'name': p.name,
                        'memory_mb': p.memory_mb,
                        'cpu_percent': p.cpu_percent,
                        'cmdline': ' '.join(p.cmdline) if p.cmdline else ''
                    }
                    for p in snapshot.ainews_processes
                ]
            }
            
            self.monitoring_db.save_emergency_snapshot(emergency_data)
            
        except Exception as e:
            self.logger.error(f"Error saving emergency snapshot: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Получить статистику работы мониторинга"""
        return {
            'running': self._running,
            'last_check_time': self._last_check_time.isoformat() if self._last_check_time else None,
            'memory_history_entries': len(self._memory_history),
            'alerts_sent': self._alerts_sent,
            'cleanups_performed': self._cleanups_performed,
            'emergency_shutdowns': self._emergency_shutdowns,
            'cleanup_callbacks_registered': len(self._cleanup_callbacks),
            'emergency_callbacks_registered': len(self._emergency_callbacks),
            'thresholds': {
                'max_memory_gb': self.max_memory_gb,
                'warning_threshold_gb': self.warning_threshold_mb / 1024,
                'critical_threshold_gb': self.critical_threshold_mb / 1024
            }
        }
    
    def get_current_memory_info(self) -> Dict[str, Any]:
        """Получить текущую информацию о памяти"""
        if not self._memory_history:
            snapshot = self.get_memory_snapshot()
        else:
            snapshot = self._memory_history[-1]
        
        ainews_memory = sum(p.memory_mb for p in snapshot.ainews_processes)
        
        return {
            'timestamp': snapshot.timestamp.isoformat(),
            'system_memory': {
                'total_mb': snapshot.total_memory_mb,
                'used_mb': snapshot.used_memory_mb,
                'available_mb': snapshot.available_memory_mb,
                'usage_percent': (snapshot.used_memory_mb / snapshot.total_memory_mb) * 100
            },
            'ainews_memory': {
                'total_mb': ainews_memory,
                'processes_count': len(snapshot.ainews_processes),
                'percentage_of_system': (ainews_memory / snapshot.used_memory_mb) * 100 if snapshot.used_memory_mb > 0 else 0
            },
            'alert_level': self._get_alert_level(snapshot.used_memory_mb).value,
            'top_consumers': [
                {
                    'name': p.name,
                    'pid': p.pid,
                    'memory_mb': p.memory_mb,
                    'is_ainews': p in snapshot.ainews_processes
                }
                for p in snapshot.top_memory_consumers[:5]
            ]
        }


# Глобальный экземпляр мониторинга памяти
memory_monitor: Optional[SystemMemoryMonitor] = None


def initialize_memory_monitor(monitoring_db=None, max_memory_gb: float = 10.0) -> SystemMemoryMonitor:
    """Инициализация глобального мониторинга памяти"""
    global memory_monitor
    
    if memory_monitor is None:
        memory_monitor = SystemMemoryMonitor(
            max_memory_gb=max_memory_gb,
            warning_threshold_gb=1.5,  # 1.5GB для AI News проекта
            critical_threshold_gb=2.0,  # 2GB для AI News проекта
            monitoring_db=monitoring_db
        )
    
    return memory_monitor


def get_memory_monitor() -> Optional[SystemMemoryMonitor]:
    """Получить глобальный экземпляр мониторинга памяти"""
    return memory_monitor
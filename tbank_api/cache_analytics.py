# tbank_api/cache_analytics.py
"""
Аналитика использования кэша (защищенная версия)
"""

from datetime import datetime
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

# 🔧 ЗАЩИЩЕННЫЙ ИМПОРТ PSUTIL
try:
    import psutil
    PSUTIL_AVAILABLE = True
    logger.info("✅ psutil доступен для мониторинга системы")
except ImportError as e:
    psutil = None
    PSUTIL_AVAILABLE = False
    logger.warning(f"⚠️ psutil не доступен: {e}")

class CacheAnalytics:
    """Аналитика и мониторинг кэша"""
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.performance_stats = {
            'hits': 0,
            'misses': 0,
            'total_requests': 0,
            'size_history': [],
            'response_times': []
        }
        self.start_time = datetime.now()
    
    def record_hit(self):
        """Записывает попадание в кэш"""
        self.performance_stats['hits'] += 1
        self.performance_stats['total_requests'] += 1
    
    def record_miss(self):
        """Записывает промах кэша"""
        self.performance_stats['misses'] += 1
        self.performance_stats['total_requests'] += 1
    
    def record_response_time(self, response_time: float):
        """Записывает время ответа"""
        self.performance_stats['response_times'].append(
            (datetime.now(), response_time)
        )
        # Храним только последние 1000 записей
        if len(self.performance_stats['response_times']) > 1000:
            self.performance_stats['response_times'] = \
                self.performance_stats['response_times'][-1000:]
    
    def get_hit_ratio(self) -> float:
        """Возвращает процент попаданий в кэш"""
        total = self.performance_stats['total_requests']
        if total == 0:
            return 0.0
        return self.performance_stats['hits'] / total
    
    def get_memory_usage(self) -> float:
        """Безопасное получение использования памяти"""
        if not PSUTIL_AVAILABLE:
            return 0.0
        
        try:
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024  # MB
        except Exception as e:
            logger.warning(f"Не удалось получить использование памяти: {e}")
            return 0.0
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Генерирует отчет о производительности"""
        hit_ratio = self.get_hit_ratio()
        response_times = [rt for _, rt in self.performance_stats['response_times']]
        avg_response_time = np.mean(response_times) if response_times else 0
        
        # Использование памяти (защищенный вызов)
        memory_usage = self.get_memory_usage()
        
        uptime_seconds = (datetime.now() - self.start_time).total_seconds()
        uptime_hours = uptime_seconds / 3600
        
        return {
            'hit_ratio': hit_ratio,
            'total_requests': self.performance_stats['total_requests'],
            'hits': self.performance_stats['hits'],
            'misses': self.performance_stats['misses'],
            'avg_response_time_ms': avg_response_time * 1000,
            'memory_usage_mb': memory_usage,
            'uptime_hours': uptime_hours,
            'requests_per_hour': self.performance_stats['total_requests'] / max(1, uptime_hours),
            'psutil_available': PSUTIL_AVAILABLE
        }
# tbank_api/advanced_analytics.py
"""
Расширенная аналитика использования кэша и оптимизаций
"""

import time
from datetime import datetime, timedelta
from collections import deque
import threading
from typing import Dict, Any, List
import logging

# ✅ ДОБАВЬТЕ ИМПОРТ PSUTIL С ОБРАБОТКОЙ ОШИБОК
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.debug("psutil не установлен. Мониторинг памяти будет отключен.")

logger = logging.getLogger(__name__)

class AdvancedCacheAnalytics:
    """Продвинутая аналитика в реальном времени"""
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.metrics_history = {
            'hit_ratio': deque(maxlen=100),
            'response_time': deque(maxlen=100),
            'memory_usage': deque(maxlen=100),
            'cache_size': deque(maxlen=100)
        }
        self.performance_alerts = []
        self.start_time = datetime.now()
        
        # Запускаем сбор метрик в фоне
        self._start_metrics_collection()
    
    def _start_metrics_collection(self):
        """Запуск сбора метрик в фоновом режиме"""
        def collect_metrics():
            while True:
                try:
                    self._collect_metrics_snapshot()
                    time.sleep(60)  # Каждую минуту
                except Exception as e:
                    logger.error(f"Ошибка сбора метрик: {e}")
                    time.sleep(300)
        
        thread = threading.Thread(target=collect_metrics, daemon=True)
        thread.start()
    
    def _collect_metrics_snapshot(self):
        """Сбор снимка метрик"""
        try:
            stats = self.cache_manager.get_detailed_analytics()
            
            # Сохраняем исторические данные
            self.metrics_history['hit_ratio'].append({
                'timestamp': datetime.now(),
                'value': float(stats.get('cache_hit_ratio', '0%').rstrip('%')) / 100
            })
            
            self.metrics_history['response_time'].append({
                'timestamp': datetime.now(),
                'value': stats.get('avg_response_time_ms', 0)
            })
            
            # ✅ БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ИСПОЛЬЗОВАНИЯ ПАМЯТИ
            memory_usage = 0
            if PSUTIL_AVAILABLE:
                try:
                    process = psutil.Process()
                    memory_usage = process.memory_info().rss / 1024 / 1024  # MB
                except Exception as e:
                    logger.debug(f"Не удалось получить использование памяти: {e}")
            else:
                # Используем значение из аналитики как запасной вариант
                memory_usage = stats.get('memory_usage_mb', 0)
            
            self.metrics_history['memory_usage'].append({
                'timestamp': datetime.now(),
                'value': memory_usage
            })
            
            self.metrics_history['cache_size'].append({
                'timestamp': datetime.now(),
                'value': stats.get('total_cache_size_mb', 0)
            })
            
            # Проверяем алерты
            self._check_performance_alerts(stats)
            
        except Exception as e:
            logger.error(f"Ошибка сбора метрик: {e}")
    
    def _check_performance_alerts(self, stats: Dict[str, Any]):
        """Проверка алертов производительности"""
        hit_ratio = float(stats.get('cache_hit_ratio', '0%').rstrip('%'))
        
        if hit_ratio < 20:  # Низкий процент попаданий
            self._add_alert("warning", "Низкий процент попаданий в кэш", 
                           f"Hit ratio: {hit_ratio}%", "cache_performance")
        
        # Проверяем использование памяти только если psutil доступен
        if PSUTIL_AVAILABLE:
            memory_usage = stats.get('memory_usage_mb', 0)
            if memory_usage > 500:  # Высокое использование памяти
                self._add_alert("error", "Высокое использование памяти", 
                               f"Используется: {memory_usage} MB", "memory")
    
    def _add_alert(self, level: str, title: str, message: str, alert_type: str):
        """Добавление алерта"""
        alert = {
            'level': level,
            'title': title,
            'message': message,
            'type': alert_type,
            'timestamp': datetime.now(),
            'acknowledged': False
        }
        self.performance_alerts.append(alert)
        logger.warning(f"🚨 {level.upper()}: {title} - {message}")
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Получить активные алерты"""
        return [alert for alert in self.performance_alerts if not alert['acknowledged']]
    
    def acknowledge_alert(self, alert_index: int):
        """Подтвердить алерт"""
        if 0 <= alert_index < len(self.performance_alerts):
            self.performance_alerts[alert_index]['acknowledged'] = True
            logger.info(f"✅ Алерт #{alert_index} подтвержден")
    
    def get_metrics_history(self, metric_type: str, last_n: int = None) -> List[Dict]:
        """Получить историю метрик"""
        history = self.metrics_history.get(metric_type, [])
        if last_n:
            return list(history)[-last_n:]
        return list(history)
    
    def get_performance_trends(self) -> Dict[str, Any]:
        """Анализ трендов производительности"""
        if not self.metrics_history['hit_ratio']:
            return {
                'status': 'no_data',
                'message': 'Метрики еще не собраны',
                'hit_ratio_trend': 'stable',
                'response_time_trend': 'stable',
                'active_alerts': 0,
                'uptime_hours': 0
            }
        
        hit_ratios = [point['value'] for point in self.metrics_history['hit_ratio']]
        response_times = [point['value'] for point in self.metrics_history['response_time']]
        
        # Простой анализ трендов
        hit_trend = 'stable'
        if len(hit_ratios) > 1:
            if hit_ratios[-1] > hit_ratios[0] + 0.1:  # +10%
                hit_trend = 'up'
            elif hit_ratios[-1] < hit_ratios[0] - 0.1:  # -10%
                hit_trend = 'down'
        
        response_trend = 'stable'
        if len(response_times) > 1:
            if response_times[-1] < response_times[0] - 10:  # -10ms
                response_trend = 'down'  # Улучшение
            elif response_times[-1] > response_times[0] + 10:  # +10ms
                response_trend = 'up'  # Ухудшение
        
        return {
            'hit_ratio_trend': hit_trend,
            'avg_hit_ratio': sum(hit_ratios) / len(hit_ratios) if hit_ratios else 0,
            'response_time_trend': response_trend,
            'avg_response_time_ms': sum(response_times) / len(response_times) if response_times else 0,
            'active_alerts': len(self.get_active_alerts()),
            'uptime_hours': round((datetime.now() - self.start_time).total_seconds() / 3600, 2),
            'data_points': len(hit_ratios),
            'memory_monitoring': PSUTIL_AVAILABLE  # ✅ Информация о доступности мониторинга памяти
        }
    
    def clear_old_alerts(self, hours_old: int = 24):
        """Очистка старых алертов"""
        cutoff_time = datetime.now() - timedelta(hours=hours_old)
        self.performance_alerts = [
            alert for alert in self.performance_alerts 
            if alert['timestamp'] > cutoff_time or not alert['acknowledged']
        ]
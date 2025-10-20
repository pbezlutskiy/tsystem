# tbank_api/auto_optimizer.py
"""
Автоматическая оптимизация параметров кэширования
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class AutoOptimizer:
    """Автоматическая оптимизация параметров системы"""
    
    def __init__(self, cache_manager, config_path: Path = None):
        self.cache_manager = cache_manager
        self.config_path = config_path or Path("tbank_api/optimization_config.json")
        self.optimization_history = []
        
        # Загружаем конфигурацию
        self.config = self._load_config()
        self.last_optimization = None
        
    def _load_config(self) -> Dict[str, Any]:
        """Загрузка конфигурации оптимизации"""
        default_config = {
            'optimization_enabled': True,
            'auto_cleanup_enabled': True,
            'cleanup_threshold_mb': 1000,
            'ttl_optimization': True,
            'performance_monitoring': True,
            'optimization_schedule': 'daily',
            'min_hit_ratio_for_cleanup': 30,
            'max_cache_size_mb': 2000
        }
        
        try:
            if self.config_path.exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    return {**default_config, **loaded_config}
        except Exception as e:
            logger.error(f"Ошибка загрузки конфигурации: {e}")
        
        return default_config
    
    def save_config(self):
        """Сохранение конфигурации"""
        try:
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            logger.info("✅ Конфигурация оптимизации сохранена")
        except Exception as e:
            logger.error(f"Ошибка сохранения конфигурации: {e}")
    
    def optimize_cache_parameters(self):
        """Автоматическая оптимизация параметров кэша"""
        if not self.config['optimization_enabled']:
            return
        
        # Проверяем когда была последняя оптимизация
        if (self.last_optimization and 
            (datetime.now() - self.last_optimization).hours < 12):
            return
            
        try:
            analytics = self.cache_manager.get_detailed_analytics()
            
            # Анализ эффективности
            hit_ratio = float(analytics.get('cache_hit_ratio', '0%').rstrip('%'))
            cache_size = analytics.get('total_cache_size_mb', 0)
            
            optimization_actions = []
            
            # Оптимизация на основе hit ratio
            if self.config['ttl_optimization']:
                ttl_action = self._optimize_based_on_hit_ratio(hit_ratio)
                if ttl_action:
                    optimization_actions.append(ttl_action)
            
            # Автоочистка при большом размере кэша
            if (self.config['auto_cleanup_enabled'] and 
                cache_size > self.config['cleanup_threshold_mb'] and
                hit_ratio < self.config['min_hit_ratio_for_cleanup']):
                cleanup_action = self._perform_auto_cleanup()
                if cleanup_action:
                    optimization_actions.append(cleanup_action)
            
            # Логируем оптимизации
            if optimization_actions:
                self._log_optimization(optimization_actions, analytics)
                self.last_optimization = datetime.now()
                
        except Exception as e:
            logger.error(f"Ошибка оптимизации параметров: {e}")
    
    def _optimize_based_on_hit_ratio(self, hit_ratio: float) -> Dict[str, Any]:
        """Оптимизация на основе hit ratio"""
        action = {}
        
        if hit_ratio < 30:
            action = {
                'type': 'increase_ttl',
                'reason': f'Низкий hit ratio: {hit_ratio}%',
                'recommendation': 'Увеличить TTL для инструментов и свечей',
                'timestamp': datetime.now().isoformat()
            }
        elif hit_ratio > 80:
            action = {
                'type': 'decrease_ttl', 
                'reason': f'Высокий hit ratio: {hit_ratio}%',
                'recommendation': 'Можно уменьшить TTL для экономии памяти',
                'timestamp': datetime.now().isoformat()
            }
        
        return action
    
    def _perform_auto_cleanup(self) -> Dict[str, Any]:
        """Автоматическая очистка кэша"""
        try:
            # Получаем статистику перед очисткой
            stats_before = self.cache_manager.get_cache_stats()
            
            # Выполняем очистку
            self.cache_manager.clear_all_cache()
            
            # Логируем действие
            return {
                'type': 'auto_cleanup',
                'reason': f'Размер кэша превысил {self.config["cleanup_threshold_mb"]} MB',
                'size_before_mb': stats_before.get('total_cache_size_mb', 0),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Ошибка автоочистки: {e}")
            return {}
    
    def _log_optimization(self, actions: List[Dict[str, Any]], analytics: Dict[str, Any]):
        """Логирование выполненных оптимизаций"""
        optimization_record = {
            'timestamp': datetime.now().isoformat(),
            'actions': actions,
            'analytics_snapshot': {
                'hit_ratio': analytics.get('cache_hit_ratio'),
                'cache_size_mb': analytics.get('total_cache_size_mb'),
                'memory_usage_mb': analytics.get('memory_usage_mb')
            }
        }
        
        self.optimization_history.append(optimization_record)
        
        # Сохраняем только последние 50 записей
        if len(self.optimization_history) > 50:
            self.optimization_history = self.optimization_history[-50:]
        
        # Логируем в консоль
        for action in actions:
            logger.info(f"⚙️ Автооптимизация: {action['type']} - {action['reason']}")
    
    def get_optimization_history(self, last_n: int = 10) -> List[Dict]:
        """История оптимизаций"""
        return list(self.optimization_history)[-last_n:]
    
    def update_config(self, new_config: Dict[str, Any]):
        """Обновление конфигурации"""
        self.config.update(new_config)
        self.save_config()
        logger.info("✅ Конфигурация оптимизации обновлена")
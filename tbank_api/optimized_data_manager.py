# tbank_api/optimized_data_manager.py
"""
Оптимизированный менеджер с расширенной аналитикой
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

# ✅ ПРАВИЛЬНЫЙ ИМПОРТ PSUTIL С ОБРАБОТКОЙ ОШИБОК
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.debug("psutil не установлен. Мониторинг памяти будет отключен.")

from .tbank_api import TBankAPI
from .tbank_cache import TBankCache, CacheConfig
from .cache_optimizer import SafeCacheOptimizer
from .advanced_analytics import AdvancedCacheAnalytics
from .smart_predictor import SmartPredictor
from .auto_optimizer import AutoOptimizer

logger = logging.getLogger(__name__)

class OptimizedTBankDataManager:
    """Оптимизированный менеджер с расширенной аналитикой"""
    
    def __init__(self, api_key: str = None):
        self.api = TBankAPI(api_key)
        self.cache = TBankCache()
        self.optimizer = SafeCacheOptimizer()
        self.available_symbols = None
        
        # ✅ ИНИЦИАЛИЗИРУЕМ РАСШИРЕННУЮ АНАЛИТИКУ
        self.advanced_analytics = AdvancedCacheAnalytics(self)
        
        self.performance_stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'optimization_savings_mb': 0.0
        }
        
         # ✅ ДОБАВЛЯЕМ УМНЫЙ ПРЕДСКАЗАТЕЛЬ И АВТООПТИМИЗАТОР
        self.smart_predictor = SmartPredictor(self)
        self.auto_optimizer = AutoOptimizer(self)
        
        logger.info("✅ Оптимизированный менеджер с AI-предсказаниями инициализирован")
    
    def get_historical_data_with_cache(self, symbol: str, 
                                     start_date: str, 
                                     end_date: str = None,
                                     timeframe: str = '1d',
                                     use_cache: bool = True) -> pd.DataFrame:
        """
        Улучшенная загрузка данных с расширенной аналитикой
        """
        self.performance_stats['total_requests'] += 1
        
        if not use_cache:
            return self.api.get_historical_data(symbol, start_date, end_date, timeframe)
            
        # Конвертация дат
        from_dt = datetime.strptime(start_date, '%Y-%m-%d')
        to_dt = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()
        
        # Получаем FIGI
        figi = self.api._get_figi_by_ticker(symbol)
        if not figi:
            logger.error(f"FIGI не найден для {symbol}")
            return pd.DataFrame()
        
        # Пытаемся загрузить из кэша
        cached_data = self.cache.load_candles(figi, timeframe, from_dt, to_dt)
        if cached_data is not None and not cached_data.empty:
            logger.info(f"✅ Данные из кэша: {symbol} ({len(cached_data)} записей)")
            self.performance_stats['cache_hits'] += 1
            return cached_data
        
        # Загружаем из API
        logger.info(f"🔄 Загрузка из API: {symbol}")
        self.performance_stats['cache_misses'] += 1
        
        api_data = self.api.get_historical_data(symbol, start_date, end_date, timeframe)
        
        if api_data.empty:
            return pd.DataFrame()
        
        # Безопасная оптимизация данных
        original_size = api_data.memory_usage(deep=True).sum() / 1024 / 1024
        optimized_data = self.optimizer.optimize_dataframe_safe(api_data)
        
        # Логируем экономию места
        optimized_size = optimized_data.memory_usage(deep=True).sum() / 1024 / 1024
        savings = original_size - optimized_size
        if savings > 0:
            self.performance_stats['optimization_savings_mb'] += savings
            logger.info(f"💾 Экономия памяти: {savings:.2f} MB для {symbol}")
        
        # Сохраняем оптимизированные данные в кэш
        self.cache.save_candles(figi, timeframe, optimized_data, (from_dt, to_dt))
        
        return api_data
    
    # ===== РАСШИРЕННАЯ АНАЛИТИКА =====
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Базовая статистика производительности"""
        total_requests = self.performance_stats['total_requests']
        cache_hits = self.performance_stats['cache_hits']
        
        hit_ratio = (cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'total_requests': total_requests,
            'cache_hits': cache_hits,
            'cache_misses': self.performance_stats['cache_misses'],
            'cache_hit_ratio': f"{hit_ratio:.1f}%",
            'memory_savings_mb': round(self.performance_stats['optimization_savings_mb'], 2),
            'avg_savings_per_request': round(
                self.performance_stats['optimization_savings_mb'] / max(1, total_requests), 4
            )
        }

    def get_detailed_analytics(self) -> Dict[str, Any]:
        """Детальная аналитика с расширенными метриками"""
        cache_stats = self.cache.get_cache_stats()
        performance_stats = self.get_performance_stats()
        
        try:
            # Безопасное получение расширенной аналитики
            advanced_trends = self.advanced_analytics.get_performance_trends()
            active_alerts = self.advanced_analytics.get_active_alerts()
        except Exception as e:
            logger.warning(f"Ошибка получения расширенной аналитики: {e}")
            advanced_trends = {
                'hit_ratio_trend': 'stable',
                'response_time_trend': 'stable', 
                'active_alerts': 0,
                'uptime_hours': 0,
                'data_points': 0
            }
            active_alerts = []
        
        # ✅ БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ИСПОЛЬЗОВАНИЯ ПАМЯТИ
        memory_usage = 0
        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            except Exception as e:
                logger.warning(f"Не удалось получить использование памяти: {e}")
        else:
            logger.debug("psutil недоступен, использование памяти не отслеживается")
        
        return {
            **cache_stats,
            **performance_stats,
            **advanced_trends,
            'memory_usage_mb': round(memory_usage, 2),
            'active_alerts_count': len(active_alerts),
            'optimization_level': 'advanced',
            'status': 'active',
            'features': {
                'advanced_analytics': True,
                'performance_monitoring': True,
                'real_time_metrics': True,
                'memory_monitoring': PSUTIL_AVAILABLE
            }
        }

    def get_advanced_analytics(self) -> Dict[str, Any]:
        """Полная расширенная аналитика"""
        return {
            'basic_stats': self.get_performance_stats(),
            'cache_info': self.cache.get_cache_stats(),
            'advanced_trends': self.advanced_analytics.get_performance_trends(),
            'active_alerts': self.advanced_analytics.get_active_alerts(),
            'metrics_history': {
                'hit_ratio': self.advanced_analytics.get_metrics_history('hit_ratio', 10),
                'response_time': self.advanced_analytics.get_metrics_history('response_time', 10)
            }
        }
    
    def acknowledge_alert(self, alert_index: int):
        """Подтвердить алерт в расширенной аналитике"""
        self.advanced_analytics.acknowledge_alert(alert_index)
    
    # ===== СОВМЕСТИМОСТЬ С СУЩЕСТВУЮЩИМ КОДОМ =====
    
    def get_instruments_with_cache(self, instrument_type: str = None, 
                                 force_refresh: bool = False) -> pd.DataFrame:
        """Получение списка инструментов с кэшированием"""
        cache_key = instrument_type or "all"
        
        if not force_refresh:
            cached_instruments = self.cache.load_instruments(cache_key)
            if cached_instruments is not None and not cached_instruments.empty:
                logger.info(f"✅ Инструменты из кэша: {cache_key}")
                return cached_instruments
        
        logger.info(f"🔄 Загрузка инструментов из API: {cache_key}")
        api_instruments = self.api.get_instruments_list(instrument_type)
        
        if api_instruments.empty:
            return pd.DataFrame()
        
        self.cache.save_instruments(api_instruments, cache_key)
        return api_instruments
    
    def get_available_symbols_cached(self, force_refresh: bool = False) -> pd.DataFrame:
        """Получение списка доступных символов с кэшированием"""
        if self.available_symbols is None or force_refresh:
            self.available_symbols = self.get_instruments_with_cache(force_refresh=force_refresh)
        return self.available_symbols
    
    def update_data_incrementally(self, symbol: str, 
                                days_back: int = 1,
                                timeframe: str = '1d') -> pd.DataFrame:
        """Инкрементальное обновление данных"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        fresh_data = self.api.get_historical_data(
            symbol=symbol,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            timeframe=timeframe
        )
        
        if fresh_data.empty:
            logger.warning(f"Нет свежих данных для {symbol}")
            return pd.DataFrame()
        
        figi = self.api._get_figi_by_ticker(symbol)
        if not figi:
            return fresh_data
        
        updated_data = self.cache.update_candles_incrementally(figi, timeframe, fresh_data)
        return updated_data
    
    def search_instruments_cached(self, query: str) -> pd.DataFrame:
        """Поиск инструментов в кэшированном списке"""
        symbols_df = self.get_available_symbols_cached()
        if symbols_df.empty:
            return pd.DataFrame()
        
        mask = (symbols_df['symbol'].str.contains(query, case=False, na=False) | 
                symbols_df['name'].str.contains(query, case=False, na=False))
        
        return symbols_df[mask].copy()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Информация о состоянии кэша"""
        return self.cache.get_cache_stats()
    
    def clear_all_cache(self):
        """Очистка всего кэша"""
        self.cache.clear_cache()
        self.available_symbols = None
    
    def is_symbol_available(self, symbol: str) -> bool:
        """Проверка доступности символа"""
        symbols_df = self.get_available_symbols_cached()
        return not symbols_df.empty and symbol in symbols_df['symbol'].values
    
    # ДОБАВЬТЕ НОВЫЕ МЕТОДЫ:
    def preload_data(self, symbol: str, timeframe: str, days_back: int = 30):
        """Предзагрузка данных"""
        from datetime import datetime, timedelta
        
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        try:
            data = self.api.get_historical_data(
                symbol, 
                start_date.strftime('%Y-%m-%d'),
                end_date.strftime('%Y-%m-%d'),
                timeframe
            )
            
            if not data.empty:
                figi = self.api._get_figi_by_ticker(symbol)
                if figi:
                    optimized_data = self.optimizer.optimize_dataframe_safe(data)
                    self.cache.save_candles(figi, timeframe, optimized_data, (start_date, end_date))
                    logger.info(f"✅ Предзагружено {len(data)} записей для {symbol}")
                    
        except Exception as e:
            logger.warning(f"Ошибка предзагрузки {symbol}: {e}")
    
    def get_prediction_stats(self) -> Dict[str, Any]:
        """Статистика предсказаний"""
        return self.smart_predictor.get_prediction_stats()
    
    def get_optimization_info(self) -> Dict[str, Any]:
        """Информация об оптимизациях"""
        return {
            'auto_optimization_enabled': self.auto_optimizer.config['optimization_enabled'],
            'optimization_history_count': len(self.auto_optimizer.optimization_history),
            'last_optimization': self.auto_optimizer.last_optimization
        }    
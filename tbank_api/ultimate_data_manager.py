# tbank_api/ultimate_data_manager.py
"""
УЛЬТИМАТИВНЫЙ менеджер данных со всеми улучшениями
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
from .tbank_api import TBankAPI
from .tbank_cache import TBankCache, CacheConfig
from .cache_optimizer import SafeCacheOptimizer
from .advanced_analytics import AdvancedCacheAnalytics
from .smart_predictor import SmartPredictor
from .auto_optimizer import AutoOptimizer

logger = logging.getLogger(__name__)

class UltimateTBankDataManager:
    """Ультимативный менеджер данных со всеми улучшениями"""
    
    def __init__(self, api_key: str = None):
        self.api = TBankAPI(api_key)
        self.cache = TBankCache()
        self.optimizer = SafeCacheOptimizer()
        self.available_symbols = None
        
        # Инициализация расширенных систем
        self.analytics = AdvancedCacheAnalytics(self)
        self.predictor = SmartPredictor(self)
        self.auto_optimizer = AutoOptimizer(self)
        
        self.performance_stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'optimization_savings_mb': 0.0,
            'predictions_made': 0
        }
        
        logger.info("🚀 UltimateTBankDataManager инициализирован со всеми улучшениями!")
    
    def get_historical_data_with_cache(self, symbol: str, 
                                     start_date: str, 
                                     end_date: str = None,
                                     timeframe: str = '1d',
                                     use_cache: bool = True) -> pd.DataFrame:
        """
        Улучшенная загрузка данных со всеми оптимизациями
        """
        self.performance_stats['total_requests'] += 1
        
        # Записываем обращение для предсказания
        self.predictor.record_access(symbol, timeframe)
        
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
        
        # Сохраняем оптимизированные данные в кэш
        self.cache.save_candles(figi, timeframe, optimized_data, (from_dt, to_dt))
        
        # Запускаем автооптимизацию
        self.auto_optimizer.optimize_cache_parameters()
        
        return api_data
    
    def get_comprehensive_analytics(self) -> Dict[str, Any]:
        """Всеобъемлющая аналитика"""
        cache_stats = self.cache.get_cache_stats()
        performance_stats = self.get_performance_stats()
        trends = self.analytics.get_performance_trends()
        
        return {
            **cache_stats,
            **performance_stats,
            **trends,
            'optimization_level': 'ultimate',
            'status': 'active',
            'features': {
                'smart_predictions': True,
                'advanced_analytics': True,
                'auto_optimization': True,
                'performance_monitoring': True
            }
        }
    
    # ... остальные методы для совместимости ...
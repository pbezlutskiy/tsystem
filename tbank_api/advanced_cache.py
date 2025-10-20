# tbank_api/advanced_cache.py
"""
Продвинутая система кэширования - НАСЛЕДУЕТ от базового кэша
"""

import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import logging
from .cache_config import CacheConfig
from .tbank_cache import TBankCache  # Наследуем от рабочего кэша

logger = logging.getLogger(__name__)

class AdvancedTBankCache(TBankCache):  # ✅ НАСЛЕДОВАНИЕ вместо делегирования
    """Продвинутый кэш с оптимизациями, наследует все методы базового кэша"""
    
    def __init__(self, config: CacheConfig = None):
        # Вызываем конструктор родителя
        super().__init__(config)
        self._access_stats = {}
        self._hits = 0
        self._misses = 0
        
    def get_historical_data_smart(self, symbol: str, start_date: str, end_date: str, 
                                timeframe: str = '1d') -> Tuple[pd.DataFrame, bool]:
        """
        Умная загрузка данных: возвращает данные и флаг "из кэша"
        """
        try:
            # Получаем FIGI через API (упрощенная версия)
            figi = self._get_figi_cached(symbol)
            if not figi:
                return pd.DataFrame(), False
                
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            
            # Используем родительский метод
            cached_data = self.load_candles(figi, timeframe, start_dt, end_dt)
            if cached_data is not None and not cached_data.empty:
                self._hits += 1
                return cached_data, True
                
            self._misses += 1
            return pd.DataFrame(), False
            
        except Exception as e:
            logger.error(f"Ошибка в умной загрузке: {e}")
            return pd.DataFrame(), False
    
    def _get_figi_cached(self, symbol: str) -> Optional[str]:
        """Упрощенный метод получения FIGI"""
        # В реальной реализации здесь будет сложная логика
        # Пока возвращаем заглушку
        return f"FIGI_{symbol}"
    
    def smart_update(self, figi: str, timeframe: str, new_data: pd.DataFrame) -> pd.DataFrame:
        """
        Умное обновление: объединяет данные
        """
        if new_data.empty:
            return new_data
            
        try:
            # Используем родительский метод для сохранения
            start_date = new_data.index.min()
            end_date = new_data.index.max()
            self.save_candles(figi, timeframe, new_data, (start_date, end_date))
            return new_data
            
        except Exception as e:
            logger.error(f"Ошибка в умном обновлении: {e}")
            return new_data
    
    def update_candles_incrementally(self, figi: str, timeframe: str,
                                   new_candles_df: pd.DataFrame) -> pd.DataFrame:
        """Алиас для совместимости"""
        return self.smart_update(figi, timeframe, new_candles_df)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Расширенная статистика"""
        base_stats = super().get_cache_stats()
        base_stats.update({
            'smart_hits': self._hits,
            'smart_misses': self._misses,
            'smart_hit_ratio': self._hits / max(1, self._hits + self._misses)
        })
        return base_stats
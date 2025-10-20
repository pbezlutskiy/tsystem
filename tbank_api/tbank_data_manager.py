# tbank_api/tbank_data_manager.py
"""
Умный менеджер данных с кэшированием для Tinkoff API
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
import logging
from .tbank_api import TBankAPI
from .tbank_cache import TBankCache, CacheConfig

logger = logging.getLogger(__name__)

class TBankDataManager:
    """Умный менеджер данных с двухуровневым кэшированием"""
    
    def __init__(self, api_key: str = None, cache_config: CacheConfig = None):
        self.api = TBankAPI(api_key)
        self.cache = TBankCache(cache_config)
        self.available_symbols = None
    
    def get_historical_data_with_cache(self, symbol: str, 
                                     start_date: str, 
                                     end_date: str = None,
                                     timeframe: str = '1d',
                                     use_cache: bool = True) -> pd.DataFrame:
        """
        Получение исторических данных с использованием кэша
        """
        # Конвертация дат
        from_dt = datetime.strptime(start_date, '%Y-%m-%d')
        to_dt = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()
        
        # Получаем FIGI
        figi = self.api._get_figi_by_ticker(symbol)
        if not figi:
            logger.error(f"FIGI не найден для {symbol}")
            return pd.DataFrame()
        
        # Пытаемся загрузить из кэша
        if use_cache:
            cached_data = self.cache.load_candles(figi, timeframe, from_dt, to_dt)
            if cached_data is not None and not cached_data.empty:
                logger.info(f"✅ Данные загружены из кэша: {symbol}")
                return cached_data
        
        # Загружаем из API
        logger.info(f"🔄 Загрузка данных из API: {symbol}")
        api_data = self.api.get_historical_data(symbol, start_date, end_date, timeframe)
        
        if api_data.empty:
            return pd.DataFrame()
        
        # Сохраняем в кэш
        if use_cache:
            self.cache.save_candles(figi, timeframe, api_data, (from_dt, to_dt))
        
        return api_data
    
    def get_instruments_with_cache(self, instrument_type: str = None, 
                                 force_refresh: bool = False) -> pd.DataFrame:
        """Получение списка инструментов с кэшированием"""
        cache_key = instrument_type or "all"
        
        # Пытаемся загрузить из кэша
        if not force_refresh:
            cached_instruments = self.cache.load_instruments(cache_key)
            if cached_instruments is not None and not cached_instruments.empty:
                logger.info(f"✅ Инструменты загружены из кэша: {cache_key}")
                return cached_instruments
        
        # Загружаем из API
        logger.info(f"🔄 Загрузка инструментов из API: {cache_key}")
        api_instruments = self.api.get_instruments_list(instrument_type)
        
        if api_instruments.empty:
            return pd.DataFrame()
        
        # Сохраняем в кэш
        self.cache.save_instruments(api_instruments, cache_key)
        
        return api_instruments
    
    def update_data_incrementally(self, symbol: str, 
                                days_back: int = 1,
                                timeframe: str = '1d') -> pd.DataFrame:
        """
        Инкрементальное обновление данных (догрузка свежих данных)
        """
        # Определяем период для догрузки
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        # Загружаем свежие данные
        fresh_data = self.api.get_historical_data(
            symbol=symbol,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            timeframe=timeframe
        )
        
        if fresh_data.empty:
            logger.warning(f"Нет свежих данных для {symbol}")
            return pd.DataFrame()
        
        # Получаем FIGI
        figi = self.api._get_figi_by_ticker(symbol)
        if not figi:
            return fresh_data
        
        # Инкрементальное обновление кэша
        updated_data = self.cache.update_candles_incrementally(
            figi, timeframe, fresh_data
        )
        
        return updated_data
    
    def get_available_symbols_cached(self, force_refresh: bool = False) -> pd.DataFrame:
        """Получение списка доступных символов с кэшированием"""
        if self.available_symbols is None or force_refresh:
            self.available_symbols = self.get_instruments_with_cache(force_refresh=force_refresh)
        return self.available_symbols
    
    def search_instruments_cached(self, query: str) -> pd.DataFrame:
        """Поиск инструментов в кэшированном списке"""
        symbols_df = self.get_available_symbols_cached()
        if symbols_df.empty:
            return pd.DataFrame()
        
        # Поиск по тикеру и названию
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
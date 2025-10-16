# tbank_api/tbank_data_loader.py
"""
Модуль загрузки данных из API Т-банка для интеграции с основной системой
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
from .tbank_api import TBankAPI
from .tbank_config import TBankConfig

logger = logging.getLogger(__name__)

class TBankDataLoader:
    """Загрузчик данных из Т-банка API"""
    
    def __init__(self, api_key: str = None):
        self.config = TBankConfig()
        
        # Используем переданный ключ или ключ из конфигурации
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = self.config.get_api_key()
        
        self.api = TBankAPI(self.api_key, self.config.get('api_url'))
        self.cache = {}
        self.cache_time = {}
    
    def load_price_data(self, symbol: str, 
                       days_back: int = 365,
                       timeframe: str = '1d') -> pd.DataFrame:
        """
        Загрузка ценовых данных для использования в торговой системе
        
        Parameters:
        -----------
        symbol : str
            Тикер инструмента
        days_back : int
            Количество дней исторических данных
        timeframe : str
            Таймфрейм данных
            
        Returns:
        --------
        pd.DataFrame
            Данные в формате системы
        """
        # Проверка API ключа
        if not self.api_key:
            logger.error("API ключ не установлен")
            return pd.DataFrame()
        
        cache_key = f"{symbol}_{timeframe}_{days_back}"
        
        # Проверка кэша
        if self._is_cached_valid(cache_key):
            logger.info(f"Используются кэшированные данные для {symbol}")
            return self.cache[cache_key].copy()
        
        # Расчет дат
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"🔄 Загрузка реальных данных для {symbol}...")
        
        # Загрузка данных
        data = self.api.get_historical_data(
            symbol=symbol,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            timeframe=timeframe
        )
        
        if data.empty:
            logger.error(f"Не удалось загрузить реальные данные для {symbol}")
            return pd.DataFrame()
        
        # Стандартизация данных под формат системы
        standardized_data = self._standardize_data(data, symbol)
        
        # Сохранение в кэш
        self.cache[cache_key] = standardized_data.copy()
        self.cache_time[cache_key] = datetime.now()
        
        logger.info(f"✅ Загружено {len(standardized_data)} реальных записей для {symbol}")
        return standardized_data
    
    def _standardize_data(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Стандартизация данных под формат торговой системы
        
        Parameters:
        -----------
        data : pd.DataFrame
            Исходные данные из API
        symbol : str
            Тикер инструмента
            
        Returns:
        --------
        pd.DataFrame
            Стандартизированные данные
        """
        result = data.copy()
        
        # Проверка обязательных колонок
        required_columns = ['close']
        for col in required_columns:
            if col not in result.columns:
                logger.error(f"Отсутствует обязательная колонка: {col}")
                return pd.DataFrame()
        
        # Заполнение отсутствующих колонок (если API не возвращает все колонки)
        if 'open' not in result.columns and 'close' in result.columns:
            result['open'] = result['close']
        
        if 'high' not in result.columns and 'close' in result.columns:
            result['high'] = result['close']
        
        if 'low' not in result.columns and 'close' in result.columns:
            result['low'] = result['close']
        
        if 'volume' not in result.columns:
            result['volume'] = 0  # Значение по умолчанию
        
        # Добавление информации об инструменте
        result['symbol'] = symbol
        
        # Сортировка по дате
        if not result.index.is_monotonic_increasing:
            result.sort_index(inplace=True)
        
        return result
    
    def _is_cached_valid(self, cache_key: str) -> bool:
        """Проверка валидности кэшированных данных"""
        if cache_key not in self.cache:
            return False
        
        cache_duration = self.config.get('cache_duration_minutes', 5)
        cache_age = datetime.now() - self.cache_time.get(cache_key, datetime.min)
        
        return cache_age.total_seconds() < cache_duration * 60
    
    def get_available_symbols(self) -> pd.DataFrame:
        """Получение списка доступных инструментов"""
        if not self.api_key:
            logger.error("API ключ не установлен")
            return pd.DataFrame()
        return self.api.get_instruments_list()
    
    def get_current_prices(self, symbols: List[str]) -> pd.DataFrame:
        """Получение текущих цен для списка инструментов"""
        if not self.api_key:
            logger.error("API ключ не установлен")
            return pd.DataFrame()
        return self.api.get_current_quotes(symbols)
    
    def clear_cache(self):
        """Очистка кэша"""
        self.cache.clear()
        self.cache_time.clear()
        logger.info("Кэш данных очищен")
    
    def is_configured(self) -> bool:
        """Проверка, настроен ли загрузчик"""
        return bool(self.api_key)
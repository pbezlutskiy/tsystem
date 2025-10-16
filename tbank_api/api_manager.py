# tbank_api/api_manager.py
"""
Менеджер для работы с API
ИСПРАВЛЕННАЯ ВЕРСИЯ
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from .tbank_api import TBankAPI
from .moex_api import MoexAPI
from .tbank_config import TBankConfig

logger = logging.getLogger(__name__)

class ApiManager:
    """ИСПРАВЛЕННЫЙ менеджер для управления API"""
    
    def __init__(self):
        self.config = TBankConfig()
        self.tbank_api = None
        self.moex_api = MoexAPI()
        self.current_api = 'moex'  # По умолчанию MOEX
        
        # Кэш для стандартизированных данных
        self._data_cache = {}
        self._cache_max_size = 10
        
        # Инициализируем Tinkoff API если есть ключ
        self._initialize_tbank_api()
    
    def _initialize_tbank_api(self):
        """Инициализация Tinkoff API с проверкой доступности"""
        api_key = self.config.get_api_key()
        if api_key and api_key.strip():
            # Убедимся, что ключ имеет правильный формат
            if not api_key.startswith('t.'):
                api_key = f"t.{api_key}"
            
            try:
                self.tbank_api = TBankAPI(api_key)
                
                # Тестируем подключение
                if self.tbank_api.test_connection():
                    logger.info("✅ Tinkoff API инициализирован и доступен")
                else:
                    logger.warning("❌ Tinkoff API не доступен - проверьте ключ")
                    self.tbank_api = None
                    
            except Exception as e:
                logger.error(f"❌ Ошибка инициализации Tinkoff API: {e}")
                self.tbank_api = None
        else:
            logger.info("ℹ️ API ключ Tinkoff не установлен - используем MOEX")
    
    def set_api(self, api_name: str) -> bool:
        """
        Установка активного API с проверкой доступности
        
        Parameters:
        -----------
        api_name : str
            Название API ('moex' или 'tbank')
            
        Returns:
        --------
        bool
            True если API успешно установлен
        """
        if api_name == 'tbank':
            if self.tbank_api is None or not self.tbank_api.is_available():
                logger.warning("Tinkoff API не инициализирован. Установите API токен.")
                return False
            
            # Дополнительная проверка подключения
            if not self.tbank_api.test_connection():
                logger.error("Tinkoff API недоступен - проверьте подключение")
                return False
        elif api_name == 'moex':
            if not self.moex_api.test_connection():
                logger.warning("MOEX API недоступен - проверьте подключение к интернету")
                # MOEX все равно устанавливаем как основной, так как может работать офлайн
        else:
            logger.error(f"Неизвестный API: {api_name}")
            return False
        
        self.current_api = api_name
        logger.info(f"✅ Активный API установлен: {api_name}")
        return True
    
    def load_price_data(self, symbol: str, 
                       days_back: int = 365,
                       timeframe: str = 'D') -> pd.DataFrame:
        """
        Загрузка ценовых данных через активный API с кэшированием
        """
        # Создаем ключ кэша
        cache_key = f"{self.current_api}_{symbol}_{days_back}_{timeframe}"
        
        # Проверяем кэш
        if cache_key in self._data_cache:
            logger.info(f"✅ Данные загружены из кэша для {symbol}")
            return self._data_cache[cache_key].copy()
        
        # Расчет дат
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"Загрузка данных через {self.current_api.upper()} API для {symbol}")
        
        try:
            if self.current_api == 'tbank' and self.tbank_api:
                # Конвертация таймфреймов для Tinkoff
                tf_map = {
                    'D': '1d', '1d': '1d',
                    'H1': '1h', '1h': '1h', 
                    'H4': '4h', '4h': '4h',
                    'W': '1w', '1w': '1w',
                    '1m': '1m', '5m': '5m', '15m': '15m'
                }
                
                api_timeframe = tf_map.get(timeframe, '1d')
                
                data = self.tbank_api.get_historical_data(
                    symbol=symbol,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    timeframe=api_timeframe
                )
            else:
                # Используем таймфреймы как есть для MOEX
                data = self.moex_api.get_historical_data(
                    symbol=symbol,
                    start_date=start_date.strftime('%Y-%m-%d'),
                    end_date=end_date.strftime('%Y-%m-%d'),
                    timeframe=timeframe
                )
            
            if data.empty:
                logger.error(f"Не удалось загрузить данные через {self.current_api.upper()} API для {symbol}")
                return pd.DataFrame()
            
            # Стандартизация данных
            standardized_data = self._standardize_data(data, symbol)
            
            if standardized_data.empty:
                logger.error(f"Ошибка стандартизации данных для {symbol}")
                return pd.DataFrame()
            
            # Сохраняем в кэш
            self._add_to_cache(cache_key, standardized_data)
            
            logger.info(f"✅ Загружено {len(standardized_data)} записей через {self.current_api.upper()} API для {symbol}")
            return standardized_data
            
        except Exception as e:
            logger.error(f"❌ Ошибка загрузки данных для {symbol}: {e}")
            return pd.DataFrame()
    
    def _standardize_data(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """
        Стандартизация данных под формат системы
        """
        if data.empty:
            return pd.DataFrame()
        
        try:
            result = data.copy()
            
            # Проверка обязательных колонок
            required_columns = ['close']
            for col in required_columns:
                if col not in result.columns:
                    logger.error(f"Отсутствует обязательная колонка '{col}' в данных")
                    return pd.DataFrame()
            
            # Стандартизация имен колонок (если нужно)
            column_mapping = {
                'time': 'date',
                'datetime': 'date',
                'timestamp': 'date'
            }
            
            for old_name, new_name in column_mapping.items():
                if old_name in result.columns and new_name not in result.columns:
                    result[new_name] = result[old_name]
            
            # Убедимся, что у нас есть индекс datetime
            if not isinstance(result.index, pd.DatetimeIndex):
                if 'date' in result.columns:
                    result['date'] = pd.to_datetime(result['date'])
                    result.set_index('date', inplace=True)
                else:
                    # Создаем индекс на основе номера строки
                    result.index = pd.date_range(
                        start=datetime.now() - timedelta(days=len(result)),
                        periods=len(result),
                        freq='D'
                    )
            
            # Заполнение отсутствующих колонок
            if 'open' not in result.columns:
                result['open'] = result['close']
            
            if 'high' not in result.columns:
                result['high'] = result[['open', 'close']].max(axis=1)
            
            if 'low' not in result.columns:
                result['low'] = result[['open', 'close']].min(axis=1)
            
            if 'volume' not in result.columns:
                result['volume'] = 0
            
            # Добавление информации об инструменте
            result['symbol'] = symbol
            
            # Сортировка по дате
            if not result.index.is_monotonic_increasing:
                result.sort_index(inplace=True)
            
            # Удаление дубликатов по индексу
            result = result[~result.index.duplicated(keep='first')]
            
            # Проверка на наличие NaN в критических колонках
            critical_columns = ['open', 'high', 'low', 'close']
            for col in critical_columns:
                if result[col].isna().any():
                    logger.warning(f"Обнаружены NaN в колонке {col} - заполняем")
                    result[col] = result[col].fillna(method='ffill').fillna(method='bfill')
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка стандартизации данных: {e}")
            return pd.DataFrame()
    
    def _add_to_cache(self, key: str, data: pd.DataFrame):
        """
        Добавление данных в кэш с ограничением размера
        """
        # Очистка старых записей если кэш переполнен
        if len(self._data_cache) >= self._cache_max_size:
            oldest_key = next(iter(self._data_cache))
            del self._data_cache[oldest_key]
            logger.debug(f"Очищен кэш для ключа: {oldest_key}")
        
        self._data_cache[key] = data.copy()
    
    def get_available_symbols(self, market: str = 'shares') -> pd.DataFrame:
        """
        Получение списка доступных инструментов
        """
        try:
            if self.current_api == 'tbank' and self.tbank_api:
                # Для Tinkoff конвертируем тип рынка
                market_map = {
                    'shares': 'shares',
                    'bonds': 'bonds', 
                    'etfs': 'etfs',
                    'currencies': 'currencies',
                    'futures': 'futures',
                    'all': None
                }
                tbank_market = market_map.get(market, 'shares')
                return self.tbank_api.get_instruments_list(tbank_market)
            else:
                return self.moex_api.get_instruments_list(market)
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения списка инструментов: {e}")
            return pd.DataFrame()
    
    def get_current_quotes(self, symbols: List[str]) -> pd.DataFrame:
        """
        Получение текущих котировок
        """
        try:
            if self.current_api == 'tbank' and self.tbank_api:
                return self.tbank_api.get_current_quotes(symbols)
            else:
                return self.moex_api.get_current_quotes(symbols)
                
        except Exception as e:
            logger.error(f"❌ Ошибка получения котировок: {e}")
            return pd.DataFrame()
    
    def test_connection(self, api_name: str = None) -> bool:
        """
        Проверка подключения к API
        """
        api_to_test = api_name or self.current_api
        
        try:
            if api_to_test == 'tbank' and self.tbank_api:
                return self.tbank_api.test_connection()
            else:
                return self.moex_api.test_connection()
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки подключения к {api_to_test}: {e}")
            return False
    
    def is_tbank_available(self) -> bool:
        """
        Проверка доступности Tinkoff API
        """
        return self.tbank_api is not None and self.tbank_api.is_available()
    
    def get_api_status(self) -> Dict[str, bool]:
        """
        Получение статуса всех API
        """
        return {
            'moex': self.moex_api.test_connection(),
            'tbank': self.is_tbank_available() and (self.tbank_api.test_connection() if self.tbank_api else False),
            'current': self.current_api
        }
    
    def clear_cache(self):
        """
        Очистка кэша данных
        """
        self._data_cache.clear()
        if self.tbank_api:
            self.tbank_api.clear_cache()
        logger.info("✅ Кэш API менеджера очищен")
    
    def reload_tbank_api(self):
        """
        Перезагрузка Tinkoff API (например, после смены ключа)
        """
        self.tbank_api = None
        self._initialize_tbank_api()
        
        # Если текущий API был Tinkoff, проверяем доступность
        if self.current_api == 'tbank':
            if not self.is_tbank_available():
                logger.warning("Tinkoff API недоступен после перезагрузки - переключаем на MOEX")
                self.set_api('moex')
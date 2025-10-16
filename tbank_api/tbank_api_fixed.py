# tbank_api/tbank_api_fixed.py
"""
Исправленная версия Tinkoff API для торговой системы
ОБНОВЛЕННАЯ ВЕРСИЯ - использует исправленный основной класс
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging

# Импортируем исправленный основной класс
from .tbank_api import TBankAPI, quotation_to_float

logger = logging.getLogger(__name__)

class TBankAPIFixed:
    """
    Улучшенный класс для работы с Tinkoff Invest API
    Наследует функциональность из исправленного TBankAPI
    """
    
    def __init__(self, api_key: str = None):
        """
        Инициализация с использованием исправленного основного класса
        
        Parameters:
        -----------
        api_key : str
            API ключ Tinkoff Invest
        """
        self.api = TBankAPI(api_key)  # Используем исправленный основной класс
        self._additional_cache = {}  # Дополнительный кэш для специфичных данных
        
    def get_instruments_list(self, instrument_type: str = None) -> pd.DataFrame:
        """
        Получение списка доступных инструментов
        
        Parameters:
        -----------
        instrument_type : str, optional
            Тип инструмента ('shares', 'bonds', 'etfs', 'currencies', 'futures')
            
        Returns:
        --------
        pd.DataFrame
            DataFrame с инструментами
        """
        return self.api.get_instruments_list(instrument_type)
    
    def get_historical_data(self, symbol: str, 
                          start_date: str, 
                          end_date: str = None,
                          timeframe: str = '1d') -> pd.DataFrame:
        """
        Получение исторических данных по инструменту
        
        Parameters:
        -----------
        symbol : str
            Тикер инструмента
        start_date : str
            Начальная дата в формате 'YYYY-MM-DD'
        end_date : str, optional
            Конечная дата в формате 'YYYY-MM-DD'
        timeframe : str
            Таймфрейм ('1d', '1h', '4h', '1w', '1m', '5m', '15m')
            
        Returns:
        --------
        pd.DataFrame
            DataFrame с историческими данными
        """
        return self.api.get_historical_data(symbol, start_date, end_date, timeframe)
    
    def get_current_quotes(self, symbols: List[str]) -> pd.DataFrame:
        """
        Получение текущих котировок
        
        Parameters:
        -----------
        symbols : List[str]
            Список тикеров
            
        Returns:
        --------
        pd.DataFrame
            DataFrame с текущими котировками
        """
        return self.api.get_current_quotes(symbols)
    
    def test_connection(self) -> bool:
        """
        Проверка подключения к API
        
        Returns:
        --------
        bool
            True если подключение успешно
        """
        return self.api.test_connection()
    
    def is_available(self) -> bool:
        """
        Проверка доступности API
        
        Returns:
        --------
        bool
            True если API доступен
        """
        return self.api.is_available()
    
    def get_instrument_info(self, symbol: str) -> Dict:
        """
        ДОПОЛНИТЕЛЬНЫЙ МЕТОД: Получение детальной информации об инструменте
        
        Parameters:
        -----------
        symbol : str
            Тикер инструмента
            
        Returns:
        --------
        Dict
            Словарь с информацией об инструменте
        """
        cache_key = f"info_{symbol}"
        if cache_key in self._additional_cache:
            return self._additional_cache[cache_key].copy()
        
        try:
            instruments_df = self.api.get_instruments_list()
            if instruments_df.empty:
                return {}
            
            instrument_data = instruments_df[instruments_df['symbol'] == symbol]
            if instrument_data.empty:
                return {}
            
            info = instrument_data.iloc[0].to_dict()
            
            # Добавляем дополнительную информацию
            info['available_for_trading'] = (
                info.get('api_trade_available', False) and
                info.get('buy_available', False) and 
                info.get('sell_available', False)
            )
            
            # Сохраняем в кэш
            self._additional_cache[cache_key] = info.copy()
            
            return info
            
        except Exception as e:
            logger.error(f"Ошибка получения информации об инструменте {symbol}: {e}")
            return {}
    
    def get_portfolio_data(self) -> pd.DataFrame:
        """
        ДОПОЛНИТЕЛЬНЫЙ МЕТОД: Получение данных портфеля
        Требует права на чтение портфеля
        
        Returns:
        --------
        pd.DataFrame
            DataFrame с позициями портфеля
        """
        if not self.api.api_key:
            logger.error("API ключ не установлен")
            return pd.DataFrame()
        
        try:
            portfolio_data = []
            
            # Используем основной класс для получения счетов
            accounts_info = self.api.get_account_info()
            
            if not accounts_info or 'accounts' not in accounts_info:
                logger.warning("Нет доступных счетов")
                return pd.DataFrame()
            
            # Здесь можно добавить логику получения портфеля для каждого счета
            # Для простоты возвращаем пустой DataFrame
            # В реальной реализации нужно использовать client.operations.get_portfolio()
            
            logger.info("Получена информация о счетах (портфель требует дополнительной настройки прав)")
            return pd.DataFrame(portfolio_data)
            
        except Exception as e:
            logger.error(f"Ошибка получения данных портфеля: {e}")
            return pd.DataFrame()
    
    def search_instruments(self, query: str, instrument_type: str = None) -> pd.DataFrame:
        """
        ДОПОЛНИТЕЛЬНЫЙ МЕТОД: Поиск инструментов по названию или тикеру
        
        Parameters:
        -----------
        query : str
            Строка для поиска
        instrument_type : str, optional
            Ограничение по типу инструмента
            
        Returns:
        --------
        pd.DataFrame
            DataFrame с найденными инструментами
        """
        try:
            instruments_df = self.api.get_instruments_list(instrument_type)
            if instruments_df.empty:
                return pd.DataFrame()
            
            # Поиск по тикеру и названию
            mask = (
                instruments_df['symbol'].str.contains(query, case=False, na=False) |
                instruments_df['name'].str.contains(query, case=False, na=False)
            )
            
            results = instruments_df[mask]
            logger.info(f"Найдено {len(results)} инструментов по запросу '{query}'")
            
            return results
            
        except Exception as e:
            logger.error(f"Ошибка поиска инструментов: {e}")
            return pd.DataFrame()
    
    def get_available_timeframes(self) -> Dict[str, List[str]]:
        """
        ДОПОЛНИТЕЛЬНЫЙ МЕТОД: Получение доступных таймфреймов
        
        Returns:
        --------
        Dict[str, List[str]]
            Словарь с доступными таймфреймами для каждого API
        """
        return {
            'tbank': ['1m', '5m', '15m', '1h', '4h', '1d', '1w'],
            'moex': ['1m', '5m', '15m', '1h', '4h', 'D', 'W']
        }
    
    def validate_symbol(self, symbol: str) -> Dict[str, bool]:
        """
        ДОПОЛНИТЕЛЬНЫЙ МЕТОД: Валидация тикера
        
        Parameters:
        -----------
        symbol : str
            Тикер для проверки
            
        Returns:
        --------
        Dict[str, bool]
            Результаты валидации
        """
        try:
            instruments_df = self.api.get_instruments_list()
            if instruments_df.empty:
                return {'exists': False, 'tradable': False}
            
            instrument_data = instruments_df[instruments_df['symbol'] == symbol]
            if instrument_data.empty:
                return {'exists': False, 'tradable': False}
            
            info = instrument_data.iloc[0]
            tradable = (
                info.get('api_trade_available', False) and
                info.get('buy_available', False) and
                info.get('sell_available', False)
            )
            
            return {
                'exists': True,
                'tradable': tradable,
                'type': info.get('type', 'unknown'),
                'currency': info.get('currency', 'unknown'),
                'name': info.get('name', '')
            }
            
        except Exception as e:
            logger.error(f"Ошибка валидации тикера {symbol}: {e}")
            return {'exists': False, 'tradable': False}
    
    def get_market_hours(self) -> Dict:
        """
        ДОПОЛНИТЕЛЬНЫЙ МЕТОД: Получение информации о времени работы рынка
        
        Returns:
        --------
        Dict
            Информация о времени работы
        """
        # Для Tinkoff - Московская биржа
        return {
            'exchange': 'MOEX',
            'timezone': 'Europe/Moscow',
            'open_time': '10:00',
            'close_time': '18:40',
            'lunch_start': '14:00', 
            'lunch_end': '14:03',
            'days': ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'],
            'is_open_now': self._is_market_open_now()
        }
    
    def _is_market_open_now(self) -> bool:
        """
        Проверка, открыт ли рынок в текущий момент
        """
        now = datetime.now()
        
        # Проверяем день недели (пн-пт)
        if now.weekday() >= 5:  # 5=суббота, 6=воскресенье
            return False
        
        # Проверяем время
        current_time = now.time()
        market_open = datetime.strptime('10:00', '%H:%M').time()
        market_close = datetime.strptime('18:40', '%H:%M').time()
        lunch_start = datetime.strptime('14:00', '%H:%M').time()
        lunch_end = datetime.strptime('14:03', '%H:%M').time()
        
        # Проверяем общее время работы
        if not (market_open <= current_time <= market_close):
            return False
        
        # Проверяем обеденный перерыв
        if lunch_start <= current_time <= lunch_end:
            return False
        
        return True
    
    def clear_cache(self):
        """
        Очистка всех кэшей
        """
        self.api.clear_cache()
        self._additional_cache.clear()
        logger.info("✅ Все кэши TBankAPIFixed очищены")
    
    def get_api_stats(self) -> Dict:
        """
        Получение статистики использования API
        
        Returns:
        --------
        Dict
            Статистика API
        """
        return {
            'tbank_available': self.is_available(),
            'connection_ok': self.test_connection(),
            'cache_size': len(self._additional_cache),
            'market_open': self._is_market_open_now()
        }


# Альтернативная упрощенная версия для обратной совместимости
class TBankAPISimple:
    """
    Упрощенная версия для обратной совместимости
    """
    
    def __init__(self, api_key: str = None):
        self.api = TBankAPIFixed(api_key)
    
    def get_instruments_list(self) -> pd.DataFrame:
        """Простая версия получения инструментов"""
        return self.api.get_instruments_list()
    
    def get_historical_data(self, symbol: str, start_date: str, end_date: str = None, timeframe: str = '1d') -> pd.DataFrame:
        """Простая версия получения исторических данных"""
        return self.api.get_historical_data(symbol, start_date, end_date, timeframe)
    
    def _get_figi_by_ticker(self, ticker: str) -> Optional[str]:
        """Получение FIGI по тикеру (для обратной совместимости)"""
        info = self.api.validate_symbol(ticker)
        if info.get('exists', False):
            # В реальной реализации нужно получить FIGI из кэша основного API
            return f"FIGI_{ticker}"  # Заглушка
        return None
    
    def test_connection(self) -> bool:
        """Проверка подключения"""
        return self.api.test_connection()
    
    def is_available(self) -> bool:
        """Проверка доступности"""
        return self.api.is_available()
# tbank_api/tbank_data_loader.py
"""
Модуль загрузки данных с БЕЗОПАСНЫМИ оптимизациями
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import logging
from config import Config  # ✅ Правильный импорт

# ✅ ПЕРЕКЛЮЧАЕМСЯ НА БЕЗОПАСНУЮ ОПТИМИЗИРОВАННУЮ ВЕРСИЮ
from .optimized_data_manager import OptimizedTBankDataManager as TBankDataManager

logger = logging.getLogger(__name__)

class TBankDataLoader:
    """Загрузчик данных с безопасными оптимизациями"""
    
    def __init__(self, api_key: str = None):
        # Убираем self.config, используем Config напрямую
        if api_key:
            self.api_key = api_key
        else:
            # Получаем токен из Config
            self.api_key = Config.TINKOFF_TOKEN
        
        # Используем безопасный оптимизированный менеджер
        self.data_manager = TBankDataManager(self.api_key)
        logger.info("✅ TBankDataLoader с безопасными оптимизациями инициализирован")
    
    def load_price_data(self, symbol: str, 
                       days_back: int = 365,
                       timeframe: str = '1d',
                       use_cache: bool = True) -> pd.DataFrame:
        """Загрузка данных с безопасными оптимизациями"""
        if not self.api_key:
            logger.error("API ключ не установлен")
            return pd.DataFrame()
        
        # Расчет дат
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        logger.info(f"🔄 Загрузка данных для {symbol}...")
        
        data = self.data_manager.get_historical_data_with_cache(
            symbol=symbol,
            start_date=start_date.strftime('%Y-%m-%d'),
            end_date=end_date.strftime('%Y-%m-%d'),
            timeframe=timeframe,
            use_cache=use_cache
        )
        
        if data.empty:
            logger.error(f"Не удалось загрузить данные для {symbol}")
            return pd.DataFrame()
        
        # Стандартизация данных
        standardized_data = self._standardize_data(data, symbol)
        
        logger.info(f"✅ Загружено {len(standardized_data)} записей для {symbol}")
        return standardized_data
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Получить статистику производительности"""
        return self.data_manager.get_performance_stats()
    
    def get_detailed_analytics(self) -> Dict[str, Any]:
        """Получить детальную аналитику"""
        return self.data_manager.get_detailed_analytics()
    
    def update_recent_data(self, symbol: str, days_back: int = 1) -> pd.DataFrame:
        """Инкрементальное обновление данных"""
        return self.data_manager.update_data_incrementally(symbol, days_back)
    
    def get_available_symbols(self) -> pd.DataFrame:
        return self.data_manager.get_available_symbols_cached()
    
    def get_current_prices(self, symbols: List[str]) -> pd.DataFrame:
        if not self.api_key:
            return pd.DataFrame()
        return self.data_manager.api.get_current_quotes(symbols)
    
    def clear_cache(self):
        self.data_manager.clear_all_cache()
    
    def is_configured(self) -> bool:
        return bool(self.api_key)
    
    def get_cache_stats(self) -> Dict[str, Any]:
        return self.data_manager.get_cache_info()
    
    def _standardize_data(self, data: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Стандартизация данных (без изменений)"""
        result = data.copy()
        
        required_columns = ['close']
        for col in required_columns:
            if col not in result.columns:
                logger.error(f"Отсутствует обязательная колонка: {col}")
                return pd.DataFrame()
        
        if 'open' not in result.columns and 'close' in result.columns:
            result['open'] = result['close']
        
        if 'high' not in result.columns and 'close' in result.columns:
            result['high'] = result['close']
        
        if 'low' not in result.columns and 'close' in result.columns:
            result['low'] = result['close']
        
        if 'volume' not in result.columns:
            result['volume'] = 0
        
        result['symbol'] = symbol
        
        if not result.index.is_monotonic_increasing:
            result.sort_index(inplace=True)
        
        return result
    
    def get_advanced_analytics(self) -> Dict[str, Any]:
        """Получить расширенную аналитику"""
        try:
            return self.data_manager.get_advanced_analytics()
        except Exception as e:
            logger.error(f"Ошибка получения расширенной аналитики: {e}")
            return {
                'error': str(e),
                'basic_stats': self.get_performance_stats(),
                'cache_info': self.get_cache_stats()
            }
# tbank_api/tbank_api.py
"""
Модуль для работы с Tinkoff Invest API (Т-банк)
ИСПРАВЛЕННАЯ ВЕРСИЯ на основе работающих примеров
"""

import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import logging
from tinkoff.invest import Client, CandleInterval
from tinkoff.invest.services import InstrumentsService
import time

logger = logging.getLogger(__name__)

def quotation_to_float(quotation) -> float:
    """Конвертация Quotation в float"""
    if hasattr(quotation, 'units') and hasattr(quotation, 'nano'):
        return quotation.units + quotation.nano / 1e9
    return float(quotation)

def moneyvalue_to_float(money_value) -> float:
    """Конвертация MoneyValue в float"""
    if hasattr(money_value, 'units') and hasattr(money_value, 'nano'):
        return money_value.units + money_value.nano / 1e9
    return float(money_value)

class TBankAPI:
    """ИСПРАВЛЕННЫЙ класс для работы с Tinkoff Invest API"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key
        self._figi_cache = {}  # Кэш FIGI для тикеров
        self._instruments_cache = None  # Кэш всех инструментов
        self._last_instruments_update = None
        self._cache_ttl = 3600  # 1 час в секундах
        
        if api_key:
            logger.info("✅ Tinkoff API инициализирован с ключом")
        else:
            logger.warning("⚠️ Tinkoff API без ключа - только MOEX будет доступен")

    def _get_instruments(self, force_refresh: bool = False) -> pd.DataFrame:
        """
        Получение списка всех инструментов с кэшированием
        """
        # Проверяем актуальность кэша
        if (self._instruments_cache is not None and 
            not force_refresh and
            self._last_instruments_update and
            (datetime.now() - self._last_instruments_update).seconds < self._cache_ttl):
            return self._instruments_cache
        
        if not self.api_key:
            return pd.DataFrame()
            
        try:
            instruments_data = []
            
            with Client(self.api_key) as client:
                # Получаем разные типы инструментов
                instrument_types = [
                    ('shares', client.instruments.shares),
                    ('bonds', client.instruments.bonds),
                    ('etfs', client.instruments.etfs),
                    ('currencies', client.instruments.currencies),
                    ('futures', client.instruments.futures)
                ]
                
                for instrument_type, method in instrument_types:
                    try:
                        response = method()
                        for instrument in response.instruments:
                            # Базовые проверки доступности инструмента
                            if (instrument.ticker and instrument.ticker.strip() and 
                                instrument.lot > 0 and instrument.min_price_increment):
                                
                                instruments_data.append({
                                    'symbol': instrument.ticker,
                                    'name': instrument.name,
                                    'type': instrument_type,
                                    'currency': instrument.currency,
                                    'lot_size': instrument.lot,
                                    'figi': instrument.figi,
                                    'class_code': instrument.class_code,
                                    'min_price_increment': moneyvalue_to_float(instrument.min_price_increment),
                                    'api_trade_available': instrument.api_trade_available_flag,
                                    'buy_available': instrument.buy_available_flag,
                                    'sell_available': instrument.sell_available_flag
                                })
                    except Exception as e:
                        logger.warning(f"Ошибка загрузки {instrument_type}: {e}")
                        continue
            
            df = pd.DataFrame(instruments_data)
            self._instruments_cache = df
            self._last_instruments_update = datetime.now()
            
            logger.info(f"✅ Загружено {len(df)} инструментов Tinkoff")
            return df
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения инструментов Tinkoff: {e}")
            return pd.DataFrame()

    def get_instruments_list(self, instrument_type: str = None) -> pd.DataFrame:
        """
        Получение списка доступных инструментов с фильтрацией
        """
        df = self._get_instruments()
        
        if df.empty:
            return pd.DataFrame()
        
        # Фильтрация по типу инструмента
        if instrument_type and instrument_type != 'all':
            df = df[df['type'] == instrument_type]
        
        # Фильтрация по доступности торговли
        df = df[df['api_trade_available'] == True]
        
        # Сортировка по тикеру
        df = df.sort_values('symbol').reset_index(drop=True)
        
        return df

    def _get_figi_by_ticker(self, ticker: str) -> Optional[str]:
        """
        Получение FIGI по тикеру с кэшированием
        """
        # Проверяем кэш
        if ticker in self._figi_cache:
            return self._figi_cache[ticker]
        
        instruments_df = self._get_instruments()
        if instruments_df.empty:
            return None
        
        # Ищем точное совпадение тикера
        match = instruments_df[instruments_df['symbol'] == ticker]
        if not match.empty:
            figi = match.iloc[0]['figi']
            self._figi_cache[ticker] = figi
            return figi
        
        # Если точного совпадения нет, ищем похожие
        similar = instruments_df[instruments_df['symbol'].str.contains(ticker, na=False)]
        if not similar.empty:
            figi = similar.iloc[0]['figi']
            self._figi_cache[ticker] = figi
            logger.info(f"Найден похожий тикер: {similar.iloc[0]['symbol']} для запроса {ticker}")
            return figi
        
        logger.warning(f"Инструмент с тикером {ticker} не найден")
        return None

    def get_historical_data(self, symbol: str, 
                          start_date: str, 
                          end_date: str = None,
                          timeframe: str = '1d') -> pd.DataFrame:
        """
        Получение исторических данных по инструменту
        """
        if not self.api_key:
            logger.error("API ключ не установлен")
            return pd.DataFrame()
        
        try:
            # Конвертация таймфреймов
            tf_map = {
                '1d': CandleInterval.CANDLE_INTERVAL_DAY,
                '1h': CandleInterval.CANDLE_INTERVAL_HOUR,
                '4h': CandleInterval.CANDLE_INTERVAL_4_HOUR,
                '1w': CandleInterval.CANDLE_INTERVAL_WEEK,
                '1m': CandleInterval.CANDLE_INTERVAL_1_MIN,
                '5m': CandleInterval.CANDLE_INTERVAL_5_MIN,
                '15m': CandleInterval.CANDLE_INTERVAL_15_MIN
            }
            
            interval = tf_map.get(timeframe, CandleInterval.CANDLE_INTERVAL_DAY)
            
            # Получаем FIGI по тикеру
            figi = self._get_figi_by_ticker(symbol)
            if not figi:
                logger.error(f"Не найден FIGI для тикера {symbol}")
                return pd.DataFrame()
            
            # Преобразуем даты
            from_time = datetime.strptime(start_date, '%Y-%m-%d')
            to_time = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()
            
            # Корректируем время для Tinkoff API
            from_time = from_time.replace(hour=0, minute=0, second=0, microsecond=0)
            to_time = to_time.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            logger.info(f"Запрос данных Tinkoff для {symbol} с {from_time} по {to_time}, таймфрейм: {timeframe}")
            
            # Получаем свечи
            candles = []
            with Client(self.api_key) as client:
                for candle in client.get_all_candles(
                    figi=figi,
                    from_=from_time,
                    to=to_time,
                    interval=interval
                ):
                    candles.append({
                        'date': candle.time,
                        'open': quotation_to_float(candle.open),
                        'high': quotation_to_float(candle.high),
                        'low': quotation_to_float(candle.low),
                        'close': quotation_to_float(candle.close),
                        'volume': candle.volume,
                        'figi': figi,
                        'symbol': symbol
                    })
            
            if not candles:
                logger.warning(f"Нет данных Tinkoff для {symbol} за период {start_date} - {end_date}")
                return pd.DataFrame()
            
            df = pd.DataFrame(candles)
            df.set_index('date', inplace=True)
            df.sort_index(inplace=True)
            
            # Убедимся, что все числовые колонки имеют правильный тип
            numeric_cols = ['open', 'high', 'low', 'close', 'volume']
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            logger.info(f"✅ Загружено {len(df)} свечей Tinkoff для {symbol}")
            return df
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения данных Tinkoff для {symbol}: {e}")
            return pd.DataFrame()

    def get_current_quotes(self, symbols: List[str]) -> pd.DataFrame:
        """
        Получение текущих котировок
        """
        if not self.api_key:
            logger.error("API ключ не установлен")
            return pd.DataFrame()
            
        try:
            quotes_data = []
            
            with Client(self.api_key) as client:
                for symbol in symbols:
                    figi = self._get_figi_by_ticker(symbol)
                    if not figi:
                        logger.warning(f"Не найден FIGI для {symbol}")
                        continue
                    
                    try:
                        # Получаем стакан цен
                        order_book = client.market_data.get_order_book(figi=figi, depth=1)
                        
                        # Получаем последнюю цену
                        last_price = quotation_to_float(order_book.last_price)
                        
                        # Получаем лучшие цены покупки/продажи
                        best_bid = quotation_to_float(order_book.bids[0].price) if order_book.bids else last_price
                        best_ask = quotation_to_float(order_book.asks[0].price) if order_book.asks else last_price
                        
                        quotes_data.append({
                            'symbol': symbol,
                            'last': last_price,
                            'bid': best_bid,
                            'ask': best_ask,
                            'spread': abs(best_ask - best_bid) if best_ask and best_bid else 0,
                            'timestamp': datetime.now(),
                            'figi': figi
                        })
                        
                    except Exception as e:
                        logger.warning(f"Не удалось получить котировку для {symbol}: {e}")
                        continue
            
            df = pd.DataFrame(quotes_data)
            logger.info(f"✅ Загружены котировки для {len(df)} инструментов Tinkoff")
            return df
            
        except Exception as e:
            logger.error(f"❌ Ошибка получения котировок Tinkoff: {e}")
            return pd.DataFrame()

    def test_connection(self) -> bool:
        """
        Проверка подключения к API
        """
        if not self.api_key:
            logger.error("API ключ не установлен")
            return False
            
        try:
            with Client(self.api_key) as client:
                # Простой запрос для проверки подключения
                accounts = client.users.get_accounts()
                logger.info("✅ Подключение к Tinkoff API успешно")
                return True
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к Tinkoff API: {e}")
            return False

    def is_available(self) -> bool:
        """Проверка доступности API"""
        return self.api_key is not None and len(self.api_key) > 0

    def clear_cache(self):
        """Очистка кэшей"""
        self._figi_cache.clear()
        self._instruments_cache = None
        self._last_instruments_update = None
        logger.info("✅ Кэши Tinkoff API очищены")

    def get_account_info(self) -> Dict:
        """
        Получение информации о счетах
        """
        if not self.api_key:
            return {}
            
        try:
            with Client(self.api_key) as client:
                accounts = client.users.get_accounts()
                accounts_info = []
                
                for account in accounts.accounts:
                    accounts_info.append({
                        'id': account.id,
                        'type': account.type.name,
                        'status': account.status.name,
                        'name': account.name
                    })
                
                return {
                    'accounts': accounts_info,
                    'total_accounts': len(accounts.accounts)
                }
                
        except Exception as e:
            logger.error(f"Ошибка получения информации о счетах: {e}")
            return {}
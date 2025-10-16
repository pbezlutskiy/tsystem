# tbank_api/moex_api.py
"""
Модуль для работы с API Московской Биржи
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
from utils.error_handler import with_error_handling

logger = logging.getLogger(__name__)

class MoexAPI:
    """Класс для работы с API Московской Биржи"""
    
    def __init__(self):
        self.base_url = "https://iss.moex.com/iss"
        self.session = requests.Session()
        self._setup_session()
    
    def _setup_session(self):
        """Настройка HTTP сессии"""
        self.session.headers.update({
            'User-Agent': 'TradingSystem/1.0'
        })
    
    @with_error_handling
    def get_historical_data(self, symbol: str, 
                          start_date: str, 
                          end_date: str = None,
                          timeframe: str = 'D') -> pd.DataFrame:
        """
        Получение исторических данных по инструменту
        
        Parameters:
        -----------
        symbol : str
            Тикер инструмента (например: 'SBER', 'GAZP')
        start_date : str
            Начальная дата в формате 'YYYY-MM-DD'
        end_date : str, optional
            Конечная дата в формате 'YYYY-MM-DD'
        timeframe : str
            Таймфрейм данных ('D' - день, 'H1' - час, 'H4' - 4 часа, 'W' - неделя)
            
        Returns:
        --------
        pd.DataFrame
            Исторические данные
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')
        
        # Определяем рынок и борд
        market, board = self._detect_market_and_board(symbol)
        
        # Конвертация таймфреймов для МБ API
        interval_map = {
            'D': '24',    # День
            'H1': '60',   # 1 час
            'H4': '240',  # 4 часа
            'W': '7'      # Неделя
        }
        
        interval = interval_map.get(timeframe, '24')
        
        endpoint = f"{self.base_url}/engines/stock/markets/{market}/boards/{board}/securities/{symbol}/candles.json"
        
        params = {
            'from': start_date,
            'till': end_date,
            'interval': interval
        }
        
        try:
            logger.info(f"Запрос данных МБ для {symbol} ({timeframe}) с {start_date} по {end_date}")
            response = self.session.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            # Проверяем наличие данных
            if 'candles' not in data or 'data' not in data['candles']:
                logger.warning(f"Нет данных МБ для {symbol} за период {start_date} - {end_date}")
                return pd.DataFrame()
                
            candles = data['candles']['data']
            
            if not candles:
                logger.warning(f"Нет данных МБ для {symbol} за период {start_date} - {end_date}")
                return pd.DataFrame()
            
            # Создаем DataFrame
            columns = ['open', 'close', 'high', 'low', 'value', 'volume', 'begin', 'end']
            df = pd.DataFrame(candles, columns=columns)
            
            # Преобразуем даты
            df['date'] = pd.to_datetime(df['begin'])
            df.set_index('date', inplace=True)
            
            # Стандартизируем колонки
            result_df = pd.DataFrame({
                'open': df['open'],
                'high': df['high'],
                'low': df['low'],
                'close': df['close'],
                'volume': df['volume']
            })
            
            # Обработка пропусков для часовых данных
            if timeframe in ['H1', 'H4']:
                result_df = self._fill_missing_data(result_df, timeframe)
            
            logger.info(f"Загружено {len(result_df)} свечей МБ для {symbol} (таймфрейм: {timeframe})")
            return result_df
            
        except Exception as e:
            logger.error(f"Ошибка получения данных МБ для {symbol}: {e}")
            return pd.DataFrame()
    
    def _fill_missing_data(self, data: pd.DataFrame, timeframe: str) -> pd.DataFrame:
        """
        Заполнение пропущенных данных для внутридневных таймфреймов
        
        Parameters:
        -----------
        data : pd.DataFrame
            Исходные данные
        timeframe : str
            Таймфрейм данных
            
        Returns:
        --------
        pd.DataFrame
            Данные с заполненными пропусками
        """
        if data.empty:
            return data
        
        # Определяем частоту
        freq_map = {'H1': '1H', 'H4': '4H', 'D': '1D'}
        freq = freq_map.get(timeframe, '1H')
        
        # Создаем полный временной ряд (только в рабочие часы)
        if timeframe in ['H1', 'H4']:
            # Для внутридневных данных - только торговые часы (10:00-18:45 МСК)
            start_time = pd.Timestamp(data.index.min().date()) + pd.Timedelta(hours=7)  # 10:00 МСК = 7:00 UTC
            end_time = pd.Timestamp(data.index.min().date()) + pd.Timedelta(hours=15, minutes=45)  # 18:45 МСК = 15:45 UTC
            full_index = pd.date_range(start=start_time, end=end_time, freq=freq)
        else:
            full_index = pd.date_range(start=data.index.min(), end=data.index.max(), freq=freq)
        
        # Реиндексируем данные
        result = data.reindex(full_index)
        
        # Заполняем пропущенные значения (forward fill для OHLC, 0 для объема)
        result[['open', 'high', 'low', 'close']] = result[['open', 'high', 'low', 'close']].ffill()
        result['volume'] = result['volume'].fillna(0)
        
        # Удаляем строки где все значения NaN (в начале ряда)
        result = result.dropna(subset=['open', 'high', 'low', 'close'])
        
        return result
    
    @with_error_handling
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
            Текущие котировки
        """
        quotes_data = []
        
        for symbol in symbols:
            try:
                market, board = self._detect_market_and_board(symbol)
                endpoint = f"{self.base_url}/engines/stock/markets/{market}/boards/{board}/securities/{symbol}.json"
                
                response = self.session.get(endpoint, timeout=10)
                response.raise_for_status()
                
                data = response.json()
                
                if 'marketdata' not in data or 'data' not in data['marketdata']:
                    continue
                    
                market_data = data['marketdata']['data']
                
                if market_data:
                    quote = market_data[0]
                    # Безопасное извлечение данных (индексы могут отличаться)
                    last_price = quote[12] if len(quote) > 12 and quote[12] else (quote[4] if len(quote) > 4 else 0)
                    change = quote[13] if len(quote) > 13 and quote[13] else 0
                    volume = quote[27] if len(quote) > 27 and quote[27] else 0
                    
                    quotes_data.append({
                        'symbol': symbol,
                        'last': last_price,
                        'change': change,
                        'volume': volume,
                        'timestamp': datetime.now()
                    })
                    
            except Exception as e:
                logger.error(f"Ошибка получения котировки МБ для {symbol}: {e}")
                continue
        
        return pd.DataFrame(quotes_data)
    
    @with_error_handling
    def get_instruments_list(self, market: str = 'shares') -> pd.DataFrame:
        """
        Получение списка инструментов
        
        Parameters:
        -----------
        market : str
            Рынок ('shares' - акции, 'bonds' - облигации, 'futures' - фьючерсы)
            
        Returns:
        --------
        pd.DataFrame
            Список инструментов
        """
        # Определяем борд для рынка
        board_map = {
            'shares': 'TQBR',
            'bonds': 'TQOB', 
            'futures': 'RFUD',
            'index': 'SNDX'
        }
        
        board = board_map.get(market, 'TQBR')
        endpoint = f"{self.base_url}/engines/stock/markets/{market}/boards/{board}/securities.json"
        
        try:
            response = self.session.get(endpoint, params={'limit': 500}, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            if 'securities' not in data or 'data' not in data['securities']:
                logger.warning(f"Нет данных по инструментам для рынка {market}")
                return pd.DataFrame()
                
            securities = data['securities']['data']
            columns = data['securities']['columns']
            
            df = pd.DataFrame(securities, columns=columns)
            
            if df.empty:
                return pd.DataFrame()
            
            # Безопасное создание результата
            result_data = []
            
            for _, row in df.iterrows():
                instrument = {'symbol': row['SECID'] if 'SECID' in row.index else ''}
                
                # Добавляем доступные колонки
                if 'SHORTNAME' in row.index:
                    instrument['name'] = row['SHORTNAME']
                elif 'SECNAME' in row.index:
                    instrument['name'] = row['SECNAME']
                else:
                    instrument['name'] = instrument['symbol']
                
                if 'LOTSIZE' in row.index:
                    instrument['lot_size'] = row['LOTSIZE']
                else:
                    instrument['lot_size'] = 1
                
                if 'CURRENCY' in row.index:
                    instrument['currency'] = row['CURRENCY']
                else:
                    instrument['currency'] = 'RUB'
                
                instrument['type'] = market
                
                # Фильтруем только активные инструменты
                if 'STATUS' in row.index and row['STATUS'] != 'A':
                    continue
                    
                result_data.append(instrument)
            
            result_df = pd.DataFrame(result_data)
            
            logger.info(f"Загружено {len(result_df)} инструментов МБ (рынок: {market})")
            return result_df
            
        except Exception as e:
            logger.error(f"Ошибка получения списка инструментов МБ: {e}")
            return pd.DataFrame()
    
    def get_available_markets(self) -> List[Dict]:
        """
        Получение списка доступных рынков
        
        Returns:
        --------
        List[Dict]
            Список рынков
        """
        markets = [
            {'code': 'shares', 'name': 'Акции', 'description': 'Основной рынок акций'},
            {'code': 'bonds', 'name': 'Облигации', 'description': 'Облигации федерального займа'},
            {'code': 'futures', 'name': 'Фьючерсы', 'description': 'Срочный рынок'},
            {'code': 'index', 'name': 'Индексы', 'description': 'Фондовые индексы'}
        ]
        return markets
    
    def _detect_market_and_board(self, symbol: str) -> tuple:
        """
        Определение рынка и борда по тикеру
        
        Parameters:
        -----------
        symbol : str
            Тикер инструмента
            
        Returns:
        --------
        tuple
            (рынок, борд)
        """
        # Для акций
        stock_symbols = ['SBER', 'GAZP', 'LKOH', 'ROSN', 'VTBR', 'YNDX', 'GMKN', 'NVTK', 'TATN', 'MTSS']
        if symbol in stock_symbols:
            return 'shares', 'TQBR'
        
        # Для фьючерсов
        futures_symbols = ['Si', 'RI', 'BR', 'GZ', 'GD']
        if any(symbol.startswith(prefix) for prefix in futures_symbols):
            return 'futures', 'RFUD'
        
        # Для индексов
        index_symbols = ['IMOEX', 'RTSI', 'RGBI']
        if symbol in index_symbols:
            return 'index', 'SNDX'
        
        # По умолчанию - акции основного рынка
        return 'shares', 'TQBR'
    
    @with_error_handling
    def test_connection(self) -> bool:
        """
        Проверка подключения к API МБ
        
        Returns:
        --------
        bool
            True если подключение успешно
        """
        try:
            endpoint = f"{self.base_url}/engines.json"
            response = self.session.get(endpoint, timeout=10)
            return response.status_code == 200
        except:
            return False
import os
from datetime import datetime, timedelta
from tinkoff.invest import Client, InstrumentStatus, InstrumentIdType
import pandas as pd


class InstrumentService:
    """Сервис для работы со справочной информацией об инструментах Tinkoff Invest API"""
    
    def __init__(self, token=None):
        """
        Инициализация сервиса
        
        Args:
            token (str): Токен Tinkoff Invest API. Если None, будет использован из config.py
        """
        self.token = token
    
    def _get_client(self):
        """Создает новый клиент для каждого запроса"""
        return Client(self.token)
    
    def get_all_shares(self, instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE):
        """
        Получение списка всех акций
        
        Args:
            instrument_status: Статус инструмента (базовый, все и т.д.)
            
        Returns:
            list: Список объектов акций
        """
        with self._get_client() as client:
            instruments_service = client.instruments
            shares = instruments_service.shares(
                instrument_status=instrument_status
            ).instruments
            return shares
    
    def get_all_etfs(self, instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE):
        """
        Получение списка всех ETF
        
        Args:
            instrument_status: Статус инструмента
            
        Returns:
            list: Список объектов ETF
        """
        with self._get_client() as client:
            instruments_service = client.instruments
            etfs = instruments_service.etfs(
                instrument_status=instrument_status
            ).instruments
            return etfs
    
    def get_all_bonds(self, instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE):
        """
        Получение списка всех облигаций
        
        Args:
            instrument_status: Статус инструмента
            
        Returns:
            list: Список объектов облигаций
        """
        with self._get_client() as client:
            instruments_service = client.instruments
            bonds = instruments_service.bonds(
                instrument_status=instrument_status
            ).instruments
            return bonds
    
    def get_all_currencies(self, instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE):
        """
        Получение списка всех валют
        
        Args:
            instrument_status: Статус инструмента
            
        Returns:
            list: Список объектов валют
        """
        with self._get_client() as client:
            instruments_service = client.instruments
            currencies = instruments_service.currencies(
                instrument_status=instrument_status
            ).instruments
            return currencies
    
    def get_all_futures(self, instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE):
        """
        Получение списка всех фьючерсов
        
        Args:
            instrument_status: Статус инструмента
            
        Returns:
            list: Список объектов фьючерсов
        """
        with self._get_client() as client:
            instruments_service = client.instruments
            futures = instruments_service.futures(
                instrument_status=instrument_status
            ).instruments
            return futures
    
    def find_instrument(self, query):
        """
        Поиск инструмента по названию, тикеру, ISIN и т.д.
        
        Args:
            query (str): Строка для поиска
            
        Returns:
            list: Список найденных инструментов
        """
        with self._get_client() as client:
            instruments_service = client.instruments
            result = instruments_service.find_instrument(query=query)
            
            # Фильтруем только валидные инструменты с FIGI
            valid_instruments = []
            for instrument in result.instruments:
                if hasattr(instrument, 'figi') and instrument.figi:
                    valid_instruments.append(instrument)
            
            return valid_instruments
    
    def get_instrument_by_figi(self, figi):
        """
        Получение инструмента по FIGI
        
        Args:
            figi (str): FIGI инструмента
            
        Returns:
            object: Объект инструмента
        """
        with self._get_client() as client:
            instruments_service = client.instruments
            instrument = instruments_service.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
                id=figi
            )
            return instrument
    
    def get_instrument_by_ticker(self, ticker, class_code=''):
        """
        Получение инструмента по тикеру и класс-коду
        
        Args:
            ticker (str): Тикер инструмента
            class_code (str): Класс-код инструмента
            
        Returns:
            object: Объект инструмента
        """
        with self._get_client() as client:
            instruments_service = client.instruments
            instrument = instruments_service.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_TICKER,
                class_code=class_code,
                id=ticker
            )
            return instrument
    
    def get_trading_schedules(self, exchange=None, from_date=None, to_date=None):
        """
        Получение расписания торгов
        
        Args:
            exchange (str): Биржа (опционально)
            from_date (datetime): Начальная дата
            to_date (datetime): Конечная дата
            
        Returns:
            object: Расписание торгов
        """
        with self._get_client() as client:
            if from_date is None:
                from_date = datetime.utcnow()
            if to_date is None:
                to_date = from_date + timedelta(days=7)
            
            schedules = client.instruments.trading_schedules(
                exchange=exchange,
                from_=from_date,
                to=to_date
            )
            return schedules
    
    def get_dividends(self, figi, from_date, to_date):
        """
        Получение информации о дивидендах
        
        Args:
            figi (str): FIGI инструмента
            from_date (datetime): Начальная дата
            to_date (datetime): Конечная дата
            
        Returns:
            object: Информация о дивидендах
        """
        with self._get_client() as client:
            dividends = client.instruments.get_dividends(
                figi=figi,
                from_=from_date,
                to=to_date
            )
            return dividends
    
    def get_accrued_interests(self, figi, from_date, to_date):
        """
        Получение графика выплаты купонов по облигации
        
        Args:
            figi (str): FIGI облигации
            from_date (datetime): Начальная дата
            to_date (datetime): Конечная дата
            
        Returns:
            object: График выплат купонов
        """
        with self._get_client() as client:
            accrued_interests = client.instruments.get_accrued_interests(
                figi=figi,
                from_=from_date,
                to=to_date
            )
            return accrued_interests
    
    def get_futures_margin(self, figi):
        """
        Получение размера гарантийного обеспечения по фьючерсу
        
        Args:
            figi (str): FIGI фьючерса
            
        Returns:
            object: Информация о гарантийном обеспечении
        """
        with self._get_client() as client:
            margin = client.instruments.get_futures_margin(figi=figi)
            return margin
    
    # Методы для конвертации в DataFrame
    def shares_to_dataframe(self, filter_russian=True):
        """
        Конвертация списка акций в DataFrame
        
        Args:
            filter_russian (bool): Фильтровать только российские акции
            
        Returns:
            pd.DataFrame: DataFrame с акциями
        """
        try:
            shares = self.get_all_shares()
            data = []
            
            for share in shares:
                if filter_russian:
                    # Фильтруем только российские акции
                    if share.currency == 'rub' and getattr(share, 'country_of_risk', '') == 'RU':
                        data.append(self._share_to_dict(share))
                else:
                    data.append(self._share_to_dict(share))
            
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Ошибка при получении акций: {e}")
            return pd.DataFrame()
    
    def etfs_to_dataframe(self, filter_russian=True):
        """
        Конвертация списка ETF в DataFrame
        
        Args:
            filter_russian (bool): Фильтровать только российские ETF
            
        Returns:
            pd.DataFrame: DataFrame с ETF
        """
        try:
            etfs = self.get_all_etfs()
            data = []
            
            for etf in etfs:
                if filter_russian:
                    if etf.currency == 'rub':
                        data.append(self._etf_to_dict(etf))
                else:
                    data.append(self._etf_to_dict(etf))
            
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Ошибка при получении ETF: {e}")
            return pd.DataFrame()
    
    def bonds_to_dataframe(self, filter_russian=True):
        """
        Конвертация списка облигаций в DataFrame
        
        Args:
            filter_russian (bool): Фильтровать только российские облигации
            
        Returns:
            pd.DataFrame: DataFrame с облигациями
        """
        try:
            bonds = self.get_all_bonds()
            data = []
            
            for bond in bonds:
                if filter_russian:
                    if bond.currency == 'rub' and getattr(bond, 'country_of_risk', '') == 'RU':
                        data.append(self._bond_to_dict(bond))
                else:
                    data.append(self._bond_to_dict(bond))
            
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Ошибка при получении облигаций: {e}")
            return pd.DataFrame()
    
    def currencies_to_dataframe(self):
        """
        Конвертация списка валют в DataFrame
        
        Returns:
            pd.DataFrame: DataFrame с валютами
        """
        try:
            currencies = self.get_all_currencies()
            data = []
            
            for currency in currencies:
                data.append(self._currency_to_dict(currency))
            
            return pd.DataFrame(data)
        except Exception as e:
            print(f"Ошибка при получении валют: {e}")
            return pd.DataFrame()
    
    # Вспомогательные методы для преобразования в словари
    def _share_to_dict(self, share):
        """Преобразование акции в словарь"""
        return {
            'FIGI': share.figi,
            'Ticker': share.ticker,
            'Name': share.name,
            'Currency': share.currency,
            'Lot': share.lot,
            'Min Price Increment': float(f"{share.min_price_increment.units}.{share.min_price_increment.nano:09d}"),
            'API Trade Available': share.api_trade_available_flag,
            'Buy Available': share.buy_available_flag,
            'Sell Available': share.sell_available_flag,
            'Exchange': share.exchange,
            'Sector': getattr(share, 'sector', ''),
            'Country': getattr(share, 'country_of_risk', ''),
            'Class Code': share.class_code,
            'Instrument Type': 'Акция'
        }
    
    def _etf_to_dict(self, etf):
        """Преобразование ETF в словарь"""
        return {
            'FIGI': etf.figi,
            'Ticker': etf.ticker,
            'Name': etf.name,
            'Currency': etf.currency,
            'Lot': etf.lot,
            'Min Price Increment': float(f"{etf.min_price_increment.units}.{etf.min_price_increment.nano:09d}"),
            'API Trade Available': etf.api_trade_available_flag,
            'Buy Available': etf.buy_available_flag,
            'Sell Available': etf.sell_available_flag,
            'Exchange': etf.exchange,
            'Fixed Commission': getattr(etf, 'fixed_commission_flag', False),
            'Focus Type': getattr(etf, 'focus_type', ''),
            'Class Code': etf.class_code,
            'Instrument Type': 'ETF'
        }
    
    def _bond_to_dict(self, bond):
        """Преобразование облигации в словарь"""
        return {
            'FIGI': bond.figi,
            'Ticker': bond.ticker,
            'Name': bond.name,
            'Currency': bond.currency,
            'Lot': bond.lot,
            'Min Price Increment': float(f"{bond.min_price_increment.units}.{bond.min_price_increment.nano:09d}"),
            'API Trade Available': bond.api_trade_available_flag,
            'Buy Available': bond.buy_available_flag,
            'Sell Available': bond.sell_available_flag,
            'Exchange': bond.exchange,
            'Country': getattr(bond, 'country_of_risk', ''),
            'Nominal': float(f"{bond.nominal.units}.{bond.nominal.nano:09d}"),
            'Aci Value': float(f"{bond.aci_value.units}.{bond.aci_value.nano:09d}"),
            'Class Code': bond.class_code,
            'Instrument Type': 'Облигация'
        }
    
    def _currency_to_dict(self, currency):
        """Преобразование валюты в словарь"""
        return {
            'FIGI': currency.figi,
            'Ticker': currency.ticker,
            'Name': currency.name,
            'Currency': currency.currency,
            'Lot': currency.lot,
            'Min Price Increment': float(f"{currency.min_price_increment.units}.{currency.min_price_increment.nano:09d}"),
            'API Trade Available': currency.api_trade_available_flag,
            'Buy Available': currency.buy_available_flag,
            'Sell Available': currency.sell_available_flag,
            'Exchange': currency.exchange,
            'Class Code': currency.class_code,
            'Instrument Type': 'Валюта'
        }
    
    # Утилитные методы
    def get_popular_russian_shares(self):
        """Получение популярных российских акций"""
        shares_df = self.shares_to_dataframe()
        
        popular_tickers = ['SBER', 'GAZP', 'LKOH', 'ROSN', 'YNDX', 'VTBR', 'TATN', 
                          'GMKN', 'PLZL', 'NLMK', 'POLY', 'AFKS', 'PHOR', 'MTSS',
                          'MGNT', 'RTKM', 'MOEX', 'ALRS', 'CHMF', 'RUAL']
        
        popular_shares = shares_df[shares_df['Ticker'].isin(popular_tickers)]
        return popular_shares.sort_values('Ticker')
    
    def search_instruments(self, query, instrument_type='all'):
        """
        Умный поиск инструментов с фильтрацией по типу
        
        Args:
            query (str): Строка для поиска
            instrument_type (str): Тип инструмента ('all', 'share', 'etf', 'bond', 'currency')
            
        Returns:
            pd.DataFrame: DataFrame с результатами поиска
        """
        instruments = self.find_instrument(query)
        
        if instrument_type != 'all':
            instruments = [i for i in instruments if i.instrument_type == instrument_type]
        
        data = []
        for instrument in instruments:
            data.append({
                'FIGI': instrument.figi,
                'Ticker': instrument.ticker,
                'Name': instrument.name,
                'Currency': getattr(instrument, 'currency', ''),
                'Instrument Type': instrument.instrument_type,
                'API Trade Available': getattr(instrument, 'api_trade_available_flag', False),
                'Exchange': getattr(instrument, 'exchange', '')
            })
        
        return pd.DataFrame(data)


# Пример использования
if __name__ == "__main__":
    # Токен для тестирования
    TOKEN = "t.8HbNCn4L0U9uBmMa5oloBrXCKxnqsTYNVK3f9iJOwDBiQ2lva9kvQ3C-MLgEESHl65ma1q0k0P6aMfS_O_co4g"
    
    service = InstrumentService(TOKEN)
    
    print("🔧 Тестирование InstrumentService...")
    
    # Тест получения популярных акций
    popular_shares = service.get_popular_russian_shares()
    print(f"📈 Популярные российские акции: {len(popular_shares)}")
    print(popular_shares[['Ticker', 'Name']].head(10))
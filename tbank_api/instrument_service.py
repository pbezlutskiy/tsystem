"""
Правильный сервис инструментов Tinkoff Invest API
"""
import pandas as pd
from datetime import datetime, timedelta
from tinkoff.invest import Client, InstrumentStatus, InstrumentIdType


class InstrumentService:
    """Сервис для работы со справочной информацией об инструментах"""
    
    def __init__(self, token=None):
        self.token = token
    
    def _get_client(self):
        """Создает клиент для запросов"""
        return Client(self.token)
    
    def get_all_shares(self):
        """Получение всех акций"""
        with self._get_client() as client:
            response = client.instruments.shares()
            return response.instruments
    
    def get_all_etfs(self):
        """Получение всех ETF"""
        with self._get_client() as client:
            response = client.instruments.etfs()
            return response.instruments
    
    def get_all_bonds(self):
        """Получение всех облигаций"""
        with self._get_client() as client:
            response = client.instruments.bonds()
            return response.instruments
    
    def get_all_currencies(self):
        """Получение всех валют"""
        with self._get_client() as client:
            response = client.instruments.currencies()
            return response.instruments
    
    def find_instrument(self, query):
        """Поиск инструментов"""
        with self._get_client() as client:
            response = client.instruments.find_instrument(query=query)
            return response.instruments
    
    def get_instrument_by_figi(self, figi):
        """Получение инструмента по FIGI"""
        with self._get_client() as client:
            instrument = client.instruments.get_instrument_by(
                id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
                id=figi
            )
            return instrument
    
    def get_popular_russian_shares(self):
        """Получение популярных российских акций"""
        try:
            shares = self.get_all_shares()
            data = []
            
            popular_tickers = ['SBER', 'GAZP', 'LKOH', 'ROSN', 'YNDX', 'VTBR', 'TATN', 
                             'GMKN', 'PLZL', 'NLMK', 'POLY', 'AFKS', 'PHOR', 'MTSS']
            
            for share in shares:
                if (hasattr(share, 'ticker') and share.ticker in popular_tickers and
                    hasattr(share, 'currency') and share.currency == 'rub' and
                    hasattr(share, 'country_of_risk') and share.country_of_risk == 'RU'):
                    
                    data.append({
                        'FIGI': share.figi,
                        'Ticker': share.ticker,
                        'Name': share.name,
                        'Currency': share.currency,
                        'Lot': share.lot,
                        'Exchange': share.exchange,
                        'Sector': getattr(share, 'sector', ''),
                        'Country': share.country_of_risk,
                    })
            
            # Сортируем по порядку популярных тикеров
            df = pd.DataFrame(data)
            df['SortOrder'] = df['Ticker'].apply(lambda x: popular_tickers.index(x) if x in popular_tickers else 999)
            df = df.sort_values('SortOrder').drop('SortOrder', axis=1)
            
            return df
            
        except Exception as e:
            print(f"❌ Ошибка получения популярных акций: {e}")
            return self._get_fallback_data()
    
    def search_instruments_dataframe(self, query):
        """Поиск инструментов с возвратом DataFrame"""
        try:
            instruments = self.find_instrument(query)
            data = []
            
            for instrument in instruments:
                if hasattr(instrument, 'ticker') and instrument.ticker:
                    data.append({
                        'FIGI': instrument.figi,
                        'Ticker': instrument.ticker,
                        'Name': instrument.name,
                        'Type': getattr(instrument, 'instrument_type', ''),
                        'Currency': getattr(instrument, 'currency', ''),
                        'Lot': getattr(instrument, 'lot', 1),
                        'Exchange': getattr(instrument, 'exchange', ''),
                        'API Trade Available': getattr(instrument, 'api_trade_available_flag', False)
                    })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"❌ Ошибка поиска '{query}': {e}")
            return pd.DataFrame()
    
    def get_instruments_dataframe(self, instrument_type='shares'):
        """Получение инструментов в виде DataFrame"""
        try:
            if instrument_type == 'shares':
                instruments = self.get_all_shares()
            elif instrument_type == 'etfs':
                instruments = self.get_all_etfs()
            elif instrument_type == 'bonds':
                instruments = self.get_all_bonds()
            elif instrument_type == 'currencies':
                instruments = self.get_all_currencies()
            else:
                return pd.DataFrame()
            
            data = []
            for instrument in instruments:
                if hasattr(instrument, 'ticker') and instrument.ticker:
                    data.append({
                        'FIGI': instrument.figi,
                        'Ticker': instrument.ticker,
                        'Name': instrument.name,
                        'Type': instrument_type,
                        'Currency': getattr(instrument, 'currency', ''),
                        'Lot': getattr(instrument, 'lot', 1),
                        'Exchange': getattr(instrument, 'exchange', ''),
                        'Country': getattr(instrument, 'country_of_risk', ''),
                        'API Trade Available': getattr(instrument, 'api_trade_available_flag', False)
                    })
            
            return pd.DataFrame(data)
            
        except Exception as e:
            print(f"❌ Ошибка получения {instrument_type}: {e}")
            return pd.DataFrame()
    
    def _get_fallback_data(self):
        """Резервные данные"""
        return pd.DataFrame([
            {'Ticker': 'SBER', 'Name': 'Сбер Банк', 'Currency': 'rub', 'Lot': 1, 'FIGI': 'BBG004730N88'},
            {'Ticker': 'GAZP', 'Name': 'Газпром', 'Currency': 'rub', 'Lot': 10, 'FIGI': 'BBG004730RP0'},
            {'Ticker': 'LKOH', 'Name': 'ЛУКОЙЛ', 'Currency': 'rub', 'Lot': 1, 'FIGI': 'BBG004731032'},
            {'Ticker': 'ROSN', 'Name': 'Роснефть', 'Currency': 'rub', 'Lot': 10, 'FIGI': 'BBG004731354'},
            {'Ticker': 'YNDX', 'Name': 'Яндекс', 'Currency': 'rub', 'Lot': 1, 'FIGI': 'BBG006L8G4H1'},
        ])

    def get_trading_schedules(self, exchange='', from_date=None, to_date=None):
        """Получение расписания торгов"""
        try:
            with self._get_client() as client:
                if from_date is None:
                    from datetime import datetime, UTC
                    from_date = datetime.now(UTC)
                if to_date is None:
                    to_date = from_date.replace(hour=23, minute=59, second=59)
                
                schedules = client.instruments.trading_schedules(
                    exchange=exchange,
                    from_=from_date,
                    to=to_date
                )
                return schedules
        except Exception as e:
            print(f"❌ Ошибка получения расписания торгов: {e}")
            return None

    def get_dividends(self, figi, from_date, to_date):
        """Получение информации о дивидендах"""
        try:
            with self._get_client() as client:
                dividends = client.instruments.get_dividends(
                    figi=figi,
                    from_=from_date,
                    to=to_date
                )
                return dividends
        except Exception as e:
            print(f"❌ Ошибка получения дивидендов: {e}")
            return None

    def get_accrued_interests(self, figi, from_date, to_date):
        """Получение графика выплаты купонов по облигации"""
        try:
            with self._get_client() as client:
                accrued_interests = client.instruments.get_accrued_interests(
                    figi=figi,
                    from_=from_date,
                    to=to_date
                )
                return accrued_interests
        except Exception as e:
            print(f"❌ Ошибка получения купонов: {e}")
            return None

    def get_futures_margin(self, figi):
        """Получение размера гарантийного обеспечения по фьючерсу"""
        try:
            with self._get_client() as client:
                margin = client.instruments.get_futures_margin(figi=figi)
                return margin
        except Exception as e:
            print(f"❌ Ошибка получения маржи: {e}")
            return None
# Тестирование
if __name__ == "__main__":
    TOKEN = "t.8HbNCn4L0U9uBmMa5oloBrXCKxnqsTYNVK3f9iJOwDBiQ2lva9kvQ3C-MLgEESHl65ma1q0k0P6aMfS_O_co4g"
    
    service = InstrumentService(TOKEN)
    
    print("🚀 Тестирование InstrumentService...")
    
    # Тест популярных акций
    popular = service.get_popular_russian_shares()
    print(f"📈 Популярные акции: {len(popular)}")
    print(popular[['Ticker', 'Name', 'Lot']].head())
    
    # Тест поиска
    search = service.search_instruments_dataframe("GAZP")
    print(f"🔍 Поиск GAZP: {len(search)} результатов")
import os
from datetime import datetime, timedelta, UTC
from tinkoff.invest import Client, InstrumentStatus, InstrumentIdType
import pandas as pd


class InstrumentServiceWorking:
    """Рабочий сервис инструментов - использует только работающие методы"""
    
    def __init__(self, token=None):
        self.token = token
    
    def _get_client(self):
        return Client(self.token)
    
    def get_popular_russian_shares_working(self):
        """Получение популярных российских акций через поиск"""
        try:
            popular_tickers = ['SBER', 'GAZP', 'LKOH', 'ROSN', 'YNDX', 'VTBR', 'TATN', 
                              'GMKN', 'PLZL', 'NLMK', 'POLY', 'AFKS', 'PHOR', 'MTSS']
            
            all_results = []
            
            for ticker in popular_tickers:
                try:
                    results = self.search_instruments_working(ticker)
                    # Фильтруем только акции с правильным тикером
                    shares = results[results['Ticker'] == ticker]
                    if not shares.empty:
                        all_results.append(shares.iloc[0])  # Берем первый результат
                except Exception as e:
                    print(f"⚠️ Ошибка поиска {ticker}: {e}")
                    continue
            
            if all_results:
                return pd.DataFrame(all_results)
            else:
                # Возвращаем тестовые данные если поиск не сработал
                return self._get_fallback_data()
                
        except Exception as e:
            print(f"❌ Ошибка получения популярных акций: {e}")
            return self._get_fallback_data()
    
    def search_instruments_working(self, query):
        """Рабочий поиск инструментов"""
        try:
            with self._get_client() as client:
                result = client.instruments.find_instrument(query=query)
                
                instruments_data = []
                for instrument in result.instruments:
                    try:
                        # Безопасное получение атрибутов
                        ticker = getattr(instrument, 'ticker', '')
                        name = getattr(instrument, 'name', '')
                        instrument_type = getattr(instrument, 'instrument_type', '')
                        currency = getattr(instrument, 'currency', '')
                        figi = getattr(instrument, 'figi', '')
                        lot = getattr(instrument, 'lot', 1)
                        exchange = getattr(instrument, 'exchange', '')
                        
                        if ticker:  # Только инструменты с тикером
                            instruments_data.append({
                                'Ticker': ticker,
                                'Name': name,
                                'Type': instrument_type,
                                'Currency': currency,
                                'FIGI': figi,
                                'Lot': lot,
                                'Exchange': exchange,
                                'API Trade Available': getattr(instrument, 'api_trade_available_flag', False)
                            })
                    except Exception as e:
                        continue
                
                return pd.DataFrame(instruments_data)
                
        except Exception as e:
            print(f"❌ Ошибка поиска '{query}': {e}")
            return pd.DataFrame()
    
    def get_instrument_by_figi_working(self, figi):
        """Получение инструмента по FIGI"""
        try:
            with self._get_client() as client:
                instrument = client.instruments.get_instrument_by(
                    id_type=InstrumentIdType.INSTRUMENT_ID_TYPE_FIGI,
                    id=figi
                )
                return instrument
        except Exception as e:
            print(f"❌ Ошибка получения инструмента {figi}: {e}")
            return None
    
    def get_trading_schedules_working(self):
        """Получение расписания торгов"""
        try:
            with self._get_client() as client:
                from_date = datetime.now(UTC)
                to_date = from_date + timedelta(days=1)
                
                schedules = client.instruments.trading_schedules(
                    exchange='',
                    from_=from_date,
                    to=to_date
                )
                return schedules
        except Exception as e:
            print(f"❌ Ошибка получения расписания: {e}")
            return None
    
    def _get_fallback_data(self):
        """Резервные данные если API не работает"""
        return pd.DataFrame([
            {'Ticker': 'SBER', 'Name': 'Сбер Банк', 'Type': 'share', 'Currency': 'rub', 'Lot': 1, 'Exchange': 'MOEX', 'FIGI': 'BBG004730N88'},
            {'Ticker': 'GAZP', 'Name': 'Газпром', 'Type': 'share', 'Currency': 'rub', 'Lot': 10, 'Exchange': 'MOEX', 'FIGI': 'BBG004730RP0'},
            {'Ticker': 'LKOH', 'Name': 'ЛУКОЙЛ', 'Type': 'share', 'Currency': 'rub', 'Lot': 1, 'Exchange': 'MOEX', 'FIGI': 'BBG004731032'},
            {'Ticker': 'ROSN', 'Name': 'Роснефть', 'Type': 'share', 'Currency': 'rub', 'Lot': 10, 'Exchange': 'MOEX', 'FIGI': 'BBG004731354'},
            {'Ticker': 'YNDX', 'Name': 'Яндекс', 'Type': 'share', 'Currency': 'rub', 'Lot': 1, 'Exchange': 'MOEX', 'FIGI': 'BBG006L8G4H1'},
            {'Ticker': 'VTBR', 'Name': 'Банк ВТБ', 'Type': 'share', 'Currency': 'rub', 'Lot': 10000, 'Exchange': 'MOEX', 'FIGI': 'BBG004730JJ5'},
            {'Ticker': 'TATN', 'Name': 'Татнефть', 'Type': 'share', 'Currency': 'rub', 'Lot': 1, 'Exchange': 'MOEX', 'FIGI': 'BBG004731489'},
            {'Ticker': 'GMKN', 'Name': 'Норильский никель', 'Type': 'share', 'Currency': 'rub', 'Lot': 1, 'Exchange': 'MOEX', 'FIGI': 'BBG0047315D0'},
            {'Ticker': 'PLZL', 'Name': 'Полюс', 'Type': 'share', 'Currency': 'rub', 'Lot': 1, 'Exchange': 'MOEX', 'FIGI': 'BBG00475J7X5'},
            {'Ticker': 'NLMK', 'Name': 'НЛМК', 'Type': 'share', 'Currency': 'rub', 'Lot': 1, 'Exchange': 'MOEX', 'FIGI': 'BBG00475K6C5'},
        ])


# Тестирование
if __name__ == "__main__":
    TOKEN = "t.8HbNCn4L0U9uBmMa5oloBrXCKxnqsTYNVK3f9iJOwDBiQ2lva9kvQ3C-MLgEESHl65ma1q0k0P6aMfS_O_co4g"
    
    service = InstrumentServiceWorking(TOKEN)
    
    print("🚀 Тестирование рабочего сервиса...")
    
    # Тест популярных акций
    print("\n📈 Получение популярных акций...")
    popular = service.get_popular_russian_shares_working()
    print(f"Найдено: {len(popular)} акций")
    print(popular[['Ticker', 'Name', 'Lot', 'Currency']])
    
    # Тест поиска
    print("\n🔍 Тест поиска 'GAZP'...")
    search_results = service.search_instruments_working("GAZP")
    print(f"Найдено: {len(search_results)} инструментов")
    if not search_results.empty:
        print(search_results[['Ticker', 'Name', 'Type', 'Currency']].head(3))
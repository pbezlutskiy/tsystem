import os
from datetime import datetime, timedelta
from tinkoff.invest import Client, InstrumentStatus, InstrumentIdType
import pandas as pd


class InstrumentServiceFixed:
    """Исправленный сервис инструментов с обработкой ошибок"""
    
    def __init__(self, token=None):
        self.token = token
    
    def _get_client(self):
        return Client(self.token)
    
    def get_shares_safe(self):
        """Безопасное получение акций с обработкой ошибок"""
        try:
            with self._get_client() as client:
                # Пробуем разные подходы
                try:
                    shares = client.instruments.shares().instruments
                    return shares
                except Exception as e:
                    print(f"⚠️ Ошибка при обычном запросе: {e}")
                    # Пробуем альтернативный метод
                    shares = client.instruments.shares(
                        instrument_status=InstrumentStatus.INSTRUMENT_STATUS_BASE
                    ).instruments
                    return shares
                    
        except Exception as e:
            print(f"❌ Критическая ошибка: {e}")
            return []
    
    def get_popular_russian_shares_fixed(self):
        """Получение популярных российских акций (безопасная версия)"""
        try:
            shares = self.get_shares_safe()
            popular_data = []
            
            # Список популярных тикеров
            popular_tickers = ['SBER', 'GAZP', 'LKOH', 'ROSN', 'YNDX', 'VTBR', 'TATN', 
                              'GMKN', 'PLZL', 'NLMK', 'POLY', 'AFKS', 'PHOR', 'MTSS']
            
            for share in shares:
                try:
                    ticker = getattr(share, 'ticker', '')
                    if ticker in popular_tickers:
                        popular_data.append({
                            'Ticker': ticker,
                            'Name': getattr(share, 'name', ''),
                            'Currency': getattr(share, 'currency', ''),
                            'Lot': getattr(share, 'lot', 1),
                            'Exchange': getattr(share, 'exchange', '')
                        })
                except Exception as e:
                    continue
            
            return pd.DataFrame(popular_data)
            
        except Exception as e:
            print(f"❌ Ошибка получения популярных акций: {e}")
            # Возвращаем тестовые данные
            return pd.DataFrame([
                {'Ticker': 'SBER', 'Name': 'Сбер Банк', 'Currency': 'rub', 'Lot': 1, 'Exchange': 'MOEX'},
                {'Ticker': 'GAZP', 'Name': 'Газпром', 'Currency': 'rub', 'Lot': 10, 'Exchange': 'MOEX'},
                {'Ticker': 'LKOH', 'Name': 'ЛУКОЙЛ', 'Currency': 'rub', 'Lot': 1, 'Exchange': 'MOEX'},
            ])
    
    def search_instruments_safe(self, query):
        """Безопасный поиск инструментов"""
        try:
            with self._get_client() as client:
                result = client.instruments.find_instrument(query=query)
                
                instruments_data = []
                for instrument in result.instruments:
                    try:
                        instruments_data.append({
                            'Ticker': getattr(instrument, 'ticker', ''),
                            'Name': getattr(instrument, 'name', ''),
                            'Type': getattr(instrument, 'instrument_type', ''),
                            'Currency': getattr(instrument, 'currency', ''),
                            'FIGI': getattr(instrument, 'figi', '')
                        })
                    except:
                        continue
                
                return pd.DataFrame(instruments_data)
                
        except Exception as e:
            print(f"❌ Ошибка поиска: {e}")
            return pd.DataFrame()


# Тестирование
if __name__ == "__main__":
    from config import Config
    TOKEN = Config.TINKOFF_TOKEN
    
    service = InstrumentServiceFixed(TOKEN)
    
    print("🔧 Тестирование исправленного сервиса...")
    
    # Тест популярных акций
    popular = service.get_popular_russian_shares_fixed()
    print(f"📈 Популярные акции: {len(popular)}")
    print(popular)
    
    # Тест поиска
    search_results = service.search_instruments_safe("SBER")
    print(f"🔍 Результаты поиска: {len(search_results)}")
    print(search_results)
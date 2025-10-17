import os
from datetime import datetime, timedelta
from tbank_api.instrument_service import InstrumentService

# Токен для тестирования
TOKEN = "t.8HbNCn4L0U9uBmMa5oloBrXCKxnqsTYNVK3f9iJOwDBiQ2lva9kvQ3C-MLgEESHl65ma1q0k0P6aMfS_O_co4g"

def main():
    service = InstrumentService(token=TOKEN)
    
    print("🚀 Тестирование сервиса инструментов...")
    
    # Тест 1: Получение акций
    print("\n1. 📊 Получение списка российских акций...")
    try:
        shares_df = service.shares_to_dataframe()
        print(f"✅ Успешно получено {len(shares_df)} российских акций")
        if len(shares_df) > 0:
            print("Первые 10 российских акций:")
            print(shares_df[['Ticker', 'Name', 'Exchange']].head(10))
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 2: Поиск инструментов (упрощенный)
    print("\n2. 🔍 Поиск российских инструментов...")
    try:
        search_queries = ['Сбер', 'Газпром', 'Лукойл', 'Норникель']
        for query in search_queries:
            print(f"\nПоиск '{query}':")
            instruments = service.find_instrument(query)
            russian_instruments = [i for i in instruments if hasattr(i, 'country_of_risk') and i.country_of_risk == 'RU']
            print(f"   Найдено российских инструментов: {len(russian_instruments)}")
            for instr in russian_instruments[:3]:
                print(f"   - {instr.ticker}: {instr.name}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 3: Получение ETF
    print("\n3. 📊 Получение ETF...")
    try:
        etfs = service.get_all_etfs()
        russian_etfs = [etf for etf in etfs if etf.currency == 'rub']
        print(f"✅ Найдено {len(russian_etfs)} российских ETF")
        for etf in russian_etfs[:5]:
            print(f"   - {etf.ticker}: {etf.name}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 4: Получение информации по конкретному инструменту
    print("\n4. 🔎 Информация по Сбербанку...")
    try:
        instrument = service.get_instrument_by_figi('BBG004730N88')
        print(f"✅ {instrument.instrument.ticker}: {instrument.instrument.name}")
        print(f"   Лот: {instrument.instrument.lot}")
        print(f"   Валюта: {instrument.instrument.currency}")
        print(f"   Минимальный шаг цены: {instrument.instrument.min_price_increment.units}.{instrument.instrument.min_price_increment.nano:09d}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
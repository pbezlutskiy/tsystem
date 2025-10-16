import os
from datetime import datetime, timedelta
from tbank_api.instrument_service import InstrumentService

# Токен для тестирования
TOKEN = "t.8HbNCn4L0U9uBmMa5oloBrXCKxnqsTYNVK3f9iJOwDBiQ2lva9kvQ3C-MLgEESHl65ma1q0k0P6aMfS_O_co4g"

def main():
    service = InstrumentService(token=TOKEN)
    
    print("🚀 Улучшенное тестирование сервиса инструментов...")
    
    # Тест 1: Получение акций
    print("\n1. 📊 Получение списка российских акций...")
    try:
        shares_df = service.shares_to_dataframe()
        print(f"✅ Успешно получено {len(shares_df)} российских акций")
        
        # Покажем известные акции
        known_tickers = ['SBER', 'GAZP', 'LKOH', 'ROSN', 'YNDX', 'VTBR', 'TATN', 'GMKN', 'PLZL', 'NLMK']
        known_shares = shares_df[shares_df['Ticker'].isin(known_tickers)]
        print("\n📈 Известные российские акции:")
        for _, share in known_shares.iterrows():
            print(f"   - {share['Ticker']}: {share['Name']}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 2: Улучшенный поиск инструментов
    print("\n2. 🔍 Улучшенный поиск инструментов...")
    try:
        search_queries = ['SBER', 'GAZP', 'LKOH', 'YNDX']
        for query in search_queries:
            print(f"\nПоиск '{query}':")
            instruments = service.find_instrument(query)
            
            if instruments:
                print(f"   Найдено инструментов: {len(instruments)}")
                for instr in instruments[:3]:  # Покажем первые 3
                    instrument_type = getattr(instr, 'instrument_type', 'Unknown')
                    currency = getattr(instr, 'currency', 'Unknown')
                    print(f"   - {instr.ticker}: {instr.name} ({instrument_type}, {currency})")
            else:
                print("   Инструменты не найдены")
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 3: Получение облигаций
    print("\n3. 📊 Получение облигаций...")
    try:
        bonds = service.get_all_bonds()
        russian_bonds = [bond for bond in bonds if bond.currency == 'rub']
        print(f"✅ Найдено {len(russian_bonds)} российских облигаций")
        
        # Покажем первые 5
        for bond in russian_bonds[:5]:
            print(f"   - {bond.ticker}: {bond.name}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 4: Поиск по FIGI
    print("\n4. 🔎 Поиск по FIGI...")
    try:
        # Популярные FIGI
        figi_dict = {
            'SBER': 'BBG004730N88',
            'GAZP': 'BBG004730RP0', 
            'LKOH': 'BBG004731032',
            'YNDX': 'BBG006L8G4H1'
        }
        
        for ticker, figi in figi_dict.items():
            instrument = service.get_instrument_by_figi(figi)
            if instrument and hasattr(instrument, 'instrument'):
                instr = instrument.instrument
                print(f"✅ {ticker}: {instr.name}")
                print(f"   FIGI: {instr.figi}")
                print(f"   Тикер: {instr.ticker}")
                print(f"   Валюта: {instr.currency}")
                print(f"   Лот: {instr.lot}")
                print(f"   Минимальный шаг: {instr.min_price_increment.units}.{instr.min_price_increment.nano:09d}")
                print()
                
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    # Тест 5: Получение валют
    print("\n5. 💰 Получение валют...")
    try:
        currencies = service.get_all_currencies()
        print(f"✅ Найдено {len(currencies)} валют")
        
        # Покажем основные валюты
        main_currencies = [c for c in currencies if c.ticker in ['USD', 'EUR', 'CNY', 'GBP']]
        for currency in main_currencies:
            print(f"   - {currency.ticker}: {currency.name}")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
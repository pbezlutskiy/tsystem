from tbank_api.instrument_service import InstrumentService
from tbank_api.instrument_service_working import InstrumentService

TOKEN = "t.8HbNCn4L0U9uBmMa5oloBrXCKxnqsTYNVK3f9iJOwDBiQ2lva9kvQ3C-MLgEESHl65ma1q0k0P6aMfS_O_co4g"

print("🔧 Тестирование исправленных импортов...")

try:
    service1 = InstrumentService(TOKEN)
    print("✅ InstrumentService работает")
    
    service2 = InstrumentServiceWorking(TOKEN) 
    print("✅ InstrumentServiceWorking работает")
    
    # Тест методов
    popular = service1.get_popular_russian_shares()
    print(f"✅ Популярные акции: {len(popular)}")
    
except Exception as e:
    print(f"❌ Ошибка: {e}")
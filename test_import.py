import sys
import os

print("🔧 Тест импорта модулей...")
print(f"Текущая директория: {os.getcwd()}")
print(f"Python path: {sys.path}")

try:
    from tbank_api.instrument_service_working import InstrumentService
    print("✅ instrument_service_working импортирован успешно!")
    
    # Тест функциональности
    TOKEN = "t.8HbNCn4L0U9uBmMa5oloBrXCKxnqsTYNVK3f9iJOwDBiQ2lva9kvQ3C-MLgEESHl65ma1q0k0P6aMfS_O_co4g"
    service = InstrumentService(TOKEN)
    print("✅ Сервис создан успешно!")
    
    # Тест поиска
    results = service.search_instruments_working("SBER")
    print(f"✅ Поиск работает! Найдено: {len(results)} инструментов")
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("📁 Содержимое папки tbank_api/:")
    try:
        files = os.listdir('tbank_api')
        for file in files:
            print(f"   - {file}")
    except:
        print("   Папка tbank_api не найдена")
except Exception as e:
    print(f"❌ Другая ошибка: {e}")
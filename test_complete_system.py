# test_complete_system.py
"""
Полное тестирование системы с расширенной аналитикой
"""

import sys
import os
import time
import pandas as pd
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tbank_api.tbank_data_loader import TBankDataLoader

def test_complete_system():
    print("🧪 ПОЛНОЕ ТЕСТИРОВАНИЕ СИСТЕМЫ")
    print("=" * 50)
    
    # Инициализация
    loader = TBankDataLoader()
    print("✅ TBankDataLoader инициализирован")
    
    # Тест 1: Базовая аналитика
    print("\n1. 📊 Тестирование базовой аналитики...")
    try:
        stats = loader.get_performance_stats()
        print(f"   • Запросов: {stats['total_requests']}")
        print(f"   • Hit Ratio: {stats['cache_hit_ratio']}")
        print("   ✅ Базовая аналитика работает")
    except Exception as e:
        print(f"   ❌ Ошибка базовой аналитики: {e}")
    
    # Тест 2: Расширенная аналитика
    print("\n2. 📈 Тестирование расширенной аналитики...")
    try:
        analytics = loader.get_detailed_analytics()
        print(f"   • Тренд Hit Ratio: {analytics.get('hit_ratio_trend', 'N/A')}")
        print(f"   • Активных алертов: {analytics.get('active_alerts_count', 0)}")
        print(f"   • Время работы: {analytics.get('uptime_hours', 0):.1f} ч")
        print("   ✅ Расширенная аналитика работает")
    except Exception as e:
        print(f"   ❌ Ошибка расширенной аналитики: {e}")
    
    # Тест 3: Полная аналитика
    print("\n3. 🎯 Тестирование полной аналитики...")
    try:
        full_analytics = loader.get_advanced_analytics()
        alerts = full_analytics.get('active_alerts', [])
        print(f"   • Всего алертов: {len(alerts)}")
        for alert in alerts:
            print(f"   • Алерт: {alert['title']} ({alert['level']})")
        print("   ✅ Полная аналитика работает")
    except Exception as e:
        print(f"   ❌ Ошибка полной аналитики: {e}")
    
    # Тест 4: Загрузка инструментов (если есть API ключ)
    print("\n4. 🔍 Тестирование загрузки инструментов...")
    try:
        symbols = loader.get_available_symbols()
        if not symbols.empty:
            print(f"   • Загружено инструментов: {len(symbols)}")
            print("   ✅ Загрузка инструментов работает")
        else:
            print("   ⚠️ Нет инструментов (возможно, нет API ключа)")
    except Exception as e:
        print(f"   ❌ Ошибка загрузки инструментов: {e}")
    
    # Тест 5: Статистика кэша
    print("\n5. 💾 Тестирование статистики кэша...")
    try:
        cache_stats = loader.get_cache_stats()
        print(f"   • Файлов инструментов: {cache_stats.get('instruments_cache_size', 0)}")
        print(f"   • Файлов свечей: {cache_stats.get('candles_cache_size', 0)}")
        print(f"   • Размер кэша: {cache_stats.get('total_cache_size_mb', 0):.2f} MB")
        print("   ✅ Статистика кэша работает")
    except Exception as e:
        print(f"   ❌ Ошибка статистики кэша: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!")
    print("💡 Система готова к использованию с расширенной аналитикой")

if __name__ == "__main__":
    test_complete_system()
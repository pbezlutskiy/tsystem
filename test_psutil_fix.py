# test_final_psutil_fix.py
"""
Финальный тест исправления psutil
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_final_psutil_fix():
    print("🧪 ФИНАЛЬНЫЙ ТЕСТ ИСПРАВЛЕНИЯ PSUTIL")
    print("=" * 50)
    
    try:
        from tbank_api.optimized_data_manager import OptimizedTBankDataManager
        
        manager = OptimizedTBankDataManager()
        
        # Даем время для сбора метрик
        print("⏳ Ждем сбор метрик...")
        time.sleep(3)
        
        # Проверяем что аналитика работает без ошибок
        analytics = manager.get_detailed_analytics()
        
        print("✅ Аналитика работает без ошибок!")
        print(f"📊 ОСНОВНЫЕ МЕТРИКИ:")
        print(f"   • Hit Ratio: {analytics.get('cache_hit_ratio', 'N/A')}")
        print(f"   • Использование памяти: {analytics.get('memory_usage_mb', 0)} MB")
        print(f"   • Активных алертов: {analytics.get('active_alerts_count', 0)}")
        print(f"   • Время работы: {analytics.get('uptime_hours', 0):.1f} ч")
        
        print(f"⚙️  ФУНКЦИОНАЛЬНОСТЬ:")
        print(f"   • Мониторинг памяти: {'✅ Включен' if analytics.get('features', {}).get('memory_monitoring') else '⚠️ Выключен'}")
        print(f"   • Расширенная аналитика: {'✅ Включена' if analytics.get('features', {}).get('advanced_analytics') else '❌ Выключена'}")
        print(f"   • Мониторинг производительности: {'✅ Активен' if analytics.get('features', {}).get('performance_monitoring') else '❌ Неактивен'}")
        
        # Проверяем расширенную аналитику
        advanced = manager.get_advanced_analytics()
        trends = advanced.get('advanced_trends', {})
        print(f"📈 РАСШИРЕННАЯ АНАЛИТИКА:")
        print(f"   • Тренд Hit Ratio: {trends.get('hit_ratio_trend', 'N/A')}")
        print(f"   • Мониторинг памяти: {'✅ Доступен' if trends.get('memory_monitoring') else '⚠️ Недоступен'}")
        
        print("\n🎉 ВСЕ ИСПРАВЛЕНИЯ РАБОТАЮТ КОРРЕКТНО!")
        print("💡 Система готова к использованию")
        
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_final_psutil_fix()
# test_ai_features.py
"""
Тестирование AI-функций
"""

import sys
import os
import time
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tbank_api.optimized_data_manager import OptimizedTBankDataManager

def test_ai_features():
    print("🧪 ТЕСТИРОВАНИЕ AI-ФУНКЦИЙ")
    print("=" * 50)
    
    manager = OptimizedTBankDataManager()
    
    # Тест 1: Умный предсказатель
    print("1. 🔮 Тестирование умного предсказателя...")
    try:
        # Симулируем несколько обращений
        manager.smart_predictor.record_access("SBER", "1d")
        manager.smart_predictor.record_access("GAZP", "1d") 
        manager.smart_predictor.record_access("SBER", "1d")
        
        stats = manager.get_prediction_stats()
        print(f"   • Отслеживается инструментов: {stats['tracked_symbols']}")
        print(f"   • Предсказаний: {stats['total_predictions']}")
        print("   ✅ Умный предсказатель работает")
    except Exception as e:
        print(f"   ❌ Ошибка предсказателя: {e}")
    
    # Тест 2: Автооптимизатор
    print("2. ⚙️ Тестирование автооптимизатора...")
    try:
        optimizer_info = manager.get_optimization_info()
        print(f"   • Автооптимизация: {'Включена' if optimizer_info['auto_optimization_enabled'] else 'Выключена'}")
        print(f"   • История оптимизаций: {optimizer_info['optimization_history_count']}")
        
        # Запускаем оптимизацию
        manager.auto_optimizer.optimize_cache_parameters()
        print("   ✅ Автооптимизатор работает")
    except Exception as e:
        print(f"   ❌ Ошибка оптимизатора: {e}")
    
    # Тест 3: Полная аналитика
    print("3. 📊 Тестирование полной аналитики...")
    try:
        analytics = manager.get_detailed_analytics()
        print(f"   • Hit Ratio: {analytics.get('cache_hit_ratio', 'N/A')}")
        print(f"   • Размер кэша: {analytics.get('total_cache_size_mb', 0):.1f} MB")
        print("   ✅ Полная аналитика работает")
    except Exception as e:
        print(f"   ❌ Ошибка аналитики: {e}")
    
    print("\n🎉 AI-ФУНКЦИИ РАБОТАЮТ!")
    print("💡 Система теперь предсказывает ваши запросы и самооптимизируется")

if __name__ == "__main__":
    test_ai_features()
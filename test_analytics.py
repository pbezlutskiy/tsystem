# test_analytics.py
"""
Тестовый скрипт для проверки расширенной аналитики
"""

import sys
import os
import logging

# Добавляем путь к проекту
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_analytics():
    """Тестирование модуля аналитики"""
    try:
        # Импортируем после настройки пути
        from tbank_api.advanced_analytics import AdvancedCacheAnalytics
        
        # Создаем mock менеджер для тестирования
        class MockCacheManager:
            def get_detailed_analytics(self):
                return {
                    'cache_hit_ratio': '75%',
                    'avg_response_time_ms': 150.5,
                    'memory_usage_mb': 245.3,
                    'instruments_cache_size': 15,
                    'candles_cache_size': 42,
                    'memory_cache_entries': 128
                }
        
        print("🚀 Тестирование AdvancedCacheAnalytics...")
        
        # Создаем экземпляр
        mock_manager = MockCacheManager()
        analytics = AdvancedCacheAnalytics(mock_manager)
        
        # Ждем немного для сбора метрик
        import time
        time.sleep(2)
        
        # Получаем тренды
        trends = analytics.get_performance_trends()
        print("📊 Тренды производительности:")
        for key, value in trends.items():
            print(f"  {key}: {value}")
        
        print("✅ Тестирование завершено успешно!")
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь, что:")
        print("1. Установлен psutil: pip install psutil")
        print("2. Файл advanced_analytics.py в папке tbank_api/")
    except Exception as e:
        print(f"❌ Ошибка тестирования: {e}")

if __name__ == "__main__":
    test_analytics()
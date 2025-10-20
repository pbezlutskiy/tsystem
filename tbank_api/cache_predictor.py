# tbank_api/cache_predictor.py
"""
Система предзагрузки и прогнозирования запросов
"""

from datetime import datetime, time
import threading
from collections import deque
import heapq
import logging
from typing import List, Tuple, Dict

logger = logging.getLogger(__name__)

class CachePredictor:
    """Предсказывает и предзагружает данные"""
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.access_pattern = deque(maxlen=1000)
        self.popular_symbols = {}
        self.preload_thread = None
        self.running = False
        
    def record_access(self, symbol: str, timeframe: str):
        """Записывает обращение к данным"""
        key = (symbol, timeframe)
        self.access_pattern.append(key)
        self.popular_symbols[key] = self.popular_symbols.get(key, 0) + 1
        
    def get_popular_symbols(self, top_n: int = 10) -> List[Tuple[Tuple[str, str], int]]:
        """Возвращает самые популярные инструменты"""
        return heapq.nlargest(top_n, self.popular_symbols.items(), key=lambda x: x[1])
    
    def start_preload_daemon(self):
        """Запускает демон предзагрузки"""
        if self.preload_thread and self.preload_thread.is_alive():
            return
            
        self.running = True
        self.preload_thread = threading.Thread(target=self._preload_worker, daemon=True)
        self.preload_thread.start()
        logger.info("✅ Демон предзагрузки запущен")
    
    def stop_preload_daemon(self):
        """Останавливает демон предзагрузки"""
        self.running = False
        if self.preload_thread:
            self.preload_thread.join(timeout=5)
            logger.info("✅ Демон предзагрузки остановлен")
    
    def _preload_worker(self):
        """Рабочий процесс предзагрузки"""
        import time as time_module
        while self.running:
            try:
                # Предзагружаем популярные инструменты в нерабочее время
                current_time = datetime.now().time()
                if time(2, 0) <= current_time <= time(5, 0):  # Ночью
                    popular_symbols = self.get_popular_symbols(3)  # Топ-3
                    
                    for (symbol, timeframe), count in popular_symbols:
                        logger.info(f"🔮 Предзагрузка {symbol} ({timeframe}) - популярность: {count}")
                        try:
                            if hasattr(self.cache_manager, 'preload_data'):
                                self.cache_manager.preload_data(symbol, timeframe, days_back=7)
                        except Exception as e:
                            logger.warning(f"Ошибка предзагрузки {symbol}: {e}")
                
                # Ждем 1 час до следующей проверки
                for _ in range(3600):
                    if not self.running:
                        break
                    time_module.sleep(1)
                
            except Exception as e:
                logger.error(f"Ошибка в демоне предзагрузки: {e}")
                time_module.sleep(300)  # Ждем 5 минут при ошибке
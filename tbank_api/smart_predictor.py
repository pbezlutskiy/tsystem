# tbank_api/smart_predictor.py
"""
Интеллектуальное предсказание и предзагрузка данных
"""

import heapq
from datetime import datetime, time
from collections import defaultdict, deque
import threading
import time as time_module
from typing import Dict, List, Tuple, Set, Any
import logging

logger = logging.getLogger(__name__)

class SmartPredictor:
    """Умный предсказатель на основе паттернов использования"""
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.access_patterns = defaultdict(lambda: deque(maxlen=1000))
        self.time_patterns = defaultdict(lambda: defaultdict(int))
        self.seasonal_patterns = defaultdict(lambda: defaultdict(int))
        self.popular_symbols = {}
        
        self.prediction_accuracy = 0
        self.total_predictions = 0
        self.successful_predictions = 0
        
        self._start_prediction_engine()
    
    def record_access(self, symbol: str, timeframe: str, timestamp: datetime = None):
        """Запись обращения с временной меткой"""
        if timestamp is None:
            timestamp = datetime.now()
        
        key = (symbol, timeframe)
        
        # Обновляем паттерны доступа
        self.access_patterns[key].append(timestamp)
        self.popular_symbols[key] = self.popular_symbols.get(key, 0) + 1
        
        # Анализируем временные паттерны
        hour = timestamp.hour
        self.time_patterns[key][hour] += 1
        
        # Сезонные паттерны (день недели)
        day_of_week = timestamp.weekday()
        self.seasonal_patterns[key][day_of_week] += 1
    
    def get_likely_requests(self, hours_ahead: int = 24) -> List[Tuple[Tuple[str, str], float]]:
        """Предсказание вероятных запросов"""
        predictions = []
        current_time = datetime.now()
        
        for (symbol, timeframe), pattern in self.time_patterns.items():
            probability = self._calculate_request_probability(symbol, timeframe, current_time, hours_ahead)
            if probability > 0.3:  # Порог вероятности
                predictions.append(((symbol, timeframe), probability))
        
        # Сортируем по вероятности
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:10]  # Топ-10 предсказаний
    
    def _calculate_request_probability(self, symbol: str, timeframe: str, 
                                     current_time: datetime, hours_ahead: int) -> float:
        """Расчет вероятности запроса"""
        key = (symbol, timeframe)
        
        # Анализ временных паттернов
        time_prob = self._analyze_time_pattern(key, current_time, hours_ahead)
        
        # Анализ частоты обращений
        freq_prob = self._analyze_frequency_pattern(key)
        
        # Комбинированная вероятность
        combined_prob = (time_prob * 0.6 + freq_prob * 0.4)
        
        return min(combined_prob, 1.0)
    
    def _analyze_time_pattern(self, key: Tuple[str, str], current_time: datetime, hours_ahead: int) -> float:
        """Анализ временных паттернов"""
        hour_patterns = self.time_patterns[key]
        if not hour_patterns:
            return 0.0
        
        total_requests = sum(hour_patterns.values())
        current_hour = current_time.hour
        
        # Проверяем следующие N часов
        probability = 0.0
        for hour_offset in range(hours_ahead):
            target_hour = (current_hour + hour_offset) % 24
            hour_prob = hour_patterns.get(target_hour, 0) / total_requests
            probability = max(probability, hour_prob)
        
        return probability
    
    def _analyze_frequency_pattern(self, key: Tuple[str, str]) -> float:
        """Анализ паттернов частоты"""
        total_requests = self.popular_symbols.get(key, 0)
        if total_requests == 0:
            return 0.0
        
        # Нормализуем относительно самого популярного инструмента
        max_requests = max(self.popular_symbols.values()) if self.popular_symbols else 1
        return total_requests / max_requests
    
    def _start_prediction_engine(self):
        """Запуск движка предсказаний"""
        def prediction_worker():
            while True:
                try:
                    self._execute_predictions()
                    time_module.sleep(1800)  # Каждые 30 минут
                except Exception as e:
                    logger.error(f"Ошибка в движке предсказаний: {e}")
                    time_module.sleep(300)
        
        thread = threading.Thread(target=prediction_worker, daemon=True)
        thread.start()
    
    def _execute_predictions(self):
        """Выполнение предсказаний и предзагрузки"""
        likely_requests = self.get_likely_requests(hours_ahead=6)
        
        for (symbol, timeframe), probability in likely_requests:
            if probability > 0.7:  # Высокая вероятность
                logger.info(f"🔮 Предзагрузка {symbol} ({timeframe}) - вероятность: {probability:.1%}")
                try:
                    self.cache_manager.preload_data(symbol, timeframe, days_back=7)
                    self.total_predictions += 1
                    # В реальной системе здесь бы отслеживалась точность предсказаний
                except Exception as e:
                    logger.warning(f"Ошибка предзагрузки {symbol}: {e}")

    # ДОБАВЛЕННЫЕ МЕТОДЫ ДЛЯ GUI:
    
    def get_popular_symbols(self, top_n: int = 10) -> List[Tuple[Tuple[str, str], int]]:
        """Возвращает самые популярные инструменты"""
        # Сортируем по количеству обращений и берем топ-N
        sorted_symbols = sorted(
            self.popular_symbols.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        return sorted_symbols[:top_n]
    
    def get_prediction_stats(self) -> Dict[str, Any]:
        """Статистика предсказаний"""
        accuracy = (self.successful_predictions / self.total_predictions * 100) if self.total_predictions > 0 else 0
        
        return {
            'total_predictions': self.total_predictions,
            'successful_predictions': self.successful_predictions,
            'prediction_accuracy': accuracy / 100,  # В долях для форматирования
            'access_patterns_count': len(self.access_patterns),
            'popular_symbols_count': len(self.popular_symbols)
        }
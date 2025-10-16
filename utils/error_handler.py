# ===== СЕКЦИЯ: ОБРАБОТКА ОШИБОК ТОРГОВОЙ СИСТЕМЫ =====
"""
Централизованная обработка ошибок для торговой системы
Декораторы для безопасного выполнения методов
"""

import logging
import traceback
import functools
from typing import Any, Callable, Dict, Optional
from datetime import datetime

import pandas as pd
import numpy as np

# Настройка логирования
logger = logging.getLogger(__name__)

def setup_error_handler_logging():
    """Настройка логирования для обработчика ошибок"""
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

setup_error_handler_logging()

class TradingError(Exception):
    """Базовое исключение торговой системы"""
    pass

class DataValidationError(TradingError):
    """Ошибка валидации данных"""
    pass

class StrategyCalculationError(TradingError):
    """Ошибка расчета стратегии"""
    pass

class RiskManagementError(TradingError):
    """Ошибка управления рисками"""
    pass

class KellyCalculationError(TradingError):
    """Ошибка расчета параметра Келли"""
    pass

class PositionSizeError(TradingError):
    """Ошибка расчета размера позиции"""
    pass

class CacheError(TradingError):
    """Ошибка работы с кэшем"""
    pass

class SimulationError(TradingError):
    """Ошибка симуляции торговли"""
    pass

def error_handler(logger: logging.Logger = None, 
                 default_return: Any = None,
                 log_level: int = logging.ERROR,
                 capture_traceback: bool = True):
    """
    Универсальный декоратор для обработки ошибок в методах системы
    
    Parameters:
    -----------
    logger : logging.Logger, optional
        Логгер для записи ошибок (по умолчанию используется модульный логгер)
    default_return : Any, optional
        Значение, возвращаемое при ошибке (по умолчанию определяется автоматически)
    log_level : int, optional
        Уровень логирования ошибок (по умолчанию ERROR)
    capture_traceback : bool, optional
        Захватывать ли traceback (по умолчанию True)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Используем переданный логгер или модульный
            current_logger = logger or logging.getLogger(func.__module__)
            
            try:
                return func(*args, **kwargs)
                
            except (DataValidationError, StrategyCalculationError, 
                   RiskManagementError, KellyCalculationError,
                   PositionSizeError, CacheError, SimulationError) as e:
                # Обработка специфичных ошибок торговой системы
                error_msg = f"{type(e).__name__} в {func.__name__}: {str(e)}"
                current_logger.log(log_level, error_msg)
                
                if capture_traceback:
                    current_logger.debug(f"Traceback для {func.__name__}:\n{traceback.format_exc()}")
                
                # Запись ошибки в объект системы (если есть)
                if args and hasattr(args[0], '_errors'):
                    args[0]._errors.append({
                        'method': func.__name__,
                        'error_type': type(e).__name__,
                        'error_message': str(e),
                        'timestamp': datetime.now(),
                        'args': str(args[1:]) if len(args) > 1 else 'None',
                        'kwargs': str(kwargs) if kwargs else 'None'
                    })
                
                return default_return if default_return is not None else safe_fallback(func.__name__, args, kwargs)
                
            except (ValueError, ZeroDivisionError, TypeError, 
                   AttributeError, KeyError, IndexError) as e:
                # Обработка стандартных Python ошибок
                error_msg = f"Ошибка данных в {func.__name__}: {str(e)}"
                current_logger.log(log_level, error_msg)
                
                if capture_traceback:
                    current_logger.debug(f"Traceback для {func.__name__}:\n{traceback.format_exc()}")
                
                return default_return if default_return is not None else safe_fallback(func.__name__, args, kwargs)
                
            except Exception as e:
                # Обработка всех остальных неожиданных ошибок
                error_msg = f"Неожиданная ошибка в {func.__name__}: {str(e)}"
                current_logger.log(log_level, error_msg)
                current_logger.error(f"Полный traceback для {func.__name__}:\n{traceback.format_exc()}")
                
                # Запись критической ошибки
                if args and hasattr(args[0], '_errors'):
                    args[0]._errors.append({
                        'method': func.__name__,
                        'error_type': 'CRITICAL',
                        'error_message': str(e),
                        'timestamp': datetime.now(),
                        'traceback': traceback.format_exc(),
                        'args': str(args[1:]) if len(args) > 1 else 'None',
                        'kwargs': str(kwargs) if kwargs else 'None'
                    })
                
                return default_return if default_return is not None else safe_fallback(func.__name__, args, kwargs)
                
        return wrapper
    return decorator

def safe_fallback(method_name: str, args: tuple, kwargs: dict) -> Any:
    """
    Безопасные значения по умолчанию при ошибках
    
    Parameters:
    -----------
    method_name : str
        Имя метода, в котором произошла ошибка
    args : tuple
        Аргументы метода
    kwargs : dict
        Именованные аргументы метода
        
    Returns:
    --------
    Any
        Безопасное значение по умолчанию
    """
    fallback_values = {
        # Методы расчета Келли
        'calculate_kelly_fraction': 0.1,
        'calculate_kelly_criterion': 0.1,
        
        # Методы расчета позиций
        'calculate_position_size': 0.0,
        'calculate_optimal_position': 0.0,
        'fast_position_size': 0.0,
        
        # Методы индикаторов
        'calculate_atr': pd.Series([0.0]),
        'calculate_sma': pd.Series([0.0]),
        'calculate_ema': pd.Series([0.0]),
        'calculate_rsi': pd.Series([50.0]),
        
        # Стратегии
        'multi_timeframe_signal': pd.DataFrame(),
        'supertrend_strategy': pd.DataFrame(),
        'vectorized_signal_calculation': pd.DataFrame(),
        
        # Симуляции
        'simulate_trading': _create_fallback_dataframe(args),
        '_optimized_simulation_loop': _create_fallback_dataframe(args),
        'run_backtest': _create_fallback_dataframe(args),
        
        # Управление рисками
        'dynamic_risk_management': 0.01,
        'calculate_risk_level': 0.01,
        'adjust_risk_parameters': 0.01,
        
        # Кэширование
        'get_from_cache': None,
        'save_to_cache': False,
        
        # Общие
        'get_performance_report': {},
        'get_cache_stats': {},
        'get_trade_history': pd.DataFrame(),
        'get_available_strategies': {'multi_timeframe': 'Мультифреймовая (MA)', 'supertrend': 'Super Trend'}
    }
    
    # Логирование использования fallback
    logger.warning(f"🛡️ Использовано безопасное значение для метода: {method_name}")
    
    return fallback_values.get(method_name, None)

def _create_fallback_dataframe(args: tuple) -> pd.DataFrame:
    """
    Создание безопасного DataFrame при ошибках симуляции
    
    Parameters:
    -----------
    args : tuple
        Аргументы метода
        
    Returns:
    --------
    pd.DataFrame
        Безопасный DataFrame с базовыми колонками
    """
    try:
       
        
        # Пытаемся получить исходные данные из аргументов
        original_data = None
        for arg in args:
            if isinstance(arg, pd.DataFrame) and not arg.empty:
                original_data = arg
                break
            elif hasattr(arg, 'price_data') and isinstance(arg.price_data, pd.DataFrame):
                original_data = arg.price_data
                break
        
        if original_data is not None:
            # Создаем безопасную копию с ограниченным количеством записей
            safe_data = original_data.copy().iloc[:min(100, len(original_data))]
        else:
            # Создаем минимальный DataFrame
            safe_data = pd.DataFrame({
                'close': [100.0] * 10
            })
        
        # Добавляем обязательные колонки
        safe_data['capital'] = 100000.0
        safe_data['kelly_f'] = 0.1
        safe_data['position_size'] = 0.0
        safe_data['risk_level'] = 0.01
        safe_data['drawdown'] = 0.0
        safe_data['position_type'] = 0
        safe_data['signal'] = 0
        
        return safe_data
        
    except Exception as e:
        # Минимальный fallback
        return pd.DataFrame({'capital': [100000.0]})

def with_error_handling(func: Callable = None, **decorator_kwargs):
    """
    Упрощенный декоратор для методов класса
    
    Parameters:
    -----------
    func : Callable, optional
        Декорируемая функция
    **decorator_kwargs
        Дополнительные аргументы для error_handler
        
    Returns:
    --------
    Callable
        Декорированная функция
    """
    if func is None:
        return lambda f: error_handler(**decorator_kwargs)(f)
    return error_handler(**decorator_kwargs)(func)

def retry_on_error(max_retries: int = 3, delay: float = 1.0, 
                  exceptions: tuple = (Exception,)):
    """
    Декоратор для повторения операции при ошибках
    
    Parameters:
    -----------
    max_retries : int, optional
        Максимальное количество попыток (по умолчанию 3)
    delay : float, optional
        Задержка между попытками в секундах (по умолчанию 1.0)
    exceptions : tuple, optional
        Типы исключений для перехвата (по умолчанию все)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    logger.warning(f"⚠️ Попытка {attempt + 1}/{max_retries} не удалась в {func.__name__}: {e}")
                    
                    if attempt < max_retries - 1:
                        import time
                        time.sleep(delay)
                    else:
                        logger.error(f"❌ Все {max_retries} попыток не удались в {func.__name__}")
                        raise last_exception
            
            # Эта строка никогда не должна выполняться
            return safe_fallback(func.__name__, args, kwargs)
        return wrapper
    return decorator

class ErrorCollector:
    """
    Класс для сбора и анализа ошибок системы
    """
    
    def __init__(self):
        self.errors = []
        self.error_stats = {}
    
    def add_error(self, method_name: str, error: Exception, 
                 args: tuple = None, kwargs: dict = None):
        """
        Добавление ошибки в коллектор
        
        Parameters:
        -----------
        method_name : str
            Имя метода, в котором произошла ошибка
        error : Exception
            Объект исключения
        args : tuple, optional
            Аргументы метода
        kwargs : dict, optional
            Именованные аргументы метода
        """
        error_info = {
            'method': method_name,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.now(),
            'args': str(args) if args else 'None',
            'kwargs': str(kwargs) if kwargs else 'None',
            'traceback': traceback.format_exc()
        }
        
        self.errors.append(error_info)
        
        # Обновление статистики
        error_type = type(error).__name__
        if error_type in self.error_stats:
            self.error_stats[error_type] += 1
        else:
            self.error_stats[error_type] = 1
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Получение сводки по ошибкам
        
        Returns:
        --------
        dict
            Сводная информация об ошибках
        """
        return {
            'total_errors': len(self.errors),
            'error_types': self.error_stats,
            'recent_errors': self.errors[-10:] if self.errors else [],
            'most_common_error': max(self.error_stats, key=self.error_stats.get) if self.error_stats else 'None'
        }
    
    def clear_errors(self):
        """Очистка коллекции ошибок"""
        self.errors.clear()
        self.error_stats.clear()
    
    def save_errors_to_file(self, filename: str = "trading_errors.log"):
        """
        Сохранение ошибок в файл
        
        Parameters:
        -----------
        filename : str, optional
            Имя файла для сохранения
        """
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=== ЛОГ ОШИБОК ТОРГОВОЙ СИСТЕМЫ ===\n\n")
                
                for i, error in enumerate(self.errors, 1):
                    f.write(f"ОШИБКА #{i}:\n")
                    f.write(f"Метод: {error['method']}\n")
                    f.write(f"Тип: {error['error_type']}\n")
                    f.write(f"Сообщение: {error['error_message']}\n")
                    f.write(f"Время: {error['timestamp']}\n")
                    f.write(f"Аргументы: {error['args']}\n")
                    f.write(f"KWArgs: {error['kwargs']}\n")
                    f.write(f"Traceback:\n{error['traceback']}\n")
                    f.write("-" * 50 + "\n")
                
                f.write(f"\nСТАТИСТИКА:\n")
                f.write(f"Всего ошибок: {len(self.errors)}\n")
                for error_type, count in self.error_stats.items():
                    f.write(f"{error_type}: {count}\n")
            
            logger.info(f"✅ Ошибки сохранены в файл: {filename}")
            
        except Exception as e:
            logger.error(f"❌ Ошибка сохранения ошибок в файл: {e}")

def validate_method_arguments(func: Callable) -> Callable:
    """
    Декоратор для валидации аргументов методов
    
    Parameters:
    -----------
    func : Callable
        Декорируемая функция
        
    Returns:
    --------
    Callable
        Декорированная функция с валидацией аргументов
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        try:
            # Базовая валидация числовых аргументов
            for i, arg in enumerate(args):
                if isinstance(arg, (int, float)) and not np.isfinite(arg):
                    raise ValueError(f"Некорректное числовое значение в аргументе {i}: {arg}")
            
            for key, value in kwargs.items():
                if isinstance(value, (int, float)) and not np.isfinite(value):
                    raise ValueError(f"Некорректное числовое значение в аргументе {key}: {value}")
            
            return func(*args, **kwargs)
            
        except ValueError as e:
            logger.error(f"❌ Ошибка валидации аргументов в {func.__name__}: {e}")
            return safe_fallback(func.__name__, args, kwargs)
    
    return wrapper

# Глобальный коллектор ошибок
global_error_collector = ErrorCollector()

def get_global_error_collector() -> ErrorCollector:
    """
    Получение глобального коллектора ошибок
    
    Returns:
    --------
    ErrorCollector
        Глобальный коллектор ошибок
    """
    return global_error_collector

# Пример использования
if __name__ == "__main__":
    # Тестирование декораторов
    
    @with_error_handling
    def test_method(x, y):
        """Тестовый метод для демонстрации работы декоратора"""
        if y == 0:
            raise ZeroDivisionError("Деление на ноль!")
        return x / y
    
    @retry_on_error(max_retries=2, delay=0.1)
    def test_retry_method():
        """Тестовый метод для демонстрации повторных попыток"""
        import random
        if random.random() < 0.7:
            raise ValueError("Случайная ошибка!")
        return "Успех!"
    
    # Тестирование
    print("🧪 Тестирование обработки ошибок...")
    
    # Тест обычного декоратора
    result1 = test_method(10, 0)  # Должен вернуть fallback значение
    print(f"Результат с ошибкой: {result1}")
    
    result2 = test_method(10, 2)  # Должен работать нормально
    print(f"Результат без ошибки: {result2}")
    
    # Тест retry декоратора
    try:
        result3 = test_retry_method()
        print(f"Результат retry: {result3}")
    except Exception as e:
        print(f"Retry не удался: {e}")
    
    # Показать статистику ошибок
    summary = global_error_collector.get_error_summary()
    print(f"📊 Статистика ошибок: {summary}")
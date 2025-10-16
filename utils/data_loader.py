# ===== СЕКЦИЯ 4: ЗАГРУЗКА И ПОДГОТОВКА ДАННЫХ =====
"""
Модуль для загрузки и предварительной обработки ценовых данных
Поддерживает различные форматы CSV файлов
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Optional
import logging
import os

# Настройка логирования
logger = logging.getLogger(__name__)

def setup_data_loader_logging():
    """Настройка логирования для модуля загрузки данных"""
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

setup_data_loader_logging()

def validate_price_data(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Комплексная валидация ценовых данных
    Возвращает словарь с результатами проверок
    
    Parameters:
    -----------
    data : pd.DataFrame
        Данные для валидации
        
    Returns:
    --------
    dict
        Результаты валидации с ключами:
        - is_valid: bool
        - errors: List[str]
        - warnings: List[str] 
        - stats: Dict[str, Any]
    """
    validation_results = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'stats': {}
    }
    
    try:
        # Проверка 1: Наличие данных
        if data.empty:
            validation_results['is_valid'] = False
            validation_results['errors'].append("DataFrame пуст")
            return validation_results
        
        # Проверка 2: Обязательные колонки
        required_columns = ['close']
        missing_columns = [col for col in required_columns if col not in data.columns]
        if missing_columns:
            validation_results['is_valid'] = False
            validation_results['errors'].append(f"Отсутствуют обязательные колонки: {missing_columns}")
        
        # Проверка 3: Корректность цен
        if 'close' in data.columns:
            close_prices = data['close']
            
            # Отрицательные цены
            negative_prices = (close_prices <= 0).sum()
            if negative_prices > 0:
                validation_results['warnings'].append(f"Обнаружено {negative_prices} отрицательных цен")
                # Автоматическое исправление
                data['close'] = close_prices.clip(lower=0.01)
                logger.warning(f"Заменено {negative_prices} отрицательных цен на минимальные значения")
            
            # NaN значения
            nan_count = close_prices.isna().sum()
            if nan_count > 0:
                validation_results['warnings'].append(f"Обнаружено {nan_count} NaN значений")
                # Заполнение NaN
                data['close'] = close_prices.ffill().bfill()
                logger.info(f"Заполнено {nan_count} NaN значений")
            
            # Выбросы (более 5 стандартных отклонений)
            if len(close_prices) > 10:
                z_scores = np.abs((close_prices - close_prices.mean()) / close_prices.std())
                outliers = (z_scores > 5).sum()
                if outliers > 0:
                    validation_results['warnings'].append(f"Обнаружено {outliers} выбросов (>5σ)")
                    
                    # Мягкая корректировка выбросов
                    q_low = close_prices.quantile(0.01)
                    q_high = close_prices.quantile(0.99)
                    data['close'] = close_prices.clip(lower=q_low, upper=q_high)
        
        # Проверка 4: Хронология данных
        if data.index.is_monotonic_increasing is False:
            validation_results['warnings'].append("Данные не отсортированы по времени")
            data.sort_index(inplace=True)
            logger.info("Данные отсортированы по времени")
        
        # Проверка 5: Достаточность данных
        if len(data) < 20:
            validation_results['warnings'].append(f"Мало данных для анализа: {len(data)} записей")
        elif len(data) < 100:
            validation_results['warnings'].append(f"Рекомендуется больше данных: {len(data)} записей (минимум 100-200)")
        
        # Проверка 6: Дубликаты индекса
        duplicate_indices = data.index.duplicated().sum()
        if duplicate_indices > 0:
            validation_results['warnings'].append(f"Обнаружено {duplicate_indices} дубликатов индекса")
            data = data[~data.index.duplicated(keep='first')]
        
        # Статистика
        validation_results['stats'] = {
            'total_records': len(data),
            'date_range': f"{data.index.min()} - {data.index.max()}" if len(data) > 0 else "N/A",
            'price_range': f"{data['close'].min():.2f} - {data['close'].max():.2f}" if 'close' in data.columns else "N/A",
            'data_quality_score': calculate_data_quality_score(data),
            'missing_values': data.isna().sum().to_dict() if not data.empty else {},
            'duplicates_removed': duplicate_indices
        }
        
    except Exception as e:
        validation_results['is_valid'] = False
        validation_results['errors'].append(f"Ошибка валидации: {str(e)}")
        logger.error(f"Ошибка валидации данных: {e}")
    
    return validation_results

def calculate_data_quality_score(data: pd.DataFrame) -> float:
    """
    Расчет оценки качества данных (0-100)
    
    Parameters:
    -----------
    data : pd.DataFrame
        Данные для оценки
        
    Returns:
    --------
    float
        Оценка качества данных от 0 до 100
    """
    if data.empty:
        return 0.0
    
    score = 100.0
    
    try:
        # Штраф за NaN (максимум -30 баллов)
        if 'close' in data.columns:
            nan_ratio = data['close'].isna().sum() / len(data)
            score -= nan_ratio * 30
        
        # Штраф за отрицательные цены (максимум -20 баллов)
        if 'close' in data.columns:
            negative_ratio = (data['close'] <= 0).sum() / len(data)
            score -= negative_ratio * 20
        
        # Штраф за недостаток данных (максимум -20 баллов)
        if len(data) < 50:
            data_penalty = (50 - len(data)) * 0.4
            score -= min(data_penalty, 20)
        
        # Штраф за неотсортированность (максимум -10 баллов)
        if not data.index.is_monotonic_increasing:
            score -= 10
        
        # Штраф за дубликаты (максимум -10 баллов)
        duplicate_ratio = data.index.duplicated().sum() / len(data)
        score -= duplicate_ratio * 10
        
        # Бонус за хороший объем данных (+10 баллов)
        if len(data) > 500:
            score += 10
        
    except Exception as e:
        logger.warning(f"Ошибка расчета оценки качества данных: {e}")
        return 50.0  # Базовая оценка при ошибках
    
    return max(0.0, min(score, 100.0))

def detect_csv_format(filename: str) -> Dict[str, Any]:
    """
    Автоматическое определение формата CSV файла
    
    Parameters:
    -----------
    filename : str
        Путь к файлу
        
    Returns:
    --------
    dict
        Информация о формате файла
    """
    format_info = {
        'delimiter': ';',
        'encoding': 'utf-8',
        'has_header': True,
        'date_format': 'auto'
    }
    
    try:
        # Чтение первых строк для анализа
        with open(filename, 'r', encoding='utf-8') as f:
            first_lines = [f.readline() for _ in range(5)]
        
        # Анализ разделителя
        delimiters = [';', ',', '\t', '|']
        delimiter_counts = {}
        
        for line in first_lines:
            for delim in delimiters:
                count = line.count(delim)
                if delim in delimiter_counts:
                    delimiter_counts[delim] += count
                else:
                    delimiter_counts[delim] = count
        
        # Выбор наиболее частого разделителя
        if delimiter_counts:
            format_info['delimiter'] = max(delimiter_counts, key=delimiter_counts.get)
        
        # Проверка заголовка
        if first_lines and any(keyword in first_lines[0].lower() for keyword in ['date', 'time', 'close', 'open']):
            format_info['has_header'] = True
        else:
            format_info['has_header'] = False
            
        # Определение формата даты
        if any('<' in line and '>' in line for line in first_lines):
            format_info['date_format'] = 'metaquotes'  # Формат MetaTrader
        
    except UnicodeDecodeError:
        # Попробуем другую кодировку
        try:
            with open(filename, 'r', encoding='cp1251') as f:
                first_lines = [f.readline() for _ in range(5)]
            format_info['encoding'] = 'cp1251'
        except:
            format_info['encoding'] = 'latin-1'
    except Exception as e:
        logger.warning(f"Ошибка определения формата файла {filename}: {e}")
    
    return format_info

def load_price_data_from_file(filename: str) -> pd.DataFrame:
    """
    Загрузка ценовых данных из CSV файла с автоматическим определением формата
    и улучшенной обработкой ошибок
    
    Parameters:
    -----------
    filename : str
        Путь к CSV файлу с данными
        
    Returns:
    --------
    pd.DataFrame
        Загруженные и обработанные данные с индексом datetime
    """
    
    # Проверка существования файла
    if not os.path.exists(filename):
        logger.error(f"Файл не найден: {filename}")
        return pd.DataFrame()
    
    try:
        logger.info(f"🔄 Загрузка данных из файла: {filename}")
        
        # Определение формата файла
        format_info = detect_csv_format(filename)
        logger.info(f"📋 Определен формат: разделитель='{format_info['delimiter']}', "
                   f"кодировка='{format_info['encoding']}', заголовок={format_info['has_header']}")
        
        # Параметры чтения CSV
        read_params = {
            'delimiter': format_info['delimiter'],
            'encoding': format_info['encoding'],
            'skipinitialspace': True,
            'on_bad_lines': 'skip'
        }
        
        if format_info['has_header']:
            data = pd.read_csv(filename, **read_params)
        else:
            data = pd.read_csv(filename, header=None, **read_params)
            # Попытка автоматического определения колонок
            if len(data.columns) >= 4:
                data.columns = ['date', 'time', 'open', 'high', 'low', 'close', 'volume'][:len(data.columns)]
        
        logger.info(f"📥 Загружено {len(data)} записей из {filename}")
        
        # Обработка данных
        result_data = process_loaded_data(data, format_info)
        
        # Валидация данных
        validation = validate_price_data(result_data)
        
        if not validation['is_valid']:
            logger.error(f"❌ Данные не прошли валидацию: {validation['errors']}")
            return pd.DataFrame()
        
        # Логирование предупреждений
        if validation['warnings']:
            for warning in validation['warnings']:
                logger.warning(f"⚠️ {warning}")
        
        # Логирование статистики
        stats = validation['stats']
        logger.info(f"✅ Успешно загружено {stats['total_records']} записей")
        logger.info(f"📊 Качество данных: {stats['data_quality_score']:.1f}/100")
        logger.info(f"📅 Диапазон дат: {stats['date_range']}")
        logger.info(f"💰 Диапазон цен: {stats['price_range']}")
        
        return result_data
        
    except pd.errors.EmptyDataError:
        logger.error(f"❌ Файл пуст или не содержит данных: {filename}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"❌ Ошибка при загрузке данных из {filename}: {str(e)}")
        return pd.DataFrame()

def process_loaded_data(data: pd.DataFrame, format_info: Dict[str, Any]) -> pd.DataFrame:
    """
    Обработка загруженных данных: преобразование колонок, дат и индекса
    
    Parameters:
    -----------
    data : pd.DataFrame
        Сырые загруженные данные
    format_info : dict
        Информация о формате файла
        
    Returns:
    --------
    pd.DataFrame
        Обработанные данные
    """
    result_data = pd.DataFrame()
    
    try:
        # Автоматическое определение колонок
        column_mapping = {
            '<CLOSE>': 'close', 'CLOSE': 'close', 'close': 'close', 'Close': 'close',
            '<HIGH>': 'high', 'HIGH': 'high', 'high': 'high', 'High': 'high',
            '<LOW>': 'low', 'LOW': 'low', 'low': 'low', 'Low': 'low',
            '<OPEN>': 'open', 'OPEN': 'open', 'open': 'open', 'Open': 'open',
            '<DATE>': 'date', 'DATE': 'date', 'date': 'date', 'Date': 'date',
            '<TIME>': 'time', 'TIME': 'time', 'time': 'time', 'Time': 'time',
            '<VOLUME>': 'volume', 'VOLUME': 'volume', 'volume': 'volume', 'Volume': 'volume'
        }
        
        # Сопоставление колонок
        for file_col, standard_col in column_mapping.items():
            if file_col in data.columns:
                # Преобразование в числовой формат с обработкой ошибок
                result_data[standard_col] = pd.to_numeric(data[file_col], errors='coerce')
                logger.debug(f"Сопоставлена колонка: {file_col} -> {standard_col}")
        
        # Обработка даты и времени
        result_data = process_datetime_columns(result_data, data, format_info)
        
        # Обязательная колонка close
        if 'close' not in result_data.columns:
            logger.error("❌ Не найдена колонка с ценами закрытия")
            return pd.DataFrame()
        
        # Заполнение отсутствующих колонок
        result_data = fill_missing_columns(result_data)
        
        # Сортировка и установка индекса
        if 'date' in result_data.columns:
            result_data = result_data.sort_values('date').reset_index(drop=True)
            result_data.set_index('date', inplace=True)
        else:
            # Создание индекса по умолчанию
            result_data.index = pd.date_range(start='2020-01-01', periods=len(result_data), freq='D')
            logger.warning("⚠️ Создан индекс даты по умолчанию")
        
        # Очистка от полных дубликатов
        result_data = result_data.drop_duplicates()
        
    except Exception as e:
        logger.error(f"❌ Ошибка обработки данных: {e}")
        return pd.DataFrame()
    
    return result_data

def process_datetime_columns(result_data: pd.DataFrame, original_data: pd.DataFrame, 
                           format_info: Dict[str, Any]) -> pd.DataFrame:
    """
    Обработка колонок даты и времени
    
    Parameters:
    -----------
    result_data : pd.DataFrame
        Обрабатываемые данные
    original_data : pd.DataFrame  
        Исходные данные
    format_info : dict
        Информация о формате
        
    Returns:
    --------
    pd.DataFrame
        Данные с обработанными колонками даты/времени
    """
    
    # Поиск колонки с датой
    date_col = None
    time_col = None
    
    for col in original_data.columns:
        col_lower = str(col).lower()
        if 'date' in col_lower:
            date_col = col
        elif 'time' in col_lower:
            time_col = col
    
    # Обработка даты
    if date_col is not None:
        date_series = original_data[date_col]
        
        # Попытка различных форматов даты
        date_formats = [
            '%Y-%m-%d', '%d-%m-%Y', '%m-%d-%Y', '%Y.%m.%d', '%d.%m.%Y',
            '%y%m%d', '%Y%m%d', '%d/%m/%Y', '%m/%d/%Y'
        ]
        
        for fmt in date_formats:
            try:
                result_data['date'] = pd.to_datetime(date_series, format=fmt, errors='coerce')
                if not result_data['date'].isna().all():
                    logger.info(f"✅ Определен формат даты: {fmt}")
                    break
            except:
                continue
        
        # Если не удалось определить формат, используем автоматическое определение
        if 'date' not in result_data.columns or result_data['date'].isna().all():
            result_data['date'] = pd.to_datetime(date_series, errors='coerce')
            logger.info("📅 Использовано автоматическое определение формата даты")
    
    # Обработка времени (если есть)
    if time_col is not None and 'date' in result_data.columns:
        time_series = original_data[time_col]
        
        # Форматирование времени
        try:
            # Для формата HHMMSS
            if time_series.dtype == 'int64' or time_series.dtype == 'float64':
                time_series = time_series.astype(str).str.zfill(6)
                time_formatted = pd.to_datetime(time_series, format='%H%M%S', errors='coerce').dt.time
            else:
                time_formatted = pd.to_datetime(time_series, errors='coerce').dt.time
            
            # Объединение даты и времени
            result_data['date'] = pd.to_datetime(
                result_data['date'].dt.date.astype(str) + ' ' + time_formatted.astype(str)
            )
            logger.info("⏰ Объединены дата и время")
            
        except Exception as e:
            logger.warning(f"⚠️ Ошибка обработки времени: {e}")
    
    # Если дата не определена, создаем ее
    if 'date' not in result_data.columns or result_data['date'].isna().all():
        result_data['date'] = pd.date_range(start='2020-01-01', periods=len(result_data), freq='D')
        logger.warning("⚠️ Созданы даты по умолчанию")
    
    return result_data

def fill_missing_columns(result_data: pd.DataFrame) -> pd.DataFrame:
    """
    Заполнение отсутствующих колонок вычисляемыми значениями
    
    Parameters:
    -----------
    result_data : pd.DataFrame
        Данные для заполнения
        
    Returns:
    --------
    pd.DataFrame
        Данные с заполненными колонками
    """
    
    # Если есть close, но нет high/low/open
    if 'close' in result_data.columns:
        if 'high' not in result_data.columns:
            result_data['high'] = result_data['close'] * 1.002  # +0.2%
            logger.info("📈 Создана колонка high на основе close")
        
        if 'low' not in result_data.columns:
            result_data['low'] = result_data['close'] * 0.998  # -0.2%
            logger.info("📉 Создана колонка low на основе close")
        
        if 'open' not in result_data.columns:
            result_data['open'] = result_data['close'].shift(1).fillna(result_data['close'])
            logger.info("📊 Создана колонка open на основе close")
    
    # Создание volume если отсутствует
    if 'volume' not in result_data.columns:
        result_data['volume'] = 1000  # Значение по умолчанию
        logger.info("📦 Создана колонка volume со значениями по умолчанию")
    
    return result_data

def get_data_summary(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Получение сводки по данным
    
    Parameters:
    -----------
    data : pd.DataFrame
        Данные для анализа
        
    Returns:
    --------
    dict
        Сводная информация о данных
    """
    if data.empty:
        return {}
    
    summary = {
        'total_records': len(data),
        'date_range': {
            'start': data.index.min(),
            'end': data.index.max(),
            'days': (data.index.max() - data.index.min()).days
        },
        'columns': list(data.columns),
        'data_types': data.dtypes.to_dict(),
        'missing_values': data.isna().sum().to_dict()
    }
    
    if 'close' in data.columns:
        close_prices = data['close']
        summary['price_stats'] = {
            'min': close_prices.min(),
            'max': close_prices.max(),
            'mean': close_prices.mean(),
            'std': close_prices.std(),
            'last': close_prices.iloc[-1]
        }
    
    return summary

# Пример использования
if __name__ == "__main__":
    # Тестирование модуля
    test_file = "SI_250929_251001.csv"
    
    if os.path.exists(test_file):
        data = load_price_data_from_file(test_file)
        if not data.empty:
            summary = get_data_summary(data)
            print("📊 Сводка данных:")
            for key, value in summary.items():
                print(f"   {key}: {value}")
    else:
        print(f"❌ Тестовый файл {test_file} не найден")
# ===== СЕКЦИЯ 19: ИНДИКАТОР SUPER TREND =====
"""
Реализация индикатора Super Trend для определения тренда
Зеленая линия под ценой - восходящий тренд, красная над ценой - нисходящий
"""

import pandas as pd
import numpy as np
from typing import Tuple

def calculate_supertrend(data: pd.DataFrame, atr_period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
    """
    ОПТИМИЗИРОВАННАЯ версия расчета Super Trend с векторизованными операциями
    """
    df = data.copy().reset_index(drop=True)
    
    print(f"🔧 Super Trend расчет: {len(df)} записей")
    print(f"   Колонки: {list(df.columns)}")
    
    # 🔍 ПРОВЕРКА ВХОДНЫХ ДАННЫХ
    if 'high' not in df.columns or 'low' not in df.columns or 'close' not in df.columns:
        print(f"❌ ОШИБКА: Отсутствуют необходимые колонки high, low, close")
        # Создаем пустые колонки чтобы избежать ошибок
        df['supertrend_direction'] = 1.0
        df['supertrend_line'] = df['close'] if 'close' in df.columns else 0.0
        return df
    
    print(f"✅ Данные проверены: high={df['high'].min():.2f}-{df['high'].max():.2f}, "
          f"low={df['low'].min():.2f}-{df['low'].max():.2f}, "
          f"close={df['close'].min():.2f}-{df['close'].max():.2f}")
    
    # Расчет HL2 и ATR
    df['hl2'] = (df['high'] + df['low']) / 2
    df['tr'] = calculate_true_range(df)
    df['atr'] = df['tr'].rolling(window=atr_period, min_periods=1).mean()
    
    print(f"📊 ATR расчет: min={df['atr'].min():.2f}, max={df['atr'].max():.2f}, "
          f"NaN={df['atr'].isna().sum()}")
    
    # Базовые полосы
    df['basic_upper'] = df['hl2'] + (multiplier * df['atr'])
    df['basic_lower'] = df['hl2'] - (multiplier * df['atr'])
    
    print(f"📈 Базовые полосы: upper={df['basic_upper'].min():.2f}-{df['basic_upper'].max():.2f}, "
          f"lower={df['basic_lower'].min():.2f}-{df['basic_lower'].max():.2f}")
    
    # Инициализация массивов для векторизованных расчетов
    final_upper = np.zeros(len(df))
    final_lower = np.zeros(len(df))
    supertrend_direction = np.zeros(len(df))
    supertrend_line = np.zeros(len(df))
    
    # Находим первый валидный индекс после расчета ATR
    first_valid_idx = df['atr'].first_valid_index()
    if first_valid_idx is None:
        print(f"❌ ОШИБКА: ATR не рассчитан, все значения NaN")
        df['supertrend_direction'] = 1.0
        df['supertrend_line'] = df['close']
        return df
    
    start_idx = df.index.get_loc(first_valid_idx)
    print(f"✅ Первый валидный индекс: {start_idx}")
    
    # Инициализация первых значений
    final_upper[start_idx] = df.iloc[start_idx]['basic_upper']
    final_lower[start_idx] = df.iloc[start_idx]['basic_lower']
    
    if df.iloc[start_idx]['close'] <= final_upper[start_idx]:
        supertrend_direction[start_idx] = -1
        supertrend_line[start_idx] = final_upper[start_idx]
    else:
        supertrend_direction[start_idx] = 1
        supertrend_line[start_idx] = final_lower[start_idx]
    
    print(f"🎯 Инициализация: direction={supertrend_direction[start_idx]}, line={supertrend_line[start_idx]:.2f}")
    
    # ВЕКТОРИЗОВАННЫЙ РАСЧЕТ для остальных значений
    valid_calculations = 0
    for i in range(start_idx + 1, len(df)):
        try:
            # Финальная верхняя полоса
            if (df.iloc[i]['basic_upper'] < final_upper[i-1]) or (df.iloc[i-1]['close'] > final_upper[i-1]):
                final_upper[i] = df.iloc[i]['basic_upper']
            else:
                final_upper[i] = final_upper[i-1]
            
            # Финальная нижняя полоса
            if (df.iloc[i]['basic_lower'] > final_lower[i-1]) or (df.iloc[i-1]['close'] < final_lower[i-1]):
                final_lower[i] = df.iloc[i]['basic_lower']
            else:
                final_lower[i] = final_lower[i-1]
            
            # Определение направления и линии Super Trend
            if supertrend_direction[i-1] == 1:  # Предыдущий тренд восходящий
                if df.iloc[i]['close'] <= final_lower[i]:
                    supertrend_direction[i] = -1
                    supertrend_line[i] = final_upper[i]
                else:
                    supertrend_direction[i] = 1
                    supertrend_line[i] = final_lower[i]
            else:  # Предыдущий тренд нисходящий
                if df.iloc[i]['close'] >= final_upper[i]:
                    supertrend_direction[i] = 1
                    supertrend_line[i] = final_lower[i]
                else:
                    supertrend_direction[i] = -1
                    supertrend_line[i] = final_upper[i]
            
            valid_calculations += 1
            
        except Exception as e:
            print(f"❌ Ошибка на шаге {i}: {e}")
            # Заполняем предыдущими значениями при ошибке
            supertrend_direction[i] = supertrend_direction[i-1]
            supertrend_line[i] = supertrend_line[i-1]
    
    print(f"✅ Успешных расчетов: {valid_calculations}/{len(df) - start_idx - 1}")
    
    # Заполняем DataFrame результатами
    df['final_upper'] = final_upper
    df['final_lower'] = final_lower
    df['supertrend_direction'] = supertrend_direction
    df['supertrend_line'] = supertrend_line
    
    # 🔍 ДИАГНОСТИКА РЕЗУЛЬТАТА
    valid_direction = df['supertrend_direction'].notna().sum()
    valid_line = df['supertrend_line'].notna().sum()
    
    print(f"🎯 Super Trend результат:")
    print(f"   Направление: {valid_direction}/{len(df)} валидных")
    print(f"   Линия: {valid_line}/{len(df)} валидных") 
    print(f"   Уникальные направления: {np.unique(df['supertrend_direction'])}")
    print(f"   Диапазон линии: {df['supertrend_line'].min():.2f} - {df['supertrend_line'].max():.2f}")
    
    return df

def calculate_true_range(data: pd.DataFrame) -> pd.Series:
    """
    Расчет True Range (TR)
    TR = max[(high - low), abs(high - prev_close), abs(low - prev_close)]
    """
    print(f"🔧 Расчет True Range...")
    
    high = data['high']
    low = data['low'] 
    close_prev = data['close'].shift(1)
    
    tr1 = high - low
    tr2 = abs(high - close_prev)
    tr3 = abs(low - close_prev)
    
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    
    print(f"📊 True Range: min={tr.min():.2f}, max={tr.max():.2f}, NaN={tr.isna().sum()}")
    
    return tr

def get_supertrend_signals(data: pd.DataFrame) -> pd.Series:
    """
    Получение торговых сигналов на основе Super Trend
    
    Returns:
    --------
    pd.Series
        Сигналы: 1 - покупка, -1 - продажа, 0 - без сигнала
    """
    if 'supertrend_direction' not in data.columns:
        data = calculate_supertrend(data)
    
    # Сигналы при смене направления
    direction_changes = data['supertrend_direction'].diff()
    
    # Покупка: смена с -1 (нисходящий) на 1 (восходящий)
    buy_signals = (direction_changes == 2)
    
    # Продажа: смена с 1 (восходящий) на -1 (нисходящий)  
    sell_signals = (direction_changes == -2)
    
    signal_series = pd.Series(0, index=data.index)
    signal_series[buy_signals] = 1
    signal_series[sell_signals] = -1
    
    # Фильтр: игнорируем сигналы, которые сразу меняются обратно
    for i in range(1, len(signal_series) - 1):
        if signal_series.iloc[i] != 0 and signal_series.iloc[i+1] == -signal_series.iloc[i]:
            signal_series.iloc[i] = 0
            signal_series.iloc[i+1] = 0
    
    return signal_series

def analyze_supertrend_performance(data: pd.DataFrame) -> dict:
    """
    Анализ эффективности сигналов Super Trend
    """
    if 'supertrend_direction' not in data.columns:
        data = calculate_supertrend(data)
    
    signals = get_supertrend_signals(data)
    
    # Статистика сигналов
    buy_signals = signals[signals == 1]
    sell_signals = signals[signals == -1]
    
    stats = {
        'total_buy_signals': len(buy_signals),
        'total_sell_signals': len(sell_signals),
        'total_signals': len(buy_signals) + len(sell_signals),
        'buy_signal_dates': buy_signals.index.tolist(),
        'sell_signal_dates': sell_signals.index.tolist()
    }
    
    return stats
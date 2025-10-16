# ===== СЕКЦИЯ 2: ОСНОВНАЯ ТОРГОВАЯ СИСТЕМА =====
import numpy as np
import pandas as pd
from datetime import datetime
from typing import List, Optional, Dict, Tuple
import warnings
import time
warnings.filterwarnings('ignore')

# Импорт декоратора обработки ошибок
from utils.error_handler import with_error_handling

class SeikotaTradingSystem:
    def __init__(self, initial_capital: float = 100000):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = []
        
        # УПРОЩЕННАЯ статистика кэша
        self._cache_stats = {
            'atr_hits': 0, 'atr_misses': 0,
            'kelly_hits': 0, 'kelly_misses': 0,
            'position_hits': 0, 'position_misses': 0,
            'risk_hits': 0, 'risk_misses': 0
        }
        
        # ПРОСТОЙ кэш
        self._atr_cache = {}
        self._kelly_cache = {}
        self._position_size_cache = {}
        self._risk_management_cache = {}
        
        self.total_commission = 0
        self.total_slippage = 0
        self.trade_count = 0
        self.trade_history = []
        
        # 🔹 ОПТИМИЗАЦИЯ: Профилирование производительности
        self.performance_stats = {
            'calculation_time': 0,
            'cache_efficiency': 0,
            'vectorized_operations': 0
        }
        
        # 🆕 RISK MANAGEMENT: Параметры стоп-лоссов и тейк-профитов
        self.risk_params = {
            'stop_loss_atr_multiplier': 2.0,    # Стоп-лосс в ATR
            'take_profit_atr_multiplier': 3.0,  # Тейк-профит в ATR  
            'trailing_stop_enabled': True,      # Трейлинг-стоп
            'trailing_stop_atr_multiplier': 1.5,
            'break_even_stop': True,            # Стоп в безубыток
            'break_even_atr_threshold': 1.0,    # ATR для активации безубытка
            'max_position_risk': 0.02,          # Макс риск на позицию (2%)
            'time_stop_days': 10,               # Временной стоп (дней)
        }
        
        # 🆕 Активные ордера и стоп-лоссы
        self.active_orders = {
            'stop_loss': {},      # {position_id: stop_price}
            'take_profit': {},    # {position_id: take_profit_price}
            'trailing_stop': {},  # {position_id: {stop_price, highest_price}}
            'break_even': {}      # {position_id: activated}
        }
        
        self.risk_management_enabled = True

    # 🆕 ДОБАВЛЯЕМ ОТСУТСТВУЮЩИЙ МЕТОД
    @with_error_handling
    def get_available_strategies(self) -> Dict[str, str]:
        """
        Возвращает список доступных торговых стратегий
        
        Returns:
        --------
        dict
            Словарь с кодами стратегий и их описаниями
        """
        return {
            'multi_timeframe': 'Мультифреймовая (MA)',
            'supertrend': 'Super Trend'
        }

    # 🆕 НОВЫЙ МЕТОД: Расчет уровней стоп-лосса и тейк-профита
    @with_error_handling
    @with_error_handling
    def calculate_risk_levels(self, entry_price: float, atr: float, position_type: int) -> Dict[str, float]:
        """
        Расчет уровней стоп-лосса и тейк-профита на основе ATR
        """
        # 🆕 Если риск-менеджмент отключен, возвращаем нейтральные значения
        if not self.risk_management_enabled:
            return {
                'stop_loss': entry_price,
                'take_profit': entry_price,
                'initial_stop_loss': entry_price
            }
        
        # ... существующий код ...
        if atr <= 0 or entry_price <= 0:
            return {
                'stop_loss': entry_price,
                'take_profit': entry_price,
                'initial_stop_loss': entry_price
            }
        
        stop_distance = atr * self.risk_params['stop_loss_atr_multiplier']
        take_profit_distance = atr * self.risk_params['take_profit_atr_multiplier']
        
        if position_type == 1:  # LONG позиция
            stop_loss = entry_price - stop_distance
            take_profit = entry_price + take_profit_distance
        else:  # SHORT позиция
            stop_loss = entry_price + stop_distance
            take_profit = entry_price - take_profit_distance
        
        # Ограничение максимального риска на позицию
        risk_percent = abs(stop_loss - entry_price) / entry_price
        if risk_percent > self.risk_params['max_position_risk']:
            # Корректируем стоп-лосс под максимальный риск
            if position_type == 1:
                stop_loss = entry_price * (1 - self.risk_params['max_position_risk'])
            else:
                stop_loss = entry_price * (1 + self.risk_params['max_position_risk'])
        
        return {
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'initial_stop_loss': stop_loss,
            'stop_distance': stop_distance,
            'take_profit_distance': take_profit_distance
        }

    # 🆕 НОВЫЙ МЕТОД: Обновление трейлинг-стопа
    @with_error_handling
    def update_trailing_stop(self, position_id: str, current_price: float, 
                           atr: float, position_type: int) -> Optional[float]:
        """
        Обновление уровня трейлинг-стопа
        
        Parameters:
        -----------
        position_id : str
            ID позиции
        current_price : float
            Текущая цена
        atr : float
            Текущее значение ATR
        position_type : int
            Тип позиции: 1 (LONG), -1 (SHORT)
            
        Returns:
        --------
        float or None
            Новый уровень стоп-лосса или None если не изменился
        """
        if position_id not in self.active_orders['trailing_stop']:
            # Инициализация трейлинг-стопа
            self.active_orders['trailing_stop'][position_id] = {
                'stop_price': self.active_orders['stop_loss'].get(position_id, current_price),
                'highest_price': current_price if position_type == 1 else float('inf'),
                'lowest_price': current_price if position_type == -1 else 0
            }
            return self.active_orders['trailing_stop'][position_id]['stop_price']
        
        trail_data = self.active_orders['trailing_stop'][position_id]
        trailing_distance = atr * self.risk_params['trailing_stop_atr_multiplier']
        
        new_stop_price = None
        
        if position_type == 1:  # LONG
            # Обновляем наивысшую цену
            if current_price > trail_data['highest_price']:
                trail_data['highest_price'] = current_price
                # Поднимаем стоп-лосс
                new_stop_price = current_price - trailing_distance
                trail_data['stop_price'] = new_stop_price
                
                # Активация безубытка
                if (self.risk_params['break_even_stop'] and 
                    current_price >= trail_data['highest_price'] * (1 + self.risk_params['break_even_atr_threshold'] * atr / trail_data['highest_price'])):
                    new_stop_price = max(new_stop_price, self.active_orders['stop_loss'].get(position_id, current_price))
                    self.active_orders['break_even'][position_id] = True
                    
        else:  # SHORT
            # Обновляем наименьшую цену
            if current_price < trail_data['lowest_price']:
                trail_data['lowest_price'] = current_price
                # Опускаем стоп-лосс
                new_stop_price = current_price + trailing_distance
                trail_data['stop_price'] = new_stop_price
                
                # Активация безубытка
                if (self.risk_params['break_even_stop'] and 
                    current_price <= trail_data['lowest_price'] * (1 - self.risk_params['break_even_atr_threshold'] * atr / trail_data['lowest_price'])):
                    new_stop_price = min(new_stop_price, self.active_orders['stop_loss'].get(position_id, current_price))
                    self.active_orders['break_even'][position_id] = True
        
        return new_stop_price

    # 🆕 НОВЫЙ МЕТОД: Проверка срабатывания ордеров
    @with_error_handling
    def check_risk_orders(self, position_id: str, current_price: float, 
                         position_type: int, entry_price: float) -> Tuple[bool, str, float]:
        """
        Проверка срабатывания стоп-лоссов и тейк-профитов
        
        Parameters:
        -----------
        position_id : str
            ID позиции
        current_price : float
            Текущая цена
        position_type : int
            Тип позиции: 1 (LONG), -1 (SHORT)
        entry_price : float
            Цена входа
            
        Returns:
        --------
        tuple
            (should_exit, exit_reason, exit_price)
        """
        # Проверка стоп-лосса
        stop_loss_price = self.active_orders['stop_loss'].get(position_id)
        if stop_loss_price:
            if (position_type == 1 and current_price <= stop_loss_price) or \
               (position_type == -1 and current_price >= stop_loss_price):
                return True, 'stop_loss', stop_loss_price
        
        # Проверка тейк-профита
        take_profit_price = self.active_orders['take_profit'].get(position_id)
        if take_profit_price:
            if (position_type == 1 and current_price >= take_profit_price) or \
               (position_type == -1 and current_price <= take_profit_price):
                return True, 'take_profit', take_profit_price
        
        # Проверка трейлинг-стопа
        if position_id in self.active_orders['trailing_stop']:
            trail_stop_price = self.active_orders['trailing_stop'][position_id]['stop_price']
            if (position_type == 1 and current_price <= trail_stop_price) or \
               (position_type == -1 and current_price >= trail_stop_price):
                return True, 'trailing_stop', trail_stop_price
        
        return False, '', 0.0

    # 🆕 НОВЫЙ МЕТОД: Установка ордеров при входе в позицию
    @with_error_handling
    @with_error_handling
    def setup_risk_orders(self, position_id: str, entry_price: float, 
                        atr: float, position_type: int):
        """
        Установка стоп-лоссов и тейк-профитов при входе в позицию
        """
        # 🆕 Если риск-менеджмент отключен, не устанавливаем ордера
        if not self.risk_management_enabled:
            return
        
        risk_levels = self.calculate_risk_levels(entry_price, atr, position_type)
        
        # Устанавливаем основные ордера
        self.active_orders['stop_loss'][position_id] = risk_levels['stop_loss']
        self.active_orders['take_profit'][position_id] = risk_levels['take_profit']
        
        # ... остальной код без изменений ...
        
        # Инициализируем трейлинг-стоп если включен
        if self.risk_params['trailing_stop_enabled']:
            self.update_trailing_stop(position_id, entry_price, atr, position_type)
        
        # Инициализируем отслеживание времени
        self.active_orders['time_stop'] = self.active_orders.get('time_stop', {})
        self.active_orders['time_stop'][position_id] = {
            'entry_time': datetime.now(),
            'max_days': self.risk_params['time_stop_days']
        }

    # 🆕 НОВЫЙ МЕТОД: Проверка временного стопа
    @with_error_handling
    def check_time_stop(self, position_id: str) -> bool:
        """
        Проверка срабатывания временного стоп-лосса
        
        Parameters:
        -----------
        position_id : str
            ID позиции
            
        Returns:
        --------
        bool
            True если пора выходить по времени
        """
        if position_id not in self.active_orders.get('time_stop', {}):
            return False
        
        time_data = self.active_orders['time_stop'][position_id]
        days_in_position = (datetime.now() - time_data['entry_time']).days
        
        return days_in_position >= time_data['max_days']

    # 🆕 НОВЫЙ МЕТОД: Очистка ордеров при выходе из позиции
    @with_error_handling
    def clear_risk_orders(self, position_id: str):
        """
        Очистка всех ордеров для позиции
        
        Parameters:
        -----------
        position_id : str
            ID позиции для очистки
        """
        for order_type in self.active_orders:
            if position_id in self.active_orders[order_type]:
                del self.active_orders[order_type][position_id]

    # 🆕 НОВЫЙ МЕТОД: Обновление параметров риска
    @with_error_handling
    def update_risk_parameters(self, **kwargs):
        """
        Обновление параметров управления рисками
        
        Parameters:
        -----------
        **kwargs
            Параметры для обновления
        """
        valid_params = [
            'stop_loss_atr_multiplier', 'take_profit_atr_multiplier',
            'trailing_stop_enabled', 'trailing_stop_atr_multiplier',
            'break_even_stop', 'break_even_atr_threshold',
            'max_position_risk', 'time_stop_days'
        ]
        
        for key, value in kwargs.items():
            if key in valid_params:
                self.risk_params[key] = value

    # 🆕 НОВЫЙ МЕТОД: Получение текущих ордеров
    @with_error_handling
    def get_active_orders(self, position_id: str = None) -> Dict:
        """
        Получение информации об активных ордерах
        
        Parameters:
        -----------
        position_id : str, optional
            ID конкретной позиции
            
        Returns:
        --------
        dict
            Информация об ордерах
        """
        if position_id:
            return {
                'stop_loss': self.active_orders['stop_loss'].get(position_id),
                'take_profit': self.active_orders['take_profit'].get(position_id),
                'trailing_stop': self.active_orders['trailing_stop'].get(position_id),
                'break_even': self.active_orders['break_even'].get(position_id, False),
                'time_stop': self.active_orders.get('time_stop', {}).get(position_id)
            }
        else:
            return self.active_orders.copy()


    # 🆕 ИЗМЕНЕНИЕ СУЩЕСТВУЮЩЕГО МЕТОДА: _optimized_simulation_loop
    
    def _optimized_simulation_loop(self, data: pd.DataFrame, initial_f: float, 
                                risk_per_trade: float, use_dynamic_risk: bool) -> pd.DataFrame:
        """
        UPDATED trading simulation loop with risk management system
        ОБНОВЛЕННЫЙ цикл симуляции торговли с системой управления рисками
        """
        
        # === 1. ИНИЦИАЛИЗАЦИЯ ИСТОРИИ ===
        capital_history = [self.initial_capital]
        f_history = [initial_f]
        trades_history = []
        position_size_history = [0]
        risk_history = [risk_per_trade]
        drawdown_history = [0]
        position_type_history = [0]
        
        # 🆕 Дополнительная история для рисков
        stop_loss_history = [0]
        take_profit_history = [0]
        exit_reason_history = ['']

        # === 2. ПЕРЕМЕННЫЕ СОСТОЯНИЯ ===
        current_f = initial_f
        current_risk = risk_per_trade
        peak_capital = self.initial_capital
        position_size = 0
        entry_price = 0
        entry_index = 0
        position_type = 0
        in_position = False
        current_position_id = None  # 🆕 ID текущей позиции

        # === 3. ОСНОВНОЙ ЦИКЛ С УЧЕТОМ РИСК-МЕНЕДЖМЕНТА ===
        for i in range(1, len(data)):
            try:
                # Получение текущих данных
                current_capital = capital_history[-1]
                signal = data['signal'].iloc[i]
                current_price = data['close'].iloc[i]
                atr = data['atr'].iloc[i] if 'atr' in data.columns else None

                # Защита от некорректных данных
                if current_price <= 0:
                    current_price = data['close'].iloc[i-1] if i > 0 else 0.01

                # Расчет просадки
                peak_capital = max(peak_capital, current_capital)
                current_drawdown = (peak_capital - current_capital) / peak_capital if peak_capital > 0 else 0

                # Динамическое управление риском
                if use_dynamic_risk:
                    current_risk = self.dynamic_risk_management(
                        current_capital, peak_capital, risk_per_trade
                    )

                # Расчет нереализованного PnL
                unrealized_pnl = 0
                if in_position and position_size > 0 and entry_price > 0:
                    if position_type == 1:  # LONG
                        price_change_pct = (current_price - entry_price) / entry_price
                        unrealized_pnl = price_change_pct * position_size
                    elif position_type == -1:  # SHORT
                        price_change_pct = (entry_price - current_price) / entry_price
                        unrealized_pnl = price_change_pct * position_size
                
                # 🆕 ПРОВЕРКА РИСК-ОРДЕРОВ ДЛЯ АКТИВНОЙ ПОЗИЦИИ
                exit_trade = False
                trade_result_pct = 0
                trade_result = 0
                exit_reason = 'signal'  # По умолчанию выход по сигналу
                exit_price = current_price  # По умолчанию выход по текущей цене

                # В основном цикле, перед проверкой риск-ордеров:
                if in_position and current_position_id and self.risk_management_enabled:  # 🆕 Добавили проверку
                    # Проверка стоп-лоссов и тейк-профитов
                    should_exit, risk_exit_reason, risk_exit_price = self.check_risk_orders(
                        current_position_id, current_price, position_type, entry_price
                    )
                    
                    if should_exit:
                        exit_trade = True
                        exit_reason = risk_exit_reason
                        exit_price = risk_exit_price

                # ... аналогично для других проверок рисков ...

                # При входе в позицию:
                if in_position and current_position_id and self.risk_management_enabled:
                    # 🆕 УСТАНОВКА ОРДЕРОВ РИСК-МЕНЕДЖМЕНТА (только если включен)
                    if atr is not None:
                        self.setup_risk_orders(
                            current_position_id, entry_price, atr, position_type
                        )
                        # 🆕 ИСПРАВЛЕНИЕ: Определяем имя типа позиции
                        position_type_name = "LONG" if position_type == 1 else "SHORT"
                    
                    # Проверка временного стопа
                    elif self.check_time_stop(current_position_id):
                        exit_trade = True
                        exit_reason = 'time_stop'
                        exit_price = current_price
                    
                    # 🆕 Обновление трейлинг-стопа
                    if self.risk_params['trailing_stop_enabled'] and atr is not None:
                        new_stop = self.update_trailing_stop(
                            current_position_id, current_price, atr, position_type
                        )
                        if new_stop:
                            # Обновляем стоп-лосс в активных ордерах
                            self.active_orders['stop_loss'][current_position_id] = new_stop

                # 📈 ЛОГИКА ВХОДА В ПОЗИЦИЮ
                if not in_position:
                    if signal == 1:  # ПОКУПКА (LONG)
                        position_size = self.calculate_position_size(
                            current_f, current_price, atr, current_risk
                        )
                        
                        if position_size > 0 and current_price > 0:
                            entry_price = current_price
                            entry_index = i
                            position_type = 1
                            in_position = True
                            current_position_id = f"L_{i}_{current_price}"  # 🆕 Генерация ID позиции
                            
                            # 🆕 УСТАНОВКА ОРДЕРОВ РИСК-МЕНЕДЖМЕНТА
                            if atr is not None:
                                self.setup_risk_orders(
                                    current_position_id, entry_price, atr, position_type
                                )
                            
                    elif signal == 0:  # ПРОДАЖА (SHORT)  
                        position_size = self.calculate_position_size(
                            current_f, current_price, atr, current_risk
                        )
                        
                        if position_size > 0 and current_price > 0:
                            entry_price = current_price
                            entry_index = i
                            position_type = -1
                            in_position = True
                            current_position_id = f"S_{i}_{current_price}"  # 🆕 Генерация ID позиции
                            
                            # 🆕 УСТАНОВКА ОРДЕРОВ РИСК-МЕНЕДЖМЕНТА
                            if atr is not None:
                                self.setup_risk_orders(
                                    current_position_id, entry_price, atr, position_type
                                )

                # 📉 ЛОГИКА ВЫХОДА ИЗ ПОЗИЦИИ
                elif in_position and not exit_trade:  # 🆕 Проверяем только если не вышли по рискам
                    # Выход из LONG при сигнале на продажу
                    if position_type == 1 and signal == 0:
                        price_change_pct = (current_price - entry_price) / entry_price
                        trade_result_pct = price_change_pct
                        trade_result = price_change_pct * position_size
                        exit_trade = True
                        exit_reason = 'signal_sell'
                        
                    # Выход из SHORT при сигнале на покупку  
                    elif position_type == -1 and signal == 1:
                        price_change_pct = (entry_price - current_price) / entry_price
                        trade_result_pct = price_change_pct
                        trade_result = price_change_pct * position_size
                        exit_trade = True
                        exit_reason = 'signal_buy'
                
                # 🆕 ОБРАБОТКА ВЫХОДА ПО РИСКАМ
                if exit_trade and in_position:
                    # Расчет PnL для выхода по рискам
                    if exit_reason in ['stop_loss', 'take_profit', 'trailing_stop', 'time_stop']:
                        if position_type == 1:  # LONG
                            price_change_pct = (exit_price - entry_price) / entry_price
                        else:  # SHORT
                            price_change_pct = (entry_price - exit_price) / entry_price
                        
                        trade_result_pct = price_change_pct
                        trade_result = price_change_pct * position_size
                    
                    # Запись сделки с информацией о причине выхода
                    trade_info = {
                        'entry_index': entry_index,
                        'exit_index': i,
                        'entry_price': entry_price,
                        'exit_price': exit_price,  # 🆕 Используем цену выхода из ордера
                        'position_size': position_size,
                        'position_type': position_type,
                        'pnl_percent': trade_result_pct * 100,
                        'pnl_absolute': trade_result,
                        'duration': i - entry_index,
                        'capital_before': current_capital,
                        'capital_after': current_capital + trade_result,
                        'exit_reason': exit_reason,  # 🆕 Причина выхода
                        'position_id': current_position_id,  # 🆕 ID позиции
                        'stop_loss': self.active_orders['stop_loss'].get(current_position_id),
                        'take_profit': self.active_orders['take_profit'].get(current_position_id)
                    }
                    self.trade_history.append(trade_info)
                    
                    # Обновление капитала и истории
                    trades_history.append(trade_result_pct)
                    current_capital += trade_result
                    
                    # Обновление параметра Келли
                    if len(trades_history) >= 10:
                        current_f = self.calculate_kelly_fraction(trades_history[-10:])
                    
                    # 🆕 ОЧИСТКА ОРДЕРОВ РИСК-МЕНЕДЖМЕНТА
                    self.clear_risk_orders(current_position_id)
                    
                    # Сброс позиции
                    position_size = 0
                    position_type = 0
                    in_position = False
                    current_position_id = None

                # 🆕 СОХРАНЕНИЕ ИНФОРМАЦИИ О РИСКАХ В ИСТОРИЮ
                current_stop_loss = 0
                current_take_profit = 0
                
                if in_position and current_position_id:
                    current_stop_loss = self.active_orders['stop_loss'].get(current_position_id, 0)
                    current_take_profit = self.active_orders['take_profit'].get(current_position_id, 0)

                # Обновление истории
                total_capital = current_capital + unrealized_pnl
                total_capital = max(total_capital, 0)

                capital_history.append(total_capital)
                f_history.append(current_f)
                position_size_history.append(position_size)
                risk_history.append(current_risk)
                drawdown_history.append(current_drawdown)
                position_type_history.append(position_type)
                stop_loss_history.append(current_stop_loss)  # 🆕
                take_profit_history.append(current_take_profit)  # 🆕
                exit_reason_history.append(exit_reason if exit_trade else '')  # 🆕

                # Обновление текущего капитала системы
                self.current_capital = total_capital

            except Exception as e:
                # При ошибке на шаге используем предыдущие значения
                capital_history.append(capital_history[-1] if capital_history else self.initial_capital)
                f_history.append(f_history[-1] if f_history else initial_f)
                position_size_history.append(position_size_history[-1] if position_size_history else 0)
                risk_history.append(risk_history[-1] if risk_history else risk_per_trade)
                drawdown_history.append(drawdown_history[-1] if drawdown_history else 0)
                position_type_history.append(position_type_history[-1] if position_type_history else 0)
                stop_loss_history.append(stop_loss_history[-1] if stop_loss_history else 0)  # 🆕
                take_profit_history.append(take_profit_history[-1] if take_profit_history else 0)  # 🆕
                exit_reason_history.append(exit_reason_history[-1] if exit_reason_history else '')  # 🆕

        # === 4. СОЗДАНИЕ РЕЗУЛЬТАТОВ С ДОПОЛНИТЕЛЬНЫМИ КОЛОНКАМИ ===
        result_data = data.iloc[1:].copy()
        result_data = result_data.reset_index(drop=True)
        
        # Сохраняем ВСЕ колонки из data
        existing_columns = result_data.columns.tolist()
        all_columns = data.columns.tolist()
        
        for col in all_columns:
            if col not in existing_columns and col in data.columns:
                if len(data[col]) > 1 and len(data[col]) - 1 == len(result_data):
                    result_data[col] = data[col].iloc[1:]
                else:
                    result_data[col] = data[col].iloc[0] if len(data[col]) > 0 else np.nan
        
        # Добавляем расчетные колонки
        if len(capital_history) > 1 and len(capital_history) - 1 == len(result_data):
            result_data['capital'] = capital_history[1:]
        else:
            result_data['capital'] = [self.initial_capital] * len(result_data)
            
        result_data['kelly_f'] = f_history[1:] if len(f_history) > 1 else [initial_f] * len(result_data)
        result_data['position_size'] = position_size_history[1:] if len(position_size_history) > 1 else [0] * len(result_data)
        result_data['risk_level'] = risk_history[1:] if len(risk_history) > 1 else [risk_per_trade] * len(result_data)
        result_data['drawdown'] = drawdown_history[1:] if len(drawdown_history) > 1 else [0] * len(result_data)
        result_data['position_type'] = position_type_history[1:] if len(position_type_history) > 1 else [0] * len(result_data)
        
        # 🆕 ДОБАВЛЯЕМ НОВЫЕ КОЛОНКИ ДЛЯ РИСК-МЕНЕДЖМЕНТА
        result_data['stop_loss_level'] = stop_loss_history[1:] if len(stop_loss_history) > 1 else [0] * len(result_data)
        result_data['take_profit_level'] = take_profit_history[1:] if len(take_profit_history) > 1 else [0] * len(result_data)
        result_data['exit_reason'] = exit_reason_history[1:] if len(exit_reason_history) > 1 else [''] * len(result_data)
        
        return result_data    

    # 🆕 ДОБАВЛЯЕМ ОТСУТСТВУЮЩИЙ МЕТОД simulate_trading
    @with_error_handling
    def simulate_trading(self, price_data: pd.DataFrame,
                    initial_f: float = 0.1,
                    risk_per_trade: float = 0.01,
                    use_multi_timeframe: bool = True,
                    use_dynamic_risk: bool = True,
                    realistic_mode: bool = False,
                    result_name: str = None,
                    strategy_type: str = 'multi_timeframe',
                    supertrend_atr_period: int = 10,
                    supertrend_multiplier: float = 3.0) -> pd.DataFrame:
        """
        ОСНОВНАЯ СИМУЛЯЦИЯ ТОРГОВЛИ
        С улучшенной валидацией и обработкой ошибок
        """
        
        # === 1. ВАЛИДАЦИЯ ВХОДНЫХ ДАННЫХ ===
        from utils.data_loader import validate_price_data
        
        # Проверка данных
        validation = validate_price_data(price_data)
        if not validation['is_valid']:
            error_msg = f"Данные не прошли валидацию: {validation['errors']}"
            # Возвращаем безопасный DataFrame
            return self._create_safe_dataframe(price_data, self.initial_capital)
        
        # Проверка параметров
        if not self._validate_parameters(initial_f, risk_per_trade):
            return self._create_safe_dataframe(price_data, self.initial_capital)
        
        # === 2. ПОДГОТОВКА СИСТЕМЫ ===
        
        # Обновление параметров системы
        self.initial_capital = initial_f * 100000  # Для совместимости
        self.current_capital = self.initial_capital
        
        # Очистка предыдущих результатов
        self.clear_caches()
        self.trade_history = []
        
        # === 3. ВЫБОР СТРАТЕГИИ ===
        data = price_data.copy()

        # В методе simulate_trading:
        if strategy_type == 'supertrend':
            data = self.supertrend_strategy(data, supertrend_atr_period, supertrend_multiplier)
        else:
            if use_multi_timeframe:
                data = self.multi_timeframe_signal(data)
                # 🔥 НЕ МЕНЯЕМ КОЛОНКУ - стратегия сама создает 'signal'
            else:
                # Простая стратегия на основе скользящей средней
                data['signal'] = np.where(
                    data['close'] > data['close'].rolling(20).mean(), 1, 0)

        # 🔥 ГАРАНТИЯ: Проверяем, что колонка signal создана
        if 'signal' not in data.columns:
            data['signal'] = (data['close'] > data['close'].rolling(20).mean()).astype(int)
        
        # === 4. ПРЕДВАРИТЕЛЬНЫЕ РАСЧЕТЫ ===
        if 'high' in data.columns and 'low' in data.columns:
            data['atr'] = self.calculate_atr(data)
        else:
            data['atr'] = data['close'].rolling(20).std()
        
        # === 5. ЗАПУСК ОПТИМИЗИРОВАННОЙ СИМУЛЯЦИИ ===
        try:
            # Используем оптимизированный метод для симуляции
            result_data = self._optimized_simulation_loop(
                data, initial_f, risk_per_trade, use_dynamic_risk
            )
            
            # === 6. ПРОВЕРКА РЕЗУЛЬТАТОВ ===
            if result_data.empty or 'capital' not in result_data.columns:
                return self._create_safe_dataframe(price_data, self.initial_capital)
            
            # === 7. ФИНАЛЬНАЯ СТАТИСТИКА ===
            final_capital = result_data['capital'].iloc[-1]
            total_return = (final_capital - self.initial_capital) / self.initial_capital * 100
            trades_count = len(self.trade_history)
            
            # Статистика производительности
            perf_report = self.get_performance_report()
            
            return result_data
            
        except Exception as e:
            # Эта ошибка будет перехвачена декоратором @with_error_handling
            raise  # Передаем исключение декоратору

    # 🆕 ДОБАВЛЯЕМ ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ
    def _validate_parameters(self, initial_f: float, risk_per_trade: float) -> bool:
        """Валидация параметров системы"""
        checks = [
            0 < initial_f <= 0.5,
            0 < risk_per_trade <= 0.1,
            self.initial_capital > 0
        ]
        
        if not all(checks):
            return False
        return True

    def _create_safe_dataframe(self, original_data: pd.DataFrame, capital: float) -> pd.DataFrame:
        """Создание безопасного DataFrame при ошибках"""
        safe_data = original_data.copy().iloc[:min(100, len(original_data))]
        safe_data['capital'] = capital
        safe_data['kelly_f'] = 0.1
        safe_data['position_size'] = 0
        safe_data['risk_level'] = 0.01
        safe_data['drawdown'] = 0
        safe_data['position_type'] = 0
        
        return safe_data

    # 🆕 ДОБАВЛЯЕМ ОТСУТСТВУЮЩИЙ МЕТОД clear_caches
    @with_error_handling
    def clear_caches(self):
        """Очистка всех кэшей для перезапуска"""
        cache_attrs = ['_atr_cache', '_kelly_cache', '_position_size_cache', '_risk_management_cache']
        
        for attr in cache_attrs:
            if hasattr(self, attr):
                try:
                    # Для словарей используем clear(), для других типов - переинициализация
                    cache_obj = getattr(self, attr)
                    if isinstance(cache_obj, dict):
                        cache_obj.clear()
                    else:
                        setattr(self, attr, {})  # Пересоздаем пустой словарь
                except Exception as e:
                    pass
        
        # Также сбрасываем статистику
        self._cache_stats = {
            'atr_hits': 0, 'atr_misses': 0,
            'kelly_hits': 0, 'kelly_misses': 0, 
            'position_hits': 0, 'position_misses': 0,
            'risk_hits': 0, 'risk_misses': 0
        }
        
        # 🆕 Очистка ордеров рисков
        self.active_orders = {
            'stop_loss': {},
            'take_profit': {},
            'trailing_stop': {},
            'break_even': {},
            'time_stop': {}
        }
        
        # Очистка истории сделок
        self.trade_history = []

    # 🆕 ДОБАВЛЯЕМ ОТСУТСТВУЮЩИЙ МЕТОД get_trade_history
    @with_error_handling
    def get_trade_history(self) -> pd.DataFrame:
        """Возвращает историю сделок в виде DataFrame"""
        if not self.trade_history:
            return pd.DataFrame()
        
        return pd.DataFrame(self.trade_history)

    # 🆕 ДОБАВЛЯЕМ ОТСУТСТВУЮЩИЙ МЕТОД get_performance_report
    @with_error_handling
    def get_performance_report(self) -> dict:
        """Отчет о производительности"""
        cache_stats = self.get_cache_stats()
        
        return {
            'calculation_time': self.performance_stats.get('calculation_time', 0),
            'cache_efficiency': cache_stats.get('overall_hit_ratio', 0),
            'vectorized_operations': self.performance_stats.get('vectorized_operations', 0),
            'total_trades': len(self.trade_history),
            'data_points_processed': getattr(self, '_data_points_processed', 0)
        }

    # 🆕 ДОБАВЛЯЕМ ОТСУТСТВУЮЩИЙ МЕТОД get_cache_stats
    @with_error_handling
    def get_cache_stats(self) -> dict:
        """Получить статистику кэширования для мониторинга производительности"""
        total_hits = (self._cache_stats['atr_hits'] + self._cache_stats['kelly_hits'] + 
                     self._cache_stats['position_hits'] + self._cache_stats['risk_hits'])
        total_misses = (self._cache_stats['atr_misses'] + self._cache_stats['kelly_misses'] + 
                       self._cache_stats['position_misses'] + self._cache_stats['risk_misses'])
        
        hit_ratio = total_hits / (total_hits + total_misses) if (total_hits + total_misses) > 0 else 0
        
        stats = {
            'cache_sizes': {
                'atr_cache': len(self._atr_cache),
                'kelly_cache': len(self._kelly_cache),
                'position_cache': len(self._position_size_cache),
                'risk_cache': len(self._risk_management_cache)
            },
            'hit_ratios': {
                'atr': self._cache_stats['atr_hits'] / (self._cache_stats['atr_hits'] + self._cache_stats['atr_misses']) if (self._cache_stats['atr_hits'] + self._cache_stats['atr_misses']) > 0 else 0,
                'kelly': self._cache_stats['kelly_hits'] / (self._cache_stats['kelly_hits'] + self._cache_stats['kelly_misses']) if (self._cache_stats['kelly_hits'] + self._cache_stats['kelly_misses']) > 0 else 0,
                'position': self._cache_stats['position_hits'] / (self._cache_stats['position_hits'] + self._cache_stats['position_misses']) if (self._cache_stats['position_hits'] + self._cache_stats['position_misses']) > 0 else 0,
                'risk': self._cache_stats['risk_hits'] / (self._cache_stats['risk_hits'] + self._cache_stats['risk_misses']) if (self._cache_stats['risk_hits'] + self._cache_stats['risk_misses']) > 0 else 0
            },
            'total_hits': total_hits,
            'total_misses': total_misses,
            'overall_hit_ratio': hit_ratio
        }
        
        return stats

    # 🆕 ДОБАВЛЯЕМ ОТСУТСТВУЮЩИЕ МЕТОДЫ ИЗ ИСХОДНОГО КОДА
    @with_error_handling
    def dynamic_risk_management(self, current_capital: float, 
                            peak_capital: float, 
                            base_risk: float = 0.01) -> float:
        """ИСПРАВЛЕННОЕ управление риском"""
        # УПРОЩЕННЫЙ ключ кэша
        cache_key = f"risk_{base_risk:.2f}"
        
        if hasattr(self, '_risk_management_cache') and cache_key in self._risk_management_cache:
            self._cache_stats['risk_hits'] += 1
            return self._risk_management_cache[cache_key]
        
        self._cache_stats['risk_misses'] += 1
        
        # ВАЖНО: Инициализируем переменную ДО любого использования
        adjusted_risk = base_risk
        
        # Расчет просадки (с защитой от деления на ноль)
        if peak_capital > 0 and current_capital > 0:
            drawdown = (peak_capital - current_capital) / peak_capital
        else:
            drawdown = 0
        
        # Логика корректировки риска
        if drawdown >= 0.10:  # Просадка >10%
            adjusted_risk = base_risk * 0.5
        elif drawdown >= 0.05:  # Просадка 5-10%
            adjusted_risk = base_risk * 0.7
        else:  # Просадка <5%
            adjusted_risk = base_risk * 1.0
        
        # Увеличение риска при росте капитала
        if current_capital > peak_capital * 1.05:
            adjusted_risk *= 1.2
        
        # Ограничения риска
        adjusted_risk = max(0.005, min(adjusted_risk, 0.05))
        
        # Сохраняем в кэш
        if not hasattr(self, '_risk_management_cache'):
            self._risk_management_cache = {}
        self._risk_management_cache[cache_key] = adjusted_risk
        
        return adjusted_risk

    @with_error_handling
    def multi_timeframe_signal(self, data: pd.DataFrame) -> pd.DataFrame:
        """СИГНАЛЫ НА НЕСКОЛЬКИХ ТАЙМФРЕЙМАХ - ОРИГИНАЛЬНАЯ ВЕРСИЯ"""
        # Оптимизированные периоды скользящих средних
        periods = {'fast': 10, 'slow': 30, 'trend': 50}
        
        for name, period in periods.items():
            data[f'ma_{name}'] = data['close'].rolling(period).mean()
            data[f'signal_{name}'] = (data['close'] > data[f'ma_{name}']).astype(int)
        
        # Комбинированный сигнал (большинство голосов)
        data['combined_signal'] = (
            data['signal_fast'] + data['signal_slow'] + data['signal_trend']
        ) >= 2
        
        # Сила тренда
        data['trend_strength'] = (
            (data['close'] > data['ma_slow']).astype(int) + 
            (data['ma_fast'] > data['ma_slow']).astype(int) +
            (data['ma_slow'] > data['ma_trend']).astype(int)
        )
        
        # Финальный сигнал с фильтром по силе тренда
        data['final_signal'] = (
            (data['combined_signal'] == True) & 
            (data['trend_strength'] >= 2)
        ).astype(int)
        
        # 🔥 ВАЖНО: Убедимся, что используется правильная колонка сигнала
        data['signal'] = data['final_signal']
        
        return data

    @with_error_handling
    def supertrend_strategy(self, data: pd.DataFrame, atr_period: int = 10, multiplier: float = 3.0) -> pd.DataFrame:
        """
        СТРАТЕГИЯ SUPER TREND - ОРИГИНАЛЬНАЯ ВЕРСИЯ
        """
        
        # Импортируем функцию расчета Super Trend
        from utils.supertrend import calculate_supertrend
        
        # Вызываем функцию расчета Super Trend
        data_with_supertrend = calculate_supertrend(data, atr_period, multiplier)
        
        # 🔧 ШАГ 2: ОБРАБОТКА NaN ЗНАЧЕНИЙ (КРИТИЧЕСКИ ВАЖНО!)
        
        if 'supertrend_direction' in data_with_supertrend.columns:
            # Проверяем количество NaN в направлении тренда
            nan_count_direction = data_with_supertrend['supertrend_direction'].isna().sum()
            
            # Заполняем NaN в направлении тренда
            first_valid_idx = data_with_supertrend['supertrend_direction'].first_valid_index()
            if first_valid_idx is not None:
                # Находим первое валидное значение направления
                first_valid_value = data_with_supertrend.loc[first_valid_idx, 'supertrend_direction']
                
                # Заполняем все NaN этим значением (forward fill)
                data_with_supertrend['supertrend_direction'] = data_with_supertrend['supertrend_direction'].fillna(first_valid_value)
            else:
                # Если ВСЕ значения NaN (крайний случай), используем направление 1 (восходящий тренд)
                data_with_supertrend['supertrend_direction'] = data_with_supertrend['supertrend_direction'].fillna(1)
        
        if 'supertrend_line' in data_with_supertrend.columns:
            # Проверяем количество NaN в линии Super Trend
            nan_count_line = data_with_supertrend['supertrend_line'].isna().sum()
            
            # Заполняем NaN в линии Super Trend
            first_valid_idx = data_with_supertrend['supertrend_line'].first_valid_index()
            if first_valid_idx is not None:
                # Находим первое валидное значение линии
                first_valid_value = data_with_supertrend.loc[first_valid_idx, 'supertrend_line']
                
                # Заполняем все NaN этим значением
                data_with_supertrend['supertrend_line'] = data_with_supertrend['supertrend_line'].fillna(first_valid_value)
            else:
                # Если ВСЕ значения NaN, используем цену закрытия как приближение
                data_with_supertrend['supertrend_line'] = data_with_supertrend['supertrend_line'].fillna(data_with_supertrend['close'])
        
        # 🔧 ШАГ 3: СОЗДАНИЕ ТОРГОВЫХ СИГНАЛОВ
        
        # Получаем направление Super Trend (теперь без NaN)
        supertrend_direction = data_with_supertrend['supertrend_direction']
        
        # Логика сигналов:
        # - Когда Super Trend меняется с -1 на 1 → ПОКУПКА (сигнал = 1)
        # - Когда Super Trend меняется с 1 на -1 → ПРОДАЖА (сигнал = 0)
        # - В остальное время → удерживаем текущую позицию
        
        signals = []
        current_position = 0  # 0 = нет позиции, 1 = лонг позиция
        
        for i in range(len(supertrend_direction)):
            current_direction = supertrend_direction.iloc[i]
            
            if i == 0:
                # Первый бар: устанавливаем начальную позицию
                # Если тренд восходящий (1) → покупаем, если нисходящий (-1) → выходим
                current_position = 1 if current_direction == 1 else 0
            else:
                previous_direction = supertrend_direction.iloc[i-1]
                
                # Проверяем смену направления тренда
                if current_direction != previous_direction:
                    # Смена направления → меняем позицию
                    if current_direction == 1:  
                        # Смена на восходящий тренд → ПОКУПКА
                        current_position = 1
                    else:  
                        # Смена на нисходящий тренд → ПРОДАЖА/ВЫХОД
                        current_position = 0
                # Если направление не изменилось → сохраняем текущую позицию
            
            signals.append(current_position)
        
        # 🔧 ШАГ 4: СОХРАНЕНИЕ РЕЗУЛЬТАТОВ
        
        # Основной торговый сигнал (0 или 1)
        data['signal'] = signals
        
        # Сохраняем данные Super Trend для отображения на графиках
        data['supertrend_direction'] = data_with_supertrend['supertrend_direction']
        data['supertrend_line'] = data_with_supertrend['supertrend_line']
        
        # ✅ ГАРАНТИЯ: Сохраняем Super Trend данные в ОСНОВНОЙ DataFrame
        # Это критически важно для отображения на графиках!
        data['supertrend_direction'] = data_with_supertrend['supertrend_direction']
        data['supertrend_line'] = data_with_supertrend['supertrend_line']
        
        return data
    
    # 🆕 ДОБАВЛЯЕМ ОТСУТСТВУЮЩИЙ МЕТОД calculate_atr
    @with_error_handling
    def calculate_atr(self, data: pd.DataFrame, period: int = 14) -> pd.Series:
        """ATR с УПРОЩЕННЫМИ ключами кэша"""
        # УПРОЩЕННЫЙ ключ - только период
        cache_key = f"atr_{period}"
        
        if hasattr(self, '_atr_cache') and cache_key in self._atr_cache:
            self._cache_stats['atr_hits'] += 1
            return self._atr_cache[cache_key]
        
        self._cache_stats['atr_misses'] += 1
        
        # Расчет ATR
        high = data['high'] if 'high' in data.columns else data['close']
        low = data['low'] if 'low' in data.columns else data['close']
        close = data['close']

        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(period, min_periods=1).mean()
        
        # Инициализация кэша если нужно
        if not hasattr(self, '_atr_cache'):
            self._atr_cache = {}
        
        # Сохраняем в кэш
        self._atr_cache[cache_key] = atr
        return atr

    # 🆕 ДОБАВЛЯЕМ ОТСУТСТВУЮЩИЙ МЕТОД calculate_position_size
    @with_error_handling
    def calculate_position_size(self, f: float, current_price: float,
                            atr: float = None, risk_per_trade: float = 0.01) -> float:
        """
        ОПТИМИЗИРОВАННЫЙ расчет размера позиции с кэшированием
        """
        # 🔒 Инициализация кэша если нужно
        if not hasattr(self, '_position_size_cache'):
            self._position_size_cache = {}
        
        try:
            # Создаем ключ кэша
            atr_value = atr if atr is not None else 0.0
            cache_key = f"pos_{f:.4f}_{current_price:.4f}_{atr_value:.4f}_{risk_per_trade:.4f}"
            
            # Проверяем кэш
            if cache_key in self._position_size_cache:
                self._cache_stats['position_hits'] += 1
                return self._position_size_cache[cache_key]
            
            self._cache_stats['position_misses'] += 1
            
            # 🔒 ЗАЩИТА: проверка входных данных
            if (not np.isfinite(f) or not np.isfinite(current_price) or 
                not np.isfinite(risk_per_trade)):
                result = 0.0
                self._position_size_cache[cache_key] = result
                return result
            
            if f <= 0 or current_price <= 0 or risk_per_trade <= 0:
                result = 0.0
                self._position_size_cache[cache_key] = result
                return result
                
            if self.current_capital <= 0:
                result = 0.0
                self._position_size_cache[cache_key] = result
                return result
            
            # Размер по Келли
            kelly_amount = self.current_capital * f
            
            # Размер по риску на сделку
            risk_amount = self.current_capital * risk_per_trade

            # Корректировка на волатильность через ATR
            if atr is not None and atr > 0:
                stop_loss_pct = (2 * atr) / current_price
                if stop_loss_pct > 0:
                    volatility_position = risk_amount / stop_loss_pct
                    position_size = min(kelly_amount, volatility_position)
                else:
                    position_size = min(kelly_amount, risk_amount * 5)
            else:
                position_size = min(kelly_amount, risk_amount * 3)

            # Ограничения размера позиции
            position_size = min(position_size, self.current_capital * 0.25)
            position_size = max(position_size, self.current_capital * 0.01)

            # 🔒 ФИНАЛЬНАЯ ПРОВЕРКА КОРРЕКТНОСТИ
            if (not np.isfinite(position_size) or 
                position_size <= 0 or 
                position_size > self.current_capital):
                position_size = min(kelly_amount, risk_amount * 3)

            # Сохраняем в кэш
            self._position_size_cache[cache_key] = position_size
            
            # Очистка старого кэша
            if len(self._position_size_cache) > 50:
                oldest_key = next(iter(self._position_size_cache))
                del self._position_size_cache[oldest_key]
            
            return position_size
            
        except Exception as e:
            return 0.0

    # 🆕 ДОБАВЛЯЕМ ОТСУТСТВУЮЩИЙ МЕТОД calculate_kelly_fraction
    @with_error_handling
    def calculate_kelly_fraction(self, trades: List[float]) -> float:
        """
        ОПТИМИЗИРОВАННЫЙ расчет оптимальной доли f по формуле Келли с кэшированием
        """
        # 🔒 Инициализация кэша если нужно
        if not hasattr(self, '_kelly_cache'):
            self._kelly_cache = {}
        
        if not trades or len(trades) < 5:
            return 0.1
        
        try:
            # Создаем ключ кэша
            trades_array = np.array(trades)
            cache_key = f"kelly_{len(trades)}_{np.mean(trades):.6f}_{np.std(trades):.6f}"
            
            if cache_key in self._kelly_cache:
                self._cache_stats['kelly_hits'] += 1
                return self._kelly_cache[cache_key]
            
            self._cache_stats['kelly_misses'] += 1
            
            # Фильтрация выбросов (3 сигма)
            if len(trades_array) > 10:
                std = np.std(trades_array)
                mean = np.mean(trades_array)
                if std > 0:
                    trades_array = trades_array[
                        (trades_array >= mean - 3*std) & 
                        (trades_array <= mean + 3*std)
                    ]

            winning_trades = trades_array[trades_array > 0]
            losing_trades = trades_array[trades_array < 0]

            if len(winning_trades) == 0 or len(losing_trades) == 0:
                result = 0.1
                self._kelly_cache[cache_key] = result
                return result

            # Базовая формула Келли
            p = len(winning_trades) / len(trades_array)
            avg_win = np.mean(winning_trades)
            avg_loss = abs(np.mean(losing_trades))

            if avg_loss < 0.001 or avg_win < 0.001:
                result = 0.1
                self._kelly_cache[cache_key] = result
                return result

            win_loss_ratio = avg_win / avg_loss
            kelly_f = p - (1 - p) / win_loss_ratio

            # Альтернативный расчет через mean/variance
            mean_return = np.mean(trades_array)
            std_return = np.std(trades_array)
            
            kelly_f_alt = mean_return / (std_return ** 2) if std_return > 0.001 else 0.1

            # Консервативный подход
            kelly_f = min(kelly_f, kelly_f_alt) if kelly_f_alt > 0 else kelly_f
            
            # Ограничения и дробное применение
            kelly_f = max(0.01, min(kelly_f, 0.25))
            fractional_f = kelly_f * 0.25

            # Сохраняем в кэш
            self._kelly_cache[cache_key] = fractional_f
            
            # Очистка старого кэша
            if len(self._kelly_cache) > 20:
                oldest_key = next(iter(self._kelly_cache))
                del self._kelly_cache[oldest_key]
            
            return fractional_f
            
        except Exception as e:
            return 0.1    
        
    # 🆕 НОВЫЙ МЕТОД: Обновление параметров риска с поддержкой отключения
    @with_error_handling
    def update_risk_parameters(self, **kwargs):
        """
        Обновление параметров управления рисками
        
        Parameters:
        -----------
        **kwargs
            Параметры для обновления
        """
        valid_params = [
            'stop_loss_atr_multiplier', 'take_profit_atr_multiplier',
            'trailing_stop_enabled', 'trailing_stop_atr_multiplier',
            'break_even_stop', 'break_even_atr_threshold',
            'max_position_risk', 'time_stop_days', 'risk_management_enabled'
        ]
        
        for key, value in kwargs.items():
            if key in valid_params:
                if key == 'risk_management_enabled':
                    self.risk_management_enabled = value
                else:
                    self.risk_params[key] = value


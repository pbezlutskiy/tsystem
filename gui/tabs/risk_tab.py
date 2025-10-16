# ===== СЕКЦИЯ: ВКЛАДКА ВИЗУАЛИЗАЦИИ РИСК-МЕНЕДЖМЕНТА =====
"""
Оптимизированная вкладка для отображения стоп-лоссов, тейк-профитов и анализа рисков
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional

from gui.components import PlotFrame

class RiskTab:
    """Оптимизированная вкладка визуализации рисков и ордеров"""
    
    # Кэш переводов для быстрого доступа
    REASON_TRANSLATIONS = {
        'stop_loss': 'Стоп-лосс',
        'take_profit': 'Тейк-профит', 
        'trailing_stop': 'Трейлинг-стоп',
        'time_stop': 'Временной стоп',
        'signal_sell': 'Сигнал продажи',
        'signal_buy': 'Сигнал покупки'
    }
    
    # Цвета для типов выходов
    REASON_COLORS = {
        'stop_loss': 'red',
        'take_profit': 'green',
        'trailing_stop': 'orange',
        'time_stop': 'purple',
        'signal_sell': 'blue',
        'signal_buy': 'cyan'
    }
    
    def __init__(self, parent, visualizer):
        self.parent = parent
        self.visualizer = visualizer
        self._current_figure = None
        self.setup_ui()
    
    def setup_ui(self):
        """Быстрая настройка пользовательского интерфейса"""
        self.frame = ttk.Frame(self.parent)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        
        self.plot_frame = PlotFrame(self.frame)
        self.plot_frame.grid(row=0, column=0, sticky="nsew")
        self.plot_frame.show_placeholder("Запустите тест с включенным risk management для отображения данных")
    
    def get_frame(self):
        """Возвращает фрейм вкладки"""
        return self.frame
    
    def update_plot(self, result_name: str):
        """Оптимизированное обновление графика рисков и ордеров"""
        # Быстрая проверка наличия данных
        if not self._validate_data_availability(result_name):
            return
        
        try:
            data = self.visualizer.results_history[result_name]['results']
            
            # Создаем комплексный график рисков
            fig = self._create_risk_analysis_plot(data)
            if fig:
                self.plot_frame.show_plot(fig)
                if self._current_figure:
                    plt.close(self._current_figure)  # Освобождаем память
                self._current_figure = fig
                
        except Exception as e:
            self.plot_frame.show_placeholder(f"Ошибка построения графика: {str(e)}")
    
    def _validate_data_availability(self, result_name: str) -> bool:
        """Быстрая валидация доступности данных"""
        if result_name not in self.visualizer.results_history:
            self.plot_frame.show_placeholder("Результат не найден")
            return False
        
        data = self.visualizer.results_history[result_name]['results']
        
        # Проверяем наличие критических колонок
        required_columns = ['stop_loss_level', 'take_profit_level']
        if not all(col in data.columns for col in required_columns):
            self.plot_frame.show_placeholder(
                "Данные о рисках не найдены. Запустите тест с включенным risk management"
            )
            return False
            
        return True
    
    def _create_risk_analysis_plot(self, data: pd.DataFrame) -> Optional[plt.Figure]:
        """Создание оптимизированного графика анализа рисков"""
        try:
            fig, axes = plt.subplots(2, 2, figsize=(14, 10))
            ((ax1, ax2), (ax3, ax4)) = axes
            
            # График 1: Цены с уровнями риска (оптимизированный)
            self._plot_price_with_risk_levels(ax1, data)
            
            # График 2: Причины выхода из позиций
            self._plot_exit_reasons(ax2, data)
            
            # График 3: Эффективность системы рисков
            self._plot_risk_efficiency(ax3, data)
            
            # График 4: Распределение расстояний до стоп-лосса
            self._plot_stop_loss_distances(ax4, data)
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"Ошибка создания графика рисков: {e}")
            return None
    
    def _plot_price_with_risk_levels(self, ax, data: pd.DataFrame):
        """Оптимизированный график цен с уровнями риска"""
        ax.plot(data.index, data['close'], label='Цена закрытия', 
                color='black', linewidth=1, alpha=0.8)
        
        # Векторизованная обработка стоп-лоссов
        valid_stops = data[data['stop_loss_level'] > 0]
        if not valid_stops.empty:
            ax.scatter(valid_stops.index, valid_stops['stop_loss_level'], 
                      color='red', s=15, alpha=0.6, label='Стоп-лосс', zorder=5)
        
        # Векторизованная обработка тейк-профитов
        valid_take_profits = data[data['take_profit_level'] > 0]
        if not valid_take_profits.empty:
            ax.scatter(valid_take_profits.index, valid_take_profits['take_profit_level'], 
                      color='green', s=15, alpha=0.6, label='Тейк-профит', zorder=5)
        
        ax.set_title('Цены с уровнями риска', fontsize=12, fontweight='bold')
        ax.set_ylabel('Цена ($)')
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    def _plot_exit_reasons(self, ax, data: pd.DataFrame):
        """Оптимизированный график причин выхода"""
        if 'exit_reason' in data.columns:
            exit_reasons = data[data['exit_reason'] != '']['exit_reason']
            if not exit_reasons.empty:
                reason_counts = exit_reasons.value_counts()
                
                # Используем предопределенные цвета
                bar_colors = [self.REASON_COLORS.get(reason, 'gray') 
                            for reason in reason_counts.index]
                
                bars = ax.bar(range(len(reason_counts)), reason_counts.values, 
                             color=bar_colors, alpha=0.7)
                
                ax.set_title('Причины выхода из позиций', fontsize=12, fontweight='bold')
                ax.set_ylabel('Количество')
                ax.set_xticks(range(len(reason_counts)))
                ax.set_xticklabels([self._translate_reason(r) for r in reason_counts.index], 
                                 rotation=45, ha='right')
                
                # Быстрое добавление значений
                for bar, count in zip(bars, reason_counts.values):
                    ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.1,
                           f'{count}', ha='center', va='bottom', fontsize=9)
    
    def _plot_risk_efficiency(self, ax, data: pd.DataFrame):
        """Оптимизированный график эффективности рисков"""
        if 'exit_reason' in data.columns and 'pnl_percent' in data.columns:
            exit_data = data[data['exit_reason'] != '']
            if not exit_data.empty:
                # Векторизованная группировка
                reasons_pnl = exit_data.groupby('exit_reason')['pnl_percent'].agg(['mean', 'count'])
                valid_reasons = reasons_pnl[reasons_pnl['count'] >= 3]
                
                if not valid_reasons.empty:
                    colors = ['green' if x >= 0 else 'red' for x in valid_reasons['mean']]
                    bars = ax.bar(range(len(valid_reasons)), valid_reasons['mean'], 
                                 color=colors, alpha=0.7)
                    
                    ax.set_title('Средний PnL по причинам выхода', fontsize=12, fontweight='bold')
                    ax.set_ylabel('Средний PnL (%)')
                    ax.set_xticks(range(len(valid_reasons)))
                    ax.set_xticklabels([self._translate_reason(r) for r in valid_reasons.index], 
                                     rotation=45, ha='right')
                    ax.axhline(y=0, color='black', linestyle='-', alpha=0.5)
                    
                    # Быстрое добавление значений
                    for bar, value in zip(bars, valid_reasons['mean']):
                        va_pos = 'bottom' if value >= 0 else 'top'
                        y_offset = 0.1 if value >= 0 else -0.3
                        ax.text(bar.get_x() + bar.get_width()/2, value + y_offset,
                               f'{value:.1f}%', ha='center', va=va_pos, fontsize=9)
    
    def _plot_stop_loss_distances(self, ax, data: pd.DataFrame):
        """Оптимизированный график распределения расстояний до стоп-лосса"""
        if 'stop_loss_level' in data.columns and 'close' in data.columns:
            active_positions = data[data['stop_loss_level'] > 0]
            if not active_positions.empty:
                # Векторизованный расчет расстояний
                stop_distances = self._calculate_stop_distances(active_positions)
                
                if stop_distances:
                    ax.hist(stop_distances, bins=min(20, len(stop_distances)), 
                           alpha=0.7, color='orange', edgecolor='black')
                    ax.set_title('Распределение расстояний до стоп-лосса', 
                               fontsize=12, fontweight='bold')
                    ax.set_xlabel('Расстояние до стопа (%)')
                    ax.set_ylabel('Частота')
                    
                    mean_distance = np.mean(stop_distances)
                    ax.axvline(x=mean_distance, color='red', linestyle='--',
                             label=f'Среднее: {mean_distance:.2f}%')
                    ax.legend()
                    ax.grid(True, alpha=0.3)
    
    def _calculate_stop_distances(self, positions: pd.DataFrame) -> list:
        """Быстрый расчет расстояний до стоп-лосса"""
        distances = []
        for _, row in positions.iterrows():
            if row['position_type'] == 1:  # LONG
                distance = (row['close'] - row['stop_loss_level']) / row['close'] * 100
            elif row['position_type'] == -1:  # SHORT
                distance = (row['stop_loss_level'] - row['close']) / row['close'] * 100
            else:
                continue
            distances.append(distance)
        return distances
    
    def _translate_reason(self, reason: str) -> str:
        """Быстрый перевод причин выхода (использует кэш)"""
        return self.REASON_TRANSLATIONS.get(reason, reason)
    
    def cleanup(self):
        """Очистка ресурсов"""
        if self._current_figure:
            plt.close(self._current_figure)
            self._current_figure = None
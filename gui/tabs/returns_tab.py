# ===== СЕКЦИЯ 10: ВКЛАДКА ДОХОДНОСТЕЙ И СТАТИСТИКИ =====
"""
Вкладка для анализа распределения доходностей и кумулятивной доходности
Статистический анализ торговых результатов
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import numpy as np
from gui.components import PlotFrame

class ReturnsTab:
    """Вкладка доходностей и статистики"""
    
    def __init__(self, parent, visualizer):
        self.parent = parent
        self.visualizer = visualizer
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.frame = ttk.Frame(self.parent)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        
        self.plot_frame = PlotFrame(self.frame)
        self.plot_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def get_frame(self):
        """Возвращает фрейм вкладки"""
        return self.frame
    
    def update_plot(self, result_name: str):
        """Обновить график доходностей"""
        if result_name not in self.visualizer.results_history:
            self.plot_frame.show_placeholder("Результат не найден")
            return
        
        data = self.visualizer.results_history[result_name]['results']
        
        # Расчет доходностей
        daily_returns = data['capital'].pct_change().dropna() * 100
        cumulative_return = (data['capital'] / data['capital'].iloc[0] - 1) * 100
        
        # Создание комплексного графика
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
        
        # График 1: Кумулятивная доходность
        ax1.plot(data.index, cumulative_return, 
                label='Кумулятивная доходность', color='blue', linewidth=2)
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        # Отметка финальной доходности
        final_return = cumulative_return.iloc[-1]
        ax1.scatter(data.index[-1], final_return, color='green' if final_return >= 0 else 'red', 
                s=100, label=f'Финальная: {final_return:.2f}%', zorder=5)
        
        ax1.set_title('Кумулятивная доходность', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Доходность (%)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # График 2: Распределение дневных доходностей
        n, bins, patches = ax2.hist(daily_returns, bins=50, alpha=0.7, 
                                color='skyblue', edgecolor='black', density=True)
        
        # Раскраска столбцов
        for i in range(len(patches)):
            if bins[i] < 0:
                patches[i].set_facecolor('lightcoral')
            else:
                patches[i].set_facecolor('lightgreen')
        
        # Статистические линии
        mean_return = daily_returns.mean()
        std_return = daily_returns.std()
        
        ax2.axvline(mean_return, color='red', linestyle='--', 
                label=f'Среднее: {mean_return:.3f}%')
        ax2.axvline(mean_return + std_return, color='orange', linestyle=':', 
                label=f'+1σ: {mean_return + std_return:.3f}%')
        ax2.axvline(mean_return - std_return, color='orange', linestyle=':', 
                label=f'-1σ: {mean_return - std_return:.3f}%')
        ax2.axvline(0, color='black', linestyle='-', alpha=0.5)
        
        ax2.set_title('Распределение дневных доходностей', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Доходность (%)')
        ax2.set_ylabel('Плотность вероятности')
        ax2.legend(fontsize=8)
        ax2.grid(True, alpha=0.3)
        
        # График 3: Накопительная гистограмма доходностей
        sorted_returns = np.sort(daily_returns)
        cdf = np.arange(1, len(sorted_returns) + 1) / len(sorted_returns)
        
        ax3.plot(sorted_returns, cdf, color='purple', linewidth=2)
        ax3.set_title('Кумулятивное распределение доходностей', fontsize=12, fontweight='bold')
        ax3.set_xlabel('Доходность (%)')
        ax3.set_ylabel('Вероятность')
        ax3.grid(True, alpha=0.3)
        ax3.axvline(x=0, color='black', linestyle='-', alpha=0.5)
        
        # График 4: Scatter plot временного ряда доходностей - САМЫЙ ПРОСТОЙ ВАРИАНТ
        if len(daily_returns) > 0:
            returns_data = daily_returns.replace([np.inf, -np.inf], np.nan).dropna()
            
            if len(returns_data) > 0:
                # SCATTER PLOT - точки доходностей по времени
                colors = ['green' if x >= 0 else 'red' for x in returns_data]
                ax4.scatter(returns_data.index, returns_data.values, c=colors, alpha=0.6, s=20)
                
                # Линия нулевой доходности
                ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)
                
                # Скользящее среднее для тренда
                if len(returns_data) > 5:
                    rolling_mean = returns_data.rolling(window=5).mean()
                    ax4.plot(rolling_mean.index, rolling_mean.values, color='blue', linewidth=2, label='Скользящее среднее (5)')
                    ax4.legend()
                
                # Статистика
                stats_text = f'Положительных: {len(returns_data[returns_data >= 0])}\n'
                stats_text += f'Отрицательных: {len(returns_data[returns_data < 0])}\n'
                stats_text += f'Соотношение: {len(returns_data[returns_data >= 0])/len(returns_data)*100:.1f}%'
                
                ax4.text(0.02, 0.98, stats_text, transform=ax4.transAxes, verticalalignment='top',
                        bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8),
                        fontsize=9)
                
                ax4.set_ylabel('Доходность (%)')
                ax4.set_xlabel('Дата')
                
            else:
                ax4.text(0.5, 0.5, 'Нет данных для анализа', 
                        ha='center', va='center', transform=ax4.transAxes,
                        fontsize=12, color='gray')
                ax4.set_ylabel('Доходность (%)')
        else:
            ax4.text(0.5, 0.5, 'Нет данных для анализа', 
                    ha='center', va='center', transform=ax4.transAxes,
                    fontsize=12, color='gray')
            ax4.set_ylabel('Доходность (%)')

        ax4.set_title('Дневные доходности по времени', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3)

        ax4.set_title('Плотность распределения доходностей', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)

        ax4.set_title('Распределение доходностей (Box Plot)', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        ax4.axhline(y=0, color='black', linestyle='-', alpha=0.5)
        
        ax4.set_title('Box Plot дневных доходностей', fontsize=12, fontweight='bold')
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        self.plot_frame.show_plot(fig)
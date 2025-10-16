# ===== СЕКЦИЯ 8: ВКЛАДКА КАПИТАЛА И ПРОСАДКИ =====
"""
Вкладка для отображения динамики капитала и просадки
Анализ эффективности управления капиталом
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from gui.components import PlotFrame

class CapitalTab:
    """Вкладка капитала и просадки"""
    
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
        """Обновить график капитала и просадки"""
        if result_name not in self.visualizer.results_history:
            self.plot_frame.show_placeholder("Результат не найден")
            return
        
        data = self.visualizer.results_history[result_name]['results']
        perf = self.visualizer.results_history[result_name]['performance']
        
        # Создание графика с двумя осями Y
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # График 1: Динамика капитала
        ax1.plot(data.index, data['capital'], label='Капитал', color='green', linewidth=2)
        ax1.axhline(y=perf.get('initial_capital', 100000), color='red', linestyle='--', 
                   label='Начальный капитал', alpha=0.7)
        
        # Отметка максимального капитала
        max_capital = data['capital'].max()
        max_capital_idx = data['capital'].idxmax()
        ax1.scatter(max_capital_idx, max_capital, color='gold', s=100, 
                   label=f'Макс. капитал: ${max_capital:,.0f}', zorder=5)
        
        ax1.set_title('Динамика капитала', fontsize=12, fontweight='bold')
        ax1.set_ylabel('Капитал ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # График 2: Просадка
        if 'drawdown' in data.columns:
            ax2.fill_between(data.index, 0, data['drawdown'] * 100, 
                           alpha=0.3, color='red', label='Просадка')
            
            # Отметка максимальной просадки
            max_dd = data['drawdown'].max() * 100
            max_dd_idx = data['drawdown'].idxmax()
            ax2.scatter(max_dd_idx, max_dd, color='darkred', s=100, 
                       label=f'Макс. просадка: {max_dd:.1f}%', zorder=5)
            
            ax2.axhline(y=0, color='black', linestyle='-', alpha=0.5)
            
            ax2.set_title('Динамика просадки', fontsize=12, fontweight='bold')
            ax2.set_xlabel('Дата')
            ax2.set_ylabel('Просадка (%)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            ax2.set_ylim(bottom=0)
        
        plt.tight_layout()
        self.plot_frame.show_plot(fig)
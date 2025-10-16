# ===== СЕКЦИЯ 9: ВКЛАДКА ПОЗИЦИЙ И УПРАВЛЕНИЯ РИСКАМИ =====
"""
Вкладка для отображения размера позиций и управления рисками
Визуализация параметров Келли и уровней риска
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import numpy as np

from gui.components import PlotFrame

class PositionTab:
    """Вкладка позиций и управления рисками"""
    
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
        """Обновить график позиций и рисков с улучшенной диагностикой"""
        if result_name not in self.visualizer.results_history:
            self.plot_frame.show_placeholder("Результат не найден")
            return
        
        data = self.visualizer.results_history[result_name]['results']
        
        # Создание графика с несколькими осями Y
        fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 10))
        
        # График 1: Размер позиции
        if 'position_size' in data.columns:
            ax1.plot(data.index, data['position_size'], 
                    label='Размер позиции', color='purple', linewidth=2)
            ax1.fill_between(data.index, 0, data['position_size'], 
                        alpha=0.3, color='purple')
            
            ax1.set_title('Размер торговой позиции', fontsize=12, fontweight='bold')
            ax1.set_ylabel('Размер позиции ($)')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
        
        # График 2: Параметр Келли f (ИСПРАВЛЕННЫЙ)
        if 'kelly_f' in data.columns:
            kelly_clean = data['kelly_f'].replace([np.inf, -np.inf], np.nan).fillna(0.1)
            kelly_clean = np.clip(kelly_clean, 0.001, 0.5)  # Ограничиваем разумные значения
            
            ax2.plot(data.index, kelly_clean * 100, 
                    label='Доля Келли f (%)', color='blue', linewidth=2)
            
            # Среднее значение
            avg_f = kelly_clean.mean() * 100
            ax2.axhline(y=avg_f, color='red', linestyle='--', 
                    label=f'Среднее: {avg_f:.2f}%', alpha=0.7)
            
            # Ограничения оси Y для читаемости
            ax2.set_ylim(0, 20)  # 0-20% для лучшей визуализации
            
            ax2.set_title('Динамика параметра Келли f', fontsize=12, fontweight='bold')
            ax2.set_ylabel('Доля Келли f (%)')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
        
        # График 3: Уровень риска
        if 'risk_level' in data.columns:
            risk_clean = data['risk_level'].replace([np.inf, -np.inf], np.nan).fillna(0.01)
            risk_clean = np.clip(risk_clean, 0.001, 0.1)
            
            ax3.plot(data.index, risk_clean * 100, 
                    label='Уровень риска', color='orange', linewidth=2)
            
            # Динамика риска
            risk_changes = data[data['risk_level'] != data['risk_level'].shift()]
            if not risk_changes.empty:
                risk_changes_clean = risk_changes['risk_level'].replace([np.inf, -np.inf], np.nan).fillna(0.01)
                ax3.scatter(risk_changes.index, risk_changes_clean * 100, 
                        color='red', s=50, label='Корректировки риска', zorder=5)
            
            ax3.set_title('Динамика уровня риска', fontsize=12, fontweight='bold')
            ax3.set_xlabel('Дата')
            ax3.set_ylabel('Риск (%)')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        
        plt.tight_layout()
        self.plot_frame.show_plot(fig)
        

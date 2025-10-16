# ===== СЕКЦИЯ 13: ВКЛАДКА СТАТИСТИКИ =====
"""
Вкладка для отображения детальной статистики производительности
Текстовое представление всех ключевых метрик системы
"""

import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from gui.components import StatsTextFrame

class StatsTab:
    """Вкладка статистики производительности"""
    
    def __init__(self, parent, visualizer):
        self.parent = parent
        self.visualizer = visualizer
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.frame = ttk.Frame(self.parent)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        
        self.stats_text = StatsTextFrame(self.frame)
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.stats_text.set_placeholder("Запустите тест для отображения статистики")
    
    def get_frame(self):
        """Возвращает фрейм вкладки"""
        return self.frame
    
    def update_stats(self, result_name: str):
        """Обновить статистику"""
        if result_name not in self.visualizer.results_history:
            self.stats_text.set_text("Результат не найден")
            return
        
        # Получение детальной статистики из визуализатора
        stats = self.visualizer.get_detailed_stats(result_name)
        self.stats_text.set_text(stats)
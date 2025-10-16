# ===== СЕКЦИЯ 14: ВКЛАДКА СРАВНЕНИЯ РЕЗУЛЬТАТОВ =====
"""
Вкладка для сравнительного анализа нескольких тестов
Визуализация производительности разных стратегий
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from gui.components import PlotFrame

class CompareTab:
    """Вкладка сравнения результатов"""
    
    def __init__(self, parent, visualizer):
        self.parent = parent
        self.visualizer = visualizer
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.frame = ttk.Frame(self.parent)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)
        
        # Панель выбора результатов для сравнения
        self.setup_control_panel()
        
        self.plot_frame = PlotFrame(self.frame)
        self.plot_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(10, 0))
        self.plot_frame.show_placeholder("Выберите результаты для сравнения")
    
    def setup_control_panel(self):
        """Настройка панели управления сравнением"""
        control_frame = ttk.Frame(self.frame)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        ttk.Label(control_frame, text="Выберите результаты для сравнения (макс. 4):").grid(
            row=0, column=0, sticky=tk.W, padx=(0, 10))
        
        # Фрейм для чекбоксов
        self.checkboxes_frame = ttk.Frame(control_frame)
        self.checkboxes_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        
        # Кнопка обновления
        self.update_btn = ttk.Button(control_frame, text="🔄 Обновить сравнение", 
                                   command=self.update_comparison)
        self.update_btn.grid(row=0, column=2, padx=(10, 0))
        
        self.checkbox_vars = {}
        self.checkboxes = {}
    
    def get_frame(self):
        """Возвращает фрейм вкладки"""
        return self.frame
    
    def update_available_results(self):
        """Обновить список доступных результатов"""
        # Очистка предыдущих чекбоксов
        for widget in self.checkboxes_frame.winfo_children():
            widget.destroy()
        
        self.checkbox_vars = {}
        self.checkboxes = {}
        
        available_results = self.visualizer.get_available_results()
        
        if not available_results:
            ttk.Label(self.checkboxes_frame, text="Нет доступных результатов", 
                     foreground='gray').grid(row=0, column=0)
            return
        
        # Создание чекбоксов для каждого результата
        for i, result_name in enumerate(available_results[:6]):  # Ограничение до 6 результатов
            var = tk.BooleanVar()
            cb = ttk.Checkbutton(self.checkboxes_frame, text=result_name, 
                               variable=var)
            cb.grid(row=0, column=i, padx=(10, 0))
            
            self.checkbox_vars[result_name] = var
            self.checkboxes[result_name] = cb
    
    def get_selected_results(self):
        """Получить список выбранных результатов"""
        selected = []
        for result_name, var in self.checkbox_vars.items():
            if var.get():
                selected.append(result_name)
        return selected[:4]  # Ограничение до 4 результатов
    
    def update_comparison(self):
        """Обновить график сравнения"""
        selected_results = self.get_selected_results()
        
        if not selected_results:
            self.plot_frame.show_placeholder("Выберите хотя бы один результат для сравнения")
            return
        
        if len(selected_results) == 1:
            self.plot_frame.show_placeholder("Для сравнения выберите минимум 2 результата")
            return
        
        # Построение графика сравнения
        fig = self.visualizer.plot_comparison_chart(selected_results)
        if fig:
            self.plot_frame.show_plot(fig)
# ===== СЕКЦИЯ 6: ОБЩИЕ КОМПОНЕНТЫ ГРАФИЧЕСКОГО ИНТЕРФЕЙСА =====
"""
Общие компоненты GUI для повторного использования
Стилизованные элементы управления
"""

import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
from typing import Callable, Optional

class StyledButton(ttk.Button):
    """Стилизованная кнопка с предустановленными настройками"""
    
    def __init__(self, parent, text: str, command: Callable, 
                 style: str = 'Accent.TButton', **kwargs):
        super().__init__(parent, text=text, command=command, style=style, **kwargs)

class LabeledEntry(ttk.Frame):
    """Поле ввода с меткой"""
    
    def __init__(self, parent, label_text: str, textvariable: tk.Variable, 
                 width: int = 20, **kwargs):
        super().__init__(parent, **kwargs)
        
        ttk.Label(self, text=label_text).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Entry(self, textvariable=textvariable, width=width).pack(side=tk.LEFT, fill=tk.X, expand=True)

class FileBrowser(ttk.Frame):
    """Компонент выбора файла с кнопкой обзора"""
    
    def __init__(self, parent, textvariable: tk.StringVar, 
                 filetypes: list = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.textvariable = textvariable
        self.filetypes = filetypes or [("CSV files", "*.csv"), ("All files", "*.*")]
        
        self.entry = ttk.Entry(self, textvariable=textvariable)
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.browse_btn = ttk.Button(self, text="Обзор", command=self._browse_file)
        self.browse_btn.pack(side=tk.RIGHT, padx=(5, 0))
    
    def _browse_file(self):
        """Открыть диалог выбора файла"""
        filename = tk.filedialog.askopenfilename(
            title="Выберите файл с данными",
            filetypes=self.filetypes
        )
        if filename:
            self.textvariable.set(filename)

class ResultsComboBox(ttk.Frame):
    """Комбинированный список для выбора результатов"""
    
    def __init__(self, parent, textvariable: tk.StringVar, 
                 on_select: Optional[Callable] = None, **kwargs):
        super().__init__(parent, **kwargs)
        
        ttk.Label(self, text="Выберите результат:").pack(anchor=tk.W)
        
        self.combobox = ttk.Combobox(self, textvariable=textvariable, state="readonly")
        self.combobox.pack(fill=tk.X, pady=2)
        
        if on_select:
            self.combobox.bind('<<ComboboxSelected>>', on_select)
    
    def update_values(self, values: list):
        """Обновить список значений"""
        self.combobox['values'] = values
        if values:
            self.combobox.set(values[-1])

class PlotFrame(ttk.Frame):
    """Фрейм для отображения графиков matplotlib"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        # Placeholder при инициализации
        self.placeholder = ttk.Label(self, text="Запустите тест для отображения графиков",
                                   font=('Arial', 12), foreground='gray')
        self.placeholder.grid(row=0, column=0)
        
        self.current_canvas = None
    
    def show_plot(self, fig):
        """Отобразить график matplotlib"""
        # Очистить предыдущий график
        self.clear_plot()
        
        # Создать новый canvas
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(fig, self)
        canvas.draw()
        canvas.get_tk_widget().grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.current_canvas = canvas
    
    def clear_plot(self):
        """Очистить текущий график"""
        if self.current_canvas:
            self.current_canvas.get_tk_widget().destroy()
            self.current_canvas = None
        
        # Скрыть placeholder
        self.placeholder.grid_remove()
    
    def show_placeholder(self, text: str = None):
        """Показать placeholder текст"""
        self.clear_plot()
        if text:
            self.placeholder.config(text=text)
        self.placeholder.grid()

class StatsTextFrame(ttk.Frame):
    """Текстовый фрейм для отображения статистики"""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        
        self.text_widget = scrolledtext.ScrolledText(self, wrap=tk.WORD, 
                                           font=('Consolas', 10),
                                           height=20)
        self.text_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.set_placeholder()
    
    def set_text(self, text: str):
        """Установить текст"""
        self.text_widget.config(state=tk.NORMAL)
        self.text_widget.delete(1.0, tk.END)
        self.text_widget.insert(tk.END, text)
        self.text_widget.config(state=tk.DISABLED)
    
    def set_placeholder(self, text: str = "Статистика будет отображена здесь после запуска теста"):
        """Установить placeholder текст"""
        self.set_text(text)
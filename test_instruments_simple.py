import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd

class SimpleInstrumentsTab(ttk.Frame):
    """Упрощенная вкладка инструментов для тестирования"""
    
    def __init__(self, parent, token):
        super().__init__(parent)
        self.token = token
        
        self.create_widgets()
        self.load_sample_data()
    
    def create_widgets(self):
        """Создание простого интерфейса"""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Заголовок
        title_label = ttk.Label(main_frame, text="📊 Инструменты - РАБОЧАЯ ВЕРСИЯ", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=10)
        
        # Информация
        info_label = ttk.Label(main_frame, text="Сервис инструментов работает!\nИспользуйте поиск для тестирования.",
                              justify=tk.CENTER)
        info_label.pack(pady=5)
        
        # Поиск
        search_frame = ttk.Frame(main_frame)
        search_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(search_frame, text="Поиск:").pack(side=tk.LEFT)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        self.search_entry.insert(0, "SBER")  # Пример по умолчанию
        
        ttk.Button(search_frame, text="Тест поиска", 
                  command=self.test_search).pack(side=tk.LEFT, padx=5)
        
        # Таблица для результатов
        columns = ('Тикер', 'Название', 'Тип', 'Валюта')
        self.tree = ttk.Treeview(main_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=150)
        
        scrollbar = ttk.Scrollbar(main_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Кнопки
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Тест подключения", 
                  command=self.test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Очистить", 
                  command=self.clear_table).pack(side=tk.LEFT, padx=5)
    
    def load_sample_data(self):
        """Загрузка тестовых данных"""
        sample_data = [
            ('SBER', 'Сбер Банк', 'Акция', 'RUB'),
            ('GAZP', 'Газпром', 'Акция', 'RUB'),
            ('LKOH', 'ЛУКОЙЛ', 'Акция', 'RUB'),
            ('YNDX', 'Яндекс', 'Акция', 'RUB'),
            ('VTBR', 'Банк ВТБ', 'Акция', 'RUB'),
        ]
        
        for item in sample_data:
            self.tree.insert('', tk.END, values=item)
    
    def test_search(self):
        """Тест поиска"""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Внимание", "Введите поисковый запрос")
            return
        
        try:
            # Простой тест - имитация поиска
            self.clear_table()
            
            # Добавляем результат поиска
            self.tree.insert('', tk.END, values=(query, f"Результат поиска: {query}", "Тест", "RUB"))
            self.tree.insert('', tk.END, values=("TEST", "Тестовый инструмент", "Акция", "RUB"))
            
            messagebox.showinfo("Успех", f"Поиск '{query}' выполнен\n(тестовый режим)")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка поиска: {e}")
    
    def test_connection(self):
        """Тест подключения к API"""
        try:
            from tinkoff.invest import Client
            
            with Client(self.token) as client:
                # Простой запрос для проверки подключения
                accounts = client.users.get_accounts()
                messagebox.showinfo("Успех", "✅ Подключение к Tinkoff API работает!")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"❌ Ошибка подключения: {e}")
    
    def clear_table(self):
        """Очистка таблицы"""
        for item in self.tree.get_children():
            self.tree.delete(item)

# Тестирование
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Тест упрощенной вкладки")
    root.geometry("800x600")
    
    TOKEN = "t.8HbNCn4L0U9uBmMa5oloBrXCKxnqsTYNVK3f9iJOwDBiQ2lva9kvQ3C-MLgEESHl65ma1q0k0P6aMfS_O_co4g"
    
    tab = SimpleInstrumentsTab(root, TOKEN)
    tab.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()
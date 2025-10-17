import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
from tbank_api.instrument_service import InstrumentService


class InstrumentsTab(ttk.Frame):
    """Вкладка для работы с инструментами"""
    
    def __init__(self, parent, token):
        super().__init__(parent)
        self.token = token
        self.service = InstrumentService(token)
        
        self.create_widgets()
        self.load_popular_shares()
    
    def create_widgets(self):
        """Создание интерфейса"""
        # Основной контейнер
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Поиск
        search_frame = ttk.LabelFrame(main_frame, text="🔍 Поиск инструментов", padding=10)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Поиск:").grid(row=0, column=0, sticky=tk.W)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.grid(row=0, column=1, padx=5)
        self.search_entry.bind('<Return>', lambda e: self.search_instruments())
        
        ttk.Button(search_frame, text="Найти", 
                  command=self.search_instruments).grid(row=0, column=2, padx=5)
        
        # Тип инструмента для поиска
        ttk.Label(search_frame, text="Тип:").grid(row=0, column=3, padx=(20, 5))
        self.instrument_type = tk.StringVar(value="all")
        type_combo = ttk.Combobox(search_frame, textvariable=self.instrument_type,
                                 values=["all", "share", "bond", "etf", "currency", "future"],
                                 state="readonly", width=10)
        type_combo.grid(row=0, column=4, padx=5)
        
        # Вкладки для разных типов инструментов
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        # Вкладка с популярными акциями
        self.shares_frame = ttk.Frame(notebook)
        notebook.add(self.shares_frame, text="📈 Популярные акции")
        
        # Вкладка с результатами поиска
        self.search_frame = ttk.Frame(notebook)
        notebook.add(self.search_frame, text="🔍 Результаты поиска")
        
        # Вкладка с ETF
        self.etfs_frame = ttk.Frame(notebook)
        notebook.add(self.etfs_frame, text="📊 ETF")
        
        # Вкладка с облигациями
        self.bonds_frame = ttk.Frame(notebook)
        notebook.add(self.bonds_frame, text="💵 Облигации")
        
        # Создание таблиц для каждой вкладки
        self.create_shares_table()
        self.create_search_table()
        self.create_etfs_table()
        self.create_bonds_table()
        
        # Кнопки управления
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Обновить акции", 
                  command=self.load_popular_shares).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Загрузить ETF", 
                  command=self.load_etfs).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Загрузить облигации", 
                  command=self.load_bonds).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Экспорт в CSV", 
                  command=self.export_to_csv).pack(side=tk.RIGHT, padx=5)
    
    def create_shares_table(self):
        """Создание таблицы для акций"""
        # Treeview для акций - добавляем FIGI как скрытую колонку
        columns = ('FIGI', 'Ticker', 'Name', 'Lot', 'Currency', 'Exchange', 'Sector')
        self.shares_tree = ttk.Treeview(self.shares_frame, columns=columns, show='headings', height=15)
        
        # Заголовки (FIGI скрываем)
        for col in columns:
            self.shares_tree.heading(col, text=col)
            if col == 'FIGI':
                self.shares_tree.column(col, width=0, stretch=False)  # Скрытая колонка
            else:
                self.shares_tree.column(col, width=100)
                    
    def create_search_table(self):
        """Создание таблицы для результатов поиска"""
        columns = ('Ticker', 'Name', 'Instrument Type', 'Currency', 'Exchange', 'API Trade')
        self.search_tree = ttk.Treeview(self.search_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(self.search_frame, orient=tk.VERTICAL, command=self.search_tree.yview)
        self.search_tree.configure(yscrollcommand=scrollbar.set)
        
        self.search_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.search_tree.bind('<Double-1>', self.show_instrument_details)
    
    def create_etfs_table(self):
        """Создание таблицы для ETF"""
        columns = ('Ticker', 'Name', 'Lot', 'Currency', 'Exchange', 'Focus Type')
        self.etfs_tree = ttk.Treeview(self.etfs_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.etfs_tree.heading(col, text=col)
            self.etfs_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(self.etfs_frame, orient=tk.VERTICAL, command=self.etfs_tree.yview)
        self.etfs_tree.configure(yscrollcommand=scrollbar.set)
        
        self.etfs_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.etfs_tree.bind('<Double-1>', self.show_instrument_details)
    
    def create_bonds_table(self):
        """Создание таблицы для облигаций"""
        columns = ('Ticker', 'Name', 'Lot', 'Currency', 'Exchange', 'Nominal')
        self.bonds_tree = ttk.Treeview(self.bonds_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.bonds_tree.heading(col, text=col)
            self.bonds_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(self.bonds_frame, orient=tk.VERTICAL, command=self.bonds_tree.yview)
        self.bonds_tree.configure(yscrollcommand=scrollbar.set)
        
        self.bonds_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.bonds_tree.bind('<Double-1>', self.show_instrument_details)
    
    def load_popular_shares(self):
        """Загрузка популярных акций"""
        try:
            self.shares_tree.delete(*self.shares_tree.get_children())
            
            shares_df = self.service.get_popular_russian_shares()
            
            for _, row in shares_df.iterrows():
                self.shares_tree.insert('', tk.END, values=(
                    row['FIGI'],  # FIGI как первое значение (скрытое)
                    row['Ticker'],
                    row['Name'],
                    row['Lot'],
                    row['Currency'],
                    row['Exchange'],
                    row.get('Sector', '')
                ))
            
            messagebox.showinfo("Успех", f"Загружено {len(shares_df)} популярных акций")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить акции: {e}")
    
    def search_instruments(self):
        """Поиск инструментов"""
        query = self.search_entry.get().strip()
        if not query:
            messagebox.showwarning("Внимание", "Введите поисковый запрос")
            return
        
        try:
            self.search_tree.delete(*self.search_tree.get_children())
            
            instrument_type = self.instrument_type.get()
            results_df = self.service.search_instruments(query, instrument_type)
            
            for _, row in results_df.iterrows():
                self.search_tree.insert('', tk.END, values=(
                    row['Ticker'],
                    row['Name'],
                    row['Instrument Type'],
                    row['Currency'],
                    row['Exchange'],
                    'Да' if row['API Trade Available'] else 'Нет'
                ))
            
            messagebox.showinfo("Результаты", f"Найдено инструментов: {len(results_df)}")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка поиска: {e}")
    
    def load_etfs(self):
        """Загрузка ETF"""
        try:
            self.etfs_tree.delete(*self.etfs_tree.get_children())
            
            etfs_df = self.service.etfs_to_dataframe()
            
            for _, row in etfs_df.iterrows():
                self.etfs_tree.insert('', tk.END, values=(
                    row['Ticker'],
                    row['Name'],
                    row['Lot'],
                    row['Currency'],
                    row['Exchange'],
                    row.get('Focus Type', '')
                ))
            
            messagebox.showinfo("Успех", f"Загружено {len(etfs_df)} ETF")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить ETF: {e}")
    
    def load_bonds(self):
        """Загрузка облигаций"""
        try:
            self.bonds_tree.delete(*self.bonds_tree.get_children())
            
            bonds_df = self.service.bonds_to_dataframe()
            # Берем только первые 100 для производительности
            bonds_df = bonds_df.head(100)
            
            for _, row in bonds_df.iterrows():
                self.bonds_tree.insert('', tk.END, values=(
                    row['Ticker'],
                    row['Name'],
                    row['Lot'],
                    row['Currency'],
                    row['Exchange'],
                    row.get('Nominal', '')
                ))
            
            messagebox.showinfo("Успех", f"Загружено {len(bonds_df)} облигаций")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить облигации: {e}")
    
    def show_instrument_details(self, event):
        """Показать детали инструмента - используем FIGI"""
        tree = event.widget
        selection = tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = tree.item(item, 'values')
        figi = values[0]  # FIGI теперь первое значение
        ticker = values[1]  # Тикер второе
        
        try:
            # Используем FIGI для поиска - это надежнее
            instrument = self.service.get_instrument_by_figi(figi)
            if instrument and hasattr(instrument, 'instrument'):
                details = instrument.instrument
                self.show_details_window(details)
            else:
                messagebox.showwarning("Внимание", 
                                    f"Не удалось найти детальную информацию для {ticker}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить детали: {e}")
    
    def show_instrument_details(self, event):
        """Показать детали инструмента"""
        tree = event.widget
        selection = tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = tree.item(item, 'values')
        ticker = values[0]
        
        try:
            # Используем улучшенный метод поиска
            instrument = self.service.get_instrument_by_ticker(ticker)
            if instrument and hasattr(instrument, 'instrument'):
                details = instrument.instrument
                self.show_details_window(details)
            else:
                messagebox.showwarning("Внимание", 
                                    f"Не удалось найти детальную информацию для {ticker}\n"
                                    f"Инструмент может быть недоступен через API")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить детали: {e}")
                        
    def export_to_csv(self):
        """Экспорт данных в CSV"""
        try:
            # Экспортируем популярные акции
            shares_df = self.service.get_popular_russian_shares()
            shares_df.to_csv('popular_shares.csv', index=False, encoding='utf-8')
            messagebox.showinfo("Успех", "Данные экспортированы в popular_shares.csv")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {e}")


# Тестирование вкладки
if __name__ == "__main__":
    root = tk.Tk()
    root.title("Тест вкладки инструментов")
    root.geometry("800x600")
    
    TOKEN = "t.8HbNCn4L0U9uBmMa5oloBrXCKxnqsTYNVK3f9iJOwDBiQ2lva9kvQ3C-MLgEESHl65ma1q0k0P6aMfS_O_co4g"
    
    tab = InstrumentsTab(root, TOKEN)
    tab.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()
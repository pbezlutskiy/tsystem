import tkinter as tk
from tkinter import ttk, messagebox
import pandas as pd
import sys
import os

# Добавляем путь к корню проекта для импорта модулей
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    from tbank_api.instrument_service import InstrumentService
    IMPORT_SUCCESS = True
except ImportError as e:
    print(f"❌ Ошибка импорта InstrumentService: {e}")
    IMPORT_SUCCESS = False


class InstrumentsTabWorking(ttk.Frame):
    """Рабочая вкладка для инструментов"""
    
    def __init__(self, parent, token):
        super().__init__(parent)
        self.token = token
        
        if not IMPORT_SUCCESS:
            self.show_import_error()
            return
            
        self.service = InstrumentService(token)
        self.create_widgets()
        self.load_popular_shares()
    
    def show_import_error(self):
        """Показать сообщение об ошибке импорта"""
        error_frame = ttk.Frame(self)
        error_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        ttk.Label(error_frame, text="❌ Ошибка загрузки модулей", 
                 font=('Arial', 14, 'bold'), foreground='red').pack(pady=10)
        
        ttk.Label(error_frame, text="Не удалось загрузить сервис инструментов.", 
                 justify=tk.CENTER).pack(pady=10)
        
        ttk.Button(error_frame, text="Перезагрузить", 
                  command=self.retry_import).pack(pady=10)
    
    def retry_import(self):
        """Попытка переимпортировать модули"""
        try:
            # Импортируем правильный класс
            from tbank_api.instrument_service import InstrumentService
            
            # Создаем сервис
            self.service = InstrumentService(self.token)
            
            # Очищаем и пересоздаем интерфейс
            for widget in self.winfo_children():
                widget.destroy()
                
            self.create_widgets()
            self.load_popular_shares()
            
            print("✅ Модуль успешно перезагружен")
            
        except ImportError as e:
            print(f"❌ Ошибка импорта: {e}")
            messagebox.showerror("Ошибка", f"Не удалось перезагрузить модуль: {e}")
        except Exception as e:
            print(f"❌ Другая ошибка: {e}")
            messagebox.showerror("Ошибка", f"Ошибка при перезагрузке: {e}")
    
    def create_widgets(self):
        """Создание интерфейса"""
        if not IMPORT_SUCCESS:
            return
            
        main_frame = ttk.Frame(self)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        title_label = ttk.Label(main_frame, text="📊 Инструменты Tinkoff API", 
                               font=('Arial', 12, 'bold'))
        title_label.pack(pady=5)
        
        status_label = ttk.Label(main_frame, text="✅ Сервис работает", 
                                foreground='green')
        status_label.pack(pady=5)
        
        search_frame = ttk.LabelFrame(main_frame, text="🔍 Поиск инструментов", padding=10)
        search_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(search_frame, text="Поиск:").grid(row=0, column=0, sticky=tk.W)
        self.search_entry = ttk.Entry(search_frame, width=30)
        self.search_entry.grid(row=0, column=1, padx=5)
        self.search_entry.bind('<Return>', lambda e: self.search_instruments())
        
        ttk.Button(search_frame, text="Найти", 
                  command=self.search_instruments).grid(row=0, column=2, padx=5)
        
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True)
        
        self.shares_frame = ttk.Frame(notebook)
        notebook.add(self.shares_frame, text="📈 Акции")
        
        self.search_frame = ttk.Frame(notebook)
        notebook.add(self.search_frame, text="🔍 Результаты")
        
        self.details_frame = ttk.Frame(notebook)
        notebook.add(self.details_frame, text="📋 Детали")
        
        self.create_shares_table()
        self.create_search_table()
        self.create_details_section()
        
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="Обновить акции", 
                  command=self.load_popular_shares).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Проверить API", 
                  command=self.test_connection).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="Экспорт", 
                  command=self.export_to_csv).pack(side=tk.RIGHT, padx=5)
    
    def create_shares_table(self):
        """Создание таблицы для акций"""
        columns = ('Тикер', 'Название', 'Лот', 'Валюта', 'FIGI')
        self.shares_tree = ttk.Treeview(self.shares_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.shares_tree.heading(col, text=col)
            self.shares_tree.column(col, width=100)
        
        scrollbar = ttk.Scrollbar(self.shares_frame, orient=tk.VERTICAL, command=self.shares_tree.yview)
        self.shares_tree.configure(yscrollcommand=scrollbar.set)
        
        self.shares_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.shares_tree.bind('<Double-1>', self.show_instrument_details_from_shares)
    
    def create_search_table(self):
        """Создание таблицы для результатов поиска"""
        columns = ('Тикер', 'Название', 'Тип', 'Валюта', 'Лот', 'Биржа', 'FIGI')
        self.search_tree = ttk.Treeview(self.search_frame, columns=columns, show='headings', height=15)
        
        for col in columns:
            self.search_tree.heading(col, text=col)
            self.search_tree.column(col, width=120)
        
        scrollbar = ttk.Scrollbar(self.search_frame, orient=tk.VERTICAL, command=self.search_tree.yview)
        self.search_tree.configure(yscrollcommand=scrollbar.set)
        
        self.search_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.search_tree.bind('<Double-1>', self.show_instrument_details_from_search)
    
    def create_details_section(self):
        """Создание секции с деталями инструмента"""
        details_text_frame = ttk.Frame(self.details_frame)
        details_text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        ttk.Label(details_text_frame, text="Детальная информация:", 
                 font=('Arial', 10, 'bold')).pack(anchor=tk.W)
        
        self.details_text = tk.Text(details_text_frame, wrap=tk.WORD, height=20, 
                                   padx=10, pady=10, font=('Arial', 9))
        
        scrollbar = ttk.Scrollbar(details_text_frame, orient=tk.VERTICAL, command=self.details_text.yview)
        self.details_text.configure(yscrollcommand=scrollbar.set)
        
        self.details_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        details_buttons = ttk.Frame(self.details_frame)
        details_buttons.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(details_buttons, text="Очистить", 
                  command=self.clear_details).pack(side=tk.LEFT, padx=5)
    
    def load_popular_shares(self):
        """Загрузка популярных акций"""
        try:
            self.shares_tree.delete(*self.shares_tree.get_children())
            
            # Правильный вызов метода
            shares_df = self.service.get_popular_russian_shares()
            
            if shares_df.empty:
                messagebox.showwarning("Предупреждение", "Не удалось загрузить акции")
                return
            
            for _, row in shares_df.iterrows():
                self.shares_tree.insert('', tk.END, values=(
                    row['Ticker'],
                    row['Name'],
                    row['Lot'],
                    row.get('Currency', 'rub'),
                    row.get('FIGI', '')
                ))
            
            messagebox.showinfo("Успех", f"Загружено {len(shares_df)} акций")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить акции: {e}")
    
    def search_instruments(self):
        """Поиск инструментов"""
        try:
            query = self.search_entry.get().strip()
            if not query:
                messagebox.showwarning("Предупреждение", "Введите запрос для поиска")
                return
            
            self.search_tree.delete(*self.search_tree.get_children())
            
            # Правильный вызов метода
            search_results = self.service.search_instruments_dataframe(query)
            
            if search_results.empty:
                messagebox.showinfo("Информация", "Инструменты не найдены")
                return
            
            for _, row in search_results.iterrows():
                self.search_tree.insert('', tk.END, values=(
                    row['Ticker'],
                    row['Name'],
                    row['Type'],
                    row.get('Currency', ''),
                    row.get('Lot', 1),
                    row.get('Exchange', ''),
                    row.get('FIGI', '')
                ))
            
            messagebox.showinfo("Успех", f"Найдено {len(search_results)} инструментов")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка поиска: {e}")

    def show_instrument_details_from_shares(self, event):
        """Показать детали инструмента из таблицы акций"""
        selection = self.shares_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.shares_tree.item(item, 'values')
        figi = values[4]  # FIGI в 5-й колонке
        
        self.show_instrument_details_by_figi(figi)
    
    def show_instrument_details_from_search(self, event):
        """Показать детали инструмента из результатов поиска"""
        selection = self.search_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.search_tree.item(item, 'values')
        ticker = values[0]
        
        try:
            # Используем правильный метод поиска
            results_df = self.service.search_instruments_dataframe(ticker)
            if not results_df.empty:
                figi = results_df.iloc[0]['FIGI']
                self.show_instrument_details_by_figi(figi)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить детали: {e}")
    
    def show_instrument_details_by_figi(self, figi):
        """Показать детали инструмента по FIGI"""
        try:
            # Используем правильный метод
            instrument = self.service.get_instrument_by_figi(figi)
            if instrument:
                self.display_instrument_details(instrument)
            else:
                messagebox.showwarning("Внимание", "Не удалось получить детали")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка получения деталей: {e}")
    
    def display_instrument_details(self, instrument):
        """Отображение деталей инструмента"""
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        
        info = f"""📊 ДЕТАЛЬНАЯ ИНФОРМАЦИЯ:

                📛 Название: {instrument.name}
                🏷️ Тикер: {instrument.ticker}
                🔢 FIGI: {instrument.figi}
                💰 Валюта: {instrument.currency}
                📦 Лот: {instrument.lot}
                🏛️ Биржа: {instrument.exchange}
                📊 Класс-код: {instrument.class_code}

                ⚙️ Доступность:
                • Торговля через API: {'✅ ДА' if instrument.api_trade_available_flag else '❌ НЕТ'}
                • Покупка: {'✅ ДА' if instrument.buy_available_flag else '❌ НЕТ'}
                • Продажа: {'✅ ДА' if instrument.sell_available_flag else '❌ НЕТ'}
                """
        
        # Добавляем информацию о минимальном шаге цены если доступно
        if hasattr(instrument, 'min_price_increment'):
            min_price = instrument.min_price_increment
            if hasattr(min_price, 'units') and hasattr(min_price, 'nano'):
                info += f"🎯 Минимальный шаг цены: {min_price.units}.{min_price.nano:09d}\n"
        
        self.details_text.insert(tk.END, info)
        self.details_text.config(state=tk.DISABLED)
        
        notebook = self.details_frame.master
        notebook.select(self.details_frame)
    
    def clear_details(self):
        """Очистка деталей инструмента"""
        self.details_text.config(state=tk.NORMAL)
        self.details_text.delete(1.0, tk.END)
        self.details_text.config(state=tk.DISABLED)
    
    def test_connection(self):
        """Проверка подключения к API"""
        try:
            # Простая проверка - пытаемся получить популярные акции
            shares_df = self.service.get_popular_russian_shares()
            
            if not shares_df.empty:
                messagebox.showinfo("Подключение", 
                                f"✅ API работает!\nЗагружено {len(shares_df)} акций")
            else:
                messagebox.showwarning("Подключение", 
                                    "⚠️ API отвечает, но не удалось загрузить данные")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"❌ Ошибка подключения: {e}")
                
    def export_to_csv(self):
        """Экспорт данных в CSV"""
        try:
            # Используем правильный метод
            shares_df = self.service.get_popular_russian_shares()
            shares_df.to_csv('instruments_export.csv', index=False, encoding='utf-8')
            messagebox.showinfo("Успех", f"Экспортировано {len(shares_df)} инструментов")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {e}")


if __name__ == "__main__":
    root = tk.Tk()
    root.title("Инструменты")
    root.geometry("900x600")
    
    TOKEN = "t.8HbNCn4L0U9uBmMa5oloBrXCKxnqsTYNVK3f9iJOwDBiQ2lva9kvQ3C-MLgEESHl65ma1q0k0P6aMfS_O_co4g"
    
    tab = InstrumentsTabWorking(root, TOKEN)
    tab.pack(fill=tk.BOTH, expand=True)
    
    root.mainloop()
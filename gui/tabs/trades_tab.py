# ===== СЕКЦИЯ 12: ВКЛАДКА СПИСКА СДЕЛОК =====
"""
Вкладка для отображения детальной информации о всех сделках
Таблица сделок с аналитикой и статистикой
"""

import tkinter as tk
from tkinter import ttk
from tkinter import scrolledtext
import pandas as pd
from gui.components import StatsTextFrame

class TradesTab:
    """Вкладка списка сделок с детальной информацией"""
    
    def __init__(self, parent, trading_system):
        self.parent = parent
        self.trading_system = trading_system
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.frame = ttk.Frame(self.parent)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(0, weight=1)
        
        # Создание Notebook для разделения на таблицу и статистику
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Вкладка с таблицей сделок
        self.trades_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.trades_frame, text="📋 Список сделок")
        
        # Вкладка со статистикой сделок
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="📊 Статистика сделок")
        
        self.setup_trades_tab()
        self.setup_stats_tab()
    
    def setup_trades_tab(self):
        """Настройка вкладки с таблицей сделок"""
        self.trades_frame.columnconfigure(0, weight=1)
        self.trades_frame.rowconfigure(0, weight=1)
        
        # Создание Treeview для отображения сделок
        columns = ('№', 'Вход', 'Выход', 'Цена входа', 'Цена выхода', 
                  'Размер', 'P&L %', 'P&L $', 'Длит.', 'Тип')
        
        self.trades_tree = ttk.Treeview(self.trades_frame, columns=columns, show='headings', height=20)
        
        # Настройка колонок
        column_widths = {
            '№': 50, 'Вход': 80, 'Выход': 80, 'Цена входа': 90, 
            'Цена выхода': 90, 'Размер': 100, 'P&L %': 80, 
            'P&L $': 100, 'Длит.': 60, 'Тип': 80
        }
        
        for col in columns:
            self.trades_tree.heading(col, text=col)
            self.trades_tree.column(col, width=column_widths.get(col, 100))
        
        # Добавляем контекстное меню
        self.setup_context_menu()
        
        # Scrollbar для таблицы
        scrollbar = ttk.Scrollbar(self.trades_frame, orient=tk.VERTICAL, command=self.trades_tree.yview)
        self.trades_tree.configure(yscrollcommand=scrollbar.set)
        
        self.trades_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
    
    def setup_context_menu(self):
        """Настройка контекстного меню для таблицы"""
        self.context_menu = tk.Menu(self.trades_tree, tearoff=0)
        self.context_menu.add_command(label="Копировать данные", command=self.copy_selected_data)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Экспорт в CSV", command=self.export_to_csv)
        
        # Привязка правой кнопки мыши
        self.trades_tree.bind("<Button-3>", self.show_context_menu)
    
    def show_context_menu(self, event):
        """Показать контекстное меню"""
        item = self.trades_tree.identify_row(event.y)
        if item:
            self.trades_tree.selection_set(item)
            self.context_menu.post(event.x_root, event.y_root)
    
    def copy_selected_data(self):
        """Копировать выделенные данные в буфер обмена"""
        selected_items = self.trades_tree.selection()
        if not selected_items:
            return
        
        copied_data = []
        for item in selected_items:
            values = self.trades_tree.item(item)['values']
            copied_data.append('\t'.join(map(str, values)))
        
        self.trades_tree.clipboard_clear()
        self.trades_tree.clipboard_append('\n'.join(copied_data))
    
    def export_to_csv(self):
        """Экспорт данных в CSV файл"""
        try:
            trade_history = self.trading_system.get_trade_history()
            if not trade_history.empty:
                filename = f"trades_export_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv"
                trade_history.to_csv(filename, index=False, encoding='utf-8')
                # Здесь можно добавить уведомление об успешном экспорте
        except Exception as e:
            print(f"Ошибка при экспорте: {e}")
    
    def setup_stats_tab(self):
        """Настройка вкладки со статистикой сделок"""
        self.stats_frame.columnconfigure(0, weight=1)
        self.stats_frame.rowconfigure(0, weight=1)
        
        self.stats_text = StatsTextFrame(self.stats_frame)
        self.stats_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.stats_text.set_placeholder("Статистика сделок будет отображена после тестирования")
    
    def get_frame(self):
        """Возвращает фрейм вкладки"""
        return self.frame
    
    def update_trades(self, result_name: str = None):
        """Обновить информацию о сделках"""
        # Очистка таблицы
        for item in self.trades_tree.get_children():
            self.trades_tree.delete(item)
        
        # Получение истории сделок
        trade_history = self.trading_system.get_trade_history()
        
        if trade_history.empty:
            self.stats_text.set_text("Нет данных о сделках")
            return
        
        # Заполнение таблицы
        for i, trade in trade_history.iterrows():
            # Определение цвета для P&L
            pnl_percent = trade['pnl_percent']
            pnl_absolute = trade['pnl_absolute']
            
            # Определение типа сделки (длинная/короткая)
            trade_type = "LONG" if trade.get('trade_type', 'long') == 'long' else "SHORT"
            
            # Форматирование значений
            values = (
                i + 1,  # №
                trade['entry_index'],
                trade['exit_index'],
                f"${trade['entry_price']:.2f}",
                f"${trade['exit_price']:.2f}",
                f"${trade['position_size']:,.0f}",
                f"{pnl_percent:+.2f}%",
                f"${pnl_absolute:+.2f}",
                f"{trade['duration']} дн.",
                trade_type
            )
            
            item = self.trades_tree.insert('', tk.END, values=values)
            
            # Подсветка прибыльных/убыточных сделок
            tags = ('profit',) if pnl_absolute > 0 else ('loss',) if pnl_absolute < 0 else ('even',)
            self.trades_tree.item(item, tags=tags)
        
        # Настройка тегов для цветового выделения
        self.trades_tree.tag_configure('profit', background='#f0fff0')  # Светло-зеленый
        self.trades_tree.tag_configure('loss', background='#fff0f0')    # Светло-красный
        self.trades_tree.tag_configure('even', background='#f0f0f0')    # Серый
        
        # Обновление статистики
        self.update_trades_stats(trade_history)
    
    def update_trades_stats(self, trade_history: pd.DataFrame):
        """Обновление статистики сделок"""
        if trade_history.empty:
            return
        
        try:
            # Расчет метрик
            total_trades = len(trade_history)
            winning_trades = len(trade_history[trade_history['pnl_absolute'] > 0])
            losing_trades = len(trade_history[trade_history['pnl_absolute'] < 0])
            even_trades = len(trade_history[trade_history['pnl_absolute'] == 0])
            win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
            
            total_pnl = trade_history['pnl_absolute'].sum()
            avg_pnl = trade_history['pnl_absolute'].mean()
            
            # Расчет средней прибыли/убытка с проверкой на пустые данные
            avg_win = (trade_history[trade_history['pnl_absolute'] > 0]['pnl_absolute'].mean() 
                      if winning_trades > 0 else 0)
            avg_loss = (trade_history[trade_history['pnl_absolute'] < 0]['pnl_absolute'].mean() 
                       if losing_trades > 0 else 0)
            
            largest_win = trade_history['pnl_absolute'].max()
            largest_loss = trade_history['pnl_absolute'].min()
            
            gross_profit = (trade_history[trade_history['pnl_absolute'] > 0]['pnl_absolute'].sum() 
                           if winning_trades > 0 else 0)
            gross_loss = (abs(trade_history[trade_history['pnl_absolute'] < 0]['pnl_absolute'].sum()) 
                         if losing_trades > 0 else 0)
            
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
            win_loss_ratio = abs(avg_win / avg_loss) if avg_loss != 0 else float('inf')
            
            avg_duration = trade_history['duration'].mean()
            
            # Расчет максимальной просадки
            cumulative_pnl = trade_history['pnl_absolute'].cumsum()
            running_max = cumulative_pnl.cummax()
            drawdown = cumulative_pnl - running_max
            max_drawdown = drawdown.min()
            
            # Форматирование статистики
            stats_text = "=" * 60 + "\n"
            stats_text += "СТАТИСТИКА СДЕЛОК\n"
            stats_text += "=" * 60 + "\n\n"
            
            stats_text += f"📊 ОБЩАЯ СТАТИСТИКА:\n"
            stats_text += f"   Всего сделок: {total_trades}\n"
            stats_text += f"   Прибыльных: {winning_trades} ({win_rate:.1f}%)\n"
            stats_text += f"   Убыточных: {losing_trades} ({100 - win_rate:.1f}%)\n"
            stats_text += f"   Безубыточных: {even_trades}\n"
            stats_text += f"   Общий P&L: ${total_pnl:+.2f}\n\n"
            
            stats_text += f"💰 ДОХОДНОСТЬ:\n"
            stats_text += f"   Средний P&L за сделку: ${avg_pnl:+.2f}\n"
            stats_text += f"   Средняя прибыль: ${avg_win:+.2f}\n"
            stats_text += f"   Средний убыток: ${avg_loss:+.2f}\n"
            stats_text += f"   Profit Factor: {profit_factor:.2f}\n"
            stats_text += f"   Соотношение прибыль/убыток: {win_loss_ratio:.2f}\n\n"
            
            stats_text += f"🎯 ЭКСТРЕМУМЫ:\n"
            stats_text += f"   Крупнейшая прибыль: ${largest_win:+.2f}\n"
            stats_text += f"   Крупнейший убыток: ${largest_loss:+.2f}\n"
            stats_text += f"   Максимальная просадка: ${max_drawdown:.2f}\n\n"
            
            stats_text += f"⏱️  ВРЕМЕННЫЕ ХАРАКТЕРИСТИКИ:\n"
            stats_text += f"   Средняя длительность сделки: {avg_duration:.1f} дней\n"
            stats_text += f"   Минимальная длительность: {trade_history['duration'].min()} дней\n"
            stats_text += f"   Максимальная длительность: {trade_history['duration'].max()} дней\n"
            
            self.stats_text.set_text(stats_text)
            
        except Exception as e:
            self.stats_text.set_text(f"Ошибка при расчете статистики: {str(e)}")
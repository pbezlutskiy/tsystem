# tbank_api/tbank_gui.py
"""
Графический интерфейс для работы с API Т-банка
"""
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext  # ✅ ДОБАВЛЯЕМ ttk
import logging
from typing import Optional, Dict, Any, List
import pandas as pd
from datetime import datetime, timedelta

# Импорты для работы с кэшированием
from .tbank_data_loader import TBankDataLoader
from config import Config

logger = logging.getLogger(__name__)

class TBankApiTab:
    """Вкладка для работы с API Т-банка"""
    
    def __init__(self, parent, main_app):
        self.main_app = main_app
        self.frame = ttk.Frame(parent)
        
        # Инициализация загрузчика данных
        self.data_loader = TBankDataLoader()
        
        # Переменные интерфейса
        self.token_var = tk.StringVar()
        self.symbol_var = tk.StringVar()
        self.days_back_var = tk.IntVar(value=365)
        self.timeframe_var = tk.StringVar(value='1d')
        self.cache_enabled = tk.BooleanVar(value=True)
        
        # Данные
        self.loaded_data = None
        self.available_instruments = None
        
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        # Основной фрейм с прокруткой
        main_frame = ttk.Frame(self.frame)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Заголовок
        title_label = ttk.Label(
            main_frame, 
            text="📡 T-Банк API - Загрузка рыночных данных",
            font=('Arial', 14, 'bold'),
            foreground='#2c3e50'
        )
        title_label.pack(pady=(0, 20))
        
        # === СЕКЦИЯ 1: НАСТРОЙКА API ===
        api_frame = ttk.LabelFrame(main_frame, text="🔧 Настройка API", padding="15")
        api_frame.pack(fill=tk.X, pady=10)
        
        # Токен API
        ttk.Label(api_frame, text="API Токен:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        token_entry = ttk.Entry(api_frame, textvariable=self.token_var, width=50, show="*")
        token_entry.grid(row=0, column=1, columnspan=2, sticky=(tk.W, tk.E), padx=5, pady=5)
        
        # Кнопки управления API
        ttk.Button(api_frame, text="🔍 Проверить подключение", 
                  command=self.test_connection).grid(row=0, column=3, padx=5, pady=5)
        ttk.Button(api_frame, text="💾 Сохранить токен", 
                  command=self.save_token).grid(row=0, column=4, padx=5, pady=5)
        
        # === СЕКЦИЯ 2: ПОИСК ИНСТРУМЕНТОВ ===
        search_frame = ttk.LabelFrame(main_frame, text="🔍 Поиск инструментов", padding="15")
        search_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(search_frame, text="Поиск:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        search_entry = ttk.Entry(search_frame, width=30)
        search_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Button(search_frame, text="Искать", 
                  command=lambda: self.search_instruments(search_entry.get())).grid(row=0, column=2, padx=5, pady=5)
        ttk.Button(search_frame, text="📋 Все инструменты", 
                  command=self.load_all_instruments).grid(row=0, column=3, padx=5, pady=5)
        
        # Таблица инструментов
        instruments_frame = ttk.Frame(search_frame)
        instruments_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=10)
        
        self.instruments_tree = ttk.Treeview(instruments_frame, columns=('ticker', 'name', 'type', 'currency'), 
                                           show='headings', height=8)
        self.instruments_tree.heading('ticker', text='Тикер')
        self.instruments_tree.heading('name', text='Название')
        self.instruments_tree.heading('type', text='Тип')
        self.instruments_tree.heading('currency', text='Валюта')
        
        self.instruments_tree.column('ticker', width=80)
        self.instruments_tree.column('name', width=200)
        self.instruments_tree.column('type', width=80)
        self.instruments_tree.column('currency', width=60)
        
        # Scrollbar для таблицы
        scrollbar = ttk.Scrollbar(instruments_frame, orient=tk.VERTICAL, command=self.instruments_tree.yview)
        self.instruments_tree.configure(yscrollcommand=scrollbar.set)
        
        self.instruments_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Обработчик выбора инструмента
        self.instruments_tree.bind('<<TreeviewSelect>>', self.on_instrument_select)
        
        # === СЕКЦИЯ 3: ЗАГРУЗКА ДАННЫХ ===
        data_frame = ttk.LabelFrame(main_frame, text="📥 Загрузка данных", padding="15")
        data_frame.pack(fill=tk.X, pady=10)
        
        # Параметры загрузки
        ttk.Label(data_frame, text="Тикер:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(data_frame, textvariable=self.symbol_var, width=15).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(data_frame, text="Дней назад:").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(data_frame, textvariable=self.days_back_var, width=10).grid(row=0, column=3, padx=5, pady=5)
        
        ttk.Label(data_frame, text="Таймфрейм:").grid(row=0, column=4, sticky=tk.W, padx=5, pady=5)
        timeframe_combo = ttk.Combobox(
            data_frame, 
            textvariable=self.timeframe_var,
            values=['1d', '1h', '4h', '1w', '1m', '5m', '15m'],
            state="readonly",
            width=8
        )
        timeframe_combo.grid(row=0, column=5, padx=5, pady=5)
        
        # Кэширование
        ttk.Checkbutton(data_frame, text="Использовать кэширование", 
                       variable=self.cache_enabled).grid(row=0, column=6, padx=10, pady=5)
        
        # Кнопки загрузки
        button_frame = ttk.Frame(data_frame)
        button_frame.grid(row=1, column=0, columnspan=7, pady=10)
        
        ttk.Button(button_frame, text="📥 Загрузить данные", 
                  command=self.load_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔄 Обновить свежие данные", 
                  command=self.update_recent_data).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🎯 Использовать в системе", 
                  command=self.use_in_main_system).pack(side=tk.LEFT, padx=5)
        
        # === СЕКЦИЯ 4: УПРАВЛЕНИЕ КЭШЕМ И ОПТИМИЗАЦИИ ===
        cache_frame = ttk.LabelFrame(main_frame, text="⚡ Управление кэшированием и оптимизациями", padding="15")
        cache_frame.pack(fill=tk.X, pady=10)
        
        cache_buttons_frame = ttk.Frame(cache_frame)
        cache_buttons_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(cache_buttons_frame, text="🗑️ Очистить кэш", 
                  command=self.clear_cache).pack(side=tk.LEFT, padx=5)
        ttk.Button(cache_buttons_frame, text="📊 Статистика кэша", 
                  command=self.show_cache_stats).pack(side=tk.LEFT, padx=5)
        ttk.Button(cache_buttons_frame, text="📈 Статистика оптимизаций", 
                  command=self.show_optimization_stats).pack(side=tk.LEFT, padx=5)  # ✅ НОВАЯ КНОПКА
        ttk.Button(cache_buttons_frame, text="🔄 Перезагрузить инструменты", 
                  command=lambda: self.load_all_instruments(force_refresh=True)).pack(side=tk.LEFT, padx=5)
        
        # В секции "Управление кэшированием и оптимизациями" ДОБАВЬТЕ:

        # Новые кнопки для расширенной аналитики
        advanced_buttons_frame = ttk.Frame(cache_frame)
        advanced_buttons_frame.pack(fill=tk.X, pady=5)

        ttk.Button(advanced_buttons_frame, text="📊 Расширенная аналитика", 
                command=self.show_advanced_analytics).pack(side=tk.LEFT, padx=5)

        ttk.Button(advanced_buttons_frame, text="🎛️ Дашборд производительности", 
                command=self.show_performance_dashboard).pack(side=tk.LEFT, padx=5)
        
        # В секции "Управление кэшированием и оптимизациями" ДОБАВИМ:

        # Новые кнопки для AI-функций
        ai_buttons_frame = ttk.Frame(cache_frame)
        ai_buttons_frame.pack(fill=tk.X, pady=5)

        ttk.Button(ai_buttons_frame, text="🤖 AI Предсказания", 
                command=self.show_ai_predictions).pack(side=tk.LEFT, padx=5)

        ttk.Button(ai_buttons_frame, text="⚡ Автооптимизация", 
                command=self.toggle_auto_optimization).pack(side=tk.LEFT, padx=5)

        ttk.Button(ai_buttons_frame, text="📊 История оптимизаций", 
                command=self.show_optimization_history).pack(side=tk.LEFT, padx=5)

        # В секции "Управление кэшированием и оптимизациями" после AI кнопок:

        # Кнопки для управления памятью
        memory_buttons_frame = ttk.Frame(cache_frame)
        memory_buttons_frame.pack(fill=tk.X, pady=5)

        ttk.Button(memory_buttons_frame, text="🧹 Очистка памяти", 
                command=self.force_memory_cleanup).pack(side=tk.LEFT, padx=5)

        ttk.Button(memory_buttons_frame, text="🚨 Управление алертами", 
                command=self.manage_memory_alerts).pack(side=tk.LEFT, padx=5)

        ttk.Button(memory_buttons_frame, text="📉 Настройки памяти", 
                command=self.configure_memory_settings).pack(side=tk.LEFT, padx=5)

        # Индикатор памяти
        self.memory_status_var = tk.StringVar(value="💾 Память: Норма")
        memory_status_label = ttk.Label(cache_frame, textvariable=self.memory_status_var,
                                    foreground="green", font=('Arial', 9, 'bold'))
        memory_status_label.pack(pady=2)

        # Запускаем мониторинг памяти
        self._start_memory_monitoring()

        # Индикатор статуса AI
        self.ai_status_var = tk.StringVar(value="🤖 AI: Активен")
        ai_status_label = ttk.Label(cache_frame, textvariable=self.ai_status_var,
                                foreground="green", font=('Arial', 9, 'bold'))
        ai_status_label.pack(pady=2)

        # Обновленная информация о режиме
        mode_label = ttk.Label(cache_frame, 
                            text="Режим: 🚀 Расширенная аналитика активна", 
                            foreground="blue", 
                            font=('Arial', 10, 'bold'))
        mode_label.pack(pady=5)

        # Информация о режиме оптимизаций
        mode_label = ttk.Label(cache_frame, text="Режим: 🛡️ Безопасные оптимизации активны", 
                              foreground="green", font=('Arial', 9, 'bold'))
        mode_label.pack(pady=5)
        
        # Информация о загрузке
        self.info_text = scrolledtext.ScrolledText(main_frame, height=6, font=('Arial', 9))
        self.info_text.pack(fill=tk.BOTH, expand=True, pady=10)
        self.info_text.insert(tk.END, "Добро пожаловать в T-Банк API!\n\n")
        self.info_text.insert(tk.END, "1. Настройте API токен\n")
        self.info_text.insert(tk.END, "2. Найдите нужный инструмент\n")
        self.info_text.insert(tk.END, "3. Загрузите исторические данные\n")
        self.info_text.insert(tk.END, "4. Используйте данные в торговой системе\n")
        self.info_text.config(state=tk.DISABLED)
        
        # Загружаем сохраненный токен
        self.load_saved_token()
        
    def show_optimization_stats(self):
        """Показать статистику оптимизаций (ОБНОВЛЕННАЯ ВЕРСИЯ)"""
        try:
            stats = self.data_loader.get_performance_stats()
            analytics = self.data_loader.get_detailed_analytics()
            
            # Получаем AI статистику
            prediction_stats = self.data_loader.data_manager.get_prediction_stats()
            optimization_info = self.data_loader.data_manager.get_optimization_info()
            
            stats_text = f"""📊 РАСШИРЕННАЯ СТАТИСТИКА СИСТЕМЫ

            🎯 ОСНОВНЫЕ МЕТРИКИ:
            • Запросов: {stats['total_requests']}
            • Попаданий в кэш: {stats['cache_hits']} ({stats['cache_hit_ratio']})
            • Экономия памяти: {stats['memory_savings_mb']} MB
            • Средняя экономия: {stats['avg_savings_per_request']} MB/запрос

            🤖 AI СИСТЕМА:
            • Предсказаний: {prediction_stats.get('total_predictions', 0)}
            • Точность: {prediction_stats.get('prediction_accuracy', 0):.1%}
            • Автооптимизация: {'ВКЛ' if optimization_info['auto_optimization_enabled'] else 'ВЫКЛ'}
            • Оптимизаций: {optimization_info['optimization_history_count']}

            💾 СОСТОЯНИЕ КЭША:
            • Файлов инструментов: {analytics.get('instruments_cache_size', 0)}
            • Файлов свечей: {analytics.get('candles_cache_size', 0)}
            • Общий размер: {analytics.get('total_cache_size_mb', 0):.2f} MB
            • Записей в памяти: {analytics.get('memory_cache_entries', 0)}

            📈 ПРОИЗВОДИТЕЛЬНОСТЬ:
            • Тренд Hit Ratio: {analytics.get('hit_ratio_trend', 'stable')}
            • Использование памяти: {analytics.get('memory_usage_mb', 0):.1f} MB
            • Активных алертов: {analytics.get('active_alerts_count', 0)}"""

            messagebox.showinfo("Расширенная статистика", stats_text)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить статистику: {str(e)}")
                
    def show_ai_predictions(self):
        """Показать AI предсказания и статистику"""
        try:
            # Получаем статистику предсказаний
            prediction_stats = self.data_loader.data_manager.get_prediction_stats()
            
            # Получаем вероятные запросы
            likely_requests = self.data_loader.data_manager.smart_predictor.get_likely_requests(hours_ahead=24)
            
            prediction_text = f"""🤖 AI СИСТЕМА ПРЕДСКАЗАНИЙ

            📊 СТАТИСТИКА ПРЕДСКАЗАНИЙ:
            • Всего предсказаний: {prediction_stats.get('total_predictions', 0)}
            • Успешных предсказаний: {prediction_stats.get('successful_predictions', 0)}
            • Точность: {prediction_stats.get('prediction_accuracy', 0):.1%}

            🔮 ВЕРОЯТНЫЕ ЗАПРОСЫ (следующие 24 часа):"""
            
            if likely_requests:
                for i, ((symbol, timeframe), probability) in enumerate(likely_requests[:5]):  # Топ-5
                    status = "✅ ВЫСОКАЯ" if probability > 0.7 else "⚠️ СРЕДНЯЯ" if probability > 0.4 else "ℹ️ НИЗКАЯ"
                    prediction_text += f"\n{i+1}. {symbol} ({timeframe}) - {probability:.1%} - {status}"
            else:
                prediction_text += "\n📭 Пока нет данных для предсказаний"
            
            # Информация о популярных инструментах
            popular_symbols = self.data_loader.data_manager.smart_predictor.get_popular_symbols()
            if popular_symbols:
                prediction_text += f"\n\n🏆 ПОПУЛЯРНЫЕ ИНСТРУМЕНТЫ:"
                for i, ((symbol, timeframe), count) in enumerate(popular_symbols[:3]):
                    prediction_text += f"\n{i+1}. {symbol} ({timeframe}) - {count} обращений"
            
            messagebox.showinfo("AI Предсказания", prediction_text)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить AI предсказания: {str(e)}")

    def toggle_auto_optimization(self):
        """Включить/выключить автооптимизацию"""
        try:
            current_state = self.data_loader.data_manager.auto_optimizer.config['optimization_enabled']
            new_state = not current_state
            
            # Обновляем конфигурацию
            self.data_loader.data_manager.auto_optimizer.update_config({
                'optimization_enabled': new_state
            })
            
            status = "ВКЛЮЧЕНА" if new_state else "ВЫКЛЮЧЕНА"
            color = "green" if new_state else "red"
            self.ai_status_var.set(f"🤖 AI: {status}")
            
            # Обновляем цвет индикатора
            for widget in self.frame.winfo_children():
                if hasattr(widget, 'winfo_children'):
                    for child in widget.winfo_children():
                        if isinstance(child, ttk.Label) and child.cget('textvariable') == str(self.ai_status_var):
                            child.configure(foreground=color)
            
            messagebox.showinfo("Автооптимизация", 
                            f"Автооптимизация {status.lower()}!\n\n"
                            f"Система будет {'автоматически оптимизировать параметры' if new_state else 'работать в ручном режиме'}.")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось изменить настройки оптимизации: {str(e)}")

    def show_optimization_history(self):
        """Показать историю оптимизаций"""
        try:
            history = self.data_loader.data_manager.auto_optimizer.get_optimization_history(last_n=10)
            
            history_text = "📋 ИСТОРИЯ АВТООПТИМИЗАЦИЙ:\n\n"
            
            if history:
                for i, record in enumerate(reversed(history)):  # Последние сначала
                    timestamp = datetime.fromisoformat(record['timestamp']).strftime('%d.%m %H:%M')
                    history_text += f"🕒 {timestamp}:\n"
                    
                    for action in record.get('actions', []):
                        action_type = action.get('type', 'unknown')
                        reason = action.get('reason', '')
                        
                        if action_type == 'auto_cleanup':
                            history_text += f"   🗑️ Автоочистка: {reason}\n"
                        elif action_type == 'increase_ttl':
                            history_text += f"   ⬆️ Увеличение TTL: {reason}\n"
                        elif action_type == 'decrease_ttl':
                            history_text += f"   ⬇️ Уменьшение TTL: {reason}\n"
                        else:
                            history_text += f"   ⚙️ {action_type}: {reason}\n"
                    
                    # Добавляем статистику на момент оптимизации
                    snapshot = record.get('analytics_snapshot', {})
                    if snapshot:
                        history_text += f"   📊 Hit Ratio: {snapshot.get('hit_ratio', 'N/A')}\n"
                        history_text += f"   💾 Размер кэша: {snapshot.get('cache_size_mb', 0):.1f} MB\n\n"
            else:
                history_text += "📭 Оптимизации еще не выполнялись\n\n"
            
            # Текущие настройки оптимизации
            config = self.data_loader.data_manager.auto_optimizer.config
            history_text += f"⚙️ ТЕКУЩИЕ НАСТРОЙКИ:\n"
            history_text += f"• Автооптимизация: {'ВКЛ' if config['optimization_enabled'] else 'ВЫКЛ'}\n"
            history_text += f"• Автоочистка: {'ВКЛ' if config['auto_cleanup_enabled'] else 'ВЫКЛ'}\n"
            history_text += f"• Порог очистки: {config['cleanup_threshold_mb']} MB\n"
            history_text += f"• Макс. размер: {config['max_cache_size_mb']} MB\n"
            
            messagebox.showinfo("История оптимизаций", history_text)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить историю оптимизаций: {str(e)}")    
    
    def load_saved_token(self):
        """Загрузка сохраненного токена"""
        try:
            # Используем токен из основного config.py
            saved_token = Config.TINKOFF_TOKEN
            if saved_token and saved_token.strip():
                self.token_var.set(saved_token)
                self.log_info(f"✅ Загружен токен API из config.py")
            else:
                self.log_info(f"⚠️ Токен не найден в config.py")
        except Exception as e:
            self.log_error(f"Ошибка загрузки токена: {e}")
    
    def save_token(self):
        """Сохранение токена API"""
        token = self.token_var.get().strip()
        if not token:
            messagebox.showwarning("Предупреждение", "Введите API токен")
            return
        
        try:
            from config import Config
            Config.set_tinkoff_token(token)
            messagebox.showinfo("Успех", "✅ Токен успешно сохранен!")
            self.log_info("✅ Токен API сохранен")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сохранения токена: {str(e)}")
            
    
    def test_connection(self):
        """Проверка подключения к API"""
        token = self.token_var.get().strip()
        if not token:
            messagebox.showwarning("Предупреждение", "Введите API токен")
            return
        
        try:
            test_loader = TBankDataLoader(token)
            if test_loader.is_configured():
                messagebox.showinfo("Успех", "✅ Подключение к T-Банк API успешно!")
                self.log_info("✅ Подключение к API успешно")
            else:
                messagebox.showerror("Ошибка", "❌ Не удалось подключиться к API")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка подключения: {str(e)}")
    
    def load_all_instruments(self, force_refresh=False):
        """Загрузка всех инструментов"""
        if not self.data_loader.is_configured():
            messagebox.showwarning("Предупреждение", "Сначала настройте API токен")
            return
        
        try:
            self.log_info("🔄 Загрузка списка инструментов...")
            
            instruments_df = self.data_loader.get_available_symbols()
            
            if instruments_df.empty:
                self.log_error("Не удалось загрузить инструменты")
                return
            
            # Очищаем таблицу
            for item in self.instruments_tree.get_children():
                self.instruments_tree.delete(item)
            
            # Заполняем таблицу
            for _, instrument in instruments_df.iterrows():
                self.instruments_tree.insert('', tk.END, values=(
                    instrument.get('symbol', ''),
                    instrument.get('name', ''),
                    instrument.get('type', ''),
                    instrument.get('currency', '')
                ))
            
            self.available_instruments = instruments_df
            self.log_info(f"✅ Загружено {len(instruments_df)} инструментов")
            
        except Exception as e:
            self.log_error(f"Ошибка загрузки инструментов: {str(e)}")
    
    def search_instruments(self, query):
        """Поиск инструментов"""
        if not query:
            self.load_all_instruments()
            return
        
        if self.available_instruments is None:
            messagebox.showwarning("Предупреждение", "Сначала загрузите список инструментов")
            return
        
        try:
            mask = (self.available_instruments['symbol'].str.contains(query, case=False, na=False) | 
                    self.available_instruments['name'].str.contains(query, case=False, na=False))
            
            filtered_instruments = self.available_instruments[mask]
            
            # Очищаем таблицу
            for item in self.instruments_tree.get_children():
                self.instruments_tree.delete(item)
            
            # Заполняем таблицу отфильтрованными данными
            for _, instrument in filtered_instruments.iterrows():
                self.instruments_tree.insert('', tk.END, values=(
                    instrument.get('symbol', ''),
                    instrument.get('name', ''),
                    instrument.get('type', ''),
                    instrument.get('currency', '')
                ))
            
            self.log_info(f"🔍 Найдено {len(filtered_instruments)} инструментов по запросу '{query}'")
            
        except Exception as e:
            self.log_error(f"Ошибка поиска: {str(e)}")
    
    def on_instrument_select(self, event):
        """Обработчик выбора инструмента в таблице"""
        selection = self.instruments_tree.selection()
        if selection:
            item = self.instruments_tree.item(selection[0])
            ticker = item['values'][0]
            self.symbol_var.set(ticker)
            self.log_info(f"✅ Выбран инструмент: {ticker}")
    
    def load_data(self):
        """Загрузка исторических данных (ОБНОВЛЕННАЯ ВЕРСИЯ)"""
        symbol = self.symbol_var.get().strip()
        if not symbol:
            messagebox.showwarning("Предупреждение", "Выберите или введите тикер инструмента")
            return
        
        days_back = self.days_back_var.get()
        timeframe = self.timeframe_var.get()
        
        if days_back <= 0:
            messagebox.showwarning("Предупреждение", "Количество дней должно быть положительным")
            return
        
        try:
            self.log_info(f"🔄 Загрузка данных для {symbol}...")
            
            use_cache = self.cache_enabled.get()
            
            # ✅ ЗАПИСЫВАЕМ ОБРАЩЕНИЕ ДЛЯ AI ПРЕДСКАЗАНИЙ (ЗАЩИЩЕННАЯ ВЕРСИЯ)
            try:
                # Проверяем, что smart_predictor существует и доступен
                if (hasattr(self.data_loader, 'data_manager') and 
                    hasattr(self.data_loader.data_manager, 'smart_predictor') and
                    hasattr(self.data_loader.data_manager.smart_predictor, 'record_access')):
                    
                    self.data_loader.data_manager.smart_predictor.record_access(symbol, timeframe)
                    self.log_info(f"🔮 AI: записано обращение к {symbol} ({timeframe})")
                else:
                    logger.debug("AI predictor недоступен для записи обращений")
            except Exception as e:
                logger.debug(f"Не удалось записать обращение для AI: {e}")
            
            # Загружаем данные
            data = self.data_loader.load_price_data(
                symbol=symbol,
                days_back=days_back,
                timeframe=timeframe,
                use_cache=use_cache
            )
            
            if data.empty:
                self.log_error(f"Не удалось загрузить данные для {symbol}")
                messagebox.showerror("Ошибка", 
                    f"Не удалось загрузить данные для {symbol}.\n"
                    f"Возможные причины:\n"
                    f"• Неправильный тикер\n"
                    f"• Проблемы с подключением к API\n"
                    f"• Нет данных за выбранный период")
                return
            
            self.loaded_data = data
            
            # Форматируем информацию о загруженных данных
            try:
                min_date = data.index.min().strftime('%Y-%m-%d')
                max_date = data.index.max().strftime('%Y-%m-%d')
                min_price = data['close'].min()
                max_price = data['close'].max()
            except Exception as e:
                logger.warning(f"Ошибка форматирования данных: {e}")
                min_date = "N/A"
                max_date = "N/A" 
                min_price = 0
                max_price = 0
            
            info_lines = [
                f"✅ ДАННЫЕ УСПЕШНО ЗАГРУЖЕНЫ",
                f"📊 Инструмент: {symbol}",
                f"📅 Период: {min_date} - {max_date}",
                f"📈 Записей: {len(data)}",
                f"💵 Диапазон цен: {min_price:.2f} - {max_price:.2f}",
                f"⏰ Таймфрейм: {timeframe}",
                f"💾 Кэширование: {'ВКЛ' if use_cache else 'ВЫКЛ'}"
            ]
            
            self.log_info("\n".join(info_lines))
            
            # Показываем статистику производительности, если доступно
            try:
                if hasattr(self.data_loader, 'get_performance_stats'):
                    stats = self.data_loader.get_performance_stats()
                    cache_info = f" (Hit Ratio: {stats.get('cache_hit_ratio', 'N/A')})" if use_cache else ""
                    self.log_info(f"⚡ Производительность: {stats.get('total_requests', 0)} запросов{cache_info}")
            except Exception as e:
                logger.debug(f"Не удалось получить статистику производительности: {e}")
            
            messagebox.showinfo(
                "Успех", 
                f"Данные для {symbol} успешно загружены!\n\n"
                f"📊 Записей: {len(data)}\n"
                f"📅 Период: {days_back} дней\n"
                f"⏰ Таймфрейм: {timeframe}\n"
                f"💾 Кэширование: {'ВКЛ' if use_cache else 'ВЫКЛ'}\n\n"
                f"Теперь вы можете использовать данные в торговой системе."
            )
            
        except Exception as e:
            error_msg = f"❌ Ошибка загрузки данных: {str(e)}"
            self.log_error(error_msg)
            # Более информативное сообщение об ошибке
            detailed_error = (
                f"Ошибка загрузки данных для {symbol}:\n\n"
                f"{str(e)}\n\n"
                f"Проверьте:\n"
                f"• Правильность тикера\n" 
                f"• Наличие интернет-подключения\n"
                f"• Корректность API ключа\n"
                f"• Доступность инструмента"
            )
            messagebox.showerror("Ошибка загрузки", detailed_error)

    def update_recent_data(self):
        """Инкрементальное обновление свежих данных"""
        symbol = self.symbol_var.get().strip()
        if not symbol:
            messagebox.showwarning("Предупреждение", "Введите символ для обновления")
            return
        
        try:
            self.log_info(f"🔄 Обновление свежих данных для {symbol}...")
            
            updated_data = self.data_loader.update_recent_data(symbol, days_back=3)
            
            if not updated_data.empty:
                self.loaded_data = updated_data
                self.log_info(f"✅ Данные обновлены! Добавлено {len(updated_data)} новых записей")
                messagebox.showinfo("Успех", 
                    f"Данные для {symbol} успешно обновлены\n"
                    f"Добавлено {len(updated_data)} новых записей")
            else:
                self.log_info("ℹ️ Нет новых данных или данные уже актуальны")
                messagebox.showinfo("Информация", 
                    f"Нет новых данных для {symbol} или данные уже актуальны")
                
        except Exception as e:
            error_msg = f"❌ Ошибка обновления данных: {str(e)}"
            self.log_error(error_msg)
            messagebox.showerror("Ошибка", error_msg)
    
    def use_in_main_system(self):
        """Использование загруженных данных в основной системе"""
        if self.loaded_data is None or self.loaded_data.empty:
            messagebox.showwarning("Предупреждение", "Сначала загрузите данные")
            return
        
        try:
            if hasattr(self.main_app, 'current_api_data'):
                self.main_app.current_api_data = self.loaded_data
                
                symbol = self.symbol_var.get().strip()
                self.log_info(f"🎯 Данные для {symbol} переданы в торговую систему")
                
                messagebox.showinfo(
                    "Успех", 
                    f"Данные для {symbol} готовы к использованию в торговой системе!\n\n"
                    f"Теперь вы можете:\n"
                    f"1. Перейти на вкладку 'Управление системой'\n"
                    f"2. Нажать 'Запустить тест'\n"
                    f"3. Проанализировать результаты"
                )
                
                if hasattr(self.main_app, 'data_file'):
                    self.main_app.data_file.set("tbank_api_loaded_data")
                    
            else:
                messagebox.showerror("Ошибка", "Не удалось передать данные в основную систему")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка передачи данных: {str(e)}")
    
    def clear_cache(self):
        """Очистка кэша"""
        try:
            if messagebox.askyesno("Очистка кэша", 
                                  "Вы уверены, что хотите очистить весь кэш?\n\n"
                                  "Это удалит все сохраненные данные инструментов и свечей."):
                self.data_loader.clear_cache()
                self.log_info("🗑️ Кэш успешно очищен")
                messagebox.showinfo("Успех", "Кэш успешно очищен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка очистки кэша: {str(e)}")
    
    def show_cache_stats(self):
        """Показать статистику кэша"""
        try:
            stats = self.data_loader.get_cache_stats()
            
            stats_text = f"""📊 СТАТИСТИКА КЭША:

            • Файлов инструментов: {stats.get('instruments_cache_size', 0)}
            • Файлов свечей: {stats.get('candles_cache_size', 0)}
            • Записей в памяти: {stats.get('memory_cache_entries', 0)}
            • Общий размер: {stats.get('total_cache_size_mb', 0):.2f} MB

            💡 Кэширование ускоряет загрузку данных
            и уменьшает количество запросов к API."""
            
            messagebox.showinfo("Статистика кэша", stats_text)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить статистику: {str(e)}")
    
    def log_info(self, message):
        """Добавление информационного сообщения в лог"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, f"\n[{datetime.now().strftime('%H:%M:%S')}] {message}")
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)
    
    def log_error(self, message):
        """Добавление сообщения об ошибке в лог"""
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, f"\n[{datetime.now().strftime('%H:%M:%S')}] ❌ {message}")
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)
    
    def get_frame(self):
        """Возвращает фрейм вкладки"""
        return self.frame

    def show_advanced_analytics(self):
        """Показать расширенную аналитику"""
        try:
            analytics = self.data_loader.get_advanced_analytics()
            
            basic_stats = analytics['basic_stats']
            cache_info = analytics['cache_info']
            trends = analytics['advanced_trends']
            alerts = analytics['active_alerts']
            metrics_history = analytics['metrics_history']
            
            # Формируем текст аналитики
            analytics_text = f"""📊 РАСШИРЕННАЯ АНАЛИТИКА СИСТЕМЫ

            🎯 ОСНОВНЫЕ МЕТРИКИ:
            • Запросов: {basic_stats['total_requests']}
            • Попаданий в кэш: {basic_stats['cache_hits']} ({basic_stats['cache_hit_ratio']})
            • Экономия памяти: {basic_stats['memory_savings_mb']} MB

            💾 СОСТОЯНИЕ КЭША:
            • Файлов инструментов: {cache_info.get('instruments_cache_size', 0)}
            • Файлов свечей: {cache_info.get('candles_cache_size', 0)}
            • Общий размер: {cache_info.get('total_cache_size_mb', 0):.2f} MB

            📈 ТРЕНДЫ ПРОИЗВОДИТЕЛЬНОСТИ:
            • Hit Ratio: {trends.get('hit_ratio_trend', 'stable')}
            • Время ответа: {trends.get('response_time_trend', 'stable')}
            • Активных алертов: {trends.get('active_alerts', 0)}
            • Время работы: {trends.get('uptime_hours', 0):.1f} часов
            • Точек данных: {trends.get('data_points', 0)}"""

            # Добавляем алерты если есть
            if alerts:
                analytics_text += "\n\n🚨 АКТИВНЫЕ АЛЕРТЫ:\n"
                for i, alert in enumerate(alerts[:5]):  # Показываем первые 5
                    level_icon = "⚠️" if alert['level'] == 'warning' else "❌"
                    analytics_text += f"{i+1}. {level_icon} [{alert['level']}] {alert['title']}\n"
                    analytics_text += f"   📝 {alert['message']}\n"
                    # Форматируем время
                    if 'timestamp' in alert:
                        try:
                            from datetime import datetime
                            alert_time = datetime.fromisoformat(alert['timestamp'].replace('Z', '+00:00'))
                            analytics_text += f"   🕒 {alert_time.strftime('%H:%M:%S')}\n"
                        except:
                            analytics_text += f"   🕒 {alert['timestamp']}\n"
            
            # Добавляем историю метрик
            hit_history = metrics_history.get('hit_ratio', [])
            if hit_history:
                latest_hit = hit_history[-1]['value'] if hit_history else 0
                analytics_text += f"\n📋 ИСТОРИЯ МЕТРИК (последние {len(hit_history)} точек)"
                analytics_text += f"\n• Последний Hit Ratio: {latest_hit:.1%}"
            
            messagebox.showinfo("Расширенная аналитика", analytics_text)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось получить аналитику: {str(e)}")

    def show_performance_dashboard(self):
        """Показать дашборд производительности"""
        try:
            analytics = self.data_loader.get_detailed_analytics()
            
            # Определяем статус системы
            status_icon = "✅" if analytics.get('status') == 'active' else "⚠️"
            hit_ratio = float(analytics.get('cache_hit_ratio', '0%').rstrip('%'))
            
            if hit_ratio > 70:
                performance_status = "Отличная"
                status_color = "🟢"
            elif hit_ratio > 40:
                performance_status = "Хорошая" 
                status_color = "🟡"
            else:
                performance_status = "Требует оптимизации"
                status_color = "🔴"
            
            dashboard_text = f"""🎛️ ДАШБОРД ПРОИЗВОДИТЕЛЬНОСТИ

            {status_icon} СТАТУС СИСТЕМЫ: {analytics.get('status', 'unknown')}
            {status_color} ПРОИЗВОДИТЕЛЬНОСТЬ: {performance_status}

            📊 ОСНОВНЫЕ ПОКАЗАТЕЛИ:
            • Hit Ratio: {analytics.get('cache_hit_ratio', '0%')}
            • Среднее время ответа: {analytics.get('avg_response_time_ms', 0):.1f} ms
            • Тренд производительности: {analytics.get('hit_ratio_trend', 'stable')}

            💾 ИСПОЛЬЗОВАНИЕ РЕСУРСОВ:
            • Использование памяти: {analytics.get('memory_usage_mb', 0):.1f} MB
            • Размер кэша: {analytics.get('total_cache_size_mb', 0):.1f} MB
            • Активных алертов: {analytics.get('active_alerts_count', 0)}

            🕒 СИСТЕМНЫЕ МЕТРИКИ:
            • Время работы: {analytics.get('uptime_hours', 0):.1f} часов
            • Всего запросов: {analytics.get('total_requests', 0)}
            • Попаданий в кэш: {analytics.get('cache_hits', 0)}
            • Промахов кэша: {analytics.get('cache_misses', 0)}

            ⚡ ФУНКЦИОНАЛЬНОСТЬ:
            • Расширенная аналитика: {'Включена' if analytics.get('features', {}).get('advanced_analytics') else 'Выключена'}
            • Мониторинг производительности: {'Активен' if analytics.get('features', {}).get('performance_monitoring') else 'Неактивен'}
            • Метрики в реальном времени: {'Работают' if analytics.get('features', {}).get('real_time_metrics') else 'Не работают'}"""

            messagebox.showinfo("Дашборд производительности", dashboard_text)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить дашборд: {str(e)}")

    def _start_memory_monitoring(self):
        """Запуск мониторинга памяти в фоне"""
        def memory_monitor():
            while True:
                try:
                    self._update_memory_status()
                    time.sleep(30)  # Проверяем каждые 30 секунд
                except Exception as e:
                    logger.error(f"Ошибка мониторинга памяти: {e}")
                    time.sleep(60)
        
        thread = threading.Thread(target=memory_monitor, daemon=True)
        thread.start()

    def _update_memory_status(self):
        """Обновление статуса памяти"""
        try:
            analytics = self.data_loader.get_detailed_analytics()
            memory_usage = analytics.get('memory_usage_mb', 0)
            
            if memory_usage > 2000:
                status = "🚨 КРИТИЧЕСКИ"
                color = "red"
            elif memory_usage > 1500:
                status = "⚠️ ВЫСОКОЕ"
                color = "orange"
            elif memory_usage > 1000:
                status = "ℹ️ ПОВЫШЕННОЕ"
                color = "blue"
            else:
                status = "✅ НОРМА"
                color = "green"
            
            # Обновляем в основном потоке
            self.frame.after(0, lambda: self._update_memory_ui(f"💾 Память: {status} ({memory_usage:.0f} MB)", color))
            
        except Exception as e:
            logger.debug(f"Не удалось обновить статус памяти: {e}")

    def _update_memory_ui(self, text: str, color: str):
        """Обновление UI памяти в основном потоке"""
        self.memory_status_var.set(text)
        # Находим и обновляем лейбл
        for widget in self.frame.winfo_children():
            if hasattr(widget, 'winfo_children'):
                for child in widget.winfo_children():
                    if isinstance(child, ttk.Label) and child.cget('textvariable') == str(self.memory_status_var):
                        child.configure(foreground=color)

    def force_memory_cleanup(self):
        """Принудительная очистка памяти"""
        try:
            # Очищаем кэш
            self.data_loader.clear_cache()
            
            # Очищаем memory cache
            if hasattr(self.data_loader.data_manager.cache, '_memory_cache'):
                self.data_loader.data_manager.cache._memory_cache.clear()
            
            # Сбор мусора
            import gc
            gc.collect()
            
            # Получаем обновленную статистику
            analytics = self.data_loader.get_detailed_analytics()
            memory_after = analytics.get('memory_usage_mb', 0)
            
            messagebox.showinfo(
                "Очистка памяти", 
                f"✅ Память успешно очищена!\n\n"
                f"Текущее использование: {memory_after:.0f} MB\n"
                f"Кэш очищен, сборка мусора выполнена."
            )
            
            self.log_info("🧹 Выполнена принудительная очистка памяти")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось очистить память: {str(e)}")

    def manage_memory_alerts(self):
        """Управление алертами памяти (упрощенная версия)"""
        try:
            analytics = self.data_loader.get_detailed_analytics()
            active_alerts = self.data_loader.data_manager.advanced_analytics.get_active_alerts()
            
            memory_alerts = [alert for alert in active_alerts if alert.get('type') == 'memory']
            
            alert_text = f"""🚨 УПРАВЛЕНИЕ АЛЕРТАМИ ПАМЯТИ

    Текущее использование: {analytics.get('memory_usage_mb', 0):.0f} MB
    Активных алертов памяти: {len(memory_alerts)}

    """
            if memory_alerts:
                alert_text += "АКТИВНЫЕ АЛЕРТЫ:\n"
                for i, alert in enumerate(memory_alerts):
                    alert_text += f"{i+1}. {alert.get('title', '')}\n"
                    alert_text += f"   {alert.get('message', '')}\n"
                    
                    # ✅ ПРОСТАЯ И НАДЕЖНАЯ ОБРАБОТКА ВРЕМЕНИ
                    timestamp = alert.get('timestamp')
                    if hasattr(timestamp, 'strftime'):
                        # Объект datetime
                        time_str = timestamp.strftime('%H:%M:%S')
                    else:
                        # Строка или другой формат
                        time_str = str(timestamp)[11:19] if len(str(timestamp)) > 10 else str(timestamp)
                    
                    alert_text += f"   Время: {time_str}\n\n"
            else:
                alert_text += "✅ Нет активных алертов памяти\n\n"
            
            # Остальной код без изменений...
            
            # Создаем диалог с кнопками
            dialog = tk.Toplevel(self.frame)
            dialog.title("Управление алертами памяти")
            dialog.geometry("500x400")
            dialog.transient(self.frame)
            dialog.grab_set()
            
            # Текст алертов
            text_widget = scrolledtext.ScrolledText(dialog, height=15, width=60)
            text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
            text_widget.insert(tk.END, alert_text)
            text_widget.config(state=tk.DISABLED)
            
            # Кнопки действий
            button_frame = ttk.Frame(dialog)
            button_frame.pack(pady=10)
            
            if memory_alerts:
                ttk.Button(button_frame, text="✅ Подтвердить все алерты",
                        command=lambda: self.acknowledge_all_memory_alerts(dialog)).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(button_frame, text="🧹 Очистка памяти",
                    command=lambda: self.cleanup_and_close(dialog)).pack(side=tk.LEFT, padx=5)
            
            ttk.Button(button_frame, text="Закрыть",
                    command=dialog.destroy).pack(side=tk.LEFT, padx=5)
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось управлять алертами: {str(e)}")

    def acknowledge_all_memory_alerts(self, dialog=None):
        """Подтвердить все алерты памяти (безопасная версия)"""
        try:
            active_alerts = self.data_loader.data_manager.advanced_analytics.get_active_alerts()
            memory_alerts = [i for i, alert in enumerate(active_alerts) if alert.get('type') == 'memory']
            
            confirmed_count = 0
            for alert_index in memory_alerts:
                try:
                    self.data_loader.data_manager.advanced_analytics.acknowledge_alert(alert_index)
                    confirmed_count += 1
                except Exception as e:
                    logger.warning(f"Не удалось подтвердить алерт {alert_index}: {e}")
            
            if dialog:
                dialog.destroy()
            
            messagebox.showinfo("Успех", f"✅ Подтверждено {confirmed_count} алертов памяти")
            self.log_info(f"✅ Подтверждены алерты памяти ({confirmed_count} шт.)")
            
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось подтвердить алерты: {str(e)}")

    def cleanup_and_close(self, dialog):
        """Очистка памяти и закрытие диалога"""
        self.force_memory_cleanup()
        if dialog:
            dialog.destroy()

    def configure_memory_settings(self):
        """Настройка параметров памяти"""
        try:
            config = self.data_loader.data_manager.auto_optimizer.config
            
            settings_text = f"""⚙️ НАСТРОЙКИ ПАМЯТИ И ОПТИМИЗАЦИИ

            Текущие настройки:
            • Автоочистка: {'ВКЛ' if config['auto_cleanup_enabled'] else 'ВЫКЛ'}
            • Порог очистки: {config['cleanup_threshold_mb']} MB
            • Макс. размер кэша: {config['max_cache_size_mb']} MB
            • Минимальный Hit Ratio: {config['min_hit_ratio_for_cleanup']}%

            Рекомендации для текущей системы:
            • Порог очистки: 500-1000 MB
            • Макс. размер: 1000-2000 MB  
            • Hit Ratio: 20-30%

            Хотите применить рекомендуемые настройки?"""
            
            if messagebox.askyesno("Настройки памяти", settings_text):
                # Применяем рекомендуемые настройки
                new_config = {
                    'cleanup_threshold_mb': 800,
                    'max_cache_size_mb': 1500,
                    'min_hit_ratio_for_cleanup': 25,
                    'auto_cleanup_enabled': True
                }
                
                self.data_loader.data_manager.auto_optimizer.update_config(new_config)
                
                messagebox.showinfo(
                    "Успех", 
                    "✅ Настройки памяти обновлены!\n\n"
                    "Новые параметры:\n"
                    "• Порог очистки: 800 MB\n"
                    "• Макс. размер: 1500 MB\n"
                    "• Min Hit Ratio: 25%\n"
                    "• Автоочистка: ВКЛ"
                )
                self.log_info("⚙️ Применены рекомендуемые настройки памяти")
                
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось настроить параметры: {str(e)}")


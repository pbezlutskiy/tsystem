# ===== СЕКЦИЯ 16: ГЛАВНОЕ ОКНО ПРИЛОЖЕНИЯ =====

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
from typing import Optional
import matplotlib
matplotlib.use('TkAgg')
from datetime import datetime
import pandas as pd
import numpy as np

# Импорт основных компонентов
from core.trading_system import SeikotaTradingSystem
from core.visualizer import ResultsVisualizer
from utils.data_loader import load_price_data_from_file
from utils.analytics import analyze_performance
from utils.error_handler import with_error_handling

# Импорт вкладок
from gui.tabs import (
    PriceTab, CapitalTab, PositionTab, ReturnsTab, 
    CorrelationTab, TradesTab, StatsTab, CompareTab, RiskTab,
    RiskAnalysisTab
)

from gui.components import FileBrowser, ResultsComboBox, StyledButton

# ✅ ДОБАВЬТЕ ПОСЛЕ СУЩЕСТВУЮЩИХ ИМПОРТОВ:
try:
    from gui.tabs.instruments_tab_working import InstrumentsTabWorking as InstrumentsTab
    INSTRUMENTS_AVAILABLE = True
    print("✅ Рабочая вкладка инструментов загружена")
except ImportError as e:
    print(f"ℹ️ Рабочая вкладка инструментов не доступна: {e}")
    INSTRUMENTS_AVAILABLE = False


# 🔧 ПЫТАЕМСЯ ИМПОРТИРОВАТЬ МОДУЛЬ Т-БАНКА
try:
    from tbank_api.tbank_gui import TBankApiTab
    TBANK_AVAILABLE = True
    print("✅ Модуль Т-банка API успешно загружен")
except ImportError as e:
    print(f"ℹ️ Модуль Т-банка API не доступен: {e}")
except Exception as e:
    print(f"⚠️ Ошибка при загрузке модуля Т-банка API: {e}")

class TradingSystemGUI:
    """Графический интерфейс торговой системы"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Торговая система Сейкоты - Управление капиталом по Келли")
        self.root.geometry("1400x900")
        self.root.configure(bg='#f0f0f0')
        
        # Инициализация системы
        self.system = SeikotaTradingSystem(initial_capital=100000)
        self.visualizer = ResultsVisualizer()
        
        # Переменные интерфейса
        self.data_file = tk.StringVar()
        self.initial_capital = tk.DoubleVar(value=100000)
        self.initial_f = tk.DoubleVar(value=0.1)
        self.risk_per_trade = tk.DoubleVar(value=0.01)
        self.use_multi_timeframe = tk.BooleanVar(value=True)
        self.use_dynamic_risk = tk.BooleanVar(value=True)
        self.use_realistic = tk.BooleanVar(value=False)
        self.selected_result = tk.StringVar()
        
        # 🆕 ДЛЯ API ДАННЫХ
        self.current_api_data = None
        
        # 🆕 НОВАЯ ПЕРЕМЕННАЯ: Включение/отключение риск-менеджмента
        self.risk_management_enabled = tk.BooleanVar(value=True)
        
        # Новые переменные для стратегий
        self.strategy_type = tk.StringVar(value='multi_timeframe')
        self.supertrend_atr_period = tk.IntVar(value=10)
        self.supertrend_multiplier = tk.DoubleVar(value=3.0)
        
        # 🆕 ПЕРЕМЕННЫЕ ДЛЯ УПРАВЛЕНИЯ РИСКАМИ
        self.stop_loss_atr = tk.DoubleVar(value=2.0)
        self.take_profit_atr = tk.DoubleVar(value=3.0)
        self.trailing_stop_enabled = tk.BooleanVar(value=False)
        self.trailing_stop_atr = tk.DoubleVar(value=2.5)
        self.break_even_enabled = tk.BooleanVar(value=True)
        self.max_position_risk = tk.DoubleVar(value=0.02)
        self.time_stop_days = tk.IntVar(value=5)
        
        # Словарь для хранения вкладок
        self.tabs = {}
        
        # 🆕 Инициализация атрибутов для избежания ошибок Pylint
        self.performance_stats = {}
        self._cache_stats = {}
        self.active_orders = {}
        
        self.setup_gui()

    def initialize_tabs(self):
        """Инициализация всех вкладок"""
        # Создание вкладок
        self.tabs['price'] = PriceTab(self.notebook, self.visualizer)
        self.tabs['capital'] = CapitalTab(self.notebook, self.visualizer)
        self.tabs['position'] = PositionTab(self.notebook, self.visualizer)
        self.tabs['returns'] = ReturnsTab(self.notebook, self.visualizer)
        self.tabs['correlation'] = CorrelationTab(self.notebook, self.visualizer)
        self.tabs['trades'] = TradesTab(self.notebook, self.system)
        self.tabs['stats'] = StatsTab(self.notebook, self.visualizer)
        self.tabs['compare'] = CompareTab(self.notebook, self.visualizer)
        self.tabs['risk'] = RiskTab(self.notebook, self.visualizer)
        self.tabs['risk_analysis'] = RiskAnalysisTab(self.notebook, self.visualizer, self)
        
        # Добавление вкладок в notebook - БЕЗ ЭМОДЗИ
        self.notebook.add(self.tabs['price'].get_frame(), text="Цены и сигналы")
        self.notebook.add(self.tabs['capital'].get_frame(), text="Капитал")
        self.notebook.add(self.tabs['position'].get_frame(), text="Позиции")
        self.notebook.add(self.tabs['returns'].get_frame(), text="Доходности")
        self.notebook.add(self.tabs['correlation'].get_frame(), text="Корреляции")
        self.notebook.add(self.tabs['trades'].get_frame(), text="Сделки")
        self.notebook.add(self.tabs['stats'].get_frame(), text="Статистика")
        self.notebook.add(self.tabs['compare'].get_frame(), text="Сравнение")
        self.notebook.add(self.tabs['risk'].get_frame(), text="Риски")
        self.notebook.add(self.tabs['risk_analysis'].get_frame(), text="Анализ рисков")
        
        # ✅ ДОБАВЛЯЕМ ВКЛАДКУ ИНСТРУМЕНТОВ
        if INSTRUMENTS_AVAILABLE:
            try:
                # Используем токен из Tinkoff API
                TOKEN = "t.8HbNCn4L0U9uBmMa5oloBrXCKxnqsTYNVK3f9iJOwDBiQ2lva9kvQ3C-MLgEESHl65ma1q0k0P6aMfS_O_co4g"
                self.instruments_tab = InstrumentsTab(self.notebook, TOKEN)
                self.notebook.add(self.instruments_tab, text="📊 Инструменты")
                print("✅ Вкладка инструментов успешно добавлена")
            except Exception as e:
                print(f"❌ Ошибка добавления вкладки инструментов: {e}")

    def setup_gui(self):
        """Настройка графического интерфейса"""
        # Создаем основной фрейм
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настраиваем grid
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Заголовок
        title_label = ttk.Label(main_frame, 
                               text="🎯 Торговая система Сейкоты - Управление капиталом по Келли",
                               font=('Arial', 16, 'bold'),
                               foreground='#2c3e50')
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Левая панель - Управление
        left_frame = ttk.LabelFrame(main_frame, text="⚙️ Управление системой", padding="10")
        left_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), padx=(0, 10))
        
        # Правая панель - Результаты
        right_frame = ttk.LabelFrame(main_frame, text="📊 Результаты и аналитика", padding="10")
        right_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка весов для растягивания
        main_frame.rowconfigure(1, weight=1)
        left_frame.columnconfigure(1, weight=1)
        right_frame.columnconfigure(0, weight=1)
        right_frame.rowconfigure(1, weight=1)
        
        self.setup_left_panel(left_frame)
        self.setup_right_panel(right_frame)
        
    def setup_left_panel(self, parent):
        """Настройка левой панели управления"""
        parent.columnconfigure(1, weight=1)
        
        # Загрузка данных
        ttk.Label(parent, text="Файл с данными:").grid(row=0, column=0, sticky=tk.W, pady=2)
        file_browser = FileBrowser(parent, self.data_file)
        file_browser.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Параметры системы
        ttk.Label(parent, text="Начальный капитал ($):").grid(row=1, column=0, sticky=tk.W, pady=2)
        ttk.Entry(parent, textvariable=self.initial_capital).grid(row=1, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(parent, text="Начальное f:").grid(row=2, column=0, sticky=tk.W, pady=2)
        ttk.Entry(parent, textvariable=self.initial_f).grid(row=2, column=1, sticky=(tk.W, tk.E), pady=2)
        
        ttk.Label(parent, text="Риск на сделку (%):").grid(row=3, column=0, sticky=tk.W, pady=2)
        ttk.Entry(parent, textvariable=self.risk_per_trade).grid(row=3, column=1, sticky=(tk.W, tk.E), pady=2)
        
        # Настройки стратегии
        ttk.Checkbutton(parent, text="Мультифреймовая стратегия", 
                    variable=self.use_multi_timeframe).grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        ttk.Checkbutton(parent, text="Динамическое управление риском", 
                    variable=self.use_dynamic_risk).grid(row=5, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        ttk.Checkbutton(parent, text="Реалистичный режим (комиссии)", 
                    variable=self.use_realistic).grid(row=6, column=0, columnspan=2, sticky=tk.W, pady=2)
    
        # 🆕 НОВЫЙ ЧЕКБОКС: Включение риск-менеджмента
        ttk.Checkbutton(parent, text="🛡️ Включить риск-менеджмент", 
                        variable=self.risk_management_enabled).grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=2)

        # ВЫБОР СТРАТЕГИИ
        ttk.Label(parent, text="Стратегия:").grid(row=8, column=0, sticky=tk.W, pady=2)
        strategy_frame = ttk.Frame(parent)
        strategy_frame.grid(row=8, column=1, sticky=(tk.W, tk.E), pady=2)

        # Комбобокс выбора стратегии
        strategies = self.system.get_available_strategies()
        strategy_combo = ttk.Combobox(strategy_frame, textvariable=self.strategy_type, 
                                    values=list(strategies.keys()), state="readonly")
        strategy_combo.pack(side=tk.LEFT, fill=tk.X, expand=True)
        strategy_combo.bind('<<ComboboxSelected>>', self.on_strategy_changed)

        # Параметры Super Trend
        self.supertrend_frame = ttk.LabelFrame(parent, text="Параметры Super Trend")
        self.supertrend_frame.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)

        ttk.Label(self.supertrend_frame, text="ATR период:").grid(row=0, column=0, sticky=tk.W, padx=5)
        ttk.Entry(self.supertrend_frame, textvariable=self.supertrend_atr_period, width=8).grid(row=0, column=1, padx=5)

        ttk.Label(self.supertrend_frame, text="Множитель:").grid(row=0, column=2, sticky=tk.W, padx=5)
        ttk.Entry(self.supertrend_frame, textvariable=self.supertrend_multiplier, width=8).grid(row=0, column=3, padx=5)
        
        # 🛡️ ПАРАМЕТРЫ УПРАВЛЕНИЯ РИСКАМИ
        risk_frame = ttk.LabelFrame(parent, text="🛡️ Управление рисками", padding="5")
        risk_frame.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(risk_frame, text="Stop Loss (ATR):").grid(row=0, column=0, sticky=tk.W, padx=2)
        ttk.Entry(risk_frame, textvariable=self.stop_loss_atr, width=6).grid(row=0, column=1, padx=2)
        
        ttk.Label(risk_frame, text="Take Profit (ATR):").grid(row=0, column=2, sticky=tk.W, padx=2)
        ttk.Entry(risk_frame, textvariable=self.take_profit_atr, width=6).grid(row=0, column=3, padx=2)
        
        ttk.Checkbutton(risk_frame, text="Trailing Stop", 
                    variable=self.trailing_stop_enabled).grid(row=1, column=0, columnspan=2, sticky=tk.W, padx=2)
        
        ttk.Label(risk_frame, text="Trailing (ATR):").grid(row=1, column=2, sticky=tk.W, padx=2)
        ttk.Entry(risk_frame, textvariable=self.trailing_stop_atr, width=6).grid(row=1, column=3, padx=2)
        
        ttk.Checkbutton(risk_frame, text="Break Even Stop", 
                    variable=self.break_even_enabled).grid(row=2, column=0, columnspan=2, sticky=tk.W, padx=2)
        
        ttk.Label(risk_frame, text="Max Position Risk (%):").grid(row=2, column=2, sticky=tk.W, padx=2)
        ttk.Entry(risk_frame, textvariable=self.max_position_risk, width=6).grid(row=2, column=3, padx=2)
        
        ttk.Label(risk_frame, text="Time Stop (days):").grid(row=3, column=0, sticky=tk.W, padx=2)
        ttk.Entry(risk_frame, textvariable=self.time_stop_days, width=6).grid(row=3, column=1, padx=2)

        # Изначально скрываем параметры Super Trend
        self.supertrend_frame.grid_remove()
        
        # Кнопки управления
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=11, column=0, columnspan=2, pady=20)
        
        StyledButton(button_frame, text="🚀 Запустить тест", 
                    command=self.run_test).pack(fill=tk.X, pady=2)
        
        StyledButton(button_frame, text="📈 Обновить графики", 
                    command=self.update_all_tabs).pack(fill=tk.X, pady=2)
        
        StyledButton(button_frame, text="💾 Экспорт результатов", 
                    command=self.export_results).pack(fill=tk.X, pady=2)
        
        StyledButton(button_frame, text="❓ Справка", 
                    command=self.show_help).pack(fill=tk.X, pady=2)
        
        # Информация о системе
        info_frame = ttk.LabelFrame(parent, text="ℹ️ Информация о системе", padding="10")
        info_frame.grid(row=12, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=10)
        
        info_text = """Система реализует принципы Эда Сейкоты:
        • Управление капиталом по формуле Келли
        • Динамическая корректировка риска
        • Мультифреймовые торговые сигналы
        • Super Trend стратегия
        • Реалистичное моделирование издержек"""
        
        ttk.Label(info_frame, text=info_text, justify=tk.LEFT, 
                 font=('Arial', 9)).pack(anchor=tk.W)
    
    def setup_right_panel(self, parent):
        """Настройка правой панели результатов"""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        
        # Выбор результата для отображения
        result_frame = ttk.Frame(parent)
        result_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        result_frame.columnconfigure(0, weight=1)
        
        self.results_combo = ResultsComboBox(result_frame, self.selected_result,
                                        on_select=self.on_result_selected)
        self.results_combo.pack(fill=tk.X)
        
        # Вкладки для разных типов аналитики
        self.notebook = ttk.Notebook(parent)
        self.notebook.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Инициализация всех вкладок
        self.initialize_tabs()
        
        # 🔧 ДОБАВЛЕНИЕ ВКЛАДКИ API ПОСЛЕ ОСНОВНЫХ ВКЛАДОК
        if TBANK_AVAILABLE:
            try:
                self.tabs['tbank_api'] = TBankApiTab(self.notebook, self)
                self.notebook.add(self.tabs['tbank_api'].get_frame(), text="📡 Т-банк API")
                print("✅ Вкладка Т-банка API успешно добавлена")
            except Exception as e:
                print(f"❌ Ошибка создания вкладки Т-банка API: {e}")
        
    def update_all_tabs(self):
        """Обновление всех вкладок"""
        if not self.selected_result.get():
            return
            
        current_result = self.selected_result.get()
        
        # Обновление графических вкладок
        self.tabs['price'].update_plot(current_result)
        self.tabs['capital'].update_plot(current_result)
        self.tabs['position'].update_plot(current_result)
        self.tabs['returns'].update_plot(current_result)
        self.tabs['correlation'].update_plot(current_result)
        self.tabs['trades'].update_trades(current_result)
        self.tabs['stats'].update_stats(current_result)
        self.tabs['risk'].update_plot(current_result)
        
    def on_strategy_changed(self, event=None):
        """Обработчик смены стратегии"""
        if self.strategy_type.get() == 'supertrend':
            self.supertrend_frame.grid()
        else:
            self.supertrend_frame.grid_remove()
                    
    def browse_file(self):
        """Выбор файла с данными"""
        filename = filedialog.askopenfilename(
            title="Выберите файл с данными",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.data_file.set(filename)
            
    @with_error_handling
    def run_test(self):
        """Запуск тестирования с поддержкой данных из API"""
        
        # === 1. ПРЕДВАРИТЕЛЬНАЯ ВАЛИДАЦИЯ ===
        
        # Проверка наличия файла с данными ИЛИ данных из API
        has_file_data = bool(self.data_file.get() and self.data_file.get() != "tbank_api_loaded_data")
        has_api_data = hasattr(self, 'current_api_data') and self.current_api_data is not None
        
        if not has_file_data and not has_api_data:
            messagebox.showerror("Ошибка", "❌ Выберите файл с данными или загрузите данные из API")
            return
        
        # Проверка параметров системы
        if not self._validate_system_parameters():
            return
        
        # 🆕 ПРИМЕНЕНИЕ ПАРАМЕТРОВ РИСКА ПЕРЕД ТЕСТИРОВАНИЕМ
        self.apply_risk_parameters()
        
        try:
            # === 2. ЗАГРУЗКА И ВАЛИДАЦИЯ ДАННЫХ ===
            data = None
            data_source = ""
            
            # Если есть данные из API, используем их
            if has_api_data:
                data = self.current_api_data.copy()
                data_source = "API Т-банка"
                print("✅ Используются данные из API Т-банка")
            else:
                # Иначе загружаем из файла
                data = load_price_data_from_file(self.data_file.get())
                data_source = f"файла {self.data_file.get()}"
            
            # Расширенная валидация данных
            from utils.data_loader import validate_price_data
            validation = validate_price_data(data)
            
            if not validation['is_valid']:
                error_msg = "❌ Данные не прошли валидацию:\n" + "\n".join(validation['errors'])
                messagebox.showerror("Ошибка данных", error_msg)
                return
            
            # Вывод предупреждений валидации
            if validation['warnings']:
                warning_msg = "⚠️ Предупреждения валидации:\n" + "\n".join(validation['warnings'])
                messagebox.showwarning("Предупреждение", warning_msg)
            
            # Проверка достаточности данных
            if len(data) < 50:
                response = messagebox.askyesno(
                    "Мало данных", 
                    f"Для тестирования доступно только {len(data)} записей.\n"
                    f"Рекомендуется минимум 100-200 записей.\n\n"
                    f"Продолжить тестирование?"
                )
                if not response:
                    return
            
            # === 3. ПОДГОТОВКА СИСТЕМЫ ===
            
            # Обновление параметров системы
            self.system.initial_capital = self.initial_capital.get()
            self.system.current_capital = self.initial_capital.get()
            
            # 🆕 ОЧИСТКА ПРЕДЫДУЩИХ РЕЗУЛЬТАТОВ
            if hasattr(self.system, 'clear_caches'):
                self.system.clear_caches()
            else:
                # Альтернативная очистка если метод еще не добавлен
                self.system.trade_history = []
            
            # === 4. СОБИРАЕМ ПАРАМЕТРЫ ТЕСТА ===
            test_params = self._collect_test_parameters()
            
            # === 5. ЗАПУСК СИМУЛЯЦИИ ===
            
            # Замер времени выполнения
            import time
            start_time = time.time()
            
            # Запуск симуляции с обработкой ошибок через декоратор
            result = self.system.simulate_trading(data, **test_params)
            
            execution_time = time.time() - start_time
            
            # === 6. ВАЛИДАЦИЯ РЕЗУЛЬТАТОВ ===
            if not self._validate_simulation_results(result):
                messagebox.showerror("Ошибка", "❌ Симуляция не вернула корректные результаты")
                return
            
            # === 7. АНАЛИЗ ПРОИЗВОДИТЕЛЬНОСТИ ===
            try:
                performance = analyze_performance(result, self.system.initial_capital)
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при анализе производительности: {str(e)}")
                return
            
            # === 8. СОХРАНЕНИЕ И ОТОБРАЖЕНИЕ РЕЗУЛЬТАТОВ ===
            
            # Генерация имени для результата с указанием источника данных
            result_name = self._generate_result_name(data_source)
            
            # Добавление результатов в визуализатор
            self.visualizer.add_simulation_result(result_name, result, performance)
            
            # === 9. ОБНОВЛЕНИЕ ИНТЕРФЕЙСА ===
            self.update_results_combo()
            self.update_all_tabs()
            
            # === 10. ФИНАЛЬНЫЙ ОТЧЕТ ===
            self._show_success_report(result, performance, execution_time, data_source)
            
        except FileNotFoundError:
            messagebox.showerror("Ошибка", f"❌ Файл не найден: {self.data_file.get()}")
        except pd.errors.EmptyDataError:
            messagebox.showerror("Ошибка", "❌ Файл с данными пуст или имеет неправильный формат")
        except Exception as e:
            # Общая обработка ошибок
            error_msg = f"❌ Неожиданная ошибка при тестировании:\n{str(e)}"
            messagebox.showerror("Ошибка", error_msg)
            
            # Дополнительная информация для отладки
            import traceback
            traceback.print_exc()

    def _validate_system_parameters(self) -> bool:
        """Валидация параметров системы перед тестированием"""
        checks = []
        
        # Проверка начального капитала
        if self.initial_capital.get() <= 0:
            checks.append("Начальный капитал должен быть положительным")
        
        # Проверка параметра Келли
        if not (0 < self.initial_f.get() <= 0.5):
            checks.append("Параметр Келли должен быть в диапазоне (0, 0.5]")
        
        # Проверка риска на сделку
        if not (0.001 <= self.risk_per_trade.get() <= 0.1):
            checks.append("Риск на сделку должен быть в диапазоне [0.1%, 10%]")
        
        if checks:
            error_msg = "❌ Ошибки в параметрах системы:\n" + "\n".join(f"• {check}" for check in checks)
            messagebox.showerror("Ошибка параметров", error_msg)
            return False
        
        return True

    def _collect_test_parameters(self) -> dict:
        """Сбор всех параметров для тестирования"""
        return {
            'initial_f': self.initial_f.get(),
            'risk_per_trade': self.risk_per_trade.get(),
            'use_multi_timeframe': self.use_multi_timeframe.get(),
            'use_dynamic_risk': self.use_dynamic_risk.get(),
            'realistic_mode': self.use_realistic.get(),
            'strategy_type': self.strategy_type.get(),
            'supertrend_atr_period': self.supertrend_atr_period.get(),
            'supertrend_multiplier': self.supertrend_multiplier.get()
        }

    def _validate_simulation_results(self, result: pd.DataFrame) -> bool:
        """Валидация результатов симуляции"""
        if result.empty:
            return False
        
        if 'capital' not in result.columns:
            return False
        
        if len(result) < 10:
            return False
        
        # Проверка на наличие ошибки в атрибутах DataFrame
        if hasattr(result, 'attrs') and 'error' in result.attrs:
            return False
        
        # Проверка корректности значений капитала
        capital_values = result['capital']
        if (capital_values <= 0).any():
            return False
        
        if capital_values.isna().any():
            return False
        
        return True

    def _generate_result_name(self, data_source: str = "") -> str:
        """Генерация имени для результата теста с указанием источника данных"""
        from datetime import datetime
        
        strategy_map = {
            'multi_timeframe': 'MA',
            'supertrend': 'ST'
        }
        
        strategy = strategy_map.get(self.strategy_type.get(), 'UNK')
        mode = "REAL" if self.use_realistic.get() else "BASIC"
        timeframe = "MULTI" if self.use_multi_timeframe.get() else "SINGLE"
        risk_mode = "DYN" if self.use_dynamic_risk.get() else "STAT"
        risk_mgmt = "RISK_ON" if self.risk_management_enabled.get() else "RISK_OFF"
        
        timestamp = datetime.now().strftime('%m%d_%H%M')
        
        # Добавляем информацию об источнике данных
        source_prefix = ""
        if "API" in data_source:
            source_prefix = "API_"
        elif "файла" in data_source:
            source_prefix = "FILE_"
        
        return f"{source_prefix}{strategy}_{mode}_{timeframe}_{risk_mode}_{risk_mgmt}_{timestamp}"

    def _show_success_report(self, result: pd.DataFrame, performance: dict, execution_time: float, data_source: str):
        """Показать отчет об успешном завершении тестирования"""
        final_capital = result['capital'].iloc[-1]
        total_return = (final_capital - self.system.initial_capital) / self.system.initial_capital * 100
        trades_count = len(self.system.trade_history)
        
        # Статистика кэша
        cache_stats = self.system.get_cache_stats() if hasattr(self.system, 'get_cache_stats') else {'overall_hit_ratio': 0}
        cache_efficiency = cache_stats.get('overall_hit_ratio', 0)
        
        # 🆕 ИНФОРМАЦИЯ О РИСК-МЕНЕДЖМЕНТЕ
        risk_status = "активна" if self.risk_management_enabled.get() else "отключена"
        risk_trades_info = ""
        if self.risk_management_enabled.get() and 'risk_system_enabled' in performance:
            risk_trades = performance.get('total_trades_with_risk', 0)
            risk_trades_info = f"\n• Сделок с рисками: {risk_trades}"
        
        # Сообщение об успехе
        success_msg = (
            f"✅ Тестирование завершено успешно!\n\n"
            f"📈 Основные результаты:\n"
            f"• Источник данных: {data_source}\n"
            f"• Сделок: {trades_count}\n"
            f"• Финальный капитал: ${final_capital:,.2f}\n"
            f"• Доходность: {total_return:+.2f}%\n"
            f"• Макс. просадка: {performance.get('max_drawdown', 0):.2f}%\n"
            f"• Риск-менеджмент: {risk_status}{risk_trades_info}\n\n"
            f"⚡ Производительность:\n"
            f"• Время выполнения: {execution_time:.2f} сек\n"
            f"• Эффективность кэша: {cache_efficiency:.1%}\n"
            f"• Обработано записей: {len(result)}\n\n"
            f"💡 Результат сохранен как: {self._generate_result_name(data_source)}"
        )
        
        messagebox.showinfo("Успех", success_msg)

    def update_results_combo(self):
        """Обновление списка доступных результатов"""
        results = self.visualizer.get_available_results()
        self.results_combo.update_values(results)
        self.tabs['compare'].update_available_results()
            
    def on_result_selected(self, event=None):
        """Обработчик выбора результата"""
        self.update_all_tabs()
                
    def export_results(self):
        """Экспорт результатов"""
        if not self.selected_result.get():
            messagebox.showwarning("Предупреждение", "Нет результатов для экспорта")
            return
            
        filename = filedialog.asksaveasfilename(
            title="Экспорт результатов",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # Собираем все данные для экспорта
                content = []
                content.append("ЭКСПОРТ РЕЗУЛЬТАТОВ ТОРГОВОЙ СИСТЕМЫ СЕЙКОТЫ")
                content.append("=" * 50)
                content.append(f"Время экспорта: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                content.append(f"Результат: {self.selected_result.get()}")
                content.append("")
                
                # Добавляем статистику
                stats = self.visualizer.get_detailed_stats(self.selected_result.get())
                content.append(stats)
                
                # Записываем в файл
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(content))
                    
                messagebox.showinfo("Успех", f"Результаты экспортированы в {filename}")
                
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка при экспорте: {str(e)}")
                
    def show_help(self):
        """Показ справки"""
        help_text = """🎯 ТОРГОВАЯ СИСТЕМА СЕЙКОТЫ - СПРАВКА

        ОСНОВНЫЕ ВОЗМОЖНОСТИ:

        📊 Управление капиталом по Келли
        • Автоматический расчет оптимального размера позиции
        • Использование дробного f для снижения риска
        • Динамическая корректировка на основе исторических данных

        ⚡ СТРАТЕГИИ:
        • Мультифреймовая (MA) - скользящие средние на трех таймфреймах
        • Super Trend - индикатор тренда с цветным кодированием

        🛡️ Управление рисками
        • Динамическая корректировка риска при просадках
        • Ограничение максимального размера позиции
        • Защита от чрезмерного риска

        💸 Реалистичное моделирование
        • Учет транзакционных издержек (комиссии)
        • Моделирование проскальзывания
        • Более точная оценка реальной доходности

        ИНСТРУКЦИЯ ПО ИСПОЛЬЗОВАНИЮ:

        1. Загрузите данные в формата CSV
        2. Выберите стратегию и настройте параметры
        3. Запустите тестирование
        4. Анализируйте результаты на графиках
        5. Сравнивайте разные стратегии

        ФОРМАТ ДАННЫХ:
        • CSV файл с разделителем ;
        • Обязательные колонки: DATE, CLOSE
        • Дополнительные: HIGH, LOW, OPEN, VOL

        ПАРАМЕТРЫ СИСТЕМЫ:
        • Начальный капитал - стартовый депозит
        • Начальное f - базовый параметр Келли
        • Риск на сделку - максимальный риск в %"""
        
        help_window = tk.Toplevel(self.root)
        help_window.title("Справка по системе")
        help_window.geometry("600x700")
        help_window.configure(bg='white')
        
        text_widget = scrolledtext.ScrolledText(help_window, wrap=tk.WORD, 
                                              font=('Arial', 10),
                                              padx=10, pady=10)
        text_widget.pack(fill=tk.BOTH, expand=True)
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)

    @with_error_handling
    def apply_risk_parameters(self):
        """Применение параметров управления рисками к системе"""
        try:
            if self.risk_management_enabled.get():
                risk_params = {
                    'stop_loss_atr_multiplier': self.stop_loss_atr.get(),
                    'take_profit_atr_multiplier': self.take_profit_atr.get(),
                    'trailing_stop_enabled': self.trailing_stop_enabled.get(),
                    'trailing_stop_atr_multiplier': self.trailing_stop_atr.get(),
                    'break_even_stop': self.break_even_enabled.get(),
                    'max_position_risk': self.max_position_risk.get(),
                    'time_stop_days': self.time_stop_days.get(),
                    'risk_management_enabled': True
                }
                
                if hasattr(self.system, 'update_risk_parameters'):
                    self.system.update_risk_parameters(**risk_params)
            else:
                # Отключаем риск-менеджмент
                if hasattr(self.system, 'update_risk_parameters'):
                    self.system.update_risk_parameters(risk_management_enabled=False)
                
        except Exception as e:
            print(f"Ошибка применения параметров риска: {e}")
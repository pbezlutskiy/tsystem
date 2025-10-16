# tbank_api/tbank_gui.py
"""
GUI компоненты для работы с API
ИСПРАВЛЕННАЯ ВЕРСИЯ
"""

import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import datetime, timedelta
from typing import List
import logging
from .api_manager import ApiManager
from .tbank_config import TBankConfig
from gui.components import PlotFrame, StyledButton

logger = logging.getLogger(__name__)

class TBankApiTab:
    """ИСПРАВЛЕННАЯ вкладка для работы с API"""
    
    def __init__(self, parent, main_app=None):
        self.parent = parent
        self.main_app = main_app
        self.config = TBankConfig()
        self.api_manager = ApiManager()
        self.current_data = None
        self.available_instruments = pd.DataFrame()
        self._setup_complete = False
        
        self.setup_ui()
        self.load_config_to_ui()
        self.load_available_instruments()
        self._setup_complete = True
        
        self.log_info("Готов к работе. Московская Биржа доступна по умолчанию.")
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.frame = ttk.Frame(self.parent)
        self.frame.columnconfigure(1, weight=1)
        self.frame.rowconfigure(3, weight=1)
        
        # Заголовок
        title_label = ttk.Label(self.frame, 
                               text="📡 Биржевые данные - API котировок",
                               font=('Arial', 14, 'bold'),
                               foreground='#2c3e50')
        title_label.grid(row=0, column=0, columnspan=4, pady=(0, 10))
        
        # Панель управления
        control_frame = ttk.LabelFrame(self.frame, text="Управление подключением", padding="10")
        control_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        control_frame.columnconfigure(1, weight=1)
        
        # ВЫБОР API
        ttk.Label(control_frame, text="Источник данных:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.api_var = tk.StringVar(value="moex")
        api_combo = ttk.Combobox(control_frame, textvariable=self.api_var,
                               values=["moex", "tbank"], state="readonly", width=10)
        api_combo.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        api_combo.bind('<<ComboboxSelected>>', self.on_api_changed)
        
        # Настройки API Т-банка
        self.tbank_frame = ttk.Frame(control_frame)
        self.tbank_frame.grid(row=1, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=2)
        self.tbank_frame.columnconfigure(1, weight=1)
        
        ttk.Label(self.tbank_frame, text="API ключ Т-банк:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.api_key_var = tk.StringVar()
        self.api_entry = ttk.Entry(self.tbank_frame, textvariable=self.api_key_var, show="*", width=30)
        self.api_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=2, padx=5)
        
        key_button_frame = ttk.Frame(self.tbank_frame)
        key_button_frame.grid(row=0, column=2, padx=5)
        
        StyledButton(key_button_frame, text="💾 Сохранить", 
                    command=self.save_api_key, width=10).pack(side=tk.LEFT, padx=2)
        
        StyledButton(key_button_frame, text="👁️ Показать", 
                    command=self.toggle_api_key_visibility, width=10).pack(side=tk.LEFT, padx=2)
        
        # Статус API
        self.api_status_var = tk.StringVar(value="✅ Московская Биржа доступна")
        status_label = ttk.Label(control_frame, textvariable=self.api_status_var, 
                 foreground='green', font=('Arial', 9))
        status_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        self._status_label = status_label  # Сохраняем ссылку для обновления цвета
        
        # Тест подключения
        test_button = StyledButton(control_frame, text="🔗 Тест подключения", 
                                 command=self.test_connection, width=20)
        test_button.grid(row=2, column=2, padx=5)
        
        # Панель выбора инструментов
        instruments_frame = ttk.LabelFrame(self.frame, text="Выбор инструмента", padding="10")
        instruments_frame.grid(row=2, column=0, columnspan=4, sticky=(tk.W, tk.E), pady=5)
        instruments_frame.columnconfigure(1, weight=1)
        
        # Рынок
        ttk.Label(instruments_frame, text="Рынок:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.market_var = tk.StringVar(value="shares")
        market_combo = ttk.Combobox(instruments_frame, textvariable=self.market_var,
                                  values=["shares", "bonds", "etfs", "currencies", "futures", "all"], 
                                  state="readonly", width=10)
        market_combo.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        market_combo.bind('<<ComboboxSelected>>', self.on_market_changed)
        
        # Инструмент
        ttk.Label(instruments_frame, text="Инструмент:").grid(row=0, column=2, sticky=tk.W, pady=2)
        self.symbol_var = tk.StringVar(value="SBER")
        self.symbol_combo = ttk.Combobox(instruments_frame, textvariable=self.symbol_var,
                                       state="readonly", width=15)
        self.symbol_combo.grid(row=0, column=3, sticky=(tk.W, tk.E), pady=2, padx=5)
        
        # Обновить список инструментов
        refresh_btn = StyledButton(instruments_frame, text="🔄 Обновить список", 
                                 command=self.load_available_instruments, width=15)
        refresh_btn.grid(row=0, column=4, padx=5)
        
        # Панель параметров данных
        params_frame = ttk.LabelFrame(self.frame, text="Параметры данных", padding="10")
        params_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        params_frame.columnconfigure(1, weight=1)
        
        # Период данных
        ttk.Label(params_frame, text="Период (дней):").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.period_var = tk.StringVar(value="365")
        period_combo = ttk.Combobox(params_frame, textvariable=self.period_var,
                                  values=["30", "90", "180", "365", "730", "1825"],
                                  state="readonly", width=8)
        period_combo.grid(row=0, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Таймфрейм
        ttk.Label(params_frame, text="Таймфрейм:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.timeframe_var = tk.StringVar(value="D")
        timeframe_combo = ttk.Combobox(params_frame, textvariable=self.timeframe_var,
                                     values=["D", "H1", "H4", "W", "1m", "5m", "15m"],
                                     state="readonly", width=8)
        timeframe_combo.grid(row=1, column=1, sticky=tk.W, pady=2, padx=5)
        
        # Кнопки управления
        buttons_frame = ttk.Frame(self.frame)
        buttons_frame.grid(row=3, column=2, columnspan=2, sticky=(tk.W, tk.E), pady=5, padx=10)
        
        StyledButton(buttons_frame, text="📥 Загрузить данные", 
                    command=self.load_data, width=18).pack(side=tk.TOP, pady=2)
        
        StyledButton(buttons_frame, text="🔄 Обновить", 
                    command=self.refresh_data, width=18).pack(side=tk.TOP, pady=2)
        
        StyledButton(buttons_frame, text="🚀 Запустить тест", 
                    command=self.run_trading_test, width=18).pack(side=tk.TOP, pady=2)
        
        StyledButton(buttons_frame, text="💾 Экспорт данных", 
                    command=self.export_data, width=18).pack(side=tk.TOP, pady=2)
        
        # Информационная панель
        info_frame = ttk.LabelFrame(self.frame, text="Информация", padding="10")
        info_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5)
        info_frame.columnconfigure(0, weight=1)
        info_frame.rowconfigure(0, weight=1)
        
        self.info_text = tk.Text(info_frame, height=10, width=60, font=('Arial', 9))
        scrollbar = ttk.Scrollbar(info_frame, orient=tk.VERTICAL, command=self.info_text.yview)
        self.info_text.configure(yscrollcommand=scrollbar.set)
        self.info_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        
        # График данных
        plot_frame = ttk.LabelFrame(self.frame, text="График данных", padding="10")
        plot_frame.grid(row=4, column=2, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=5, padx=(10, 0))
        plot_frame.columnconfigure(0, weight=1)
        plot_frame.rowconfigure(0, weight=1)
        
        self.plot_widget = PlotFrame(plot_frame)
        self.plot_widget.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Настройка весов для растягивания
        self.frame.rowconfigure(4, weight=1)
        
        # Обновляем интерфейс в зависимости от выбранного API
        self.on_api_changed()
    
    def on_api_changed(self, event=None):
        """Обработчик изменения выбранного API"""
        if not self._setup_complete:
            return
            
        api_name = self.api_var.get()
        
        try:
            if api_name == 'tbank':
                self.tbank_frame.grid()  # Показываем настройки Т-банка
                if self.api_manager.is_tbank_available():
                    # Дополнительная проверка подключения
                    if self.api_manager.test_connection('tbank'):
                        self.api_status_var.set("✅ Т-банк API доступен")
                        self._update_status_color('green')
                    else:
                        self.api_status_var.set("⚠️ Т-банк API настроен, но недоступен")
                        self._update_status_color('orange')
                else:
                    self.api_status_var.set("❌ Т-банк API не настроен")
                    self._update_status_color('red')
            else:
                self.tbank_frame.grid_remove()  # Скрываем настройки Т-банка
                if self.api_manager.test_connection('moex'):
                    self.api_status_var.set("✅ Московская Биржа доступна")
                    self._update_status_color('green')
                else:
                    self.api_status_var.set("⚠️ Московская Биржа недоступна")
                    self._update_status_color('orange')
            
            # Устанавливаем активный API в менеджере
            if self.api_manager.set_api(api_name):
                # Обновляем список инструментов
                self.load_available_instruments()
            else:
                logger.warning(f"Не удалось установить API: {api_name}")
                
        except Exception as e:
            logger.error(f"Ошибка при смене API: {e}")
            self.api_status_var.set("❌ Ошибка при смене API")
            self._update_status_color('red')
    
    def on_market_changed(self, event=None):
        """Обработчик изменения рынка"""
        self.load_available_instruments()
    
    def load_available_instruments(self):
        """Загрузка списка доступных инструментов"""
        try:
            market = self.market_var.get()
            self.available_instruments = self.api_manager.get_available_symbols(market)
            
            if not self.available_instruments.empty:
                symbols = self.available_instruments['symbol'].tolist()
                self.symbol_combo['values'] = symbols
                
                if symbols and not self.symbol_var.get() in symbols:
                    self.symbol_var.set(symbols[0])
                
                self.log_info(f"✅ Загружено {len(symbols)} инструментов для рынка {market}")
            else:
                self.log_info("❌ Не удалось загрузить список инструментов")
                self.symbol_combo['values'] = []
                
        except Exception as e:
            self.log_info(f"❌ Ошибка загрузки инструментов: {str(e)}")
            self.symbol_combo['values'] = []
    
    def _update_status_color(self, color: str):
        """Обновление цвета статуса"""
        self._status_label.config(foreground=color)
    
    def load_config_to_ui(self):
        """Загрузка конфигурации в интерфейс"""
        api_key = self.config.get_api_key()
        if api_key:
            self.api_key_var.set(api_key)
    
    def save_api_key(self):
        """Сохранение API ключа Т-банка"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("Предупреждение", "Введите API ключ Т-банка")
            return
        
        try:
            self.config.set_api_key(api_key)
            # Пересоздаем менеджер с новым ключом
            self.api_manager.reload_tbank_api()
            self.log_info("✅ API ключ Т-банка сохранен")
            
            # Обновляем статус
            self.on_api_changed()
            
        except Exception as e:
            self.log_info(f"❌ Ошибка сохранения API ключа: {str(e)}")
            messagebox.showerror("Ошибка", f"Не удалось сохранить API ключ: {str(e)}")
    
    def test_connection(self):
        """Тестирование подключения к выбранному API"""
        api_name = self.api_var.get()
        
        if api_name == 'tbank' and not self.config.is_api_key_set():
            messagebox.showwarning("Предупреждение", "Сначала сохраните API ключ Т-банка")
            return
        
        try:
            if self.api_manager.test_connection(api_name):
                self.log_info(f"✅ Подключение к {api_name.upper()} API успешно")
                messagebox.showinfo("Успех", f"Подключение к {api_name.upper()} API успешно установлено")
                self._update_status_color('green')
            else:
                self.log_info(f"❌ Ошибка подключения к {api_name.upper()} API")
                messagebox.showerror("Ошибка", f"Не удалось подключиться к {api_name.upper()} API")
                self._update_status_color('red')
                
        except Exception as e:
            self.log_info(f"❌ Исключение при тесте подключения: {str(e)}")
            messagebox.showerror("Ошибка", f"Ошибка тестирования подключения: {str(e)}")
    
    def toggle_api_key_visibility(self):
        """Переключение видимости API ключа"""
        current_show = self.api_entry.cget('show')
        if current_show == '*':
            self.api_entry.config(show='')
        else:
            self.api_entry.config(show='*')
    
    def load_data(self):
        """Загрузка данных через выбранный API"""
        symbol = self.symbol_var.get().strip()
        if not symbol:
            messagebox.showwarning("Предупреждение", "Выберите инструмент")
            return
        
        try:
            days_back = int(self.period_var.get())
            timeframe = self.timeframe_var.get()
            
            api_name = self.api_var.get()
            self.log_info(f"Загрузка данных для {symbol} через {api_name.upper()} API...")
            self.log_info(f"Параметры: период={days_back} дней, таймфрейм={timeframe}")
            
            # Показываем индикатор загрузки
            self.parent.config(cursor='watch')
            self.frame.update()
            
            data = self.api_manager.load_price_data(
                symbol=symbol,
                days_back=days_back,
                timeframe=timeframe
            )
            
            # Возвращаем курсор
            self.parent.config(cursor='')
            
            if data.empty:
                self.log_info("❌ Не удалось загрузить данные")
                messagebox.showerror("Ошибка", f"Не удалось загрузить данные для {symbol}")
                return
            
            self.current_data = data
            self.update_info_panel(data)
            self.plot_data(data)
            self.log_info(f"✅ Загружено {len(data)} записей для {symbol}")
            
        except ValueError:
            self.log_info("❌ Ошибка: неверный формат параметров")
            messagebox.showerror("Ошибка", "Проверьте правильность введенных параметров")
        except Exception as e:
            self.log_info(f"❌ Ошибка загрузки: {str(e)}")
            messagebox.showerror("Ошибка", f"Ошибка загрузки данных: {str(e)}")
        finally:
            # Всегда возвращаем курсор
            self.parent.config(cursor='')
    
    def refresh_data(self):
        """Обновление данных"""
        if self.current_data is not None:
            # Очищаем кэш перед обновлением
            self.api_manager.clear_cache()
            self.load_data()
        else:
            messagebox.showinfo("Информация", "Сначала загрузите данные")
    
    def run_trading_test(self):
        """Запуск тестирования на загруженных данных"""
        if self.current_data is None or self.current_data.empty:
            messagebox.showwarning("Предупреждение", "Сначала загрузите данные")
            return
        
        if self.main_app is None:
            messagebox.showerror("Ошибка", "Не удалось подключиться к основной системе")
            return
        
        try:
            if self.set_data_to_main_app(self.current_data):
                self.main_app.run_test()
                self.log_info("✅ Тестирование запущено с данными из API")
            else:
                self.log_info("❌ Не удалось передать данные в основную систему")
                messagebox.showerror("Ошибка", "Не удалось передать данные в торговую систему")
                
        except Exception as e:
            self.log_info(f"❌ Ошибка запуска теста: {str(e)}")
            messagebox.showerror("Ошибка", f"Ошибка запуска тестирования: {str(e)}")
    
    def set_data_to_main_app(self, data: pd.DataFrame) -> bool:
        """Передача данных в главное приложение"""
        if self.main_app is not None:
            try:
                self.main_app.current_api_data = data
                self.main_app.data_file.set("api_loaded_data")
                return True
            except Exception as e:
                logger.error(f"Ошибка передачи данных в основное приложение: {e}")
                return False
        return False
    
    def export_data(self):
        """Экспорт данных в файл"""
        if self.current_data is None:
            messagebox.showwarning("Предупреждение", "Нет данных для экспорта")
            return
        
        try:
            api_name = self.api_var.get()
            symbol = self.symbol_var.get()
            timeframe = self.timeframe_var.get()
            filename = f"{api_name}_{symbol}_{timeframe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            # Экспортируем данные
            self.current_data.to_csv(filename, encoding='utf-8')
            
            self.log_info(f"✅ Данные экспортированы в {filename}")
            messagebox.showinfo("Успех", f"Данные экспортированы в {filename}")
            
        except Exception as e:
            self.log_info(f"❌ Ошибка экспорта: {str(e)}")
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {str(e)}")
    
    def update_info_panel(self, data: pd.DataFrame):
        """Обновление информационной панели"""
        if data.empty:
            return
            
        api_name = self.api_var.get()
        symbol = self.symbol_var.get()
        market = self.market_var.get()
        
        # Получаем информацию об инструменте
        instrument_info = ""
        if not self.available_instruments.empty and symbol in self.available_instruments['symbol'].values:
            instrument_data = self.available_instruments[self.available_instruments['symbol'] == symbol].iloc[0]
            instrument_info = f"Название: {instrument_data.get('name', 'N/A')}\n"
            if 'lot_size' in instrument_data:
                instrument_info += f"Лот: {instrument_data['lot_size']}\n"
            if 'currency' in instrument_data:
                instrument_info += f"Валюта: {instrument_data['currency']}\n"
            if 'type' in instrument_data:
                instrument_info += f"Тип: {instrument_data['type']}\n"
        
        # Базовая статистика
        price_stats = ""
        if 'close' in data.columns:
            price_stats = f"""
СТАТИСТИКА ЦЕН:
Минимум: {data['close'].min():.2f}
Максимум: {data['close'].max():.2f}
Текущая: {data['close'].iloc[-1]:.2f}
Изменение: {((data['close'].iloc[-1] - data['close'].iloc[0]) / data['close'].iloc[0] * 100):+.2f}%
Волатильность: {data['close'].pct_change().std()*100:.2f}%"""
        
        info_text = f"""📊 ИНФОРМАЦИЯ О ДАННЫХ:

Источник: {api_name.upper()}
Рынок: {market}
Инструмент: {symbol}
{instrument_info}
Период: {self.period_var.get()} дней
Таймфрейм: {self.timeframe_var.get()}
Записей: {len(data):,}

ДИАПАЗОН ДАТ:
Начало: {data.index.min().strftime('%d.%m.%Y %H:%M')}
Конец: {data.index.max().strftime('%d.%m.%Y %H:%M')}
{price_stats}

ПОСЛЕДНИЕ ДАННЫЕ:
{data.tail(3).to_string()}
"""
        
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(1.0, info_text)
    
    def plot_data(self, data: pd.DataFrame):
        """Построение графика данных"""
        if data.empty:
            return
        
        try:
            fig, ax = plt.subplots(figsize=(12, 6))
            
            # Основной график цен
            ax.plot(data.index, data['close'], label='Цена закрытия', 
                    color='blue', linewidth=1.5)
            
            api_name = self.api_var.get()
            symbol = self.symbol_var.get()
            timeframe = self.timeframe_var.get()
            
            # Настройка графика
            ax.set_title(f'{symbol} - Цены ({api_name.upper()} API, {timeframe})', 
                        fontsize=12, fontweight='bold')
            ax.set_ylabel('Цена', fontsize=10)
            ax.grid(True, alpha=0.3)
            ax.legend()
            
            # Форматирование дат в зависимости от таймфрейма
            if timeframe in ['H1', 'H4', '1m', '5m', '15m']:
                fig.autofmt_xdate()
                ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d.%m %H:%M'))
            else:
                fig.autofmt_xdate()
                ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%d.%m.%Y'))
            
            self.plot_widget.show_plot(fig)
            
        except Exception as e:
            self.log_info(f"❌ Ошибка построения графика: {str(e)}")
    
    def log_info(self, message: str):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_message = f"[{timestamp}] {message}\n"
        
        self.info_text.insert(tk.END, log_message)
        self.info_text.see(tk.END)
    
    def get_frame(self):
        """Возвращает фрейм вкладки"""
        return self.frame
    
    def cleanup(self):
        """Очистка ресурсов"""
        try:
            self.api_manager.clear_cache()
            if hasattr(self, 'plot_widget'):
                self.plot_widget.clear_plot()
        except Exception as e:
            logger.error(f"Ошибка при очистке ресурсов: {e}")
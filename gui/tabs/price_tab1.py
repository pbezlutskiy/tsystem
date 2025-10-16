# ===== СЕКЦИЯ 7: ВКЛАДКА ЦЕН И ТОРГОВЫХ СИГНАЛОВ =====
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np
import pandas as pd
from datetime import datetime
from gui.components import PlotFrame
from utils.supertrend import calculate_supertrend

class PriceTab:
    """Вкладка цен и торговых сигналов"""
    
    def __init__(self, parent, visualizer):
        self.parent = parent
        self.visualizer = visualizer
        self.current_fig = None
        self.last_result_name = None
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.frame = ttk.Frame(self.parent)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)  # Основное место для графика
        
        # Панель управления
        control_frame = ttk.Frame(self.frame)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Левая часть - управление масштабом
        left_frame = ttk.Frame(control_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        ttk.Button(left_frame, text="📊 Автомасштаб", 
                  command=self.auto_scale).pack(side=tk.LEFT, padx=2)
        ttk.Button(left_frame, text="💾 Сохранить", 
                  command=self.save_plot).pack(side=tk.LEFT, padx=2)
        
        # Правая часть - настройки отображения
        right_frame = ttk.Frame(control_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.X)
        
        # Настройки временной шкалы
        ttk.Label(right_frame, text="Временная шкала:").pack(side=tk.LEFT, padx=(10, 2))
        self.timeframe_var = tk.StringVar(value="auto")
        timeframe_combo = ttk.Combobox(right_frame, textvariable=self.timeframe_var, 
                                      values=["auto", "1D", "1W", "1M", "3M", "6M", "1Y"], 
                                      state="readonly", width=5)
        timeframe_combo.pack(side=tk.LEFT, padx=2)
        timeframe_combo.bind('<<ComboboxSelected>>', self.on_timeframe_change)
        
        # Настройки отображения сигналов
        self.show_supertrend = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_frame, text="SuperTrend", 
                       variable=self.show_supertrend,
                       command=self.refresh_current_plot).pack(side=tk.LEFT, padx=5)
        
        self.show_trade_signals = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_frame, text="Сигналы", 
                       variable=self.show_trade_signals,
                       command=self.refresh_current_plot).pack(side=tk.LEFT, padx=5)
        
        self.show_entries_exits = tk.BooleanVar(value=True)
        ttk.Checkbutton(right_frame, text="Входы/Выходы", 
                       variable=self.show_entries_exits,
                       command=self.refresh_current_plot).pack(side=tk.LEFT, padx=5)
        
        self.show_rsi = tk.BooleanVar(value=False)
        ttk.Checkbutton(right_frame, text="RSI", 
                       variable=self.show_rsi,
                       command=self.refresh_current_plot).pack(side=tk.LEFT, padx=5)
        
        # Панель информации о датах
        self.info_frame = ttk.Frame(self.frame)
        self.info_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=2)
        
        self.date_info_label = ttk.Label(self.info_frame, text="Период: - | Свечей: -")
        self.date_info_label.pack(side=tk.LEFT)
        
        self.zoom_info_label = ttk.Label(self.info_frame, text="Масштаб: Авто")
        self.zoom_info_label.pack(side=tk.RIGHT)
        
        # Основной фрейм с графиком
        self.plot_frame = PlotFrame(self.frame)
        self.plot_frame.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        self.frame.rowconfigure(1, weight=1)
        
        # Привязка событий мыши для информации о датах
        self.setup_mouse_events()
    
    def setup_mouse_events(self):
        """Настройка обработчиков событий мыши для графика"""
        pass
    
    def on_mouse_move(self, event):
        """Обработка движения мыши для показа даты"""
        if event.inaxes and self.current_fig and hasattr(self.plot_frame, 'fig_canvas'):
            try:
                # Преобразование координат в дату
                x_date = mdates.num2date(event.xdata).strftime('%d.%m.%Y %H:%M')
                y_value = f"{event.ydata:.2f}" if event.ydata else "-"
                
                # Обновление информации в реальном времени
                info_text = f"Дата: {x_date} | Цена: {y_value}"
                self.zoom_info_label.config(text=info_text)
                
            except (ValueError, TypeError):
                pass
    
    def on_zoom(self, event):
        """Обновление информации после масштабирования"""
        if self.current_fig and len(self.current_fig.axes) > 0 and hasattr(self.plot_frame, 'fig_canvas'):
            ax = self.current_fig.axes[0]
            xlim = ax.get_xlim()
            
            try:
                start_date = mdates.num2date(xlim[0]).strftime('%d.%m.%Y')
                end_date = mdates.num2date(xlim[1]).strftime('%d.%m.%Y')
                self.zoom_info_label.config(text=f"Масштаб: {start_date} - {end_date}")
            except (ValueError, TypeError):
                self.zoom_info_label.config(text="Масштаб: Авто")

    def on_timeframe_change(self, event=None):
        """Обработка изменения временной шкалы"""
        self.refresh_current_plot()
    
    def auto_scale(self):
        """Автоматическое масштабирование графика"""
        if self.last_result_name:
            self.update_plot(self.last_result_name)
            self.zoom_info_label.config(text="Масштаб: Авто")

    def save_plot(self):
        """Сохранить текущий график в файл"""
        if self.current_fig:
            try:
                filename = f"trading_chart_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                self.current_fig.savefig(filename, dpi=300, bbox_inches='tight')
                print(f"✅ График сохранен: {filename}")
            except Exception as e:
                print(f"❌ Ошибка сохранения: {e}")
    
    def refresh_current_plot(self):
        """Обновить текущий график с новыми настройками"""
        if self.last_result_name:
            self.update_plot(self.last_result_name)
    
    def detect_strategy_type(self, data):
        """Определить тип торговой стратегии по данным"""
        if 'supertrend_direction' in data.columns and 'supertrend_line' in data.columns:
            return "Super Trend"
        elif 'ma_fast' in data.columns and 'ma_slow' in data.columns:
            return "Мультифреймовая MA"
        elif 'rsi' in data.columns and 'rsi_oversold' in data.columns:
            return "RSI Strategy"
        else:
            return "Базовая"
    
    def setup_time_axis(self, ax, dates, timeframe="auto"):
        """Настройка временной шкалы"""
        # Проверяем, что dates - это datetime объекты
        is_datetime_index = (hasattr(dates, 'dtype') and 
                           (np.issubdtype(dates.dtype, np.datetime64) or 
                            hasattr(dates, 'dt'))) or (
                           len(dates) > 0 and hasattr(dates[0], 'year'))
        
        if timeframe == "auto" and is_datetime_index:
            try:
                # Автоматическое определение формата в зависимости от диапазона дат
                date_range = dates.max() - dates.min()
                if hasattr(date_range, 'days'):
                    days_range = date_range.days
                else:
                    # Если это не timedelta, используем длину массива как приближение
                    days_range = len(dates) / 24  # предполагаем часовые данные
                
                if days_range <= 7:
                    # Неделя или меньше - показывать дни и время
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m\n%H:%M'))
                    ax.xaxis.set_major_locator(mdates.DayLocator(interval=1))
                elif days_range <= 30:
                    # До месяца - показывать дни
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
                    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=1))
                elif days_range <= 90:
                    # До 3 месяцев - показывать недели
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m'))
                    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=0, interval=1))
                else:
                    # Более 3 месяцев - показывать месяцы
                    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
                    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=max(1, int(days_range // 90))))
            except Exception as e:
                print(f"⚠️ Ошибка в автоформатировании дат: {e}")
                # Используем базовое форматирование
                ax.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
        elif timeframe != "auto" and is_datetime_index:
            # Ручной выбор формата
            timeframe_formats = {
                "1D": ('%H:%M', mdates.HourLocator(interval=4)),
                "1W": ('%d.%m', mdates.DayLocator(interval=1)),
                "1M": ('%d.%m', mdates.WeekdayLocator(byweekday=0, interval=1)),
                "3M": ('%b %Y', mdates.MonthLocator(interval=1)),
                "6M": ('%b %Y', mdates.MonthLocator(interval=2)),
                "1Y": ('%b %Y', mdates.MonthLocator(interval=3))
            }
            
            if timeframe in timeframe_formats:
                try:
                    date_format, locator = timeframe_formats[timeframe]
                    ax.xaxis.set_major_formatter(mdates.DateFormatter(date_format))
                    ax.xaxis.set_major_locator(locator)
                except Exception as e:
                    print(f"⚠️ Ошибка в ручном форматировании дат: {e}")
        
        # Если это не datetime индекс, используем числовые метки
        if not is_datetime_index:
            ax.set_xlabel('Индекс данных')
            # Убираем форматирование дат для числового индекса
            ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'{int(x)}'))
        else:
            # Поворачиваем даты для лучшей читаемости
            plt.setp(ax.xaxis.get_majorticklabels(), rotation=45, ha='right')
        
        # Добавляем сетку
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', which='major', labelsize=8)
    
    def calculate_technical_indicators(self, data):
        """Расчет технических индикаторов для отображения"""
        indicators = {}
        
        # SuperTrend (только если включен)
        if (self.show_supertrend.get() and 
            'high' in data.columns and 'low' in data.columns):
            try:
                from utils.supertrend import calculate_supertrend
                indicators['supertrend'] = calculate_supertrend(data, atr_period=10, multiplier=3.0)
                print("✅ Super Trend рассчитан")
            except Exception as e:
                print(f"❌ Ошибка расчета Super Trend: {e}")
        
        # RSI (только если включен)
        if self.show_rsi.get() and 'close' in data.columns:
            try:
                indicators['rsi'] = self.calculate_rsi(data['close'])
                print("✅ RSI рассчитан")
            except Exception as e:
                print(f"❌ Ошибка расчета RSI: {e}")
        
        return indicators
    
    def calculate_rsi(self, prices, period=14):
        """Расчет RSI индикатора"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def plot_price_and_positions(self, ax, data, indicators, dates):
        """Построение графика цен и позиций"""
        strategy_name = self.detect_strategy_type(data)
        ax.set_title(f'Цены и торговые позиции ({strategy_name})', 
                    fontsize=12, fontweight='bold', pad=10)
        
        # Настройка временной шкалы
        self.setup_time_axis(ax, dates, self.timeframe_var.get())
        
        # 1. ФОНОВАЯ ПОДСВЕТКА ПОЗИЦИЙ
        if 'position_type' in data.columns and self.show_entries_exits.get():
            self._plot_position_background(ax, data, dates)
        
        # 2. ОСНОВНАЯ ЦЕНА ЗАКРЫТИЯ
        ax.plot(dates, data['close'], label='Цена закрытия', 
                color='black', linewidth=1.5, alpha=0.8, zorder=2)
        
        # 3. SUPER TREND ИНДИКАТОР (только если включен)
        if (self.show_supertrend.get() and 'supertrend' in indicators and 
            indicators['supertrend'] is not None):
            self._plot_supertrend(ax, indicators['supertrend'], dates)
        
        # 4. СКОЛЬЗЯЩИЕ СРЕДНИЕ
        self._plot_moving_averages(ax, data, dates, strategy_name)
        
        # 5. ТОРГОВЫЕ СИГНАЛЫ (точки входа/выхода) - только если включены
        if self.show_entries_exits.get():
            self._plot_trade_signals(ax, data, dates)
        
        # Настройка внешнего вида
        ax.set_ylabel('Цена ($)')
        ax.legend(fontsize=8, loc='upper left')
        ax.grid(True, alpha=0.3)
        
        # Включаем автоматическое масштабирование
        ax.autoscale(enable=True, axis='both', tight=True)

    def plot_trading_signals(self, ax, data, indicators, dates):
        """Построение графика торговых сигналов"""
        # УВЕЛИЧИВАЕМ ОТСТУПЫ ДЛЯ ЗАГОЛОВКА И ПОДПИСЕЙ
        ax.set_title('Торговые сигналы и индикаторы', fontsize=12, fontweight='bold', pad=20)
        
        # Настройка временной шкалы
        self.setup_time_axis(ax, dates, self.timeframe_var.get())
        
        # Основной торговый сигнал (только если включен)
        if self.show_trade_signals.get() and 'signal' in data.columns:
            ax.plot(dates, data['signal'], label='Торговый сигнал', 
                color='purple', linewidth=2)
        
        # Комбинированный сигнал (только если включен)
        if self.show_trade_signals.get() and 'combined_signal' in data.columns:
            ax.plot(dates, data['combined_signal'], label='Комбинированный сигнал', 
                color='orange', linewidth=1, alpha=0.7)
        
        # RSI индикатор (только если включен)
        if self.show_rsi.get():
            rsi_data = None
            if 'rsi' in data.columns:
                rsi_data = data['rsi']
            elif 'rsi' in indicators:
                rsi_data = indicators['rsi']
            
            if rsi_data is not None:
                ax_twin = ax.twinx()
                ax_twin.plot(dates, rsi_data, label='RSI', 
                        color='blue', linewidth=1, alpha=0.7)
                ax_twin.axhline(y=70, color='red', linestyle='--', alpha=0.5, label='Перекупленность')
                ax_twin.axhline(y=30, color='green', linestyle='--', alpha=0.5, label='Перепроданность')
                ax_twin.set_ylabel('RSI', color='blue', labelpad=15)
                ax_twin.set_ylim(0, 100)
                ax_twin.legend(loc='upper right', fontsize=7)
        
        # УВЕЛИЧИВАЕМ ОТСТУПЫ ДЛЯ ПОДПИСЕЙ ОСЕЙ
        ax.set_xlabel('Дата', labelpad=15)
        ax.set_ylabel('Сигнал', labelpad=15)
        
        if self.show_trade_signals.get():
            # РАЗМЕЩАЕМ ЛЕГЕНДУ ВНУТРИ ГРАФИКА, ЧТОБЫ НЕ ЗАНИМАЛА МЕСТО СВЕРХУ
            ax.legend(loc='upper left', fontsize=8, bbox_to_anchor=(0, 0.98))
        
        ax.grid(True, alpha=0.3)
        
        # ВАЖНО: УВЕЛИЧИВАЕМ ДИАПАЗОН ПО Y ДЛЯ ОТСТУПОВ
        ax.set_ylim(-0.25, 1.25)  # Значительно увеличиваем диапазон
        
        # ДОБАВЛЯЕМ ОТСТУПЫ ПО X
        if len(dates) > 1:
            if hasattr(dates, 'min') and hasattr(dates, 'max'):
                x_padding = (dates.max() - dates.min()) * 0.03  # 3% отступ по X
                ax.set_xlim(dates.min() - x_padding, dates.max() + x_padding)

    def update_plot(self, result_name: str):
        """Обновить график цен и сигналов"""
        self.last_result_name = result_name
        
        if result_name not in self.visualizer.results_history:
            self.plot_frame.show_placeholder("Результат не найден")
            return
        
        data = self.visualizer.results_history[result_name]['results']
        
        if data.empty:
            self.plot_frame.show_placeholder("Нет данных для отображения")
            return
        
        # Подготовка данных - правильное преобразование дат
        if hasattr(data.index, 'to_pydatetime'):
            dates = data.index
        else:
            try:
                dates = pd.to_datetime(data.index)
                if dates.min().year == 1970:
                    print("⚠️ Обнаружены даты 1970 года - используем числовой индекс")
                    dates = pd.RangeIndex(start=0, stop=len(data))
            except:
                dates = pd.RangeIndex(start=0, stop=len(data))
        
        # Обновление информации о периоде
        if hasattr(dates, 'min') and hasattr(dates, 'max'):
            if hasattr(dates.min(), 'strftime'):
                start_date = dates.min().strftime('%d.%m.%Y')
                end_date = dates.max().strftime('%d.%m.%Y')
                date_info = f"Период: {start_date} - {end_date}"
            else:
                date_info = f"Период: индексы {dates.min()} - {dates.max()}"
        else:
            date_info = "Период: неизвестно"
        
        total_candles = len(data)
        self.date_info_label.config(text=f"{date_info} | Свечей: {total_candles}")
        
        # Расчет индикаторов (учитываем настройки чекбоксов)
        indicators = self.calculate_technical_indicators(data)
        
        # СОЗДАЕМ БОЛЬШУЮ ФИГУРУ ДЛЯ ГРАФИКА СИГНАЛОВ
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12), 
                                    gridspec_kw={'height_ratios': [1.8, 1]})  # Больше места для сигналов
        
        # Очищаем оси перед построением
        ax1.clear()
        ax2.clear()
        
        # Построение графиков с учетом настроек чекбоксов
        self.plot_price_and_positions(ax1, data, indicators, dates)
        self.plot_trading_signals(ax2, data, indicators, dates)
        
        # НАСТРОЙКА ОТСТУПОВ ДЛЯ ГРАФИКА СИГНАЛОВ
        plt.subplots_adjust(
            left=0.07,    # Уменьшаем отступ слева
            right=0.95,   # Отступ справа  
            bottom=0.06,  # Уменьшаем отступ снизу
            top=0.95,     # Увеличиваем отступ сверху
            hspace=0.5    # Увеличиваем расстояние между графиками
        )
        
        self.current_fig = fig
        self.plot_frame.show_plot(fig)
        
        # Подключаем события мыши
        if hasattr(self.plot_frame, 'fig_canvas'):
            canvas = self.plot_frame.fig_canvas
            canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
            canvas.mpl_connect('button_release_event', self.on_zoom)
            canvas.draw()
        
        strategy_type = self.detect_strategy_type(data)
        print(f"✅ График обновлен: {strategy_type}, "
            f"SuperTrend: {self.show_supertrend.get()}, "
            f"Сигналы: {self.show_trade_signals.get()}, "
            f"Входы/Выходы: {self.show_entries_exits.get()}, "
            f"RSI: {self.show_rsi.get()}, "
            f"Временная шкала: {self.timeframe_var.get()}")
        
    def _plot_position_background(self, ax, data, dates):
        """Фоновая подсветка торговых позиций"""
        position_type = data['position_type'].values
        
        # Находим сегменты позиций
        position_changes = np.where(np.diff(position_type) != 0)[0] + 1
        segments = []
        
        if len(position_changes) > 0:
            segments.append((0, position_changes[0], position_type[0]))
            for i in range(len(position_changes) - 1):
                segments.append((position_changes[i], position_changes[i + 1], 
                               position_type[position_changes[i]]))
            segments.append((position_changes[-1], len(data), 
                           position_type[position_changes[-1]]))
        else:
            segments = [(0, len(data), position_type[0])]
        
        # Закрашиваем сегменты позиций
        for start_idx, end_idx, pos_type in segments:
            if pos_type == 1:  # LONG позиция
                if hasattr(dates, '__getitem__') and hasattr(dates[0], 'year'):
                    ax.axvspan(dates[start_idx], dates[end_idx - 1], 
                              alpha=0.15, color='green', label='LONG' if start_idx == 0 else "", 
                              zorder=1)
                else:
                    ax.axvspan(start_idx, end_idx - 1, 
                              alpha=0.15, color='green', label='LONG' if start_idx == 0 else "", 
                              zorder=1)
            elif pos_type == -1:  # SHORT позиция
                if hasattr(dates, '__getitem__') and hasattr(dates[0], 'year'):
                    ax.axvspan(dates[start_idx], dates[end_idx - 1], 
                              alpha=0.15, color='red', label='SHORT' if start_idx == 0 else "", 
                              zorder=1)
                else:
                    ax.axvspan(start_idx, end_idx - 1, 
                              alpha=0.15, color='red', label='SHORT' if start_idx == 0 else "", 
                              zorder=1)
    
    def _plot_supertrend(self, ax, supertrend_data, dates):
        """Отрисовка SuperTrend индикатора"""
        direction = supertrend_data['supertrend_direction'].values
        supertrend_line = supertrend_data['supertrend_line'].values
        
        # Находим точки смены направления
        change_points = np.where(np.diff(direction) != 0)[0] + 1
        
        # Разбиваем на сегменты
        segments = []
        if len(change_points) > 0:
            segments.append((0, change_points[0]))
            for i in range(len(change_points) - 1):
                segments.append((change_points[i], change_points[i + 1]))
            segments.append((change_points[-1], len(supertrend_data)))
        else:
            segments = [(0, len(supertrend_data))]
        
        # Отрисовка сегментов
        for start_idx, end_idx in segments:
            segment_direction = direction[start_idx]
            
            color = 'green' if segment_direction == 1 else 'red'
            label = 'SuperTrend' if start_idx == 0 else ""
            
            if hasattr(supertrend_data.index, '__getitem__') and hasattr(supertrend_data.index[0], 'year'):
                ax.plot(supertrend_data.index[start_idx:end_idx], supertrend_line[start_idx:end_idx],
                       color=color, linewidth=2, label=label, zorder=3)
            else:
                ax.plot(np.arange(start_idx, end_idx), supertrend_line[start_idx:end_idx],
                       color=color, linewidth=2, label=label, zorder=3)
    
    def _plot_moving_averages(self, ax, data, dates, strategy_name):
        """Отрисовка скользящих средних"""
        ma_columns = ['ma_fast', 'ma_slow', 'ma_trend']
        ma_colors = ['blue', 'red', 'orange']
        ma_labels = ['MA Быстрая', 'MA Медленная', 'MA Тренд']
        
        for i, ma_col in enumerate(ma_columns):
            if ma_col in data.columns:
                ax.plot(dates, data[ma_col], 
                       label=ma_labels[i], color=ma_colors[i],
                       alpha=0.7, linewidth=1, zorder=2)
    
    def _plot_trade_signals(self, ax, data, dates):
        """Отрисовка точек входа и выхода"""
        if 'entry_signal' in data.columns:
            entry_signals = data[data['entry_signal'] == 1]
            if not entry_signals.empty:
                if hasattr(dates, '__getitem__') and hasattr(dates[0], 'year'):
                    entry_dates = dates[data['entry_signal'] == 1]
                else:
                    entry_dates = np.where(data['entry_signal'] == 1)[0]
                ax.scatter(entry_dates, entry_signals['close'],
                          color='lime', marker='^', s=80, zorder=4,
                          label='Вход', edgecolors='black', linewidth=0.5)
        
        if 'exit_signal' in data.columns:
            exit_signals = data[data['exit_signal'] == 1]
            if not exit_signals.empty:
                if hasattr(dates, '__getitem__') and hasattr(dates[0], 'year'):
                    exit_dates = dates[data['exit_signal'] == 1]
                else:
                    exit_dates = np.where(data['exit_signal'] == 1)[0]
                ax.scatter(exit_dates, exit_signals['close'],
                          color='red', marker='v', s=80, zorder=4,
                          label='Выход', edgecolors='black', linewidth=0.5)

    def get_frame(self):  
        """Возвращает фрейм вкладки"""
        return self.frame
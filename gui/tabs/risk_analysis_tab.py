# ===== СЕКЦИЯ: ВКЛАДКА АНАЛИЗА РИСК-МЕНЕДЖМЕНТА =====
"""
Вкладка для детального анализа эффективности риск-менеджмента
Визуализация стоп-лоссов, тейк-профитов и статистики выходов
"""

import tkinter as tk
from tkinter import ttk
from tkinter import Menu
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from typing import Optional


class RiskAnalysisTab:
    """Вкладка для анализа эффективности риск-менеджмента"""
    
    def __init__(self, parent, visualizer, main_window=None):
        self.parent = parent
        self.visualizer = visualizer
        self.main_window = main_window  # 🆕 Сохраняем ссылку на главное окно
        self.current_figure = None
        
        self.frame = ttk.Frame(parent)
        self.setup_ui()
    
    def setup_ui(self):
        """Настройка интерфейса вкладки"""
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=1)
        
        # Панель управления
        control_frame = ttk.Frame(self.frame)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        control_frame.columnconfigure(1, weight=1)
        
        # 🆕 ДОБАВЛЯЕМ ВЫПАДАЮЩИЙ СПИСОК С РЕЗУЛЬТАТАМИ
        ttk.Label(control_frame, text="Результат:").grid(row=0, column=0, padx=5, sticky=tk.W)
        
        self.result_var = tk.StringVar()
        self.result_combo = ttk.Combobox(control_frame, textvariable=self.result_var, 
                                        state="readonly", width=30)
        self.result_combo.grid(row=0, column=1, padx=5, sticky=(tk.W, tk.E))
        self.result_combo.bind('<<ComboboxSelected>>', self._on_result_selected)
        
        # Кнопки управления
        button_frame = ttk.Frame(self.frame)
        button_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        button_frame.columnconfigure(1, weight=1)  # Даем пространство для индикатора

        # Основная кнопка обновления
        ttk.Button(button_frame, text="🔄 Обновить анализ",
                command=self.update_analysis).grid(row=0, column=0, padx=5, sticky=tk.W)

        # Выпадающее меню для дополнительных функций
        def show_analysis_menu():
            """Показать меню анализа"""
            try:
                menu = Menu(self.frame, tearoff=0, font=('Arial', 9))
                menu.add_command(label="📈 График ордеров", command=self.show_risk_plot)
                menu.add_command(label="📊 Статистика рисков", command=self.show_risk_stats)
                menu.add_command(label="⚖️ Сравнить стратегии", command=self.compare_risk_strategies)
                menu.add_separator()
                
                
                # Показываем меню под кнопкой
                x = self.analysis_btn.winfo_rootx()
                y = self.analysis_btn.winfo_rooty() + self.analysis_btn.winfo_height()
                menu.post(x, y)
            except Exception as e:
                print(f"❌ Ошибка показа меню: {e}")

        self.analysis_btn = ttk.Button(button_frame, text="📊 Анализ ▼",
                                    command=show_analysis_menu)
        self.analysis_btn.grid(row=0, column=1, padx=5, sticky=tk.W)

        # Индикатор загрузки
        self.status_label = ttk.Label(button_frame, text="Выберите результат для анализа", 
                                    foreground="gray")
        self.status_label.grid(row=0, column=2, padx=5, sticky=tk.E)
        
        # Область для отображения
        self.notebook = ttk.Notebook(self.frame)
        self.notebook.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))  # 🆕 Изменяем на row=2
        
        # Вкладка с текстовой статистикой
        self.stats_frame = ttk.Frame(self.notebook)
        self.stats_text = tk.Text(self.stats_frame, wrap=tk.WORD, font=('Consolas', 9), 
                                 height=25, width=80)
        scrollbar = ttk.Scrollbar(self.stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        self.stats_text.configure(yscrollcommand=scrollbar.set)
        
        self.stats_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.notebook.add(self.stats_frame, text="📋 Детальная статистика")
        
        # Вкладка с графиком риск-ордеров
        self.plot_frame = ttk.Frame(self.notebook)
        self.plot_frame.columnconfigure(0, weight=1)  # ✅ ДОБАВИТЬ
        self.plot_frame.rowconfigure(0, weight=1)     # ✅ ДОБАВИТЬ
        self.notebook.add(self.plot_frame, text="📈 Визуализация ордеров")
        
        # Вкладка с эффективностью выходов
        self.efficiency_frame = ttk.Frame(self.notebook)
        self.efficiency_text = tk.Text(self.efficiency_frame, wrap=tk.WORD, font=('Consolas', 9),
                                      height=25, width=80)
        efficiency_scrollbar = ttk.Scrollbar(self.efficiency_frame, orient=tk.VERTICAL, 
                                           command=self.efficiency_text.yview)
        self.efficiency_text.configure(yscrollcommand=efficiency_scrollbar.set)
        
        self.efficiency_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        efficiency_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.notebook.add(self.efficiency_frame, text="🎯 Эффективность выходов")
        
        # Заглушка при инициализации
        self.show_placeholder()
    
    def _on_result_selected(self, event=None):
        """Обработчик выбора результата"""
        self.update_analysis()

    def update_results_list(self):
        """Обновление списка доступных результатов"""
        try:
            if hasattr(self.visualizer, 'get_available_results'):
                results = self.visualizer.get_available_results()
                self.result_combo['values'] = results
                if results:
                    self.result_combo.set(results[-1])  # Выбираем последний результат
        except Exception as e:
            print(f"❌ Ошибка обновления списка результатов: {e}")

    def show_placeholder(self):
        """Показать заглушку при отсутствии данных"""
        placeholder_text = """
        🎯 АНАЛИЗ ЭФФЕКТИВНОСТИ РИСК-МЕНЕДЖМЕНТА
        ======================================
        
        Для отображения анализа:
        
        1. Загрузите данные и запустите тестирование
        2. Выберите результат в выпадающем списке
        3. Нажмите "Обновить анализ"
        
        📊 Что будет показано:
        • Эффективность стоп-лоссов и тейк-профитов
        • Визуализация ордеров на графике цен
        • Статистика по типам выходов из позиций
        • Рекомендации по оптимизации параметров рисков
        """
        
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, placeholder_text)
        self.stats_text.config(state=tk.DISABLED)
        
        self.efficiency_text.config(state=tk.NORMAL)
        self.efficiency_text.delete(1.0, tk.END)
        self.efficiency_text.insert(tk.END, placeholder_text)
        self.efficiency_text.config(state=tk.DISABLED)
    
    def update_analysis(self):
        """Обновление анализа рисков"""
        current_result = self._get_current_result()
        
        # 🆕 ДОБАВИМ ОТЛАДОЧНУЮ ИНФОРМАЦИЮ
        print(f"🔍 Отладка: current_result = '{current_result}'")
        print(f"🔍 Отладка: main_window = {self.main_window}")
        
        if not current_result:
            self._show_error("❌ Выберите результат для анализа")
            
            # 🆕 Покажем доступные результаты
            if hasattr(self.visualizer, 'get_available_results'):
                available = self.visualizer.get_available_results()
                print(f"🔍 Доступные результаты: {available}")
                
            return
        
        try:
            self.status_label.config(text="⏳ Анализируем риски...", foreground="blue")
            self.frame.update()
            
            # Обновляем все вкладки
            self._update_stats_tab(current_result)
            self._update_efficiency_tab(current_result)
            
            self.status_label.config(text="✅ Анализ завершен", foreground="green")
            
        except Exception as e:
            self._show_error(f"❌ Ошибка анализа: {str(e)}")
                

    def show_risk_plot(self):
        """Упрощенная версия без тулбара"""
        current_result = self._get_current_result()
        if not current_result:
            self._show_error("❌ Выберите результат для анализа")
            return
        
        try:
            self.status_label.config(text="⏳ Строим график...", foreground="blue")
            self.frame.update()
            
            # Переключаемся на вкладку с графиком
            self.notebook.select(1)
            
            # Очищаем предыдущий график
            for widget in self.plot_frame.winfo_children():
                widget.destroy()
            
            # Создаем новый график
            fig = self.visualizer.plot_risk_levels(current_result)
            if fig:
                canvas = FigureCanvasTkAgg(fig, self.plot_frame)
                canvas.draw()
                canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)  # ✅ pack ТОЛЬКО для canvas
                
                self.current_figure = fig
                self.status_label.config(text="✅ График построен", foreground="green")
            else:
                self._show_error("❌ Не удалось построить график")
            
        except Exception as e:
            self._show_error(f"❌ Ошибка построения графика: {str(e)}")
                            
    def show_risk_stats(self):
        """Показать статистику рисков"""
        current_result = self._get_current_result()
        if not current_result:
            self._show_error("❌ Выберите результат для анализа")
            return
        
        try:
            self.status_label.config(text="⏳ Загружаем статистику...", foreground="blue")
            self.frame.update()
            
            # Переключаемся на вкладку со статистикой
            self.notebook.select(0)
            
            # Получаем отчет об эффективности
            if hasattr(self.visualizer, 'get_risk_efficiency_report'):
                stats_report = self.visualizer.get_risk_efficiency_report(current_result)
            else:
                stats_report = self._generate_basic_efficiency_report(current_result)
            
            self.stats_text.config(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, stats_report)
            self.stats_text.config(state=tk.DISABLED)
            
            self.status_label.config(text="✅ Статистика загружена", foreground="green")
            
        except Exception as e:
            self._show_error(f"❌ Ошибка загрузки статистики: {str(e)}")
                
    def _update_stats_tab(self, result_name: str):
        """Обновление вкладки со статистикой"""
        try:
            # Получаем детальную статистику рисков
            stats = self.visualizer.get_detailed_risk_stats(result_name)
            
            self.stats_text.config(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, stats)
            self.stats_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.stats_text.config(state=tk.NORMAL)
            self.stats_text.delete(1.0, tk.END)
            self.stats_text.insert(tk.END, f"❌ Ошибка загрузки статистики: {str(e)}")
            self.stats_text.config(state=tk.DISABLED)
    
    def _update_efficiency_tab(self, result_name: str):
        """Обновление вкладки с эффективностью выходов"""
        try:
            if hasattr(self.visualizer, 'get_risk_efficiency_report'):
                efficiency_report = self.visualizer.get_risk_efficiency_report(result_name)
            else:
                efficiency_report = self._generate_basic_efficiency_report(result_name)
            
            self.efficiency_text.config(state=tk.NORMAL)
            self.efficiency_text.delete(1.0, tk.END)
            self.efficiency_text.insert(tk.END, efficiency_report)
            self.efficiency_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.efficiency_text.config(state=tk.NORMAL)
            self.efficiency_text.delete(1.0, tk.END)
            self.efficiency_text.insert(tk.END, f"❌ Ошибка анализа эффективности: {str(e)}")
            self.efficiency_text.config(state=tk.DISABLED)
                
    def _generate_basic_efficiency_report(self, result_name: str) -> str:
        """Генерация базового отчета об эффективности"""
        if result_name not in self.visualizer.results_history:
            return "Данные не найдены"
        
        data = self.visualizer.results_history[result_name]
        performance = data['performance']
        
        report = "🎯 ОТЧЕТ ЭФФЕКТИВНОСТИ ВЫХОДОВ\n"
        report += "=" * 40 + "\n\n"
        
        if performance.get('risk_system_enabled', False):
            report += "✅ СИСТЕМА РИСК-МЕНЕДЖМЕНТА АКТИВНА\n\n"
            
            # Статистика по типам выходов
            report += "📊 СТАТИСТИКА ВЫХОДОВ:\n"
            report += f"• Всего сделок с рисками: {performance.get('total_trades_with_risk', 0)}\n"
            report += f"• Стоп-лоссы: {performance.get('stop_loss_trades', 0)}\n"
            report += f"• Тейк-профиты: {performance.get('take_profit_trades', 0)}\n"
            report += f"• Risk-Reward Ratio: {performance.get('risk_reward_ratio', 0):.2f}\n"
            report += f"• Win Rate: {performance.get('win_rate_with_stops', 0):.1f}%\n\n"
            
            # Анализ PnL
            if 'pnl_by_reason' in performance:
                report += "💰 PnL ПО ТИПАМ ВЫХОДОВ:\n"
                pnl_data = performance['pnl_by_reason']
                for reason, stats in pnl_data.items():
                    if 'mean' in stats:
                        report += f"• {reason}: {stats['mean']:+.2f}% (n={stats.get('count', 0)})\n"
        else:
            report += "❌ СИСТЕМА РИСК-МЕНЕДЖМЕНТА НЕ АКТИВНА\n"
            report += "Сделки закрывались только по торговым сигналам\n"
        
        return report
    

    def _get_current_result(self) -> str:
        """Получить текущий выбранный результат"""
        try:
            # Способ 1: через переданное главное окно
            if self.main_window and hasattr(self.main_window, 'selected_result'):
                result = self.main_window.selected_result.get()
                if result:
                    return result
            
            # Способ 2: через parent chain
            current = self.parent
            for _ in range(5):  # Максимум 5 уровней вверх
                if hasattr(current, 'selected_result'):
                    return current.selected_result.get()
                if hasattr(current, 'master'):
                    current = current.master
                else:
                    break
            
            # Способ 3: через toplevel
            root = self.frame.winfo_toplevel()
            if hasattr(root, 'selected_result'):
                return root.selected_result.get()
                
            self._show_error("❌ Не удалось найти выбранный результат")
            return ""
            
        except Exception as e:
            self._show_error(f"❌ Ошибка получения результата: {str(e)}")
            return ""

    def _show_error(self, message: str):
        """Показать сообщение об ошибке"""
        self.status_label.config(text=message, foreground="red")
        
        self.stats_text.config(state=tk.NORMAL)
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, message)
        self.stats_text.config(state=tk.DISABLED)
    
    def clear_analysis(self):
        """Очистить анализ"""
        self.show_placeholder()
        self.status_label.config(text="Анализ очищен", foreground="gray")
        
        # Очищаем график
        if self.current_figure:
            plt.close(self.current_figure)
            self.current_figure = None
        
        for widget in self.plot_frame.winfo_children():
            widget.destroy()
    
    def get_frame(self):
        """Возвращает фрейм вкладки"""
        return self.frame

    def update_tab(self, result_name: str = None):
        """Обновить вкладку (вызывается из главного окна)"""
        if result_name:
            self.update_analysis()
        else:
            self.clear_analysis()

    def compare_risk_strategies(self):
        """Сравнение разных стратегий риск-менеджмента"""
        current_result = self._get_current_result()
        if not current_result:
            self._show_error("❌ Выберите результат для анализа")
            return
        
        try:
            self.status_label.config(text="⏳ Сравниваем стратегии...", foreground="blue")
            self.frame.update()
            
            # Переключаемся на вкладку эффективности
            self.notebook.select(2)
            
            comparison_report = self._generate_strategy_comparison(current_result)
            
            self.efficiency_text.config(state=tk.NORMAL)
            self.efficiency_text.delete(1.0, tk.END)
            self.efficiency_text.insert(tk.END, comparison_report)
            self.efficiency_text.config(state=tk.DISABLED)
            
            self.status_label.config(text="✅ Сравнение завершено", foreground="green")
            
        except Exception as e:
            self._show_error(f"❌ Ошибка сравнения стратегий: {str(e)}")

    def _generate_strategy_comparison(self) -> str:
        """Генерация отчета сравнения стратегий"""
        current_result = self._get_current_result()
        
        report = "⚖️ СРАВНЕНИЕ СТРАТЕГИЙ РИСК-МЕНЕДЖМЕНТА\n"
        report += "=" * 50 + "\n\n"
        
        # Добавляем информацию о текущих настройках
        if current_result:
            report += f"📋 ТЕКУЩИЕ НАСТРОЙКИ ({current_result}):\n"
            # Здесь можно добавить информацию о текущих параметрах
            report += "• Используются параметры из тестирования\n\n"
        
        report += "📊 РЕКОМЕНДУЕМЫЕ СТРАТЕГИИ:\n\n"
        
        report += "1. 🟢 КОНСЕРВАТИВНАЯ (ATR: 1.5/2.0)\n"
        report += "   • Стоп-лосс: 1.5 ATR\n"
        report += "   • Тейк-профит: 2.0 ATR\n"
        report += "   • Risk-Reward: 1.33\n"
        report += "   • Для: Низкая волатильность, начинающие трейдеры\n\n"
        
        report += "2. 🟡 УМЕРЕННАЯ (ATR: 2.0/3.0)\n" 
        report += "   • Стоп-лосс: 2.0 ATR\n"
        report += "   • Тейк-профит: 3.0 ATR\n"
        report += "   • Risk-Reward: 1.50\n"
        report += "   • Для: Стандартные условия, сбалансированный риск\n\n"
        
        report += "3. 🔴 АГРЕССИВНАЯ (ATR: 2.5/4.0)\n"
        report += "   • Стоп-лосс: 2.5 ATR\n"
        report += "   • Тейк-профит: 4.0 ATR\n"
        report += "   • Risk-Reward: 1.60\n"
        report += "   • Для: Высокая волатильность, опытные трейдеры\n\n"
        
        report += "💡 СОВЕТЫ:\n"
        report += "• Протестируйте разные параметры в основном интерфейсе\n"
        report += "• Сравните результаты в разделе 'Сравнение'\n"
        report += "• Используйте 'График ордеров' для визуальной оценки эффективности\n"
        
        return report
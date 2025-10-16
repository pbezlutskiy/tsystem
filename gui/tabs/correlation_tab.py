# ===== СЕКЦИЯ 11: ВКЛАДКА КОРРЕЛЯЦИОННОГО АНАЛИЗА =====
"""
Вкладка для анализа корреляций между различными параметрами системы
Матрица корреляций и heatmap
"""

import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from tkinter import messagebox, filedialog
import datetime
from scipy.cluster import hierarchy
from gui.components import PlotFrame

class CorrelationTab:
    """Вкладка корреляционного анализа"""
    
    def __init__(self, parent, visualizer):
        self.parent = parent
        self.visualizer = visualizer
        self.selected_variables = []
        self.analysis_history = []  # Для хранения истории анализов
        self.setup_ui()
    
    def setup_ui(self):
        """Расширенная настройка пользовательского интерфейса"""
        self.frame = ttk.Frame(self.parent)
        self.frame.columnconfigure(0, weight=1)
        self.frame.rowconfigure(2, weight=1)
        
        # Основная панель управления
        control_frame = ttk.Frame(self.frame)
        control_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=5)
        control_frame.columnconfigure(1, weight=1)
        
        # Выбор целевой переменной
        ttk.Label(control_frame, text="Анализировать корреляции с:").grid(row=0, column=0, padx=5, sticky=tk.W)
        self.target_var = tk.StringVar(value="capital")
        self.target_combo = ttk.Combobox(control_frame, textvariable=self.target_var, 
                                        width=20, state="readonly")
        self.target_combo.grid(row=0, column=1, padx=5, sticky=tk.W)
        
        # Кнопка обновления
        self.update_btn = ttk.Button(control_frame, text="Обновить график", 
                                    command=self._on_update_click)
        self.update_btn.grid(row=0, column=2, padx=10)
        
        # Кнопка помощи
        self.help_btn = ttk.Button(control_frame, text="Как использовать?", 
                                  command=self._show_help)
        self.help_btn.grid(row=0, column=3, padx=5)
        
        # Статистика корреляций
        self.stats_label = ttk.Label(control_frame, text="", foreground="blue")
        self.stats_label.grid(row=0, column=4, padx=10, sticky=tk.W)
        
        # Панель расширенных настроек
        settings_frame = ttk.LabelFrame(self.frame, text="Расширенные настройки", padding=5)
        settings_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # 1. Выбор переменных
        ttk.Button(settings_frame, text="Выбрать переменные", 
                  command=self._select_variables).grid(row=0, column=0, padx=5)
        
        # 2. Порог корреляции
        ttk.Label(settings_frame, text="Порог:").grid(row=0, column=1, padx=5)
        self.corr_threshold = tk.DoubleVar(value=0.7)
        ttk.Scale(settings_frame, from_=0.3, to=0.9, variable=self.corr_threshold,
                 orient=tk.HORIZONTAL, length=80).grid(row=0, column=2, padx=5)
        ttk.Label(settings_frame, textvariable=self.corr_threshold).grid(row=0, column=3, padx=5)
        
        # 3. Размер скользящего окна для временных корреляций
        ttk.Label(settings_frame, text="Окно:").grid(row=0, column=4, padx=5)
        self.window_size = tk.IntVar(value=50)
        ttk.Spinbox(settings_frame, from_=10, to=200, textvariable=self.window_size,
                   width=5).grid(row=0, column=5, padx=5)
        
        # Панель дополнительных функций
        advanced_frame = ttk.LabelFrame(self.frame, text="Дополнительные анализы", padding=5)
        advanced_frame.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=5)
        
        # Кнопки дополнительных анализов
        ttk.Button(advanced_frame, text="Временные корреляции", 
                  command=self._show_time_correlations).grid(row=0, column=0, padx=5)
        ttk.Button(advanced_frame, text="Кластеризация", 
                  command=self._show_clustering).grid(row=0, column=1, padx=5)
        ttk.Button(advanced_frame, text="Scatter Plot", 
                  command=self._show_scatter_dialog).grid(row=0, column=2, padx=5)
        ttk.Button(advanced_frame, text="Сравнить тесты", 
                  command=self._show_comparison).grid(row=0, column=3, padx=5)
        ttk.Button(advanced_frame, text="Экспорт", 
                  command=self._export_analysis).grid(row=0, column=4, padx=5)
        ttk.Button(advanced_frame, text="Граф корреляций", 
                  command=self._show_correlation_network).grid(row=0, column=5, padx=5)
        
        self.plot_frame = PlotFrame(self.frame)
        self.plot_frame.grid(row=3, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
    
    def _show_time_correlations(self):
        """Показать анализ временных корреляций"""
        if not hasattr(self, 'current_result_name'):
            messagebox.showwarning("Предупреждение", "Сначала загрузите данные")
            return
            
        data = self.visualizer.results_history[self.current_result_name]['results']
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        if self.selected_variables:
            numeric_cols = [col for col in numeric_cols if col in self.selected_variables]
        
        if len(numeric_cols) <= 1:
            messagebox.showwarning("Предупреждение", "Недостаточно переменных для анализа")
            return
        
        fig = self._create_time_correlation_analysis(data, numeric_cols)
        self._show_in_window(fig, "Временные корреляции")
    
    def _create_time_correlation_analysis(self, data, numeric_cols):
        """Создать анализ временных корреляций"""
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        target_var = self.target_var.get()
        window_size = self.window_size.get()
        
        # График 1: Скользящие корреляции с целевой переменной
        if target_var in numeric_cols:
            rolling_corrs = {}
            top_variables = self._get_top_correlated_variables(data[numeric_cols], target_var, 5)
            
            for col in top_variables:
                if col != target_var:
                    rolling_corrs[col] = data[target_var].rolling(window=window_size).corr(data[col])
            
            for col, corr_series in rolling_corrs.items():
                axes[0, 0].plot(corr_series.index, corr_series.values, 
                               label=self._shorten_label(col), alpha=0.7, linewidth=2)
            
            axes[0, 0].set_title(f'Скользящие корреляции с {self._shorten_label(target_var)}\n(окно={window_size})')
            axes[0, 0].set_ylabel('Корреляция')
            axes[0, 0].legend()
            axes[0, 0].grid(True, alpha=0.3)
            axes[0, 0].axhline(y=0, color='black', linestyle='-', alpha=0.5)
            axes[0, 0].axhline(y=0.7, color='red', linestyle='--', alpha=0.5, label='Сильная корр.')
            axes[0, 0].axhline(y=-0.7, color='red', linestyle='--', alpha=0.5)
        
        # График 2: Стабильность корреляций во времени
        correlation_stability = self._calculate_correlation_stability(data[numeric_cols], window_size)
        if correlation_stability:
            variables = [self._shorten_label(x[0]) for x in correlation_stability]
            stability_values = [x[1] for x in correlation_stability]
            
            bars = axes[0, 1].barh(range(len(correlation_stability)), stability_values,
                                  color='lightcoral', alpha=0.7)
            
            # Добавление значений на столбцы
            for i, (bar, value) in enumerate(zip(bars, stability_values)):
                axes[0, 1].text(value + 0.01, i, f'{value:.3f}', 
                               va='center', fontweight='bold')
            
            axes[0, 1].set_yticks(range(len(correlation_stability)))
            axes[0, 1].set_yticklabels(variables)
            axes[0, 1].set_title('Нестабильность корреляций\n(стандартное отклонение)')
            axes[0, 1].set_xlabel('Стандартное отклонение')
            axes[0, 1].grid(True, alpha=0.3, axis='x')
        
        # График 3: Heatmap изменяющихся корреляций
        if len(numeric_cols) > 1:
            # Вычисляем корреляции в разных временных отрезках
            segments = 4
            segment_size = len(data) // segments
            correlation_matrices = []
            
            for i in range(segments):
                start_idx = i * segment_size
                end_idx = start_idx + segment_size if i < segments - 1 else len(data)
                segment_data = data.iloc[start_idx:end_idx]
                corr_matrix = segment_data[numeric_cols].corr()
                correlation_matrices.append(corr_matrix)
            
            # Разница между первой и последней корреляционной матрицей
            if len(correlation_matrices) >= 2:
                corr_change = correlation_matrices[-1] - correlation_matrices[0]
                
                im = axes[1, 0].imshow(corr_change.values, cmap='coolwarm', aspect='auto',
                                      vmin=-1, vmax=1)
                
                axes[1, 0].set_xticks(range(len(numeric_cols)))
                axes[1, 0].set_yticks(range(len(numeric_cols)))
                axes[1, 0].set_xticklabels([self._shorten_label(col) for col in numeric_cols], 
                                         rotation=45, ha='right', fontsize=8)
                axes[1, 0].set_yticklabels([self._shorten_label(col) for col in numeric_cols], 
                                         fontsize=8)
                axes[1, 0].set_title('Изменение корреляций\n(конец - начало)')
                
                plt.colorbar(im, ax=axes[1, 0], shrink=0.8)
        
        # График 4: Самые изменчивые корреляционные пары
        volatile_pairs = self._find_volatile_correlation_pairs(data[numeric_cols], window_size)
        if volatile_pairs:
            pairs = [f"{self._shorten_label(p[0])}-{self._shorten_label(p[1])}" 
                    for p in volatile_pairs]
            volatilities = [p[2] for p in volatile_pairs]
            
            axes[1, 1].barh(range(len(volatile_pairs)), volatilities, color='orange', alpha=0.7)
            axes[1, 1].set_yticks(range(len(volatile_pairs)))
            axes[1, 1].set_yticklabels(pairs)
            axes[1, 1].set_title('Самые изменчивые корреляционные пары')
            axes[1, 1].set_xlabel('Изменчивость (std)')
            axes[1, 1].grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        return fig
    
    def _get_top_correlated_variables(self, data, target_var, n=5):
        """Получить топ-N наиболее коррелированных переменных"""
        if target_var not in data.columns:
            return []
        
        correlations = data.corr()[target_var].abs().sort_values(ascending=False)
        return correlations.index[1:n+1].tolist()  # Исключаем саму переменную
    
    def _calculate_correlation_stability(self, data, window_size):
        """Рассчитать стабильность корреляций во времени"""
        stabilities = []
        target_var = self.target_var.get()
        
        if target_var in data.columns:
            for col in data.columns:
                if col != target_var:
                    rolling_corr = data[target_var].rolling(window=window_size).corr(data[col])
                    stabilities.append((col, rolling_corr.std()))
        
        return sorted(stabilities, key=lambda x: x[1], reverse=True)[:8]
    
    def _find_volatile_correlation_pairs(self, data, window_size):
        """Найти самые изменчивые корреляционные пары"""
        volatile_pairs = []
        columns = data.columns.tolist()
        
        for i in range(len(columns)):
            for j in range(i+1, len(columns)):
                col1, col2 = columns[i], columns[j]
                rolling_corr = data[col1].rolling(window=window_size).corr(data[col2])
                volatility = rolling_corr.std()
                
                if not np.isnan(volatility):
                    volatile_pairs.append((col1, col2, volatility))
        
        return sorted(volatile_pairs, key=lambda x: x[2], reverse=True)[:6]
    
    def _show_clustering(self):
        """Показать кластеризацию переменных"""
        if not hasattr(self, 'current_result_name'):
            messagebox.showwarning("Предупреждение", "Сначала загрузите данные")
            return
            
        data = self.visualizer.results_history[self.current_result_name]['results']
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        if self.selected_variables:
            numeric_cols = [col for col in numeric_cols if col in self.selected_variables]
        
        if len(numeric_cols) <= 2:
            messagebox.showwarning("Предупреждение", "Недостаточно переменных для кластеризации")
            return
        
        fig = self._create_clustering_analysis(data[numeric_cols])
        self._show_in_window(fig, "Кластеризация переменных")
    
    def _create_clustering_analysis(self, data):
        """Создать анализ кластеризации"""
        correlation_matrix = data.corr()
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 8))
        
        # График 1: Дендрограмма
        try:
            # Преобразуем корреляции в расстояния
            distance_matrix = 1 - np.abs(correlation_matrix)
            np.fill_diagonal(distance_matrix.values, 0)
            
            linkage_matrix = hierarchy.linkage(distance_matrix, method='ward')
            dendro = hierarchy.dendrogram(linkage_matrix, 
                                        labels=[self._shorten_label(col) for col in correlation_matrix.columns],
                                        orientation='left',
                                        ax=axes[0])
            axes[0].set_title('Дендрограмма корреляций\n(иерархическая кластеризация)')
            axes[0].set_xlabel('Расстояние')
            
            # График 2: Кластеризованная heatmap
            reordered_indices = dendro['leaves']
            reordered_cols = [correlation_matrix.columns[i] for i in reordered_indices]
            reordered_corr = correlation_matrix.loc[reordered_cols, reordered_cols]
            
            sns.heatmap(reordered_corr, annot=True, cmap='coolwarm', center=0,
                       fmt='.2f', linewidths=0.5, ax=axes[1],
                       annot_kws={'size': 8, 'weight': 'bold'})
            
            axes[1].set_title('Кластеризованная матрица корреляций')
            axes[1].set_xticklabels([self._shorten_label(col) for col in reordered_cols], 
                                  rotation=45, ha='right', fontsize=9)
            axes[1].set_yticklabels([self._shorten_label(col) for col in reordered_cols], 
                                  fontsize=9)
            
        except Exception as e:
            axes[0].text(0.5, 0.5, f'Ошибка кластеризации:\n{str(e)}', 
                        ha='center', va='center', transform=axes[0].transAxes)
            axes[0].set_title('Дендрограмма (ошибка)')
            axes[1].text(0.5, 0.5, 'Невозможно построить\nкластеризованную матрицу', 
                        ha='center', va='center', transform=axes[1].transAxes)
            axes[1].set_title('Кластеризованная матрица (ошибка)')
        
        plt.tight_layout()
        return fig
    
    def _show_comparison(self):
        """Показать сравнение корреляций между разными тестами"""
        available_results = list(self.visualizer.results_history.keys())
        
        if len(available_results) < 2:
            messagebox.showwarning("Предупреждение", "Недостаточно тестов для сравнения")
            return
        
        # Диалог выбора тестов для сравнения
        compare_window = tk.Toplevel(self.frame)
        compare_window.title("Сравнение тестов")
        compare_window.geometry("300x200")
        
        ttk.Label(compare_window, text="Выберите тесты для сравнения:").pack(pady=10)
        
        test_vars = []
        checkboxes_frame = ttk.Frame(compare_window)
        checkboxes_frame.pack(pady=10)
        
        for i, result_name in enumerate(available_results):
            var = tk.BooleanVar(value=True if i < 3 else False)  # Выбираем первые 3 по умолчанию
            cb = ttk.Checkbutton(checkboxes_frame, text=result_name, variable=var)
            cb.grid(row=i//2, column=i%2, sticky=tk.W, padx=10, pady=2)
            test_vars.append((result_name, var))
        
        def run_comparison():
            selected_tests = [name for name, var in test_vars if var.get()]
            if len(selected_tests) < 2:
                messagebox.showwarning("Предупреждение", "Выберите хотя бы 2 теста")
                return
            
            compare_window.destroy()
            self._create_comparison_analysis(selected_tests)
        
        ttk.Button(compare_window, text="Сравнить", 
                  command=run_comparison).pack(pady=10)
    
    def _create_comparison_analysis(self, result_names):
        """Создать сравнительный анализ"""
        n_tests = len(result_names)
        fig, axes = plt.subplots(n_tests, 2, figsize=(16, 5 * n_tests))
        
        if n_tests == 1:
            axes = [axes]  # Чтобы унифицировать обработку
        
        for i, result_name in enumerate(result_names):
            if result_name in self.visualizer.results_history:
                data = self.visualizer.results_history[result_name]['results']
                numeric_cols = data.select_dtypes(include=[np.number]).columns
                
                if self.selected_variables:
                    numeric_cols = [col for col in numeric_cols if col in self.selected_variables]
                
                if len(numeric_cols) > 1:
                    corr_matrix = data[numeric_cols].corr()
                    
                    # Heatmap
                    sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
                               fmt='.2f', ax=axes[i][0] if n_tests > 1 else axes[0],
                               cbar_kws={'shrink': 0.8})
                    title_ax = axes[i][0] if n_tests > 1 else axes[0]
                    title_ax.set_title(f'Корреляции: {result_name}')
                    
                    # Топ корреляций с целевой переменной
                    target_var = self.target_var.get()
                    if target_var in numeric_cols:
                        target_corrs = corr_matrix[target_var].drop(target_var)
                        top_corrs = target_corrs.abs().sort_values(ascending=False).head(5)
                        
                        bars_ax = axes[i][1] if n_tests > 1 else axes[1]
                        colors = ['green' if target_corrs[col] > 0 else 'red' for col in top_corrs.index]
                        bars = bars_ax.barh(range(len(top_corrs)), target_corrs[top_corrs.index].values,
                                           color=colors, alpha=0.7)
                        
                        bars_ax.set_yticks(range(len(top_corrs)))
                        bars_ax.set_yticklabels([self._shorten_label(idx) for idx in top_corrs.index])
                        bars_ax.set_title(f'Топ-5 корреляций с {self._shorten_label(target_var)}')
                        bars_ax.set_xlabel('Корреляция')
                        bars_ax.grid(True, alpha=0.3, axis='x')
                        
                        # Добавление значений
                        for j, (bar, value) in enumerate(zip(bars, target_corrs[top_corrs.index].values)):
                            bars_ax.text(value + (0.01 if value >= 0 else -0.05), j, 
                                       f'{value:.3f}', va='center', fontweight='bold')
        
        plt.tight_layout()
        self._show_in_window(fig, f"Сравнение {len(result_names)} тестов")
    
    def _show_correlation_network(self):
        """Показать граф корреляций"""
        if not hasattr(self, 'current_result_name'):
            messagebox.showwarning("Предупреждение", "Сначала загрузите данные")
            return
            
        data = self.visualizer.results_history[self.current_result_name]['results']
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        if self.selected_variables:
            numeric_cols = [col for col in numeric_cols if col in self.selected_variables]
        
        if len(numeric_cols) <= 2:
            messagebox.showwarning("Предупреждение", "Недостаточно переменных для графа")
            return
        
        # Диалог выбора порога
        threshold_window = tk.Toplevel(self.frame)
        threshold_window.title("Настройки графа")
        threshold_window.geometry("250x120")
        
        ttk.Label(threshold_window, text="Порог корреляции:").pack(pady=5)
        network_threshold = tk.DoubleVar(value=0.5)
        ttk.Scale(threshold_window, from_=0.3, to=0.8, variable=network_threshold,
                 orient=tk.HORIZONTAL, length=150).pack(pady=5)
        ttk.Label(threshold_window, textvariable=network_threshold).pack()
        
        def create_network():
            threshold_window.destroy()
            fig = self._create_correlation_network(data[numeric_cols], network_threshold.get())
            self._show_in_window(fig, f"Граф корреляций (порог: {network_threshold.get():.2f})")
        
        ttk.Button(threshold_window, text="Создать граф", 
                  command=create_network).pack(pady=10)
    
    def _create_correlation_network(self, data, threshold=0.5):
        """Создать граф корреляций"""
        try:
            import networkx as nx
        except ImportError:
            fig, ax = plt.subplots(figsize=(10, 6))
            ax.text(0.5, 0.5, 'Для построения графа установите networkx:\npip install networkx', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
            ax.set_title('Граф корреляций (networkx не установлен)')
            return fig
        
        correlation_matrix = data.corr()
        G = nx.Graph()
        
        # Добавление узлов
        for col in correlation_matrix.columns:
            G.add_node(col, label=self._shorten_label(col))
        
        # Добавление ребер для сильных корреляций
        for i in range(len(correlation_matrix.columns)):
            for j in range(i+1, len(correlation_matrix.columns)):
                corr_val = correlation_matrix.iloc[i, j]
                if abs(corr_val) > threshold:
                    col1, col2 = correlation_matrix.columns[i], correlation_matrix.columns[j]
                    G.add_edge(col1, col2, weight=corr_val, 
                              color='green' if corr_val > 0 else 'red')
        
        fig, ax = plt.subplots(figsize=(12, 10))
        
        if len(G.edges()) > 0:
            pos = nx.spring_layout(G, k=1, iterations=50)
            
            # Рисование графа
            edges = G.edges(data=True)
            edge_weights = [abs(edge[2]['weight']) * 3 for edge in edges]
            edge_colors = [edge[2]['color'] for edge in edges]
            
            nx.draw_networkx_nodes(G, pos, node_color='lightblue', 
                                 node_size=800, alpha=0.8, ax=ax)
            nx.draw_networkx_edges(G, pos, width=edge_weights, 
                                 edge_color=edge_colors, alpha=0.6, ax=ax)
            nx.draw_networkx_labels(G, pos, 
                                  {node: self._shorten_label(node) for node in G.nodes()},
                                  font_size=9, ax=ax)
            
            # Легенда
            ax.text(0.05, 0.95, f'Узлов: {len(G.nodes())}\nРебер: {len(G.edges())}', 
                   transform=ax.transAxes, bbox=dict(boxstyle="round,pad=0.3", facecolor="white"))
        else:
            ax.text(0.5, 0.5, f'Нет корреляций выше порога {threshold}', 
                   ha='center', va='center', transform=ax.transAxes, fontsize=12)
        
        ax.set_title(f'Граф корреляций (порог: {threshold})')
        ax.axis('off')
        
        return fig

    # ... остальные методы из первого этапа остаются без изменений ...
    # _show_help, get_frame, _on_update_click, update_plot, _update_correlation_stats,
    # _select_variables, _apply_variable_selection, _select_all_vars, _deselect_all_vars,
    # _show_scatter_dialog, _create_scatter_plot, _export_analysis, _export_to_excel,
    # _show_in_window, _get_common_variables, _shorten_label
   
    def _show_help(self):
        """Показать справку по использованию корреляционного анализа"""
        help_text = """
            📊 КОРРЕЛЯЦИОННЫЙ АНАЛИЗ: КАК ИСПОЛЬЗОВАТЬ

            🔍 ЧТО ТАКОЕ КОРРЕЛЯЦИЯ?
            Корреляция показывает взаимосвязь между параметрами системы:
            • От -1.0 до 0.0: Отрицательная связь (при росте одного параметра другой уменьшается)
            • 0.0: Отсутствие связи
            • От 0.0 до +1.0: Положительная связь (параметры изменяются в одном направлении)

            🎯 КЛЮЧЕВЫЕ ИНСАЙТЫ ДЛЯ ТРЕЙДИНГА:

            1. СИЛЬНЫЕ КОРРЕЛЯЦИИ (>0.7 или <-0.7):
            • Выявляют дублирующие параметры - можно упростить систему
            • Помогают найти скрытые зависимости в стратегии

            2. КОРРЕЛЯЦИИ С КАПИТАЛОМ:
            • Положительные: параметры, способствующие росту капитала
            • Отрицательные: параметры, связанные с просадками

            3. УПРАВЛЕНИЕ РИСКАМИ:
            • Диверсифицируйте факторы с низкой корреляцией
            • Избегайте стратегий, зависящих от сильно коррелированных параметров

            4. ОПТИМИЗАЦИЯ СИСТЕМЫ:
            • Уберите избыточные параметры с высокой корреляцией
            • Сфокусируйтесь на независимых факторах влияния

            ⚠️ ВАЖНО: Корреляция ≠ причинно-следственная связь!
            Сильная корреляция не всегда означает, что один параметр вызывает изменение другого.

            📈 ПРАКТИЧЕСКОЕ ПРИМЕНЕНИЕ:
            • Анализируйте корреляции после каждого теста стратегии
            • Сравнивайте корреляции на разных рынках/периодах
            • Используйте для создания сбалансированных портфелей
                    """
        
        # Создаем окно помощи
        help_window = tk.Toplevel(self.frame)
        help_window.title("Справка по корреляционному анализу")
        help_window.geometry("600x500")
        help_window.resizable(True, True)
        
        # Создаем текстовое поле с прокруткой
        text_frame = ttk.Frame(help_window)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        text_widget = tk.Text(text_frame, wrap=tk.WORD, font=("Arial", 10), 
                             padx=10, pady=10, bg="#f8f9fa")
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Вставляем текст
        text_widget.insert(tk.END, help_text)
        text_widget.config(state=tk.DISABLED)
        
        # Кнопка закрытия
        close_btn = ttk.Button(help_window, text="Закрыть", 
                              command=help_window.destroy)
        close_btn.pack(pady=10)
        
        # Фокус на окно помощи
        help_window.transient(self.frame)
        help_window.grab_set()
        help_window.focus_set()
    
    def get_frame(self):
        """Возвращает фрейм вкладки"""
        return self.frame
    
    def _on_update_click(self):
        """Обработчик клика по кнопке обновления"""
        if hasattr(self, 'current_result_name'):
            self.update_plot(self.current_result_name)
    
    def update_plot(self, result_name: str):
        """Обновить график корреляций"""
        self.current_result_name = result_name
        
        try:
            if result_name not in self.visualizer.results_history:
                self.plot_frame.show_placeholder("Результат не найден")
                self.stats_label.config(text="")
                return
            
            data = self.visualizer.results_history[result_name]['results']
            
            # Проверка на пустые данные
            if data.empty:
                self.plot_frame.show_placeholder("Нет данных для анализа")
                self.stats_label.config(text="")
                return
                
            # Выбор числовых колонок для анализа
            numeric_cols = data.select_dtypes(include=[np.number]).columns
            
            # ФИЛЬТРАЦИЯ ПО ВЫБРАННЫМ ПЕРЕМЕННЫМ
            if self.selected_variables:
                numeric_cols = [col for col in numeric_cols if col in self.selected_variables]
            
            if len(numeric_cols) <= 1:
                self.plot_frame.show_placeholder("Недостаточно данных для корреляционного анализа")
                self.stats_label.config(text="")
                return
            
            # Обновление списка переменных для комбобокса
            current_targets = list(self.target_combo['values'])
            new_targets = [col for col in numeric_cols if col in self._get_common_variables()]
            if set(current_targets) != set(new_targets):
                self.target_combo['values'] = new_targets
                # Если текущая цель не в новых значениях, установить первую доступную
                if self.target_var.get() not in new_targets and new_targets:
                    self.target_var.set(new_targets[0])
            
            # Создание комплексного графика корреляций
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
            
            # График 1: Heatmap корреляций с использованием seaborn
            correlation_matrix = data[numeric_cols].corr()
            
            # Построение heatmap с seaborn
            sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                       fmt='.2f', linewidths=0.5, ax=ax1, cbar_kws={'shrink': 0.8},
                       annot_kws={'size': 8, 'weight': 'bold'})
            
            # Настройка осей
            ax1.set_xticklabels([self._shorten_label(col) for col in numeric_cols], 
                               rotation=45, ha='right', fontsize=9)
            ax1.set_yticklabels([self._shorten_label(col) for col in numeric_cols], 
                               fontsize=9)
            ax1.set_title('Матрица корреляций\n(тепловая карта взаимосвязей)', fontsize=12, fontweight='bold')
            
            # График 2: Важнейшие корреляции с выбранной целевой переменной
            target_var = self.target_var.get()
            if target_var in numeric_cols:
                target_correlations = correlation_matrix[target_var].drop(target_var).sort_values(ascending=False)
                
                # Выбор топ-8 наиболее коррелированных параметров
                top_count = min(8, len(target_correlations))
                top_correlations = target_correlations.head(top_count)
                
                colors = ['green' if x > 0 else 'red' for x in top_correlations.values]
                bars = ax2.barh(range(len(top_correlations)), top_correlations.values, 
                               color=colors, alpha=0.7)
                
                # Добавление значений на столбцы
                for i, (bar, value) in enumerate(zip(bars, top_correlations.values)):
                    ax2.text(value + (0.01 if value >= 0 else -0.05), i, 
                            f'{value:.3f}', va='center', 
                            fontweight='bold', color='black' if abs(value) < 0.7 else 'white')
                
                ax2.set_yticks(range(len(top_correlations)))
                ax2.set_yticklabels([self._shorten_label(idx) for idx in top_correlations.index])
                ax2.set_title(f'Топ-{top_count} корреляций с {self._shorten_label(target_var)}\n(ключевые факторы влияния)', 
                             fontsize=12, fontweight='bold')
                ax2.set_xlabel('Коэффициент корреляции')
                ax2.axvline(x=0, color='black', linestyle='-', alpha=0.5)
                ax2.axvline(x=0.5, color='blue', linestyle='--', alpha=0.3, label='Сильная корреляция')
                ax2.axvline(x=-0.5, color='blue', linestyle='--', alpha=0.3)
                ax2.grid(True, alpha=0.3, axis='x')
                ax2.legend()
                
                # Обновление статистики
                self._update_correlation_stats(correlation_matrix, target_var)
            else:
                ax2.text(0.5, 0.5, f'Переменная "{target_var}" не найдена\nв числовых данных', 
                        ha='center', va='center', transform=ax2.transAxes, fontsize=12)
                ax2.set_title('Корреляции с целевой переменной', fontsize=12, fontweight='bold')
                self.stats_label.config(text="Целевая переменная не найдена")
            
            plt.tight_layout()
            self.plot_frame.show_plot(fig)
            
        except Exception as e:
            self.plot_frame.show_placeholder(f"Ошибка построения графиков: {str(e)}")
            self.stats_label.config(text=f"Ошибка: {str(e)}")
    
    def _update_correlation_stats(self, correlation_matrix, target_var):
        """Обновить статистику корреляций"""
        try:
            # Статистика сильных корреляций
            strong_pos = ((correlation_matrix > 0.7) & (correlation_matrix < 1.0)).sum().sum()
            strong_neg = (correlation_matrix < -0.7).sum().sum()
            
            # Корреляции с целевой переменной
            target_corrs = correlation_matrix[target_var].drop(target_var)
            strong_target_pos = (target_corrs > 0.7).sum()
            strong_target_neg = (target_corrs < -0.7).sum()
            
            stats_text = (f"Сильные корр.: +{strong_pos}/-{strong_neg} | "
                         f"С {self._shorten_label(target_var)}: +{strong_target_pos}/-{strong_target_neg}")
            self.stats_label.config(text=stats_text)
            
        except Exception as e:
            self.stats_label.config(text=f"Ошибка статистики: {str(e)}")
    
    def _select_variables(self):
        """Диалог выбора переменных для анализа"""
        if not hasattr(self, 'current_result_name'):
            messagebox.showwarning("Предупреждение", "Сначала загрузите данные")
            return
            
        data = self.visualizer.results_history[self.current_result_name]['results']
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        select_window = tk.Toplevel(self.frame)
        select_window.title("Выбор переменных для анализа")
        select_window.geometry("400x500")
        
        # Список переменных с чекбоксами
        var_frame = ttk.Frame(select_window)
        var_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.var_checkboxes = {}
        for i, col in enumerate(numeric_cols):
            var = tk.BooleanVar(value=True)  # По умолчанию все выбраны
            cb = ttk.Checkbutton(var_frame, text=f"{self._shorten_label(col)} ({col})", 
                               variable=var)
            cb.grid(row=i, column=0, sticky=tk.W, pady=2)
            self.var_checkboxes[col] = var
        
        # Кнопки
        btn_frame = ttk.Frame(select_window)
        btn_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(btn_frame, text="Выбрать все", 
                  command=self._select_all_vars).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Сбросить", 
                  command=self._deselect_all_vars).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Применить", 
                  command=lambda: self._apply_variable_selection(select_window)).pack(side=tk.RIGHT, padx=5)
    
    def _apply_variable_selection(self, window):
        """Применить выбранные переменные"""
        self.selected_variables = [col for col, var in self.var_checkboxes.items() if var.get()]
        window.destroy()
        if hasattr(self, 'current_result_name'):
            self.update_plot(self.current_result_name)
    
    def _select_all_vars(self):
        """Выбрать все переменные"""
        for var in self.var_checkboxes.values():
            var.set(True)
    
    def _deselect_all_vars(self):
        """Сбросить выбор всех переменных"""
        for var in self.var_checkboxes.values():
            var.set(False)
    
    def _show_scatter_dialog(self):
        """Диалог для выбора переменных scatter plot"""
        if not hasattr(self, 'current_result_name'):
            messagebox.showwarning("Предупреждение", "Сначала загрузите данные")
            return
            
        data = self.visualizer.results_history[self.current_result_name]['results']
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        if len(numeric_cols) < 2:
            messagebox.showwarning("Предупреждение", "Недостаточно числовых переменных для scatter plot")
            return
        
        dialog = tk.Toplevel(self.frame)
        dialog.title("Scatter Plot - Выбор переменных")
        dialog.geometry("300x150")
        
        ttk.Label(dialog, text="X-axis:").grid(row=0, column=0, padx=5, pady=5, sticky=tk.W)
        x_var = tk.StringVar(value=numeric_cols[0])
        ttk.Combobox(dialog, textvariable=x_var, values=numeric_cols, width=20).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(dialog, text="Y-axis:").grid(row=1, column=0, padx=5, pady=5, sticky=tk.W)
        y_var = tk.StringVar(value=numeric_cols[1] if len(numeric_cols) > 1 else numeric_cols[0])
        ttk.Combobox(dialog, textvariable=y_var, values=numeric_cols, width=20).grid(row=1, column=1, padx=5, pady=5)
        
        def create_scatter():
            self._create_scatter_plot(x_var.get(), y_var.get())
            dialog.destroy()
        
        ttk.Button(dialog, text="Создать график", command=create_scatter).grid(row=2, column=0, columnspan=2, pady=10)
    
    def _create_scatter_plot(self, x_var, y_var):
        """Создать scatter plot для двух переменных"""
        data = self.visualizer.results_history[self.current_result_name]['results']
        
        if x_var not in data.columns or y_var not in data.columns:
            messagebox.showerror("Ошибка", "Выбранные переменные не найдены в данных")
            return
        
        fig, ax = plt.subplots(figsize=(10, 6))
        
        scatter = ax.scatter(data[x_var], data[y_var], alpha=0.6, s=50)
        ax.set_xlabel(self._shorten_label(x_var))
        ax.set_ylabel(self._shorten_label(y_var))
        
        # Расчет корреляции
        corr = data[x_var].corr(data[y_var])
        ax.set_title(f'{self._shorten_label(x_var)} vs {self._shorten_label(y_var)}\nКорреляция: {corr:.3f}')
        
        # Линия тренда
        if len(data) > 1:
            z = np.polyfit(data[x_var], data[y_var], 1)
            p = np.poly1d(z)
            ax.plot(data[x_var], p(data[x_var]), "r--", alpha=0.8, label=f'Тренд (R={corr:.3f})')
            ax.legend()
        
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Показать в отдельном окне
        self._show_in_window(fig, f"Scatter: {x_var} vs {y_var}")
    
    def _export_analysis(self):
        """Экспорт корреляционного анализа"""
        if not hasattr(self, 'current_result_name'):
            messagebox.showwarning("Предупреждение", "Сначала загрузите данные")
            return
            
        filename = f"correlation_analysis_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        filepath = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialfile=filename
        )
        
        if filepath:
            self._export_to_excel(filepath)
            messagebox.showinfo("Успех", f"Данные экспортированы в:\n{filepath}")
    
    def _export_to_excel(self, filepath):
        """Экспорт в Excel"""
        data = self.visualizer.results_history[self.current_result_name]['results']
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        
        if self.selected_variables:
            numeric_cols = [col for col in numeric_cols if col in self.selected_variables]
        
        correlation_matrix = data[numeric_cols].corr()
        
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            # Основная матрица
            correlation_matrix.to_excel(writer, sheet_name='Матрица корреляций')
            
            # Сильные корреляции
            strong_corrs = []
            threshold = self.corr_threshold.get()
            for i in range(len(correlation_matrix.columns)):
                for j in range(i+1, len(correlation_matrix.columns)):
                    corr_val = correlation_matrix.iloc[i, j]
                    if abs(corr_val) > threshold:
                        strong_corrs.append({
                            'Переменная 1': correlation_matrix.columns[i],
                            'Переменная 2': correlation_matrix.columns[j], 
                            'Корреляция': corr_val,
                            'Тип': 'Положительная' if corr_val > 0 else 'Отрицательная'
                        })
            
            if strong_corrs:
                pd.DataFrame(strong_corrs).to_excel(writer, sheet_name='Сильные корреляции', index=False)
            
            # Статистика
            stats_data = {
                'Метрика': ['Всего переменных', 'Сильные корреляции', 'Пороговое значение'],
                'Значение': [len(numeric_cols), len(strong_corrs), threshold]
            }
            pd.DataFrame(stats_data).to_excel(writer, sheet_name='Статистика', index=False)
    
    def _show_in_window(self, fig, title):
        """Показать график в отдельном окне"""
        window = tk.Toplevel(self.frame)
        window.title(title)
        window.geometry("800x600")
        
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        canvas = FigureCanvasTkAgg(fig, master=window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        
        # Кнопка закрытия
        ttk.Button(window, text="Закрыть", command=window.destroy).pack(pady=10)
    
    def _get_common_variables(self):
        """Возвращает список общих переменных для анализа"""
        return [
            'capital', 'kelly_f', 'position_size', 'risk_level', 'drawdown', 
            'close', 'ma_fast', 'ma_slow', 'ma_trend', 'signal', 'returns',
            'equity', 'balance', 'profit', 'loss', 'sharpe', 'volatility'
        ]
    
    def _shorten_label(self, label: str) -> str:
        """Сокращение длинных названий колонок для подписей"""
        short_names = {
            'capital': 'Капитал',
            'kelly_f': 'Келли f',
            'position_size': 'Позиция',
            'risk_level': 'Риск',
            'drawdown': 'Просадка',
            'close': 'Цена',
            'ma_fast': 'MA быстрая',
            'ma_slow': 'MA медленная',
            'ma_trend': 'MA тренд',
            'signal': 'Сигнал',
            'returns': 'Доходность',
            'equity': 'Эквити',
            'balance': 'Баланс',
            'profit': 'Прибыль',
            'loss': 'Убыток',
            'sharpe': 'Шарп',
            'volatility': 'Волатильность'
        }
        return short_names.get(label, label[:12] + '...' if len(label) > 12 else label)
# ===== СЕКЦИЯ 3: ВИЗУАЛИЗАЦИЯ РЕЗУЛЬТАТОВ =====
"""
Класс для визуализации и анализа результатов тестирования
Содержит методы для построения графиков и генерации отчетов
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
from typing import List, Dict, Optional
from utils.analytics import analyze_performance

class ResultsVisualizer:
    """Класс для визуализации результатов тестирования"""
    
    def __init__(self):
        self.results_history = {}
        self.validation_results = {}
        self.trade_analytics = {}
    
    def add_simulation_result(self, name: str, results: pd.DataFrame, performance: dict):
        """Добавление результатов симуляции"""
        self.results_history[name] = {
            'results': results,
            'performance': performance,
            'timestamp': datetime.now()
        }
    
    def add_validation_result(self, name: str, results: dict):
        """Добавление результатов валидации"""
        self.validation_results[name] = {
            'results': results,
            'timestamp': datetime.now()
        }
    
    def get_performance_summary(self, result_name: str = None) -> str:
        """Получить сводку производительности в виде текста"""
        if not self.results_history:
            return "Нет данных для отображения"
        
        if result_name:
            results = {result_name: self.results_history[result_name]}
        else:
            results = self.results_history
        
        summary = "=" * 80 + "\n"
        summary += "СВОДКА ПРОИЗВОДИТЕЛЬНОСТИ\n"
        summary += "=" * 80 + "\n"
        
        for name, data in results.items():
            perf = data['performance']
            summary += f"\n📊 {name.upper()}\n"
            summary += "-" * 40 + "\n"
            summary += f"💰 Капитал: ${perf['final_capital']:,.2f} | Доходность: {perf['total_return']:+.2f}%\n"
            summary += f"📉 Макс. просадка: {perf['max_drawdown']:.2f}% | Средняя: {perf.get('avg_drawdown', 0):.2f}%\n"
            summary += f"🎯 Коэф. Шарпа: {perf['sharpe_ratio']:.2f} | Волатильность: {perf.get('volatility', 0):.2f}%\n"
            summary += f"⚖️  Средний f: {perf['avg_kelly_f']:.3f} | Средний риск: {perf.get('avg_risk', 0):.1f}%\n"
            summary += f"📏 Средняя позиция: ${perf['avg_position_size']:,.2f}\n"
            
            if 'total_costs' in perf:
                summary += f"💸 Издержки: ${perf['total_costs']:.2f} ({perf.get('costs_percentage', 0):.2f}%)\n"
        
        return summary

    def plot_comparison_chart(self, result_names: List[str] = None, figsize=(12, 8)):
        """Сравнительный график нескольких тестов"""
        if not self.results_history:
            print("Нет данных для сравнения")
            return None
        
        if result_names is None:
            result_names = list(self.results_history.keys())[:4]
        
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize)
        colors = ['blue', 'green', 'red', 'orange', 'purple', 'brown']
        
        # График 1: Сравнение капитала
        for i, name in enumerate(result_names):
            if name in self.results_history:
                data = self.results_history[name]['results']
                ax1.plot(data.index, data['capital'], label=name, linewidth=2, 
                        color=colors[i % len(colors)])
        
        ax1.set_title('Сравнение динамики капитала', fontsize=12, fontweight='bold')
        ax1.set_xlabel('Время')
        ax1.set_ylabel('Капитал ($)')
        ax1.legend()
        ax1.grid(True, alpha=0.3)
        
        # График 2: Сравнение просадок
        for i, name in enumerate(result_names):
            if name in self.results_history:
                data = self.results_history[name]['results']
                if 'drawdown' in data.columns:
                    ax2.plot(data.index, data['drawdown'] * 100, label=name, 
                            linewidth=2, color=colors[i % len(colors)])
        
        ax2.set_title('Сравнение просадок', fontsize=12, fontweight='bold')
        ax2.set_xlabel('Время')
        ax2.set_ylabel('Просадка (%)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # График 3: Гистограмма доходностей
        returns = []
        labels = []
        for name in result_names:
            if name in self.results_history:
                perf = self.results_history[name]['performance']
                returns.append(perf['total_return'])
                labels.append(name)
        
        colors_bars = ['green' if x >= 0 else 'red' for x in returns]
        bars = ax3.bar(labels, returns, color=colors_bars, alpha=0.7)
        
        for bar, value in zip(bars, returns):
            ax3.text(bar.get_x() + bar.get_width()/2, bar.get_height() + (0.1 if value >=0 else -0.5),
                    f'{value:.1f}%', ha='center', va='bottom' if value >=0 else 'top', 
                    fontweight='bold')
        
        ax3.set_title('Сравнение общей доходности', fontsize=12, fontweight='bold')
        ax3.set_ylabel('Доходность (%)')
        ax3.tick_params(axis='x', rotation=45)
        ax3.grid(True, alpha=0.3)
        
        # График 4: Основные метрики
        metrics = ['total_return', 'sharpe_ratio', 'max_drawdown']
        metric_names = ['Доходность\n(%)', 'Коэф.\nШарпа', 'Просадка\n(%)']
        
        x = np.arange(len(metric_names))
        width = 0.8 / len(result_names)
        
        for i, name in enumerate(result_names):
            if name in self.results_history:
                perf = self.results_history[name]['performance']
                values = [
                    perf.get('total_return', 0),
                    perf.get('sharpe_ratio', 0),
                    -perf.get('max_drawdown', 0)  # Отрицательное для визуализации
                ]
                ax4.bar(x + i * width, values, width, label=name, alpha=0.7, 
                       color=colors[i % len(colors)])
        
        ax4.set_title('Сравнение основных метрик', fontsize=12, fontweight='bold')
        ax4.set_ylabel('Значение')
        ax4.set_xticks(x + width * (len(result_names) - 1) / 2)
        ax4.set_xticklabels(metric_names)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig

    # В методе get_detailed_stats добавляем раздел рисков:
    def get_detailed_stats(self, result_name: str) -> str:
        """Получить детальную статистику в виде текста"""
        if result_name not in self.results_history:
            return f"Результат '{result_name}' не найден"
        
        data = self.results_history[result_name]['results']
        perf = self.results_history[result_name]['performance']
        daily_returns = data['capital'].pct_change().dropna() * 100
        
        stats = "=" * 60 + "\n"
        stats += "ДЕТАЛЬНАЯ СТАТИСТИКА\n"
        stats += "=" * 60 + "\n"
        
        stats += f"\n📈 ОСНОВНЫЕ МЕТРИКИ:\n"
        stats += f"   Общая доходность: {perf['total_return']:+.2f}%\n"
        stats += f"   Коэффициент Шарпа: {perf['sharpe_ratio']:.2f}\n"
        stats += f"   Максимальная просадка: {perf['max_drawdown']:.2f}%\n"
        stats += f"   Волатильность: {perf.get('volatility', 0):.2f}%\n"
        
        stats += f"\n⚖️  УПРАВЛЕНИЕ РИСКАМИ:\n"
        stats += f"   Средний Kelly f: {perf['avg_kelly_f']:.3f}\n"
        stats += f"   Средний уровень риска: {perf.get('avg_risk', 0):.1f}%\n"
        stats += f"   Средний размер позиции: ${perf['avg_position_size']:,.2f}\n"
        stats += f"   Корректировок риска: {perf.get('risk_adjustments', 0)}\n"
        
        # 🆕 РАЗДЕЛ СИСТЕМЫ РИСК-МЕНЕДЖМЕНТА
        if perf.get('risk_system_enabled', False):
            stats += f"\n🛡️  СИСТЕМА УПРАВЛЕНИЯ РИСКАМИ:\n"
            stats += f"   Сделок с рисками: {perf.get('total_trades_with_risk', 0)}\n"
            stats += f"   Стоп-лоссов: {perf.get('stop_loss_trades', 0)}\n"
            stats += f"   Тейк-профитов: {perf.get('take_profit_trades', 0)}\n"
            stats += f"   Risk-Reward Ratio: {perf.get('risk_reward_ratio', 0):.2f}\n"
            stats += f"   Win Rate с рисками: {perf.get('win_rate_with_stops', 0):.1f}%\n"
        
        stats += f"\n💸 ТРАНЗАКЦИОННЫЕ ИЗДЕРЖКИ:\n"
        if 'total_costs' in perf:
            stats += f"   Общие издержки: ${perf['total_costs']:.2f}\n"
            stats += f"   Комиссии: ${perf.get('total_commission', 0):.2f}\n"
            stats += f"   Проскальзывание: ${perf.get('total_slippage', 0):.2f}\n"
            stats += f"   Издержки в %: {perf.get('costs_percentage', 0):.2f}%\n"
        
        stats += f"\n📊 СТАТИСТИКА ДОХОДНОСТЕЙ:\n"
        stats += f"   Средняя дневная доходность: {daily_returns.mean():.4f}%\n"
        stats += f"   Стандартное отклонение: {daily_returns.std():.4f}%\n"
        stats += f"   Асимметрия: {daily_returns.skew():.3f}\n"
        stats += f"   Эксцесс: {daily_returns.kurtosis():.3f}\n"
        
        return stats

    def get_available_results(self) -> List[str]:
        """Получить список доступных результатов"""
        return list(self.results_history.keys())
    
    def get_available_validations(self) -> List[str]:
        """Получить список доступных валидаций"""
        return list(self.validation_results.keys())
    

    # 🆕 ДОБАВЛЯЕМ НОВЫЕ МЕТОДЫ В КЛАСС ResultsVisualizer

    def plot_risk_levels(self, result_name: str, figsize=(14, 10)):
        """
        Создание графика с отображением риск-ордеров и точек выхода
        """
        if result_name not in self.results_history:
            print(f"❌ Результат '{result_name}' не найден")
            return None
        
        try:
            data = self.results_history[result_name]['results']
            
            # 🆕 СОЗДАЕМ ТОЛЬКО НУЖНОЕ КОЛИЧЕСТВО ГРАФИКОВ
            # Если есть история сделок - 4 графика, иначе - 2
            has_trade_history = 'trade_history' in self.results_history[result_name]
            
            if has_trade_history:
                fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=figsize)
            else:
                fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
            
            fig.suptitle(f'📊 Визуализация риск-менеджмента: {result_name}', 
                        fontsize=14, fontweight='bold')
            
            # График 1: Цены с риск-ордерами
            ax1.plot(data.index, data['close'], label='Цена закрытия', 
                    linewidth=1, color='black', alpha=0.7)
            
            # Отображение стоп-лоссов и тейк-профитов (только где есть позиции)
            positions = data[data['position_type'] != 0]
            if not positions.empty and 'stop_loss_level' in positions.columns:
                # Стоп-лоссы
                stops = positions[positions['stop_loss_level'] > 0]
                if not stops.empty:
                    ax1.scatter(stops.index, stops['stop_loss_level'], 
                            color='red', marker='_', s=30, label='Стоп-лосс', alpha=0.6)
                
                # Тейк-профиты
                takes = positions[positions['take_profit_level'] > 0]
                if not takes.empty:
                    ax1.scatter(takes.index, takes['take_profit_level'], 
                            color='green', marker='_', s=30, label='Тейк-профит', alpha=0.6)
            
            # Отметки точек выхода
            exit_points = data[data['exit_reason'] != '']
            exit_colors = {
                'stop_loss': 'red',
                'take_profit': 'green', 
                'trailing_stop': 'orange',
                'time_stop': 'purple',
                'signal_sell': 'blue',
                'signal_buy': 'blue'
            }
            
            for reason, color in exit_colors.items():
                points = exit_points[exit_points['exit_reason'] == reason]
                if not points.empty:
                    ax1.scatter(points.index, points['close'], 
                            color=color, marker='o', s=40, label=f'Выход: {reason}', alpha=0.8)
            
            ax1.set_title('📈 Цены с риск-ордерами и точками выхода')
            ax1.set_ylabel('Цена')
            ax1.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax1.grid(True, alpha=0.3)
            
            # График 2: Капитал с отметками выходов
            ax2.plot(data.index, data['capital'], label='Капитал', linewidth=2, color='blue')
            
            for reason, color in exit_colors.items():
                points = exit_points[exit_points['exit_reason'] == reason]
                if not points.empty:
                    ax2.scatter(points.index, points['capital'], 
                            color=color, marker='o', s=50, label=f'Выход: {reason}', alpha=0.8)
            
            ax2.set_title('💰 Динамика капитала с точками выхода')
            ax2.set_ylabel('Капитал ($)')
            ax2.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
            ax2.grid(True, alpha=0.3)
            
            # График 3: Распределение PnL по типам выходов (только если есть история сделок)
            if has_trade_history:
                trades = self.results_history[result_name]['trade_history']
                if not trades.empty and 'exit_reason' in trades.columns:
                    # Группируем по причинам выхода
                    pnl_by_reason = trades.groupby('exit_reason')['pnl_percent'].agg(['mean', 'count', 'std'])
                    
                    if not pnl_by_reason.empty:
                        reasons = pnl_by_reason.index
                        means = pnl_by_reason['mean']
                        counts = pnl_by_reason['count']
                        
                        colors = [exit_colors.get(reason, 'gray') for reason in reasons]
                        bars = ax3.bar(reasons, means, color=colors, alpha=0.7, yerr=pnl_by_reason['std'])
                        
                        # Добавляем подписи
                        for bar, count, mean_val in zip(bars, counts, means):
                            height = bar.get_height()
                            ax3.text(bar.get_x() + bar.get_width()/2., height,
                                    f'n={count}\n{mean_val:+.1f}%', 
                                    ha='center', va='bottom' if height >=0 else 'top',
                                    fontsize=8)
                        
                        ax3.set_title('📊 Средний PnL по типам выходов')
                        ax3.set_ylabel('Средний PnL (%)')
                        ax3.tick_params(axis='x', rotation=45)
                        ax3.grid(True, alpha=0.3)
                else:
                    ax3.text(0.5, 0.5, 'Нет данных о сделках', 
                            ha='center', va='center', transform=ax3.transAxes, fontsize=12)
                    ax3.set_title('📊 Средний PnL по типам выходов')
            
            # График 4: Эффективность риск-ордеров во времени (только если есть точки выхода)
            if has_trade_history and not exit_points.empty and 'pnl_percent' in exit_points.columns:
                # Создаем скользящее окно эффективности
                window_size = min(20, len(exit_points))
                if window_size > 5:
                    exit_points_sorted = exit_points.sort_index()
                    
                    # Рассчитываем скользящую эффективность
                    rolling_profitable = exit_points_sorted['pnl_percent'].rolling(
                        window=window_size).apply(lambda x: (x > 0).sum() / len(x) * 100)
                    
                    ax4.plot(rolling_profitable.index, rolling_profitable, 
                            label='Процент прибыльных выходов', linewidth=2, color='purple')
                    ax4.axhline(y=50, color='red', linestyle='--', alpha=0.7, label='Уровень 50%')
                    
                    ax4.set_title('📈 Эффективность выходов (скользящее окно)')
                    ax4.set_ylabel('Процент прибыльных выходов (%)')
                    ax4.legend()
                    ax4.grid(True, alpha=0.3)
                else:
                    ax4.text(0.5, 0.5, 'Недостаточно данных\nдля анализа эффективности', 
                            ha='center', va='center', transform=ax4.transAxes, fontsize=10)
                    ax4.set_title('📈 Эффективность выходов')
            elif has_trade_history:
                ax4.text(0.5, 0.5, 'Нет данных о точках выхода', 
                        ha='center', va='center', transform=ax4.transAxes, fontsize=10)
                ax4.set_title('📈 Эффективность выходов')
            
            plt.tight_layout()
            return fig
            
        except Exception as e:
            print(f"❌ Ошибка построения графика риск-ордеров: {e}")
            return None

    def get_detailed_risk_stats(self, result_name: str) -> str:
        """Получение детальной статистики по риск-менеджменту"""
        if result_name not in self.results_history:
            return f"❌ Результат '{result_name}' не найден"
        
        try:
            data = self.results_history[result_name]
            performance = data['performance']
            
            stats = "=" * 70 + "\n"
            stats += "📊 ДЕТАЛЬНАЯ СТАТИСТИКА РИСК-МЕНЕДЖМЕНТА\n"
            stats += "=" * 70 + "\n\n"
            
            # Основные метрики рисков
            if performance.get('risk_system_enabled', False):
                stats += "✅ СИСТЕМА РИСК-МЕНЕДЖМЕНТА АКТИВНА\n\n"
                
                stats += "📈 ОСНОВНЫЕ МЕТРИКИ:\n"
                stats += f"• Сделок с рисками: {performance.get('total_trades_with_risk', 0)}\n"
                stats += f"• Стоп-лоссы: {performance.get('stop_loss_trades', 0)}\n"
                stats += f"• Тейк-профиты: {performance.get('take_profit_trades', 0)}\n"
                stats += f"• Трейлинг-стопы: {performance.get('trailing_stop_trades', 0)}\n"
                stats += f"• Risk-Reward Ratio: {performance.get('risk_reward_ratio', 0):.2f}\n"
                stats += f"• Win Rate с рисками: {performance.get('win_rate_with_stops', 0):.1f}%\n\n"
                
                # Анализ PnL по причинам
                if 'pnl_by_reason' in performance:
                    stats += "💰 PnL ПО ПРИЧИНАМ ВЫХОДА:\n"
                    pnl_data = performance['pnl_by_reason']
                    for reason, stats_data in pnl_data.items():
                        if 'mean' in stats_data:
                            mean_pnl = stats_data['mean']
                            count = stats_data.get('count', 0)
                            color = "🟢" if mean_pnl > 0 else "🔴"
                            stats += f"• {color} {reason}: {mean_pnl:+.2f}% (n={count})\n"
                    stats += "\n"
                
                # Эффективность стоп-лоссов
                stats += "🛑 ЭФФЕКТИВНОСТЬ СТОП-ЛОССОВ:\n"
                stats += f"• Средний PnL: {performance.get('avg_stop_loss_pnl', 0):+.2f}%\n"
                stats += f"• Эффективность: {performance.get('stop_loss_efficiency', 0):.1f}%\n\n"
                
            else:
                stats += "❌ СИСТЕМА РИСК-МЕНЕДЖМЕНТА НЕ АКТИВНА\n"
                stats += "Сделки закрывались только по торговым сигналам\n\n"
            
            # Расширенная аналитика из trade_history
            if 'trade_history' in data:
                trades = data['trade_history']
                if not trades.empty:
                    risk_trades = trades[trades['exit_reason'].isin([
                        'stop_loss', 'take_profit', 'trailing_stop', 'time_stop'
                    ])]
                    
                    if not risk_trades.empty:
                        stats += "📊 РАСШИРЕННАЯ АНАЛИТИКА:\n"
                        stats += f"• Всего сделок: {len(trades)}\n"
                        stats += f"• Сделок с рисками: {len(risk_trades)}\n"
                        stats += f"• Среднее время удержания: {risk_trades['duration'].mean():.1f} дней\n"
                        stats += f"• Макс. время удержания: {risk_trades['duration'].max():.1f} дней\n\n"
            
            # Рекомендации
            stats += "💡 РЕКОМЕНДАЦИИ:\n"
            win_rate = performance.get('win_rate_with_stops', 0)
            risk_reward = performance.get('risk_reward_ratio', 0)
            
            if win_rate > 60 and risk_reward > 1.5:
                stats += "• 🎉 Отличные параметры рисков! Продолжайте в том же духе.\n"
            elif win_rate > 50 and risk_reward > 1.0:
                stats += "• 👍 Хорошие результаты. Можно экспериментировать с параметрами.\n"
            elif win_rate < 40 or risk_reward < 0.8:
                stats += "• ⚠️ Рекомендуется оптимизировать параметры риск-менеджмента.\n"
            else:
                stats += "• 📈 Стабильные результаты. Рассмотрите тонкую настройку параметров.\n"
            
            return stats
            
        except Exception as e:
            return f"❌ Ошибка формирования статистики: {str(e)}"

    def get_risk_efficiency_report(self, result_name: str) -> str:
        """Генерация отчета об эффективности риск-менеджмента"""
        if result_name not in self.results_history:
            return f"❌ Результат '{result_name}' не найден"
        
        try:
            data = self.results_history[result_name]
            performance = data['performance']
            
            report = "🎯 ОТЧЕТ ЭФФЕКТИВНОСТИ РИСК-МЕНЕДЖМЕНТА\n"
            report += "=" * 50 + "\n\n"
            
            # Основная статистика
            if performance.get('risk_system_enabled', False):
                report += "✅ СИСТЕМА РИСК-МЕНЕДЖМЕНТА АКТИВНА\n\n"
                
                report += "📊 ОСНОВНЫЕ ПОКАЗАТЕЛИ:\n"
                report += f"• Сделок с рисками: {performance.get('total_trades_with_risk', 0)}\n"
                report += f"• Стоп-лоссы: {performance.get('stop_loss_trades', 0)}\n"
                report += f"• Тейк-профиты: {performance.get('take_profit_trades', 0)}\n"
                report += f"• Risk-Reward Ratio: {performance.get('risk_reward_ratio', 0):.2f}\n"
                report += f"• Win Rate: {performance.get('win_rate_with_stops', 0):.1f}%\n\n"
                
                # Анализ PnL по типам выходов
                if 'pnl_by_reason' in performance:
                    report += "💰 PnL ПО ТИПАМ ВЫХОДОВ:\n"
                    pnl_data = performance['pnl_by_reason']
                    for reason, stats in pnl_data.items():
                        if 'mean' in stats:
                            mean_pnl = stats['mean']
                            count = stats.get('count', 0)
                            emoji = "🟢" if mean_pnl > 0 else "🔴"
                            report += f"• {emoji} {reason}: {mean_pnl:+.2f}% (n={count})\n"
                    report += "\n"
                
                # Эффективность стоп-лоссов
                avg_stop_pnl = performance.get('avg_stop_loss_pnl', 0)
                stop_efficiency = performance.get('stop_loss_efficiency', 0)
                report += f"🛑 ЭФФЕКТИВНОСТЬ СТОП-ЛОССОВ:\n"
                report += f"• Средний PnL: {avg_stop_pnl:+.2f}%\n"
                report += f"• Доля от всех сделок: {stop_efficiency:.1f}%\n\n"
                
            else:
                report += "❌ СИСТЕМА РИСК-МЕНЕДЖМЕНТА НЕ АКТИВНА\n"
                report += "Сделки закрывались только по торговым сигналам\n\n"
            
            # Расширенная статистика из истории сделок
            if 'trade_history' in data:
                trades = data['trade_history']
                if not trades.empty:
                    risk_trades = trades[trades['exit_reason'].isin(['stop_loss', 'take_profit', 'trailing_stop'])]
                    
                    if not risk_trades.empty:
                        report += "📈 РАСШИРЕННАЯ СТАТИСТИКА:\n"
                        report += f"• Всего сделок: {len(trades)}\n"
                        report += f"• Сделок с рисками: {len(risk_trades)}\n"
                        report += f"• Средняя продолжительность: {risk_trades['duration'].mean():.1f} дней\n"
                        report += f"• Макс. продолжительность: {risk_trades['duration'].max():.1f} дней\n\n"
            
            # Рекомендации
            report += "💡 РЕКОМЕНДАЦИИ:\n"
            win_rate = performance.get('win_rate_with_stops', 0)
            risk_reward = performance.get('risk_reward_ratio', 0)
            
            if win_rate > 60 and risk_reward > 1.5:
                report += "• 🎉 Отличные параметры рисков! Продолжайте в том же духе.\n"
            elif win_rate > 50 and risk_reward > 1.0:
                report += "• 👍 Хорошие результаты. Можно экспериментировать с параметрами.\n"
            elif win_rate < 40 or risk_reward < 0.8:
                report += "• ⚠️ Рекомендуется оптимизировать параметры риск-менеджмента.\n"
                report += "• Попробуйте изменить множители ATR для стоп-лоссов и тейк-профитов\n"
            else:
                report += "• 📈 Стабильные результаты. Рассмотрите тонкую настройку параметров.\n"
            
            return report
            
        except Exception as e:
            return f"❌ Ошибка формирования отчета: {str(e)}"    
        

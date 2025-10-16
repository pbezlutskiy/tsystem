# ===== СЕКЦИЯ 5: АНАЛИТИКА И РАСЧЕТЫ ПРОИЗВОДИТЕЛЬНОСТИ =====
"""
Модуль аналитических функций для расчета метрик производительности
Статистический анализ результатов торговли
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, List

def analyze_performance(results: pd.DataFrame, initial_capital: float) -> Dict[str, Any]:
    """Комплексный анализ результатов торговли с расчетом ключевых метрик"""
    capital = results['capital']

    # Основные метрики доходности
    total_return_pct = (capital.iloc[-1] - initial_capital) / initial_capital * 100

    # Расчет просадки
    cumulative_max = capital.cummax()
    drawdown = (cumulative_max - capital) / cumulative_max
    max_drawdown_pct = drawdown.max() * 100
    avg_drawdown = drawdown.mean() * 100

    # Расчет волатильности и Шарпа
    returns = capital.pct_change().dropna()
    
    if len(returns) > 0 and returns.std() > 0:
        sharpe = returns.mean() / returns.std() * np.sqrt(252)
    else:
        sharpe = 0

    volatility = returns.std() * np.sqrt(252) * 100 if len(returns) > 0 else 0
    
    # Дополнительные метрики управления рисками
    avg_risk = results['risk_level'].mean() * 100 if 'risk_level' in results.columns else 1.0
    risk_adjustments = len(results[results['risk_level'] != results['risk_level'].iloc[0]]) if 'risk_level' in results.columns else 0

    # 🆕 АНАЛИЗ ЭФФЕКТИВНОСТИ РИСК-МЕНЕДЖМЕНТА
    risk_metrics = analyze_risk_management(results)

    # Сбор всех метрик в словарь
    performance = {
        'total_return': total_return_pct,
        'max_drawdown': max_drawdown_pct,
        'sharpe_ratio': sharpe,
        'final_capital': capital.iloc[-1],
        'volatility': volatility,
        'avg_drawdown': avg_drawdown,
        'avg_kelly_f': results['kelly_f'].mean() if 'kelly_f' in results.columns else 0,
        'avg_position_size': results['position_size'].mean() if 'position_size' in results.columns else 0,
        'avg_risk': avg_risk,
        'risk_adjustments': risk_adjustments,
        'initial_capital': initial_capital,
        # 🆕 МЕТРИКИ РИСК-МЕНЕДЖМЕНТА
        **risk_metrics
    }

    return performance

# 🆕 НОВАЯ ФУНКЦИЯ: Анализ эффективности системы управления рисками

def analyze_risk_management(results: pd.DataFrame) -> Dict[str, Any]:
    """
    Анализ эффективности системы стоп-лоссов и тейк-профитов
    """
    risk_metrics = {
        'risk_system_enabled': False,
        'total_trades_with_risk': 0,
        'stop_loss_trades': 0,
        'take_profit_trades': 0,
        'trailing_stop_trades': 0,
        'time_stop_trades': 0,
        'avg_stop_loss_pnl': 0,
        'avg_take_profit_pnl': 0,
        'stop_loss_efficiency': 0,
        'risk_reward_ratio': 0,
        'win_rate_with_stops': 0
    }
    
    # Проверяем наличие данных о рисках
    if 'exit_reason' not in results.columns:
        return risk_metrics
    
    # Фильтруем сделки с указанной причиной выхода
    exit_trades = results[results['exit_reason'] != '']
    if exit_trades.empty:
        return risk_metrics
    
    risk_metrics['risk_system_enabled'] = True
    risk_metrics['total_trades_with_risk'] = len(exit_trades)
    
    # Анализ по типам выходов
    risk_exit_reasons = ['stop_loss', 'take_profit', 'trailing_stop', 'time_stop']
    
    for reason in risk_exit_reasons:
        reason_trades = exit_trades[exit_trades['exit_reason'] == reason]
        count = len(reason_trades)
        
        if count > 0:
            risk_metrics[f'{reason}_trades'] = count
            
            # Средний PnL для этого типа выхода (используем абсолютный PnL если процентного нет)
            if 'pnl_percent' in reason_trades.columns:
                avg_pnl = reason_trades['pnl_percent'].mean()
            elif 'pnl_absolute' in reason_trades.columns and 'capital_before' in reason_trades.columns:
                # Рассчитываем процентный PnL на лету
                pnl_pct = (reason_trades['pnl_absolute'] / reason_trades['capital_before']) * 100
                avg_pnl = pnl_pct.mean()
            else:
                avg_pnl = 0
                
            risk_metrics[f'avg_{reason}_pnl'] = avg_pnl
    
    # Эффективность стоп-лоссов
    stop_loss_trades = exit_trades[exit_trades['exit_reason'] == 'stop_loss']
    if len(stop_loss_trades) > 0:
        # Процент стоп-лоссов от общего числа сделок
        risk_metrics['stop_loss_efficiency'] = len(stop_loss_trades) / len(exit_trades) * 100
        
        # Средний убыток по стоп-лоссам
        if 'pnl_percent' in stop_loss_trades.columns:
            avg_stop_loss = stop_loss_trades['pnl_percent'].mean()
        elif 'pnl_absolute' in stop_loss_trades.columns and 'capital_before' in stop_loss_trades.columns:
            pnl_pct = (stop_loss_trades['pnl_absolute'] / stop_loss_trades['capital_before']) * 100
            avg_stop_loss = pnl_pct.mean()
        else:
            avg_stop_loss = 0
            
        risk_metrics['avg_stop_loss_pnl'] = avg_stop_loss
    
    # Risk-Reward Ratio
    take_profit_trades = exit_trades[exit_trades['exit_reason'] == 'take_profit']
    if len(take_profit_trades) > 0 and len(stop_loss_trades) > 0:
        if 'pnl_percent' in take_profit_trades.columns:
            avg_profit = take_profit_trades['pnl_percent'].mean()
        elif 'pnl_absolute' in take_profit_trades.columns and 'capital_before' in take_profit_trades.columns:
            pnl_pct = (take_profit_trades['pnl_absolute'] / take_profit_trades['capital_before']) * 100
            avg_profit = pnl_pct.mean()
        else:
            avg_profit = 0
            
        avg_loss = abs(risk_metrics['avg_stop_loss_pnl'])
        
        if avg_loss > 0:
            risk_metrics['risk_reward_ratio'] = avg_profit / avg_loss
    
    # Win Rate с использованием стоп-лоссов
    if 'pnl_percent' in exit_trades.columns:
        winning_risk_trades = exit_trades[exit_trades['pnl_percent'] > 0]
    elif 'pnl_absolute' in exit_trades.columns:
        winning_risk_trades = exit_trades[exit_trades['pnl_absolute'] > 0]
    else:
        winning_risk_trades = pd.DataFrame()
        
    if len(exit_trades) > 0:
        risk_metrics['win_rate_with_stops'] = len(winning_risk_trades) / len(exit_trades) * 100
    
    # Анализ распределения PnL по причинам выхода
    pnl_data = {}
    for reason in risk_exit_reasons:
        reason_trades = exit_trades[exit_trades['exit_reason'] == reason]
        if len(reason_trades) > 0:
            if 'pnl_percent' in reason_trades.columns:
                pnl_data[reason] = {
                    'mean': reason_trades['pnl_percent'].mean(),
                    'std': reason_trades['pnl_percent'].std(),
                    'count': len(reason_trades)
                }
            elif 'pnl_absolute' in reason_trades.columns and 'capital_before' in reason_trades.columns:
                pnl_pct = (reason_trades['pnl_absolute'] / reason_trades['capital_before']) * 100
                pnl_data[reason] = {
                    'mean': pnl_pct.mean(),
                    'std': pnl_pct.std(),
                    'count': len(reason_trades)
                }
    
    if pnl_data:
        risk_metrics['pnl_by_reason'] = pnl_data
    
    return risk_metrics

# 🆕 НОВАЯ ФУНКЦИЯ: Детальный анализ сделок с рисками
def analyze_trades_with_risk_management(trade_history: pd.DataFrame) -> Dict[str, Any]:
    """
    Детальный анализ сделок с учетом системы управления рисками
    
    Parameters:
    -----------
    trade_history : pd.DataFrame
        История сделок с колонками exit_reason, stop_loss, take_profit
        
    Returns:
    --------
    dict
        Детальная статистика по сделкам с рисками
    """
    if trade_history.empty:
        return {}
    
    analysis = {
        'total_trades': len(trade_history),
        'trades_with_risk_data': 0,
        'exit_reason_stats': {},
        'avg_risk_metrics': {},
        'risk_efficiency': {}
    }
    
    # Проверяем наличие данных о рисках
    if 'exit_reason' not in trade_history.columns:
        return analysis
    
    # Статистика по причинам выхода
    exit_reasons = trade_history['exit_reason'].value_counts()
    analysis['exit_reason_stats'] = exit_reasons.to_dict()
    
    # Анализ эффективности по типам выходов
    for reason in exit_reasons.index:
        reason_trades = trade_history[trade_history['exit_reason'] == reason]
        
        reason_stats = {
            'count': len(reason_trades),
            'avg_pnl': reason_trades['pnl_percent'].mean() if 'pnl_percent' in reason_trades.columns else 0,
            'win_rate': len(reason_trades[reason_trades['pnl_percent'] > 0]) / len(reason_trades) * 100 if len(reason_trades) > 0 else 0,
            'avg_duration': reason_trades['duration'].mean() if 'duration' in reason_trades.columns else 0
        }
        
        analysis['risk_efficiency'][reason] = reason_stats
    
    # Анализ расстояний стоп-лоссов и тейк-профитов
    if 'stop_loss' in trade_history.columns and 'take_profit' in trade_history.columns:
        valid_trades = trade_history[
            (trade_history['stop_loss'] > 0) & 
            (trade_history['take_profit'] > 0) &
            (trade_history['entry_price'] > 0)
        ]
        
        if not valid_trades.empty:
            # Расчет риск-риворд соотношений
            risk_rewards = []
            for _, trade in valid_trades.iterrows():
                if trade['position_type'] == 1:  # LONG
                    risk = trade['entry_price'] - trade['stop_loss']
                    reward = trade['take_profit'] - trade['entry_price']
                else:  # SHORT
                    risk = trade['stop_loss'] - trade['entry_price']
                    reward = trade['entry_price'] - trade['take_profit']
                
                if risk > 0:
                    risk_rewards.append(reward / risk)
            
            if risk_rewards:
                analysis['avg_risk_metrics'] = {
                    'avg_risk_reward_ratio': np.mean(risk_rewards),
                    'median_risk_reward_ratio': np.median(risk_rewards),
                    'min_risk_reward_ratio': np.min(risk_rewards),
                    'max_risk_reward_ratio': np.max(risk_rewards)
                }
    
    analysis['trades_with_risk_data'] = len(trade_history[trade_history['exit_reason'] != ''])
    
    return analysis

def calculate_trade_metrics(trade_history: pd.DataFrame) -> Dict[str, Any]:
    """Расчет детальных метрик по сделкам"""
    if trade_history.empty:
        return {}
    
    metrics = {
        'total_trades': len(trade_history),
        'winning_trades': len(trade_history[trade_history['pnl_absolute'] > 0]),
        'losing_trades': len(trade_history[trade_history['pnl_absolute'] < 0]),
        'total_pnl': trade_history['pnl_absolute'].sum(),
        'avg_pnl_per_trade': trade_history['pnl_absolute'].mean(),
        'win_rate': len(trade_history[trade_history['pnl_absolute'] > 0]) / len(trade_history) * 100,
        'avg_win': trade_history[trade_history['pnl_absolute'] > 0]['pnl_absolute'].mean(),
        'avg_loss': trade_history[trade_history['pnl_absolute'] < 0]['pnl_absolute'].mean(),
        'largest_win': trade_history['pnl_absolute'].max(),
        'largest_loss': trade_history['pnl_absolute'].min(),
        'avg_trade_duration': trade_history['duration'].mean()
    }
    
    # Profit Factor
    gross_profit = trade_history[trade_history['pnl_absolute'] > 0]['pnl_absolute'].sum()
    gross_loss = abs(trade_history[trade_history['pnl_absolute'] < 0]['pnl_absolute'].sum())
    metrics['profit_factor'] = gross_profit / gross_loss if gross_loss > 0 else float('inf')
    
    # 🆕 ДОБАВЛЯЕМ АНАЛИЗ РИСК-МЕНЕДЖМЕНТА К ОСНОВНЫМ МЕТРИКАМ
    risk_analysis = analyze_trades_with_risk_management(trade_history)
    metrics['risk_analysis'] = risk_analysis
    
    return metrics

# 🆕 НОВАЯ ФУНКЦИЯ: Генерация отчета по рискам
def generate_risk_report(performance: Dict[str, Any], trade_metrics: Dict[str, Any]) -> str:
    """
    Генерация текстового отчета по системе управления рисками
    
    Parameters:
    -----------
    performance : dict
        Метрики производительности
    trade_metrics : dict
        Метрики сделок
        
    Returns:
    --------
    str
        Текстовый отчет
    """
    report = []
    report.append("=" * 60)
    report.append("ОТЧЕТ ПО СИСТЕМЕ УПРАВЛЕНИЯ РИСКАМИ")
    report.append("=" * 60)
    report.append("")
    
    # Основная информация
    if performance.get('risk_system_enabled', False):
        report.append("✅ СИСТЕМА РИСК-МЕНЕДЖМЕНТА АКТИВНА")
        report.append(f"   Всего сделок с рисками: {performance.get('total_trades_with_risk', 0)}")
        report.append("")
    else:
        report.append("❌ СИСТЕМА РИСК-МЕНЕДЖМЕНТА НЕ АКТИВНА")
        report.append("")
        return "\n".join(report)
    
    # Статистика по типам выходов
    report.append("📊 СТАТИСТИКА ВЫХОДОВ:")
    for reason in ['stop_loss', 'take_profit', 'trailing_stop', 'time_stop']:
        count = performance.get(f'{reason}_trades', 0)
        if count > 0:
            avg_pnl = performance.get(f'avg_{reason}_pnl', 0)
            report.append(f"   {reason.upper()}: {count} сделок, средний PnL: {avg_pnl:+.2f}%")
    
    report.append("")
    
    # Эффективность
    report.append("🎯 ЭФФЕКТИВНОСТЬ РИСК-МЕНЕДЖМЕНТА:")
    report.append(f"   Win Rate с рисками: {performance.get('win_rate_with_stops', 0):.1f}%")
    report.append(f"   Risk-Reward Ratio: {performance.get('risk_reward_ratio', 0):.2f}")
    report.append(f"   Эффективность стоп-лоссов: {performance.get('stop_loss_efficiency', 0):.1f}%")
    
    # Анализ PnL по причинам
    if 'pnl_by_reason' in performance:
        report.append("")
        report.append("💰 PnL ПО ПРИЧИНАМ ВЫХОДА:")
        pnl_data = performance['pnl_by_reason']
        for reason, stats in pnl_data.items():
            if 'mean' in stats and stats.get('count', 0) > 0:
                report.append(f"   {reason}: {stats['mean']:+.2f}% (n={stats['count']})")
    
    return "\n".join(report)

# 🆕 НОВАЯ ФУНКЦИЯ: Детальный анализ эффективности риск-ордеров
def analyze_risk_efficiency(trade_history: pd.DataFrame, price_data: pd.DataFrame) -> Dict[str, Any]:
    """
    Глубокий анализ эффективности стоп-лоссов и тейк-профитов
    """
    if trade_history.empty:
        return {}
    
    analysis = {
        'total_trades_with_risk': 0,
        'stop_loss_analysis': {},
        'take_profit_analysis': {}, 
        'exit_timing_analysis': {},
        'risk_efficiency_score': 0
    }
    
    # Фильтруем сделки с риск-менеджментом
    risk_trades = trade_history[trade_history['exit_reason'].isin([
        'stop_loss', 'take_profit', 'trailing_stop', 'time_stop'
    ])]
    
    analysis['total_trades_with_risk'] = len(risk_trades)
    
    if risk_trades.empty:
        return analysis
    
    # Анализ стоп-лоссов
    stop_loss_trades = risk_trades[risk_trades['exit_reason'] == 'stop_loss']
    if not stop_loss_trades.empty:
        analysis['stop_loss_analysis'] = {
            'count': len(stop_loss_trades),
            'avg_pnl_percent': stop_loss_trades['pnl_percent'].mean(),
            'avg_pnl_absolute': stop_loss_trades['pnl_absolute'].mean(),
            'max_loss': stop_loss_trades['pnl_percent'].min(),
            'premature_stops': 0,  # Будеи рассчитывать ниже
            'optimal_stops': 0
        }
    
    # Анализ тейк-профитов
    take_profit_trades = risk_trades[risk_trades['exit_reason'] == 'take_profit']
    if not take_profit_trades.empty:
        analysis['take_profit_analysis'] = {
            'count': len(take_profit_trades),
            'avg_pnl_percent': take_profit_trades['pnl_percent'].mean(),
            'avg_pnl_absolute': take_profit_trades['pnl_absolute'].mean(),
            'max_profit': take_profit_trades['pnl_percent'].max(),
            'missed_profits': 0,  # Будем рассчитывать ниже
            'optimal_takes': 0
        }
    
    # Анализ времени удержания
    analysis['exit_timing_analysis'] = {
        'avg_hold_time_days': risk_trades['duration'].mean(),
        'median_hold_time_days': risk_trades['duration'].median(),
        'quickest_exit': risk_trades['duration'].min(),
        'longest_hold': risk_trades['duration'].max()
    }
    
    # 🆕 Расчет эффективности риск-менеджмента
    analysis['risk_efficiency_score'] = calculate_risk_efficiency_score(analysis)
    
    return analysis

# 🆕 НОВАЯ ФУНКЦИЯ: Расчет общего скора эффективности
def calculate_risk_efficiency_score(risk_analysis: Dict) -> float:
    """Расчет общей оценки эффективности риск-менеджмента (0-100)"""
    score = 50  # Базовая оценка
    
    if not risk_analysis.get('total_trades_with_risk', 0):
        return 0
    
    # Бонус за использование риск-менеджмента
    score += min(20, risk_analysis['total_trades_with_risk'] / 10)
    
    # Анализ стоп-лоссов
    stop_analysis = risk_analysis.get('stop_loss_analysis', {})
    if stop_analysis:
        avg_stop_pnl = stop_analysis.get('avg_pnl_percent', 0)
        if avg_stop_pnl > -5:  # Хорошие стопы (потери < 5%)
            score += 15
        elif avg_stop_pnl > -10:  # Приемлемые стопы
            score += 5
    
    # Анализ тейк-профитов  
    take_analysis = risk_analysis.get('take_profit_analysis', {})
    if take_analysis:
        avg_take_pnl = take_analysis.get('avg_pnl_percent', 0)
        if avg_take_pnl > 5:  # Хорошие тейки (прибыль > 5%)
            score += 15
        elif avg_take_pnl > 2:  # Приемлемые тейки
            score += 5
    
    return min(100, max(0, score))

# 🆕 НОВАЯ ФУНКЦИЯ: Генерация отчета по эффективности рисков
def generate_risk_efficiency_report(risk_analysis: Dict) -> str:
    """Генерация текстового отчета по эффективности риск-менеджмента"""
    report = []
    report.append("=" * 60)
    report.append("📊 ОТЧЕТ ЭФФЕКТИВНОСТИ РИСК-МЕНЕДЖМЕНТА")
    report.append("=" * 60)
    
    if not risk_analysis.get('total_trades_with_risk', 0):
        report.append("❌ Нет данных о сделках с риск-менеджментом")
        return "\n".join(report)
    
    # Общая статистика
    report.append(f"📈 Общее количество сделок с рисками: {risk_analysis['total_trades_with_risk']}")
    report.append(f"🎯 Оценка эффективности: {risk_analysis['risk_efficiency_score']:.1f}/100")
    report.append("")
    
    # Анализ стоп-лоссов
    stop_analysis = risk_analysis.get('stop_loss_analysis', {})
    if stop_analysis:
        report.append("🛑 АНАЛИЗ СТОП-ЛОССОВ:")
        report.append(f"   • Количество: {stop_analysis['count']}")
        report.append(f"   • Средний PnL: {stop_analysis['avg_pnl_percent']:+.2f}%")
        report.append(f"   • Макс. убыток: {stop_analysis['max_loss']:+.2f}%")
        report.append("")
    
    # Анализ тейк-профитов
    take_analysis = risk_analysis.get('take_profit_analysis', {})
    if take_analysis:
        report.append("✅ АНАЛИЗ ТЕЙК-ПРОФИТОВ:")
        report.append(f"   • Количество: {take_analysis['count']}")
        report.append(f"   • Средний PnL: {take_analysis['avg_pnl_percent']:+.2f}%")
        report.append(f"   • Макс. прибыль: {take_analysis['max_profit']:+.2f}%")
        report.append("")
    
    # Анализ времени
    timing_analysis = risk_analysis.get('exit_timing_analysis', {})
    if timing_analysis:
        report.append("⏱️  АНАЛИЗ ВРЕМЕНИ УДЕРЖАНИЯ:")
        report.append(f"   • Среднее время: {timing_analysis['avg_hold_time_days']:.1f} дней")
        report.append(f"   • Медианное время: {timing_analysis['median_hold_time_days']:.1f} дней")
        report.append(f"   • Самое короткое: {timing_analysis['quickest_exit']} дней")
        report.append(f"   • Самое долгое: {timing_analysis['longest_hold']} дней")
    
    # Рекомендации
    report.append("")
    report.append("💡 РЕКОМЕНДАЦИИ:")
    score = risk_analysis['risk_efficiency_score']
    if score >= 80:
        report.append("   🎉 Отличная эффективность! Продолжайте в том же духе.")
    elif score >= 60:
        report.append("   👍 Хорошие результаты. Возможно, стоит настроить параметры рисков.")
    elif score >= 40:
        report.append("   ⚠️ Средняя эффективность. Рекомендуется пересмотреть стратегию рисков.")
    else:
        report.append("   🚨 Низкая эффективность. Необходима оптимизация параметров рисков.")
    
    return "\n".join(report)

# Оптимизированные функции аналитики:

def analyze_performance_optimized(results: pd.DataFrame, initial_capital: float) -> Dict[str, Any]:
    """Оптимизированный анализ производительности"""
    
    if results.empty:
        return {}
    
    capital = results['capital']
    
    # Векторизованные расчеты
    total_return_pct = (capital.iloc[-1] - initial_capital) / initial_capital * 100
    
    # Оптимизированный расчет просадки
    cumulative_max = capital.cummax()
    drawdown = (cumulative_max - capital) / cumulative_max
    max_drawdown_pct = drawdown.max() * 100
    
    # Быстрый расчет доходностей
    returns = capital.pct_change().dropna()
    
    # Оптимизированный расчет Шарпа
    if len(returns) > 1 and returns.std() > 0:
        sharpe = returns.mean() / returns.std() * np.sqrt(252)
    else:
        sharpe = 0
    
    # Быстрый сбор метрик
    performance = {
        'total_return': total_return_pct,
        'max_drawdown': max_drawdown_pct,
        'sharpe_ratio': sharpe,
        'final_capital': capital.iloc[-1],
        'volatility': returns.std() * np.sqrt(252) * 100 if len(returns) > 0 else 0,
        'total_trades': len(results[results['position_type'] != 0]) if 'position_type' in results.columns else 0
    }
    
    # Добавляем метрики рисков если доступны
    if 'risk_level' in results.columns:
        performance.update({
            'avg_risk': results['risk_level'].mean() * 100,
            'risk_adjustments': len(results[results['risk_level'] != results['risk_level'].iloc[0]])
        })
    
    return performance

def analyze_risk_management_optimized(results: pd.DataFrame) -> Dict[str, Any]:
    """Оптимизированный анализ риск-менеджмента"""
    
    risk_metrics = {
        'risk_system_enabled': False,
        'total_trades_with_risk': 0
    }
    
    if 'exit_reason' not in results.columns:
        return risk_metrics
    
    # Быстрый фильтр сделок с рисками
    exit_trades = results[results['exit_reason'] != '']
    if exit_trades.empty:
        return risk_metrics
    
    risk_metrics.update({
        'risk_system_enabled': True,
        'total_trades_with_risk': len(exit_trades)
    })
    
    # Быстрый подсчет по типам выходов
    for reason in ['stop_loss', 'take_profit', 'trailing_stop', 'time_stop']:
        count = len(exit_trades[exit_trades['exit_reason'] == reason])
        if count > 0:
            risk_metrics[f'{reason}_trades'] = count
    
    return risk_metrics

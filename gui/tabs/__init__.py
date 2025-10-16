# ===== СЕКЦИЯ 15: ПАКЕТ ВКЛАДОК ГРАФИЧЕСКОГО ИНТЕРФЕЙСА =====
"""
Инициализационный файл пакета вкладок
Экспорт всех классов вкладок для удобного импорта
"""

from .price_tab import PriceTab
from .capital_tab import CapitalTab
from .position_tab import PositionTab
from .returns_tab import ReturnsTab
from .correlation_tab import CorrelationTab
from .trades_tab import TradesTab
from .stats_tab import StatsTab
from .compare_tab import CompareTab
from .risk_tab import RiskTab
from .risk_analysis_tab import RiskAnalysisTab  # 🆕 НОВАЯ ВКЛАДКА

__all__ = [
    'PriceTab',
    'CapitalTab', 
    'PositionTab',
    'ReturnsTab',
    'CorrelationTab',
    'TradesTab',
    'StatsTab',
    'CompareTab',
    'RiskTab',
    'RiskAnalysisTab'  # 🆕 ДОБАВЛЯЕМ НОВУЮ ВКЛАДКУ
]
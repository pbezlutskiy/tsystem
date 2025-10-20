# tbank_api/cache_optimizer.py
"""
Безопасная оптимизация хранения данных
"""

import pandas as pd
import numpy as np
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

class SafeCacheOptimizer:
    """Безопасный оптимизатор - только проверенные методы"""
    
    @staticmethod
    def optimize_dataframe_safe(df: pd.DataFrame) -> pd.DataFrame:
        """
        Безопасная оптимизация DataFrame - только то, что не может сломать данные
        """
        if df.empty:
            return df
        
        result = df.copy()
        
        try:
            # 1. Удаление дубликатов по индексу (абсолютно безопасно)
            result = result[~result.index.duplicated(keep='first')]
            
            # 2. Сортировка по индексу (безопасно)
            if not result.index.is_monotonic_increasing:
                result = result.sort_index()
            
            # 3. Оптимизация числовых типов (осторожно)
            for col in result.select_dtypes(include=[np.float64]).columns:
                # Проверяем, что преобразование безопасно
                if result[col].notna().all():
                    try:
                        # Пробуем преобразовать во float32
                        test_values = result[col].astype(np.float32)
                        # Проверяем, что не потеряли точность
                        if np.allclose(result[col].values, test_values.values, rtol=1e-6):
                            result[col] = test_values
                            logger.debug(f"✅ Оптимизирован столбец {col} -> float32")
                    except Exception as e:
                        logger.warning(f"Не удалось оптимизировать {col}: {e}")
            
            logger.info(f"✅ Данные оптимизированы: {len(result)} записей")
            return result
            
        except Exception as e:
            logger.error(f"❌ Ошибка оптимизации данных: {e}")
            return df  # Возвращаем оригинал при ошибке
    
    @staticmethod
    def get_size_reduction_stats(original_df: pd.DataFrame, optimized_df: pd.DataFrame) -> Dict[str, Any]:
        """Статистика сокращения размера"""
        if original_df.empty or optimized_df.empty:
            return {'size_reduction_percent': 0, 'original_size_mb': 0, 'optimized_size_mb': 0}
        
        original_size = original_df.memory_usage(deep=True).sum() / 1024 / 1024
        optimized_size = optimized_df.memory_usage(deep=True).sum() / 1024 / 1024
        
        reduction = ((original_size - optimized_size) / original_size * 100) if original_size > 0 else 0
        
        return {
            'size_reduction_percent': round(reduction, 2),
            'original_size_mb': round(original_size, 2),
            'optimized_size_mb': round(optimized_size, 2)
        }
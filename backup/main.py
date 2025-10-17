# ===== СЕКЦИЯ 1: ГЛАВНЫЙ ФАЙЛ ЗАПУСКА =====
"""
Главный файл для запуска торговой системы Сейкоты
Автоматически инициализирует все компоненты и запускает GUI
"""

import tkinter as tk
from tkinter import messagebox
import sys
import os

# Добавляем пути для импорта модулей
sys.path.append(os.path.join(os.path.dirname(__file__), 'core'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'gui'))
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))

from gui.main_window import TradingSystemGUI

def main():
    """Основная функция запуска программы"""
    try:
        # Создаем главное окно
        root = tk.Tk()
        
        # Настраиваем стиль
        style = tk.ttk.Style()
        style.configure('Accent.TButton', font=('Arial', 10, 'bold'))
        
        # Запускаем приложение - ПРАВИЛЬНЫЙ ВЫЗОВ
        app = TradingSystemGUI(root)  # ✅ ПЕРЕДАЕМ root КАК АРГУМЕНТ
        root.mainloop()
        
    except Exception as e:
        messagebox.showerror("Критическая ошибка", 
                           f"Не удалось запустить приложение: {str(e)}")

if __name__ == "__main__":
    main()
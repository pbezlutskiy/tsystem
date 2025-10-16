import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta, UTC
from tinkoff.invest import Client, CandleInterval
import mplfinance as mpf
from config import Config
TOKEN = Config.TINKOFF_TOKEN

def plot_candlestick_basic(candles_df):
    """Базовый свечной график с использованием matplotlib"""
    fig, ax = plt.subplots(figsize=(15, 8))

    # Проходим по всем свечам
    for i, row in candles_df.iterrows():
        time = row['time']
        open_price = row['open']
        close_price = row['close']
        high_price = row['high']
        low_price = row['low']

        # Определяем цвет свечи
        color = 'green' if close_price >= open_price else 'red'
        line_color = 'darkgreen' if close_price >= open_price else 'darkred'

        # Рисуем тень (high to low)
        ax.plot([time, time], [low_price, high_price], color='black', linewidth=0.5)

        # Рисуем тело свечи
        body_bottom = min(open_price, close_price)
        body_top = max(open_price, close_price)
        body_height = body_top - body_bottom

        # Добавляем прямоугольник для тела свечи
        if body_height > 0:
            rect = plt.Rectangle((mdates.date2num(time) - 0.0002, body_bottom),
                                0.0004, body_height,
                                facecolor=color, edgecolor=line_color, linewidth=1)
            ax.add_patch(rect)
        else:
            # Для дожи (open == close) рисуем линию
            ax.plot([time - timedelta(minutes=10), time + timedelta(minutes=10)],
                   [open_price, open_price], color=line_color, linewidth=2)

    # Настройки графика
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=3))
    ax.xaxis.set_minor_locator(mdates.HourLocator(interval=6))
    plt.xticks(rotation=45)

    ax.set_title('Свечной график SBER (1 час)', fontsize=16, fontweight='bold')
    ax.set_ylabel('Цена, руб.', fontsize=12)
    ax.set_xlabel('Дата', fontsize=12)
    ax.grid(True, alpha=0.3)
    ax.legend(['Свечи SBER'])

    plt.tight_layout()
    plt.show()

def plot_with_mplfinance(candles_df):
    """Свечной график с использованием mplfinance"""
    # Подготавливаем данные для mplfinance
    df = candles_df.set_index('time')
    df = df[['open', 'high', 'low', 'close', 'volume']]
    df.columns = ['Open', 'High', 'Low', 'Close', 'Volume']

    # Убедимся, что индекс в правильном формате
    df.index = pd.DatetimeIndex(df.index)

    print(f"Данные для mplfinance: {len(df)} свечей")
    print(df.head())

    # Настройка стиля
    mc = mpf.make_marketcolors(
        up='green', down='red',
        edge={'up': 'green', 'down': 'red'},
        wick={'up': 'black', 'down': 'black'},
        volume={'up': 'green', 'down': 'red'}
    )

    style = mpf.make_mpf_style(
        marketcolors=mc,
        gridstyle='--',
        y_on_right=False
    )

    # Построение графика
    try:
        mpf.plot(df,
                 type='candle',
                 style=style,
                 title='SBER - Свечной график (1 час)',
                 ylabel='Цена (руб)',
                 volume=True,
                 figsize=(12, 8),
                 datetime_format='%Y-%m-%d',
                 xrotation=45,
                 show_nontrading=False)
        print("График mplfinance построен успешно!")
    except Exception as e:
        print(f"Ошибка при построении графика mplfinance: {e}")

def plot_candlestick_simple(candles_df):
    """Простой и надежный свечной график"""
    fig, ax = plt.subplots(figsize=(15, 8))

    # Преобразуем время в числовой формат для matplotlib
    times = [mdates.date2num(t) for t in candles_df['time']]

    # Рисуем свечи
    for i in range(len(candles_df)):
        t = times[i]
        open_p = candles_df.iloc[i]['open']
        high_p = candles_df.iloc[i]['high']
        low_p = candles_df.iloc[i]['low']
        close_p = candles_df.iloc[i]['close']

        # Цвет свечи
        color = 'green' if close_p >= open_p else 'red'

        # Тень
        ax.plot([t, t], [low_p, high_p], color='black', linewidth=1)

        # Тело свечи
        width = 0.0004
        body_bottom = min(open_p, close_p)
        body_top = max(open_p, close_p)

        ax.add_patch(plt.Rectangle((t - width/2, body_bottom),
                                 width, body_top - body_bottom,
                                 facecolor=color, edgecolor='black'))

    # Настройки оси X
    ax.xaxis_date()
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))

    plt.xticks(rotation=45)
    plt.title('Свечной график SBER - 1 час')
    plt.ylabel('Цена (руб)')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

def main():
    with Client(TOKEN) as client:
        try:
            # Используем современный подход с UTC
            from_time = datetime.now(UTC) - timedelta(days=30)
            to_time = datetime.now(UTC)

            candles = client.market_data.get_candles(
                figi="BBG004730N88",  # SBER
                from_=from_time,
                to=to_time,
                interval=CandleInterval.CANDLE_INTERVAL_HOUR
            )

            print(f"Получено свечей: {len(candles.candles)}")
            print("-" * 80)

            # Собираем данные в DataFrame
            candles_data = []

            for candle in candles.candles:
                # Преобразуем Quotation в float
                open_price = candle.open.units + candle.open.nano / 1e9
                close_price = candle.close.units + candle.close.nano / 1e9
                high_price = candle.high.units + candle.high.nano / 1e9
                low_price = candle.low.units + candle.low.nano / 1e9

                print(f"Время: {candle.time.strftime('%Y-%m-%d %H:%M:%S')} | "
                      f"O: {open_price:8.2f} | C: {close_price:8.2f} | "
                      f"H: {high_price:8.2f} | L: {low_price:8.2f} | "
                      f"Объем: {candle.volume:8.0f}")

                candles_data.append({
                    'time': candle.time,
                    'open': open_price,
                    'close': close_price,
                    'high': high_price,
                    'low': low_price,
                    'volume': candle.volume
                })

            df = pd.DataFrame(candles_data)

            if len(df) > 0:
                print(f"\nДоступно свечей для построения: {len(df)}")
                print("Строим графики...")

                # Спросим пользователя какой график построить
                choice = input("Выберите тип графика (1 - базовый, 2 - mplfinance, 3 - простой): ")

                if choice == "1":
                    plot_candlestick_basic(df)
                elif choice == "2":
                    plot_with_mplfinance(df)
                elif choice == "3":
                    plot_candlestick_simple(df)
                else:
                    print("Неверный выбор, строим базовый график")
                    plot_candlestick_basic(df)

            else:
                print("Нет данных для построения графика")

        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()

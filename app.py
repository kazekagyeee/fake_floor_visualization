import streamlit as st
import pandas as pd
import serial
import time
import os

# Настройки стримлита
st.set_page_config(layout="wide")

# Настройки COM-порта
COM_PORT = "COM8"  # Укажите ваш COM-порт
BAUD_RATE = 9600

# Имя файла для логирования
LOG_FILE = "log.csv"

# Список параметров из строки данных
SENSORS = ["MQ2", "MQ9", "smoke", "T", "u", "P", "g", "dB", "vibro"]
SENSOR_LABELS = {
    "MQ2": "Газ MQ2 (единицы)",
    "MQ9": "Газ MQ9 (единицы)",
    "smoke": "Дым (ppm)",
    "T": "Температура (°C)",
    "u": "Влажность (%)",
    "P": "Давление (Па)",
    "g": "Газ (единицы)",
    "dB": "Уровень шума (дБ)",
    "vibro": "Вибрация (единицы)"
}

# Инициализация COM-порта
try:
    ser = serial.Serial(COM_PORT, BAUD_RATE, timeout=1)
    st.success(f"Соединение с {COM_PORT} установлено.")
except Exception as e:
    st.error(f"Ошибка подключения к {COM_PORT}: {e}")
    ser = None

# Инициализация файла лога
if not os.path.exists(LOG_FILE):
    pd.DataFrame(columns=["timestamp"] + SENSORS).to_csv(LOG_FILE, index=False)

# Функция для разбора строки данных
def parse_sensor_data(raw_data):
    try:
        # Убираем пробелы и делим строку по разделителю ":"
        data_parts = [part.strip() for part in raw_data.split(":")]
        parsed_data = {}
        for part in data_parts:
            if "=" in part:
                key, value = part.split("=")
                parsed_data[key] = float(value)  # Преобразуем значение в число
        return parsed_data
    except Exception as e:
        st.error(f"Ошибка разбора данных: {e}")
        return {}

# Заголовок Streamlit
st.title("Система контроля и мониторинга фальшпола Supervisor")

# Загружаем данные из CSV
data = pd.read_csv(LOG_FILE)


# Создаем столбцы для графиков
columns = st.columns(3)

# Плейсхолдеры для графиков
charts = {}

# Создаем графики для каждого датчика
for i, sensor in enumerate(SENSORS):
    with columns[i % 3]:
        st.markdown(f"### {SENSOR_LABELS[sensor]}")
        charts[sensor] = st.empty()  # Создаем пустое место для графика


# Основной цикл обработки данных
while True:
    if ser and ser.in_waiting > 0:
        try:
            # Читаем строку из COM-порта
            raw_data = ser.readline().decode("utf-8").strip()
            print(raw_data)
            parsed_data = parse_sensor_data(raw_data)

            if parsed_data:
                # Добавляем текущие данные в DataFrame
                current_time = time.strftime("%Y-%m-%d %H:%M:%S")
                new_row = {"timestamp": current_time, **parsed_data}
                data = pd.concat([data, pd.DataFrame([new_row])], ignore_index=True)

                # Сохраняем данные в файл
                data.to_csv(LOG_FILE, index=False)

                # Обновляем графики
                for sensor in SENSORS:
                    if sensor in data.columns:
                        with charts[sensor]:
                            charts[sensor].line_chart(data[sensor].dropna())  # Обновляем данные графика
        except Exception as e:
            st.error(f"Ошибка обработки данных: {e}")

    time.sleep(0.5)  # Задержка между обновлениями

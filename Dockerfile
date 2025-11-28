# Використовуємо офіційний базовий образ Python
FROM python:3.11-slim

# Встановлюємо робочу директорію в контейнері
WORKDIR /app

# Копіюємо requirements.txt та встановлюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо решту файлів проекту (скрипт і конфігурацію)
COPY . .

# Визначаємо команду для запуску скрипта
# Ми припускаємо, що наш скрипт називається emulator.py
CMD ["python", "emulator.py"]

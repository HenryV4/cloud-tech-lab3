# Використовуємо офіційний базовий образ Python
FROM python:3.11-slim

# Встановлюємо робочу директорію в контейнері
WORKDIR /app/emulator

# Копіюємо файли емулятора
COPY emulator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо решту файлів проекту 
COPY emulator/config.json .
COPY emulator/emulator.py .

# Визначаємо команду для запуску скрипта
# Вважаємо, що наш скрипт називається emulator.py
CMD ["python", "emulator.py"]

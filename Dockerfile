FROM python:3.9-slim
WORKDIR /app
# Копіюємо файли з папки emulator всередину контейнера
COPY emulator/ .
# Встановлюємо залежності
RUN pip install -r requirements.txt
# Запускаємо скрипт (зверни увагу, ім'я файлу emulator.py)
CMD ["python", "emulator.py"]

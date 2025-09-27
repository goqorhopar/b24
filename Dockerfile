FROM python:3.11-slim

WORKDIR /app

# Устанавливаем зависимости
RUN pip install --no-cache-dir \
    requests \
    google-generativeai \
    python-dotenv

# Копируем файлы
COPY autonomous_bot.py .
COPY requirements.txt .

# Создаем директорию логов
RUN mkdir -p logs

# Запускаем бота
CMD ["python", "autonomous_bot.py"]
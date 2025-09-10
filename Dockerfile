# Используем официальный Python образ
FROM python:3.11-slim

# Устанавливаем метаданные
LABEL maintainer="Telegram Gemini Bot"
LABEL version="2.0"
LABEL description="Telegram bot for sales meeting analysis with Gemini AI and Bitrix24 integration"

# Устанавливаем переменные окружения
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# Создаем рабочую директорию
WORKDIR /app

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Создаем пользователя для безопасности
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Копируем файл зависимостей
COPY requirements.txt .

# Обновляем pip и устанавливаем зависимости
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код приложения
COPY . .

# Создаем директорию для базы данных и логов
RUN mkdir -p /app/data /app/logs

# Устанавливаем права доступа
RUN chown -R appuser:appgroup /app
RUN chmod +x /app/*.py

# Переключаемся на непривилегированного пользователя
USER appuser

# Устанавливаем переменные окружения по умолчанию
ENV PORT=3000
ENV LOG_LEVEL=info
ENV DB_PATH=/app/data/bot_state.db

# Открываем порт
EXPOSE 3000

# Проверка здоровья контейнера
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1

# Команда запуска
CMD ["gunicorn", "main:app", "--bind", "0.0.0.0:3000", "--workers", "2", "--timeout", "120", "--worker-class", "sync", "--max-requests", "1000", "--max-requests-jitter", "100", "--preload", "--access-logfile", "-", "--error-logfile", "-"]

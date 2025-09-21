# Dockerfile для Telegram Meeting Bot
FROM python:3.11-slim

# Устанавливаем системные зависимости
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    curl \
    xvfb \
    pulseaudio \
    pulseaudio-utils \
    alsa-utils \
    && rm -rf /var/lib/apt/lists/*

# Устанавливаем Google Chrome
RUN wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update \
    && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Создаем пользователя для запуска приложения
RUN useradd -m -s /bin/bash botuser

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем Python зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем исходный код
COPY src/ ./src/
COPY *.py ./

# Создаем директории для данных
RUN mkdir -p /app/data/recordings /app/data/logs /app/data/backups \
    && chown -R botuser:botuser /app

# Переключаемся на непривилегированного пользователя
USER botuser

# Настраиваем переменные окружения
ENV PYTHONPATH=/app
ENV DISPLAY=:99
ENV PULSE_RUNTIME_PATH=/tmp/pulse

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Открываем порт
EXPOSE 5000

# Команда запуска
CMD ["python", "main.py"]
